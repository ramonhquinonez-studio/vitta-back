from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user, require_role
from app.schemas.nutrition_lookup import FoodPortionOut, NutritionMatchOut

from ..application.nutrition_lookup_service import NutritionLookupService
from ..infrastructure.usda_fdc_repository import UsdaFdcRepository

router = APIRouter(
    prefix="/nutrition",
    tags=["nutrition_lookup"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_nutrition_lookup_service() -> NutritionLookupService:
    return NutritionLookupService(UsdaFdcRepository())


@router.get("/search", response_model=list[NutritionMatchOut])
async def search_nutrition(
    query: str,
    current=Depends(get_current_user),
    service: NutritionLookupService = Depends(get_nutrition_lookup_service),
):
    try:
        matches = await service.search(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [
        NutritionMatchOut(
            fdc_id=m.fdc_id,
            description=m.description,
            kcal_per_100g=m.kcal_per_100g,
            protein_per_100g=m.protein_per_100g,
            carbs_per_100g=m.carbs_per_100g,
            fat_per_100g=m.fat_per_100g,
        )
        for m in matches
    ]


@router.get("/food/{fdc_id}/portions", response_model=list[FoodPortionOut])
async def get_food_portions(
    fdc_id: int,
    current=Depends(get_current_user),
    service: NutritionLookupService = Depends(get_nutrition_lookup_service),
):
    try:
        portions = await service.get_portions(fdc_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [FoodPortionOut(description=p.description, gram_weight=p.gram_weight) for p in portions]
