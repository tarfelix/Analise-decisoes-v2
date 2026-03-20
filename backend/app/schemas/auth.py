"""Auth request/response schemas."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    email: str
    nome: str
    role: str
    first_access: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    nome: str
    password: str
    role: str = "advogado"
