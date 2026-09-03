from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recommendation:
    id: str
    owner_id: str | None
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
    # Only meaningful for kind="brand": ties this recommendation to one of
    # the fixed SMAE equivalency-group ids (`equivalencies` module), so a
    # patient's plan can surface "best brand for this menu item" against
    # whichever brand recommendation their nutritionist assigned for the
    # same group.
    equivalency_group_id: str | None = None
