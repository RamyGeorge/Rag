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
from openai import OpenAI

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
qdrant = QdrantClient(host=QDRANT_HOST, port=6333)

print("Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
VECTOR_SIZE = 384 

router = APIRouter(prefix="/index", tags=["RAG pipeline"])

# used as the payload for push endpoint (JSON NODY IN POSTMAN WOULD CONTAIN PROJECT_ID AS A STR AND DO_RESET)
class IndexPushRequest(BaseModel):
    project_id: str   
    do_reset: int = 0 
#Same as above
class QueryRequest(BaseModel): 
    project_id: str 
    query: str
    top_k: int = 5

@router.post("/push")
async def push_data_to_index(request: Request, payload: IndexPushRequest):
    project_id = payload.project_id
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder_path = os.path.join(base_dir, "assets", project_id)
    
    collection_name = f"project_{project_id}"

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail=f"Project folder not found at: {folder_path}")

    files_in_folder = os.listdir(folder_path)
    if not files_in_folder:
        raise HTTPException(status_code=400, detail="Folder is empty.")

    project_model = request.app.state.project_model
    chunk_model = request.app.state.chunk_model
    await project_model.get_project_or_create_one(project_id)

    if payload.do_reset == 1:
        await chunk_model.delete_chunks_by_project(project_id)
        if qdrant.collection_exists(collection_name):
            qdrant.delete_collection(collection_name)

    if not qdrant.collection_exists(collection_name):
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    all_chunks: list[ChunkScheme] = []
    processed_files: list[str] = []

    for f in files_in_folder:
        file_path = os.path.join(folder_path, f)
        if os.path.isfile(file_path):
            chunks = process_file(file_path)
            if not chunks: continue
            
            file_chunks = [
                ChunkScheme(project_id=project_id, file_name=f, text=chunk_text, chunk_order=idx)
                for idx, chunk_text in enumerate(chunks)
            ]
            all_chunks.extend(file_chunks)
            processed_files.append(f)
    
    if not all_chunks:
        raise HTTPException(status_code=400, detail="No text extracted.")

    texts_to_embed = [chunk.text for chunk in all_chunks]
    vectors = embedder.encode(texts_to_embed).tolist()
    
    qdrant_points = []
    for i, chunk in enumerate(all_chunks):
        chunk.embedding = vectors[i]
        qdrant_points.append(PointStruct(
            id=str(uuid.uuid4()), vector=vectors[i],
            payload={"text": chunk.text, "file_name": chunk.file_name, "chunk_order": chunk.chunk_order}
        ))
    # dopnt insert more than 32mb at a time (will fail)
    qdrant.upsert(collection_name=collection_name, points=qdrant_points)

    inserted = await chunk_model.insert_many_chunks(all_chunks)
    total_chunks = await chunk_model.get_chunk_count(project_id)
    
    await project_model.update_chunk_count(project_id, total_chunks)
    await project_model.update_files(project_id, processed_files)
    
    return JSONResponse(status_code=200, content={"message": "Processing complete"})


@router.post("/search_rag")
async def answer_rag(request: Request, payload: QueryRequest): # Using renamed model
    project_id = payload.project_id
    query = payload.query
    top_k = payload.top_k
    
    
    collection_name = f"project_{project_id}"

    if not qdrant.collection_exists(collection_name):
        raise HTTPException(status_code=404, detail=f"No data found for project '{project_id}'. Did you run /push?")

    query_vector = embedder.encode(query).tolist()

    search_results = qdrant.search(collection_name=collection_name, query_vector=query_vector, limit=top_k)

    if not search_results:
        return JSONResponse(status_code=404, content={"message": "No relevant context found."})

    context_chunks = []
    sources_used = []
    for hit in search_results:
        text = hit.payload.get("text", "")
        file_name = hit.payload.get("file_name", "Unknown File")
        context_chunks.append(f"--- Document Source: {file_name} ---\n{text}\n")
        sources_used.append(file_name)
    context_str = "\n".join(context_chunks)

    system_prompt = (
        "You are an AI assistant. Answer the user's question based STRICTLY "
        "on the provided context documents. If the context does not contain the answer, "
        "do not guess or improvice. Say 'I don't know based on the provided documents.'"
    )
    user_prompt = f"CONTEXT DOCUMENTS:\n{context_str}\n\nUSER QUESTION: {query}\n\nANSWER:"

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set in docker-compose.yaml")

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.2 
        )
        final_answer = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation failed: {str(e)}")

    return JSONResponse(status_code=200, content={
        "project_id": project_id,
        "query": query,
        "answer": final_answer,
        "sources_cited": list(set(sources_used)),
        "raw_context_fed_to_llm": context_chunks 
    })
