
from typing import Dict, Any, Optional
from app.schemas.intelligence import HarvestRecommendation, MarketData

class EconomicStrategyEngine:
    """
    The Financial Analyst.
    Compares outcome scenarios.
    """
    
    @staticmethod
    def compare_grain_vs_silage(
        yield_kg_ha: float,
        silage_tonnes_ha: float,
        market: MarketData
    ) -> HarvestRecommendation:
        """
        Compare Grain Harvest vs Silage Conversion.
        """
        if not market or not market.silage_price_per_tonne:
            return None
            
        # Option A: Grain
        # Revenue = Yield (tonnes) * Price
        grain_tonnes = yield_kg_ha / 1000.0
        grain_revenue = grain_tonnes * market.grain_price_per_tonne
        # Costs (simplified)
        grain_net = grain_revenue - (market.harvest_cost_per_ha or 0)
        
        # Option B: Silage
        silage_revenue = silage_tonnes_ha * market.silage_price_per_tonne
        # Silage often has higher harvest cost (chopping)
        silage_cost = (market.harvest_cost_per_ha or 0) * 1.5 # Assumption if not provided
        silage_net = silage_revenue - silage_cost
        
        diff = silage_net - grain_net
        
        if diff > 0:
            return HarvestRecommendation(
                recommended_strategy="HARVEST_SILAGE",
                financial_gain_estimate=round(diff, 2),
                rationale=f"Silage value exceeds grain by ${round(diff,2)}/ha due to quality/price spread."
            )
        else:
             return HarvestRecommendation(
                recommended_strategy="HARVEST_GRAIN",
                financial_gain_estimate=round(abs(diff), 2),
                rationale=f"Grain harvest retains ${round(abs(diff),2)}/ha higher value."
            )
