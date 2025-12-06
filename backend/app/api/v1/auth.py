"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.core.security import verify_password, create_access_token, decode_access_token, get_password_hash
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse, TenantResponse
from app.models.tenant import User, Tenant


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")


# TEMPORARY: Hash generator endpoint for debugging
@router.get("/generate-hash/{password}")
async def generate_hash(password: str):
    """Temporary endpoint to generate password hash. Remove in production."""
    hashed = get_password_hash(password)
    return {
        "password": password,
        "hash": hashed,
        "sql": f"UPDATE users SET password_hash = '{hashed}' WHERE username = 'admin';"
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    Compatible with standard OAuth2 flows (e.g. Swagger UI, Postman).
    """
    # 1. Find User (allow login by username OR email)
    # Note: Logic assumes username/email is unique across system or we just pick first match.
    # Given User model has unique=True for both username and email, this is safe.
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()

    if not user:
        # Avoid enumeration attacks technically, but for MVP debug log is fine
        print(f"[AUTH] User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Verify Password
    if not verify_password(form_data.password, user.password_hash):
        print(f"[AUTH] Password mismatch for user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Check if User/Tenant is Active
    if not user.is_active:
         raise HTTPException(status_code=400, detail="User account is inactive")
         
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
         raise HTTPException(status_code=400, detail="Tenant is inactive")
         
    # 4. Generate Token
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 4. Generate Token
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "user_id": str(user.id), # Required by get_current_user
            "tenant_id": str(tenant.id),
            "role_id": str(user.role_id)
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "tenant": tenant
    }


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
    return UserResponse.model_validate(current_user)
