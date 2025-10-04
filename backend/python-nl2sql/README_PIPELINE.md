# NL2SQL Two-Model Pipeline

A FastAPI backend that converts natural language questions to SQL queries and provides natural language explanations using a two-model approach:

1. **SQLCoder LLM** → Generates SQL queries from natural language
2. **Database Execution** → Safely executes SQL with user isolation  
3. **Llama 3.2 LLM** → Provides natural language explanations of results

## 🏗️ Architecture

```
User Question → SQLCoder → SQL Query → Database → Results → Llama 3.2 → Natural Language Answer
                   ↓              ↓         ↓           ↓
              Redis Memory    User Isolation  Postgres   Conversation History
```

## 🚀 Features

- **Two-Model Pipeline**: SQLCoder for SQL generation + Llama 3.2 for explanations
- **Redis Memory**: Conversation history and dataset context per user/chat
- **Multi-user Isolation**: All queries scoped to `user_id` for security
- **Enhanced Metadata**: Comprehensive dataset analysis and schema extraction
- **Error Handling**: Intelligent error categorization and fallback responses
- **Input Validation**: SQL injection prevention and input sanitization
- **Conversation Context**: Maintains chat history for contextual queries

## 📋 Prerequisites

- Python 3.13+
- PostgreSQL database
- Redis server
- Ollama with SQLCoder and Llama 3.2 models

```bash
# Install Ollama models
ollama pull sqlcoder
ollama pull llama3.2
```

## 🛠️ Installation

1. **Install Dependencies**:
```bash
cd /home/balaji/Projects/chatbot/backend/python-nl2sql
pip install -r pyproject.toml
```

2. **Start Redis**:
```bash
redis-server --daemonize yes
```

3. **Configure Database**:
```python
# Update models/database.py with your PostgreSQL connection
DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

4. **Run the API**:
```bash
python main.py
```

## 📚 API Endpoints

### Core Endpoints

#### `POST /api/upload`
Upload CSV/XLSX dataset and generate metadata.

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@marks.csv" \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "chat_id=550e8400-e29b-41d4-a716-446655440001"
```

Response:
```json
{
  "success": true,
  "message": "Dataset uploaded and processed successfully",
  "file_id": "uuid",
  "table_name": "user_550e8400_marks",
  "rows": 1000,
  "columns": 5,
  "filename": "marks.csv"
}
```

#### `POST /api/ask`
Ask natural language questions about your data.

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me the top 5 students in maths",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "chat_id": "550e8400-e29b-41d4-a716-446655440001"
  }'
```

Response:
```json
{
  "success": true,
  "answer": "Here are the top 5 students in mathematics: Student A scored 95, Student B scored 92, Student C scored 91, Student D scored 90, and Student E scored 89. These students demonstrate excellent performance in mathematics.",
  "sql_query": "SELECT name, maths FROM user_550e8400_marks ORDER BY maths DESC LIMIT 5;",
  "result_count": 5,
  "execution_success": true
}
```

### Chat Management

#### `POST /chats/`
Create a new chat session.

#### `GET /chats/{chat_id}/history`
Get conversation history for a chat.

#### `DELETE /chats/{chat_id}`
Clear chat history and dataset context.

### Memory Management

#### `GET /memory/stats`
Get Redis memory usage statistics.

#### `DELETE /memory/user/{user_id}`
Delete all memory data for a user.

## 🔧 Helper Functions

The system includes modular helper functions in `utils/nl2sql_helpers.py`:

### `extract_metadata(df, table_name, user_id)`
Extract comprehensive metadata from DataFrame for SQL generation.

```python
metadata = extract_metadata(df, "marks", "user_123")
# Returns: table schema, column types, sample data, statistics
```

### `generate_sql(question, user_id, chat_id, dataset_context)`
Generate SQL query using SQLCoder with conversation history.

```python
result = await generate_sql(
    "Show top students", 
    "user_123", 
    "chat_456", 
    dataset_context
)
# Returns: {"success": True, "sql_query": "SELECT ...", "raw_response": "..."}
```

### `execute_sql(sql, user_id, db)`
Execute SQL query safely with user isolation.

```python
result = await execute_sql(
    "SELECT * FROM user_123_marks LIMIT 10", 
    "user_123", 
    db_session
)
# Returns: {"success": True, "result": [...], "row_count": 10}
```

### `generate_answer(question, sql_query, sql_result, dataset_context)`
Generate natural language explanation using Llama 3.2.

```python
result = await generate_answer(
    "Show top students",
    "SELECT name, score FROM...",
    sql_execution_result,
    dataset_context
)
# Returns: {"success": True, "answer": "Here are the top students..."}
```

## 📊 Example Usage Flow

```python
# 1. Upload dataset
upload_response = requests.post("/api/upload", files={"file": open("marks.csv")})

