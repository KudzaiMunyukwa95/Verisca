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
    sample_dicts = [sample.dict(exclude_unset=True) for sample in request.samples]
    
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
    sample_dicts = [sample.dict(exclude_unset=True) for sample in request.samples]
    
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
