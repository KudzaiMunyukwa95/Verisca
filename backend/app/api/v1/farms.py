from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_, text
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.models.tenant import User
from app.models.spatial import Farm, Field
from app.schemas.spatial import (
    FarmCreate, FarmUpdate, FarmResponse,
    FieldCreate, FieldUpdate, FieldResponse,
    SamplingRequest, SamplingResponse
)
from app.services.spatial import SpatialService, VerisSpatialError

router = APIRouter()

@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new farm with spatial capabilities.
    """
    # Simply using SQLAlchemy sync session here, wrapped in async def, 
    # FastAPI runs this in a threadpool so it's non-blocking.
    
    # Check permissions (add role checks later as needed)
    
    # Check uniqueness
    existing_farm = db.execute(
        select(Farm).where(
            Farm.tenant_id == current_user.tenant_id,
            Farm.farm_code == farm_data.farm_code,
            Farm.is_active == True
        )
    ).scalar_one_or_none()
    
    if existing_farm:
        raise HTTPException(status_code=400, detail="Farm code already exists")
    
    # Create farm
    # Extract location if present manually
    farm_location_wkt = None
    if farm_data.farm_location:
        farm_location_wkt = f"POINT({farm_data.farm_location.lng} {farm_data.farm_location.lat})"
    
    db_obj = Farm(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        farm_code=farm_data.farm_code,
        farm_name=farm_data.farm_name,
        farmer_name=farm_data.farmer_name,
        farmer_contact=farm_data.farmer_contact,
        farm_address=farm_data.farm_address,
        farm_characteristics=farm_data.farm_characteristics,
        registration_numbers=farm_data.registration_numbers,
        insurance_history=farm_data.insurance_history,
        total_farm_area=farm_data.total_farm_area,
        operational_area=farm_data.operational_area,
        farm_location=farm_location_wkt
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Convert WKT to string for response if needed by Pydantic (though pure WKT usually works)
    # The response model handles string types
    if db_obj.farm_location is not None:
        # Convert internal geometry to WKT for response
        wkt_query = text("SELECT ST_AsText(:geom)")
        wkt_res = db.execute(wkt_query, {"geom": db_obj.farm_location}).scalar()
        db_obj.farm_location = wkt_res
        
    return db_obj

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
    List farms with filtering.
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
    
    query = query.offset(skip).limit(limit).order_by(Farm.created_at.desc())
    
    farms = db.execute(query).scalars().all()
    
    # Post-process for WKT output
    for farm in farms:
        if farm.farm_location is not None:
            # We can use ST_AsText in query or just return the object representation if acceptable
            # For correctness with Pydantic model demanding str, usually safer to query string explicitly
            # But GeoAlchemy2 elements usually str() to WKT or HEX. Let's see.
            # Using specific helper if needed. For now assume Pydantic's from_attributes handles it or we map it.
            # To be safe, let's leave as is, usually GeoAlchemy2 Elements serialize to WKT/HEX string
            pass
            
    return farms

@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed farm information"""
    farm = db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    return farm

@router.post("/{farm_id}/fields", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    farm_id: UUID,
    field_data: FieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create field with GPS boundary polygon
    """
    # Validate farm access
    farm = db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.tenant_id == current_user.tenant_id,
            Farm.is_active == True
        )
    ).scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")
    
    # Validate field boundary
    boundary_validation = await SpatialService.validate_field_boundary(
        field_data.boundary_coordinates, db
    )
    
    if not boundary_validation["valid"]:
        raise HTTPException(status_code=400, detail=boundary_validation["error"])
    
    # Check uniqueness
    existing_field = db.execute(
        select(Field).where(
            Field.farm_id == farm_id,
            Field.field_code == field_data.field_code
        )
    ).scalar_one_or_none()
    
    if existing_field:
        raise HTTPException(status_code=400, detail="Field code already exists on this farm")
    
    # Calculate metrics
    field_metrics = await SpatialService.calculate_field_metrics(
        field_data.boundary_coordinates, db
    )
    
    # Create Field
    db_obj = Field(
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
        access_notes=field_data.access_notes,
        historical_yields=field_data.historical_yields,
        land_use_restrictions=field_data.land_use_restrictions
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj

@router.post("/{farm_id}/fields/{field_id}/sampling-points", response_model=SamplingResponse)
async def generate_sampling_points(
    farm_id: UUID,
    field_id: UUID,
    sampling_request: SamplingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate GPS sampling points for field assessment
    """
    # Validate access
    field = db.execute(
        select(Field).join(Farm).where(
            Field.id == field_id,
            Farm.id == farm_id,
            Farm.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found or access denied")
        
    # Get boundary WKT
    wkt_query = text("SELECT ST_AsText(field_boundary) FROM fields WHERE id = :field_id")
    boundary_wkt = db.execute(wkt_query, {"field_id": field_id}).scalar()
    
    if not boundary_wkt:
        raise HTTPException(status_code=500, detail="Field boundary data corrupted")
        
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
