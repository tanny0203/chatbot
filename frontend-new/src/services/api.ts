import axios, { type AxiosResponse } from 'axios';
import type {
  User,
  UserLoginDTO,
  UserRegisterDTO,
  AuthResponse,
  Chat,
  CreateChatDTO,
  Message,
  FileResponse,
  NL2SQLRequest,
  NL2SQLResponse,
  UploadResponse,
} from '../types/api';

// Backend URLs
const GO_API_BASE_URL = 'http://localhost:8080';  // Go backend for auth, chats
const PYTHON_API_BASE_URL = 'http://localhost:8000';  // Python FastAPI for NL2SQL

// Create axios instance for Go backend (auth, chat management)
const goApi = axios.create({
  baseURL: GO_API_BASE_URL,
  withCredentials: true, // Important for cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create axios instance for Python backend (NL2SQL, file uploads)
const pythonApi = axios.create({
  baseURL: PYTHON_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include user context for Python API
pythonApi.interceptors.request.use((config) => {
  // Get user ID from localStorage or auth context if needed
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      // Add user_id to requests that need it
      if (config.data && typeof config.data === 'object') {
        config.data.user_id = user.id;
      }
    } catch (error) {
      console.error('Error parsing user from localStorage:', error);
    }
  }
  return config;
});

// Auth API (Go backend)
export const authApi = {
  register: async (userData: UserRegisterDTO): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await goApi.post('/auth/register', userData);
    return response.data;
  },

  login: async (credentials: UserLoginDTO): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await goApi.post('/auth/login', credentials);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response: AxiosResponse<User> = await goApi.get('/auth/me');
    return response.data;
  },

  logout: async (): Promise<void> => {
    // Clear cookie by setting it with past expiration
    document.cookie = 'Authorization=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  },
};

// Chat API (Go backend for chat management)
export const chatApi = {
  getChats: async (): Promise<Chat[]> => {
    const response: AxiosResponse<Chat[]> = await goApi.get('/chats');
    return response.data;
  },

  createChat: async (chatData: CreateChatDTO): Promise<Chat> => {
    const response: AxiosResponse<Chat> = await goApi.post('/chats', chatData);
    return response.data;
  },

  getMessages: async (chatId: string): Promise<Message[]> => {
    const response: AxiosResponse<Message[]> = await goApi.get(`/chats/${chatId}/messages`);
    return response.data;
  },

  // Sending messages is handled by Python NL2SQL backend now.

  getFiles: async (chatId: string): Promise<FileResponse[]> => {
    const response: AxiosResponse<FileResponse[]> = await goApi.get(`/chats/${chatId}/files`);
    return response.data;
  },
};

// NL2SQL API (Python FastAPI backend)
export const nl2sqlApi = {
  // Upload file to Python backend
  uploadFile: async (chatId: string, userId: string, file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    formData.append('chat_id', chatId);
    
    const response: AxiosResponse<UploadResponse> = await pythonApi.post(
      '/api/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Ask NL2SQL question
  askQuestion: async (request: NL2SQLRequest): Promise<NL2SQLResponse> => {
    try {
      const response: AxiosResponse<NL2SQLResponse> = await pythonApi.post('/api/ask', request);
      return response.data;
    } catch (err: any) {
      // Normalize FastAPI HTTPException detail payloads to our NL2SQLResponse shape
      const detail = err?.response?.data?.detail;
      if (detail && typeof detail === 'object') {
        // No dataset case
        if (detail.requires_dataset) {
          return {
            success: false,
            answer: detail.message || 'Please upload a dataset first.',
            requires_dataset: true,
            error: detail.error || 'no_dataset',
          } as NL2SQLResponse;
        }

        // Other processing failures
        return {
          success: false,
          answer: detail.message || 'Processing failed.',
          sql_query: detail.sql_query,
          result_count: 0,
          execution_success: false,
          error: detail.error || 'processing_failed',
        } as NL2SQLResponse;
      }

      // Fallback for network or unexpected errors
      return {
        success: false,
        answer: 'Request to NL2SQL backend failed.',
        error: err?.message || 'unknown_error',
      } as NL2SQLResponse;
    }
  },

  // Get chat history from Python backend
  getChatHistory: async (chatId: string, userId: string, limit?: number): Promise<any> => {
    const params = new URLSearchParams({ user_id: userId });
    if (limit) params.append('limit', limit.toString());
    
    const response = await pythonApi.get(`/chats/${chatId}/history?${params}`);
    return response.data;
  },

  // Create chat in Python backend
  createPythonChat: async (userId: string): Promise<any> => {
    const response = await pythonApi.post('/chats/', { user_id: userId });
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<any> => {
    const response = await pythonApi.get('/health');
    return response.data;
  },
};

// Legacy file upload (for backward compatibility with Go backend)
export const fileApi = {
  uploadFile: async (chatId: string, file: File): Promise<FileResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response: AxiosResponse<FileResponse> = await goApi.post(
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

export default { goApi, pythonApi };