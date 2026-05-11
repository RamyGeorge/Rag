from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from .db_schemes.ProjectScheme import ProjectScheme

class ProjectModel:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["projects"]

    async def create_indexes(self):
        # indexing using project_id
        await self.collection.create_index("project_id", unique=True)

    async def get_project_or_create_one(self, project_id: str) -> ProjectScheme:
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
        await self.collection.update_one(
            {"project_id": project_id},
            {
                "$addToSet": {"files": {"$each": file_names}},
                "$set": {"updated_at": datetime.now()},
            },
        )

    async def update_chunk_count(self, project_id: str, count: int):
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