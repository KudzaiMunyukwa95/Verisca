from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_password_hash
from app.api.v1.auth import get_current_user
from app.models.tenant import User, Role
from app.schemas import user as schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve users.
    Only allows viewing users within the same tenant.
    """
    query = select(User).where(User.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    users = db.execute(query).scalars().all()
    return users

@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new user.
    """
    # Check permissions (basic check for now - can be enhanced with roles)
    # Ideally should check if current_user.role has 'user_management' permission
    
    # Check if user with this email already exists
    existing_user = db.execute(select(User).where(User.email == user_in.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this user name already exists in the system.",
        )
        
    # Ensure tenant_id is set (usually to current user's tenant)
    if not user_in.tenant_id:
        user_in.tenant_id = current_user.tenant_id
        
    # Verify tenant consistency
    if user_in.tenant_id != current_user.tenant_id:
         # In a real multi-tenant system, super-admins might be able to create users for other tenants
         # For now, restrict to own tenant
         raise HTTPException(status_code=400, detail="Cannot create user for another tenant")

    # Create user
    db_obj = User(
        email=user_in.email,
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        employee_id=user_in.employee_id,
        assessor_license=user_in.assessor_license,
        is_active=user_in.is_active,
        tenant_id=user_in.tenant_id,
        role_id=user_in.role_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: UUID,
    user_in: schemas.UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
        
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["password_hash"] = hashed_password
        
    for field, value in update_data.items():
        setattr(user, field, value)
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
        
    # Soft delete ideally, but hard delete for MVP for now or check 'is_active' logic
    # Here we'll do a hard delete as per standard CRUD, but usually setting is_active=False is safer
    db.delete(user)
    db.commit()
    return user
