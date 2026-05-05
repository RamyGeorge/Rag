"""
TIP: Implement the Settings class using pydantic_settings to load configuration from the .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Loads all configuration from the .env file (or environment variables).
    pydantic-settings automatically maps env var names to field names
    (case-insensitive).
    """

    APP_NAME: str = "RAG"
    APP_VERSION: str = "0.1.0"

    FILE_ALLOWED_EXTENSIONS: list[str] = Field(
        default=["plain/text", "application/pdf"],
        description="MIME types allowed for upload"
    )
    FILE_MAX_SIZE_MB: int = 16
    FILE_CHUNK_SIZE: int = 4096

    MONGODB_URI: str = "mongodb://mongodb:27017"
    MONGODB_DB_NAME: str = "rag"

    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = ""
    GENERATE_RESPONSE_MODEL: str = "gpt-3.5-turbo"
    EMBEDDINGS_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536
    MAX_INPUT_TOKENS: int = 4096
    MAX_RESPONSE_TOKENS: int = 512
    TEMPERATURE: float = 0.2

    VECTOR_DB_PATH: str = "./vectordb"
    VECTOR_DISTANCE_METRIC: str = "cosine"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()