from typing import Protocol

from .entities import AuthUser


class AuthRepository(Protocol):
    async def get_user_by_email(self, email: str) -> AuthUser | None:
        ...

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        ...

    async def create_user(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> AuthUser:
        ...

    async def get_invite_code(self, code: str) -> dict | None:
        ...

    async def consume_invite_code(self, code: str, user_id: str) -> None:
        ...

    async def create_patient_for_user(
        self,
        *,
        user_id: str,
        owner_id: str,
        name: str,
    ) -> None:
        ...

    async def link_user_to_patient(self, *, user_id: str, patient_id: str) -> bool:
        ...

    async def create_unowned_patient_for_user(self, *, user_id: str, name: str) -> str:
        """Self-registration with no nutritionist yet. Returns the generated
        connection code for the patient to share so a nutritionist can claim
        them later (`PatientsRepository.claim_patient`)."""
        ...

    async def get_patient_name(self, patient_id: str) -> str | None:
        ...

    async def update_password_hash(self, user_id: str, password_hash: str) -> None:
        ...
