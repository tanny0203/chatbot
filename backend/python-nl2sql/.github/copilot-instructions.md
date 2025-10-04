# GitHub Copilot Instructions - Python NL2SQL Backend

## rules and instructions:
- Always follow the existing code style and conventions.
- avoid adding any new dependencies unless absolutely necessary.
- prioritize code readability and maintainability.
- do only what i have given to do.
- avoid unnecessary complexity.
- stop using deprecated libraries and functions.
- stop over-engineering solutions and stick core to simplicity.
- dont create any new files unless absolutely necessary.
- avoid redundant code and duplication.

## Architecture Overview

This is a **dual-database FastAPI microservice** for a chatbot system that processes file uploads (CSV/Excel) and converts them into queryable SQL tables. The service uses a **separation of concerns** between metadata storage and file data storage:

- **Main Database** (`tempdb`): Stores application metadata (users, chats, files records)
- **File Storage Database** (`filestorage`): Stores actual uploaded file data as dynamically created tables

## Key Components & Data Flow

### 1. File Upload Pipeline (`main.py` + `services/file_service.py`)
- **Entry**: `POST /chats/{chat_id}/files` endpoint
- **Process**: CSV/Excel → pandas DataFrame → PostgreSQL table with auto-generated schema
- **Output**: File metadata + column analysis + SQL schema generation
- Uses `tmp_uploads/` directory for temporary file processing (auto-cleanup)

### 2. Database Architecture (`models/database.py`)
```python
# Two separate database connections:
main_engine = create_engine(MAIN_DATABASE_URL)           # Metadata
file_storage_engine = create_engine(FILE_STORAGE_DATABASE_URL)  # File data
```

### 3. Dynamic Table Generation (`services/file_service.py`)
- **Smart type inference**: Optimizes PostgreSQL column types (SMALLINT vs INTEGER vs BIGINT)
- **Column name sanitization**: Handles special characters, reserved words, duplicates
- **Metadata extraction**: Statistical analysis, sample values, data quality metrics

## Critical Patterns & Conventions

### Database Session Management
Always use dependency injection for database sessions:
```python
# For metadata operations
db: Session = Depends(get_main_db)

# For file data operations  
file_storage_engine  # Direct engine usage
```

### File Processing Workflow
1. **Validate** → UUID format, file extensions (.csv, .xlsx, .xls)
2. **Temporary storage** → `tmp_uploads/{uuid}_{filename}`
3. **DataFrame processing** → pandas read + type inference
4. **Schema generation** → `generate_table_schema()` with optimized SQL types
5. **Table creation** → `create_table_sql()` + `insert_values()`
6. **Metadata storage** → File record in main DB + detailed column metadata
7. **Cleanup** → Remove temporary files

### Column Naming & SQL Generation
- Uses `clean_column_name()` for PostgreSQL compatibility
- Handles reserved words by appending `_col` suffix
- Generates optimized VARCHAR lengths based on actual data
- Always includes auto-incrementing `id` and `created_at` columns

## Development Workflows

### Running the Service
```bash
cd /home/balaji/Projects/chatbot/backend/python-nl2sql
python main.py  # Runs on localhost:8000 with auto-reload
```

### Testing File Upload
Use `test_endpoint.py` with sample CSV:
```bash
python test_endpoint.py  # Tests with student-por.csv
```

### Database Environment Variables
```bash
MAIN_DATABASE_URL=postgresql://user:pass@localhost:5432/tempdb
FILE_STORAGE_DATABASE_URL=postgresql://user:pass@localhost:5432/filestorage
```

## Integration Points

### Models Structure
- `models/user.py` → User authentication/management
- `models/chat.py` → Chat sessions
- `models/file.py` → File metadata (links to dynamic tables in file storage DB)
- `models/column_metadata.py` → Detailed column analysis
- `models/data_quality.py` → Data validation metrics

### External Dependencies
- **PostgreSQL**: Dual database setup required
- **pandas + openpyxl**: File processing
- **SQLAlchemy**: ORM for main DB, direct SQL for file storage
- **FastAPI**: REST API with CORS enabled for all origins

### Missing Components (Referenced but Not Implemented)
- `services.two_model_pipeline` → NL2SQL conversion logic
- `services.memory_service` → Chat context management

## Security & Performance Notes

- **UUID-based isolation**: All resources use UUIDs for security
- **Temporary file cleanup**: Always removes uploaded files after processing
- **Optimized SQL types**: Reduces storage overhead with smart type inference
- **Chunked inserts**: Uses `chunksize=1000` for large file uploads
- **Connection pooling**: SQLAlchemy handles connection management

## Common Task Patterns

**Adding new file formats**: Extend the validation in upload endpoint and add parser in `services/file_service.py`

**Database queries**: Use `file_storage_engine` for querying uploaded data tables, `get_main_db()` for metadata

**Error handling**: FastAPI HTTPException with specific status codes for different failure modes

**Column metadata**: The `get_column_metadata()` function provides rich statistical analysis including data types, nullability, sample values, and distribution metrics