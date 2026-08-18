from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Recipe, RecipeCollection


class MongoRecipesRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_for_owner(self, owner_id: str) -> list[RecipeCollection]:
        owner_oid = self._as_oid(owner_id)
        cursor = self._db.recipe_collections.find({"owner_id": owner_oid}).sort("updated_at", -1)
        return [self._to_entity(doc) async for doc in cursor]

    def _to_entity(self, document: dict) -> RecipeCollection:
        return RecipeCollection(
            id=str(document["_id"]),
            owner_id=str(document["owner_id"]),
            title=document.get("title") or "",
            description=document.get("description"),
            recipes=[self._recipe_from_dict(r) for r in document.get("recipes", [])],
        )

    def _recipe_from_dict(self, recipe: dict) -> Recipe:
        return Recipe(
            id=str(recipe.get("id") or recipe.get("_id") or ""),
            title=recipe.get("title") or "",
            meal_type=recipe.get("meal_type"),
            minutes=recipe.get("minutes"),
            portions=recipe.get("portions"),
            kcal=recipe.get("kcal"),
            ingredients=list(recipe.get("ingredients") or []),
            steps=list(recipe.get("steps") or []),
            url=recipe.get("url"),
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid owner id")
        return ObjectId(id_str)
