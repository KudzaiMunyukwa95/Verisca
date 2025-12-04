"""
Claim model for insurance claim management.
"""
from sqlalchemy import Column, String, Numeric, Date, TIMESTAMP, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Claim(Base):
    """
    Claim model representing insurance claims for crop loss.
    """
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    claim_number = Column(String(50), unique=True, nullable=False, index=True)
    policy_number = Column(String(100), nullable=False, index=True)
    insured_name = Column(String(100), nullable=False)
    
    farm_id = Column(UUID(as_uuid=True), ForeignKey('farms.id'), nullable=False)
    field_id = Column(UUID(as_uuid=True), ForeignKey('fields.id'), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey('crops.id'), nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey('crop_varieties.id'))
    
    planting_date = Column(Date, nullable=False)
    expected_harvest_date = Column(Date)
    expected_yield = Column(Numeric(8, 2), nullable=False)  # tonnes/hectare
    insured_area = Column(Numeric(8, 2), nullable=False)  # hectares
    sum_insured = Column(Numeric(12, 2))
    
    # Loss Information
    loss_notification_date = Column(Date, nullable=False)
    suspected_peril_id = Column(UUID(as_uuid=True), ForeignKey('perils.id'))
    peril_severity_level = Column(String(20))
    loss_description = Column(String)
    estimated_loss_percentage = Column(Numeric(5, 2))
    
    # Claim Status
    claim_status = Column(String(30), default='reported', index=True)  # 'reported', 'assigned', 'in_progress', 'completed', 'settled'
    priority = Column(String(20), default='normal')
    assigned_assessor_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), index=True)
    
    # Key Dates
    assignment_date = Column(TIMESTAMP(timezone=True))
    target_completion_date = Column(Date)
    actual_completion_date = Column(TIMESTAMP(timezone=True))
    
    # Final Results
    final_loss_percentage = Column(Numeric(5, 2))
    final_yield_estimate = Column(Numeric(8, 2))
    settlement_amount = Column(Numeric(12, 2))
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    __table_args__ = (
        Index('idx_claims_farm_field', 'farm_id', 'field_id'),
    )
