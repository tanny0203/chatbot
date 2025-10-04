# Dual Backend Setup - Frontend Configuration

This frontend now connects to **two backends** for a complete NL2SQL chat application:

## 🏗️ Backend Architecture

### 1. **Go Backend** (Port 8080)
- **Authentication**: Login, register, logout
- **Chat Management**: Create chats, get chat list, basic chat history
- **User Management**: User profile, sessions

### 2. **Python FastAPI Backend** (Port 8000)
- **NL2SQL Processing**: Natural language to SQL queries
- **File Upload**: CSV/Excel dataset processing
- **Data Analysis**: Statistical analysis and insights
- **Memory Management**: Redis-based conversation context

## 🔄 Request Flow

### Authentication & Chat Management
```
Frontend → Go Backend (8080)
- POST /auth/login
- POST /auth/register
- GET /chats
- POST /chats
```

### NL2SQL & File Upload
```
Frontend → Python FastAPI (8000)
- POST /api/upload (file upload)
- POST /api/ask (NL2SQL questions)
- GET /chats/{chat_id}/history (conversation context)
```

### Message Processing
1. **User sends message** → Frontend
2. **Frontend tries Python backend first** (NL2SQL)
   - If successful: Returns AI answer with SQL insights
   - If no dataset: Returns helpful message
   - If fails: Falls back to Go backend
3. **Messages stored in both backends** for consistency

## 🚀 Quick Start

### 1. Start Go Backend
```bash
cd backend/go-backend
go run main.go
# Runs on http://localhost:8080
```

### 2. Start Python FastAPI Backend
```bash
cd backend/python-nl2sql
python main.py
# Runs on http://localhost:8000
```

### 3. Start Frontend
```bash
cd frontend-new
npm run dev
# Runs on http://localhost:5173
```

## 📋 Testing the Integration

### 1. **Authentication** (Go Backend)
- Register a new user
- Login with credentials
- Verify session management

### 2. **Chat Creation** (Go Backend → Python Backend)
- Create a new chat
- Chat ID is synchronized between backends

### 3. **File Upload** (Python Backend)
- Click the paperclip icon (📎)
- Upload a CSV or Excel file
- File is processed and stored with metadata
- Success message appears in chat

### 4. **NL2SQL Queries** (Python Backend)
- After uploading data, ask questions like:
  - "Show me the top 10 records"
  - "What's the average value in column X?"
  - "How many rows are in the dataset?"
- Responses include natural language answers + SQL queries

### 5. **Fallback to Regular Chat** (Go Backend)
- If no dataset is uploaded, questions go to Go backend
- Regular chat functionality preserved

## 🔧 API Configuration

The frontend automatically routes requests to the appropriate backend:

```typescript
// Go Backend (8080) - Auth & Chat Management
const goApi = axios.create({
  baseURL: 'http://localhost:8080',
  withCredentials: true, // For cookies
});

// Python Backend (8000) - NL2SQL & File Upload
const pythonApi = axios.create({
  baseURL: 'http://localhost:8000',
  // User context added via interceptor
});
```

## 📊 Example Workflow

1. **Login** → Go Backend authenticates user
2. **Create Chat** → Go Backend creates chat, Python backend is notified
3. **Upload Dataset** → Python backend processes file, stores metadata
4. **Ask "Top 5 sales"** → Python backend:
   - Generates SQL: `SELECT * FROM user_123_sales ORDER BY amount DESC LIMIT 5`
   - Executes query safely
   - Returns: "Here are your top 5 sales: Alice ($5000), Bob ($4500)..."
5. **Chat History** → Combined from both backends

## 🛠️ Features

### File Upload
- **Supported formats**: CSV, XLSX, XLS
- **Size limit**: 50MB
- **Processing**: Automatic metadata extraction
- **Storage**: PostgreSQL with user isolation
- **Feedback**: Real-time upload progress

### NL2SQL Processing
- **Models**: SQLCoder + Llama 3.2
- **Context**: Conversation history + dataset schema
- **Safety**: Read-only queries, user isolation
- **Memory**: Redis-based conversation persistence

### Error Handling
- **Graceful fallback**: Python → Go backend
- **User feedback**: Clear error messages
- **Retry logic**: Automatic error recovery

## 🔍 Debugging

### Check Backend Health
- Go Backend: `GET http://localhost:8080/health`
- Python Backend: `GET http://localhost:8000/health`

### Monitor Network Requests
- Open browser dev tools → Network tab
- Watch requests going to different ports (8080 vs 8000)
- Verify authentication cookies and user context

### Test Individual APIs
```bash
# Test Go backend
curl http://localhost:8080/chats -H "Cookie: Authorization=your_token"

# Test Python backend
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "user_id": "uuid", "chat_id": "uuid"}'
```

## 🎯 Benefits of Dual Backend

1. **Separation of Concerns**: Auth vs AI processing
2. **Technology Optimization**: Go for performance, Python for AI
3. **Scalability**: Independent scaling of services
4. **Maintenance**: Easier to update individual components
5. **Fallback**: Redundancy for better reliability