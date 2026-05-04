from fastapi import APIRouter, UploadFile, File, HTTPException , JSONRESPONSE 
import os
from aiofiles import *
from routes.Constraints import *
from controllers import FileController
router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])

@router.post("/{dir_name}")
async def upload_file(dir_name,file: UploadFile = File(...)):
    
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        return HTTPException(status_code=400, content={"error_msg": error_msg})

    file_path = FileController().get_file_path(dir_name) 
    async with aiofiles.open(file_path, 'wb') as out_file:
        while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
            await out_file.write(chunk)
      
        

async def validate_file(file: UploadFile):

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in FILE_ALLOWED_EXTENSION:
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension."
        )
    content = await file.read()

    if len(content) > FILE_MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail="File too large."
        )

    if ext == ".txt":
        try:
            content.decode("utf-8")
        except:
            raise HTTPException(
                status_code=400,
                detail="TXT must be UTF-8."
            )

    return content