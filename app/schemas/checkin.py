from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class FormFieldIn(BaseModel):
    id: str
    type: str
    label: str
    required: bool = False
    options: List[str] = Field(default_factory=list)
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None


class FormFieldOut(FormFieldIn):
    pass


class FormTemplateCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    fields: List[FormFieldIn]


class FormTemplateOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    fields: List[FormFieldOut]
    archived: bool
    created_at: datetime
    updated_at: datetime


class FormAnswerIn(BaseModel):
    field_id: str
    values: List[str] = Field(default_factory=list)


class FormResponseCreate(BaseModel):
    template_id: str
    appointment_id: Optional[str] = None
    answers: List[FormAnswerIn]


class FormAnswerOut(BaseModel):
    field_id: str
    values: List[str]


class FormResponseOut(BaseModel):
    id: str
    template_id: str
    appointment_id: Optional[str] = None
    answers: List[FormAnswerOut]
    submitted_at: datetime
