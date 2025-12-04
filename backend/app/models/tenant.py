"""
Tenant model - Multi-tenant organization management.
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Tenant(Base):
    """
    Tenant model representing insurance companies or assessor organizations.
    All data is isolated by tenant_id for multi-tenancy.
    """
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_code = Column(String(20), unique=True, nullable=False, index=True)
    tenant_name = Column(String(100), nullable=False)
    tenant_type = Column(String(20), nullable=False)  # 'insurer', 'assessor_company', 'system_admin'
    
    contact_email = Column(String(100), nullable=False)
    contact_phone = Column(String(20))
    address = Column(JSON)
    billing_info = Column(JSON)
    tenant_config = Column(JSON, default={})
    
    subscription_tier = Column(String(20), default='standard')
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    __table_args__ = (
        Index('idx_tenants_active', 'is_active'),
    )


class Role(Base):
    """
    Role model for user permissions.
    """
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), unique=True, nullable=False)
    role_description = Column(String)
    permissions = Column(JSON, nullable=False, default=[])
    is_system_role = Column(Boolean, default=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class User(Base):
    """
    User model with multi-tenant isolation.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), nullable=False)
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20))
    employee_id = Column(String(50))
    assessor_license = Column(String(50))
    specializations = Column(JSON, default=[])
    profile_image_url = Column(String(500))
    
    last_login_at = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    __table_args__ = (
        Index('idx_users_tenant', 'tenant_id'),
        Index('idx_users_active', 'is_active', 'tenant_id'),
    )
