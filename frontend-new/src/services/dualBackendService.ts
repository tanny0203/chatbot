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
   * Send a message that might be an NL2SQL query
   * First tries Python backend for NL2SQL, falls back to Go backend for regular chat
   */
  async sendMessage(chatId: string, content: string): Promise<Message> {
    if (!this.user) {
      throw new Error('User not authenticated');
    }

    try {
      // First, try to send to Python NL2SQL backend
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

        // Also store the message in the Go backend for chat history
        try {
          await chatApi.sendMessage(chatId, { content });
          await chatApi.sendMessage(chatId, { content: assistantMessage.content });
        } catch (error) {
          console.warn('Failed to store message in Go backend:', error);
          // Continue anyway, as the NL2SQL response is the primary concern
        }

        return assistantMessage;
      } else if (nl2sqlResponse.requires_dataset) {
        // If no dataset is uploaded, return a helpful message
        const helpMessage: Message = {
          id: `help-${Date.now()}`,
          role: 'assistant',
          content: nl2sqlResponse.error || 'Please upload a dataset first before asking questions about your data.',
          created_at: new Date().toISOString(),
        };

        // Store in Go backend
        try {
          await chatApi.sendMessage(chatId, { content });
          await chatApi.sendMessage(chatId, { content: helpMessage.content });
        } catch (error) {
          console.warn('Failed to store help message in Go backend:', error);
        }

        return helpMessage;
      } else {
        // If NL2SQL failed for other reasons, fall back to Go backend
        return await chatApi.sendMessage(chatId, { content });
      }
    } catch (error) {
      console.warn('NL2SQL backend failed, falling back to Go backend:', error);
      
      // Fall back to Go backend for regular chat
      try {
        return await chatApi.sendMessage(chatId, { content });
      } catch (goError) {
        console.error('Both backends failed:', { nl2sqlError: error, goError });
        throw new Error('Failed to send message to both backends');
      }
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
        const systemMessage = `📊 Dataset "${uploadResponse.filename}" uploaded successfully! 
        
Table: ${uploadResponse.table_name}
Rows: ${uploadResponse.rows.toLocaleString()}
Columns: ${uploadResponse.columns}

You can now ask questions about your data.`;

        // Store the system message in Go backend for chat history
        try {
          await chatApi.sendMessage(chatId, { content: systemMessage });
        } catch (error) {
          console.warn('Failed to store upload message in Go backend:', error);
        }

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
      
      // Create error message
      const errorMessage = `❌ File upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`;
      
      // Store error message in Go backend
      try {
        await chatApi.sendMessage(chatId, { content: errorMessage });
      } catch (chatError) {
        console.warn('Failed to store error message in Go backend:', chatError);
      }

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
      // Get messages from Go backend (primary chat history)
      const goMessages = await chatApi.getMessages(chatId);
      
      // Optionally, get NL2SQL history for additional context
      if (this.user) {
        try {
          const pythonHistory = await nl2sqlApi.getChatHistory(chatId, this.user.id, 10);
          if (pythonHistory.success && pythonHistory.history) {
            // Merge or supplement with Python history if needed
            // For now, we'll primarily use Go backend messages
            console.log('Python history available:', pythonHistory.history.length, 'messages');
          }
        } catch (error) {
          console.warn('Failed to get Python history:', error);
        }
      }

      return goMessages;
    } catch (error) {
      console.error('Failed to get chat history:', error);
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