from datetime import datetime

from pydantic import BaseModel


class BodyCompositionMetrics(BaseModel):
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    skeletal_muscle_kg: float | None = None
    body_fat_mass_kg: float | None = None
    total_body_water_l: float | None = None
    protein_kg: float | None = None
    minerals_kg: float | None = None
    bmi: float | None = None
    visceral_fat_level: float | None = None
    bmr_kcal: float | None = None
    waist_hip_ratio: float | None = None
    obesity_degree_pct: float | None = None
    inbody_score: float | None = None
    ideal_weight_kg: float | None = None
    weight_control_kg: float | None = None
    fat_control_kg: float | None = None
    muscle_control_kg: float | None = None
    grip_strength_left_kg: float | None = None
    grip_strength_right_kg: float | None = None


class BodyCompositionOut(BaseModel):
    id: str
    at: datetime
    provider: str | None = None
    metrics: BodyCompositionMetrics
    attachment_url: str | None = None
    attachment_type: str | None = None
