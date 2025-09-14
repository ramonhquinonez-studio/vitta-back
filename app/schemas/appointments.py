from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

Mode = Literal["online", "onsite"]
Status = Literal["confirmed", "pending", "canceled"]
PaymentStatus = Literal["unpaid", "paid", "refunded", "pending"]

class AppointmentIn(BaseModel):
    patient_id: str
    start: datetime
    end: datetime
    mode: Mode
    status: Status = "confirmed"
    payment_status: PaymentStatus = "unpaid"
    video_room_url: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)

class AppointmentUpdate(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    mode: Optional[Mode] = None
    status: Optional[Status] = None
    payment_status: Optional[PaymentStatus] = None
    video_room_url: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)

class AppointmentOut(BaseModel):
    id: str
    patient_id: str
    start: datetime
    end: datetime
    mode: Mode
    status: Status
    payment_status: PaymentStatus
    video_room_url: Optional[str] = None
    notes: Optional[str] = None
    owner_id: str
