from typing import Optional

from pydantic import BaseModel, Field


class ExerciseLibraryItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    default_sets: Optional[int] = None
    default_reps: Optional[int] = None
    default_weight_kg: Optional[float] = None
    default_duration_seconds: Optional[int] = None
    default_rest_seconds: Optional[int] = None
    video_url: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=300)


class ExerciseLibraryItemOut(BaseModel):
    id: str
    name: str
    default_sets: Optional[int] = None
    default_reps: Optional[int] = None
    default_weight_kg: Optional[float] = None
    default_duration_seconds: Optional[int] = None
    default_rest_seconds: Optional[int] = None
    video_url: Optional[str] = None
    notes: Optional[str] = None
