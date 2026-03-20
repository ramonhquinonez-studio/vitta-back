from datetime import datetime
from typing import Any

from ..domain.repositories import PlansRepository


class PlansService:
    def __init__(self, repository: PlansRepository):
        self._repository = repository

    async def create_plan(self, owner_id: str, payload: dict) -> dict:
        return await self._repository.create_for_owner(owner_id, payload)

    async def list_plans(self, owner_id: str, *, query: str | None = None, goal: str | None = None) -> list[dict]:
        return await self._repository.list_for_owner(owner_id, query=query, goal=goal)

    async def get_plan(self, owner_id: str, plan_id: str) -> dict:
        plan = await self._repository.get_for_owner(owner_id, plan_id)
        if plan is None:
            raise LookupError("Plan not found")
        return plan

    async def update_plan(self, owner_id: str, plan_id: str, payload: dict) -> dict:
        if not payload:
            raise ValueError("No fields to update")
        updated = await self._repository.update_for_owner(owner_id, plan_id, payload)
        if updated is None:
            raise LookupError("Plan not found")
        return updated

    async def delete_plan(self, owner_id: str, plan_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, plan_id)
        if not deleted:
            raise LookupError("Plan not found")

    async def grocery_list(self, owner_id: str, plan_id: str) -> list[dict[str, Any]]:
        plan = await self.get_plan(owner_id, plan_id)
        factor = int(plan.get("duration_days", 7))
        aggregated: dict[tuple[str, str], float] = {}

        for meal in plan.get("meals", []):
            for item in meal.get("items", []):
                key = (
                    str(item.get("name", "")).strip(),
                    str(item.get("unit", "")).strip(),
                )
                quantity = float(item.get("qty", 0.0)) * factor
                aggregated[key] = aggregated.get(key, 0.0) + quantity

        items = [
            {"name": key[0], "qty": round(value, 2), "unit": key[1]}
            for key, value in aggregated.items()
        ]
        items.sort(key=lambda item: item["name"].lower())
        return items

    async def assign_plan(self, owner_id: str, plan_id: str, patient_id: str | None) -> dict:
        if not patient_id:
            raise ValueError("patient_id is required")
        await self.get_plan(owner_id, plan_id)
        if not await self._repository.patient_exists_for_owner(owner_id, patient_id):
            raise LookupError("Patient not found")
        await self._repository.assign_plan(owner_id, plan_id, patient_id)
        return {"ok": True}
