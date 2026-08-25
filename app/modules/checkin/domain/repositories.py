from typing import Protocol

from .entities import FormTemplate


class CheckinRepository(Protocol):
    async def create_template(self, owner_id: str, payload: dict) -> FormTemplate:
        ...

    async def list_templates(
        self, owner_id: str, *, include_archived: bool = False
    ) -> list[FormTemplate]:
        ...

    async def get_template(self, owner_id: str, template_id: str) -> FormTemplate | None:
        ...

    async def update_template(
        self, owner_id: str, template_id: str, payload: dict
    ) -> FormTemplate | None:
        ...

    async def archive_template(self, owner_id: str, template_id: str) -> bool:
        ...
