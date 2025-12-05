from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from app.db.base import Base

class Farm(Base):
    __tablename__ = "farms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Core farm data
    farm_code = Column(String(50), nullable=False)
    farm_name = Column(String(100), nullable=False)
    farmer_name = Column(String(100))
    farmer_contact = Column(JSONB)  # {"phone": "+263...", "email": "..."}
    
    # Spatial data
    farm_location = Column(Geometry('POINT', 4326))  # Farm center point
    farm_address = Column(JSONB)
    total_farm_area = Column(DECIMAL(10,2))  # Hectares
    operational_area = Column(DECIMAL(10,2))  # Cultivated area
    
    # Farm characteristics
    farm_characteristics = Column(JSONB)  # Soil, climate, infrastructure
    registration_numbers = Column(JSONB)  # Government registrations
    insurance_history = Column(JSONB)  # Previous claims, policies
    
    # Audit fields
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="farms")
    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")
    # claims = relationship("Claim", back_populates="farm")  # Add this later when Claim model exists
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'farm_code', name='unique_tenant_farm_code'),
        Index('idx_farms_location', 'farm_location', postgresql_using='gist'),
    )

class Field(Base):
    __tablename__ = "fields"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    
    # Field identification
    field_code = Column(String(50), nullable=False)
    field_name = Column(String(100))
    
    # Spatial data (CRITICAL: These are auto-calculated)
    field_boundary = Column(Geometry('POLYGON', 4326), nullable=False)  # GPS boundary
    field_area = Column(DECIMAL(8,2), nullable=False)  # Auto-calculated from boundary
    field_center = Column(Geometry('POINT', 4326))  # Auto-calculated centroid
    
    # Field characteristics
    soil_characteristics = Column(JSONB)  # Type, pH, fertility, drainage
    irrigation_type = Column(String(30))  # rainfed, sprinkler, drip, flood
    elevation_meters = Column(Integer)
    slope_characteristics = Column(JSONB)  # Grade, aspect, drainage
    
    # Operational data
    access_notes = Column(Text)  # How to reach the field
    historical_yields = Column(JSONB)  # Previous season data
    land_use_restrictions = Column(JSONB)  # Easements, restrictions
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    farm = relationship("Farm", back_populates="fields")
    # claims = relationship("Claim", back_populates="field") # Add later
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('farm_id', 'field_code', name='unique_farm_field_code'),
        Index('idx_fields_boundary', 'field_boundary', postgresql_using='gist'),
        Index('idx_fields_center', 'field_center', postgresql_using='gist'),
    )
