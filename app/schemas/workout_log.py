from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class WorkoutSetLogIn(BaseModel):
    set_index: int = Field(..., ge=0)
    completed: bool = True
    reps_completed: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = None
    rpe: Optional[int] = Field(None, ge=1, le=10)


class WorkoutExerciseLogIn(BaseModel):
    workout_plan_id: str
    day_index: int = Field(..., ge=0)
    exercise_index: int = Field(..., ge=0)
    sets: List[WorkoutSetLogIn] = Field(default_factory=list)
    comment: Optional[str] = Field(None, max_length=500)
    photo_url: Optional[str] = None
    photo_content_type: Optional[str] = None
