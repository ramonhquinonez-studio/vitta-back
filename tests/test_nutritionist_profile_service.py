import unittest
from datetime import datetime

from app.modules.nutritionist_profile.application.nutritionist_profile_service import (
    NutritionistProfileService,
)
from app.modules.nutritionist_profile.domain.entities import (
    MacroSplit,
    NutritionistProfile,
    SocialLink,
)


class _FakeNutritionistProfileRepository:
    def __init__(self):
        self.profiles: dict[str, NutritionistProfile] = {}
        self.patient_counts: dict[str, int] = {}

    async def get_for_owner(self, owner_id):
        return self.profiles.get(owner_id)

    async def upsert_for_owner(self, owner_id, payload):
        current = self.profiles.get(owner_id) or NutritionistProfile(owner_id=owner_id)
        social_links = [
            SocialLink(platform=link["platform"], handle=link["handle"])
            for link in payload.get("social_links", [
                {"platform": l.platform, "handle": l.handle} for l in current.social_links
            ])
        ]
        macro_split_payload = payload.get("macro_split", "__unset__")
        if macro_split_payload == "__unset__":
            macro_split = current.macro_split
        elif macro_split_payload is None:
            macro_split = None
        else:
            macro_split = MacroSplit(**macro_split_payload)
        updated = NutritionistProfile(
            owner_id=owner_id,
            role_label=payload.get("role_label", current.role_label),
            bio=payload.get("bio", current.bio),
            years_experience=payload.get("years_experience", current.years_experience),
            session_price=payload.get("session_price", current.session_price),
            session_price_currency=payload.get(
                "session_price_currency", current.session_price_currency
            ),
            social_links=social_links,
            cedula=payload.get("cedula", current.cedula),
            practice_name=payload.get("practice_name", current.practice_name),
            logo_url=payload.get("logo_url", current.logo_url),
            brand_color=payload.get("brand_color", current.brand_color),
            city=payload.get("city", current.city),
            specializations=payload.get("specializations", current.specializations),
            energy_equation=payload.get("energy_equation", current.energy_equation),
            portions_mode=payload.get("portions_mode", current.portions_mode),
            macro_split=macro_split,
            units=payload.get("units", current.units),
            meals_per_day=payload.get("meals_per_day", current.meals_per_day),
            onboarding_completed_at=payload.get(
                "onboarding_completed_at", current.onboarding_completed_at
            ),
        )
        self.profiles[owner_id] = updated
        return updated

    async def count_patients_for_owner(self, owner_id):
        return self.patient_counts.get(owner_id, 0)

    async def mark_onboarding_completed(self, owner_id):
        return await self.upsert_for_owner(
            owner_id, {"onboarding_completed_at": datetime(2026, 8, 19, 12, 0, 0)}
        )


class NutritionistProfileServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_my_profile_returns_defaults_when_none_saved_yet(self):
        repository = _FakeNutritionistProfileRepository()
        repository.patient_counts["owner-1"] = 3
        service = NutritionistProfileService(repository)

        result = await service.get_my_profile("owner-1")

        self.assertIsNone(result["role_label"])
        self.assertEqual(result["session_price_currency"], "MXN")
        self.assertEqual(result["social_links"], [])
        self.assertEqual(result["patient_count"], 3)

    async def test_update_my_profile_saves_fields_and_reports_patient_count(self):
        repository = _FakeNutritionistProfileRepository()
        repository.patient_counts["owner-1"] = 5
        service = NutritionistProfileService(repository)

        result = await service.update_my_profile(
            "owner-1",
            {
                "role_label": "Nutrióloga clínica",
                "bio": "12 años ayudando a mis pacientes.",
                "years_experience": 12,
                "session_price": 650.0,
                "session_price_currency": "MXN",
                "social_links": [{"platform": "instagram", "handle": "@dra.ruiz"}],
            },
        )

        self.assertEqual(result["role_label"], "Nutrióloga clínica")
        self.assertEqual(result["years_experience"], 12)
        self.assertEqual(result["session_price"], 650.0)
        self.assertEqual(result["social_links"], [{"platform": "instagram", "handle": "@dra.ruiz"}])
        self.assertEqual(result["patient_count"], 5)

    async def test_update_my_profile_rejects_an_empty_payload(self):
        repository = _FakeNutritionistProfileRepository()
        service = NutritionistProfileService(repository)

        with self.assertRaises(ValueError):
            await service.update_my_profile("owner-1", {})

    async def test_get_profile_for_owner_returns_none_when_never_saved(self):
        repository = _FakeNutritionistProfileRepository()
        service = NutritionistProfileService(repository)

        result = await service.get_profile_for_owner("owner-1")

        self.assertIsNone(result)

    async def test_update_my_profile_saves_onboarding_fields(self):
        repository = _FakeNutritionistProfileRepository()
        service = NutritionistProfileService(repository)

        result = await service.update_my_profile(
            "owner-1",
            {
                "cedula": "1234567",
                "practice_name": "Consultorio Vitta",
                "city": "CDMX",
                "specializations": ["clinica", "deportiva"],
                "energy_equation": "mifflin",
                "portions_mode": "equivalentes",
                "macro_split": {"protein_pct": 30.0, "carbs_pct": 40.0, "fat_pct": 30.0},
                "units": "metric",
                "meals_per_day": 5,
            },
        )

        self.assertEqual(result["cedula"], "1234567")
        self.assertEqual(result["practice_name"], "Consultorio Vitta")
        self.assertEqual(result["specializations"], ["clinica", "deportiva"])
        self.assertEqual(result["energy_equation"], "mifflin")
        self.assertEqual(result["portions_mode"], "equivalentes")
        self.assertEqual(result["macro_split"]["protein_pct"], 30.0)
        self.assertEqual(result["meals_per_day"], 5)
        self.assertIsNone(result["onboarding_completed_at"])

    async def test_complete_onboarding_sets_the_completion_timestamp(self):
        repository = _FakeNutritionistProfileRepository()
        service = NutritionistProfileService(repository)

        result = await service.complete_onboarding("owner-1")

        self.assertIsNotNone(result["onboarding_completed_at"])


if __name__ == "__main__":
    unittest.main()
