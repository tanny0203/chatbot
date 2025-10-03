import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Paperclip, Bot, User } from 'lucide-react';
import type { Chat, Message } from '../types/api';

interface ChatWindowProps {
  chat: Chat | null;
  messages: Message[];
  onSendMessage: (content: string) => void;
  loading: boolean;
  onToggleSidebar: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  chat,
  messages,
  onSendMessage,
  loading,
  onToggleSidebar,
}) => {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
            <button type="button" className="attach-btn">
              <Paperclip size={16} />
            </button>
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              disabled={sending}
              className="message-input"
            />
            
            <button
              type="submit"
              disabled={!input.trim() || sending}
              className="send-btn"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatWindow;