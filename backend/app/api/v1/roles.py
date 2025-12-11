from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.models.tenant import User, Role
from pydantic import BaseModel
from typing import Optional, List as PList

# Simple Pydantic schema for creating roles (since I couldn't find a dedicated schema file)
class RoleCreate(BaseModel):
    role_name: str
    role_description: Optional[str] = None
    permissions: Optional[PList[str]] = []
    is_system_role: Optional[bool] = False

class RoleResponse(BaseModel):
    id: Any # UUID
    role_name: str
    role_description: Optional[str]
    is_system_role: bool
    
    class Config:
        from_attributes = True

router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
def read_roles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve all roles.
    """
    # Simple query to get all roles
    query = select(Role).offset(skip).limit(limit)
    roles = db.execute(query).scalars().all()
    return roles

@router.post("/", response_model=RoleResponse)
def create_role(
    *,
    db: Session = Depends(get_db),
    role_in: RoleCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new role.
    """
    # Check checks
    existing_role = db.execute(select(Role).where(Role.role_name == role_in.role_name)).scalar_one_or_none()
    if existing_role:
        # Idempotency: Return existing role instead of error, or update it
        return existing_role

    db_obj = Role(
        role_name=role_in.role_name,
        role_description=role_in.role_description,
        permissions=role_in.permissions,
        is_system_role=role_in.is_system_role
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
