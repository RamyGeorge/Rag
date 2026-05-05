from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from helpers.config import settings
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from routes.data_ingestion import router as ingestion_router
from routes.nlp_rag import router as nlp_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    app.state.db = db
    app.state.project_model = ProjectModel(db)
    app.state.chunk_model = ChunkModel(db)

    await app.state.project_model.create_indexes()
    await app.state.chunk_model.create_indexes()

    print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")

    yield

    client.close()
    print("MongoDB connection closed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(ingestion_router)
app.include_router(nlp_router)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} v{settings.APP_VERSION} is running"}