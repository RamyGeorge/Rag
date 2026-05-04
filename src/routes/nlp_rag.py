from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

router = APIRouter(prefix="/index", tags=["RAG pipeline"])

class IndexPushRequest(BaseModel):
    project_id: str   
    do_reset: int = 0 

@router.post("/index/push")
async def push_data_to_index(request: Request, payload: IndexPushRequest):
    project_id = payload.project_id

    folder_path = os.path.join("assets", project_id)

    files_in_folder = os.listdir(folder_path)

    for f in files_in_folder:


