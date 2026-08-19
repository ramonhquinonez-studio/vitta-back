import unittest
from dataclasses import replace
from datetime import datetime

from app.modules.consultations.application.consultations_service import ConsultationsService
from app.modules.consultations.domain.entities import Consultation, EvaluationSnapshot


class _FakeConsultationsRepository:
    def __init__(self):
        self.consultations: dict[str, Consultation] = {}
        self.next_id = 1

    async def find_open_draft(self, owner_id, patient_id):
        matches = [
            c
            for c in self.consultations.values()
            if c.owner_id == owner_id and c.patient_id == patient_id and c.status == "draft"
        ]
        if not matches:
            return None
        return matches[-1]

    async def create_draft(self, owner_id, *, patient_id, appointment_id):
        consultation = Consultation(
            id=str(self.next_id),
            owner_id=owner_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            status="draft",
            current_step=1,
        )
        self.consultations[consultation.id] = consultation
        self.next_id += 1
        return consultation

    async def get_for_owner(self, owner_id, consultation_id):
        consultation = self.consultations.get(consultation_id)
        if consultation and consultation.owner_id == owner_id:
            return consultation
        return None

    async def update_for_owner(self, owner_id, consultation_id, updates):
        current = await self.get_for_owner(owner_id, consultation_id)
        if current is None:
            return None
        updated = replace(current, **updates)
        self.consultations[consultation_id] = updated
        return updated

    async def update_evaluation_for_owner(self, owner_id, consultation_id, updates):
        current = await self.get_for_owner(owner_id, consultation_id)
        if current is None:
            return None
        existing = current.evaluation or EvaluationSnapshot()
        merged = replace(existing, **updates)
        return await self.update_for_owner(owner_id, consultation_id, {"evaluation": merged})

    async def update_close_for_owner(self, owner_id, consultation_id, updates):
        return await self.update_for_owner(owner_id, consultation_id, updates)

    async def complete_for_owner(self, owner_id, consultation_id):
        return await self.update_for_owner(
            owner_id,
            consultation_id,
            {"status": "completed", "completed_at": datetime(2026, 1, 1)},
        )


class ConsultationsServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_start_creates_a_new_draft_when_none_exists(self):
        service = ConsultationsService(_FakeConsultationsRepository())

        consultation = await service.start("owner-1", patient_id="patient-1", appointment_id="a-1")

        self.assertEqual(consultation.status, "draft")
        self.assertEqual(consultation.current_step, 1)
        self.assertEqual(consultation.appointment_id, "a-1")

    async def test_start_resumes_the_existing_open_draft(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        first = await service.start("owner-1", patient_id="patient-1", appointment_id=None)

        resumed = await service.start("owner-1", patient_id="patient-1", appointment_id=None)

        self.assertEqual(resumed.id, first.id)
        self.assertEqual(len(repository.consultations), 1)

    async def test_start_backfills_appointment_id_onto_an_existing_draft(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        first = await service.start("owner-1", patient_id="patient-1", appointment_id=None)

        resumed = await service.start("owner-1", patient_id="patient-1", appointment_id="a-9")

        self.assertEqual(resumed.id, first.id)
        self.assertEqual(resumed.appointment_id, "a-9")

    async def test_update_evaluation_merges_only_provided_fields(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        consultation = await service.start("owner-1", patient_id="patient-1", appointment_id=None)
        await service.update_evaluation(
            "owner-1",
            consultation.id,
            weight_kg=70,
            height_cm=None,
            body_fat_pct=None,
            waist_cm=None,
            hip_cm=None,
            arm_cm=None,
            notes=None,
        )

        updated = await service.update_evaluation(
            "owner-1",
            consultation.id,
            weight_kg=None,
            height_cm=175,
            body_fat_pct=None,
            waist_cm=None,
            hip_cm=None,
            arm_cm=None,
            notes=None,
        )

        self.assertEqual(updated.evaluation.weight_kg, 70)
        self.assertEqual(updated.evaluation.height_cm, 175)

    async def test_update_evaluation_rejects_an_empty_payload(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        consultation = await service.start("owner-1", patient_id="patient-1", appointment_id=None)

        with self.assertRaises(ValueError):
            await service.update_evaluation(
                "owner-1",
                consultation.id,
                weight_kg=None,
                height_cm=None,
                body_fat_pct=None,
                waist_cm=None,
                hip_cm=None,
                arm_cm=None,
                notes=None,
            )

    async def test_update_close_saves_private_notes_and_next_appointment(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        consultation = await service.start("owner-1", patient_id="patient-1", appointment_id=None)

        updated = await service.update_close(
            "owner-1",
            consultation.id,
            private_notes="Sigue con dolor de rodilla",
            next_appointment_id="a-2",
        )

        self.assertEqual(updated.private_notes, "Sigue con dolor de rodilla")
        self.assertEqual(updated.next_appointment_id, "a-2")

    async def test_complete_marks_the_consultation_completed(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        consultation = await service.start("owner-1", patient_id="patient-1", appointment_id=None)

        completed = await service.complete("owner-1", consultation.id)

        self.assertEqual(completed.status, "completed")
        self.assertIsNotNone(completed.completed_at)

    async def test_complete_rejects_an_already_completed_consultation(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        consultation = await service.start("owner-1", patient_id="patient-1", appointment_id=None)
        await service.complete("owner-1", consultation.id)

        with self.assertRaises(ValueError):
            await service.complete("owner-1", consultation.id)

    async def test_get_consultation_raises_when_not_found(self):
        service = ConsultationsService(_FakeConsultationsRepository())

        with self.assertRaises(LookupError):
            await service.get_consultation("owner-1", "missing")

    async def test_starting_a_new_draft_after_completion_creates_a_fresh_one(self):
        repository = _FakeConsultationsRepository()
        service = ConsultationsService(repository)
        first = await service.start("owner-1", patient_id="patient-1", appointment_id=None)
        await service.complete("owner-1", first.id)

        second = await service.start("owner-1", patient_id="patient-1", appointment_id=None)

        self.assertNotEqual(second.id, first.id)
        self.assertEqual(second.status, "draft")


if __name__ == "__main__":
    unittest.main()
