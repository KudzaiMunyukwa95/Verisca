# VERISCA BACKEND COMPLETE IMPLEMENTATION PROMPT 🚀
## AI-Powered Development: World-Class Agricultural Assessment Platform

---

## PROJECT CONTEXT

You are implementing the complete backend for **Verisca** - the world's most advanced agricultural insurance assessment platform. This system digitizes the complete USDA crop loss adjustment methodology for African insurance markets.

**Current Foundation:**
- ✅ Multi-tenant authentication with JWT
- ✅ User management API (CRUD)
- ✅ PostgreSQL 15 + PostGIS database
- ✅ FastAPI with async/await patterns
- ✅ Deployed on Render with production configuration

**Your Mission:** Implement all remaining backend components to create the world's leading agricultural assessment API.

---

## IMPLEMENTATION SCOPE

### Core Components to Implement:
1. **Farm/Field Spatial Management** (PostGIS operations)
2. **Claims Workflow Management** (Insurance claim lifecycle)
3. **GPS Sampling Engine** (Automated sampling point generation)
4. **USDA Calculation Engine** (Scientific crop loss calculations)
5. **Assessment Session Management** (Complete assessment workflow)
6. **Evidence & File Handling** (Photo/document management)
7. **Lookup Tables System** (USDA exhibits and charts)
8. **PDF Report Generation** (Professional assessment reports)
9. **Mobile Sync Infrastructure** (Offline-first mobile support)

### Quality Standards:
- **Scientific Accuracy**: Match USDA methodology exactly
- **Performance**: Sub-100ms API responses for calculations
- **Security**: Complete multi-tenant data isolation
- **Scalability**: Support unlimited insurers and assessors
- **Reliability**: 99.9% uptime production deployment

---

## TECHNICAL ARCHITECTURE

### Database Integration Pattern:
```python
# Follow existing patterns for all new models
class NewModel(Base):
    __tablename__ = "new_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="new_models")
```

### API Endpoint Pattern:
```python
# Maintain consistent patterns with existing user management
@router.post("/", response_model=ResponseSchema)
async def create_resource(
    resource: CreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Always validate tenant access
    if hasattr(resource, 'tenant_id') and resource.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Implementation logic
    pass
```

### Error Handling Standard:
```python
# Consistent error responses across all endpoints
from app.core.exceptions import (
    VerisSpatialError,
    VerisCalculationError,
    VerisTenantAccessError
)

@router.post("/endpoint")
async def endpoint(...):
    try:
        # Implementation
        pass
    except VerisSpatialError as e:
        raise HTTPException(status_code=400, detail=f"Spatial operation failed: {str(e)}")
    except VerisCalculationError as e:
        raise HTTPException(status_code=422, detail=f"Calculation error: {str(e)}")
```

---

## DETAILED IMPLEMENTATION REQUIREMENTS

### 1. SPATIAL FARM/FIELD MANAGEMENT 🗺️

**Models to Implement:**
```python
# app/models/spatial.py
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Area, ST_Transform, ST_Centroid, ST_Contains

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
    claims = relationship("Claim", back_populates="farm")
    
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
    claims = relationship("Claim", back_populates="field")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('farm_id', 'field_code', name='unique_farm_field_code'),
        Index('idx_fields_boundary', 'field_boundary', postgresql_using='gist'),
        Index('idx_fields_center', 'field_center', postgresql_using='gist'),
    )
```

