// User Types
export interface User {
  id: string;
  name: string;
  email: string;
}

export interface UserLoginDTO {
  email: string;
  password: string;
}

export interface UserRegisterDTO {
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  status: string;
  user?: User;
  token: string;
}

// Chat Types
export interface Chat {
  id: string;
  title: string;
  created_at: string;
}

export interface CreateChatDTO {
  title: string;
}

// Message Types
export interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface SendMessageDTO {
  content: string;
}

// File Types
export interface FileResponse {
  id: string;
  filename: string;
  table_name: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status?: string;
}