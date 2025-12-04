"""
Crop-related models: Crop, CropVariety, GrowthStage.
"""
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Crop(Base):
    """
    Crop model representing different crop types (maize, wheat, etc.).
    """
    __tablename__ = "crops"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_code = Column(String(20), unique=True, nullable=False, index=True)
    crop_name = Column(String(100), nullable=False)
    scientific_name = Column(String(100))
    crop_family = Column(String(50))
    
    typical_growing_season = Column(JSON)
    physiological_characteristics = Column(JSON)
    standard_units = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True, index=True)
    methodology_source = Column(String(100))
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class CropVariety(Base):
    """
    Crop variety model (e.g., SC403, SC719 for maize).
    """
    __tablename__ = "crop_varieties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey('crops.id', ondelete='CASCADE'), nullable=False, index=True)
    
    variety_code = Column(String(30), nullable=False)
    variety_name = Column(String(100), nullable=False)
    variety_type = Column(String(50))
    maturity_days = Column(Integer)
    maturity_category = Column(String(20))
    
    growth_stage_range = Column(JSON, nullable=False)
    characteristics = Column(JSON)
    growing_regions = Column(JSON)
    yield_potential_range = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_varieties_crop', 'crop_id'),
    )


class GrowthStage(Base):
    """
    Growth stage model (e.g., EMERGENCE, V3, V6, VT, R1 for maize).
    """
    __tablename__ = "growth_stages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id = Column(UUID(as_uuid=True), ForeignKey('crops.id', ondelete='CASCADE'), nullable=False, index=True)
    
    stage_code = Column(String(30), nullable=False)
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    base_days_from_planting = Column(Integer, nullable=False)
    
    stage_characteristics = Column(JSON, nullable=False)
    assessment_implications = Column(JSON)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_growth_stages_crop', 'crop_id'),
        Index('idx_growth_stages_order', 'crop_id', 'stage_order'),
    )
