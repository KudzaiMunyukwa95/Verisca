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
    # Enhanced Hail support
    stalk_damage_severity: Optional[str] = None  # none/light/moderate/severe
    growing_point_damage_pct: Optional[float] = None
    ear_damage_pct: Optional[float] = None
    
    # For Weight Method
    weight_lbs: Optional[float] = None
    sample_area_acres: Optional[float] = 0.01
    # Enhanced Weight Method Quality
    foreign_material_pct: Optional[float] = None
    damaged_kernels_pct: Optional[float] = None
    broken_kernels_pct: Optional[float] = None
    heat_damage_pct: Optional[float] = None

    # For Maturity Line Weight
    maturity_line_position: Optional[float] = None  # 0-100% down kernel
    kernel_moisture_pct: Optional[float] = None

    # For Tonnage Method
    fresh_weight_lbs: Optional[float] = None
    quality_grade: Optional[str] = None  # excellent/good/fair/poor

    length_measured_m: float = 10.0
    row_width_m: float = 0.9

class CalculationRequest(BaseModel):
    growth_stage: str
    normal_plant_population: int = 40000
    samples: List[SampleMeasurement]
    
    # Optional global parameters for Weight Method
    moisture_pct: Optional[float] = None
    test_weight: Optional[float] = None
    
    # Optional global parameters for new methods
    expected_final_moisture: Optional[float] = 15.0

class CalculationResult(BaseModel):
    method: str
    growth_stage: str
    loss_percentage: float
    average_potential_yield_pct: float
    sample_details: List[Dict[str, Any]]