**Spatial Service Implementation:**
```python
# app/services/spatial.py
from shapely.geometry import Point, Polygon
from shapely.wkt import loads, dumps
from shapely.ops import transform
from geoalchemy2.functions import ST_Area, ST_Transform, ST_AsText, ST_GeomFromText
import pyproj
import random
from typing import List, Dict, Tuple

class SpatialService:
    """
    World-class spatial operations for agricultural field management
    """
    
    @staticmethod
    async def calculate_field_metrics(boundary_coordinates: List[List[float]], 
                                    db: Session) -> Dict:
        """
        Calculate field area and center from GPS boundary coordinates
        
        Args:
            boundary_coordinates: List of [longitude, latitude] pairs
            db: Database session
            
        Returns:
            Dict with area_hectares, center_lat, center_lng, boundary_wkt
        """
        try:
            # Validate coordinates
            if len(boundary_coordinates) < 4:
                raise VerisSpatialError("Field boundary requires minimum 4 coordinate pairs")
            
            # Ensure polygon is closed
            if boundary_coordinates[0] != boundary_coordinates[-1]:
                boundary_coordinates.append(boundary_coordinates[0])
            
            # Create WKT polygon string
            coords_wkt = ",".join([f"{lng} {lat}" for lng, lat in boundary_coordinates])
            boundary_wkt = f"POLYGON(({coords_wkt}))"
            
            # Calculate area using PostGIS (accurate spherical calculation)
            area_query = text("""
                SELECT ST_Area(ST_Transform(ST_GeomFromText(:wkt, 4326), 3857)) / 10000.0 as area_hectares
            """)
            area_result = await db.execute(area_query, {"wkt": boundary_wkt})
            area_hectares = area_result.scalar()
            
            # Calculate centroid
            centroid_query = text("""
                SELECT ST_Y(ST_Centroid(ST_GeomFromText(:wkt, 4326))) as lat,
                       ST_X(ST_Centroid(ST_GeomFromText(:wkt, 4326))) as lng
            """)
            centroid_result = await db.execute(centroid_query, {"wkt": boundary_wkt})
            centroid_row = centroid_result.fetchone()
            
            return {
                "area_hectares": round(float(area_hectares), 4),
                "center_lat": float(centroid_row.lat),
                "center_lng": float(centroid_row.lng),
                "boundary_wkt": boundary_wkt,
                "perimeter_meters": await SpatialService._calculate_perimeter(boundary_wkt, db)
            }
            
        except Exception as e:
            raise VerisSpatialError(f"Failed to calculate field metrics: {str(e)}")
    
    @staticmethod
    async def generate_sampling_points(field_boundary_wkt: str, 
                                     min_samples: int,
                                     method: str = "random",
                                     edge_buffer_meters: float = 5.0,
                                     min_distance_meters: float = 20.0,
                                     db: Session = None) -> List[Dict]:
        """
        Generate GPS sampling points within field boundary using USDA methodology
        
        This is the core Verisca differentiator - automated, unbiased sampling
        """
        try:
            # Get field bounds from database for accurate calculations
            bounds_query = text("""
                SELECT ST_XMin(geom) as min_lng, ST_YMin(geom) as min_lat,
                       ST_XMax(geom) as max_lng, ST_YMax(geom) as max_lat
                FROM (SELECT ST_GeomFromText(:wkt, 4326) as geom) as subq
            """)
            bounds_result = await db.execute(bounds_query, {"wkt": field_boundary_wkt})
            bounds = bounds_result.fetchone()
            
            # Convert buffer distances to degree approximations
            # At equator: 1 degree ≈ 111,000 meters
            # Adjusted for latitude (approximate for Zimbabwe: -17 to -22 degrees)
            lat_center = (bounds.min_lat + bounds.max_lat) / 2
            meters_per_degree = 111000 * abs(math.cos(math.radians(lat_center)))
            
            edge_buffer_degrees = edge_buffer_meters / meters_per_degree
            min_distance_degrees = min_distance_meters / meters_per_degree
            
            # Generate sample points
            points = []
            max_attempts = min_samples * 100  # Prevent infinite loops
            attempts = 0
            
            while len(points) < min_samples and attempts < max_attempts:
                # Generate random candidate point
                candidate_lng = random.uniform(bounds.min_lng, bounds.max_lng)
                candidate_lat = random.uniform(bounds.min_lat, bounds.max_lat)
                
                # Check if point is inside field with buffer
                inside_check = text("""
                    SELECT ST_Contains(
                        ST_Buffer(ST_GeomFromText(:wkt, 4326), :buffer),
                        ST_Point(:lng, :lat)
                    )
                """)
                
                inside_result = await db.execute(inside_check, {
                    "wkt": field_boundary_wkt,
                    "buffer": -edge_buffer_degrees,  # Negative buffer = shrink polygon
                    "lng": candidate_lng,
                    "lat": candidate_lat
                })
                
                if not inside_result.scalar():
                    attempts += 1
                    continue
                
                # Check minimum distance from other points
                too_close = any(
                    SpatialService._calculate_distance(
                        candidate_lat, candidate_lng,
                        point['lat'], point['lng']
                    ) < min_distance_meters
                    for point in points
                )
                
                if too_close:
                    attempts += 1
                    continue
                
                # Calculate distance from field edge for quality assessment
                edge_distance_query = text("""
                    SELECT ST_Distance(
                        ST_Transform(ST_Point(:lng, :lat, 4326), 3857),
                        ST_Transform(ST_Boundary(ST_GeomFromText(:wkt, 4326)), 3857)
                    ) as distance_meters
                """)
                
                edge_result = await db.execute(edge_distance_query, {
                    "lng": candidate_lng,
                    "lat": candidate_lat,
                    "wkt": field_boundary_wkt
                })
                
                edge_distance = edge_result.scalar()
                
                # Add point to collection
                points.append({
                    "sample_number": len(points) + 1,
                    "lat": round(candidate_lat, 7),  # ~1cm precision
                    "lng": round(candidate_lng, 7),
                    "distance_from_edge_meters": round(float(edge_distance), 1),
                    "gps_accuracy_required": "sub_meter",  # Mobile app guidance
                    "sampling_notes": f"Random point {len(points) + 1} of {min_samples}"
                })
                
                attempts += 1
            
            if len(points) < min_samples:
                raise VerisSpatialError(
                    f"Could only generate {len(points)} of {min_samples} required points. "
                    f"Field may be too small or constraints too restrictive."
                )
            
            return points
            
        except Exception as e:
            raise VerisSpatialError(f"Sampling point generation failed: {str(e)}")
    
    @staticmethod
    def _calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two GPS points using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Earth radius in meters
        
        return c * r
    
    @staticmethod
    async def validate_field_boundary(coordinates: List[List[float]], 
                                    db: Session) -> Dict:
        """
        Comprehensive field boundary validation
        """
        try:
            # Basic coordinate validation
            if len(coordinates) < 4:
                return {"valid": False, "error": "Minimum 4 coordinate pairs required"}
            
            # Ensure closed polygon
            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            
            # Check coordinate ranges (rough bounds for Africa)
            for lng, lat in coordinates:
                if not (-25 <= lng <= 55):  # Africa longitude range
                    return {"valid": False, "error": f"Invalid longitude: {lng}"}
                if not (-35 <= lat <= 20):   # Africa latitude range  
                    return {"valid": False, "error": f"Invalid latitude: {lat}"}
            
            # Create polygon and validate with PostGIS
            coords_wkt = ",".join([f"{lng} {lat}" for lng, lat in coordinates])
            boundary_wkt = f"POLYGON(({coords_wkt}))"
            
            validation_query = text("""
                SELECT 
                    ST_IsValid(ST_GeomFromText(:wkt, 4326)) as is_valid,
                    ST_Area(ST_Transform(ST_GeomFromText(:wkt, 4326), 3857)) / 10000.0 as area_hectares,
                    ST_NumPoints(ST_GeomFromText(:wkt, 4326)) as num_points
            """)
            
            result = await db.execute(validation_query, {"wkt": boundary_wkt})
            row = result.fetchone()
            
            if not row.is_valid:
                return {"valid": False, "error": "Invalid polygon geometry"}
            
            if row.area_hectares < 0.01:  # Minimum 100 square meters
                return {"valid": False, "error": "Field too small (minimum 0.01 hectares)"}
                
            if row.area_hectares > 10000:  # Maximum 10,000 hectares
                return {"valid": False, "error": "Field too large (maximum 10,000 hectares)"}
            
            return {
                "valid": True,
                "area_hectares": round(float(row.area_hectares), 4),
                "num_points": int(row.num_points),
                "boundary_wkt": boundary_wkt
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}
```

