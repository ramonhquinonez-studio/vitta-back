from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Message:
    id: str
    owner_id: str
    patient_id: str
    sender_role: str  # "patient" | "nutritionist"
    text: str
    created_at: datetime
    read_at: datetime | None = None
