import unittest

from app.modules.plans.application.plans_service import PlansService
from app.schemas.plan import PlanCreate


class _FakePlansRepository:
    def __init__(self):
        self.plan = {
            "id": "plan-1",
            "name": "Base",
            "goal": "custom",
            "duration_days": 3,
            "meals": [
                {
                    "title": "Desayuno",
                    "items": [
                        {"name": "Avena", "qty": 1, "unit": "taza"},
                        {"name": "Platano", "qty": 2, "unit": "pieza"},
                    ],
                },
                {
                    "title": "Cena",
                    "items": [
                        {"name": "Avena", "qty": 0.5, "unit": "taza"},
                    ],
                },
            ],
            "created_at": None,
            "updated_at": None,
        }

    async def create_for_owner(self, owner_id, payload):
        return self.plan

    async def list_for_owner(self, owner_id, *, query=None, goal=None):
        return [self.plan]

    async def get_for_owner(self, owner_id, plan_id):
        return self.plan if plan_id == "plan-1" else None

    async def update_for_owner(self, owner_id, plan_id, payload):
        return self.plan if plan_id == "plan-1" else None

    async def delete_for_owner(self, owner_id, plan_id):
        return plan_id == "plan-1"

    async def patient_exists_for_owner(self, owner_id, patient_id):
        return patient_id == "patient-1"

    async def assign_plan(self, owner_id, plan_id, patient_id):
        return None

    async def set_attachment_for_owner(
        self, owner_id, plan_id, attachment_url, attachment_type
    ):
        if plan_id != "plan-1":
            return None
        self.plan = {
            **self.plan,
            "attachment_url": attachment_url,
            "attachment_type": attachment_type,
        }
        return self.plan


class PlansServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_grocery_list_aggregates_items_by_duration(self):
        service = PlansService(_FakePlansRepository())

        items = await service.grocery_list("owner-1", "plan-1")

        self.assertEqual(
            items,
            [
                {"name": "Avena", "qty": 4.5, "unit": "taza"},
                {"name": "Platano", "qty": 6.0, "unit": "pieza"},
            ],
        )

    async def test_assign_plan_requires_patient_id(self):
        service = PlansService(_FakePlansRepository())

        with self.assertRaises(ValueError):
            await service.assign_plan("owner-1", "plan-1", None)

    async def test_set_attachment_updates_plan(self):
        service = PlansService(_FakePlansRepository())

        updated = await service.set_attachment(
            "owner-1", "plan-1", "/uploads/plans/plan-1/x.pdf", "application/pdf"
        )

        self.assertEqual(updated["attachment_url"], "/uploads/plans/plan-1/x.pdf")
        self.assertEqual(updated["attachment_type"], "application/pdf")

    async def test_set_attachment_missing_plan_raises(self):
        service = PlansService(_FakePlansRepository())

        with self.assertRaises(LookupError):
            await service.set_attachment(
                "owner-1", "missing", "/uploads/x.pdf", "application/pdf"
            )


class PlanSchemaTest(unittest.TestCase):
    def test_plan_create_parses_eating_out_options_per_meal(self):
        payload = PlanCreate(
            name="Plan",
            duration_days=7,
            meals=[
                {
                    "title": "Desayuno",
                    "items": [],
                    "eating_out_options": [
                        {
                            "restaurant": "Subway",
                            "dish": "Sandwich de pavo 6\"",
                            "kcal": 320,
                            "protein": 22.5,
                        }
                    ],
                },
                {"title": "Cena", "items": []},
            ],
        )

        dumped = payload.model_dump()

        self.assertEqual(len(dumped["meals"][0]["eating_out_options"]), 1)
        self.assertEqual(
            dumped["meals"][0]["eating_out_options"][0]["restaurant"], "Subway"
        )
        self.assertEqual(dumped["meals"][1]["eating_out_options"], [])