**API Endpoints Implementation:**
```python
# app/api/v1/farms.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.spatial import Farm, Field
from app.schemas.spatial import (
    FarmCreate, FarmUpdate, FarmResponse,
    FieldCreate, FieldUpdate, FieldResponse,
    SamplingRequest, SamplingResponse
)
from app.services.spatial import SpatialService

router = APIRouter(prefix="/farms", tags=["farms"])

@router.post("/", response_model=FarmResponse, status_code=201)
async def create_farm(
    farm_data: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new farm with spatial capabilities
    
    Creates a farm record with GPS location and calculates spatial metrics.
    Validates tenant access and farm code uniqueness.
    """
    # Validate tenant access
    if current_user.role.role_name not in ["system_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check farm code uniqueness within tenant
    existing_farm = await db.execute(
        select(Farm).where(
            Farm.tenant_id == current_user.tenant_id,
            Farm.farm_code == farm_data.farm_code,
            Farm.is_active == True
        )
    )
    
    if existing_farm.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Farm code already exists")
    
    # Create farm with spatial processing
    farm = Farm(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **farm_data.dict(exclude={"farm_location"})
    )
    
    # Process GPS location if provided
    if farm_data.farm_location:
        farm.farm_location = f"POINT({farm_data.farm_location.lng} {farm_data.farm_location.lat})"
    
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    
    return farm

@router.get("/", response_model=List[FarmResponse])
async def list_farms(
    active_only: bool = Query(True, description="Filter to active farms only"),
    search: Optional[str] = Query(None, description="Search farm name or code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List farms with filtering and pagination
    
    Returns farms accessible to current user with spatial data included.
    """
    query = select(Farm).where(Farm.tenant_id == current_user.tenant_id)
    
    if active_only:
        query = query.where(Farm.is_active == True)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Farm.farm_name.ilike(search_pattern),
                Farm.farm_code.ilike(search_pattern),
                Farm.farmer_name.ilike(search_pattern)
            )
        )
    
    # Include related data
    query = query.options(selectinload(Farm.fields))
    query = query.offset(skip).limit(limit).order_by(Farm.created_at.desc())
    
    result = await db.execute(query)
    farms = result.scalars().all()
    
    return farms

@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: str = Path(..., description="Farm ID"),
    include_fields: bool = Query(True, description="Include field data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed farm information with spatial data"""
    
    query = select(Farm).where(
        Farm.id == farm_id,
        Farm.tenant_id == current_user.tenant_id
    )
    
    if include_fields:
        query = query.options(selectinload(Farm.fields))
    
    result = await db.execute(query)
    farm = result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    return farm

@router.post("/{farm_id}/fields", response_model=FieldResponse, status_code=201)
async def create_field(
    farm_id: str,
    field_data: FieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create field with GPS boundary polygon
    
    Validates field boundary, calculates area and center point automatically.
    """
    # Validate farm access
    farm_query = select(Farm).where(
        Farm.id == farm_id,
        Farm.tenant_id == current_user.tenant_id,
        Farm.is_active == True
    )
    
    farm_result = await db.execute(farm_query)
    farm = farm_result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")
    
    # Validate field boundary
    boundary_validation = await SpatialService.validate_field_boundary(
        field_data.boundary_coordinates, db
    )
    
    if not boundary_validation["valid"]:
        raise HTTPException(status_code=400, detail=boundary_validation["error"])
    
    # Check field code uniqueness within farm
    existing_field = await db.execute(
        select(Field).where(
            Field.farm_id == farm_id,
            Field.field_code == field_data.field_code
        )
    )
    
    if existing_field.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Field code already exists on this farm")
    
    # Calculate field metrics
    field_metrics = await SpatialService.calculate_field_metrics(
        field_data.boundary_coordinates, db
    )
    
    # Create field with calculated spatial data
    field = Field(
        farm_id=farm_id,
        field_code=field_data.field_code,
        field_name=field_data.field_name,
        field_boundary=field_metrics["boundary_wkt"],
        field_area=field_metrics["area_hectares"],
        field_center=f"POINT({field_metrics['center_lng']} {field_metrics['center_lat']})",
        soil_characteristics=field_data.soil_characteristics,
        irrigation_type=field_data.irrigation_type,
        elevation_meters=field_data.elevation_meters,
        slope_characteristics=field_data.slope_characteristics,
        access_notes=field_data.access_notes
    )
    
    db.add(field)
    await db.commit()
    await db.refresh(field)
    
    return field

@router.post("/{farm_id}/fields/{field_id}/sampling-points", 
            response_model=SamplingResponse)
async def generate_sampling_points(
    farm_id: str,
    field_id: str,
    sampling_request: SamplingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate GPS sampling points for field assessment
    
    This is core Verisca functionality - automated, scientific sampling.
    """
    # Validate field access
    field_query = select(Field).join(Farm).where(
        Field.id == field_id,
        Farm.id == farm_id,
        Farm.tenant_id == current_user.tenant_id
    )
    
    field_result = await db.execute(field_query)
    field = field_result.scalar_one_or_none()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found or access denied")
    
    # Get field boundary as WKT
    boundary_query = text("""
        SELECT ST_AsText(field_boundary) as boundary_wkt
        FROM fields WHERE id = :field_id
    """)
    
    boundary_result = await db.execute(boundary_query, {"field_id": field_id})
    boundary_wkt = boundary_result.scalar()
    
    if not boundary_wkt:
        raise HTTPException(status_code=500, detail="Field boundary data corrupted")
    
    # Generate sampling points
    try:
        sample_points = await SpatialService.generate_sampling_points(
            field_boundary_wkt=boundary_wkt,
            min_samples=sampling_request.minimum_samples,
            method=sampling_request.sampling_method,
            edge_buffer_meters=sampling_request.edge_buffer_meters,
            min_distance_meters=sampling_request.min_distance_meters,
            db=db
        )
        
        return SamplingResponse(
            field_id=field_id,
            farm_id=farm_id,
            field_area_hectares=float(field.field_area),
            sampling_method=sampling_request.sampling_method,
            total_sample_points=len(sample_points),
            sample_points=sample_points,
            generation_timestamp=datetime.utcnow(),
            gps_accuracy_requirements={
                "minimum_accuracy_meters": 1.0,
                "required_satellites": 8,
                "collection_duration_seconds": 30
            }
        )
        
    except VerisSpatialError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sampling generation failed: {str(e)}")
```

### 2. CLAIMS MANAGEMENT SYSTEM 📋

