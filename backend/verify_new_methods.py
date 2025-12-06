import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.services.calculations import CalculationService

async def test_new_methods():
    print("Verifying New Calculation Methods...")
    
    # Mock DB
    mock_db = MagicMock()
    
    # --- Test 1: Maturity Line ---
    print("\n1. Testing Maturity Line Method (R5 Dent)...")
    samples_mat = [{
        "sample_number": 1,
        "weight_lbs": 0.5, # Weight of sample
        "sample_area_acres": 0.001,
        "maturity_line_position": 50.0 # 50% down
    }]
    
    # Logic in service:
    # R5, 50% line -> Dev Factor = 0.75 + (0.5 * 0.25) = 0.875
    # Projected Weight = 0.5 / 0.875 = 0.5714 lbs
    # Shelled (0.8) = 0.4571 lbs
    # Bu = 0.4571 / 56 = 0.00816
    # Per Acre = 0.00816 / 0.001 = 8.16 bu/acre
    
    res_mat = await CalculationService.calculate_maturity_line_weight(
        db=mock_db, samples=samples_mat, growth_stage="R5"
    )
    print(f"Projected Yield: {res_mat['projected_yield_bu_acre']} bu/acre")
    print(f"Dev Factor Pct: {res_mat['current_development_pct']}%")
    
    assert 8.0 < res_mat['projected_yield_bu_acre'] < 8.3
    
    # --- Test 2: Tonnage Method ---
    print("\n2. Testing Tonnage Method...")
    samples_ton = [{
        "sample_number": 1,
        "fresh_weight_lbs": 20.0,
        "sample_area_acres": 0.001
    }]
    
    # Mock Exhibit 21
    original_get = CalculationService.get_lookup_value
    CalculationService.seed_exhibit_21 = AsyncMock()
    
    async def mock_lookup(db, table, val, stage):
        if "silage" in table:
            if val == 70.0: return 0.9
        return 1.0
    CalculationService.get_lookup_value = mock_lookup
    
    # Input: 70% Moisture, Good Quality (Manual)
    # Factor (70%) = 0.9
    # Quality (Good) = 0.95
    # Fresh Tons = (20 / 2000) / 0.001 = 10.0 tons/acre
    # Adjusted = 10.0 * 0.9 * 0.95 = 8.55 tons/acre
    
    res_ton = await CalculationService.calculate_tonnage_method(
        db=mock_db, samples=samples_ton, moisture_pct=70.0, quality_grade="good"
    )
    
    print(f"Tons/Acre (Adj): {res_ton['tons_per_acre']}")
    print(f"Quality Grade: {res_ton['quality_grade']}")
    
    assert 8.5 <= res_ton['tons_per_acre'] <= 8.6
    assert res_ton['quality_grade'] == "good"
    
    print("\n✅ VERIFICATION SUCCESSFUL: New methods logic verified.")
    CalculationService.get_lookup_value = original_get

if __name__ == "__main__":
    asyncio.run(test_new_methods())
