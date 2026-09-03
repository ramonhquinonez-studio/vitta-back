from datetime import datetime
from uuid import uuid4

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Recipe, RecipeCollection


class MongoRecipesRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_for_owner(self, owner_id: str) -> list[RecipeCollection]:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        cursor = self._db.recipe_collections.find({"owner_id": owner_oid}).sort("updated_at", -1)
        return [self._to_entity(doc) async for doc in cursor]

    async def create_collection(self, owner_id: str, payload: dict) -> RecipeCollection:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        document = {
            "owner_id": owner_oid,
            "title": payload["title"],
            "description": payload.get("description"),
            "recipes": [],
            "updated_at": datetime.utcnow(),
        }
        result = await self._db.recipe_collections.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_entity(document)

    async def update_collection(
        self, owner_id: str, collection_id: str, payload: dict
    ) -> RecipeCollection | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        collection_oid = self._as_oid(collection_id, field_name="collection")
        result = await self._db.recipe_collections.update_one(
            {"_id": collection_oid, "owner_id": owner_oid},
            {"$set": {**payload, "updated_at": datetime.utcnow()}},
        )
        if result.matched_count == 0:
            return None
        document = await self._db.recipe_collections.find_one({"_id": collection_oid})
        return self._to_entity(document)

    async def delete_collection(self, owner_id: str, collection_id: str) -> bool:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        collection_oid = self._as_oid(collection_id, field_name="collection")
        result = await self._db.recipe_collections.delete_one(
            {"_id": collection_oid, "owner_id": owner_oid},
        )
        return result.deleted_count > 0

    async def add_recipe(
        self, owner_id: str, collection_id: str, payload: dict
    ) -> RecipeCollection | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        collection_oid = self._as_oid(collection_id, field_name="collection")
        recipe = {
            "id": uuid4().hex,
            "title": payload["title"],
            "meal_type": payload.get("meal_type"),
            "minutes": payload.get("minutes"),
            "portions": payload.get("portions"),
            "kcal": payload.get("kcal"),
            "ingredients": payload.get("ingredients") or [],
            "steps": payload.get("steps") or [],
            "url": payload.get("url"),
            "eating_out_option": payload.get("eating_out_option"),
        }
        result = await self._db.recipe_collections.update_one(
            {"_id": collection_oid, "owner_id": owner_oid},
            {
                "$push": {"recipes": recipe},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        if result.matched_count == 0:
            return None
        document = await self._db.recipe_collections.find_one({"_id": collection_oid})
        return self._to_entity(document)

    async def update_recipe(
        self, owner_id: str, collection_id: str, recipe_id: str, payload: dict
    ) -> RecipeCollection | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        collection_oid = self._as_oid(collection_id, field_name="collection")
        field_updates = {f"recipes.$[r].{key}": value for key, value in payload.items()}
        result = await self._db.recipe_collections.update_one(
            {"_id": collection_oid, "owner_id": owner_oid},
            {"$set": {**field_updates, "updated_at": datetime.utcnow()}},
            array_filters=[{"r.id": recipe_id}],
        )
        if result.matched_count == 0:
            return None
        document = await self._db.recipe_collections.find_one({"_id": collection_oid})
        return self._to_entity(document)

    async def delete_recipe(
        self, owner_id: str, collection_id: str, recipe_id: str
    ) -> RecipeCollection | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        collection_oid = self._as_oid(collection_id, field_name="collection")
        result = await self._db.recipe_collections.update_one(
            {"_id": collection_oid, "owner_id": owner_oid},
            {
                "$pull": {"recipes": {"id": recipe_id}},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        if result.matched_count == 0:
            return None
        document = await self._db.recipe_collections.find_one({"_id": collection_oid})
        return self._to_entity(document)

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
            eating_out_option=recipe.get("eating_out_option"),
        )

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)