**Models:**
```python
# app/models/claims.py
class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Claim identification
    claim_number = Column(String(50), unique=True, nullable=False)
    policy_number = Column(String(100), nullable=False, index=True)
    insured_name = Column(String(100), nullable=False, index=True)
    
    # Spatial references
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    
    # Agricultural data
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    variety_id = Column(UUID(as_uuid=True), ForeignKey("crop_varieties.id"))
    planting_date = Column(Date, nullable=False)
    expected_harvest_date = Column(Date)
    expected_yield = Column(DECIMAL(8,2), nullable=False)  # tonnes/hectare
    insured_area = Column(DECIMAL(8,2), nullable=False)    # hectares
    sum_insured = Column(DECIMAL(12,2))  # Total coverage amount
    
    # Loss information
    loss_notification_date = Column(Date, nullable=False, index=True)
    suspected_peril_id = Column(UUID(as_uuid=True), ForeignKey("perils.id"))
    peril_severity_level = Column(String(20))  # From lookup tables
    loss_description = Column(Text)
    estimated_loss_percentage = Column(DECIMAL(5,2))
    
    # Workflow status
    claim_status = Column(String(30), default="reported", nullable=False, index=True)
    # Values: reported, assigned, in_progress, field_complete, calculated, completed, settled
    priority = Column(String(20), default="normal")  # urgent, high, normal, low
    
    # Assignment
    assigned_assessor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assignment_date = Column(DateTime(timezone=True))
    target_completion_date = Column(Date)
    actual_completion_date = Column(DateTime(timezone=True))
    
    # Final results
    final_loss_percentage = Column(DECIMAL(5,2))
    final_yield_estimate = Column(DECIMAL(8,2))  # tonnes/hectare
    settlement_amount = Column(DECIMAL(12,2))
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="claims")
    farm = relationship("Farm", back_populates="claims")
    field = relationship("Field", back_populates="claims")
    crop = relationship("Crop", back_populates="claims")
    variety = relationship("CropVariety", back_populates="claims")
    suspected_peril = relationship("Peril", back_populates="claims")
    assigned_assessor = relationship("User", foreign_keys=[assigned_assessor_id])
    assessment_sessions = relationship("AssessmentSession", back_populates="claim")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('expected_yield > 0', name='positive_expected_yield'),
        CheckConstraint('insured_area > 0', name='positive_insured_area'),
        CheckConstraint('estimated_loss_percentage >= 0 AND estimated_loss_percentage <= 100', 
                       name='valid_loss_percentage'),
        Index('idx_claims_status_date', 'claim_status', 'loss_notification_date'),
        Index('idx_claims_tenant_status', 'tenant_id', 'claim_status'),
    )

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    session_number = Column(Integer, nullable=False, default=1)
    
    # Assessor and methodology
    assessor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    method_id = Column(UUID(as_uuid=True), ForeignKey("assessment_methods.id"), nullable=False)
    peril_id = Column(UUID(as_uuid=True), ForeignKey("perils.id"), nullable=False)
    growth_stage_id = Column(UUID(as_uuid=True), ForeignKey("growth_stages.id"), nullable=False)
    methodology_version_id = Column(UUID(as_uuid=True), ForeignKey("methodology_versions.id"))
    
    # Session status
    session_status = Column(String(30), default="planned", nullable=False)
    # Values: planned, in_progress, field_complete, calculated, completed, cancelled
    session_type = Column(String(30), default="primary")  # primary, follow_up, quality_check
    
    # Field visit data
    visit_date = Column(Date)
    visit_start_time = Column(DateTime(timezone=True))
    visit_end_time = Column(DateTime(timezone=True))
    weather_conditions = Column(JSONB)  # Temperature, humidity, wind, precipitation
    field_access_notes = Column(Text)
    
    # Growth stage assessment
    assessed_growth_stage_confidence = Column(DECIMAL(3,2))  # 0.00-1.00
    variety_stage_adjustment = Column(JSONB)  # Variety-specific timing adjustments
    
    # Sampling configuration
    sampling_plan = Column(JSONB, nullable=False)  # Complete sampling setup
    actual_samples_collected = Column(Integer)
    sampling_quality_score = Column(DECIMAL(3,2))  # Quality assessment 0.00-1.00
    
    # Assessment results
    raw_assessment_data = Column(JSONB)  # All field measurements
    calculation_results = Column(JSONB)  # Intermediate calculations
    final_appraisal = Column(DECIMAL(8,2))  # tonnes/hectare
    confidence_score = Column(DECIMAL(3,2))  # Overall confidence 0.00-1.00
    quality_flags = Column(JSONB, default='[]')  # Array of quality issues
    
    # Evidence summary
    total_photos_captured = Column(Integer, default=0)
    total_gps_points_captured = Column(Integer, default=0)
    evidence_quality_score = Column(DECIMAL(3,2))
    field_notes = Column(Text)
    
    # Technical metadata
    app_version = Column(String(20))  # Mobile app version used
    device_info = Column(JSONB)  # Device and technical information
    gps_accuracy_meters = Column(DECIMAL(5,2))  # Average GPS accuracy
    
    # Offline/Sync information
    session_created_offline = Column(Boolean, default=False)
    last_synced_at = Column(DateTime(timezone=True))
    sync_status = Column(String(20), default="pending")  # pending, syncing, synced, conflict
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="assessment_sessions")
    assessor = relationship("User", back_populates="assessment_sessions")
    method = relationship("AssessmentMethod", back_populates="assessment_sessions")
    peril = relationship("Peril", back_populates="assessment_sessions")
    growth_stage = relationship("GrowthStage", back_populates="assessment_sessions")
    sample_points = relationship("SamplePoint", back_populates="session", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="session", cascade="all, delete-orphan")
    calculations = relationship("Calculation", back_populates="session", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('claim_id', 'session_number', name='unique_claim_session_number'),
        CheckConstraint('assessed_growth_stage_confidence >= 0 AND assessed_growth_stage_confidence <= 1',
                       name='valid_growth_stage_confidence'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1',
                       name='valid_confidence_score'),
        Index('idx_sessions_claim', 'claim_id'),
        Index('idx_sessions_assessor', 'assessor_id'),
        Index('idx_sessions_status', 'session_status'),
    )
```

