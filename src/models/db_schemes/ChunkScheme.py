from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class ChunkScheme(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    file_name: str

    text: str
    chunk_order: int

    embedding: Optional[list[float]] = Field(default=None)
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