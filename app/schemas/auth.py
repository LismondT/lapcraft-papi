from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator
from uuid import UUID


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    is_superuser: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    name: str
    exp: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str
