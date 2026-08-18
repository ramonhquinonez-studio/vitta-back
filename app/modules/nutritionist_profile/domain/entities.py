from dataclasses import dataclass, field


@dataclass(frozen=True)
class SocialLink:
    platform: str
    handle: str


@dataclass(frozen=True)
class NutritionistProfile:
    owner_id: str
    role_label: str | None = None
    bio: str | None = None
    years_experience: int | None = None
    session_price: float | None = None
    session_price_currency: str = "MXN"
    social_links: list[SocialLink] = field(default_factory=list)
