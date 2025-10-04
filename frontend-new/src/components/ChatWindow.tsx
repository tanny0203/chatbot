import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Paperclip, Bot, User } from 'lucide-react';
import type { Chat, Message } from '../types/api';

interface ChatWindowProps {
  chat: Chat | null;
  messages: Message[];
  onSendMessage: (content: string) => void;
  onFileUpload?: (file: File) => Promise<void>;
  loading: boolean;
  onToggleSidebar: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  chat,
  messages,
  onSendMessage,
  onFileUpload,
  loading,
  onToggleSidebar,
}) => {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const messageContent = input.trim();
    setInput('');
    setSending(true);

    try {
      await onSendMessage(messageContent);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !onFileUpload || !chat) return;

    // Validate file type
    const validTypes = ['.csv', '.xlsx', '.xls'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!validTypes.includes(fileExtension)) {
      alert('Please upload a CSV or Excel file (.csv, .xlsx, .xls)');
      return;
    }

    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      alert('File size must be less than 50MB');
      return;
    }

    setUploading(true);
    try {
      await onFileUpload(file);
    } catch (error) {
      console.error('File upload failed:', error);
      alert('File upload failed. Please try again.');
    } finally {
      setUploading(false);
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleAttachClick = () => {
    if (!chat) {
      alert('Please create or select a chat first');
      return;
    }
    fileInputRef.current?.click();
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <button className="sidebar-toggle mobile-only" onClick={onToggleSidebar}>
          <Menu size={20} />
        </button>
        
        <div className="chat-info">
          <h2>{chat?.title || 'Select a chat or start a new one'}</h2>
          <div className="chat-subtitle">
            {chat ? 'Ask questions about your data or upload a dataset' : 'Create a new chat to get started'}
          </div>
        </div>
      </div>

      <div className="messages-container">
        {loading && messages.length === 0 ? (
          <div className="loading-messages">
            <div className="loading-spinner"></div>
            <p>Loading messages...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-icon">
              <Bot size={48} />
            </div>
            <h3>How can I help you today?</h3>
            <p>Send a message to start the conversation</p>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
              >
                <div className="message-avatar">
                  {message.role === 'user' ? (
                    <User size={16} />
                  ) : (
                    <Bot size={16} />
                  )}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {message.content}
                  </div>
                  <div className="message-time">
                    {formatTime(message.created_at)}
                  </div>
                </div>
              </div>
            ))}
            {sending && (
              <div className="message assistant-message">
                <div className="message-avatar">
                  <Bot size={16} />
                </div>
                <div className="message-content">
                  <div className="message-text">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <form onSubmit={handleSubmit} className="message-form">
          <div className="input-wrapper">
            <button 
              type="button" 
              className={`attach-btn ${uploading ? 'uploading' : ''}`}
              onClick={handleAttachClick}
              disabled={uploading}
              title="Upload CSV or Excel file"
            >
              <Paperclip size={16} />
            </button>
            
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".csv,.xlsx,.xls"
              style={{ display: 'none' }}
            />
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={uploading ? "Uploading file..." : "Type a message or upload a dataset..."}
              disabled={sending || uploading}
              className="message-input"
            />
            
            <button
              type="submit"
              disabled={!input.trim() || sending || uploading}
              className="send-btn"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
        
        {uploading && (
          <div className="upload-status">
            <div className="upload-spinner"></div>
            <span>Uploading and processing file...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatWindow;