import datetime
from fastapi import FastAPI, UploadFile, File as FastAPIFile, APIRouter, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import tempfile
import os
import json
import asyncio
import pandas as pd
from typing import AsyncGenerator, Optional
from pathlib import Path
from models.database import get_main_db, file_storage_engine
from models.file import File
from services.file_service import get_column_metadata, generate_table_schema, create_table_sql, insert_values, clean_table_name, save_table_metadata


app = FastAPI(title="Chat File Upload API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for requests
class ChatMessage(BaseModel):
    message: str
    user_id: str

class CreateChatRequest(BaseModel):
    user_id: str

class ClearChatRequest(BaseModel):
    user_id: str

class AskRequest(BaseModel):
    question: str
    user_id: str
    chat_id: str


chat_router = APIRouter(prefix="/chats", tags=["chats"])


progress_store = {}



async def generate_progress_updates(task_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE updates for file upload progress"""
    # Wait for task to be created
    wait_count = 0
    while task_id not in progress_store and wait_count < 100:
        await asyncio.sleep(0.1)
        wait_count += 1
    
    if task_id not in progress_store:
        yield f"data: {json.dumps({'status': 'error', 'message': 'Task not found', 'progress': 0})}\n\n"
        return
    
    last_data = None
    while True:
        if task_id in progress_store:
            progress_data = progress_store[task_id]
            
            # Only send if data has changed
            if progress_data != last_data:
                data = json.dumps(progress_data)
                yield f"data: {data}\n\n"
                last_data = progress_data.copy()
            
            # If completed or error, clean up and exit
            if progress_data.get("status") in ["completed", "error"]:
                await asyncio.sleep(1)
                if task_id in progress_store:
                    del progress_store[task_id]
                break
        
        await asyncio.sleep(0.1)

@chat_router.get("/{chat_id}/files/upload/progress/{task_id}")
async def get_upload_progress(task_id: str):
    """SSE endpoint for file upload progress"""
    return StreamingResponse(
        generate_progress_updates(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@chat_router.post("/{chat_id}/files")
async def upload_file(
    chat_id: str,
    file: UploadFile = FastAPIFile(...),
    user_id: str = Form(...), 
    db: Session = Depends(get_main_db)
):
    """Upload file and return metadata immediately"""
    try:
        # Validate chat_id and user_id as UUID
        try:
            chat_id_uuid = uuid.UUID(chat_id)
            user_id_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid chat ID or user ID")

        # Validate file extension
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

        # Read file content
        file_content = await file.read()
        filename = file.filename

        # Create a project-local tmp directory and write the file there
        base_dir = Path(__file__).resolve().parent
        tmp_dir = base_dir / "tmp_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = tmp_dir / f"{uuid.uuid4()}_{filename}"
        
        try:
            with open(temp_path, "wb") as f:
                f.write(file_content)

            # Read the file into DataFrame
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(temp_path)
            else:  # Excel files
                df = pd.read_excel(temp_path)

            # Generate unique table name
            raw_table_name = f"{chat_id}_{filename}"
            table_name = clean_table_name(raw_table_name)
            
            # Generate SQL schema
            sql_schema = generate_table_schema(df, table_name)

            
            # Create table in file storage database
            create_table_sql(sql_schema, table_name, file_storage_engine)

            
            # Insert data
            insert_values(df, table_name, file_storage_engine)

            
            # Create file record in main database
            file_record = File(
                chat_id=chat_id_uuid,
                user_id=user_id_uuid,
                filename=filename,
                table_name=table_name,
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )

            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            # Generate column metadata and persist
            metadata = get_column_metadata(df, file_record.id)
            save_table_metadata(metadata, db)

            # Serialize metadata to JSON-friendly dicts
            columns_metadata = [
                {
                    "id": str(m.id) if getattr(m, "id", None) is not None else None,
                    "file_id": str(m.file_id) if getattr(m, "file_id", None) is not None else None,
                    "column_name": m.column_name,
                    "data_type": m.data_type,
                    "sql_type": m.sql_type,
                    "nullable": m.nullable,
                    "is_category": m.is_category,
                    "is_boolean": m.is_boolean,
                    "is_date": m.is_date,
                    "unique_count": m.unique_count,
                    "null_count": m.null_count,
                    "min_value": m.min_value,
                    "max_value": m.max_value,
                    "mean_value": m.mean_value,
                    "median_value": m.median_value,
                    "std_value": m.std_value,
                    "sample_values": m.sample_values,
                    "top_values": m.top_values,
                    "enum_values": m.enum_values,
                    "value_mappings": m.value_mappings,
                    "synonym_mappings": m.synonym_mappings,
                    "example_queries": m.example_queries,
                    "description": m.description,
                }
                for m in metadata
            ]

            # Return the required JSON response
            return {
                "file_id": str(file_record.id),
                "filename": filename,
                "table_name": table_name,
                "sql_schema": sql_schema,
                "columns_metadata": columns_metadata,
            }
            
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
            
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)