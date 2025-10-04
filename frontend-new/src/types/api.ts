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

// NL2SQL Types (for Python FastAPI backend)
export interface NL2SQLRequest {
  question: string;
  user_id: string;
  chat_id: string;
}

export interface NL2SQLResponse {
  success: boolean;
  answer: string;
  sql_query?: string;
  result_count?: number;
  execution_success?: boolean;
  error?: string;
  requires_dataset?: boolean;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  file_id: string;
  table_name: string;
  rows: number;
  columns: number;
  filename: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status?: string;
}