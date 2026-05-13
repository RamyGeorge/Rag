# RAG (Retrieval-Augmented Generation) System

## 📋 Project Overview

A production-ready **Retrieval-Augmented Generation (RAG)** system built with FastAPI that enables intelligent document ingestion, vectorization, and semantic search with LLM-powered responses. This system processes documents (PDF and text files), creates embeddings, stores them in a vector database, and generates contextually relevant answers using Groq's LLaMA-based LLM.

---

## 🎯 Core Features

### 1. **Document Ingestion**
   - Upload and store documents (PDF, TXT) via HTTP endpoint
   - Organized file management with project-based directories
   - Asynchronous file handling with configurable chunk sizes
   - File validation and error handling

### 2. **Document Processing Pipeline**
   - **Text Extraction:** PDFPlumber for PDF parsing, native text file reading
   - **Text Cleaning:** Comprehensive preprocessing including:
     - HTML tag and entity removal
     - URL, email, and phone number removal
     - Date, time, and currency normalization
     - Non-ASCII character filtering
     - Punctuation and special character removal
   - **Chunking:** Configurable text segmentation with overlap support (default: 500 chars/chunk, 50 char overlap)

### 3. **Vector Indexing & Semantic Search**
   - **Embedding Model:** `all-MiniLM-L6-v2` (384-dimensional vectors)
   - **Vector Database:** Qdrant for fast similarity search
   - **Distance Metric:** Cosine similarity
   - Per-project collection management
   - Batch upsert operations for efficient indexing
   - Configurable top-k retrieval (default: 5)

### 4. **RAG Query Engine**
   - Semantic search across document corpus
   - Context-aware LLM response generation using Groq's LLaMA-3.3-70B
   - Source citation and transparency
   - Strict context-adherence prompting to minimize hallucinations
   - Full context traceability in responses

### 5. **Metadata Management**
   - MongoDB-backed project and chunk metadata storage
   - Async motor driver for non-blocking database operations
   - Unique indexing on project IDs
   - Automatic timestamps for audit trails
   - Chunk ordering and file tracking

---

## 🏗️ Architecture

### Tech Stack
```
Frontend/API:    FastAPI + Uvicorn
Vector DB:       Qdrant 
Metadata DB:     MongoDB + Motor (async driver)
Embeddings:      Sentence Transformers (all-MiniLM-L6-v2)
LLM:             Groq API (LLaMA-3.3-70B)
File Processing: PDFPlumber + PyMuPDF
Containerization: Docker + Docker Compose
```

### Project Structure
```
Rag/
├── src/
│   ├── main.py                 # FastAPI app setup & lifespan management
│   ├── requirements.txt         # Python dependencies
│   ├── controllers/
│   │   ├── FileController.py    # File path management
│   │   └── ProcessController.py # Document processing pipeline
│   ├── models/
│   │   ├── ProjectModel.py      # Project data access layer
│   │   ├── ChunkModel.py        # Chunk data access layer
│   │   └── db_schemes/
│   │       ├── ProjectScheme.py # Project schema (Pydantic)
│   │       └── ChunkScheme.py   # Chunk schema (Pydantic)
│   ├── routes/
│   │   ├── data_ingestion.py    # POST /ingest/{dir_name} - File upload
│   │   ├── nlp_rag.py           # POST /index/push - Indexing & POST /index/search_rag - Query
│   │   └── Constraints.py       # Configuration constants
│   ├── helpers/
│   │   └── config.py            # Settings (Pydantic BaseSettings)
│   ├── stores/
│   │   ├── llm/                 # LLM provider integrations
│   │   └── vectordb/            # Vector DB provider integrations
│   └── assets/                  # Document storage (project folders)
└── docker/
    ├── Dockerfile              # Multi-stage app container
    └── docker-compose.yaml     # Services orchestration
```

---

## 🚀 API Endpoints

### 1. **Health Check**
```http
GET /
Response: {"message": "RAG v0.1.0 is running"}
```

### 2. **Document Upload**
```http
POST /ingest/{project_id}
Content-Type: multipart/form-data

file: <PDF or TXT file>

Response:
{
  "status": "success",
  "project_id": "my_project",
  "file_name": "document.pdf",
  "saved_to": "/app/assets/my_project/document.pdf"
}
```

### 3. **Build Vector Index**
```http
POST /index/push
Content-Type: application/json

{
  "project_id": "my_project",
  "do_reset": 0  # Set to 1 to reset existing index
}

Response:
{
  "message": "Processing complete"
}
```

### 4. **Semantic Search with RAG**
```http
POST /index/search_rag
Content-Type: application/json

{
  "project_id": "my_project",
  "query": "What is the main topic?",
  "top_k": 5  # Optional, default: 5
}

Response:
{
  "project_id": "my_project",
  "query": "What is the main topic?",
  "answer": "Based on the provided documents, ...",
  "sources_cited": ["document.pdf"],
  "raw_context_fed_to_llm": [
    "--- Document Source: document.pdf ---\nRelevant excerpt..."
  ]
}
```

---

## 🔧 Configuration

