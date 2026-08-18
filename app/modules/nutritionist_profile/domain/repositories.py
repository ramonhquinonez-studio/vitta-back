from typing import Protocol

from .entities import NutritionistProfile


class NutritionistProfileRepository(Protocol):
    async def get_for_owner(self, owner_id: str) -> NutritionistProfile | None:
        ...

    async def upsert_for_owner(self, owner_id: str, payload: dict) -> NutritionistProfile:
        ...

    async def count_patients_for_owner(self, owner_id: str) -> int:
        ...
