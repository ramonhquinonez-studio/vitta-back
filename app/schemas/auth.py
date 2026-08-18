from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6)
    invite_code: str = Field(..., min_length=4, max_length=40)

class RegisterNutritionistIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access: str
    refresh: str

class RefreshIn(BaseModel):
    refresh_token: str

class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class InviteCodeOut(BaseModel):
    code: str
    expires_at: datetime

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ForgotPasswordOut(BaseModel):
    ok: bool = True
    message: str
    # Solo se rellena fuera de producción: no hay integración de envío de
    # correo todavía, así que en local/dev el token se devuelve aquí para
    # poder probar el flujo completo sin bandeja de entrada real.
    reset_token: str | None = None

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)