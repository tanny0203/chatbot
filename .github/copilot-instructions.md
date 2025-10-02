# 📊 NL2SQL Data Chatbot - Architecture Guide

**Talk to your data — in plain English.**

Upload any CSV/XLSX dataset and query it using natural language with >95% accuracy. The system automatically generates schema metadata, translates questions to SQL, executes queries, and returns human-readable insights with optional visualizations.

## System Architecture

**Current State**: Hybrid 3-tier system transitioning to full Go backend
- **Frontend**: React chat interface (`frontend/chatxl/`) 
- **Go Backend**: File processing, database management, schema inference (`backend/go-backend/`)
- **Python NL2SQL**: FastAPI + LangChain/LangGraph + Ollama (`backend/python-nl2sql/`)
- **Future**: Evaluating LangChain-Go to consolidate into single Go backend

### Data Flow Pipeline
1. User uploads CSV/XLSX → Go processes & stores in DuckDB/PostgreSQL
2. Go generates comprehensive metadata with statistical analysis & query examples  
3. Python translates natural language → SQL using LLM (Ollama/GPT-4)
4. Go executes SQL, performs analytics (correlations, trends) 
5. Results returned as human-readable insights + optional visualizations

## Key Components

### Go Backend (`backend/go-backend/`) - Core Data Engine
- **Single endpoint**: `POST /upload` at `:8080` 
- **Database**: DuckDB (development) → PostgreSQL (production)
- **Advanced file processing**: CSV/XLSX with 1000-row batch inserts
- **Production-grade type inference**: `inferColumnTypeAdvanced()` in `internal/api/upload.go`
  - Statistical analysis: min/max/mean/median/std for numerics
  - Categorical detection with frequency analysis & enum mappings
  - Date pattern recognition, boolean normalization
  - Generates query examples & synonym mappings for 95% NL2SQL accuracy
- **Future**: May handle full backend if LangChain-Go proves reliable

### Python NL2SQL Service (`backend/python-nl2sql/`) - LLM Interface  
- **FastAPI** with LangChain/LangGraph orchestration
- **LLM Options**: 
  - Development: Ollama (Llama-3, Mistral, SQLCoder)
  - Production: GPT-4, Defog SQLCoder, fine-tuned Llama-3
- **Advanced Analytics**: pandas, NumPy, SciPy for correlations/regressions
- **Dependencies**: Managed via `uv` package manager

### Frontend (`frontend/chatxl/`) - Chat Interface
- **React 19 + Vite + TypeScript** chat-style interface
- **Features**: File upload, natural language queries, result visualization
- **Current**: Basic template - needs chat UI implementation

## Development Workflows

### Backend Services
```fish
# Go backend
cd backend/go-backend
go run main.go  # Starts on :8080

# Python NL2SQL 
cd backend/python-nl2sql
uv run fastapi dev main.py  # Auto-reload enabled
```

### Frontend
```fish
cd frontend/chatxl
npm run dev     # Vite dev server
npm run build   # Production build
```

## Project Conventions

### File Processing Patterns
- **Concurrent type inference**: Uses goroutines with `sync.WaitGroup` for column analysis
- **Batch processing**: 1000-row batches for database inserts to handle large files
- **Comprehensive metadata**: Every column gets `ColumnMetadata` with statistical analysis, examples, and mappings

### Database Patterns  
- **DuckDB in-memory**: `db.InitDB()` creates global `*sql.DB` connection
- **Dynamic table creation**: Tables named after uploaded filenames (without extension)
- **Type mapping**: Go types → SQL types with production-ready inference logic

### Error Handling
- Go: Return errors up the stack, handle in main HTTP handler with appropriate status codes
- Python: FastAPI automatic error handling with validation
- No global error middleware - handle at endpoint level

### Code Organization
- **Go**: Clean architecture with `internal/api/`, `internal/db/` separation
- **Python**: Simple FastAPI structure, main logic in `model.py`
- **Frontend**: Standard Vite/React structure

## Integration Points

### Go ↔ Database
- Single global `db.Db` connection in `internal/db/db_init.go`
- All SQL operations in `internal/api/upload.go`
- Tables auto-created with inferred schemas

### Go ↔ Python Integration
- **Metadata handoff**: Go's comprehensive schema analysis feeds Python NL2SQL
- **Query execution**: Go handles SQL execution & analytics post-translation
- **Production pipeline**: Upload → Schema → NL2SQL → Execute → Analytics → Insights

### Example Queries Supported
- `"Top 10 students by marks"` → `SELECT * FROM students ORDER BY marks DESC LIMIT 10`
- `"Which city had lowest rainfall in 2024?"` → `SELECT city FROM weather WHERE year=2024 ORDER BY rainfall ASC LIMIT 1`  
- `"Year-over-year sales growth trend?"` → Complex analytical query with window functions

### Critical Files
- `backend/go-backend/internal/api/upload.go`: Advanced schema inference engine (679 lines)
- `backend/python-nl2sql/model.py`: LLM orchestration with LangChain/LangGraph
- `backend/go-backend/main.go`: Single HTTP endpoint for file processing

### Architecture Decision Points
- **Database**: DuckDB (dev) vs PostgreSQL (prod) - embedded vs scalable
- **LLM Orchestration**: LangChain vs LangGraph - choosing between frameworks  
- **Backend Consolidation**: Evaluating LangChain-Go to merge Python → Go
- **Frontend**: Building chat interface with file upload + query interface

## Dependencies & Tooling
- **Go**: Gin router, DuckDB/PostgreSQL drivers, `tealeg/xlsx/v3` processing
- **Python**: UV package manager, LangChain/LangGraph, pandas/NumPy/SciPy analytics
- **Frontend**: React 19, TypeScript 5.8, Vite build system