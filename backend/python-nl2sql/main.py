from fastapi import FastAPI, UploadFile, File, APIRouter, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
import tempfile
import os
import json
import asyncio
from typing import AsyncGenerator
from models.database import get_main_db
from services.file_service import FileService

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_router = APIRouter(prefix="/chats", tags=["chats"])

# Store for progress tracking
progress_store = {}

@app.get("/")
async def home():
    return {"Hello": "World"}

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
    file: UploadFile = File(...),
    user_id: str = Form(...), 
    db: Session = Depends(get_main_db)
):
    """Upload file with progress tracking"""
    # Generate task ID for progress tracking
    task_id = str(uuid.uuid4())
    
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
    
    # Start background processing
    asyncio.create_task(process_file_background(task_id, chat_id_uuid, user_id_uuid, file_content, filename, db))
    
    return {"task_id": task_id}

async def process_file_background(task_id: str, chat_id_uuid: uuid.UUID, user_id_uuid: uuid.UUID, file_content: bytes, filename: str, db: Session):
    """Background task to process the file with progress updates"""
    try:
        # Stage 1: Uploading file
        progress_store[task_id] = {
            "status": "uploading",
            "message": "Uploading file",
            "progress": 50,
            "filename": filename
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
            temp_file.write(file_content)
            temp_file.flush()

            try:
                # Stage 2: Generating metadata
                progress_store[task_id] = {
                    "status": "metadata",
                    "message": "Generating metadata",
                    "progress": 90,
                    "filename": filename
                }

                # Process file
                file_service = FileService(db)
                file_record, stats = await file_service.process_file(
                    temp_file.name,
                    filename,
                    chat_id_uuid,
                    user_id_uuid
                )

                # Completed
                progress_store[task_id] = {
                    "status": "completed",
                    "message": "Upload completed",
                    "progress": 100,
                    "filename": filename,
                    "file_id": str(file_record.id),
                    "table_name": file_record.table_name
                }

            finally:
                # Clean up temporary file
                os.unlink(temp_file.name)
                
    except Exception as e:
        # Update progress: Error
        progress_store[task_id] = {
            "status": "error",
            "message": f"Error: {str(e)}",
            "progress": 0,
            "filename": filename,
            "error": str(e)
        }
            
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)