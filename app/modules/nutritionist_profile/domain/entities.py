from datetime import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SocialLink:
    platform: str
    handle: str


@dataclass(frozen=True)
class MacroSplit:
    protein_pct: float
    carbs_pct: float
    fat_pct: float


@dataclass(frozen=True)
class NutritionistProfile:
    owner_id: str
    role_label: str | None = None
    bio: str | None = None
    years_experience: int | None = None
    session_price: float | None = None
    session_price_currency: str = "MXN"
    social_links: list[SocialLink] = field(default_factory=list)
    # Professional profile (onboarding step 2)
    cedula: str | None = None
    practice_name: str | None = None
    logo_url: str | None = None
    brand_color: str | None = None
    city: str | None = None
    # Specialization (onboarding step 3)
    specializations: list[str] = field(default_factory=list)
    # Workflow defaults (onboarding step 4)
    energy_equation: str | None = None
    portions_mode: str | None = None
    macro_split: MacroSplit | None = None
    units: str | None = None
    meals_per_day: int | None = None
    # Onboarding tracking
    onboarding_completed_at: datetime | None = None
