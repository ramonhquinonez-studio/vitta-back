from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Article, ArticleSection


class MongoContentLibraryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_articles(self) -> list[Article]:
        cursor = self._db.content_articles.find({}).sort("order", 1)
        return [self._to_entity(doc) async for doc in cursor]

    async def list_for_owner(self, owner_id: str) -> list[Article]:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        cursor = self._db.content_articles.find({"owner_id": owner_oid}).sort("updated_at", -1)
        return [self._to_entity(doc) async for doc in cursor]

    async def create_for_owner(self, owner_id: str, payload: dict) -> Article:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        document = {
            "owner_id": owner_oid,
            "category": payload.get("category") or "",
            "title": payload["title"],
            "description": payload.get("description") or "",
            "read_time": payload.get("read_time") or "",
            "emoji": payload.get("emoji") or "📖",
            "order": 0,
            "video_url": payload.get("video_url"),
            "sections": payload.get("sections") or [],
            "updated_at": datetime.utcnow(),
        }
        result = await self._db.content_articles.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_entity(document)

    async def update_for_owner(
        self, owner_id: str, article_id: str, payload: dict
    ) -> Article | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        article_oid = self._as_oid(article_id, field_name="article")
        result = await self._db.content_articles.update_one(
            {"_id": article_oid, "owner_id": owner_oid},
            {"$set": {**payload, "updated_at": datetime.utcnow()}},
        )
        if result.matched_count == 0:
            return None
        document = await self._db.content_articles.find_one({"_id": article_oid})
        return self._to_entity(document)

    async def delete_for_owner(self, owner_id: str, article_id: str) -> bool:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        article_oid = self._as_oid(article_id, field_name="article")
        result = await self._db.content_articles.delete_one(
            {"_id": article_oid, "owner_id": owner_oid},
        )
        return result.deleted_count > 0

    def _to_entity(self, document: dict) -> Article:
        owner_id = document.get("owner_id")
        return Article(
            id=str(document["_id"]),
            category=document.get("category") or "",
            title=document["title"],
            description=document.get("description") or "",
            read_time=document.get("read_time") or "",
            emoji=document.get("emoji") or "📖",
            order=document.get("order", 0),
            sections=[
                ArticleSection(
                    title=section["title"],
                    text=section["text"],
                    bullets=section.get("bullets"),
                )
                for section in document.get("sections", [])
            ],
            owner_id=str(owner_id) if owner_id else None,
            video_url=document.get("video_url"),
        )

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)
