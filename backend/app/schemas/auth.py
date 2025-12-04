"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str
    tenant_code: str


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[uuid.UUID] = None
    tenant_id: Optional[uuid.UUID] = None
    username: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    assessor_license: Optional[str] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TenantResponse(BaseModel):
    """Tenant response schema."""
    id: uuid.UUID
    tenant_code: str
    tenant_name: str
    tenant_type: str
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Complete login response with token and user info."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    tenant: TenantResponse
