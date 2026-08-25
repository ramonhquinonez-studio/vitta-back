import unittest

from app.modules.workout_plans.application.workout_plans_service import WorkoutPlansService

_SAMPLE_DAYS = [
    {"label": "Día 1 - Piernas", "exercises": [{"name": "Sentadilla", "sets": 4, "reps": 10}]},
]


class _FakeWorkoutPlansRepository:
    def __init__(self):
        self.plans: dict[str, dict] = {}
        self.sequence = 1
        self.owned_patients: set[tuple[str, str]] = {("owner-1", "patient-1")}
        self.assignments: list[dict] = []

    async def create_for_owner(self, owner_id, payload):
        plan = {
            "id": str(self.sequence),
            "owner_id": owner_id,
            "name": payload["name"],
            "goal": payload.get("goal"),
            "days": payload["days"],
        }
        self.sequence += 1
        self.plans[plan["id"]] = plan
        return plan

    async def list_for_owner(self, owner_id):
        return [p for p in self.plans.values() if p["owner_id"] == owner_id]

    async def get_for_owner(self, owner_id, plan_id):
        plan = self.plans.get(plan_id)
        if plan and plan["owner_id"] == owner_id:
            return plan
        return None

    async def update_for_owner(self, owner_id, plan_id, payload):
        current = await self.get_for_owner(owner_id, plan_id)
        if current is None:
            return None
        updated = {**current, **payload}
        self.plans[plan_id] = updated
        return updated

    async def delete_for_owner(self, owner_id, plan_id):
        current = await self.get_for_owner(owner_id, plan_id)
        if current is None:
            return False
        del self.plans[plan_id]
        return True

    async def patient_exists_for_owner(self, owner_id, patient_id):
        return (owner_id, patient_id) in self.owned_patients

    async def assign_plan(self, owner_id, plan_id, patient_id):
        self.assignments.append({"owner_id": owner_id, "plan_id": plan_id, "patient_id": patient_id})


class WorkoutPlansServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_plan_persists_days_and_exercises(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)

        plan = await service.create_plan("owner-1", {"name": "Rutina full body", "days": _SAMPLE_DAYS})

        self.assertEqual(plan["name"], "Rutina full body")
        self.assertEqual(len(plan["days"]), 1)
        self.assertEqual(plan["days"][0]["exercises"][0]["name"], "Sentadilla")

    async def test_create_plan_rejects_a_blank_name(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)

        with self.assertRaises(ValueError):
            await service.create_plan("owner-1", {"name": "", "days": _SAMPLE_DAYS})

    async def test_create_plan_rejects_no_days(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)

        with self.assertRaises(ValueError):
            await service.create_plan("owner-1", {"name": "Vacío", "days": []})

    async def test_create_plan_rejects_an_exercise_without_a_name(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)
        days = [{"label": "Día 1", "exercises": [{"name": "", "sets": 3}]}]

        with self.assertRaises(ValueError):
            await service.create_plan("owner-1", {"name": "T", "days": days})

    async def test_get_plan_rejects_a_plan_not_owned(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)
        plan = await service.create_plan("owner-1", {"name": "T", "days": _SAMPLE_DAYS})

        with self.assertRaises(LookupError):
            await service.get_plan("owner-2", plan["id"])

    async def test_delete_plan_rejects_a_plan_not_owned(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)
        plan = await service.create_plan("owner-1", {"name": "T", "days": _SAMPLE_DAYS})

        with self.assertRaises(LookupError):
            await service.delete_plan("owner-2", plan["id"])

    async def test_assign_plan_requires_a_patient_id(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)
        plan = await service.create_plan("owner-1", {"name": "T", "days": _SAMPLE_DAYS})

        with self.assertRaises(ValueError):
            await service.assign_plan("owner-1", plan["id"], None)

    async def test_assign_plan_rejects_a_patient_not_owned(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)
        plan = await service.create_plan("owner-1", {"name": "T", "days": _SAMPLE_DAYS})

        with self.assertRaises(LookupError):
            await service.assign_plan("owner-1", plan["id"], "patient-999")

    async def test_assign_plan_records_the_assignment(self):
        repo = _FakeWorkoutPlansRepository()
        service = WorkoutPlansService(repo)
        plan = await service.create_plan("owner-1", {"name": "T", "days": _SAMPLE_DAYS})

        result = await service.assign_plan("owner-1", plan["id"], "patient-1")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(len(repo.assignments), 1)
        self.assertEqual(repo.assignments[0]["patient_id"], "patient-1")


if __name__ == "__main__":
    unittest.main()
