import axios, { type AxiosResponse } from 'axios';
import type { 
  User, 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse,
  Chat,
  CreateChatRequest,
  CreateChatResponse,
  SendMessageRequest,
  SendMessageResponse,
  ApiResponse
} from '../types/api';

const API_BASE_URL = 'http://localhost:8080';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important for cookie-based auth
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to handle auth
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access - redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<ApiResponse<AuthResponse>> => {
    try {
      const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/login', credentials);
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Login failed' };
    }
  },

  register: async (userData: RegisterRequest): Promise<ApiResponse<AuthResponse>> => {
    try {
      const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/register', userData);
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Registration failed' };
    }
  },

  logout: async (): Promise<ApiResponse<AuthResponse>> => {
    try {
      const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/logout');
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Logout failed' };
    }
  },

  getCurrentUser: async (): Promise<ApiResponse<User>> => {
    try {
      const response: AxiosResponse<User> = await apiClient.get('/auth/me');
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Failed to get user info' };
    }
  }
};

// Chat API
export const chatAPI = {
  createChat: async (chatData: CreateChatRequest): Promise<ApiResponse<CreateChatResponse>> => {
    try {
      const response: AxiosResponse<CreateChatResponse> = await apiClient.post('/chats', chatData);
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Failed to create chat' };
    }
  },

  getChat: async (chatId: string): Promise<ApiResponse<Chat>> => {
    try {
      const response: AxiosResponse<Chat> = await apiClient.get(`/chats/${chatId}`);
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Failed to get chat' };
    }
  },

  getAllChats: async (): Promise<ApiResponse<Chat[]>> => {
    try {
      const response: AxiosResponse<Chat[]> = await apiClient.get('/chats');
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Failed to get chats' };
    }
  },

  sendMessage: async (chatId: string, messageData: SendMessageRequest): Promise<ApiResponse<SendMessageResponse>> => {
    try {
      const response: AxiosResponse<SendMessageResponse> = await apiClient.post(`/chats/${chatId}/message`, messageData);
      return { data: response.data };
    } catch (error: any) {
      return { error: error.response?.data?.error || 'Failed to send message' };
    }
  }
};

export default apiClient;