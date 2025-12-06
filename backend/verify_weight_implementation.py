import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.services.calculations import CalculationService

async def test_weight_method():
    print("Verifying Weight Method Calculation Logic...")
    
    # Mock DB session
    mock_db = MagicMock()
    
    # Mock samples input
    samples = [
        {
            "sample_number": 1,
            "weight_lbs": 10.0,
            "sample_area_acres": 0.01,
            "foreign_material_pct": 2.0,
            "damaged_kernels_pct": 3.0,
            "broken_kernels_pct": 1.0,
            "heat_damage_pct": 0.0
        }
    ]
    
    # Mock lookup
    original_get_lookup = CalculationService.get_lookup_value
    original_seed_17 = CalculationService.seed_exhibit_17
    original_seed_23 = CalculationService.seed_exhibit_23
    original_seed_24 = CalculationService.seed_exhibit_24

    async def mock_lookup(db, table_name, input_val, stage=None):
        if "moistureAdjustment" in table_name:
            # 20% moisture -> 0.9412
            if input_val == 20.0: return 0.9412
            return 1.0
        if "testWeightPack" in table_name:
            # 54 lbs -> 0.98
            if input_val == 54.0: return 0.98
            return 1.0
        return 1.0

    CalculationService.get_lookup_value = mock_lookup
    CalculationService.seed_exhibit_17 = AsyncMock()
    CalculationService.seed_exhibit_23 = AsyncMock()
    CalculationService.seed_exhibit_24 = AsyncMock()
    
    try:
        # Test Case:
        # Weight: 10 lbs (Ear Corn)
        # Shelling: 0.8 (Default) -> 8.0 lbs shelled
        # Bushels: 8.0 / 56.0 = 0.142857 bu
        # Per Acre (0.01 sample): 14.2857 bu/acre raw
        
        # Adjustments:
        # Moisture (20%): 0.9412
        # Test Weight (54 lbs): 0.98
        # Adjusted Yield = 14.2857 * 0.9412 * 0.98 = 13.178 bu/acre
        
        # Deductions:
        # FM: 2%
        # Damaged: 3%
        # Broken: 1%
        # Total: 6% deduction
        # Final Yield = 13.178 * (1 - 0.06) = 12.387 bu/acre
        
        result = await CalculationService.calculate_weight_method(
            db=mock_db,
            samples=samples,
            moisture_pct=20.0,
            test_weight=54.0
        )
        
        print("\n--- Result ---")
        print(f"Avg Yield: {result['avg_yield_bu_acre']} bu/acre")
        print(f"Moisture Factor: {result['moisture_factor']}")
        print(f"Test Weight Factor: {result['test_weight_factor']}")
        
        details = result['sample_details'][0]
        quality = details['quality_adjustments']
        print(f"\nSample Raw Yield: {details['yield_bu_acre_raw']}")
        print(f"Sample Final Yield: {details['yield_bu_acre_adj']}")
        print(f"Deductions: FM={quality['foreign_material_deduction']}%, Dmg={quality['damaged_kernel_deduction']}%, Brk={quality['broken_kernel_deduction']}%")
        
        # Assertions (Approximate checks)
        assert 14.2 <= details['yield_bu_acre_raw'] <= 14.4
        assert 12.3 <= details['yield_bu_acre_adj'] <= 12.5
        assert result['avg_yield_bu_acre'] == details['yield_bu_acre_adj']
        
        print("\n✅ VERIFICATION SUCCESSFUL: Weight method logic matches expectations.")
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        CalculationService.get_lookup_value = original_get_lookup
        CalculationService.seed_exhibit_17 = original_seed_17
        CalculationService.seed_exhibit_23 = original_seed_23
        CalculationService.seed_exhibit_24 = original_seed_24

if __name__ == "__main__":
    asyncio.run(test_weight_method())