**Claims API:**
```python
# app/api/v1/claims.py
@router.post("/", response_model=ClaimResponse, status_code=201)
async def create_claim(
    claim_data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new insurance claim with comprehensive validation
    """
    # Generate unique claim number
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    claim_number = f"VER-{current_user.tenant.tenant_code}-{timestamp}-{random_suffix}"
    
    # Validate field access and get spatial data
    field_query = select(Field).join(Farm).where(
        Field.id == claim_data.field_id,
        Farm.tenant_id == current_user.tenant_id
    ).options(selectinload(Field.farm))
    
    field_result = await db.execute(field_query)
    field = field_result.scalar_one_or_none()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found or access denied")
    
    # Validate crop and variety
    if claim_data.variety_id:
        variety_query = select(CropVariety).where(
            CropVariety.id == claim_data.variety_id,
            CropVariety.crop_id == claim_data.crop_id
        )
        variety_result = await db.execute(variety_query)
        if not variety_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid crop variety for selected crop")
    
    # Business validation
    if claim_data.insured_area > field.field_area:
        raise HTTPException(
            status_code=400, 
            detail=f"Insured area ({claim_data.insured_area} ha) exceeds field area ({field.field_area} ha)"
        )
    
    # Validate planting date
    if claim_data.planting_date > date.today():
        raise HTTPException(status_code=400, detail="Planting date cannot be in the future")
        
    if claim_data.loss_notification_date < claim_data.planting_date:
        raise HTTPException(status_code=400, detail="Loss notification cannot be before planting date")
    
    # Create claim
    claim = Claim(
        tenant_id=current_user.tenant_id,
        claim_number=claim_number,
        created_by=current_user.id,
        **claim_data.dict(exclude={"farm_id"}),  # farm_id derived from field
        farm_id=field.farm_id
    )
    
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    
    # Load full claim data for response
    full_claim = await db.execute(
        select(Claim)
        .options(
            selectinload(Claim.farm),
            selectinload(Claim.field),
            selectinload(Claim.crop),
            selectinload(Claim.variety),
            selectinload(Claim.suspected_peril)
        )
        .where(Claim.id == claim.id)
    )
    
    return full_claim.scalar_one()

@router.get("/", response_model=List[ClaimResponse])
async def list_claims(
    status: Optional[str] = Query(None, description="Filter by claim status"),
    assignee: Optional[str] = Query(None, description="Filter by assignee ('me', 'unassigned', or user_id)"),
    peril: Optional[str] = Query(None, description="Filter by peril type"),
    date_from: Optional[date] = Query(None, description="Filter claims from this date"),
    date_to: Optional[date] = Query(None, description="Filter claims to this date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List claims with comprehensive filtering
    """
    query = select(Claim).where(Claim.tenant_id == current_user.tenant_id)
    
    # Apply filters
    if status:
        query = query.where(Claim.claim_status == status)
    
    if assignee == "me":
        query = query.where(Claim.assigned_assessor_id == current_user.id)
    elif assignee == "unassigned":
        query = query.where(Claim.assigned_assessor_id.is_(None))
    elif assignee:  # Specific user ID
        query = query.where(Claim.assigned_assessor_id == assignee)
    
    if peril:
        peril_subquery = select(Peril.id).where(Peril.peril_code == peril)
        query = query.where(Claim.suspected_peril_id.in_(peril_subquery))
    
    if date_from:
        query = query.where(Claim.loss_notification_date >= date_from)
    
    if date_to:
        query = query.where(Claim.loss_notification_date <= date_to)
    
    # Include related data for efficient loading
    query = query.options(
        selectinload(Claim.farm),
        selectinload(Claim.field),
        selectinload(Claim.crop),
        selectinload(Claim.assigned_assessor)
    )
    
    # Apply pagination and ordering
    query = query.offset(skip).limit(limit).order_by(Claim.loss_notification_date.desc())
    
    result = await db.execute(query)
    claims = result.scalars().all()
    
    return claims

@router.patch("/{claim_id}/assign", response_model=ClaimResponse)
async def assign_claim(
    claim_id: str,
    assignment: ClaimAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign claim to assessor with business logic validation
    """
    # Validate claim access
    claim_query = select(Claim).where(
        Claim.id == claim_id,
        Claim.tenant_id == current_user.tenant_id
    )
    
    claim_result = await db.execute(claim_query)
    claim = claim_result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Validate current status allows assignment
    if claim.claim_status not in ["reported", "assigned"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot assign claim in status: {claim.claim_status}"
        )
    
    # Validate assessor
    assessor_query = select(User).where(
        User.id == assignment.assessor_id,
        User.tenant_id == current_user.tenant_id,
        User.is_active == True
    ).options(selectinload(User.role))
    
    assessor_result = await db.execute(assessor_query)
    assessor = assessor_result.scalar_one_or_none()
    
    if not assessor:
        raise HTTPException(status_code=404, detail="Assessor not found")
    
    if "assessor" not in assessor.role.role_name.lower():
        raise HTTPException(status_code=400, detail="User does not have assessor role")
    
    # Check assessor workload (business rule: max 10 active claims)
    active_claims = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.assigned_assessor_id == assignment.assessor_id,
            Claim.claim_status.in_(["assigned", "in_progress", "field_complete"])
        )
    )
    
    if active_claims.scalar() >= 10:
        raise HTTPException(
            status_code=400,
            detail="Assessor has reached maximum active claims (10)"
        )
    
    # Update claim assignment
    claim.assigned_assessor_id = assignment.assessor_id
    claim.assignment_date = datetime.utcnow()
    claim.target_completion_date = assignment.target_completion_date
    claim.claim_status = "assigned"
    claim.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(claim)
    
    return claim

@router.post("/{claim_id}/assessment-sessions", response_model=SessionResponse, status_code=201)
async def create_assessment_session(
    claim_id: str,
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new assessment session with automated method selection
    """
    # Validate claim access and status
    claim_query = select(Claim).where(
        Claim.id == claim_id,
        Claim.tenant_id == current_user.tenant_id
    ).options(
        selectinload(Claim.crop),
        selectinload(Claim.field)
    )
    
    claim_result = await db.execute(claim_query)
    claim = claim_result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Validate assessor assignment
    if claim.assigned_assessor_id != current_user.id:
        if current_user.role.role_name not in ["system_admin", "tenant_admin"]:
            raise HTTPException(status_code=403, detail="Claim not assigned to you")
    
    # Get next session number
    max_session = await db.execute(
        select(func.max(AssessmentSession.session_number)).where(
            AssessmentSession.claim_id == claim_id
        )
    )
    next_session_number = (max_session.scalar() or 0) + 1
    
    # Validate method applicability for crop/peril/growth stage
    method_validation = await db.execute(
        select(CropPerilMethod).where(
            CropPerilMethod.crop_id == claim.crop_id,
            CropPerilMethod.peril_id == session_data.peril_id,
            CropPerilMethod.method_id == session_data.method_id,
            CropPerilMethod.is_active == True
        )
    )
    
    if not method_validation.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Selected method not applicable for this crop/peril combination"
        )
    
    # Generate sampling plan if not provided
    if not session_data.sampling_plan:
        # Get field boundary for sampling
        field_boundary = await db.execute(
            text("SELECT ST_AsText(field_boundary) FROM fields WHERE id = :field_id"),
            {"field_id": str(claim.field_id)}
        )
        boundary_wkt = field_boundary.scalar()
        
        # Generate sample points
        sample_points = await SpatialService.generate_sampling_points(
            field_boundary_wkt=boundary_wkt,
            min_samples=3,  # Default minimum
            db=db
        )
        
        sampling_plan = {
            "method": "random",
            "minimum_samples": len(sample_points),
            "sample_points": sample_points,
            "generated_at": datetime.utcnow().isoformat(),
            "field_area_hectares": float(claim.field.field_area)
        }
    else:
        sampling_plan = session_data.sampling_plan
    
    # Create assessment session
    session = AssessmentSession(
        claim_id=claim_id,
        session_number=next_session_number,
        assessor_id=current_user.id,
        method_id=session_data.method_id,
        peril_id=session_data.peril_id,
        growth_stage_id=session_data.growth_stage_id,
        visit_date=session_data.visit_date,
        sampling_plan=sampling_plan,
        session_type=session_data.session_type or "primary"
    )
    
    db.add(session)
    
    # Update claim status
    if claim.claim_status == "assigned":
        claim.claim_status = "in_progress"
        claim.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(session)
    
    return session
```

### 3. USDA CALCULATION ENGINE 🧮

