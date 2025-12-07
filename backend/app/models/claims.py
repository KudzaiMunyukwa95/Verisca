from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, UniqueConstraint, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
import enum

from app.db.base import Base

class ClaimStatus(str, enum.Enum):
    REPORTED = "reported"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"

class AssessmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SYNCED = "synced"

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number = Column(String(50), unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Location
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    
    # Loss Details
    peril_type = Column(String(50), nullable=False)  # drought, hail, etc.
    date_of_loss = Column(DateTime(timezone=True), nullable=False)
    loss_description = Column(Text)
    
    # Workflow
    status = Column(String(20), default=ClaimStatus.REPORTED, index=True)
    assigned_assessor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    # tenant = relationship("Tenant", back_populates="claims") # Linked via back_populates in tenant
    # farm = relationship("Farm", back_populates="claims")
    # field = relationship("Field", back_populates="claims")
    assessment_sessions = relationship("AssessmentSession", back_populates="claim", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_claims_tenant_status', 'tenant_id', 'status'),
    )

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    assessor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session Details
    date_started = Column(DateTime(timezone=True), default=func.now())
    date_completed = Column(DateTime(timezone=True))
    status = Column(String(20), default=AssessmentStatus.IN_PROGRESS, index=True)
    
    # Methodology
    assessment_method = Column(String(50), nullable=False) # stand_reduction, hail_count, etc.
    growth_stage = Column(String(50)) # V1, V2... VT, R1...
    
    # Conditions
    weather_conditions = Column(JSON) # {temp, wind, cloud_cover}
    crop_conditions = Column(JSON) # {soil_moisture, weed_pressure, disease_pressure}
    
    # Results High Level
    calculated_result = Column(JSON) # {final_yield_est, loss_percentage}
    assessor_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="assessment_sessions")
    samples = relationship("AssessmentSample", back_populates="session", cascade="all, delete-orphan")

class AssessmentSample(Base):
    """
    Individual data points collected during an assessment session.
    Corresponds to a physical stop in the field at a GPS point.
    """
    __tablename__ = "assessment_samples"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False)
    
    sample_number = Column(Integer, nullable=False)
    
    # Location verification
    sample_location = Column(Geometry('POINT', 4326))
    gps_accuracy_meters = Column(Float)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    
    # Measurements (Variable based on method)
    # Example Stand Reduction: { "row_width": 0.76, "length_measured": 5.0, "plant_count": 28, "gap_count": 2 }
    measurements = Column(JSON, nullable=False)
    
    # Photos/Evidence at this specific point
    evidence_refs = Column(JSON) # ["photo_id_1", "photo_id_2"]
    
    notes = Column(Text)
    
    session = relationship("AssessmentSession", back_populates="samples")
    
    __table_args__ = (
        UniqueConstraint('session_id', 'sample_number', name='unique_session_sample_num'),
    )
