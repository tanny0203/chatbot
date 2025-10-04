"""
Helper functions for the NL2SQL two-model pipeline.
Clean, modular functions for data processing, SQL generation, and execution.
"""

import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from services.two_model_pipeline import get_two_model_pipeline
from services.memory_service import get_memory_service
import json

logger = logging.getLogger(__name__)

def extract_metadata(df: pd.DataFrame, table_name: str, user_id: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from DataFrame for SQL generation.
    
    Args:
        df: Pandas DataFrame with the dataset
        table_name: Original table name (without user prefix)
        user_id: User ID for multi-tenant isolation
        
    Returns:
        Dictionary with table schema, column info, and sample data
    """
    pipeline = get_two_model_pipeline()
    return pipeline.extract_metadata(df, table_name, user_id)

async def generate_sql(question: str, user_id: str, chat_id: str, dataset_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate SQL query using SQLCoder model with conversation history and dataset context.
    
    Args:
        question: Natural language question from user
        user_id: User ID for conversation history
        chat_id: Chat ID for conversation context
        dataset_context: Table metadata and schema information
        
    Returns:
        Dictionary with success status, SQL query, and any errors
    """
    try:
        pipeline = get_two_model_pipeline()
        result = await pipeline.generate_sql(user_id, chat_id, question, dataset_context)
        
        if result["success"]:
            logger.info(f"Generated SQL for user {user_id}: {result['sql_query'][:100]}...")
        else:
            logger.error(f"SQL generation failed: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_sql: {e}")
        return {
            "success": False,
            "error": str(e),
            "sql_query": None
        }

async def execute_sql(sql: str, user_id: str, db: Session) -> Dict[str, Any]:
    """
    Execute SQL query safely with user isolation and return results.
    
    Args:
        sql: SQL query to execute
        user_id: User ID for security validation
        db: Database session
        
    Returns:
        Dictionary with execution results, row count, and column info
    """
    try:
        pipeline = get_two_model_pipeline()
        result = await pipeline.execute_sql(sql, user_id, db)
        
        if result["success"]:
            logger.info(f"Executed SQL for user {user_id}: {result['row_count']} rows returned")
        else:
            logger.error(f"SQL execution failed: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in execute_sql: {e}")
        return {
            "success": False,
            "error": str(e),
            "result": None
        }

async def generate_answer(question: str, sql_query: str, sql_result: Dict[str, Any], dataset_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate natural language explanation using Llama 3.2 based on query results.
    
    Args:
        question: Original user question
        sql_query: Generated SQL query
        sql_result: Results from SQL execution
        dataset_context: Dataset metadata for context
        
    Returns:
        Dictionary with natural language answer and metadata
    """
    try:
        pipeline = get_two_model_pipeline()
        result = await pipeline.generate_answer(question, sql_query, sql_result, dataset_context)
        
        if result["success"]:
            logger.info(f"Generated answer with {len(result['answer'])} characters")
        else:
            logger.error(f"Answer generation failed: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_answer: {e}")
        return {
            "success": False,
            "error": str(e),
            "answer": "I encountered an error generating a response to your question."
        }

def validate_user_input(question: str, user_id: str, chat_id: str) -> Dict[str, Any]:
    """
    Validate user input for security and format requirements.
    
    Args:
        question: User's natural language question
        user_id: User ID to validate
        chat_id: Chat ID to validate
        
    Returns:
        Dictionary with validation status and any errors
    """
    try:
        # Check question length and content
        if not question or not question.strip():
            return {
                "valid": False,
                "error": "Question cannot be empty"
            }
        
        if len(question) > 1000:
            return {
                "valid": False,
                "error": "Question is too long (max 1000 characters)"
            }
        
        # Basic SQL injection prevention
        dangerous_patterns = [
            "drop table", "delete from", "truncate", "alter table",
            "create table", "insert into", "update set", "grant", "revoke"
        ]
        
        question_lower = question.lower()
        for pattern in dangerous_patterns:
            if pattern in question_lower:
                return {
                    "valid": False,
                    "error": f"Question contains potentially dangerous content: {pattern}"
                }
        
        # Validate UUIDs
        import uuid
        try:
            uuid.UUID(user_id)
            uuid.UUID(chat_id)
        except ValueError:
            return {
                "valid": False,
                "error": "Invalid user ID or chat ID format"
            }
        
        return {
            "valid": True,
            "cleaned_question": question.strip()
        }
        
    except Exception as e:
        logger.error(f"Error validating user input: {e}")
        return {
            "valid": False,
            "error": "Input validation failed"
        }

def format_sql_result_for_display(sql_result: Dict[str, Any], max_rows: int = 10) -> Dict[str, Any]:
    """
    Format SQL execution results for user-friendly display.
    
    Args:
        sql_result: Raw SQL execution results
        max_rows: Maximum number of rows to include in formatted output
        
    Returns:
        Dictionary with formatted results suitable for display
    """
    try:
        if not sql_result.get("success"):
            return {
                "success": False,
                "error": sql_result.get("error", "Unknown error"),
                "formatted_result": "Query failed to execute"
            }
        
        result_data = sql_result.get("result", [])
        row_count = sql_result.get("row_count", 0)
        columns = sql_result.get("columns", [])
        
        if row_count == 0:
            return {
                "success": True,
                "formatted_result": "No results found",
                "summary": "Query executed successfully but returned no data",
                "row_count": 0
            }
        
        # Format limited data for display
        display_data = result_data[:max_rows]
        
        # Create summary
        summary_parts = [f"Found {row_count:,} row{'s' if row_count != 1 else ''}"]
        if len(columns) > 0:
            summary_parts.append(f"{len(columns)} column{'s' if len(columns) != 1 else ''}")
        
        if row_count > max_rows:
            summary_parts.append(f"showing first {max_rows}")
        
        formatted_result = {
            "success": True,
            "data": display_data,
            "columns": columns,
            "row_count": row_count,
            "summary": ", ".join(summary_parts),
            "truncated": row_count > max_rows
        }
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error formatting SQL result: {e}")
        return {
            "success": False,
            "error": str(e),
            "formatted_result": "Error formatting results"
        }

def get_conversation_context(user_id: str, chat_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get relevant conversation context for SQL generation.
    
    Args:
        user_id: User ID
        chat_id: Chat ID
        limit: Maximum number of previous messages to include
        
    Returns:
        List of relevant conversation messages
    """
    try:
        memory_service = get_memory_service()
        history = memory_service.get_conversation_history(user_id, chat_id)
        
        # Filter and limit conversation history
        relevant_messages = []
        for msg in history[-limit*2:]:  # Get more to filter relevant ones
            if msg.get("role") in ["human", "ai"]:
                # Include human questions and AI SQL responses
                if (msg["role"] == "human" or 
                    (msg["role"] == "ai" and msg.get("metadata", {}).get("type") in ["sql_generation", "complete_response"])):
                    relevant_messages.append({
                        "role": msg["role"],
                        "content": msg["content"][:200],  # Truncate long content
                        "timestamp": msg.get("timestamp")
                    })
        
        return relevant_messages[-limit:]  # Return last N relevant messages
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        return []

def handle_sql_error(error: str, sql_query: str) -> Dict[str, Any]:
    """
    Handle and categorize SQL execution errors for better user feedback.
    
    Args:
        error: Error message from SQL execution
        sql_query: The SQL query that failed
        
    Returns:
        Dictionary with error category and user-friendly message
    """
    try:
        error_lower = error.lower()
        
        # Categorize common SQL errors
        if "column" in error_lower and "does not exist" in error_lower:
            return {
                "category": "column_not_found",
                "user_message": "I tried to reference a column that doesn't exist in your dataset. Let me try a different approach.",
                "technical_error": error,
                "suggestion": "Check the column names in your dataset"
            }
        
        elif "table" in error_lower and ("does not exist" in error_lower or "not found" in error_lower):
            return {
                "category": "table_not_found",
                "user_message": "I couldn't find the data table. Please make sure you've uploaded a dataset.",
                "technical_error": error,
                "suggestion": "Upload a dataset first"
            }
        
        elif "syntax error" in error_lower:
            return {
                "category": "syntax_error",
                "user_message": "I generated an invalid SQL query. Let me try rephrasing your question.",
                "technical_error": error,
                "suggestion": "Try rephrasing your question"
            }
        
        elif "permission denied" in error_lower or "access denied" in error_lower:
            return {
                "category": "permission_error",
                "user_message": "I don't have permission to access the requested data.",
                "technical_error": error,
                "suggestion": "Contact support if this persists"
            }
        
        else:
            return {
                "category": "unknown_error",
                "user_message": "I encountered an error while processing your query. Please try again.",
                "technical_error": error,
                "suggestion": "Try simplifying your question"
            }
            
    except Exception as e:
        logger.error(f"Error handling SQL error: {e}")
        return {
            "category": "error_handler_failed",
            "user_message": "I encountered an unexpected error. Please try again.",
            "technical_error": str(e),
            "suggestion": "Contact support if this persists"
        }

def create_fallback_response(question: str, error_info: Dict[str, Any]) -> str:
    """
    Create a helpful fallback response when the pipeline fails.
    
    Args:
        question: Original user question
        error_info: Error information from pipeline
        
    Returns:
        User-friendly fallback response
    """
    try:
        error_category = error_info.get("category", "unknown")
        
        fallback_responses = {
            "no_dataset": "I don't see any uploaded dataset. Please upload a CSV or Excel file first, then I'll be able to answer questions about your data.",
            "column_not_found": "I had trouble finding the columns you mentioned. Could you check the column names in your dataset and try again?",
            "table_not_found": "I couldn't access your dataset. Please make sure it was uploaded successfully.",
            "syntax_error": "I had trouble creating a proper query for your question. Could you try rephrasing it?",
            "unknown_error": "I encountered an unexpected error. Please try asking your question in a different way."
        }
        
        base_response = fallback_responses.get(error_category, fallback_responses["unknown_error"])
        
        # Add helpful suggestions based on question content
        question_lower = question.lower()
        suggestions = []
        
        if any(word in question_lower for word in ["show", "display", "list"]):
            suggestions.append("Try asking 'What columns are in my data?' first")
        
        if any(word in question_lower for word in ["top", "best", "highest", "maximum"]):
            suggestions.append("Make sure to specify which column to sort by")
        
        if any(word in question_lower for word in ["count", "how many", "total"]):
            suggestions.append("Try asking 'How many rows are in my dataset?'")
        
        if suggestions:
            base_response += f" Here are some suggestions: {'; '.join(suggestions)}."
        
        return base_response
        
    except Exception as e:
        logger.error(f"Error creating fallback response: {e}")
        return "I'm having trouble processing your question right now. Please try again later."