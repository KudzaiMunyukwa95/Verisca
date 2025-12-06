from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.services.calculations import CalculationService
from app.schemas.calculations import CalculationRequest, CalculationResult

from app.models.lookup import LookupTable
from sqlalchemy import select
from pydantic import BaseModel

router = APIRouter()

# ... import existing ...

@router.get("/lookup-tables", response_model=List[dict])
async def get_all_lookup_tables(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Download all lookup tables for offline caching.
    """
    tables = db.execute(select(LookupTable)).scalars().all()
    
    # Return a simplified structure or the raw model
    return [
        {
            "id": str(t.id),
            "table_name": t.table_name,
            "input_value": t.input_value,
            "stage_or_condition": t.stage_or_condition,
            "output_value": t.output_value,
            "updated_at": t.updated_at
        }
        for t in tables
    ]

@router.post("/stand-reduction", response_model=CalculationResult)
async def calculate_stand_reduction(
    request: CalculationRequest,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Optional: require auth
):
    """
    Perform on-the-fly Stand Reduction calculation.
    """
    # Convert Pydantic models to dicts for service
    sample_dicts = [sample.model_dump() for sample in request.samples]
    
    try:
        result = await CalculationService.calculate_stand_reduction(
            db=db,
            samples=sample_dicts,
            growth_stage=request.growth_stage,
            normal_plant_population_per_ha=request.normal_plant_population
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/hail-damage", response_model=CalculationResult)
async def calculate_hail_damage(
    request: CalculationRequest,
    db: Session = Depends(get_db),
):
    """
    Perform on-the-fly Hail Damage calculation (Exhibits 13, 14, 15).
    """
    sample_dicts = [sample.model_dump(exclude_unset=True) for sample in request.samples]
    
    try:
        result = await CalculationService.calculate_hail_damage(
            db=db,
            samples=sample_dicts,
            growth_stage=request.growth_stage,
            normal_plant_population_per_ha=request.normal_plant_population
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/weight-method", response_model=CalculationResult)
async def calculate_weight_method(
    request: CalculationRequest,
    db: Session = Depends(get_db),
):
    """
    Perform on-the-fly Weight Method Appraisal (Exhibit 17 + Quality).
    """
    sample_dicts = [sample.model_dump(exclude_unset=True) for sample in request.samples]
    
    try:
        result = await CalculationService.calculate_weight_method(
            db=db,
            samples=sample_dicts,
            # Pass fields if relevant or default
            moisture_pct=request.moisture_pct,
            test_weight_kg_hl=request.test_weight_kg_hl
        )
        
        # Mapping Metric Result
        result["average_potential_yield_pct"] = result["avg_yield_kg_ha"] 
        result["loss_percentage"] = 0.0 
        result["growth_stage"] = "Mature"
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/maturity-line-weight", response_model=CalculationResult)
async def calculate_maturity_line_weight(
    request: CalculationRequest,
    db: Session = Depends(get_db),
):
    """
    Perform on-the-fly Maturity Line Weight calculation (R3-R5).
    """
    sample_dicts = [sample.model_dump(exclude_unset=True) for sample in request.samples]
    
    try:
        result = await CalculationService.calculate_maturity_line_weight(
            db=db,
            samples=sample_dicts,
            growth_stage=request.growth_stage,
            expected_final_moisture=request.expected_final_moisture
        )
        
        # Adaptation for MVP Schema
        result["average_potential_yield_pct"] = result["projected_yield_bu_acre"]
        result["loss_percentage"] = 0.0 # Yield projection
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tonnage-method", response_model=CalculationResult)
async def calculate_tonnage_method(
    request: CalculationRequest,
    db: Session = Depends(get_db),
):
    """
    Perform on-the-fly Tonnage Method calculation (Silage).
    """
    sample_dicts = [sample.model_dump(exclude_unset=True) for sample in request.samples]
    
    try:
        # Check if quality grade provided in first sample or request level?
        # Our schema puts quality_grade in SampleMeasurement for simplicity,
        # but typically it's a field level or sample level thing.
        # Let's check first sample for field-level defaults if needed, 
        # or typical usage is sample-specific in the loop.
        
        # However, the calculate_tonnage_method signature expects single global quality inputs
        # derived from request or samples. 
        # Let's extract from the first sample or add to request?
        # The service method signature: calculate_tonnage_method(..., moisture_pct, visual_damage_pct, quality_grade)
        # We need to extract these.
        
        # Assuming moisture_pct is global in request
        moisture = request.moisture_pct if request.moisture_pct else 65.0
        
        # Extract quality grade from first sample as default if exists
        q_grade = None
        if sample_dicts and 'quality_grade' in sample_dicts[0]:
            q_grade = sample_dicts[0]['quality_grade']
            
        result = await CalculationService.calculate_tonnage_method(
            db=db,
            samples=sample_dicts,
            moisture_pct=moisture,
            quality_grade=q_grade
        )
        
        # Adaptation for MVP Schema
        result["loss_percentage"] = 0.0
        result["average_potential_yield_pct"] = result["tonnes_per_ha"] 
        result["growth_stage"] = request.growth_stage
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from app.schemas.calculations import ReplantingRequest, ReplantingResult, StageModRequest, StageModResult

@router.post("/replanting-analysis", response_model=ReplantingResult)
async def analyze_replanting_decision(
    request: ReplantingRequest,
    # db: Session = Depends(get_db) # Not strictly needed if no lookup
):
    """
    Financial analysis for Replant vs. Keep decision (USDA Part 3).
    """
    try:
        result = await CalculationService.calculate_replanting_analysis(
            normal_yield_kg_ha=request.normal_yield_kg_ha,
            price_per_kg=request.price_per_kg,
            share=request.share_percent,
            stand_pct=request.surviving_stand_pct,
            replant_cost_per_ha=request.replanting_cost_per_ha,
            replant_factor=request.replanted_yield_factor
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stage-modification", response_model=StageModResult)
async def calculate_stage_modification(
    request: StageModRequest,
):
    """
    Adjusted growth stage for short-season varieties (Exhibit 16).
    """
    try:
        result = await CalculationService.calculate_stage_modification(
            days_from_planting=request.days_from_planting,
            maturity_days=request.maturity_days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/seed-tables", status_code=201)
async def seed_lookup_tables(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Initialize USDA lookup tables (Exhibit 11, etc.)
    """
    await CalculationService.seed_lookup_tables(db)
    await CalculationService.seed_lookup_tables(db)
    return {"message": "Lookup tables seeded successfully"}

class LookupUpdate(BaseModel):
    table_name: str
    input_value: float
    stage_or_condition: Optional[str] = None
    output_value: float

@router.patch("/admin/lookup-tables", status_code=status.HTTP_200_OK)
async def update_lookup_value(
    update_data: LookupUpdate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_admin_user) # TODO: Enforce Admin
):
    """
    Admin: Update specific lookup table value.
    This allows tweaking factors (e.g. Test Weight discounts) without redeploy.
    """
    # Find the specific entry
    query = select(LookupTable).where(
        LookupTable.table_name == update_data.table_name,
        # using float comparison with small epsilon if needed, but usually equality works for exact inputs
        LookupTable.input_value == update_data.input_value 
    )
    
    if update_data.stage_or_condition:
        query = query.where(LookupTable.stage_or_condition == update_data.stage_or_condition)
        
    entry = db.execute(query).scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Lookup entry not found")
        
    entry.output_value = update_data.output_value
    db.commit()
    
    return {"message": "Value updated", "new_value": entry.output_value}
