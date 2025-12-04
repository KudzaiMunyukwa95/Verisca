"""
Farm and Field models with PostGIS spatial support.
"""
from sqlalchemy import Column, String, Numeric, Boolean, TIMESTAMP, JSON, Index, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from app.db.base import Base


class Farm(Base):
    """
    Farm model with spatial location support.
    """
    __tablename__ = "farms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    farm_code = Column(String(50), nullable=False)
    farm_name = Column(String(100), nullable=False)
    farmer_name = Column(String(100))
    farmer_contact = Column(JSON)
    
    # PostGIS geometry column for farm center point
    farm_location = Column(Geometry('POINT', srid=4326))
    farm_address = Column(JSON)
    
    total_farm_area = Column(Numeric(10, 2))
    operational_area = Column(Numeric(10, 2))
    farm_characteristics = Column(JSON)
    registration_numbers = Column(JSON)
    insurance_history = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    __table_args__ = (
        Index('idx_farms_tenant', 'tenant_id'),
    )


class Field(Base):
    """
    Field model with PostGIS polygon boundary.
    """
    __tablename__ = "fields"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    
    field_code = Column(String(50), nullable=False)
    field_name = Column(String(100))
    
    # PostGIS geometry columns
    field_boundary = Column(Geometry('POLYGON', srid=4326), nullable=False)
    field_center = Column(Geometry('POINT', srid=4326))
    field_area = Column(Numeric(8, 2), nullable=False)  # hectares
    
    soil_characteristics = Column(JSON)
    irrigation_type = Column(String(30))
    elevation_meters = Column(Integer)
    slope_characteristics = Column(JSON)
    access_notes = Column(String)
    historical_yields = Column(JSON)
    land_use_restrictions = Column(JSON)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_fields_farm', 'farm_id'),
    )
