# Golang Backend with Gin and DuckDB

This is a Golang implementation of the Python FastAPI backend using Gin framework and DuckDB.

## Features

- File upload endpoint (`/upload`) - supports CSV and XLSX files
- SQL query execution endpoint (`/query`)
- DuckDB in-memory database
- Automatic table creation from uploaded files
- Type inference for columns

## Setup

1. Initialize Go modules:
```bash
go mod tidy
```

2. Run the server:
```bash
go run .
```

The server will start on port 8000.

## API Endpoints

### POST /upload
Upload a CSV or XLSX file and create a table in DuckDB.

**Request:** Multipart form with `file` field

**Response:**
```json
{
  "message": "Uploaded filename.csv successfully",
  "table": "filename",
  "metadata": "Table info with columns and types",
  "sample_rows": [...]
}
```

### POST /query
Execute SQL queries on the uploaded data.

**Request:**
```json
{
  "sql": "SELECT * FROM table_name LIMIT 10"
}
```

**Response:**
```json
{
  "query": "SELECT * FROM table_name LIMIT 10",
  "result": [...]
}
```

## Dependencies

- `github.com/gin-gonic/gin` - HTTP web framework
- `github.com/marcboeker/go-duckdb` - DuckDB driver for Go
- `github.com/tealeg/xlsx/v3` - Excel file reading library
