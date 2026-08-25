from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkoutExerciseIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=300)
    video_url: Optional[str] = None


class WorkoutDayIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    exercises: List[WorkoutExerciseIn] = Field(default_factory=list)


class WorkoutPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    goal: Optional[str] = None
    days: List[WorkoutDayIn]


class WorkoutPlanUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    days: Optional[List[WorkoutDayIn]] = None


class WorkoutPlanOut(BaseModel):
    id: str
    name: str
    goal: Optional[str] = None
    days: List[WorkoutDayIn]
    created_at: datetime
    updated_at: datetime