**Core Calculation Service:**
```python
# app/services/calculations.py
from typing import List, Dict, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import math
from app.core.exceptions import VerisCalculationError

@dataclass
class SampleMeasurement:
    """Single sample measurement data"""
    sample_number: int
    surviving_plants: int
    normal_plant_population: int
    growth_stage: str
    base_yield: float
    row_width_cm: float
    sample_area_hectares: float
    measurement_confidence: float = 1.0
    notes: Optional[str] = None

@dataclass
class CalculationStep:
    """Individual calculation step for audit trail"""
    step_number: int
    step_name: str
    input_values: Dict
    formula_used: str
    result: float
    result_unit: str
    notes: Optional[str] = None

@dataclass
class AssessmentResult:
    """Complete assessment calculation result"""
    method: str
    methodology_source: str
    sample_results: List[Dict]
    calculation_steps: List[CalculationStep]
    final_appraisal: float
    confidence_score: float
    quality_indicators: Dict
    calculation_timestamp: str
    total_samples_used: int

class USDACalculationEngine:
    """
    World-class implementation of USDA FCIC-25080 Corn Loss Adjustment Standards
    
    This engine provides scientifically accurate, auditable calculations that match
    the USDA methodology exactly. All lookup tables, interpolation methods, and
    rounding rules follow official USDA specifications.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.methodology_source = "USDA_FCIC_25080"
        
    async def calculate_stand_reduction(self, samples: List[SampleMeasurement]) -> AssessmentResult:
        """
        Calculate stand reduction using exact USDA methodology
        
        Implements the complete USDA stand reduction workflow:
        1. Calculate percent of stand for each sample
        2. Round to nearest 5% (USDA standard)
        3. Lookup percent potential from official exhibits
        4. Apply interpolation if needed
        5. Calculate individual sample appraisals
        6. Compute final average appraisal
        7. Assess calculation confidence
        """
        if not samples:
            raise VerisCalculationError("No sample data provided for calculation")
        
        calculation_steps = []
        sample_results = []
        
        # Validate all samples before processing
        for sample in samples:
            self._validate_sample_data(sample)
        
        # Process each sample
        for i, sample in enumerate(samples):
            # Step 1: Calculate percent of stand
            percent_stand = (sample.surviving_plants / sample.normal_plant_population) * 100
            
            calculation_steps.append(CalculationStep(
                step_number=len(calculation_steps) + 1,
                step_name=f"Calculate Percent Stand - Sample {sample.sample_number}",
                input_values={
                    "surviving_plants": sample.surviving_plants,
                    "normal_plant_population": sample.normal_plant_population
                },
                formula_used="(surviving_plants / normal_plant_population) × 100",
                result=percent_stand,
                result_unit="percent",
                notes=f"Raw percentage before rounding"
            ))
            
            # Step 2: Round to nearest 5% (USDA standard)
            rounded_percent_stand = self._round_to_nearest_5(percent_stand)
            
            calculation_steps.append(CalculationStep(
                step_number=len(calculation_steps) + 1,
                step_name=f"Round Stand Percentage - Sample {sample.sample_number}",
                input_values={"raw_percent": percent_stand},
                formula_used="Round to nearest 5%",
                result=rounded_percent_stand,
                result_unit="percent",
                notes="USDA requires rounding to 5% increments for lookup tables"
            ))
            
            # Step 3: Lookup percent potential from USDA exhibits
            percent_potential = await self._lookup_percent_potential(
                stand_percentage=rounded_percent_stand,
                growth_stage=sample.growth_stage
            )
            
            calculation_steps.append(CalculationStep(
                step_number=len(calculation_steps) + 1,
                step_name=f"Lookup Percent Potential - Sample {sample.sample_number}",
                input_values={
                    "stand_percent": rounded_percent_stand,
                    "growth_stage": sample.growth_stage
                },
                formula_used="USDA Exhibit Lookup with interpolation",
                result=percent_potential,
                result_unit="percent",
                notes=f"From USDA exhibit for {sample.growth_stage} stage"
            ))
            
            # Step 4: Calculate sample appraisal
            sample_appraisal = (percent_potential / 100) * sample.base_yield
            
            calculation_steps.append(CalculationStep(
                step_number=len(calculation_steps) + 1,
                step_name=f"Calculate Sample Appraisal - Sample {sample.sample_number}",
                input_values={
                    "percent_potential": percent_potential,
                    "base_yield": sample.base_yield
                },
                formula_used="(percent_potential / 100) × base_yield",
                result=sample_appraisal,
                result_unit="tonnes_per_hectare",
                notes="Final appraisal for this sample"
            ))
            
            # Store sample result
            sample_result = {
                "sample_number": sample.sample_number,
                "surviving_plants": sample.surviving_plants,
                "normal_plant_population": sample.normal_plant_population,
                "percent_stand": round(percent_stand, 1),
                "rounded_percent_stand": rounded_percent_stand,
                "percent_potential": percent_potential,
                "sample_appraisal": round(sample_appraisal, 1),
                "measurement_confidence": sample.measurement_confidence,
                "notes": sample.notes
            }
            
            sample_results.append(sample_result)
        
        # Step 5: Calculate final average appraisal
        total_appraisal = sum(result["sample_appraisal"] for result in sample_results)
        final_appraisal = total_appraisal / len(sample_results)
        
        calculation_steps.append(CalculationStep(
            step_number=len(calculation_steps) + 1,
            step_name="Calculate Final Average Appraisal",
            input_values={
                "sample_appraisals": [r["sample_appraisal"] for r in sample_results],
                "total_samples": len(sample_results)
            },
            formula_used="Sum(sample_appraisals) / number_of_samples",
            result=final_appraisal,
            result_unit="tonnes_per_hectare",
            notes="Final field appraisal (USDA average method)"
        ))
        
        # Step 6: Calculate confidence score
        confidence_score = self._calculate_confidence_score(sample_results)
        quality_indicators = self._assess_quality_indicators(sample_results, samples)
        
        return AssessmentResult(
            method="stand_reduction",
            methodology_source=self.methodology_source,
            sample_results=sample_results,
            calculation_steps=calculation_steps,
            final_appraisal=round(final_appraisal, 1),
            confidence_score=confidence_score,
            quality_indicators=quality_indicators,
            calculation_timestamp=datetime.utcnow().isoformat(),
            total_samples_used=len(samples)
        )
    
    async def _lookup_percent_potential(self, stand_percentage: int, growth_stage: str) -> float:
        """
        Query USDA lookup tables with interpolation support
        
        Uses proper USDA exhibits:
        - Exhibit 11: Emergence through 10th Leaf
        - Exhibit 12: 11th Leaf through Tasseling
        - Milk Stage: Direct correlation (100% stand = 100% potential)
        """
        # Determine which exhibit to use based on growth stage
        exhibit_code = self._get_exhibit_for_stage(growth_stage)
        
        if exhibit_code == "DIRECT_CORRELATION":
            # Milk stage and later: direct relationship
            return float(stand_percentage)
        
        # Query exact match first
        exact_match = await self.db.execute(
            text("""
                SELECT output_value
                FROM lookup_table_data ltd
                JOIN lookup_table_definitions ltd ON ltd.table_definition_id = ltd.id
                WHERE ltd.table_code = :exhibit_code
                AND ltd.input_values->>'stand_percent' = :stand_percent::text
                AND ltd.input_values->>'growth_stage' = :growth_stage
            """),
            {
                "exhibit_code": exhibit_code,
                "stand_percent": stand_percentage,
                "growth_stage": growth_stage
            }
        )
        
        exact_result = exact_match.scalar()
        if exact_result:
            return float(exact_result)
        
        # No exact match - perform interpolation
        return await self._interpolate_percent_potential(exhibit_code, stand_percentage, growth_stage)
    
    async def _interpolate_percent_potential(self, exhibit_code: str, 
                                           stand_percent: int, growth_stage: str) -> float:
        """
        Perform linear interpolation between lookup table values
        
        USDA methodology requires interpolation when exact values aren't found.
        """
        # Find bounding values for interpolation
        lower_query = text("""
            SELECT (ltd.input_values->>'stand_percent')::int as stand_pct,
                   ltd.output_value
            FROM lookup_table_data ltd
            JOIN lookup_table_definitions ltd ON ltd.table_definition_id = ltd.id
            WHERE ltd.table_code = :exhibit_code
            AND ltd.input_values->>'growth_stage' = :growth_stage
            AND (ltd.input_values->>'stand_percent')::int <= :stand_percent
            ORDER BY (ltd.input_values->>'stand_percent')::int DESC
            LIMIT 1
        """)
        
        upper_query = text("""
            SELECT (ltd.input_values->>'stand_percent')::int as stand_pct,
                   ltd.output_value
            FROM lookup_table_data ltd
            JOIN lookup_table_definitions ltd ON ltd.table_definition_id = ltd.id
            WHERE ltd.table_code = :exhibit_code
            AND ltd.input_values->>'growth_stage' = :growth_stage
            AND (ltd.input_values->>'stand_percent')::int >= :stand_percent
            ORDER BY (ltd.input_values->>'stand_percent')::int ASC
            LIMIT 1
        """)
        
        lower_result = await self.db.execute(lower_query, {
            "exhibit_code": exhibit_code,
            "growth_stage": growth_stage,
            "stand_percent": stand_percent
        })
        
        upper_result = await self.db.execute(upper_query, {
            "exhibit_code": exhibit_code,
            "growth_stage": growth_stage,
            "stand_percent": stand_percent
        })
        
        lower_row = lower_result.fetchone()
        upper_row = upper_result.fetchone()
        
        if not lower_row or not upper_row:
            raise VerisCalculationError(
                f"Cannot find lookup values for {growth_stage} at {stand_percent}% stand in {exhibit_code}"
            )
        
        # Perform linear interpolation
        x1, y1 = int(lower_row.stand_pct), float(lower_row.output_value)
        x2, y2 = int(upper_row.stand_pct), float(upper_row.output_value)
        
        if x1 == x2:  # Exact match case
            return y1
        
        # Linear interpolation formula: y = y1 + (y2-y1) * (x-x1) / (x2-x1)
        interpolated = y1 + (y2 - y1) * (stand_percent - x1) / (x2 - x1)
        
        # Round to nearest whole percent per USDA standards
        return round(interpolated)
    
    def _get_exhibit_for_stage(self, growth_stage: str) -> str:
        """Determine which USDA exhibit to use for growth stage"""
        early_stages = ['EMERGENCE', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10']
        late_stages = ['V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'VT', 'R1']
        milk_stages = ['R2', 'R3', 'R4', 'R5', 'R6']
        
        if growth_stage in early_stages:
            return 'MAIZE_STAND_REDUCTION_EARLY'  # Exhibit 11
        elif growth_stage in late_stages:
            return 'MAIZE_STAND_REDUCTION_LATE'   # Exhibit 12
        elif growth_stage in milk_stages:
            return 'DIRECT_CORRELATION'           # Milk stage rule
        else:
            raise VerisCalculationError(f"Unknown growth stage: {growth_stage}")
    
    def _round_to_nearest_5(self, value: float) -> int:
        """Round to nearest 5 percent per USDA standards"""
        return int(round(value / 5) * 5)
    
    def _validate_sample_data(self, sample: SampleMeasurement) -> None:
        """Validate sample data meets USDA requirements"""
        if sample.surviving_plants < 0:
            raise VerisCalculationError(f"Sample {sample.sample_number}: Surviving plants cannot be negative")
        
        if sample.normal_plant_population <= 0:
            raise VerisCalculationError(f"Sample {sample.sample_number}: Normal plant population must be positive")
        
        if sample.surviving_plants > sample.normal_plant_population:
            raise VerisCalculationError(
                f"Sample {sample.sample_number}: Surviving plants cannot exceed normal population"
            )
        
        if sample.base_yield <= 0:
            raise VerisCalculationError(f"Sample {sample.sample_number}: Base yield must be positive")
        
        if sample.sample_area_hectares <= 0:
            raise VerisCalculationError(f"Sample {sample.sample_number}: Sample area must be positive")
    
    def _calculate_confidence_score(self, sample_results: List[Dict]) -> float:
        """
        Calculate assessment confidence based on sample variance and quality
        
        Higher confidence = lower variance between samples
        """
        if len(sample_results) < 2:
            return 0.6  # Lower confidence with single sample
        
        appraisals = [result["sample_appraisal"] for result in sample_results]
        mean_appraisal = sum(appraisals) / len(appraisals)
        
        if mean_appraisal == 0:
            return 1.0  # Perfect confidence if all samples show total loss
        
        # Calculate coefficient of variation
        variance = sum((x - mean_appraisal) ** 2 for x in appraisals) / len(appraisals)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_appraisal
        
        # Convert CV to confidence score (0.0 to 1.0)
        # CV of 0.0 = perfect confidence (1.0)
        # CV of 0.3+ = low confidence (0.1)
        confidence = max(0.1, min(1.0, 1.0 - (cv / 0.3)))
        
        # Adjust for measurement confidence
        avg_measurement_confidence = sum(
            result["measurement_confidence"] for result in sample_results
        ) / len(sample_results)
        
        final_confidence = confidence * avg_measurement_confidence
        
        return round(final_confidence, 2)
    
    def _assess_quality_indicators(self, sample_results: List[Dict], 
                                 samples: List[SampleMeasurement]) -> Dict:
        """Assess calculation quality indicators"""
        return {
            "sample_count": len(sample_results),
            "sample_variance": self._calculate_sample_variance(sample_results),
            "all_samples_valid": all(r["measurement_confidence"] >= 0.7 for r in sample_results),
            "methodology_compliance": "USDA_FCIC_25080",
            "interpolation_used": any(
                # Check if any values required interpolation
                not self._is_standard_lookup_value(r["rounded_percent_stand"])
                for r in sample_results
            ),
            "edge_effects_detected": any(
                # Check if samples were too close to field edges
                hasattr(s, 'distance_from_edge') and s.distance_from_edge < 5
                for s in samples
            )
        }
    
    def _calculate_sample_variance(self, sample_results: List[Dict]) -> float:
        """Calculate variance between sample appraisals"""
        if len(sample_results) < 2:
            return 0.0
        
        appraisals = [result["sample_appraisal"] for result in sample_results]
        mean = sum(appraisals) / len(appraisals)
        variance = sum((x - mean) ** 2 for x in appraisals) / len(appraisals)
        
        return round(variance, 2)
    
    def _is_standard_lookup_value(self, percent_stand: int) -> bool:
        """Check if percent stand is standard lookup value (increments of 5)"""
        return percent_stand % 5 == 0
```

