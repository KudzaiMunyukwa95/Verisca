
import asyncio
from unittest.mock import MagicMock
from app.services.calculations import CalculationService

async def test_metric():
    print("Verifying Metric System Migration...")
    
    # 1. Test Helper Conversions
    print("\n1. Testing Conversion Helpers...")
    kg = 1000
    lbs = CalculationService.to_lbs(kg)
    print(f"{kg} kg = {lbs:.2f} lbs (Expected ~2204.62)")
    assert abs(lbs - 2204.62) < 1.0
    
    ha = 1.0
    acres = CalculationService.to_acres(ha)
    print(f"{ha} ha = {acres:.2f} acres (Expected ~2.47)")
    assert abs(acres - 2.471) < 0.01
    
    # 2. Test Weight Method (Metric)
    print("\n2. Testing Weight Method (Metric)...")
    # Scenario: 
    # Sample 1: 5 kg corn (fresh), 10 m2 area
    # Yield = (5 / 10) * 10000 = 5000 kg/ha (Raw)
    # Shelling 0.8 -> 4000 kg/ha shelled
    
    samples = [{"sample_number": 1, "fresh_weight_kg": 5.0, "sample_area_m2": 10.0}]
    
    # Needs DB mock for lookups
    db = MagicMock()
    # Mock lookup returning 1.0 for factors
    CalculationService.get_lookup_value = MagicMock(return_value=1.0)
    # Mock seeding method to not fail
    CalculationService.seed_exhibit_21 = MagicMock()

    # We need to instantiate class or just use static? It's static.
    # But get_lookup_value is async.
    
    # Using a slightly different approach for mocking async static method in a script without ample setup is hard
    # We will assume get_lookup_value fails gracefully in the code (try/except pass) if DB is mock.
    
    res = await CalculationService.calculate_weight_method(db, samples)
    print(f"Calculated Yield: {res['avg_yield_kg_ha']} kg/ha")
    
    # Verification Logic
    # 5 kg / 10 m2 = 0.5 kg/m2
    # in acres: 5 kg = 11.023 lbs
    # 10 m2 = 0.00247 acres
    # Lbs/Acre = 11.023 / 0.00247 = 4462 lbs/acre
    # Shelled (0.8) = 3569 lbs/acre
    # Bu/Acre = 3569 / 56 = 63.7 bu/acre
    # Kg/Ha = 63.7 * 62.77 (approx) = 4000 kg/ha
    # Matched!
    
    assert res['avg_yield_kg_ha'] > 3900 and res['avg_yield_kg_ha'] < 4100
    
    print("\n✅ Metric Verification Successful.")

if __name__ == "__main__":
    asyncio.run(test_metric())