### Environment Variables (.env)
```env
# MongoDB
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DB_NAME=rag

# Qdrant Vector DB
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# API Keys
GROQ_API_KEY=gsk_YOUR_API_KEY_HERE

# File Upload
FILE_MAX_SIZE_MB=16
FILE_CHUNK_SIZE=4096

# LLM Settings
GENERATE_RESPONSE_MODEL=gpt-3.5-turbo
EMBEDDINGS_MODEL=text-embedding-ada-002
EMBEDDING_DIMENSION=1536
MAX_INPUT_TOKENS=4096
MAX_RESPONSE_TOKENS=512
TEMPERATURE=0.2
```

---

## 🐳 Quick Start

### Prerequisites
- Docker & Docker Compose
- Groq API Key (free tier available)

### Setup & Run

1. **Clone & Configure**
   ```bash
   cd Rag/
   # Edit docker/docker-compose.yaml with your GROQ_API_KEY
   ```

2. **Start Services**
   ```bash
   docker-compose -f docker/docker-compose.yaml up -d
   ```

3. **Verify Services**
   ```bash
   curl http://localhost:8000/
   ```

### Docker Services
| Service | Port | Purpose |
|---------|------|---------|
| FastAPI App | 8000 | Main API server |
| MongoDB | 27017 | Metadata storage |
| Qdrant | 6333 | Vector database |

---

## 📊 Workflow Example

### Step 1: Upload Documents
```bash
curl -X POST "http://localhost:8000/ingest/earnings_reports" \
  -F "file=@Q4_2023_Report.pdf"
```

### Step 2: Build Index
```bash
curl -X POST "http://localhost:8000/index/push" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "earnings_reports", "do_reset": 0}'
```

### Step 3: Query with RAG
```bash
curl -X POST "http://localhost:8000/index/search_rag" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "earnings_reports", "query": "What was the revenue growth?", "top_k": 5}'
```

---

## 🔍 Key Components Explained

### Text Cleaning Pipeline
The `ProcessController.clean_text()` function performs aggressive preprocessing:
- Removes HTML tags, URLs, emails, phone numbers
- Filters dates, times, currency amounts, units
- Removes non-ASCII characters and single letters
- Converts to lowercase and removes duplicated characters
- Leaves only alphanumeric content and spaces

### Chunking Strategy
- Fixed chunk size: 500 characters
- Overlap: 50 characters (prevents context loss at boundaries)
- Dynamic chunk count based on document length

### Vector Search
1. User query encoded with `all-MiniLM-L6-v2` embedding model
2. Cosine similarity search against stored embeddings in Qdrant
3. Top-k most relevant chunks retrieved
4. Context compiled into LLM prompt

### LLM Response Generation
- Model: LLaMA-3.3-70B (via Groq API)
- System Prompt: Enforces strict context adherence
- Temperature: 0.2 (deterministic, focused responses)
- Safety: Instructs model to refuse answers outside document context

---



## 📈 Performance Considerations

### Scalability
- **Async I/O:** Motor driver for non-blocking MongoDB operations
- **Batch Processing:** Qdrant upsert supports large point batches (32MB limit)
- **Vector DB:** Qdrant provides fast HNSW-based indexing
- **Containerization:** Horizontal scaling via Docker Compose orchestration

### Optimization Tips
- Increase `top_k` for broader context retrieval
- Adjust chunk `overlap` for domain-specific requirements
- Use `do_reset=1` to rebuild indices after significant document updates
- Monitor chunk extraction quality via `raw_context_fed_to_llm` response field

---


## 📝 Data Models

### ProjectScheme
```python
{
  "_id": ObjectId,
  "project_id": str (unique),
  "files": [str],           # List of processed filenames
  "chunk_count": int,       # Total chunks indexed
  "created_at": datetime,
  "updated_at": datetime
}
```

### ChunkScheme
```python
{
  "_id": ObjectId,
  "project_id": str,
  "file_name": str,
  "text": str,
  "chunk_order": int,
  "embedding": [float],     # 384-dimensional vector
  "created_at": datetime
}
```

---

## 🧪 Testing

### Manual Testing Workflow
1. Start containers: `docker-compose up`
2. Upload test document: `curl -X POST ... /ingest/test`
3. Index documents: `curl -X POST ... /index/push`
4. Query system: `curl -X POST ... /index/search_rag`
5. Verify MongoDB: `docker exec mongo mongosh rag`
6. Inspect vectors: `curl http://localhost:6333/collections`

---

## 🚧 Future Enhancements

- [ ] Multi-language support for embeddings and LLM responses
- [ ] Document metadata extraction and filtering
- [ ] Hybrid search (keyword + semantic)
- [ ] Query expansion and reformulation
- [ ] Feedback loop for answer relevance scoring
- [ ] Rate limiting and request authentication
- [ ] Batch indexing with progress tracking
- [ ] Document expiration and TTL policies
- [ ] REST client SDK (Python, JavaScript)
- [ ] Web UI for document management and querying

---



##  Contributors

- Amr Hany
- Ahmed Atta
- Ramy George
- virginia hany
- belal khaled

---

## ✅ Project Status

**Current Version:** 0.1.0 (Production-Ready MVP)

The RAG system is fully functional and ready for:
- Document knowledge base creation
- Semantic search across document collections
- Context-aware AI-powered Q&A
- Enterprise document management applications

For issues, improvements, or questions, please refer to the architecture documentation and API specifications above.

---

**Last Updated:** 2026-05-13
