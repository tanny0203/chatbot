import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { chatApi } from '../services/api';
import ChatSidebar from './ChatSidebar';
import ChatWindow from './ChatWindow';
import NewChatModal from './NewChatModal';
import type { Chat, Message } from '../types/api';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { chatId } = useParams();
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showNewChatModal, setShowNewChatModal] = useState(false);

  useEffect(() => {
    loadChats();
  }, []);

  useEffect(() => {
    if (selectedChat) {
      loadMessages(selectedChat.id);
    }
  }, [selectedChat]);

  useEffect(() => {
    if (chatId && chats.length > 0) {
      const chat = chats.find(c => c.id === chatId);
      if (chat && chat.id !== selectedChat?.id) {
        setSelectedChat(chat);
      }
    } else if (!chatId) {
      // If no chatId in URL, clear selected chat
      setSelectedChat(null);
      setMessages([]);
    }
  }, [chatId, chats, selectedChat]);

  const loadChats = async () => {
    try {
      const chatData = await chatApi.getChats();
      setChats(chatData);
    } catch (error) {
      console.error('Failed to load chats:', error);
    }
  };

  const loadMessages = async (chatId: string) => {
    setLoading(true);
    try {
      const messageData = await chatApi.getMessages(chatId);
      setMessages(messageData);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewChat = async (title: string) => {
    try {
      const newChat = await chatApi.createChat({ title });
      setChats([newChat, ...chats]);
      navigate(`/c/${newChat.id}`);
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  const selectChat = (chat: Chat) => {
    navigate(`/c/${chat.id}`);
  };

  const openNewChatModal = () => {
    setShowNewChatModal(true);
  };

  const sendMessage = async (content: string) => {
    let chatToUse = selectedChat;
    
    if (!chatToUse) {
      // Create a new chat first if none is selected
      try {
        const newChat = await chatApi.createChat({ title: 'New Chat' });
        setChats([newChat, ...chats]);
        setMessages([]); // Clear previous messages
        navigate(`/c/${newChat.id}`);
        chatToUse = newChat;
      } catch (error) {
        console.error('Failed to create chat:', error);
        return;
      }
    }

    // Create user message object and add it immediately to the UI
    const userMessage: Message = {
      id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, // Unique temporary ID
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    };

    // Add user message to state immediately
    setMessages(prevMessages => [...prevMessages, userMessage]);

    try {
      // Send message to API and get response
      const assistantMessage = await chatApi.sendMessage(chatToUse.id, { content });
      
      // Add assistant response to messages
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
      
      // Reload chats to update the latest activity
      loadChats();
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove the user message if sending failed
      setMessages(prevMessages => prevMessages.filter(msg => msg.id !== userMessage.id));
    }
  };

  return (
    <div className="dashboard">
      <ChatSidebar
        chats={chats}
        selectedChat={selectedChat}
        onSelectChat={selectChat}
        onNewChat={openNewChatModal}
        user={user}
        onLogout={logout}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      
      <div className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <ChatWindow
          chat={selectedChat}
          messages={messages}
          onSendMessage={sendMessage}
          loading={loading}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
      </div>

      <NewChatModal
        isOpen={showNewChatModal}
        onClose={() => setShowNewChatModal(false)}
        onCreateChat={createNewChat}
      />
    </div>
  );
};

export default Dashboard;