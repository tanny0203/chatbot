from fastapi import FastAPI, UploadFile, File, APIRouter, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import tempfile
import os
import json
import asyncio
from typing import AsyncGenerator, Optional
from models.database import get_main_db
from services.file_service import FileService
from services.chat_service import get_chat_service
from services.memory_service import get_memory_service
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="NL2SQL Chat API", description="Natural Language to SQL with Memory")

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

# Routers
chat_router = APIRouter(prefix="/chats", tags=["chats"])
memory_router = APIRouter(prefix="/memory", tags=["memory"])
api_router = APIRouter(prefix="/api", tags=["api"])

# Store for progress tracking
progress_store = {}

@app.get("/")
async def home():
    return {"message": "NL2SQL Chat API with Redis Memory", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        memory_service = get_memory_service()
        stats = memory_service.get_memory_stats()
        return {
            "status": "healthy",
            "redis_connected": True,
            "memory_stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "redis_connected": False,
            "error": str(e)
        }

# === Chat Endpoints ===

@chat_router.post("/")
async def create_chat(request: CreateChatRequest, db: Session = Depends(get_main_db)):
    """Create a new chat"""
    try:
        chat_service = get_chat_service(db)
        chat_id = chat_service.create_chat(request.user_id)
        return {
            "success": True,
            "chat_id": chat_id,
            "message": "Chat created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/{chat_id}/messages")
async def send_message(chat_id: str, message: ChatMessage, db: Session = Depends(get_main_db)):
    """Send a message to the chat and get AI response"""
    try:
        chat_service = get_chat_service(db)
        response = await chat_service.send_message(message.user_id, chat_id, message.message)
        
        if response["success"]:
            return response
        else:
            # Return 400 for user errors (like no dataset), 500 for server errors
            status_code = 400 if response.get("requires_dataset") else 500
            raise HTTPException(status_code=status_code, detail=response)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/{chat_id}/history")
async def get_chat_history(
    chat_id: str, 
    user_id: str, 
    limit: Optional[int] = None,
    db: Session = Depends(get_main_db)
):
    """Get chat history"""
    try:
        chat_service = get_chat_service(db)
        response = chat_service.get_chat_history(user_id, chat_id, limit)
        
        if response["success"]:
            return response
        else:
            raise HTTPException(status_code=400, detail=response)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.delete("/{chat_id}")
async def clear_chat(chat_id: str, request: ClearChatRequest, db: Session = Depends(get_main_db)):
    """Clear chat history and dataset context"""
    try:
        chat_service = get_chat_service(db)
        response = chat_service.clear_chat(request.user_id, chat_id)
        
        if response["success"]:
            return response
        else:
            raise HTTPException(status_code=400, detail=response)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/user/{user_id}")
async def get_user_chats(user_id: str, db: Session = Depends(get_main_db)):
    """Get all chats for a user"""
    try:
        chat_service = get_chat_service(db)
        response = chat_service.get_user_chats(user_id)
        
        if response["success"]:
            return response
        else:
            raise HTTPException(status_code=400, detail=response)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# === Memory Management Endpoints ===

@memory_router.get("/stats")
async def get_memory_stats():
    """Get Redis memory usage statistics"""
    try:
        memory_service = get_memory_service()
        stats = memory_service.get_memory_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.delete("/user/{user_id}")
async def delete_user_memory(user_id: str):
    """Delete all memory data for a user"""
    try:
        memory_service = get_memory_service()
        memory_service.delete_all_user_data(user_id)
        return {
            "success": True,
            "message": f"All memory data deleted for user {user_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Main API Endpoints ===

@api_router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    chat_id: str = Form(...),
    db: Session = Depends(get_main_db)
):
    """Upload CSV/XLSX dataset and store in Postgres with metadata generation"""
    try:
        # Validate UUIDs
        user_id_uuid = uuid.UUID(user_id)
        chat_id_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID or chat ID format")

    # Validate file extension
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    try:
        # Read file content
        file_content = await file.read()
        
        # Create temporary file and close it before processing (Windows-safe)
        temp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            temp_path = temp_file.name

        try:
            # Process file using FileService
            file_service = FileService(db)
            file_record, stats = await file_service.process_file(
                temp_path,
                file.filename,
                chat_id_uuid,
                user_id_uuid
            )

            # Update dataset context in Redis memory using enhanced pipeline
            chat_service = get_chat_service(db)
            chat_service.update_dataset_context_from_file_service(
                user_id, chat_id, file_record, stats
            )

            return {
                "success": True,
                "message": "Dataset uploaded and processed successfully",
                "file_id": str(file_record.id),
                "table_name": file_record.table_name,
                "rows": stats.get("rows", 0),
                "columns": len(stats.get("columns", [])),
                "filename": file.filename
            }
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.post("/ask")
async def ask_question(request: AskRequest, db: Session = Depends(get_main_db)):
    """Ask a natural language question about the uploaded dataset"""
    try:
        # Validate UUIDs
        uuid.UUID(request.user_id)
        uuid.UUID(request.chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID or chat ID format")

    try:
        # Use chat service which internally uses the two-model pipeline
        chat_service = get_chat_service(db)
        response = await chat_service.send_message(request.user_id, request.chat_id, request.question)
        
        if response["success"]:
            return {
                "success": True,
                "answer": response["answer"],
                "sql_query": response.get("sql_query"),
                "result_count": response.get("result_count", 0),
                "execution_success": response.get("execution_success", False)
            }
        else:
            # Handle different error types
            if response.get("requires_dataset"):
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "error": "no_dataset",
                        "message": response["message"],
                        "requires_dataset": True
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "processing_failed",
                        "message": response["message"],
                        "stage": response.get("stage", "unknown")
                    }
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

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

    # Start background processing (the background task will handle temp file safely)
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

        # Create temporary file, close it, then process (Windows-safe)
        temp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            temp_path = temp_file.name

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
                temp_path,
                filename,
                chat_id_uuid,
                user_id_uuid
            )

            # Update dataset context in Redis memory
            chat_service = get_chat_service(db)
            chat_service.update_dataset_context_from_file_service(
                str(user_id_uuid), str(chat_id_uuid), file_record, stats
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
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                
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
app.include_router(memory_router)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)