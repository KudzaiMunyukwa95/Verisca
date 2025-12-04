"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.core.security import verify_password, create_access_token, decode_access_token
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse, TenantResponse
from app.models.tenant import User, Tenant


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Args:
        login_data: Login credentials (username, password, tenant_code)
        db: Database session
        
    Returns:
        LoginResponse with access token, user info, and tenant info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find tenant by code
    tenant = db.query(Tenant).filter(
        Tenant.tenant_code == login_data.tenant_code,
        Tenant.is_active == True
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant code",
        )
    
    # Find user by username and tenant
    user = db.query(User).filter(
        User.username == login_data.username,
        User.tenant_id == tenant.id,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # Update last login time
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "username": user.username,
        }
    )
    
    # Prepare response
    return LoginResponse(
        access_token=access_token,
        user=UserResponse.from_orm(user),
        tenant=TenantResponse.from_orm(tenant)
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Current authenticated User
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        UserResponse with current user details
    """
    return UserResponse.from_orm(current_user)
