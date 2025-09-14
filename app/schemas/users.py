from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str

