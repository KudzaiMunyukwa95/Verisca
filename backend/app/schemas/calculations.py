from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SampleMeasurement(BaseModel):
    sample_number: int
    surviving_plants: Optional[int] = None # For Stand Reduction (Drought)
    
    # For Hail
    original_stand_count: Optional[int] = None
    destroyed_plants: Optional[int] = None
    percent_defoliation: Optional[float] = None
    direct_damage_pct: Optional[float] = None
    
    # For Weight Method
    weight_lbs: Optional[float] = None
    sample_area_acres: Optional[float] = 0.01

    length_measured_m: float = 10.0
    row_width_m: float = 0.9

class CalculationRequest(BaseModel):
    growth_stage: str
    normal_plant_population: int = 40000
    samples: List[SampleMeasurement]
    
    # Optional global parameters for Weight Method
    moisture_pct: Optional[float] = None
    test_weight: Optional[float] = None

class CalculationResult(BaseModel):
    method: str
    growth_stage: str
    loss_percentage: float
    average_potential_yield_pct: float
    sample_details: List[Dict[str, Any]]
