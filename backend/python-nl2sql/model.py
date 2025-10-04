from langchain_community.llms import Ollama
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from typing import Dict, List, Any, Optional
import logging
from services.memory_service import get_memory_service

logger = logging.getLogger(__name__)

class NL2SQLModel:
    """Enhanced NL2SQL model with Redis memory and dataset context"""
    
    def __init__(self, model_name: str = "llama2"):
        self.llm = Ollama(model=model_name)
        self.memory_service = get_memory_service()
        
        # Enhanced prompt template with dataset context and conversation history
        self.prompt_template = PromptTemplate(
            input_variables=["dataset_context", "conversation_history", "question"],
            template="""You are a data assistant that converts natural language questions to SQL queries.

Dataset Context:
{dataset_context}

Previous Conversation:
{conversation_history}

Current Question: {question}

Instructions:
1. Use only the columns and table mentioned in the dataset context
2. Consider the conversation history for context
3. Generate a valid SQL query
4. If the question refers to previous queries, build upon that context
5. Always use the correct table name from the dataset context

SQL Query:"""
        )
    
    def _format_dataset_context(self, dataset_context: Optional[Dict[str, Any]]) -> str:
        """Format dataset context for the prompt"""
        if not dataset_context:
            return "No dataset context available. Please upload a dataset first."
        
        context_parts = []
        
        if dataset_context.get("table_name"):
            context_parts.append(f"Table: {dataset_context['table_name']}")
        
        if dataset_context.get("columns"):
            columns_info = []
            column_types = dataset_context.get("column_types", {})
            
            for col in dataset_context["columns"]:
                col_type = column_types.get(col, "unknown")
                columns_info.append(f"{col} ({col_type})")
            
            context_parts.append(f"Columns: {', '.join(columns_info)}")
        
        if dataset_context.get("row_count"):
            context_parts.append(f"Total Rows: {dataset_context['row_count']:,}")
        
        if dataset_context.get("sample_data"):
            context_parts.append("Sample Data:")
            for i, row in enumerate(dataset_context["sample_data"][:3]):  # Show first 3 rows
                context_parts.append(f"  Row {i+1}: {row}")
        
        return "\n".join(context_parts)
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for the prompt"""
        if not history:
            return "No previous conversation."
        
        formatted_history = []
        # Show last 5 exchanges to keep context manageable
        recent_history = history[-10:] if len(history) > 10 else history
        
        for msg in recent_history:
            role = "User" if msg["role"] == "human" else "Assistant"
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            formatted_history.append(f"{role}: {content}")
        
        return "\n".join(formatted_history)
    
    def generate_sql(self, user_id: str, chat_id: str, question: str) -> Dict[str, Any]:
        """Generate SQL with memory and dataset context"""
        try:
            # Get dataset context
            dataset_context = self.memory_service.get_dataset_context(user_id, chat_id)
            
            # Get conversation history
            conversation_history = self.memory_service.get_conversation_history(user_id, chat_id)
            
            # Format context for prompt
            formatted_dataset = self._format_dataset_context(dataset_context)
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Create the prompt
            prompt = self.prompt_template.format(
                dataset_context=formatted_dataset,
                conversation_history=formatted_history,
                question=question
            )
            
            # Generate SQL using Ollama
            response = self.llm.invoke(prompt)
            
            # Clean up the response (remove extra explanations)
            sql_query = self._extract_sql_from_response(response)
            
            # Store the conversation in memory
            self.memory_service.add_message_to_conversation(
                user_id, chat_id, "human", question
            )
            self.memory_service.add_message_to_conversation(
                user_id, chat_id, "ai", sql_query, 
                metadata={"type": "sql_generation"}
            )
            
            return {
                "success": True,
                "sql_query": sql_query,
                "raw_response": response,
                "has_dataset_context": dataset_context is not None,
                "conversation_length": len(conversation_history)
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            
            # Still store the failed attempt
            self.memory_service.add_message_to_conversation(
                user_id, chat_id, "human", question
            )
            self.memory_service.add_message_to_conversation(
                user_id, chat_id, "ai", f"Error: {str(e)}", 
                metadata={"type": "error"}
            )
            
            return {
                "success": False,
                "error": str(e),
                "has_dataset_context": False,
                "conversation_length": 0
            }
    
    def _extract_sql_from_response(self, response: str) -> str:
        """Extract clean SQL query from Ollama response"""
        # Remove common prefixes and suffixes
        response = response.strip()
        
        # Look for SQL keywords to find the actual query
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE"]
        
        lines = response.split('\n')
        sql_lines = []
        found_sql = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with SQL keyword
            if any(line.upper().startswith(keyword) for keyword in sql_keywords):
                found_sql = True
                sql_lines.append(line)
            elif found_sql:
                # Continue collecting SQL until we hit a non-SQL line
                if line.endswith(';') or any(keyword in line.upper() for keyword in ['FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'JOIN', 'LIMIT']):
                    sql_lines.append(line)
                else:
                    break
        
        if sql_lines:
            return '\n'.join(sql_lines)
        
        # If no clear SQL found, return the response as-is
        return response
    
    def store_dataset_context(self, user_id: str, chat_id: str, dataset_info: Dict[str, Any]):
        """Store dataset context in Redis memory"""
        try:
            self.memory_service.store_dataset_context(user_id, chat_id, dataset_info)
            
            # Add a system message about the dataset upload
            self.memory_service.add_message_to_conversation(
                user_id, chat_id, "ai", 
                f"Dataset '{dataset_info.get('file_name', 'Unknown')}' has been uploaded and analyzed. "
                f"Table: {dataset_info.get('table_name', 'N/A')}, "
                f"Columns: {len(dataset_info.get('columns', []))}, "
                f"Rows: {dataset_info.get('row_count', 0):,}",
                metadata={"type": "dataset_upload", "table_name": dataset_info.get("table_name")}
            )
            
        except Exception as e:
            logger.error(f"Error storing dataset context: {e}")
    
    def get_conversation_history(self, user_id: str, chat_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a chat"""
        return self.memory_service.get_conversation_history(user_id, chat_id)
    
    def clear_conversation(self, user_id: str, chat_id: str):
        """Clear conversation history"""
        self.memory_service.clear_conversation(user_id, chat_id)
        self.memory_service.clear_dataset_context(user_id, chat_id)
    
    def get_dataset_context(self, user_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset context for a chat"""
        return self.memory_service.get_dataset_context(user_id, chat_id)

# Global instance
_model_instance = None

def get_nl2sql_model() -> NL2SQLModel:
    """Get singleton instance of NL2SQL model"""
    global _model_instance
    if _model_instance is None:
        _model_instance = NL2SQLModel()
    return _model_instance

# Legacy function for backward compatibility
def nl2sql(question: str) -> str:
    """Legacy function - use get_nl2sql_model().generate_sql() instead"""
    model = get_nl2sql_model()
    result = model.generate_sql("default_user", "default_chat", question)
    return result.get("sql_query", "Error generating SQL")

# Example
if __name__ == "__main__":
    model = get_nl2sql_model()
    
    # Example dataset context
    dataset_context = {
        "table_name": "users",
        "columns": ["id", "name", "email", "registration_date"],
        "column_types": {"id": "INTEGER", "name": "TEXT", "email": "TEXT", "registration_date": "DATE"},
        "row_count": 1000,
        "file_name": "users.csv"
    }
    
    # Store dataset context
    model.store_dataset_context("test_user", "test_chat", dataset_context)
    
    # Ask question
    result = model.generate_sql("test_user", "test_chat", "Show me all users who registered in 2023")
    print(f"Success: {result['success']}")
    print(f"SQL: {result.get('sql_query', result.get('error'))}")