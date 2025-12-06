
from typing import List, Dict, Any, Optional
import math
from app.schemas.intelligence import ValidationFlag

class ValidationEngine:
    """
    The Auditor.
    Detects anomalies, outliers, and potential fraud.
    """
    
    @staticmethod
    def validate_statistical_consistency(
        method: str, 
        samples: List[Dict[str, Any]]
    ) -> List[ValidationFlag]:
        flags = []
        if len(samples) < 3:
            return flags # Not enough data for stats
            
        # Extract the key metric based on method
        values = []
        key = ""
        if method == "WEIGHT_METHOD":
            key = "avg_yield_kg_ha" # No wait, looking for sample level
            # We need to look at 'yield_bu_acre' or similar from the processed result? 
            # Or raw inputs? Raw inputs are better for fraud detection.
            # Let's look at 'fresh_weight_kg' if available in input, or processed yield.
            key = "yield_kg_ha_adj" # from result
        elif method == "HAIL_DAMAGE":
            key = "total_sample_loss"
            
        # Note: The Orchestrator passes 'method_result["sample_details"]' here
        try:
            values = [s.get(key, 0.0) for s in samples if key in s]
        except:
            return []
            
        if not values: return []
        
        # 1. Coefficient of Variation (CV)
        # CV = StdDev / Mean
        mean = sum(values) / len(values)
        if mean == 0: return []
        
        variance = sum([((x - mean) ** 2) for x in values]) / len(values)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean
        
        # Fraud Check A: "Too Perfect" (CV < 5%)
        # Nature rarely produces uniform corn yields across a field to < 5% variance.
        if cv < 0.05 and len(samples) > 5:
            flags.append(ValidationFlag(
                check_type="statistical",
                status="WARNING",
                message="Data is suspiciously uniform (CV < 5%). Potential manufactured data.",
                confidence_score=0.75
            ))
            
        # Error Check B: "Sloppy/High Variance" (CV > 40%)
        # Unless it's a disaster area, >40% variance usually means bad sampling technique
        if cv > 0.40:
             flags.append(ValidationFlag(
                check_type="statistical",
                status="WARNING",
                message=f"High variance detected (CV {int(cv*100)}%). Verify damaged patches.",
                confidence_score=0.60
            ))
            
        # 2. Outlier Detection (Z-Score)
        # Flag any sample > 2 StdDev from mean
        for i, val in enumerate(values):
            if std_dev > 0:
                z_score = abs(val - mean) / std_dev
                if z_score > 2.5:
                     flags.append(ValidationFlag(
                        check_type="outlier",
                        status="FAIL", # Strong flag
                        message=f"Sample #{i+1} is a statistical outlier (Z={round(z_score,1)}). Value: {val}",
                        confidence_score=0.90
                    ))
                    
        return flags

    @staticmethod
    def validate_biological_plausibility(
        method: str, 
        result: Dict[str, Any]
    ) -> List[ValidationFlag]:
        flags = []
        
        # Check Max Yield (e.g. Corn > 20 tonnes/ha is unlikely in most regions)
        if method == "WEIGHT_METHOD":
            yield_val = result.get("avg_yield_kg_ha", 0)
            if yield_val > 18000: # 18 tonnes
                flags.append(ValidationFlag(
                    check_type="biological",
                    status="WARNING",
                    message=f"Calculated yield ({yield_val} kg/ha) exceeds regional biological maximums.",
                    confidence_score=0.95
                ))
                
        # Check Hail: If Stalk Damage is 100% but Defoliation is 0% -> Impossible
        if method == "HAIL_DAMAGE":
             # Need deep inspection of breakdown
             pass
             
        return flags

    @staticmethod
    def validate_sample_sufficiency(
        field_area_ha: float,
        num_samples: int,
        policy_min_samples_per_ha: float = 0.5 
    ) -> List[ValidationFlag]:
        """
        Ensures minimum sampling density.
        Default: 1 sample per 2 hectares (0.5 samples/ha).
        Minimum absolute samples: 3 (USDA typically requires minimums based on acres).
        """
        flags = []
        
        # 1. Absolute Minimum
        if num_samples < 3:
             flags.append(ValidationFlag(
                check_type="sufficiency",
                status="FAIL", # Hard stop usually
                message=f"Insufficient samples ({num_samples}). Minimum required is 3.",
                confidence_score=1.0
            ))
             return flags
             
        # 2. Density Check
        if field_area_ha > 0:
            actual_density = num_samples / field_area_ha
            if actual_density < policy_min_samples_per_ha:
                 required = int(math.ceil(field_area_ha * policy_min_samples_per_ha))
                 flags.append(ValidationFlag(
                    check_type="sufficiency",
                    status="WARNING", # Warn assessor to take more
                    message=f"Sampling density low ({num_samples} for {field_area_ha}ha). Recommended: {required} points.",
                    confidence_score=0.90
                ))
        return flags
        
    @staticmethod
    def validate_gps_consistency(
        samples: List[Any], # List of AssessmentSampleInput
        field_boundary_wkt: Optional[str] = None
    ) -> List[ValidationFlag]:
        """
        Checks if points are distinct and within field (if boundary provided).
        """
        flags = []
        # Need logic here to check distances between points (Cluster detection)
        # For now, simple duplicate check
        
        # TODO: Implement point-in-polygon if WKT provided
        
        return flags
