import redis
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class RedisMemoryService:
    """Redis-based memory service for LangChain conversations and dataset context"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    # === Conversation Memory Methods ===
    
    def get_conversation_key(self, user_id: str, chat_id: str) -> str:
        """Generate Redis key for conversation memory"""
        return f"conversation:{user_id}:{chat_id}"
    
    def get_conversation_history(self, user_id: str, chat_id: str) -> List[Dict[str, Any]]:
        """Retrieve conversation history from Redis"""
        key = self.get_conversation_key(user_id, chat_id)
        try:
            history_json = self.redis_client.get(key)
            if history_json:
                return json.loads(history_json)
            return []
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    def add_message_to_conversation(self, user_id: str, chat_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        key = self.get_conversation_key(user_id, chat_id)
        try:
            # Get existing history
            history = self.get_conversation_history(user_id, chat_id)
            
            # Add new message
            message = {
                "role": role,  # "human" or "ai"
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            history.append(message)
            
            # Store back to Redis with expiration (7 days)
            self.redis_client.setex(
                key, 
                timedelta(days=7), 
                json.dumps(history)
            )
            
        except Exception as e:
            logger.error(f"Error adding message to conversation: {e}")
    
    def clear_conversation(self, user_id: str, chat_id: str):
        """Clear conversation history"""
        key = self.get_conversation_key(user_id, chat_id)
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
    
    # === Dataset Context Memory Methods ===
    
    def get_dataset_key(self, user_id: str, chat_id: str) -> str:
        """Generate Redis key for dataset context"""
        return f"dataset:{user_id}:{chat_id}"
    
    def store_dataset_context(self, user_id: str, chat_id: str, dataset_context: Dict[str, Any]):
        """Store dataset metadata and context"""
        key = self.get_dataset_key(user_id, chat_id)
        try:
            context_data = {
                "table_name": dataset_context.get("table_name"),
                "columns": dataset_context.get("columns", []),
                "column_types": dataset_context.get("column_types", {}),
                "sample_data": dataset_context.get("sample_data", []),
                "row_count": dataset_context.get("row_count", 0),
                "file_name": dataset_context.get("file_name"),
                "upload_timestamp": datetime.utcnow().isoformat(),
                "metadata": dataset_context.get("metadata", {})
            }
            
            # Store with expiration (30 days)
            self.redis_client.setex(
                key,
                timedelta(days=30),
                json.dumps(context_data)
            )
            
        except Exception as e:
            logger.error(f"Error storing dataset context: {e}")
    
    def get_dataset_context(self, user_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve dataset context from Redis"""
        key = self.get_dataset_key(user_id, chat_id)
        try:
            context_json = self.redis_client.get(key)
            if context_json:
                return json.loads(context_json)
            return None
        except Exception as e:
            logger.error(f"Error retrieving dataset context: {e}")
            return None
    
    def clear_dataset_context(self, user_id: str, chat_id: str):
        """Clear dataset context"""
        key = self.get_dataset_key(user_id, chat_id)
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error clearing dataset context: {e}")
    
    # === Utility Methods ===
    
    def get_user_chats(self, user_id: str) -> List[str]:
        """Get all chat IDs for a user"""
        try:
            pattern = f"conversation:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            chat_ids = []
            for key in keys:
                # Extract chat_id from key pattern
                parts = key.split(":")
                if len(parts) >= 3:
                    chat_ids.append(parts[2])
            return list(set(chat_ids))
        except Exception as e:
            logger.error(f"Error getting user chats: {e}")
            return []
    
    def delete_all_user_data(self, user_id: str):
        """Delete all data for a user (conversations + datasets)"""
        try:
            # Delete all conversation keys
            conv_pattern = f"conversation:{user_id}:*"
            conv_keys = self.redis_client.keys(conv_pattern)
            if conv_keys:
                self.redis_client.delete(*conv_keys)
            
            # Delete all dataset keys
            dataset_pattern = f"dataset:{user_id}:*"
            dataset_keys = self.redis_client.keys(dataset_pattern)
            if dataset_keys:
                self.redis_client.delete(*dataset_keys)
                
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get Redis memory usage stats"""
        try:
            info = self.redis_client.info('memory')
            return {
                "used_memory": info.get('used_memory'),
                "used_memory_human": info.get('used_memory_human'),
                "peak_memory": info.get('used_memory_peak'),
                "peak_memory_human": info.get('used_memory_peak_human')
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {}

# Global instance
memory_service = None

def get_memory_service() -> RedisMemoryService:
    """Get singleton instance of memory service"""
    global memory_service
    if memory_service is None:
        memory_service = RedisMemoryService()
    return memory_service