import axios, { type AxiosResponse } from 'axios';
import type {
  User,
  UserLoginDTO,
  UserRegisterDTO,
  AuthResponse,
  Chat,
  CreateChatDTO,
  Message,
  SendMessageDTO,
  FileResponse,
} from '../types/api';

const API_BASE_URL = 'http://localhost:8080';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important for cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth API
export const authApi = {
  register: async (userData: UserRegisterDTO): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/auth/register', userData);
    return response.data;
  },

  login: async (credentials: UserLoginDTO): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/auth/login', credentials);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response: AxiosResponse<User> = await api.get('/auth/me');
    return response.data;
  },

  logout: async (): Promise<void> => {
    // Clear cookie by setting it with past expiration
    document.cookie = 'Authorization=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  },
};

// Chat API
export const chatApi = {
  getChats: async (): Promise<Chat[]> => {
    const response: AxiosResponse<Chat[]> = await api.get('/chats');
    return response.data;
  },

  createChat: async (chatData: CreateChatDTO): Promise<Chat> => {
    const response: AxiosResponse<Chat> = await api.post('/chats', chatData);
    return response.data;
  },

  getMessages: async (chatId: string): Promise<Message[]> => {
    const response: AxiosResponse<Message[]> = await api.get(`/chats/${chatId}/messages`);
    return response.data;
  },

  sendMessage: async (chatId: string, messageData: SendMessageDTO): Promise<Message> => {
    const response: AxiosResponse<Message> = await api.post(`/chats/${chatId}/messages`, messageData);
    return response.data;
  },

  getFiles: async (chatId: string): Promise<FileResponse[]> => {
    const response: AxiosResponse<FileResponse[]> = await api.get(`/chats/${chatId}/files`);
    return response.data;
  },

  uploadFile: async (chatId: string, file: File): Promise<FileResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response: AxiosResponse<FileResponse> = await api.post(
      `/chats/${chatId}/files`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};

export default api;