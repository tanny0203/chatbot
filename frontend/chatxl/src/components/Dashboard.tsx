import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { chatAPI } from '../services/api';
import ChatList from './ChatList';
import ChatWindow from './ChatWindow';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { chatId } = useParams<{ chatId: string }>();
  const { user, logout } = useAuth();
  const [selectedChatId, setSelectedChatId] = useState<string | null>(chatId || null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const [chatListRefresh, setChatListRefresh] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  // Sync selectedChatId with URL parameter
  useEffect(() => {
    setSelectedChatId(chatId || null);
  }, [chatId]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleChatSelect = (chatId: string) => {
    setSelectedChatId(chatId);
    setSidebarOpen(false);
    navigate(`/chat/${chatId}`);
  };

  const handleNavigateToChat = (chatId: string) => {
    setSelectedChatId(chatId);
    setSidebarOpen(false);
    setChatListRefresh(prev => prev + 1); // Trigger chat list refresh
    navigate(`/chat/${chatId}`);
  };

  const handleNewChat = async () => {
    if (isCreatingChat) return;
    
    try {
      setIsCreatingChat(true);
      const response = await chatAPI.createChat({ title: 'New Chat' });
      
      if (response.data) {
        const newChatId = response.data.id;
        setSelectedChatId(newChatId);
        setSidebarOpen(false);
        setChatListRefresh(prev => prev + 1); // Trigger chat list refresh
        navigate(`/chat/${newChatId}`);
      } else if (response.error) {
        console.error('Failed to create chat:', response.error);
        // You can add a toast notification here later
        alert('Failed to create new chat. Please try again.');
      }
    } catch (error) {
      console.error('Error creating chat:', error);
      alert('Failed to create new chat. Please try again.');
    } finally {
      setIsCreatingChat(false);
    }
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <h2>ChatXL</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="gemini-layout enhanced">
      {/* Sidebar */}
      <div className={`gemini-sidebar enhanced-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="gemini-sidebar-header enhanced-header">
          <div className="brand-logo">
            <span className="brand-icon">💬</span>
            <h2>ChatXL</h2>
          </div>
          <button onClick={toggleSidebar} className="sidebar-close enhanced-close">
            ✕
          </button>
        </div>
        
        <button 
          onClick={handleNewChat} 
          className="gemini-new-chat enhanced-new-chat"
          disabled={isCreatingChat}
        >
          <span>{isCreatingChat ? '⟳' : '+'}</span>
          {isCreatingChat ? 'Creating...' : 'New Chat'}
        </button>
        
        <div className="gemini-chat-list enhanced-chat-list">
          <ChatList 
            selectedChatId={selectedChatId} 
            onChatSelect={handleChatSelect}
            refreshTrigger={chatListRefresh}
          />
        </div>
        
        <div className="gemini-user-section enhanced-user-section">
          <div className="user-info enhanced-user-info">
            <div className="user-avatar">
              {(user?.name || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
            <span>{user?.name || user?.email}</span>
          </div>
          <button onClick={handleLogout} className="gemini-logout enhanced-logout">
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="gemini-main enhanced-main">
        {/* Header */}
        <div className="gemini-header enhanced-gemini-header">
          <button onClick={toggleSidebar} className="sidebar-toggle enhanced-toggle">
            ☰
          </button>
          <div className="header-spacer">
            {/* Spacer for better layout balance */}
          </div>
          <div className="header-actions enhanced-actions">
            <button 
              onClick={handleNewChat} 
              className="header-new-chat enhanced-header-new"
              disabled={isCreatingChat}
            >
              <span>{isCreatingChat ? '⟳' : '+'}</span>
              {isCreatingChat ? 'Creating...' : 'New'}
            </button>
          </div>
        </div>

        {/* Chat Area */}
        <div className="gemini-chat-area enhanced-chat-area">
          <ChatWindow 
            selectedChatId={selectedChatId} 
            onNewChat={handleNewChat}
            onNavigateToChat={handleNavigateToChat}
          />
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && <div className="sidebar-overlay enhanced-overlay" onClick={toggleSidebar}></div>}
    </div>
  );
};

export default Dashboard;