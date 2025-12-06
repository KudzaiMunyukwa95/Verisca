from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.services.calculations import CalculationService
from app.schemas.calculations import CalculationRequest, CalculationResult

from app.models.lookup import LookupTable
from sqlalchemy import select

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
            test_weight=request.test_weight
        )
        # Hack: map result keys to CalculationResult schema loosely
        # The schema expects 'loss_percentage' and 'average_potential_yield_pct'
        # But Weight Method returns 'avg_yield_bu_acre'.
        # We might need to adjust the response schema or result dict.
        # For now, let's map 'average_potential_yield_pct' to yield
        # and 'loss_percentage' to 0 (since it's an appraisal of what IS there, not what is lost)
        
        # Proper solution: Update schema or use separate schema.
        # Quick fix for MVP:
        result["average_potential_yield_pct"] = result["avg_yield_bu_acre"] 
        result["loss_percentage"] = 0.0 # Not a loss calculation, it's a yield appraisal
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
        result["average_potential_yield_pct"] = result["tons_per_acre"] # Mapping tons to yield field
        result["growth_stage"] = request.growth_stage
        
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
    return {"message": "Lookup tables seeded successfully"}
