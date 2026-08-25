import unittest
from datetime import datetime

from app.modules.checkin.application.checkin_service import CheckinService
from app.modules.checkin.domain.entities import FormField, FormTemplate

_SAMPLE_FIELDS = [
    {"id": "f1", "type": "text", "label": "¿Cómo te sentiste esta semana?", "required": True, "options": []},
    {"id": "f2", "type": "scale", "label": "Energía", "required": False, "options": [], "scale_min": 1, "scale_max": 5},
]


class _FakeCheckinRepository:
    def __init__(self):
        self.templates: dict[str, FormTemplate] = {}
        self.sequence = 1

    async def create_template(self, owner_id, payload):
        template = FormTemplate(
            id=str(self.sequence),
            owner_id=owner_id,
            title=payload["title"],
            description=payload.get("description"),
            fields=[FormField(**f) for f in payload["fields"]],
            archived=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.sequence += 1
        self.templates[template.id] = template
        return template

    async def list_templates(self, owner_id, *, include_archived=False):
        items = [t for t in self.templates.values() if t.owner_id == owner_id]
        if not include_archived:
            items = [t for t in items if not t.archived]
        return items

    async def get_template(self, owner_id, template_id):
        template = self.templates.get(template_id)
        if template and template.owner_id == owner_id:
            return template
        return None

    async def update_template(self, owner_id, template_id, payload):
        current = await self.get_template(owner_id, template_id)
        if current is None:
            return None
        updated = FormTemplate(
            id=current.id,
            owner_id=current.owner_id,
            title=payload["title"],
            description=payload.get("description"),
            fields=[FormField(**f) for f in payload["fields"]],
            archived=current.archived,
            created_at=current.created_at,
            updated_at=datetime.utcnow(),
        )
        self.templates[template_id] = updated
        return updated

    async def archive_template(self, owner_id, template_id):
        current = await self.get_template(owner_id, template_id)
        if current is None:
            return False
        self.templates[template_id] = FormTemplate(
            id=current.id,
            owner_id=current.owner_id,
            title=current.title,
            description=current.description,
            fields=current.fields,
            archived=True,
            created_at=current.created_at,
            updated_at=datetime.utcnow(),
        )
        return True


class CheckinServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_template_persists_ordered_fields(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)

        template = await service.create_template(
            "owner-1", {"title": "Check-in semanal", "description": None, "fields": _SAMPLE_FIELDS}
        )

        self.assertEqual(template.title, "Check-in semanal")
        self.assertEqual(len(template.fields), 2)
        self.assertEqual(template.fields[0].id, "f1")

    async def test_create_template_rejects_a_blank_title(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)

        with self.assertRaises(ValueError):
            await service.create_template("owner-1", {"title": "", "fields": _SAMPLE_FIELDS})

    async def test_create_template_rejects_no_fields(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)

        with self.assertRaises(ValueError):
            await service.create_template("owner-1", {"title": "Vacío", "fields": []})

    async def test_create_template_rejects_an_invalid_field_type(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)
        fields = [{"id": "f1", "type": "essay", "label": "x", "required": False, "options": []}]

        with self.assertRaises(ValueError):
            await service.create_template("owner-1", {"title": "T", "fields": fields})

    async def test_create_template_rejects_a_choice_field_without_options(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)
        fields = [{"id": "f1", "type": "single_choice", "label": "x", "required": False, "options": []}]

        with self.assertRaises(ValueError):
            await service.create_template("owner-1", {"title": "T", "fields": fields})

    async def test_list_templates_excludes_archived_by_default(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)
        template = await service.create_template(
            "owner-1", {"title": "T", "fields": _SAMPLE_FIELDS}
        )
        await service.archive_template("owner-1", template.id)

        active = await service.list_templates("owner-1")
        everything = await service.list_templates("owner-1", include_archived=True)

        self.assertEqual(active, [])
        self.assertEqual(len(everything), 1)

    async def test_archive_template_rejects_a_template_not_owned(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)
        template = await service.create_template(
            "owner-1", {"title": "T", "fields": _SAMPLE_FIELDS}
        )

        with self.assertRaises(LookupError):
            await service.archive_template("owner-2", template.id)

    async def test_update_template_replaces_fields_wholesale(self):
        repo = _FakeCheckinRepository()
        service = CheckinService(repo)
        template = await service.create_template(
            "owner-1", {"title": "T", "fields": _SAMPLE_FIELDS}
        )
        new_fields = [{"id": "f1", "type": "number", "label": "Peso", "required": True, "options": []}]

        updated = await service.update_template(
            "owner-1", template.id, {"title": "T actualizado", "fields": new_fields}
        )

        self.assertEqual(updated.title, "T actualizado")
        self.assertEqual(len(updated.fields), 1)
        self.assertEqual(updated.fields[0].type, "number")


if __name__ == "__main__":
    unittest.main()
