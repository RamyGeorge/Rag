from fastapi import APIRouter, Request,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import aiofiles
from controllers.FileController import FileController
from controllers.ProcessController import process_file
from models.db_schemes import ChunkScheme
from routes.Constraints import FILE_ALLOWED_EXTENSION, FILE_CHUNK_SIZE, FILE_MAX_SIZE_MB
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
qdrant = QdrantClient(host=QDRANT_HOST, port=6333)
embedder = SentenceTransformer('all-MiniLM-L6-v2')
VECTOR_SIZE = 384 

router = APIRouter(prefix="/index", tags=["RAG pipeline"])

class IndexPushRequest(BaseModel):
    project_id: str   
    do_reset: int = 0 

@router.post("/push")
async def push_data_to_index(request: Request, payload: IndexPushRequest):
    project_id = payload.project_id
    
    # 1. ROBUST PATHING
    # This finds the 'assets' folder relative to this file's directory
    # (Assuming nlp_rag.py is in src/routes/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder_path = os.path.join(base_dir, "assets", project_id)
    
    print(f"DEBUG: Looking for folder at: {folder_path}")

    # 2. VALIDATE DIRECTORY
    if not os.path.isdir(folder_path):
        raise HTTPException(
            status_code=404,
            detail=f"Project folder '{project_id}' not found. Searched at: {folder_path}"
        )

    files_in_folder = os.listdir(folder_path)
    if not files_in_folder:
        raise HTTPException(
            status_code=400,
            detail=f"Folder '{project_id}' is empty. No files to process."
        )

    # 3. GET MODELS FROM APP STATE
    project_model = request.app.state.project_model
    chunk_model = request.app.state.chunk_model
    project = await project_model.get_project_or_create_one(project_id)

    # 4. QDRANT COLLECTION SETUP
    collection_name = f"project_{project_id}"
    
    # Reset logic (If do_reset=1, delete Qdrant and Mongo data)
    if payload.do_reset == 1:
        print(f"Resetting data for project: {project_id}")
        await chunk_model.delete_chunks_by_project(project_id)
        if qdrant.collection_exists(collection_name):
            qdrant.delete_collection(collection_name)

    # IMPORTANT: Create the collection if it doesn't exist!
    if not qdrant.collection_exists(collection_name):
        print(f"Creating collection: {collection_name}")
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    # 5. PROCESS FILES
    all_chunks: list[ChunkScheme] = []
    processed_files: list[str] = []

    for file_name in files_in_folder:
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            print(f"Processing file: {file_name}...")
            chunks = process_file(file_path)
            if not chunks: continue
            
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
    
    if not all_chunks:
        raise HTTPException(status_code=400, detail="No text extracted.")

    # 6. EMBED & UPLOAD TO QDRANT
    print(f"Generating vectors for {len(all_chunks)} chunks...")
    texts_to_embed = [chunk.text for chunk in all_chunks]
    vectors = embedder.encode(texts_to_embed).tolist()
    
    qdrant_points = []
    for i, chunk in enumerate(all_chunks):
        chunk.embedding = vectors[i] # Save vector to Mongo object
        qdrant_points.append(PointStruct(
            id=str(uuid.uuid4()), 
            vector=vectors[i],
            payload={
                "text": chunk.text,
                "file_name": chunk.file_name,
                "chunk_order": chunk.chunk_order
            }
        ))

    print("Uploading to Qdrant...")
    qdrant.upsert(collection_name=collection_name, points=qdrant_points)

    # 7. SAVE TO MONGODB
    inserted = await chunk_model.insert_many_chunks(all_chunks)
    total_chunks = await chunk_model.get_chunk_count(project_id)
    
    await project_model.update_chunk_count(project_id, total_chunks)
    await project_model.update_files(project_id, processed_files)
    
    return JSONResponse(status_code=200, content={
        "message": "Processing complete",
        "project_id": project_id,
        "qdrant_collection": collection_name,
        "mongo_chunks": inserted,
        "qdrant_vectors": len(qdrant_points)
    })


