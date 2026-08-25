from datetime import datetime

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: str
    sender_role: str
    text: str
    created_at: datetime
    read_at: datetime | None


class MessageIn(BaseModel):
    text: str
