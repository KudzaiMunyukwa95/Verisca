from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime

# --- Shared Components ---

class GeoPoint(BaseModel):
    lat: float
    lng: float

    @validator('lat')
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('lng')
    def validate_lng(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

# --- Farm Schemas ---

class FarmBase(BaseModel):
    farm_code: str
    farm_name: str
    farmer_name: Optional[str] = None
    farmer_contact: Optional[Dict[str, Any]] = None
    farm_address: Optional[Dict[str, Any]] = None
    farm_characteristics: Optional[Dict[str, Any]] = None
    registration_numbers: Optional[Dict[str, Any]] = None
    insurance_history: Optional[Dict[str, Any]] = None

class FarmCreate(FarmBase):
    farm_location: Optional[GeoPoint] = None
    total_farm_area: Optional[float] = None
    operational_area: Optional[float] = None

class FarmUpdate(BaseModel):
    farm_name: Optional[str] = None
    farmer_name: Optional[str] = None
    farmer_contact: Optional[Dict[str, Any]] = None
    farm_location: Optional[GeoPoint] = None
    is_active: Optional[bool] = None

class FarmResponse(FarmBase):
    id: UUID
    tenant_id: UUID
    farm_location: Optional[str] = None # WKT format or similar
    total_farm_area: Optional[float]
    operational_area: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: UUID
    
    class Config:
        from_attributes = True

# --- Field Schemas ---

class FieldBase(BaseModel):
    field_code: str
    field_name: Optional[str] = None
    soil_characteristics: Optional[Dict[str, Any]] = None
    irrigation_type: Optional[str] = None
    elevation_meters: Optional[int] = None
    slope_characteristics: Optional[Dict[str, Any]] = None
    access_notes: Optional[str] = None
    historical_yields: Optional[Dict[str, Any]] = None
    land_use_restrictions: Optional[Dict[str, Any]] = None

class FieldCreate(FieldBase):
    boundary_coordinates: List[List[float]] # List of [lng, lat] pairs
    
    @validator('boundary_coordinates')
    def validate_coordinates(cls, v):
        if len(v) < 3:
            raise ValueError('Field boundary must have at least 3 points')
        return v

class FieldUpdate(BaseModel):
    field_name: Optional[str] = None
    irrigation_type: Optional[str] = None
    access_notes: Optional[str] = None

class FieldResponse(FieldBase):
    id: UUID
    farm_id: UUID
    field_boundary: str # WKT
    field_area: float # Hectares
    field_center: Optional[str] # WKT or string rep
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# --- Sampling Schemas ---

class SamplingRequest(BaseModel):
    minimum_samples: int = Field(5, ge=3, le=50)
    sampling_method: str = Field("random", pattern="^(random|grid|stratified)$")
    edge_buffer_meters: float = Field(5.0, ge=0.0)
    min_distance_meters: float = Field(20.0, ge=1.0)

class SamplingPoint(BaseModel):
    sample_number: int
    lat: float
    lng: float
    distance_from_edge_meters: float
    gps_accuracy_required: str
    sampling_notes: Optional[str]

class SamplingResponse(BaseModel):
    field_id: UUID
    farm_id: UUID
    field_area_hectares: float
    sampling_method: str
    total_sample_points: int
    sample_points: List[SamplingPoint]
    generation_timestamp: datetime
    gps_accuracy_requirements: Dict[str, Any]
