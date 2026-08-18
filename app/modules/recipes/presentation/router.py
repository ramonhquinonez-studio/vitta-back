from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.schemas.recipes import (
    RecipeCollectionCreate,
    RecipeCollectionOut,
    RecipeCollectionUpdate,
    RecipeIn,
    RecipeUpdate,
)

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


@router.post("", response_model=RecipeCollectionOut, status_code=201)
async def create_recipe_collection(
    payload: RecipeCollectionCreate,
    current=Depends(get_current_user),
    service: RecipesService = Depends(get_recipes_service),
):
    try:
        collection = await service.create_collection(_owner_id(current), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(collection)


@router.patch("/{collection_id}", response_model=RecipeCollectionOut)
async def update_recipe_collection(
    collection_id: str,
    payload: RecipeCollectionUpdate,
    current=Depends(get_current_user),
    service: RecipesService = Depends(get_recipes_service),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        collection = await service.update_collection(_owner_id(current), collection_id, updates)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(collection)


@router.delete("/{collection_id}")
async def delete_recipe_collection(
    collection_id: str,
    current=Depends(get_current_user),
    service: RecipesService = Depends(get_recipes_service),
):
    try:
        await service.delete_collection(_owner_id(current), collection_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/{collection_id}/recipes", response_model=RecipeCollectionOut, status_code=201)
async def add_recipe(
    collection_id: str,
    payload: RecipeIn,
    current=Depends(get_current_user),
    service: RecipesService = Depends(get_recipes_service),
):
    try:
        collection = await service.add_recipe(_owner_id(current), collection_id, payload.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(collection)


@router.patch("/{collection_id}/recipes/{recipe_id}", response_model=RecipeCollectionOut)
async def update_recipe(
    collection_id: str,
    recipe_id: str,
    payload: RecipeUpdate,
    current=Depends(get_current_user),
    service: RecipesService = Depends(get_recipes_service),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        collection = await service.update_recipe(
            _owner_id(current), collection_id, recipe_id, updates
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(collection)


@router.delete("/{collection_id}/recipes/{recipe_id}", response_model=RecipeCollectionOut)
async def delete_recipe(
    collection_id: str,
    recipe_id: str,
    current=Depends(get_current_user),
    service: RecipesService = Depends(get_recipes_service),
):
    try:
        collection = await service.delete_recipe(_owner_id(current), collection_id, recipe_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize(collection)
