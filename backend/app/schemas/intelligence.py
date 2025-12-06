from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import date

# Import existing specific schemas if needed, or redefine for comprehensive wrapper
# For simplicity, we define the higher-level structures here

class PerilType(str, Enum):
    HAIL = "HAIL"
    DROUGHT = "DROUGHT"
    WIND = "WIND"
    DISEASE = "DISEASE"
    FROST = "FROST"
    FLOOD = "FLOOD"

class GrowthStage(str, Enum):
    EMERGENCE = "Emergence"
    VE_V2 = "VE-V2"
    V3_V5 = "V3-V5"
    V6_V8 = "V6-V8"
    V9_V12 = "V9-V12"
    VT = "VT" # Tassel
    R1 = "R1" # Silk
    R2 = "R2" # Blister
    R3 = "R3" # Milk
    R4 = "R4" # Dough
    R5 = "R5" # Dent
    MATURE = "Mature"

class MarketData(BaseModel):
    grain_price_per_tonne: float
    silage_price_per_tonne: Optional[float] = None
    harvest_cost_per_ha: Optional[float] = 0.0
    transport_cost_per_tonne: Optional[float] = 0.0
    drying_cost_per_tonne: Optional[float] = 0.0

class FieldContext(BaseModel):
    field_size_ha: float
    crop_variety: Optional[str] = None
    planting_date: Optional[date] = None
    expected_yield_kg_ha: Optional[float] = None # For comparison

class AssessmentSampleInput(BaseModel):
    sample_number: int
    # Flexible input: can contain counts, weights, damage %
    # The orchestrator will route these to the correct calculator
    counts: Optional[Dict[str, int]] = None # stand, destroyed
    weights: Optional[Dict[str, float]] = None # fresh_weight_kg
    damages: Optional[Dict[str, float]] = None # defoliation, ear_damage
    
class ComprehensiveAssessmentRequest(BaseModel):
    primary_peril: PerilType
    secondary_perils: List[PerilType] = []
    growth_stage: GrowthStage
    measurement_date: date
    
    field_context: FieldContext
    market_data: Optional[MarketData] = None
    
    samples: List[AssessmentSampleInput]
    
    # Global parameters
    moisture_pct: Optional[float] = None
    test_weight_kg_hl: Optional[float] = None

class ValidationFlag(BaseModel):
    check_type: str # 'statistical', 'biological', 'consistency'
    status: str # 'PASS', 'WARNING', 'FAIL'
    message: str
    confidence_score: float

class HarvestRecommendation(BaseModel):
    recommended_strategy: str # 'HARVEST_GRAIN', 'HARVEST_SILAGE', 'REPLANT', 'MAINTAIN'
    financial_gain_estimate: float
    rationale: str

class ComprehensiveAssessmentResult(BaseModel):
    assessment_id: str
    primary_method_used: str
    
    # Core Results
    calculated_loss_pct: float
    calculated_yield_kg_ha: float
    
    # Intelligence
    validation_flags: List[ValidationFlag]
    economic_recommendation: Optional[HarvestRecommendation] = None
    
    detailed_breakdown: Dict[str, Any]
