
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.intelligence import (
    ComprehensiveAssessmentRequest, 
    ComprehensiveAssessmentResult,
    PerilType, GrowthStage, ValidationFlag
)
from app.services.calculations import CalculationService

class AssessmentOrchestrator:
    """
    The Brain of Verisca.
    Orchestrates complex multi-method assessments.
    """
    
    @staticmethod
    async def perform_comprehensive_assessment(
        db: Session,
        request: ComprehensiveAssessmentRequest
    ) -> ComprehensiveAssessmentResult:
        
        # 1. Determine Method Strategy
        primary_method = AssessmentOrchestrator._determine_primary_method(
            request.primary_peril, 
            request.growth_stage
        )
        
        # 2. Map Inputs to generic calculator format
        # We need to convert the 'AssessmentSampleInput' list into the specific dict format 
        # expected by CalculationService (e.g. 'surviving_plants', 'weight_kg', etc)
        # This mapping depends on the method selected.
        
        sample_dicts = AssessmentOrchestrator._map_samples(request.samples, primary_method)
        
        # 3. Execute Primary Method
        method_result = {}
        
        if primary_method == "STAND_REDUCTION":
            # Early season
            method_result = await CalculationService.calculate_stand_reduction(
                db, sample_dicts, request.growth_stage.value
            )
        elif primary_method == "HAIL_DAMAGE":
            method_result = await CalculationService.calculate_hail_damage(
                db, sample_dicts, request.growth_stage.value
            )
        elif primary_method == "WEIGHT_METHOD":
            # Late season grain
            method_result = await CalculationService.calculate_weight_method(
                db, sample_dicts, 
                moisture_pct=request.moisture_pct,
                test_weight_kg_hl=request.test_weight_kg_hl
            )
        elif primary_method == "TONNAGE_METHOD":
            # Silage
            method_result = await CalculationService.calculate_tonnage_method(
                db, sample_dicts,
                moisture_pct=request.moisture_pct or 65.0
            )
        
        # 4. Economic Analysis
        from app.services.economics import EconomicStrategyEngine
        
        economic_rec = None
        if request.market_data and primary_method == "WEIGHT_METHOD":
             # If we did Grain, let's also estimate Silage for comparison (Scenario Beta)
             # Reuse samples but map to Tonnage input (fresh weight)
             # This assumes 'fresh_weight_kg' was available in samples
             silage_dicts = AssessmentOrchestrator._map_samples(request.samples, "TONNAGE_METHOD")
             silage_res = await CalculationService.calculate_tonnage_method(
                 db, silage_dicts, request.moisture_pct or 65.0
             )
             
             yield_kg = method_result.get("avg_yield_kg_ha", 0)
             tonnes_silage = silage_res.get("tonnes_per_ha", 0)
             
             economic_rec = EconomicStrategyEngine.compare_grain_vs_silage(
                 yield_kg, tonnes_silage, request.market_data
             )
        
        # 5. Validation
        from app.services.validation import ValidationEngine
        
        flags = []
        if "sample_details" in method_result:
            stats_flags = ValidationEngine.validate_statistical_consistency(primary_method, method_result["sample_details"])
            flags.extend(stats_flags)
            
        # Sufficiency Check (Step 7: Minimum points logic)
        # Using default field size 10ha if not mapped for MVP
        field_size = request.field_area_ha or 10.0
        suff_flags = ValidationEngine.validate_sample_sufficiency(field_size, len(request.samples))
        flags.extend(suff_flags)
            
        bio_flags = ValidationEngine.validate_biological_plausibility(primary_method, method_result)
        flags.extend(bio_flags)
        
        return ComprehensiveAssessmentResult(
            assessment_id=f"ASM-{datetime.now().strftime('%Y%m%d%H%M')}",
            primary_method_used=primary_method,
            calculated_loss_pct=method_result.get("loss_percentage", 0.0),
            calculated_yield_kg_ha=method_result.get("avg_yield_kg_ha", 0.0) or method_result.get("tonnes_per_ha", 0.0),
            validation_flags=flags,
            economic_recommendation=economic_rec,
            detailed_breakdown=method_result
        )

    @staticmethod
    def _determine_primary_method(peril: PerilType, stage: GrowthStage) -> str:
        """
        Intelligent Selection Logic
        """
        # Rule 1: Early season is usually Stand Reduction unless it's Hail
        early_stages = [GrowthStage.EMERGENCE, GrowthStage.VE_V2, GrowthStage.V3_V5, GrowthStage.V6_V8]
        if stage in early_stages:
            if peril == PerilType.HAIL:
                return "HAIL_DAMAGE" # Uses Ex 13
            return "STAND_REDUCTION" # Uses Ex 11
            
        # Rule 2: Middle season Hail
        mid_stages = [GrowthStage.V9_V12, GrowthStage.VT, GrowthStage.R1]
        if stage in mid_stages and peril == PerilType.HAIL:
            return "HAIL_DAMAGE" # Uses Ex 14 + Defoliation
            
        # Rule 3: Late season is usually Appraisal (Weight) if crop is there
        late_stages = [GrowthStage.R4, GrowthStage.R5, GrowthStage.MATURE]
        if stage in late_stages:
            # Check if we are appraising Silage or Grain? 
            # Default to Weight Method for Grain, but if Silage requested... 
            # The Peril doesn't strictly dictate this, usually User Intent does.
            # However, if Peril is "Drought" in late stage, looking for Quality/Yield -> Weight Method.
            return "WEIGHT_METHOD"
            
        # Fallback
        return "STAND_REDUCTION"

    @staticmethod
    def _map_samples(samples: List[Any], method: str) -> List[Dict[str, Any]]:
        mapped = []
        for s in samples:
            d = {"sample_number": s.sample_number}
            
            # Extract flexible dicts
            counts = s.counts or {}
            weights = s.weights or {}
            damages = s.damages or {}
            
            if method == "STAND_REDUCTION":
                d["surviving_plants"] = counts.get("surviving_plants", 0)
                d["length_measured_m"] = 10.0 # Default or pass in context
                
            elif method == "HAIL_DAMAGE":
                d["original_stand_count"] = counts.get("original_stand", 40)
                d["destroyed_plants"] = counts.get("destroyed", 0)
                d["percent_defoliation"] = damages.get("defoliation", 0.0)
                d["stalk_damage_severity"] = "none" # simplified mapping needed
                
            elif method == "WEIGHT_METHOD":
                d["fresh_weight_kg"] = weights.get("fresh_weight", 0.0)
                d["sample_area_m2"] = 10.0 # Default
                d["foreign_material_pct"] = damages.get("foreign_material", 0.0)
                
            mapped.append(d)
        return mapped
