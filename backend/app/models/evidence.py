from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

from geoalchemy2 import Geometry

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Context (optional links)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id"))
    
    # Location (Geotagging)
    location = Column(Geometry('POINT', 4326))
    gps_accuracy_meters = Column(Float)
    
    # File Metadata
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False) # UUID based
    file_path = Column(String(500), nullable=False) # Relative or absolute path
    content_type = Column(String(100))
    file_size_bytes = Column(Integer)
    
    url = Column(String(500)) # Public or Access URL
    
    description = Column(String(500))
    tags = Column(JSONB) # ["photo", "hail_damage"]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
