from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import Dict, List, Any, Optional, Tuple
import logging
import pandas as pd
import json
import re
from datetime import datetime
from services.memory_service import get_memory_service
from models.database import get_main_db

logger = logging.getLogger(__name__)

class TwoModelPipeline:
    """Two-model pipeline: SQLCoder for SQL generation + Llama 3.2 for natural language responses"""
    
    def __init__(self, sql_model: str = "sqlcoder", nlp_model: str = "llama3.2"):
        """Initialize both models"""
        try:
            self.sqlcoder = Ollama(model=sql_model)
            self.llama = Ollama(model=nlp_model)
            self.memory_service = get_memory_service()
            logger.info(f"Initialized models: SQLCoder ({sql_model}), Llama ({nlp_model})")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise
        
        # SQL generation prompt template
        self.sql_prompt = PromptTemplate(
            input_variables=["dataset_context", "conversation_history", "question"],
            template="""You are an expert SQL code generator. Generate only the SQL query, no explanations.

Dataset Schema:
{dataset_context}

Previous Conversation:
{conversation_history}

Question: {question}

Requirements:
1. Generate ONLY the SQL query, no explanations or comments
2. Use only the table and columns from the dataset schema
3. Always include the user_id filter for data isolation
4. Make queries safe and efficient
5. Use proper SQL syntax for PostgreSQL
6. If referencing previous queries, build upon that context

SQL Query:"""
        )
        
        # Natural language response prompt template
        self.nlp_prompt = PromptTemplate(
            input_variables=["question", "sql_query", "sql_result", "dataset_context"],
            template="""You are a data assistant that explains query results in natural language.

User Question: {question}
SQL Query Executed: {sql_query}
Query Results: {sql_result}
Dataset Info: {dataset_context}

Instructions:
1. Provide a clear, natural language explanation of the results
2. Include key insights or patterns if relevant
3. If no results, explain why and suggest alternatives
4. Keep the response conversational and helpful
5. Don't repeat the SQL query in your response
6. Format numbers appropriately (commas for thousands, etc.)

Response:"""
        )
    
    def extract_metadata(self, df: pd.DataFrame, table_name: str, user_id: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from DataFrame for SQL generation"""
        try:
            metadata = {
                "table_name": f"user_{user_id}_{table_name}",
                "original_table_name": table_name,
                "columns": list(df.columns),
                "row_count": len(df),
                "column_info": {}
            }
            
            # Extract detailed column information
            for col in df.columns:
                col_info = {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "sql_type": self._pandas_to_sql_type(df[col].dtype),
                    "null_count": df[col].isnull().sum(),
                    "unique_count": df[col].nunique(),
                    "sample_values": df[col].dropna().head(3).tolist()
                }
                
                # Add statistics for numeric columns
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_info.update({
                        "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                        "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                        "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None
                    })
                
                # Add categorical info for low-cardinality columns
                if col_info["unique_count"] <= 20:
                    value_counts = df[col].value_counts().head(10)
                    col_info["top_values"] = [
                        {"value": str(val), "count": int(count)} 
                        for val, count in value_counts.items()
                    ]
                
                metadata["column_info"][col] = col_info
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {
                "table_name": f"user_{user_id}_{table_name}",
                "columns": list(df.columns) if df is not None else [],
                "row_count": 0,
                "column_info": {},
                "error": str(e)
            }
    
    def _pandas_to_sql_type(self, dtype) -> str:
        """Convert pandas dtype to SQL type"""
        dtype_str = str(dtype).lower()
        
        if 'int' in dtype_str:
            return 'INTEGER'
        elif 'float' in dtype_str:
            return 'DOUBLE PRECISION'
        elif 'bool' in dtype_str:
            return 'BOOLEAN'
        elif 'datetime' in dtype_str or 'timestamp' in dtype_str:
            return 'TIMESTAMP'
        elif 'date' in dtype_str:
            return 'DATE'
        else:
            return 'TEXT'
    
    def _format_dataset_context(self, dataset_context: Dict[str, Any]) -> str:
        """Format dataset context for SQL generation prompt"""
        if not dataset_context or "error" in dataset_context:
            return "No dataset available"
        
        context_parts = [
            f"Table: {dataset_context['table_name']}",
            f"Total Rows: {dataset_context['row_count']:,}"
        ]
        
        # Add column information
        context_parts.append("\nColumns:")
        for col_name, col_info in dataset_context.get("column_info", {}).items():
            col_desc = f"  - {col_name} ({col_info['sql_type']})"
            
            if col_info.get("sample_values"):
                samples = [str(v) for v in col_info["sample_values"]]
                col_desc += f" - Examples: {', '.join(samples)}"
            
            if col_info.get("top_values"):
                top_vals = [f"{v['value']} ({v['count']})" for v in col_info["top_values"][:3]]
                col_desc += f" - Top values: {', '.join(top_vals)}"
            
            context_parts.append(col_desc)
        
        return "\n".join(context_parts)
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for context"""
        if not history:
            return "No previous conversation"
        
        formatted = []
        recent_history = history[-6:] if len(history) > 6 else history
        
        for msg in recent_history:
            if msg["role"] == "human":
                formatted.append(f"User: {msg['content']}")
            elif msg["role"] == "ai" and msg.get("metadata", {}).get("type") == "sql_generation":
                # Show previous SQL for context
                formatted.append(f"Generated SQL: {msg['content'][:100]}...")
        
        return "\n".join(formatted)
    
    async def generate_sql(self, user_id: str, chat_id: str, question: str, dataset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query using SQLCoder"""
        try:
            # Get conversation history
            conversation_history = self.memory_service.get_conversation_history(user_id, chat_id)
            
            # Format context for prompt
            formatted_dataset = self._format_dataset_context(dataset_context)
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Create prompt
            prompt = self.sql_prompt.format(
                dataset_context=formatted_dataset,
                conversation_history=formatted_history,
                question=question
            )
            
            # Generate SQL
            raw_response = await self.sqlcoder.ainvoke(prompt)
            sql_query = self._clean_sql_response(raw_response)
            
            # Validate SQL basic structure
            if not self._is_valid_sql_structure(sql_query):
                raise ValueError("Generated SQL appears to be invalid")
            
            # Add user_id filter if not present
            sql_query = self._ensure_user_isolation(sql_query, user_id, dataset_context.get("table_name", ""))
            
            return {
                "success": True,
                "sql_query": sql_query,
                "raw_response": raw_response
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql_query": None
            }
    
    def _clean_sql_response(self, response: str) -> str:
        """Clean SQL response from model"""
        # Remove code blocks and extra text
        response = response.strip()
        
        # Look for SQL query patterns
        sql_pattern = r'(SELECT.*?(?:;|$))'
        match = re.search(sql_pattern, response, re.IGNORECASE | re.DOTALL)
        
        if match:
            sql = match.group(1)
        else:
            # Fallback: take everything that looks like SQL
            lines = response.split('\n')
            sql_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    sql_lines.append(line)
            sql = '\n'.join(sql_lines)
        
        # Clean up
        sql = sql.replace('```sql', '').replace('```', '').strip()
        if not sql.endswith(';'):
            sql += ';'
            
        return sql
    
    def _is_valid_sql_structure(self, sql: str) -> bool:
        """Basic validation of SQL structure"""
        sql_upper = sql.upper().strip()
        
        # Check for basic SQL keywords
        if not any(keyword in sql_upper for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            return False
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            return False
        
        return True
    
    def _ensure_user_isolation(self, sql: str, user_id: str, table_name: str) -> str:
        """Ensure SQL query includes user isolation"""
        # This is a basic implementation - you might need more sophisticated parsing
        if f"user_{user_id}_" not in sql and table_name:
            # Replace table name with user-specific table name
            original_table = table_name.replace(f"user_{user_id}_", "")
            sql = sql.replace(original_table, table_name)
        
        return sql
    
    async def execute_sql(self, sql: str, user_id: str, db: Session) -> Dict[str, Any]:
        """Execute SQL query safely and return results"""
        try:
            # Additional security check - ensure query is read-only
            sql_upper = sql.upper().strip()
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
            
            if any(keyword in sql_upper for keyword in dangerous_keywords):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed",
                    "result": None
                }
            
            # Execute query
            result = db.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()
            
            # Convert to list of dictionaries
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "success": True,
                "result": data,
                "row_count": len(data),
                "columns": list(columns)
            }
            
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def generate_answer(self, question: str, sql_query: str, sql_result: Dict[str, Any], dataset_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate natural language answer using Llama 3.2"""
        try:
            # Format SQL result for prompt
            if sql_result["success"]:
                if sql_result["row_count"] == 0:
                    result_text = "No results found."
                else:
                    # Format first few rows
                    result_data = sql_result["result"][:10]  # Limit to first 10 rows
                    result_text = f"Found {sql_result['row_count']} rows:\n"
                    result_text += json.dumps(result_data, indent=2, default=str)
                    
                    if sql_result["row_count"] > 10:
                        result_text += f"\n... and {sql_result['row_count'] - 10} more rows"
            else:
                result_text = f"Query failed: {sql_result['error']}"
            
            # Format dataset context
            dataset_summary = f"Dataset: {dataset_context.get('original_table_name', 'Unknown')}, {dataset_context.get('row_count', 0)} total rows"
            
            # Create prompt
            prompt = self.nlp_prompt.format(
                question=question,
                sql_query=sql_query,
                sql_result=result_text,
                dataset_context=dataset_summary
            )
            
            # Generate natural language response
            response = await self.llama.ainvoke(prompt)
            
            return {
                "success": True,
                "answer": response.strip(),
                "result_count": sql_result.get("row_count", 0) if sql_result["success"] else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating natural language answer: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "I encountered an error generating a response to your question."
            }
    
    async def process_query(self, user_id: str, chat_id: str, question: str, db: Session) -> Dict[str, Any]:
        """Complete pipeline: question -> SQL -> execution -> natural language answer"""
        try:
            # Get dataset context
            dataset_context = self.memory_service.get_dataset_context(user_id, chat_id)
            
            if not dataset_context:
                return {
                    "success": False,
                    "error": "No dataset found. Please upload a dataset first.",
                    "requires_dataset": True
                }
            
            # Step 1: Generate SQL
            sql_result = await self.generate_sql(user_id, chat_id, question, dataset_context)
            
            if not sql_result["success"]:
                return {
                    "success": False,
                    "error": f"SQL generation failed: {sql_result['error']}",
                    "stage": "sql_generation"
                }
            
            sql_query = sql_result["sql_query"]
            
            # Step 2: Execute SQL
            execution_result = await self.execute_sql(sql_query, user_id, db)
            
            # Step 3: Generate natural language answer
            answer_result = await self.generate_answer(question, sql_query, execution_result, dataset_context)
            
            # Store conversation in memory
            self.memory_service.add_message_to_conversation(user_id, chat_id, "human", question)
            
            if answer_result["success"]:
                self.memory_service.add_message_to_conversation(
                    user_id, chat_id, "ai", answer_result["answer"],
                    metadata={
                        "type": "complete_response",
                        "sql_query": sql_query,
                        "result_count": answer_result.get("result_count", 0),
                        "execution_success": execution_result["success"]
                    }
                )
            else:
                self.memory_service.add_message_to_conversation(
                    user_id, chat_id, "ai", f"Error: {answer_result['error']}",
                    metadata={"type": "error", "sql_query": sql_query}
                )
            
            return {
                "success": answer_result["success"],
                "answer": answer_result["answer"],
                "sql_query": sql_query,
                "result_count": answer_result.get("result_count", 0),
                "execution_success": execution_result["success"],
                "raw_result": execution_result["result"] if execution_result["success"] else None
            }
            
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            
            # Store error in conversation
            self.memory_service.add_message_to_conversation(user_id, chat_id, "human", question)
            self.memory_service.add_message_to_conversation(
                user_id, chat_id, "ai", f"System error: {str(e)}",
                metadata={"type": "system_error"}
            )
            
            return {
                "success": False,
                "error": str(e),
                "answer": "I encountered a system error processing your question. Please try again."
            }

# Global instance
_pipeline_instance = None

def get_two_model_pipeline() -> TwoModelPipeline:
    """Get singleton instance of the two-model pipeline"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = TwoModelPipeline()
    return _pipeline_instance