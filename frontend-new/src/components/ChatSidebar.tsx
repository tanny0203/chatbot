import React from 'react';
import { Plus, MessageSquare, User, LogOut, Menu, X } from 'lucide-react';
import type { Chat, User as UserType } from '../types/api';

interface ChatSidebarProps {
  chats: Chat[];
  selectedChat: Chat | null;
  onSelectChat: (chat: Chat) => void;
  onNewChat: () => void;
  user: UserType | null;
  onLogout: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  chats,
  selectedChat,
  onSelectChat,
  onNewChat,
  user,
  onLogout,
  isOpen,
  onToggle,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div className="sidebar-overlay" onClick={onToggle} />
      )}
      
      <div className={`sidebar ${isOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="sidebar-header">
          <button className="sidebar-toggle desktop-hidden" onClick={onToggle}>
            <X size={20} />
          </button>
          
          <button className="new-chat-btn" onClick={onNewChat}>
            <Plus size={16} />
            New chat
          </button>
        </div>

        <div className="chat-list">
          {chats.length === 0 ? (
            <div className="empty-state">
              <MessageSquare size={32} className="empty-icon" />
              <p>No conversations yet</p>
              <p className="empty-subtitle">Start a new chat to begin</p>
            </div>
          ) : (
            chats.map((chat) => (
              <button
                key={chat.id}
                className={`chat-item ${selectedChat?.id === chat.id ? 'active' : ''}`}
                onClick={() => onSelectChat(chat)}
              >
                <div className="chat-item-content">
                  <div className="chat-title">{chat.title}</div>
                  <div className="chat-date">{formatDate(chat.created_at)}</div>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              <User size={16} />
            </div>
            <div className="user-details">
              <div className="user-name">{user?.name || 'User'}</div>
              <div className="user-email">{user?.email}</div>
            </div>
          </div>
          
          <button className="logout-btn" onClick={onLogout}>
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </>
  );
};

export default ChatSidebar;