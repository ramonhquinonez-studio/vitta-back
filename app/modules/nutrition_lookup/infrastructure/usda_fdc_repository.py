import requests

from app.core.config import settings

from ..domain.entities import FoodPortion, NutritionMatch

_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
_FOOD_URL = "https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
_NUTRIENT_NUMBERS = {"203": "protein", "204": "fat", "205": "carbs", "208": "kcal"}


def _get_with_retry(url: str, params: dict) -> requests.Response:
    """The upstream endpoint occasionally returns a transient 404 (an
    api.data.gov gateway hiccup, not a real not-found) — one retry clears it.
    """
    response = None
    for attempt in range(2):
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response
    raise RuntimeError(f"USDA FoodData Central request failed: {response.status_code if response else 'no response'}")


class UsdaFdcRepository:
    """Looks up real nutrient composition and portion weights from USDA
    FoodData Central."""

    async def search(self, query: str, limit: int = 10) -> list[NutritionMatch]:
        params = {
            "api_key": settings.USDA_FDC_API_KEY,
            "query": query,
            "dataType": "SR Legacy,Foundation",
            "pageSize": limit,
        }
        response = _get_with_retry(_SEARCH_URL, params)

        matches = []
        for food in response.json().get("foods", []):
            values: dict[str, float] = {}
            for nutrient in food.get("foodNutrients", []):
                key = _NUTRIENT_NUMBERS.get(str(nutrient.get("nutrientNumber")))
                if key:
                    values[key] = nutrient.get("value")
            matches.append(
                NutritionMatch(
                    fdc_id=food["fdcId"],
                    description=food["description"],
                    kcal_per_100g=values.get("kcal"),
                    protein_per_100g=values.get("protein"),
                    carbs_per_100g=values.get("carbs"),
                    fat_per_100g=values.get("fat"),
                )
            )
        return matches

    async def get_portions(self, fdc_id: int) -> list[FoodPortion]:
        response = _get_with_retry(_FOOD_URL.format(fdc_id=fdc_id), {"api_key": settings.USDA_FDC_API_KEY})

        portions = []
        for portion in response.json().get("foodPortions", []):
            gram_weight = portion.get("gramWeight")
            if not gram_weight:
                continue
            amount = portion.get("amount")
            modifier = portion.get("modifier") or (portion.get("measureUnit") or {}).get("name")
            description = " ".join(str(p) for p in (amount, modifier) if p and str(p) != "undetermined")
            if not description:
                continue
            portions.append(FoodPortion(description=description, gram_weight=gram_weight))
        return portions
