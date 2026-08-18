from typing import Any

from ..domain.entities import NutritionistProfile
from ..domain.repositories import NutritionistProfileRepository


def _serialize(profile: NutritionistProfile, patient_count: int) -> dict[str, Any]:
    return {
        "role_label": profile.role_label,
        "bio": profile.bio,
        "years_experience": profile.years_experience,
        "session_price": profile.session_price,
        "session_price_currency": profile.session_price_currency,
        "social_links": [
            {"platform": link.platform, "handle": link.handle}
            for link in profile.social_links
        ],
        "cedula": profile.cedula,
        "practice_name": profile.practice_name,
        "logo_url": profile.logo_url,
        "brand_color": profile.brand_color,
        "city": profile.city,
        "specializations": profile.specializations,
        "energy_equation": profile.energy_equation,
        "portions_mode": profile.portions_mode,
        "macro_split": (
            {
                "protein_pct": profile.macro_split.protein_pct,
                "carbs_pct": profile.macro_split.carbs_pct,
                "fat_pct": profile.macro_split.fat_pct,
            }
            if profile.macro_split
            else None
        ),
        "units": profile.units,
        "meals_per_day": profile.meals_per_day,
        "onboarding_completed_at": profile.onboarding_completed_at,
        "patient_count": patient_count,
    }


class NutritionistProfileService:
    def __init__(self, repository: NutritionistProfileRepository):
        self._repository = repository

    async def get_my_profile(self, owner_id: str) -> dict[str, Any]:
        profile = await self._repository.get_for_owner(owner_id)
        if profile is None:
            profile = NutritionistProfile(owner_id=owner_id)
        patient_count = await self._repository.count_patients_for_owner(owner_id)
        return _serialize(profile, patient_count)

    async def update_my_profile(self, owner_id: str, payload: dict) -> dict[str, Any]:
        if not payload:
            raise ValueError("No fields to update")
        profile = await self._repository.upsert_for_owner(owner_id, payload)
        patient_count = await self._repository.count_patients_for_owner(owner_id)
        return _serialize(profile, patient_count)

    async def complete_onboarding(self, owner_id: str) -> dict[str, Any]:
        profile = await self._repository.mark_onboarding_completed(owner_id)
        patient_count = await self._repository.count_patients_for_owner(owner_id)
        return _serialize(profile, patient_count)

    async def get_profile_for_owner(self, owner_id: str) -> dict[str, Any] | None:
        profile = await self._repository.get_for_owner(owner_id)
        if profile is None:
            return None
        patient_count = await self._repository.count_patients_for_owner(owner_id)
        return _serialize(profile, patient_count)
