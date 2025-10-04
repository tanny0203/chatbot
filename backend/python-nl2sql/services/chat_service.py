from typing import Dict, List, Any, Optional
from models.database import get_main_db
from services.memory_service import get_memory_service
from services.two_model_pipeline import get_two_model_pipeline
from utils.nl2sql_helpers import (
    validate_user_input, 
    handle_sql_error, 
    create_fallback_response,
    format_sql_result_for_display
)
import uuid
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat operations with memory"""
    
    def __init__(self, db: Session):
        self.db = db
        self.memory_service = get_memory_service()
        self.pipeline = get_two_model_pipeline()
    
    def create_chat(self, user_id: str) -> str:
        """Create a new chat and return chat_id"""
        chat_id = str(uuid.uuid4())
        
        # Initialize empty conversation in memory
        # (This happens automatically when first message is sent)
        
        logger.info(f"Created new chat {chat_id} for user {user_id}")
        return chat_id
    
    async def send_message(self, user_id: str, chat_id: str, message: str) -> Dict[str, Any]:
        """Send a message and get AI response with enhanced error handling"""
        try:
            # Validate user input
            validation_result = validate_user_input(message, user_id, chat_id)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["error"],
                    "error": validation_result["error"],
                    "validation_failed": True
                }
            
            # Use cleaned question
            cleaned_message = validation_result["cleaned_question"]
            
            # Use the two-model pipeline to process the query
            result = await self.pipeline.process_query(user_id, chat_id, cleaned_message, self.db)
            
            if result["success"]:
                # Format SQL results for better display
                if result.get("raw_result"):
                    formatted_result = format_sql_result_for_display({
                        "success": result.get("execution_success", False),
                        "result": result["raw_result"],
                        "row_count": result.get("result_count", 0)
                    })
                else:
                    formatted_result = None
                
                return {
                    "success": True,
                    "message": result["answer"],
                    "answer": result["answer"],
                    "sql_query": result.get("sql_query"),
                    "result_count": result.get("result_count", 0),
                    "execution_success": result.get("execution_success", False),
                    "formatted_result": formatted_result,
                    "has_dataset": True
                }
            else:
                # Enhanced error handling
                error_info = {
                    "category": "unknown_error",
                    "stage": result.get("stage", "unknown")
                }
                
                if result.get("requires_dataset"):
                    error_info["category"] = "no_dataset"
                elif "SQL generation failed" in result.get("error", ""):
                    error_info["category"] = "sql_generation_error"
                elif result.get("stage") == "sql_execution":
                    error_info = handle_sql_error(result.get("error", ""), result.get("sql_query", ""))
                
                # Create fallback response
                fallback_message = create_fallback_response(cleaned_message, error_info)
                
                return {
                    "success": False,
                    "message": fallback_message,
                    "error": result.get("error"),
                    "error_category": error_info.get("category"),
                    "requires_dataset": result.get("requires_dataset", False),
                    "stage": result.get("stage", "unknown"),
                    "suggestion": error_info.get("suggestion")
                }
                
        except ValueError as e:
            return {
                "success": False,
                "message": "Invalid user ID or chat ID format",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            fallback_message = create_fallback_response(message, {"category": "system_error"})
            return {
                "success": False,
                "message": fallback_message,
                "error": str(e),
                "error_category": "system_error"
            }
    
    def get_chat_history(self, user_id: str, chat_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get chat history with optional limit"""
        try:
            uuid.UUID(user_id)
            uuid.UUID(chat_id)
            
            history = self.memory_service.get_conversation_history(user_id, chat_id)
            dataset_context = self.memory_service.get_dataset_context(user_id, chat_id)
            
            if limit:
                history = history[-limit:]
            
            return {
                "success": True,
                "history": history,
                "dataset_context": {
                    "has_dataset": dataset_context is not None,
                    "table_name": dataset_context.get("table_name") if dataset_context else None,
                    "file_name": dataset_context.get("file_name") if dataset_context else None,
                    "row_count": dataset_context.get("row_count") if dataset_context else None
                },
                "total_messages": len(self.memory_service.get_conversation_history(user_id, chat_id))
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": "Invalid user ID or chat ID format",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return {
                "success": False,
                "message": "Error retrieving chat history",
                "error": str(e)
            }
    
    def clear_chat(self, user_id: str, chat_id: str) -> Dict[str, Any]:
        """Clear chat history and dataset context"""
        try:
            uuid.UUID(user_id)
            uuid.UUID(chat_id)
            
            self.nl2sql_model.clear_conversation(user_id, chat_id)
            
            return {
                "success": True,
                "message": "Chat cleared successfully"
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": "Invalid user ID or chat ID format",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error clearing chat: {e}")
            return {
                "success": False,
                "message": "Error clearing chat",
                "error": str(e)
            }
    
    def get_user_chats(self, user_id: str) -> Dict[str, Any]:
        """Get all chats for a user"""
        try:
            uuid.UUID(user_id)
            
            chat_ids = self.memory_service.get_user_chats(user_id)
            
            # Get basic info for each chat
            chats = []
            for chat_id in chat_ids:
                history = self.memory_service.get_conversation_history(user_id, chat_id)
                dataset_context = self.memory_service.get_dataset_context(user_id, chat_id)
                
                if history:  # Only include chats with messages
                    last_message = history[-1] if history else None
                    chats.append({
                        "chat_id": chat_id,
                        "message_count": len(history),
                        "last_message": last_message.get("content", "") if last_message else "",
                        "last_message_time": last_message.get("timestamp") if last_message else None,
                        "has_dataset": dataset_context is not None,
                        "dataset_name": dataset_context.get("file_name") if dataset_context else None
                    })
            
            # Sort by last message time (most recent first)
            chats.sort(key=lambda x: x.get("last_message_time", ""), reverse=True)
            
            return {
                "success": True,
                "chats": chats,
                "total_chats": len(chats)
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": "Invalid user ID format",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error getting user chats: {e}")
            return {
                "success": False,
                "message": "Error retrieving user chats",
                "error": str(e)
            }
    
    def update_dataset_context_from_file_service(self, user_id: str, chat_id: str, file_record, stats: Dict[str, Any]):
        """Update dataset context when a file is uploaded via FileService"""
        try:
            # Create a DataFrame from the stats to use the pipeline's metadata extraction
            import pandas as pd
            
            # Try to reconstruct basic DataFrame info for metadata extraction
            if stats.get("head") and stats.get("columns"):
                sample_df = pd.DataFrame(stats["head"], columns=stats["columns"])
            else:
                # Fallback: create minimal DataFrame structure
                columns = stats.get("columns", [])
                sample_df = pd.DataFrame(columns=columns)
            
            # Use pipeline's metadata extraction
            table_name = file_record.table_name.replace(f"user_{user_id}_", "")
            enhanced_metadata = self.pipeline.extract_metadata(sample_df, table_name, user_id)
            
            # Add additional info from file_record and stats
            enhanced_metadata.update({
                "file_name": file_record.filename,
                "row_count": stats.get("rows", enhanced_metadata.get("row_count", 0)),
                "file_id": str(file_record.id),
                "upload_time": file_record.created_at.isoformat() if hasattr(file_record, 'created_at') else None
            })
            
            # Store enhanced metadata in Redis memory
            self.memory_service.store_dataset_context(user_id, chat_id, enhanced_metadata)
            
            # Add system message about dataset upload
            self.memory_service.add_message_to_conversation(
                user_id, chat_id, "ai",
                f"Dataset '{file_record.filename}' uploaded successfully! "
                f"Table: {enhanced_metadata['table_name']}, "
                f"Columns: {len(enhanced_metadata['columns'])}, "
                f"Rows: {enhanced_metadata['row_count']:,}. "
                f"You can now ask questions about your data.",
                metadata={"type": "dataset_upload", "table_name": enhanced_metadata["table_name"]}
            )
            
            logger.info(f"Updated enhanced dataset context for chat {chat_id}: {file_record.table_name}")
            
        except Exception as e:
            logger.error(f"Error updating dataset context: {e}")
            
            # Fallback to basic context storage
            basic_context = {
                "table_name": file_record.table_name,
                "file_name": file_record.filename,
                "columns": stats.get("columns", []),
                "row_count": stats.get("rows", 0),
                "error": f"Enhanced metadata extraction failed: {str(e)}"
            }
            self.memory_service.store_dataset_context(user_id, chat_id, basic_context)

def get_chat_service(db: Session) -> ChatService:
    """Factory function to create ChatService with database dependency"""
    return ChatService(db)