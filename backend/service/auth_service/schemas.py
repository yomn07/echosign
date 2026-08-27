from pydantic import BaseModel, EmailStr
from typing import Optional

class MessageResponse(BaseModel):
    message: str
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: Optional[str] = None


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: Optional[str] = None
    is_verified: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class Usersignin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str