**Calculation API:**
```python
# app/api/v1/calculations.py
@router.post("/stand-reduction", response_model=CalculationResponse)
async def calculate_stand_reduction(
    calculation_request: StandReductionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform USDA stand reduction calculation with full audit trail
    
    This endpoint provides world-class agricultural assessment calculations
    following exact USDA FCIC-25080 methodology.
    """
    # Validate session access
    session_query = select(AssessmentSession).join(Claim).where(
        AssessmentSession.id == calculation_request.session_id,
        Claim.tenant_id == current_user.tenant_id
    ).options(selectinload(AssessmentSession.claim))
    
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    
    # Validate assessor access
    if session.assessor_id != current_user.id:
        if current_user.role.role_name not in ["system_admin", "tenant_admin", "supervisor"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Convert request to calculation format
    samples = [
        SampleMeasurement(
            sample_number=s.sample_number,
            surviving_plants=s.surviving_plants,
            normal_plant_population=s.normal_plant_population,
            growth_stage=s.growth_stage,
            base_yield=float(s.base_yield),
            row_width_cm=float(s.row_width_cm or 75),  # Default 75cm rows
            sample_area_hectares=float(s.sample_area_hectares),
            measurement_confidence=float(s.measurement_confidence or 1.0),
            notes=s.notes
        )
        for s in calculation_request.samples
    ]
    
    # Perform calculation
    calculation_engine = USDACalculationEngine(db)
    
    try:
        result = await calculation_engine.calculate_stand_reduction(samples)
    except VerisCalculationError as e:
        raise HTTPException(status_code=422, detail=f"Calculation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal calculation error: {str(e)}")
    
    # Store calculation in database for complete audit trail
    calculation_record = Calculation(
        session_id=calculation_request.session_id,
        calculation_step=1,  # Primary calculation
        calculation_type='stand_reduction',
        calculation_name='USDA Stand Reduction Method',
        input_data=calculation_request.dict(),
        intermediate_results={
            "sample_results": result.sample_results,
            "calculation_steps": [step.__dict__ for step in result.calculation_steps],
            "quality_indicators": result.quality_indicators
        },
        final_result=Decimal(str(result.final_appraisal)),
        result_units='tonnes_per_hectare',
        calculation_confidence=Decimal(str(result.confidence_score)),
        validation_status='valid',
        calculated_at=datetime.utcnow(),
        calculation_version='1.0'
    )
    
    db.add(calculation_record)
    
    # Update session with results
    session.final_appraisal = Decimal(str(result.final_appraisal))
    session.confidence_score = Decimal(str(result.confidence_score))
    session.calculation_results = {
        "method": result.method,
        "final_appraisal": result.final_appraisal,
        "confidence_score": result.confidence_score,
        "total_samples": result.total_samples_used,
        "calculation_timestamp": result.calculation_timestamp
    }
    session.session_status = 'calculated'
    session.updated_at = datetime.utcnow()
    
    # Update parent claim if this is primary assessment
    if session.session_type == 'primary':
        claim = session.claim
        claim.final_loss_percentage = Decimal('100') - (Decimal(str(result.final_appraisal)) / Decimal(str(calculation_request.base_yield))) * Decimal('100')
        claim.final_yield_estimate = Decimal(str(result.final_appraisal))
        claim.claim_status = 'calculated'
        claim.updated_by = current_user.id
    
    await db.commit()
    
    return CalculationResponse(
        session_id=str(session.id),
        calculation_id=str(calculation_record.id),
        method=result.method,
        methodology_source=result.methodology_source,
        final_appraisal=result.final_appraisal,
        confidence_score=result.confidence_score,
        sample_count=result.total_samples_used,
        sample_results=result.sample_results,
        calculation_steps=result.calculation_steps,
        quality_indicators=result.quality_indicators,
        calculation_timestamp=result.calculation_timestamp
    )
```

