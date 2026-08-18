from ..domain.entities import Patient
from ..domain.repositories import PatientsRepository


class PatientsService:
    def __init__(self, repository: PatientsRepository):
        self._repository = repository

    async def list_patients(
        self,
        owner_id: str,
        *,
        page: int,
        limit: int,
        query: str | None = None,
    ) -> tuple[list[Patient], int]:
        return await self._repository.list_for_owner(
            owner_id,
            page=page,
            limit=limit,
            query=query,
        )

    async def create_patient(self, owner_id: str, payload: dict) -> Patient:
        return await self._repository.create_for_owner(owner_id, payload)

    async def get_patient(self, owner_id: str, patient_id: str) -> Patient:
        patient = await self._repository.get_for_owner(owner_id, patient_id)
        if patient is None:
            raise LookupError("Patient not found")
        return patient

    async def update_patient(self, owner_id: str, patient_id: str, payload: dict) -> Patient:
        if not payload:
            raise ValueError("No fields to update")
        patient = await self._repository.update_for_owner(owner_id, patient_id, payload)
        if patient is None:
            raise LookupError("Patient not found")
        return patient

    async def delete_patient(self, owner_id: str, patient_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, patient_id)
        if not deleted:
            raise LookupError("Patient not found")

    async def add_body_composition(self, owner_id: str, patient_id: str, payload: dict) -> dict:
        created = await self._repository.add_body_composition(owner_id, patient_id, payload)
        if created is None:
            raise LookupError("Patient not found")
        return created

    async def list_body_compositions(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_body_compositions(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def create_invite_code(self, owner_id: str) -> dict:
        return await self._repository.create_invite_code(owner_id)
