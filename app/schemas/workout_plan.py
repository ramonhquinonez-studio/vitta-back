from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class WorkoutSetIn(BaseModel):
    reps_min: Optional[int] = Field(None, ge=0)
    reps_max: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    rest_seconds: Optional[int] = Field(None, ge=0)


class WorkoutMediaIn(BaseModel):
    url: str
    media_type: str = Field(pattern="^(photo|video)$")


class WorkoutExerciseIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    sets: List[WorkoutSetIn] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=300)
    media: List[WorkoutMediaIn] = Field(default_factory=list)


class WorkoutDayIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    exercises: List[WorkoutExerciseIn] = Field(default_factory=list)
    weekdays: List[int] = Field(default_factory=list)

    @field_validator("weekdays")
    @classmethod
    def _validate_weekdays(cls, value: List[int]) -> List[int]:
        for weekday in value:
            if weekday < 1 or weekday > 7:
                raise ValueError("weekdays must be ISO weekday integers (1=Mon..7=Sun)")
        return value


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
