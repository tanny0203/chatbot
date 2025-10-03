
import React, { useState, useEffect } from 'react';
import { chatAPI } from '../services/api';
import type { Chat } from '../types/api';

interface ChatListProps {
  selectedChatId?: string | null;
  onChatSelect?: (chatId: string) => void;
  refreshTrigger?: number; // Add this to trigger refresh when new chat is created
}

const ChatList: React.FC<ChatListProps> = ({ selectedChatId, onChatSelect, refreshTrigger }) => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadChats();
  }, [refreshTrigger]);

  const loadChats = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await chatAPI.getAllChats();
      
      if (response.data) {
        // Sort chats by updated_at (most recent first)
        const sortedChats = response.data.sort((a, b) => 
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
        setChats(sortedChats);
      } else if (response.error) {
        // For now, show empty state instead of error to avoid blocking the UI
        console.warn('Backend not available, showing empty state:', response.error);
        setChats([]);
      }
    } catch (error) {
      // For now, show empty state instead of error to avoid blocking the UI
      console.warn('Backend not available, showing empty state:', error);
      setChats([]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return 'Today';
    } else if (diffDays === 2) {
      return 'Yesterday';
    } else if (diffDays <= 7) {
      return `${diffDays - 1} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getLastMessage = (chat: Chat) => {
    if (chat.messages && chat.messages.length > 0) {
      const lastMessage = chat.messages[chat.messages.length - 1];
      return lastMessage.content.length > 50 
        ? lastMessage.content.substring(0, 50) + '...'
        : lastMessage.content;
    }
    return 'No messages yet';
  };

  if (isLoading) {
    return (
      <div className="chat-list-loading">
        <div className="loading-spinner-small"></div>
        <span>Loading chats...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chat-list-error">
        <div className="error-icon">⚠️</div>
        <span>{error}</span>
        <button onClick={loadChats} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  if (chats.length === 0) {
    return (
      <div className="chat-list-empty">
        <div className="empty-icon">💬</div>
        <span>No chats yet</span>
        <p>Create your first chat to get started!</p>
      </div>
    );
  }

  return (
    <div className="gemini-chat-list">
      {chats.map((chat) => (
        <div
          key={chat.id}
          className={`chat-item ${selectedChatId === chat.id ? 'active' : ''}`}
          onClick={() => onChatSelect?.(chat.id)}
        >
          <div className="chat-item-content">
            <div className="chat-title">{chat.title}</div>
            <div className="chat-preview">{getLastMessage(chat)}</div>
          </div>
          <div className="chat-time">{formatDate(chat.updated_at)}</div>
        </div>
      ))}
    </div>
  );
};

export default ChatList;