# 2. Ask questions with context
questions = [
    "What are the top 5 students in maths?",
    "Now show their science scores too",  # Uses conversation context
    "What's the average score across all subjects?",
    "Show me students who improved from maths to science"
]

for question in questions:
    response = requests.post("/api/ask", json={
        "question": question,
        "user_id": "user_123",
        "chat_id": "chat_456"
    })
    print(f"Q: {question}")
    print(f"A: {response.json()['answer']}")
    print(f"SQL: {response.json()['sql_query']}")
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Full test with multiple questions
python test_pipeline.py

# Simple test with one question
python test_pipeline.py simple
```

The test creates sample student marks data and tests:
- Dataset upload and metadata extraction
- Various natural language questions
- SQL generation and execution
- Natural language response generation
- Conversation history and context

## 🔒 Security Features

- **User Isolation**: All SQL queries automatically scoped to `user_id`
- **SQL Injection Prevention**: Input validation and dangerous pattern detection
- **Read-Only Queries**: Only SELECT statements allowed, no data modification
- **Input Sanitization**: Question length limits and content validation
- **Error Handling**: Safe error messages without exposing system details

## 🎯 Supported Question Types

The system handles various natural language patterns:

- **Aggregations**: "What's the average score?", "How many students?"
- **Filtering**: "Show students with score > 90", "Find grade A students"
- **Sorting**: "Top 10 students", "Lowest performers", "Best in maths"
- **Grouping**: "Average by grade", "Count by category"
- **Comparisons**: "Students better than average", "Above median performance"
- **Complex Queries**: "Students who improved", "Correlation between subjects"

## 🚨 Error Handling

The system provides intelligent error handling:

- **No Dataset**: Prompts user to upload data first
- **Column Not Found**: Suggests checking column names
- **Syntax Errors**: Offers to rephrase the question
- **Empty Results**: Explains why no data was found
- **System Errors**: Provides helpful fallback responses

## 📈 Performance Considerations

- **Redis Memory**: Conversation history expires after 7 days
- **Dataset Context**: Metadata cached for 30 days
- **Result Limiting**: Large query results truncated for display
- **Connection Pooling**: Database connections efficiently managed
- **Model Caching**: LLM instances reused across requests

## 🔧 Configuration

Key configuration options:

```python
# Model configuration
SQL_MODEL = "sqlcoder"  # Ollama model for SQL generation
NLP_MODEL = "llama3.2"  # Ollama model for explanations

# Redis configuration
REDIS_URL = "redis://localhost:6379/0"

# Memory expiration
CONVERSATION_TTL = 7 * 24 * 3600  # 7 days
DATASET_TTL = 30 * 24 * 3600      # 30 days

# Result limits
MAX_DISPLAY_ROWS = 10
MAX_QUESTION_LENGTH = 1000
```

## 🐛 Troubleshooting

Common issues and solutions:

1. **Models not responding**: Check Ollama is running with correct models
2. **Redis connection failed**: Ensure Redis server is running
3. **Database errors**: Verify PostgreSQL connection and permissions
4. **Memory issues**: Monitor Redis memory usage via `/memory/stats`
5. **Slow responses**: Consider optimizing SQL queries or model performance

## 📝 API Documentation

Full API documentation available at: `http://localhost:8000/docs` (Swagger UI)

## 🤝 Contributing

The modular architecture makes it easy to extend:

- Add new question types in `two_model_pipeline.py`
- Enhance error handling in `nl2sql_helpers.py`
- Extend metadata extraction for new data types
- Add support for additional file formats
- Implement custom SQL validators