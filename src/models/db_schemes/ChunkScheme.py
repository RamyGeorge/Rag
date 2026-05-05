from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class ChunkScheme(BaseModel):
    """
    Represents a single text chunk document in MongoDB.
    Each chunk is a processed fragment of a file belonging to a project.

    Collection: chunks

    Indexes (to be created at startup):
        - project_id  (for fast project-scoped queries)
        - chunk_order (for ordered retrieval within a file)
    """

    id: Optional[str] = Field(default=None, alias="_id")


    project_id: str = Field(..., description="References ProjectScheme.project_id")
    file_name: str = Field(..., description="Source file this chunk was extracted from")

    text: str = Field(..., description="Cleaned text content of the chunk")
    chunk_order: int = Field(..., description="Zero-based position of this chunk within its source file")

    embedding: Optional[list[float]] = Field(
        default=None,
        description="Dense vector produced by the embedding model. Null until /index/push is called."
    )

    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    def to_mongo(self) -> dict:
        return self.model_dump(exclude={"id"})

    @staticmethod
    def from_mongo(doc: dict) -> "ChunkScheme":
        if doc is None:
            return None
        doc["_id"] = str(doc["_id"])
        return ChunkScheme(**doc)