from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum

# --- Enums ---

class ClaimStatusEnum(str, Enum):
    REPORTED = "reported"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"

class AssessmentStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SYNCED = "synced"

# --- Claims ---

class ClaimBase(BaseModel):
    farm_id: Optional[UUID] = None
    field_id: Optional[UUID] = None
    # Flexible input for "Quick Create"
    farm_name: Optional[str] = None
    field_name: Optional[str] = None
    assessor_email: Optional[str] = None # Added for assignment
    
    peril_type: str
    date_of_loss: datetime
    loss_description: Optional[str] = None

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatusEnum] = None
    assigned_assessor_id: Optional[UUID] = None
    loss_description: Optional[str] = None

class ClaimResponse(ClaimBase):
    id: UUID
    claim_number: str
    tenant_id: UUID
    status: ClaimStatusEnum
    assigned_assessor_id: Optional[UUID]
    
    # Flattened UI Fields
    farm_name: Optional[str] = None
    field_name: Optional[str] = None
    assessor_name: Optional[str] = None
    
    created_at: datetime
    updated_at: Optional[datetime]
    created_by_user_id: Optional[UUID]
    
    class Config:
        from_attributes = True

# --- Assessment Samples ---

class AssessmentSampleBase(BaseModel):
    sample_number: int
    gps_accuracy_meters: Optional[float] = None
    measurements: Dict[str, Any]
    evidence_refs: Optional[List[str]] = None
    notes: Optional[str] = None

class AssessmentSampleCreate(AssessmentSampleBase):
    lat: float
    lng: float
    timestamp: Optional[datetime] = None

class AssessmentSampleResponse(AssessmentSampleBase):
    id: UUID
    session_id: UUID
    sample_location: Optional[str] = None # WKT
    timestamp: datetime
    
    class Config:
        from_attributes = True

# --- Assessment Sessions ---

class AssessmentSessionBase(BaseModel):
    assessment_method: str
    growth_stage: Optional[str] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    crop_conditions: Optional[Dict[str, Any]] = None
    assessor_notes: Optional[str] = None

class AssessmentSessionCreate(AssessmentSessionBase):
    claim_id: UUID
    # Assessor ID inferred from current user

class AssessmentSessionUpdate(BaseModel):
    status: Optional[AssessmentStatusEnum] = None
    date_completed: Optional[datetime] = None
    growth_stage: Optional[str] = None
    calculated_result: Optional[Dict[str, Any]] = None
    assessor_notes: Optional[str] = None

class AssessmentSessionResponse(AssessmentSessionBase):
    id: UUID
    claim_id: UUID
    assessor_id: UUID
    date_started: datetime
    date_completed: Optional[datetime]
    status: AssessmentStatusEnum
    calculated_result: Optional[Dict[str, Any]] = None
    samples: List[AssessmentSampleResponse] = []
    
    class Config:
        from_attributes = True
