import os
import aiofiles
from fastapi import APIRouter, Request, UploadFile, File, HTTPException

from controllers.FileController import FileController
from routes.Constraints import FILE_ALLOWED_EXTENSION, FILE_CHUNK_SIZE, FILE_MAX_SIZE_MB

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])

@router.post("/{dir_name}")
async def upload_file(request: Request, dir_name: str, file: UploadFile = File(...)):
    ret = validate_file(file)
    file_path = FileController().get_file_path(dir_name, file.filename)
    if(ret != "success"):
        return {"failed"}
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await file.read(FILE_CHUNK_SIZE):
                await out_file.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File write failed: {str(e)}")
    
    project_model = request.app.state.project_model
    await project_model.get_project_or_create_one(dir_name)
    await project_model.update_files(dir_name, [file.filename])

    return {
        "status": "success",
        "project_id": dir_name,
        "file_name": file.filename,
        "saved_to": file_path,
    }


def validate_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in FILE_ALLOWED_EXTENSION:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{ext}'. Allowed: {FILE_ALLOWED_EXTENSION}"
        )
    
    return "success"