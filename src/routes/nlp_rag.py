from fastapi import APIRouter, Request,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import aiofiles
from controllers.FileController import FileController
from controllers.ProcessController import process_file
from models.db_schemes import ChunkScheme
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

    project_model = request.app.state.project_model
    chunk_model = request.app.state.chunk_model

    project = await project_model.get_project_or_create_one(project_id)

    if payload.do_reset == 1:
        deleted = await chunk_model.delete_chunks_by_project(project_id)
        print(f" Deleted {deleted} existing chunks for project '{project_id}'")

    all_chunks: list[ChunkScheme] = []
    processed_files: list[str] = []

    for file_name in files_in_folder:
        file_path = os.path.join(folder_path, file_name)
        
        if os.path.isfile(file_path):
            print(f"Processing file: {file_name}...")
            
            chunks = process_file(file_path)
            
            if not chunks:
                continue
            
            file_chunks = [
                ChunkScheme(
                    project_id=project_id,
                    file_name=file_name,
                    text=chunk_text,
                    chunk_order=idx,
                )
                for idx, chunk_text in enumerate(chunks)
            ]
            all_chunks.extend(file_chunks)
            processed_files.append(file_name)
    
    
    inserted = await chunk_model.insert_many_chunks(all_chunks)
    total_chunks = await chunk_model.get_chunk_count(project_id)
    
    await project_model.update_chunk_count(project_id, total_chunks)
    await project_model.update_files(project_id, processed_files)
    
    return JSONResponse(status_code=200, content={
        "message": f"Successfully processed {len(processed_files)} file(s).",
        "project_id": project_id,
        "chunks_inserted": inserted,
        "total_chunks_in_db": total_chunks,
        "processed_files": processed_files,
        "sample_chunks": [c.text for c in all_chunks[:3]],
    })


