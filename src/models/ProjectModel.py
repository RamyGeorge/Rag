from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from .db_schemes.ProjectScheme import ProjectScheme


class ProjectModel:
    """
    Data-access layer for the `projects` MongoDB collection.
    All methods are async (motor).
    """

    COLLECTION = "projects"
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[self.COLLECTION]

    async def create_indexes(self):
        """Call once at application startup."""
        await self.collection.create_index("project_id", unique=True)

    async def get_project_or_create_one(self, project_id: str) -> ProjectScheme:
        """
        Upsert pattern: return the existing project or create a new one.
        This keeps the POST /ingest and POST /index/push endpoints idempotent.
        """
        doc = await self.collection.find_one({"project_id": project_id})
        if doc:
            return ProjectScheme.from_mongo(doc)

        project = ProjectScheme(project_id=project_id)
        result = await self.collection.insert_one(project.to_mongo())
        project.id = str(result.inserted_id)
        return project

    async def get_project(self, project_id: str) -> ProjectScheme | None:
        doc = await self.collection.find_one({"project_id": project_id})
        return ProjectScheme.from_mongo(doc) if doc else None

    async def update_files(self, project_id: str, file_names: list[str]):
        """Append new file names (avoids duplicates via $addToSet)."""
        await self.collection.update_one(
            {"project_id": project_id},
            {
                "$addToSet": {"files": {"$each": file_names}},
                "$set": {"updated_at": datetime.now()},
            },
        )

    async def update_chunk_count(self, project_id: str, count: int):
        """Overwrite the total chunk count after a fresh indexing run."""
        await self.collection.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "chunk_count": count,
                    "updated_at": datetime.now(),
                }
            },
        )

    async def delete_project(self, project_id: str) -> bool:
        result = await self.collection.delete_one({"project_id": project_id})
        return result.deleted_count > 0