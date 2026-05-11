from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from bson.json_util import dumps

class ProjectScheme(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
        
    files: list[str] = Field(default_factory=list)
    chunk_count: int = Field(default=0)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    def to_mongo(self) -> dict:
        data = self.model_dump(exclude={"id"})
        return data

    @staticmethod
    def from_mongo(doc: dict) -> "ProjectScheme":
        if doc is None:
            return None
        doc["_id"] = str(doc["_id"])
        return ProjectScheme(**doc)