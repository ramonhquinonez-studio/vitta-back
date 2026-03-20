from typing import Protocol, Any


class PlansRepository(Protocol):
    async def create_for_owner(self, owner_id: str, payload: dict) -> dict:
        ...

    async def list_for_owner(self, owner_id: str, *, query: str | None = None, goal: str | None = None) -> list[dict]:
        ...

    async def get_for_owner(self, owner_id: str, plan_id: str) -> dict | None:
        ...

    async def update_for_owner(self, owner_id: str, plan_id: str, payload: dict) -> dict | None:
        ...

    async def delete_for_owner(self, owner_id: str, plan_id: str) -> bool:
        ...

    async def patient_exists_for_owner(self, owner_id: str, patient_id: str) -> bool:
        ...

    async def assign_plan(self, owner_id: str, plan_id: str, patient_id: str) -> None:
        ...
