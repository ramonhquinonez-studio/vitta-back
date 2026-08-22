from datetime import datetime
from typing import Protocol, Any


class MeRepository(Protocol):
    async def get_user(self, user_id: str) -> dict | None:
        ...

    async def get_patient_for_user(self, user_id: str) -> dict | None:
        ...

    async def update_patient_profile(self, patient_id: str, payload: dict) -> dict | None:
        ...

    async def list_appointments(
        self,
        patient_id: str,
        *,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[dict]:
        ...

    async def get_active_plan(self, patient_id: str) -> dict | None:
        ...

    async def find_owner_overlap(
        self,
        owner_id: str,
        *,
        start: datetime,
        end: datetime,
        exclude_appointment_id: str | None = None,
    ) -> dict | None:
        ...

    async def create_patient_appointment(
        self,
        *,
        owner_id: str,
        patient_id: str,
        start: datetime,
        end: datetime,
        mode: str,
        note: str | None,
    ) -> dict:
        ...

    async def get_patient_appointment(self, patient_id: str, appointment_id: str) -> dict | None:
        ...

    async def update_patient_appointment(self, patient_id: str, appointment_id: str, updates: dict) -> dict | None:
        ...

    async def list_measurements(self, patient_id: str, *, limit: int) -> list[dict]:
        ...

    async def create_measurement(self, *, owner_id: str | None, patient_id: str, payload: dict) -> dict:
        ...

    async def list_measurements_since(self, patient_id: str, *, since: datetime) -> list[dict]:
        ...

    async def list_prescriptions(self, patient_id: str, *, limit: int) -> list[dict]:
        ...

    async def list_recipe_collections(self, owner_id: str | None) -> list[dict]:
        ...

    async def get_recipe_for_owner(self, owner_id: str | None, recipe_id: str) -> dict | None:
        ...

    async def list_education_videos(self, owner_id: str | None) -> list[dict]:
        ...

    async def list_articles(self, owner_id: str | None) -> list[dict]:
        ...

    async def get_nutritionist_profile(self, owner_id: str | None) -> dict | None:
        ...

    async def list_clinical_notes(self, patient_id: str) -> list[dict]:
        ...

    async def list_body_compositions(self, patient_id: str) -> list[dict]:
        ...

    async def get_body_composition_by_id(self, body_composition_id: str) -> dict | None:
        ...

    async def get_plan_summary(self, plan_id: str) -> dict | None:
        ...

    async def list_food_diary_entries(self, patient_id: str, *, limit: int) -> list[dict]:
        ...

    async def create_food_diary_entry(
        self, *, owner_id: str | None, patient_id: str, payload: dict
    ) -> dict:
        ...

    async def list_recommendations(
        self, owner_id: str | None, *, kind: str | None = None
    ) -> list[dict]:
        ...

    async def get_hydration_today(self, patient_id: str) -> dict:
        ...

    async def add_hydration(self, patient_id: str, *, delta_ml: int) -> dict:
        ...
