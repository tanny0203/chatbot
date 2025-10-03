import React, { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../services/api';
import type { Chat } from '../types/api';

interface ChatWindowProps {
  selectedChatId?: string | null;
  onNewChat?: () => void;
  onNavigateToChat?: (chatId: string) => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ selectedChatId = null, onNewChat, onNavigateToChat }) => {
  const [chatData, setChatData] = useState<Chat | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [inputValue, setInputValue] = useState(''); // For welcome screen input
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatData?.messages]);

  // Load chat data when selectedChatId changes
  useEffect(() => {
    if (selectedChatId) {
      loadChat(selectedChatId);
    } else {
      setChatData(null);
      setError(null);
    }
  }, [selectedChatId]);

  const loadChat = async (chatId: string) => {
    setIsLoadingChat(true);
    setError(null);
    
    try {
      const response = await chatAPI.getChat(chatId);
      
      if (response.data) {
        setChatData(response.data);
      } else if (response.error) {
        setError(response.error);
        console.error('Failed to load chat:', response.error);
      }
    } catch (error) {
      setError('Failed to load chat. Please try again.');
      console.error('Error loading chat:', error);
    } finally {
      setIsLoadingChat(false);
    }
  };

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !selectedChatId || isSendingMessage) return;

    const messageContent = messageInput.trim();
    setMessageInput('');
    setIsSendingMessage(true);
    setError(null);

    try {
      const response = await chatAPI.sendMessage(selectedChatId, { content: messageContent });
      
      if (response.data) {
        // Reload the chat to get the updated messages
        await loadChat(selectedChatId);
      } else if (response.error) {
        setError(response.error);
        setMessageInput(messageContent); // Restore message on error
        console.error('Failed to send message:', response.error);
      }
    } catch (error) {
      setError('Failed to send message. Please try again.');
      setMessageInput(messageContent); // Restore message on error
      console.error('Error sending message:', error);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (selectedChatId) {
        // Handle existing chat
        handleSendMessage();
      } else {
        // Handle new chat creation
        handleWelcomeMessage();
      }
    }
  };

  const handleWelcomeMessage = async () => {
    console.log('handleWelcomeMessage called with inputValue:', inputValue);
    if (!inputValue.trim()) return;
    
    try {
      setIsSendingMessage(true);
      console.log('Creating new chat...');
      
      // Create new chat first
      const newChatResponse = await chatAPI.createChat({ title: 'New Chat' });
      console.log('New chat response:', newChatResponse);
      
      if (newChatResponse.data) {
        console.log('Sending message to chat:', newChatResponse.data.id);
        // Send the first message
        const messageResponse = await chatAPI.sendMessage(newChatResponse.data.id, { content: inputValue });
        console.log('Message response:', messageResponse);
        
        if (messageResponse.data) {
          // Clear welcome input
          setInputValue('');
          
          // Navigate to the new chat
          if (onNavigateToChat) {
            console.log('Navigating to chat:', newChatResponse.data.id);
            onNavigateToChat(newChatResponse.data.id);
          }
          
          // Notify parent to refresh chat list
          if (onNewChat) {
            console.log('Calling onNewChat');
            onNewChat();
          }
        } else {
          console.error('Failed to send message:', messageResponse.error);
          setError('Failed to send message');
        }
      } else {
        console.error('Failed to create chat:', newChatResponse.error);
        setError('Failed to create new chat');
      }
    } catch (error) {
      console.error('Error creating new chat:', error);
      setError('Failed to create new chat');
    } finally {
      setIsSendingMessage(false);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Show welcome screen if no chat selected
  if (!selectedChatId) {
    return (
      <div className="chat-window-classic">
        <div className="welcome-area-classic">
          <div className="welcome-container-classic">
            <div className="welcome-header-classic">
              <div className="classic-logo">
                <div className="logo-circle">
                  <span className="logo-text">CX</span>
                </div>
                <div className="logo-details">
                  <h1 className="app-title">ChatXL</h1>
                </div>
              </div>
            </div>
            
            <div className="welcome-content-classic">
              <div className="greeting-section">
                <h2 className="greeting-title">Welcome to ChatXL</h2>
                <p className="greeting-text">
                  Start your conversation with AI assistance.
                </p>
              </div>
              
              <div className="action-section">
                <button 
                  onClick={() => {
                    console.log('Start Chat button clicked');
                    inputRef.current?.focus();
                  }} 
                  className="primary-action-btn"
                >
                  <span className="btn-icon">✨</span>
                  Start Chat
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Welcome Input Area - Always Visible for immediate interaction */}
        <div className="input-area-classic">
          <div className="input-container-classic">
            <div className="input-wrapper-classic">
              <textarea
                ref={inputRef}
                className="message-input-classic"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message to start a new chat..."
                rows={1}
                disabled={isSendingMessage}
              />
              <button
                className="send-button-classic"
                onClick={handleWelcomeMessage}
                disabled={!inputValue.trim() || isSendingMessage}
              >
                <span className="send-icon-classic">
                  {isSendingMessage ? '⏳' : '→'}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show loading state while loading chat
  if (isLoadingChat) {
    return (
      <div className="chat-window-classic">
        <div className="welcome-area-classic">
          <div className="welcome-container-classic">
            <div className="loading-content">
              <div className="loading-spinner"></div>
              <h2 className="greeting-title">Loading your conversation...</h2>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error && !chatData) {
    return (
      <div className="chat-window-classic">
        <div className="welcome-area-classic">
          <div className="welcome-container-classic">
            <div className="welcome-content-classic">
              <div className="greeting-section">
                <h2 className="greeting-title">Oops! Something went wrong</h2>
                <p className="greeting-text">{error}</p>
              </div>
              <div className="action-section">
                <button 
                  onClick={() => selectedChatId && loadChat(selectedChatId)} 
                  className="primary-action-btn"
                >
                  <span className="btn-icon">🔄</span>
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show chat interface
  return (
    <div className="chat-window-classic">
      <div className="chat-header-classic">
        <div className="chat-title-section">
          <div className="status-indicator"></div>
          <div className="chat-details">
            <h3 className="chat-name">{chatData?.title || `Chat ${selectedChatId}`}</h3>
            <span className="chat-status">
              {chatData?.messages.length || 0} messages
            </span>
          </div>
        </div>
        <div className="chat-actions">
          <button className="header-btn" title="Chat Settings">
            ⚙️
          </button>
          <button className="header-btn" title="More Options">
            ⋮
          </button>
        </div>
      </div>
      
      <div className="messages-area-classic">
        {chatData?.messages.map((message) => (
          <div key={message.id} className="message-classic">
            <div className="message-avatar-classic">
              {message.role === 'user' ? 'U' : 'AI'}
            </div>
            <div className="message-bubble-classic">
              <div className="message-content-classic">
                <p>{message.content}</p>
              </div>
              <div className="message-meta">
                <span className="message-time">{formatTime(message.created_at)}</span>
              </div>
            </div>
          </div>
        ))}
        
        {isSendingMessage && (
          <div className="message-classic">
            <div className="message-avatar-classic">
              <span style={{ opacity: 0.7 }}>AI</span>
            </div>
            <div className="message-bubble-classic">
              <div className="message-content-classic">
                <p style={{ opacity: 0.7, fontStyle: 'italic' }}>
                  Composing a thoughtful response...
                </p>
              </div>
            </div>
          </div>
        )}
        
        {error && (
          <div className="message-classic">
            <div className="message-avatar-classic" style={{ background: '#e53e3e' }}>
              ⚠️
            </div>
            <div className="message-bubble-classic">
              <div className="message-content-classic">
                <p style={{ color: '#e53e3e' }}>{error}</p>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-area-classic">
        <div className="input-container-classic">
          <div className="input-wrapper-classic">
            <textarea
              ref={inputRef}
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Share your thoughts with elegance..."
              className="message-input-classic"
              rows={1}
              disabled={isSendingMessage}
            />
            <button 
              onClick={handleSendMessage}
              className="send-button-classic"
              disabled={!messageInput.trim() || isSendingMessage}
            >
              <span className="send-icon-classic">
                {isSendingMessage ? '⏳' : '→'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;