---

## QUALITY & PERFORMANCE REQUIREMENTS

### Code Quality Standards:
- **Type Hints**: All functions must have complete type annotations
- **Documentation**: Comprehensive docstrings for all classes and methods
- **Error Handling**: Specific exception types with detailed error messages
- **Logging**: Structured logging for all operations (DEBUG, INFO, WARNING, ERROR)
- **Testing**: Unit tests for all calculation algorithms with USDA validation data

### Performance Targets:
- **API Response Time**: <100ms for calculations, <50ms for CRUD operations
- **Database Queries**: Optimized with proper indexes, no N+1 queries
- **Concurrent Users**: Support 100+ concurrent assessments
- **Memory Usage**: <512MB per worker process
- **Calculation Accuracy**: Match USDA results to 0.1 precision

### Security Requirements:
- **Input Validation**: Strict Pydantic schemas for all endpoints
- **SQL Injection**: Use parameterized queries exclusively
- **Multi-tenant Isolation**: Complete data separation via tenant_id filtering
- **Authentication**: JWT token validation on all endpoints
- **Audit Logging**: Complete trail of all data modifications

---

## DEPLOYMENT & MONITORING

### Environment Configuration:
```env
# Production environment variables
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SECRET_KEY=your-secret-key-for-jwt
CORS_ORIGINS=["https://yourdomain.com"]
DEBUG=false

# USDA calculation settings
USDA_LOOKUP_TABLES_ENABLED=true
CALCULATION_PRECISION=1  # Decimal places for final results
INTERPOLATION_ENABLED=true

# Performance settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
ASYNC_WORKERS=4

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

### Monitoring & Alerts:
```python
# Add performance monitoring to calculation endpoints
import time
from app.core.metrics import track_calculation_performance

@router.post("/calculations/stand-reduction")
async def calculate_stand_reduction(...):
    start_time = time.time()
    
    try:
        result = await calculation_engine.calculate_stand_reduction(samples)
        
        # Track success metrics
        track_calculation_performance(
            method="stand_reduction",
            duration_ms=(time.time() - start_time) * 1000,
            sample_count=len(samples),
            success=True
        )
        
        return result
        
    except Exception as e:
        # Track failure metrics
        track_calculation_performance(
            method="stand_reduction",
            duration_ms=(time.time() - start_time) * 1000,
            sample_count=len(samples),
            success=False,
            error_type=type(e).__name__
        )
        raise
```

---

## SUCCESS METRICS

### Technical KPIs:
- ✅ **100% USDA Accuracy**: All calculations match official USDA results
- ✅ **Sub-second Performance**: 95% of requests complete in <1 second
- ✅ **99.9% Uptime**: Production service availability
- ✅ **Zero Data Loss**: Complete audit trail and backup systems
- ✅ **Multi-tenant Scalability**: Support unlimited insurers

### Business KPIs:
- ✅ **Assessment Speed**: <30 minutes per field (vs 2-4 hours manual)
- ✅ **Consistency**: <5% variance between assessors (vs 30%+ manual)
- ✅ **Scientific Credibility**: USDA methodology compliance
- ✅ **Regulatory Compliance**: Complete audit trail and documentation
- ✅ **Market Ready**: Production deployment with real insurer data

---

This implementation creates the world's most advanced agricultural assessment backend. Follow these specifications exactly to build a system that revolutionizes agricultural insurance technology with scientific precision and enterprise reliability.

**Your API will be the global standard for digital crop loss assessment! 🌍🌽📊**
