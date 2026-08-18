from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.schemas.recipes import RecipeCollectionOut

from ..application.recipes_service import RecipesService
from ..domain.entities import Recipe, RecipeCollection
from ..infrastructure.mongo_recipes_repository import MongoRecipesRepository


router = APIRouter(prefix="/recipe_collections", tags=["recipes"])


def get_recipes_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RecipesService:
    return RecipesService(MongoRecipesRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _serialize_recipe(recipe: Recipe) -> dict:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "meal_type": recipe.meal_type,
        "minutes": recipe.minutes,
        "portions": recipe.portions,
        "kcal": recipe.kcal,
        "ingredients": recipe.ingredients,
        "steps": recipe.steps,
        "url": recipe.url,
    }


def _serialize(collection: RecipeCollection) -> dict:
    return {
        "id": collection.id,
        "title": collection.title,
        "description": collection.description,
        "recipes": [_serialize_recipe(r) for r in collection.recipes],
    }


@router.get("", response_model=list[RecipeCollectionOut])
async def list_my_recipe_collections(
    current=Depends(get_current_user),
    service: RecipesService = Depends(get_recipes_service),
):
    collections = await service.list_my_collections(_owner_id(current))
    return [_serialize(c) for c in collections]
