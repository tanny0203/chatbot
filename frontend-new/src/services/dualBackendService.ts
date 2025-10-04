import type { Message, Chat, User } from '../types/api';
import { chatApi, nl2sqlApi } from './api';

/**
 * Service that orchestrates between Go backend (chat management) and Python backend (NL2SQL)
 */
export class DualBackendService {
  private user: User | null = null;

  constructor(user: User | null = null) {
    this.user = user;
  }

  setUser(user: User | null) {
    this.user = user;
  }

  /**
   * Send a message to the Python NL2SQL backend.
   * The Go backend no longer handles message sending.
   */
  async sendMessage(chatId: string, content: string): Promise<Message> {
    if (!this.user) {
      throw new Error('User not authenticated');
    }

    try {
      // Send to Python NL2SQL backend
      const nl2sqlResponse = await nl2sqlApi.askQuestion({
        question: content,
        user_id: this.user.id,
        chat_id: chatId,
      });

      if (nl2sqlResponse.success) {
        // If successful, create a Message object from the NL2SQL response
        const assistantMessage: Message = {
          id: `nl2sql-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: this.formatNL2SQLResponse(nl2sqlResponse),
          created_at: new Date().toISOString(),
        };

        return assistantMessage;
      } else if (nl2sqlResponse.requires_dataset) {
        // If no dataset is uploaded, return a helpful message
        const helpMessage: Message = {
          id: `help-${Date.now()}`,
          role: 'assistant',
          content: nl2sqlResponse.error || 'Please upload a dataset first before asking questions about your data.',
          created_at: new Date().toISOString(),
        };

        return helpMessage;
      } else {
        throw new Error('NL2SQL request failed');
      }
    } catch (error) {
      console.error('NL2SQL backend failed:', error);
      throw error;
    }
  }

  /**
   * Upload a file to the Python backend and handle the response
   */
  async uploadFile(chatId: string, file: File): Promise<{
    success: boolean;
    message: string;
    fileInfo?: any;
  }> {
    if (!this.user) {
      throw new Error('User not authenticated');
    }

    try {
      const uploadResponse = await nl2sqlApi.uploadFile(chatId, this.user.id, file);
      
      if (uploadResponse.success) {
        // Create a system message about the successful upload
  // Note: We no longer persist assistant/system messages via Go backend.
  // Surface success via UI by returning success=true.

        return {
          success: true,
          message: 'File uploaded successfully',
          fileInfo: uploadResponse,
        };
      } else {
        throw new Error(uploadResponse.message || 'Upload failed');
      }
    } catch (error) {
      console.error('File upload failed:', error);
      
  // No Go backend storage for errors; surface via return value only

      return {
        success: false,
        message: error instanceof Error ? error.message : 'Upload failed',
      };
    }
  }

  /**
   * Get comprehensive chat history from both backends
   */
  async getChatHistory(chatId: string): Promise<Message[]> {
    try {
      if (!this.user) return [];
      const pythonHistory = await nl2sqlApi.getChatHistory(chatId, this.user.id, 50);
      if (pythonHistory && pythonHistory.success && Array.isArray(pythonHistory.history)) {
        // Map python history to Message interface if formats differ
        const messages: Message[] = pythonHistory.history.map((h: any, idx: number) => ({
          id: h.id || `py-${idx}-${Date.now()}`,
          role: h.role || h.type || (h.is_user ? 'user' : 'assistant'),
          content: h.content || h.text || '',
          created_at: h.created_at || new Date().toISOString(),
        }));
        return messages;
      }
      return [];
    } catch (error) {
      console.error('Failed to get Python chat history:', error);
      return [];
    }
  }

  /**
   * Create a new chat in both backends
   */
  async createChat(title: string): Promise<Chat> {
    try {
      // Create chat in Go backend (primary)
      const goChat = await chatApi.createChat({ title });
      
      // Optionally create corresponding chat in Python backend
      if (this.user) {
        try {
          await nl2sqlApi.createPythonChat(this.user.id);
        } catch (error) {
          console.warn('Failed to create chat in Python backend:', error);
          // Continue anyway, as Go backend chat is the primary one
        }
      }

      return goChat;
    } catch (error) {
      console.error('Failed to create chat:', error);
      throw error;
    }
  }

  /**
   * Check health of both backends
   */
  async healthCheck(): Promise<{
    goBackend: boolean;
    pythonBackend: boolean;
    overall: boolean;
  }> {
    let goHealthy = false;
    let pythonHealthy = false;

    try {
      // Check Go backend (try to get chats)
      await chatApi.getChats();
      goHealthy = true;
    } catch (error) {
      console.warn('Go backend health check failed:', error);
    }

    try {
      // Check Python backend
      await nl2sqlApi.healthCheck();
      pythonHealthy = true;
    } catch (error) {
      console.warn('Python backend health check failed:', error);
    }

    return {
      goBackend: goHealthy,
      pythonBackend: pythonHealthy,
      overall: goHealthy && pythonHealthy,
    };
  }

  /**
   * Format NL2SQL response for display
   */
  private formatNL2SQLResponse(response: any): string {
    let content = response.answer;

    // Add SQL query if available (for debugging/transparency)
    if (response.sql_query && response.execution_success) {
      content += `\n\n📊 Query executed: \`${response.sql_query}\``;
    }

    // Add result count if available
    if (response.result_count !== undefined) {
      if (response.result_count === 0) {
        content += '\n\n📋 No results found.';
      } else {
        content += `\n\n📋 Found ${response.result_count.toLocaleString()} result${response.result_count === 1 ? '' : 's'}.`;
      }
    }

    return content;
  }
}

// Global instance
let dualBackendService: DualBackendService | null = null;

export const getDualBackendService = (user?: User | null): DualBackendService => {
  if (!dualBackendService) {
    dualBackendService = new DualBackendService(user);
  } else if (user !== undefined) {
    dualBackendService.setUser(user);
  }
  return dualBackendService;
};

export default DualBackendService;