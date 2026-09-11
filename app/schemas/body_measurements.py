from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Fixed circumference-site vocabulary (spec 084). The paired limbs (arm/thigh/
# calf) also accept `<site>_left` / `<site>_right` keys (spec 087) — the bare
# key stays valid and means "single value / side unspecified".
_BASE_SITES = ("neck", "chest", "arm", "waist", "hip", "thigh", "calf")
_PAIRED_SITES = ("arm", "thigh", "calf")
CIRCUMFERENCE_SITES: frozenset[str] = frozenset(
    _BASE_SITES
    + tuple(f"{s}_{side}" for s in _PAIRED_SITES for side in ("left", "right"))
)


class BodyMeasurementsIn(BaseModel):
    """A circumference reading set — from the interactive body figure. Written
    to the same `measurements` collection as weight/photo entries, minus the
    photo."""

    circumferences: dict[str, float] = Field(default_factory=dict)
    at: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)
    # Nutritionist-side entry may also carry the tape-measured scalars.
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    body_fat_pct: float | None = Field(default=None, ge=0, le=80)
    waist_cm: float | None = Field(default=None, ge=0, le=300)

    @field_validator("circumferences")
    @classmethod
    def _clean(cls, value: dict[str, float]) -> dict[str, float]:
        cleaned: dict[str, float] = {}
        for site, cm in (value or {}).items():
            if site not in CIRCUMFERENCE_SITES:
                raise ValueError(f"unknown circumference site: {site}")
            if cm is None:
                continue
            if not (0 < float(cm) <= 300):
                raise ValueError(f"{site} must be between 0 and 300 cm")
            cleaned[site] = round(float(cm), 1)
        return cleaned
