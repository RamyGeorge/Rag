from fastapi import APIRouter, Request,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import aiofiles
from controllers.FileController import FileController
from controllers.ProcessController import process_file
from routes.Constraints import FILE_ALLOWED_EXTENSION, FILE_CHUNK_SIZE, FILE_MAX_SIZE_MB


router = APIRouter(prefix="/index", tags=["RAG pipeline"])

class IndexPushRequest(BaseModel):
    project_id: str   
    do_reset: int = 0 

@router.post("/push")
async def push_data_to_index(request: Request, payload: IndexPushRequest):
    project_id = payload.project_id
    folder_path = os.path.join("assets", project_id)
    if not os.path.isdir(folder_path):
        raise HTTPException(
            status_code=404,
            detail=f"Project folder '{project_id}' not found in assets directory."
        )

    files_in_folder = os.listdir(folder_path)
    if not files_in_folder:
        raise HTTPException(
            status_code=400,
            detail="No files found in the project directory to process."
        )

    all_project_chunks = []
    processed_files = []

    for file_name in files_in_folder:
        file_path = os.path.join(folder_path, file_name)
        
        
        if os.path.isfile(file_path):
            print(f"Processing file: {file_name}...")
            
            chunks = process_file(file_path)
            
            if chunks:
                all_project_chunks.extend(chunks)
                processed_files.append(file_name)
                
    return JSONResponse(status_code=200, content={
        "message": f"Successfully processed {len(processed_files)} file(s).",
        "project_id": project_id,
        "total_chunks_created": len(all_project_chunks),
        "processed_files": processed_files,
        "sample_chunks": all_project_chunks[:3] # Return a small sample for verification
    })
        


