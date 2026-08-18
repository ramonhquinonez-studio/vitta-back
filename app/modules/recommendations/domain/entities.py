from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recommendation:
    id: str
    owner_id: str
    kind: str  # "supplement" | "brand"
    title: str
    subtitle: str | None = None
    category: str | None = None
    brand: str | None = None
    description: str | None = None
    benefits: list[str] = field(default_factory=list)
    usage: str | None = None
    notes: str | None = None
    price: str | None = None
    rating: float | None = None
    emoji: str | None = None
