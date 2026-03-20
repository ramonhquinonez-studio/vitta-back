from dataclasses import dataclass, field


@dataclass(frozen=True)
class Patient:
    id: str
    owner_id: str
    name: str
    age: int | None = None
    sex: str | None = None
    height_cm: float | None = None
    allergies: list[str] = field(default_factory=list)
    notes: str | None = None
