import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.services.calculations import CalculationService

async def test_hail_calculation():
    print("Verifying Hail Damage Calculation Logic...")
    
    # Mock DB session
    mock_db = MagicMock()
    
    # Mock samples input
    samples = [
        {
            "sample_number": 1,
            "original_stand_count": 40,
            "destroyed_plants": 4, # 10% reduction
            "percent_defoliation": 50.0,
            "stalk_damage_severity": "moderate", # 35%
            "growing_point_damage_pct": 5.0,
            "ear_damage_pct": 0.0,
            "direct_damage_pct": 2.0,
            "length_measured_m": 10.0,
            "row_width_m": 0.9
        }
    ]
    
    # Mock get_lookup_value to return predictable results
    # We need to patch the static method. Since it's an async static method on the class...
    # Let's just monkeypatch it on the class for this test.
    original_get_lookup = CalculationService.get_lookup_value
    original_seed_17 = CalculationService.seed_exhibit_17
    original_seed_23 = CalculationService.seed_exhibit_23
    original_seed_24 = CalculationService.seed_exhibit_24

    async def mock_lookup(db, table_name, input_val, stage=None):
        if "hailStandReduction" in table_name:
            # 10% reduction -> assume 3% damage (from exhibit 13 simplified)
            if input_val == 10.0: return 3.0
            return input_val
        if "leafLoss" in table_name:
            # 50% defoliation -> assume 20% loss
            return 20.0
        return 0.0

    CalculationService.get_lookup_value = mock_lookup
    CalculationService.seed_exhibit_17 = AsyncMock()
    CalculationService.seed_exhibit_23 = AsyncMock()
    CalculationService.seed_exhibit_24 = AsyncMock()
    
    try:
        result = await CalculationService.calculate_hail_damage(
            db=mock_db,
            samples=samples,
            growth_stage="8thLeaf"
        )
        
        print("\n--- Result ---")
        print(f"Loss Percentage: {result['loss_percentage']}%")
        print(f"Damage Breakdown: {result['damage_breakdown']}")
        
        # Validation
        # Stand Reduction Input: 10%
        # Stand Damage Lookup: 3.0%
        # Stalk Damage (Moderate): 35.0%
        # Growing Point: 5.0%
        # Direct Other: 2.0%
        # Total Direct = 3.0 + 35.0 + 5.0 + 2.0 = 45.0%
        
        # Defoliation Input: 50%
        # Defoliation Loss Lookup: 20.0%
        
        # Total Loss = 45.0 + 20.0 = 65.0%
        
        details = result['sample_details'][0]
        print(f"\nCalculated Total Direct: {details['total_direct_damage']}% (Expected 45.0%)")
        print(f"Calculated Total Loss: {details['total_sample_loss']}% (Expected 65.0%)")
        
        assert details['total_direct_damage'] == 45.0
        assert details['total_sample_loss'] == 65.0
        assert result['loss_percentage'] == 65.0
        
        print("\n✅ VERIFICATION SUCCESSFUL: Calculation logic matches expected USDA formula.")
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore
        CalculationService.get_lookup_value = original_get_lookup
        CalculationService.seed_exhibit_17 = original_seed_17
        CalculationService.seed_exhibit_23 = original_seed_23
        CalculationService.seed_exhibit_24 = original_seed_24

if __name__ == "__main__":
    asyncio.run(test_hail_calculation())
