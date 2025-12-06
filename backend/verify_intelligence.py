
import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock
from datetime import date

# Mock dependencies before import
sys.modules['app.db.session'] = MagicMock()
sys.modules['app.services.calculations'] = MagicMock()

# Import the code to test
from app.services.orchestrator import AssessmentOrchestrator
from app.services.calculations import CalculationService
from app.schemas.intelligence import (
    ComprehensiveAssessmentRequest, PerilType, GrowthStage, 
    MarketData, FieldContext, AssessmentSampleInput
)

async def test_intelligence():
    print("🧠 Verifying Verisca Intelligence Engine...")
    
    # Setup Mocks
    db = MagicMock()
    
    # Simuluate SERVICE result for Weight Method
    CalculationService.calculate_weight_method = AsyncMock()
    # Assume 4000 kg/ha grain yield
    CalculationService.calculate_weight_method.return_value = {
        "avg_yield_kg_ha": 4000.0,
        "sample_details": [
            {"yield_kg_ha_adj": 4000.0}, 
            {"yield_kg_ha_adj": 3950.0},
            {"yield_kg_ha_adj": 4050.0},
            {"yield_kg_ha_adj": 4000.0}, 
            {"yield_kg_ha_adj": 4000.0},
            {"yield_kg_ha_adj": 4000.0} # Very uniform -> Should trigger Fraud Warning
        ]
    }
    
    # Simulate SERVICE result for Tonnage Method
    CalculationService.calculate_tonnage_method = AsyncMock()
    # Assume 30 tonnes/ha silage
    CalculationService.calculate_tonnage_method.return_value = {
        "tonnes_per_ha": 30.0
    }
    
    # Build Request: Scenario Beta (Grain vs Silage)
    # Grain Price: $300/t. Yield 4t = $1200
    # Silage Price: $50/t. Yield 30t = $1500
    # Expected: Silage Recommendation
    
    req = ComprehensiveAssessmentRequest(
        primary_peril=PerilType.DROUGHT, # Late season stress
        growth_stage=GrowthStage.R5,
        measurement_date=date.today(),
        field_context=FieldContext(field_size_ha=10.0),
        market_data=MarketData(
            grain_price_per_tonne=300.0,
            silage_price_per_tonne=50.0
        ),
        samples=[
            AssessmentSampleInput(sample_number=i, weights={"fresh_weight": 5.0}) for i in range(1,7)
        ]
    )
    
    # Run Orchestrator
    result = await AssessmentOrchestrator.perform_comprehensive_assessment(db, req)
    
    print(f"\nMethod Selected: {result.primary_method_used}")
    assert result.primary_method_used == "WEIGHT_METHOD"
    
    print(f"Calculated Grain Yield: {result.calculated_yield_kg_ha} kg/ha")
    
    # Check Validation Flags
    print("\nValidation Flags:")
    hit_fraud_warning = False
    for flag in result.validation_flags:
        print(f" - [{flag.status}] {flag.message}")
        if "CV < 5%" in flag.message: hit_fraud_warning = True
            
    # Note: Using mock uniform data, CV should be very low.
    # Logic in validation: cv < 0.05 and len > 5 -> Warning
    # 4000 vs 3950... variance is tiny. Should trigger.
    
    # Check Economic Rec
    if result.economic_recommendation:
        rec = result.economic_recommendation
        print(f"\nEconomic Recommendation: {rec.recommended_strategy}")
        print(f"Rationale: {rec.rationale}")
        
        # 1200 vs 1500 (gross). 
        # Logic in economics: Silage Net vs Grain Net.
        # Grain Net = 1200. Silage Net = 1500. Diff 300.
        # Costs default to 0 in this test input.
        assert rec.recommended_strategy == "HARVEST_SILAGE"
        
    print("\n✅ Intelligence Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_intelligence())
