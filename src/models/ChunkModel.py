from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import InsertOne, DeleteMany
from .db_schemes.ChunkScheme import ChunkScheme


BATCH_SIZE = 100  # Number of documents per bulk-write batch


class ChunkModel:
    """
    Data-access layer for the `chunks` MongoDB collection.
    All methods are async (motor).

    Design notes:
    - Chunks are always scoped to a project_id.
    - Bulk insertion is batched to avoid exhausting MongoDB's 16 MB document limit.
    - Pagination is used when fetching all chunks for a project (avoids OOM for large corpora).
    """

    COLLECTION = "chunks"

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[self.COLLECTION]


    async def create_indexes(self):
        """Call once at application startup."""
        await self.collection.create_index("project_id")
        await self.collection.create_index([("project_id", 1), ("chunk_order", 1)])


    async def insert_many_chunks(self, chunks: list[ChunkScheme]) -> int:
        """
        Bulk-insert chunks in batches of BATCH_SIZE.
        Returns total number of inserted documents.
        """
        inserted = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            ops = [InsertOne(chunk.to_mongo()) for chunk in batch]
            result = await self.collection.bulk_write(ops, ordered=False)
            inserted += result.inserted_count
        return inserted

    async def delete_chunks_by_project(self, project_id: str) -> int:
        """Delete all chunks belonging to a project (used for do_reset=1)."""
        result = await self.collection.bulk_write(
            [DeleteMany({"project_id": project_id})]
        )
        return result.deleted_count


    async def get_chunks_by_project(
        self,
        project_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> list[ChunkScheme]:
        """
        Paginated retrieval of chunks for a project, ordered by chunk_order.
        page is 1-indexed.
        """
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find({"project_id": project_id})
            .sort("chunk_order", 1)
            .skip(skip)
            .limit(page_size)
        )
        docs = await cursor.to_list(length=page_size)
        return [ChunkScheme.from_mongo(doc) for doc in docs]

    async def get_chunk_count(self, project_id: str) -> int:
        return await self.collection.count_documents({"project_id": project_id})

    async def get_chunk_by_id(self, chunk_id: str) -> ChunkScheme | None:
        from bson import ObjectId
        doc = await self.collection.find_one({"_id": ObjectId(chunk_id)})
        return ChunkScheme.from_mongo(doc) if doc else None