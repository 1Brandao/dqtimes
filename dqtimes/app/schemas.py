from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema para criação de usuário"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """Schema para login de usuário"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema para resposta de token JWT"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema para dados extraídos do token"""
    email: Optional[str] = None


class UserResponse(BaseModel):
    """Schema para resposta de usuário (sem senha)"""
    id: int
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
