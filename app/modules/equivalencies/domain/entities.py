from dataclasses import dataclass


@dataclass(frozen=True)
class EquivalencyGroup:
    id: str
    name: str
    kcal: float
    carbs_g: float
    protein_g: float
    fat_g: float


@dataclass(frozen=True)
class EquivalencyFood:
    id: str
    group_id: str
    name: str
    portion_description: str
    owner_id: str | None = None
