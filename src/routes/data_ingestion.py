import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException

from controllers.FileController import FileController
from routes.Constraints import FILE_ALLOWED_EXTENSION, FILE_CHUNK_SIZE, FILE_MAX_SIZE_MB

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


@router.post("/{dir_name}")
async def upload_file(dir_name: str, file: UploadFile = File(...)):
    validate_file(file)

    file_path = FileController().get_file_path(dir_name, file.filename)

    return {"filename": file.filename, "path": file_path, "size_bytes": uploaded_size}


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