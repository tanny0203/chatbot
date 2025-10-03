// User types
export interface User {
  id: string;
  email: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  status: string;
}

// Chat types
export interface Chat {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface CreateChatRequest {
  title: string;
}

export interface CreateChatResponse {
  id: string;
  title: string;
  created_at: string;
}

// Message types
export interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface SendMessageRequest {
  content: string;
}

export interface SendMessageResponse {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

// API Response wrappers
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status?: string;
}