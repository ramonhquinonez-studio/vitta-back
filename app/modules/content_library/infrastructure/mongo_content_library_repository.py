from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Article, ArticleSection


class MongoContentLibraryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_articles(self) -> list[Article]:
        cursor = self._db.content_articles.find({}).sort("order", 1)
        return [self._to_entity(doc) async for doc in cursor]

    def _to_entity(self, document: dict) -> Article:
        return Article(
            id=document["_id"],
            category=document["category"],
            title=document["title"],
            description=document["description"],
            read_time=document["read_time"],
            emoji=document["emoji"],
            order=document["order"],
            sections=[
                ArticleSection(
                    title=section["title"],
                    text=section["text"],
                    bullets=section.get("bullets"),
                )
                for section in document.get("sections", [])
            ],
        )
