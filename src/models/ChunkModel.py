from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import InsertOne, DeleteMany
from .db_schemes.ChunkScheme import ChunkScheme
from bson import ObjectId

BATCH_SIZE = 100

class ChunkModel:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["chunks"]

    async def create_indexes(self):
        await self.collection.create_index("project_id")
        await self.collection.create_index([("project_id", 1), ("chunk_order", 1)])

    #processing chunks in batches
    async def insert_many_chunks(self, chunks: list[ChunkScheme]) -> int:
        inserted = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            ops = [InsertOne(chunk.to_mongo()) for chunk in batch]
            result = await self.collection.bulk_write(ops, ordered=False)
            inserted += result.inserted_count
        return inserted

    #deleting all content the chunks by project_id
    async def delete_chunks_by_project(self, project_id: str) -> int:
        result = await self.collection.delete_many({"project_id": project_id})
        return result.deleted_count

    async def get_chunks_by_project(
        self,
        project_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> list[ChunkScheme]:
        skip_len = (page - 1) * page_size
        query = (
            self.collection.find({"project_id": project_id})
            .sort("chunk_order", 1).skip(skip_len).limit(page_size)
        )
        docs = await query.to_list(length=page_size)
        return [ChunkScheme.from_mongo(doc) for doc in docs]

    async def get_chunk_count(self, project_id: str) -> int:
        return await self.collection.count_documents({"project_id": project_id})

    async def get_chunk_by_id(self, chunk_id: str) -> ChunkScheme | None:
        doc = await self.collection.find_one({"_id": ObjectId(chunk_id)})
        return ChunkScheme.from_mongo(doc) if doc else None