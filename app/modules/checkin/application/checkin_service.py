from ..domain.entities import FormTemplate
from ..domain.repositories import CheckinRepository

_VALID_FIELD_TYPES = {"text", "number", "single_choice", "multi_choice", "scale"}


class CheckinService:
    def __init__(self, repository: CheckinRepository):
        self._repository = repository

    async def create_template(self, owner_id: str, payload: dict) -> FormTemplate:
        self._validate_template_payload(payload)
        return await self._repository.create_template(owner_id, payload)

    async def list_templates(
        self, owner_id: str, *, include_archived: bool = False
    ) -> list[FormTemplate]:
        return await self._repository.list_templates(owner_id, include_archived=include_archived)

    async def get_template(self, owner_id: str, template_id: str) -> FormTemplate:
        template = await self._repository.get_template(owner_id, template_id)
        if template is None:
            raise LookupError("Template not found")
        return template

    async def update_template(self, owner_id: str, template_id: str, payload: dict) -> FormTemplate:
        self._validate_template_payload(payload)
        template = await self._repository.update_template(owner_id, template_id, payload)
        if template is None:
            raise LookupError("Template not found")
        return template

    async def archive_template(self, owner_id: str, template_id: str) -> None:
        archived = await self._repository.archive_template(owner_id, template_id)
        if not archived:
            raise LookupError("Template not found")

    def _validate_template_payload(self, payload: dict) -> None:
        if not payload.get("title"):
            raise ValueError("title is required")
        fields = payload.get("fields") or []
        if not fields:
            raise ValueError("At least one field is required")
        for field_payload in fields:
            if field_payload.get("type") not in _VALID_FIELD_TYPES:
                raise ValueError(f"Invalid field type: {field_payload.get('type')}")
            if not field_payload.get("label"):
                raise ValueError("Every field needs a label")
            if field_payload.get("type") in {"single_choice", "multi_choice"} and not field_payload.get(
                "options"
            ):
                raise ValueError("Choice fields need at least one option")
