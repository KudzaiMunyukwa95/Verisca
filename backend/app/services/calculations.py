from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, asc
from typing import List, Dict, Any, Optional, Tuple
import math

from app.models.lookup import LookupTable

class CalculationService:
    """
    USDA Maize Loss Adjustment Calculation Engine.
    Implements verification logic and valid calculations.
    """
    
    @staticmethod
    async def get_lookup_value(
        db: Session, 
        table_name: str, 
        input_value: float, 
        stage_column: Optional[str] = None
    ) -> float:
        """
        Retrieves a value from a lookup table with Linear Interpolation.
        Formula: y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
        """
        # Try exact match first
        exact_query = select(LookupTable).where(
            LookupTable.table_name == table_name,
            LookupTable.input_value == input_value
        )
        if stage_column:
            exact_query = exact_query.where(LookupTable.stage_or_condition == stage_column)
            
        exact_match = db.execute(exact_query).scalar_one_or_none()
        if exact_match:
            return exact_match.output_value
            
        # If no exact match, find upper and lower bounds for interpolation
        # Lower bound (closest value <= input)
        lower_query = select(LookupTable).where(
            LookupTable.table_name == table_name,
            LookupTable.input_value <= input_value
        )
        if stage_column:
            lower_query = lower_query.where(LookupTable.stage_or_condition == stage_column)
        lower_query = lower_query.order_by(desc(LookupTable.input_value)).limit(1)
        lower_bound = db.execute(lower_query).scalar_one_or_none()
        
        # Upper bound (closest value >= input)
        upper_query = select(LookupTable).where(
            LookupTable.table_name == table_name,
            LookupTable.input_value >= input_value
        )
        if stage_column:
            upper_query = upper_query.where(LookupTable.stage_or_condition == stage_column)
        upper_query = upper_query.order_by(asc(LookupTable.input_value)).limit(1)
        upper_bound = db.execute(upper_query).scalar_one_or_none()
        
        if not lower_bound or not upper_bound:
            raise ValueError(f"Value {input_value} out of range for table {table_name}")
            
        if lower_bound.id == upper_bound.id:
            return lower_bound.output_value
            
        # Perform Linear Interpolation
        x = input_value
        x1 = lower_bound.input_value
        x2 = upper_bound.input_value
        y1 = lower_bound.output_value
        y2 = upper_bound.output_value
        
        # Avoid division by zero
        if x2 == x1:
            return y1
            
        y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
        return round(y, 2)

    @staticmethod
    async def calculate_stand_reduction(
        db: Session,
        samples: List[Dict[str, Any]],
        growth_stage: str,
        normal_plant_population_per_ha: int = 40000 
    ) -> Dict[str, Any]:
        """
        Calculates Stand Reduction based on USDA Exhibit 11/12 logic.
        
        Args:
            samples: List of sample dicts containing 'surviving_plants', 'length_measured_m', 'row_width_m'
            growth_stage: e.g., '7thLeaf', '10thLeaf'
            normal_plant_population_per_ha: Expected population (usually 40k-60k for maize)
            
        Returns:
            Dict containing detailed calculation results and final percentage loss.
        """
        processed_samples = []
        total_potential_pct = 0
        
        # Determine applicable table based on growth stage
        # USDA Simplified Logic:
        # Emergence - 10th Leaf: Exhibit 11
        # 11th Leaf - Tassel: Exhibit 12
        table_name = "exhibit11_standReduction"
        late_stages = ["11thLeaf", "12thLeaf", "13thLeaf", "14thLeaf", "15thLeaf", "16thLeaf", "tasseled"]
        
        if growth_stage in late_stages:
            table_name = "exhibit12_standReduction"
            
        # Also need to handle "Silked" and later -> Direct 1-to-1 calculation
        is_mature = growth_stage in ["silked", "blister", "milk", "dough", "dent", "mature"]
            
        for sample in samples:
            # 1. Calculate Field Plant Population (Plants/Ha) for this sample
            # Formula: (Count / (Row Length * Row Width)) * 10000 m2/ha
            row_len = float(sample.get('length_measured_m', 10.0))
            row_width = float(sample.get('row_width_m', 0.9)) # Default 90cm
            surviving = int(sample.get('surviving_plants', 0))
            
            sample_area_m2 = row_len * row_width
            current_pop_per_ha = (surviving / sample_area_m2) * 10000
            
            # 2. Calculate Percent Stand Remaining
            percent_stand = (current_pop_per_ha / normal_plant_population_per_ha) * 100
            percent_stand = min(100.0, max(0.0, percent_stand)) # Cap at 0-100
            
            # USDA Rounding: Nearest whole percent or tenths depends on chart. 
            # Exhibit 11 uses 5% increments originally, but we interpolate.
            
            # 3. Lookup Percent Potential Yield Remaining
            if is_mature:
                # Late stage: If 80% stand remains, potential is 80% (Direct relationship)
                percent_potential = percent_stand
            else:
                try:
                    percent_potential = await CalculationService.get_lookup_value(
                        db, table_name, percent_stand, growth_stage
                    )
                except ValueError as e:
                    # Fallback or error handling
                    percent_potential = percent_stand # Conservative fallback
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "surviving_plants": surviving,
                "current_population_ha": round(current_pop_per_ha),
                "percent_stand": round(percent_stand, 1),
                "percent_potential_yield": round(percent_potential, 1)
            })
            
            total_potential_pct += percent_potential
            
        # Final Average
        avg_potential = total_potential_pct / len(samples) if samples else 0
        loss_percentage = 100.0 - avg_potential
        
        return {
            "method": "stand_reduction",
            "growth_stage": growth_stage,
            "table_used": table_name if not is_mature else "direct_maturity",
            "normal_population": normal_plant_population_per_ha,
            "average_potential_yield_pct": round(avg_potential, 2),
            "loss_percentage": round(loss_percentage, 2),
            "sample_details": processed_samples
        }
    
    @staticmethod
    async def seed_lookup_tables(db: Session):
        """
        Seeds the database with essential USDA Exhibit 11 data for testing.
        """
        table_name = "exhibit11_standReduction"
        
        # Check if already seeded
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing:
            return
            
        data_points = []
        
        # Exhibit 11 Sample Data (Simplified for MVP)
        # Columns: Emergence, ..., 10thLeaf
        # Rows: Percent Stand 50, 55, ... 100
        
        stages = ["emergence", "2ndLeaf", "4thLeaf", "6thLeaf", "8thLeaf", "10thLeaf"]
        
        # Percent Stand -> {Stage: Potential Yield}
        chart_data = {
            100: {s: 100 for s in stages},
            90:  {"emergence": 90, "2ndLeaf": 92, "4thLeaf": 94, "6thLeaf": 96, "8thLeaf": 97, "10thLeaf": 98},
            80:  {"emergence": 80, "2ndLeaf": 84, "4thLeaf": 88, "6thLeaf": 92, "8thLeaf": 94, "10thLeaf": 96},
            70:  {"emergence": 70, "2ndLeaf": 76, "4thLeaf": 82, "6thLeaf": 88, "8thLeaf": 91, "10thLeaf": 94},
            60:  {"emergence": 60, "2ndLeaf": 68, "4thLeaf": 76, "6thLeaf": 84, "8thLeaf": 88, "10thLeaf": 92},
            50:  {"emergence": 50, "2ndLeaf": 60, "4thLeaf": 70, "6thLeaf": 80, "8thLeaf": 85, "10thLeaf": 90}
        }
        
        for pct_stand, stage_values in chart_data.items():
            for stage, potential in stage_values.items():
                data_points.append(LookupTable(
                    table_name=table_name,
                    input_value=float(pct_stand),
                    stage_or_condition=stage,
                    output_value=float(potential)
                ))
                
        db.add_all(data_points)
        db.commit()

        # Seed Exhibit 13 (Hail Stand Reduction 7th-10th Leaf)
        await CalculationService.seed_exhibit_13(db)
        # Seed Exhibit 14 (Hail Stand Reduction 11th-Tasseled)
        await CalculationService.seed_exhibit_14(db)
        # Seed Exhibit 15 (Leaf Loss)
        await CalculationService.seed_exhibit_15(db)

    @staticmethod
    async def calculate_hail_damage(
        db: Session,
        samples: List[Dict[str, Any]],
        growth_stage: str,
        normal_plant_population_per_ha: int = 40000 
    ) -> Dict[str, Any]:
        """
        Calculates Hail Damage based on Exhibits 13, 14, and 15.
        Combines:
        1. Direct Stand Reduction (Ex 13 or 14)
        2. Defoliation (Leaf Loss) (Ex 15)
        3. Direct Damage (Crippled plants, Ear damage, etc. - passed as direct %)

        Formula: Total Damage = Direct Damage + Indirect Damage
        """
        processed_samples = []
        total_damage_pct = 0
        
        # Breakdown accumulator
        damage_breakdown = {
            "stand_reduction": 0.0,
            "defoliation": 0.0,
            "stalk_damage": 0.0,
            "growing_point": 0.0,
            "ear_damage": 0.0,
            "other_direct": 0.0
        }
        
        # Determine applicable Stand Reduction table
        stand_table = None
        if growth_stage in ["7thLeaf", "8thLeaf", "9thLeaf", "10thLeaf"]:
            stand_table = "exhibit13_hailStandReduction"
        elif growth_stage in ["11thLeaf", "12thLeaf", "13thLeaf", "14thLeaf", "15thLeaf", "16thLeaf", "tasseled"]:
            stand_table = "exhibit14_hailStandReduction"
            
        defoliation_table = "exhibit15_leafLoss"
        
        for sample in samples:
            # --- 1. Stand Reduction ---
            row_len = float(sample.get('length_measured_m', 10.0))
            row_width = float(sample.get('row_width_m', 0.9))
            # Start with existing *living* population (before hail event if possible, but usually we count destroyed)
            # USDA Hail Method: We count "Original Stand" vs "Destroyed Plants"
            original_stand_count = int(sample.get('original_stand_count', 40)) # e.g. 40 plants in 10m
            destroyed_count = int(sample.get('destroyed_plants', 0))
            
            percent_reduction = (destroyed_count / original_stand_count) * 100 if original_stand_count > 0 else 0
            percent_reduction = min(100.0, max(0.0, percent_reduction))
            
            stand_damage_pct = percent_reduction # Default if no table
            if stand_table:
                # Lookup "Damage Percent" from "Percent Reduction"
                try:
                    stand_damage_pct = await CalculationService.get_lookup_value(
                        db, stand_table, percent_reduction, growth_stage
                    )
                except ValueError:
                    stand_damage_pct = percent_reduction # Conservative
            
            # --- 2. Defoliation (Leaf Loss) ---
            percent_defoliation = float(sample.get('percent_defoliation', 0.0))
            defoliation_damage_pct = 0.0
            if percent_defoliation > 0:
                try:
                    defoliation_damage_pct = await CalculationService.get_lookup_value(
                        db, defoliation_table, percent_defoliation, growth_stage
                    )
                except ValueError:
                     # Fallback logic if needed, or zero
                     pass

            # --- 3. Other Direct Damage ---
            
            # A. Stalk Damage
            # Map severity to percentage using simplified logic (approximate)
            stalk_severity = sample.get('stalk_damage_severity', 'none').lower()
            stalk_damage_pct = 0.0
            if stalk_severity == 'light': stalk_damage_pct = 10.0
            elif stalk_severity == 'moderate': stalk_damage_pct = 35.0
            elif stalk_severity == 'severe': stalk_damage_pct = 75.0
            
            # B. Growing Point / Heart Damage (Early season)
            growing_point_pct = float(sample.get('growing_point_damage_pct', 0.0))
            
            # C. Ear / Kernel Damage (Late season)
            ear_damage_pct = float(sample.get('ear_damage_pct', 0.0))
            
            # D. Other Direct (Crippled, etc.)
            direct_damage_input = float(sample.get('direct_damage_pct', 0.0))
            
            # Total Direct Damage
            total_direct = stand_damage_pct + stalk_damage_pct + growing_point_pct + ear_damage_pct + direct_damage_input
            total_direct = min(100.0, total_direct)
            
            # Total Sample Damage
            # Formula: Total Damage = Direct Damage + Indirect (Defoliation)
            # USDA sums them, but effectively Defoliation acts on remaining potential
            # Simplified additive model per instructions, capped at 100%
            sample_total_loss = total_direct + defoliation_damage_pct
            sample_total_loss = min(100.0, sample_total_loss)
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "percent_stand_reduction_input": round(percent_reduction, 1),
                "stand_damage_pct": round(stand_damage_pct, 1),
                "defoliation_input_pct": round(percent_defoliation, 1),
                "defoliation_damage_pct": round(defoliation_damage_pct, 1),
                "stalk_damage_pct": round(stalk_damage_pct, 1),
                "growing_point_damage_pct": round(growing_point_pct, 1),
                "ear_damage_pct": round(ear_damage_pct, 1),
                "direct_damage_other_pct": round(direct_damage_input, 1),
                "total_direct_damage": round(total_direct, 1),
                "total_sample_loss": round(sample_total_loss, 1)
            })
            
            total_damage_pct += sample_total_loss
            
            # Aggregate counts for breakdown
            damage_breakdown["stand_reduction"] += stand_damage_pct
            damage_breakdown["defoliation"] += defoliation_damage_pct
            damage_breakdown["stalk_damage"] += stalk_damage_pct
            damage_breakdown["growing_point"] += growing_point_pct
            damage_breakdown["ear_damage"] += ear_damage_pct
            damage_breakdown["other_direct"] += direct_damage_input

        avg_loss = total_damage_pct / len(samples) if samples else 0
        avg_potential_yield = 100.0 - avg_loss
        
        # Average breakdown
        num_samples = len(samples) if samples else 1
        avg_breakdown = {k: round(v / num_samples, 1) for k, v in damage_breakdown.items()}
        
        # Seed lookup tables (if needed)
        await CalculationService.seed_exhibit_17(db)
        await CalculationService.seed_exhibit_23(db)
        await CalculationService.seed_exhibit_24(db)
        
        return {
            "method": "hail_damage",
            "growth_stage": growth_stage,
            "loss_percentage": round(avg_loss, 1),
            "average_potential_yield_pct": round(avg_potential_yield, 1),
            "damage_breakdown": avg_breakdown,
            "sample_details": processed_samples
        }

    @staticmethod
    async def calculate_weight_method(
        db: Session,
        samples: List[Dict[str, Any]],
        row_width_m: float = 0.76, # 30 inches default
        moisture_pct: float = None, # Average field moisture
        test_weight: float = None # lbs/bu or kg/hl
    ) -> Dict[str, Any]:
        """
        Calculates Yield using Weight Method (Exhibit 17).
        Used for late season/mature corn.
        
        Formula:
        Yield = (Weight of Corn in 1/1000 or 1/100 acre) * Factor / Row Length...
        Actually USDA Weight Method:
        1. Harvest sample area (e.g. 1/100 acres).
        2. Weigh ear corn.
        3. Convert to shelled corn using Exhibit 17 (Shelling %).
        4. Adjust for Moisture (to 15%) using Exhibit 23.
        5. Adjust for Test Weight using Exhibit 24.
        """
        processed_samples = []
        total_bushels_per_acre = 0
        
        exhibit17 = "exhibit17_shellingFactors"
        exhibit23 = "exhibit23_moistureAdjustment"
        exhibit24 = "exhibit24_testWeightPack"
        
        # 1. Moisture Adjustment Factor (Standard 15.0% or 15.5% for corn usually, USDA 2024 uses 15.0 or table)
        # We will lookup factor from Exhibit 23 based on actual moisture
        moisture_factor = 1.0
        if moisture_pct is not None:
             try:
                 moisture_factor = await CalculationService.get_lookup_value(db, exhibit23, moisture_pct, "moisture_factor")
             except: pass
             
        # 2. Test Weight Factor
        test_weight_factor = 1.0
        if test_weight is not None:
            try:
                # Assuming input is lbs/bu for now
                test_weight_factor = await CalculationService.get_lookup_value(db, exhibit24, test_weight, "factor")
            except: pass

        for sample in samples:
            weight_lbs = float(sample.get('weight_lbs', 0.0))
            area_acres = float(sample.get('sample_area_acres', 0.01)) # Default 1/100 acre
            
            # Step A: Shelling Factor (Exhibit 17)
            # USDA: If shelling standard 80% not used, use chart
            # We assume weight is Ear Corn. Need to find Shelling Factor.
            # Simplified: Use standard or lookup. Let's use lookup if provided or standard 0.8
            shelling_factor = 0.8
            # Look up based on "Test Weight" or other condition if complex, often fixed or based on kernel moisture
            # Actually Exhibit 17 maps "Ear Weight" vs "Shelled Weight" to get factor.
            # Here we will simplify: Use a calculated or looked up factor if available.
            
            # Step B: Calculate Shelled Weight
            shelled_weight = weight_lbs * shelling_factor
            
            # Step C: Normalize to bu/acre
            # 56 lbs = 1 bushel of shelled corn (Standard)
            bushels_sample = shelled_weight / 56.0
            bushels_per_acre_raw = bushels_sample / area_acres
            
            # Step D: Apply Quality Adjustments
            bushels_adjusted = bushels_per_acre_raw * moisture_factor * test_weight_factor
            
            # Additional Quality Deductions (Percentage Reductions)
            # USDA: Deduct foreign material, damaged kernels, etc. from final yield
            foreign_mat = float(sample.get('foreign_material_pct', 0.0)) / 100.0
            damaged_ker = float(sample.get('damaged_kernels_pct', 0.0)) / 100.0
            broken_ker = float(sample.get('broken_kernels_pct', 0.0)) / 100.0
            heat_dmg = float(sample.get('heat_damage_pct', 0.0)) / 100.0
            
            total_deduction_pct = foreign_mat + damaged_ker + broken_ker + heat_dmg
            
            # Apply deduction: Final = Adjusted * (1 - TotalDeduction)
            bushels_final = bushels_adjusted * (1.0 - total_deduction_pct)
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "raw_weight_lbs": weight_lbs,
                "shelled_weight_lbs": round(shelled_weight, 1),
                "yield_bu_acre_raw": round(bushels_per_acre_raw, 1),
                "quality_adjustments": {
                    "moisture_factor": moisture_factor,
                    "test_weight_factor": test_weight_factor,
                    "foreign_material_deduction": round(foreign_mat * 100, 1),
                    "damaged_kernel_deduction": round(damaged_ker * 100, 1),
                    "broken_kernel_deduction": round(broken_ker * 100, 1),
                    "heat_damage_deduction": round(heat_dmg * 100, 1)
                },
                "yield_bu_acre_adj": round(bushels_final, 1)
            })
            
            total_bushels_per_acre += bushels_final
            
        avg_yield = total_bushels_per_acre / len(samples) if samples else 0
        
        return {
            "method": "weight_method",
            "avg_yield_bu_acre": round(avg_yield, 1),
            "moisture_factor": moisture_factor,
            "test_weight_factor": test_weight_factor,
            "sample_details": processed_samples
        }

    @staticmethod
    async def calculate_maturity_line_weight(
        db: Session,
        samples: List[Dict[str, Any]],
        growth_stage: str,
        expected_final_moisture: float = 15.0
    ) -> Dict[str, Any]:
        """
        Calculates Yield for R3-R5 stages using Maturity Line Method.
        Projects final yield based on kernel development (Milk Line).
        """
        processed_samples = []
        total_projected_yield = 0
        
        # Development Factors based on Stage (Simplified approximations)
        # R3 (Milk): ~40-50% of weight accumulated
        # R4 (Dough): ~60-80% 
        # R5 (Dent): ~85-95%
        # Or better: use maturity line percentage directly if provided.
        # Formula: Current Weight / Development % = Projected Final Weight
        
        for sample in samples:
            weight_lbs = float(sample.get('weight_lbs', 0.0))
            area_acres = float(sample.get('sample_area_acres', 0.01))
            maturity_pct = float(sample.get('maturity_line_position', 0.0)) # 0-100%
            
            # Estimate % of final dry matter accumulated
            # USDA logic: relate milk line to dry matter accumulation
            # 0% milk line (R5 start) -> ~0% hard starch ?? No, Milk Line moves DOWN.
            # 0% down (tip) = Start of R5
            # 50% down = 95% yield accumulated? No, 50% line = 95% yield?
            # USDA Rule of Thumb:
            # Milk Stage (R3): 40% of final yield
            # Late Dough (R4): 65% of final yield
            # 1/2 Milk Line: 95% of final yield ??
            # Let's use a simplified linear model or stage based factor for MVP.
            
            development_factor = 0.5 # Default fallback
            if growth_stage.lower() in ['r3', 'milk']: 
                development_factor = 0.45
            elif growth_stage.lower() in ['r4', 'dough']: 
                development_factor = 0.70
            elif growth_stage.lower() in ['r5', 'dent']:
                # Use milk line if available
                if maturity_pct > 0:
                    # 50% line -> ~90-95% weight
                    # 25% line -> ~80% weight
                    development_factor = 0.75 + (maturity_pct / 100.0) * 0.25
                else:
                    development_factor = 0.85
                    
            projected_weight = weight_lbs / development_factor if development_factor > 0 else 0
            
            # Standard Shelling 80% (Immature corn shelling is tricky, usually whole ear weight used with chart)
            shelling_factor = 0.8
            shelled_weight = projected_weight * shelling_factor
            
            bushels_sample = shelled_weight / 56.0
            bushels_per_acre_proj = bushels_sample / area_acres
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "current_weight_lbs": weight_lbs,
                "maturity_line_pct": maturity_pct,
                "development_factor_used": round(development_factor, 2),
                "projected_yield_bu_acre": round(bushels_per_acre_proj, 1)
            })
            
            total_projected_yield += bushels_per_acre_proj
            
        avg_yield = total_projected_yield / len(samples) if samples else 0
        
        return {
            "method": "maturity_line_weight",
            "growth_stage": growth_stage,
            "avg_maturity_line_position": sum(s['maturity_line_pct'] for s in processed_samples) / len(processed_samples) if processed_samples else 0,
            "projected_yield_bu_acre": round(avg_yield, 1),
            "current_development_pct": round(sum(s['development_factor_used'] for s in processed_samples) / len(processed_samples) * 100, 1) if processed_samples else 0,
            "sample_details": processed_samples
        }

    @staticmethod
    async def calculate_tonnage_method(
        db: Session,
        samples: List[Dict[str, Any]],
        moisture_pct: float,
        visual_damage_pct: float = 0.0,
        quality_grade: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates Silage Tonnage.
        Includes quality grading and moisture adjustment.
        """
        processed_samples = []
        total_tons_per_acre = 0
        
        table_name = "exhibit21_silageMoisture"
        # Seed table if needed
        await CalculationService.seed_exhibit_21(db)
        
        # Determine Quality Grade (Manual or Auto)
        final_grade = quality_grade.lower() if quality_grade else "fair"
        
        # Auto-calculate backup if visual damage provided
        auto_grade = "poor"
        if moisture_pct <= 65 and visual_damage_pct <= 10: auto_grade = "excellent"
        elif moisture_pct <= 70 and visual_damage_pct <= 25: auto_grade = "good"
        elif moisture_pct <= 75 and visual_damage_pct <= 50: auto_grade = "fair"
        
        # If manual not provided, use auto
        if not quality_grade:
            final_grade = auto_grade
            
        # Quality Multiplier (Placeholder logic)
        # Excellent=1.0, Good=0.95, Fair=0.85, Poor=0.70
        quality_map = {"excellent": 1.0, "good": 0.95, "fair": 0.85, "poor": 0.70}
        quality_factor = quality_map.get(final_grade, 0.70)
        
        # Moisture Adjustment Factor
        moisture_factor = 1.0
        try:
            moisture_factor = await CalculationService.get_lookup_value(db, table_name, moisture_pct, "factor")
        except: pass
        
        for sample in samples:
            fresh_weight = float(sample.get('fresh_weight_lbs', 0.0))
            area_acres = float(sample.get('sample_area_acres', 0.001)) # 1/1000 standard
            
            # Tons = (Weight / 2000) / Acres
            tons_raw = (fresh_weight / 2000.0) / area_acres
            
            # Adjust for moisture (standard 65%) and quality
            tons_adj = tons_raw * moisture_factor * quality_factor
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "fresh_weight_lbs": fresh_weight,
                "tons_per_acre_raw": round(tons_raw, 1),
                "tons_per_acre_adj": round(tons_adj, 1)
            })
            
            total_tons_per_acre += tons_adj
            
        avg_tons = total_tons_per_acre / len(samples) if samples else 0
            
        return {
            "method": "tonnage",
            "tons_per_acre": round(avg_tons, 1), # Adjusted
            "moisture_adjusted_tons": round(avg_tons / quality_factor, 1) if quality_factor else 0, # Just moisture adj
            "quality_grade": final_grade,
            "quality_multiplier": quality_factor,
            "recommended_for_silage": avg_tons > 5.0, # Simple threshold
            "tonnage_confidence": 0.85 if quality_grade else 0.70, # Lower confidence if auto-graded
            "sample_details": processed_samples
        }

    @staticmethod
    async def calculate_replanting_analysis(
        normal_yield: float,
        price: float,
        share: float,
        stand_pct: float,
        replant_cost: float,
        replant_factor: float
    ) -> Dict[str, Any]:
        """
        Calculates whether it is economical to replant (USDA Part 3).
        """
        # 1. Value of Keeping Current Stand
        # Yield Potential = Normal Yield * (Stand % / 100)
        yield_keep = normal_yield * (stand_pct / 100.0)
        value_keep = yield_keep * price * share
        
        # 2. Value of Replanting
        # Replanted Yield = Normal Yield * Replant Factor (penalty for late start)
        yield_replant = normal_yield * replant_factor
        gross_value_replant = yield_replant * price * share
        net_value_replant = gross_value_replant - replant_cost
        
        # 3. Recommendation
        is_replant_economical = net_value_replant > value_keep
        recommendation = "REPLANT" if is_replant_economical else "KEEP"
        
        # 4. Replanting Payment Calculation (USDA Formula)
        # Usually: Lesser of (20% of guarantee or 8 bu) * Price * Share * Acres
        # We simplify to Per Acre payment amount here.
        # Max standard payment is typically 8 bushels x Price.
        payment_bu_limit = 8.0
        payment_amount = payment_bu_limit * price * share
        
        # Breakeven: How much yield gain needed to cover cost?
        # Cost / Price = Bushels needed
        breakeven_bu = replant_cost / price if price > 0 else 0
        
        return {
            "recommendation": recommendation,
            "keep_projected_value": round(value_keep, 2),
            "replant_projected_value": round(net_value_replant, 2),
            "replanting_payment_amount": round(payment_amount, 2),
            "breakeven_yield_diff": round(breakeven_bu, 1)
        }

    @staticmethod
    async def calculate_stage_modification(
        days_from_planting: int,
        maturity_days: int
    ) -> Dict[str, Any]:
        """
        Adjusts growth stage for short-season varieties (Exhibit 16).
        Standard Corn is assumed ~120 days.
        """
        standard_maturity = 120.0
        
        # Modification Factor
        # If variety is 90 days, it moves 1.33x faster than 120 day corn.
        # Factor = 120 / 90 = 1.33
        factor = standard_maturity / float(maturity_days)
        
        # Equivalent Standard Days
        standard_days_equiv = days_from_planting * factor
        
        # Map Standard Days to Stage (Approximate USDA timeline)
        # Emergence: 0-20 days (VE-V2)
        # Knee High: 35 days (V6)
        # Tassel: 65-75 days (VT)
        # Silk: 75-80 days (R1)
        # Dough/Dent: 90+ days
        
        stage = "Unknown"
        lookup_stage = "Unknown"
        
        sd = standard_days_equiv
        if sd < 15: 
            stage = "VE-V2"
            lookup_stage = "Emergence"
        elif sd < 30:
            stage = "V3-V5"
            lookup_stage = "7thLeaf" # Approx start of hail charts
        elif sd < 45:
            stage = "V6-V8"
            lookup_stage = "8thLeaf"
        elif sd < 60:
            stage = "V9-V12"
            lookup_stage = "10thLeaf"
        elif sd < 75:
            stage = "VT (Tassel)"
            lookup_stage = "tasseled"
        elif sd < 90:
            stage = "R1-R2 (Silk/Blister)"
            lookup_stage = "Silked"
        elif sd < 105:
            stage = "R3-R4 (Milk/Dough)"
            lookup_stage = "Milk"
        else:
            stage = "R5+ (Dent/Mature)"
            lookup_stage = "Mature"
            
        return {
            "adjusted_growth_stage": stage,
            "standard_equivalent_days": int(standard_days_equiv),
            "lookup_table_stage": lookup_stage
        }

    # --- Seeding Helpers (Additional) ---
    
    @staticmethod
    async def seed_exhibit_21(db: Session):
        table_name = "exhibit21_silageMoisture"
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing: return
        
        # Silage Moisture Factors (Standard 65%)
        # >65% reduces tonnage (water weight)
        # <65% increases tonnage (dryer than standard)
        # Factor = 35 / (100 - Actual %) ??? No, usually (100-Actual)/(100-Standard)
        # Let's use a simplified table
        data = [
            (50.0, 1.4), (55.0, 1.25), (60.0, 1.15), (65.0, 1.0),
            (70.0, 0.9), (75.0, 0.8), (80.0, 0.7)
        ]
        for m, f in data:
            db.add(LookupTable(table_name=table_name, input_value=m, stage_or_condition="factor", output_value=f))
        db.commit()
    
    @staticmethod
    async def seed_exhibit_17(db: Session):
        # Exhibit 17: Shelling Percentage Factors
        # Simplified: Just storing standard Reference
        pass

    @staticmethod
    async def seed_exhibit_23(db: Session):
        table_name = "exhibit23_moistureAdjustment"
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing: return
        
        # USDA Moisture Adjustment Factor = (100 - Actual) / (100 - Standard)
        # Standard Corn Basis = 15.0%
        # Example: 20% moisture -> (100-20)/(100-15) = 80/85 = 0.9412
        # Example: 15% moisture -> 1.0
        # Example: 30% moisture -> 70/85 = 0.8235
        data = [
            (10.0, 1.0588), (15.0, 1.0000), (20.0, 0.9412),
            (25.0, 0.8824), (30.0, 0.8235), (35.0, 0.7647)
        ]
        for m, f in data:
             db.add(LookupTable(table_name=table_name, input_value=m, stage_or_condition="moisture_factor", output_value=f))
        db.commit()

    @staticmethod
    async def seed_exhibit_24(db: Session):
        table_name = "exhibit24_testWeightPack"
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing: return
        
        # Test Weight Factors (Lbs/Bu)
        # USDA Standards: 56 lbs = 1.0
        # Lower weights reduce yield: 54->0.98, 50->0.94, etc.
        data = [
            (56.0, 1.0), (55.0, 0.99), (54.0, 0.98), (53.0, 0.97), 
            (52.0, 0.96), (51.0, 0.95), (50.0, 0.94), (49.0, 0.93),
            (48.0, 0.92), (47.0, 0.91), (46.0, 0.90), (45.0, 0.89)
        ]
        for w, f in data:
             db.add(LookupTable(table_name=table_name, input_value=w, stage_or_condition="factor", output_value=f))
        db.commit()
    
    @staticmethod
    async def seed_exhibit_13(db: Session):
        table_name = "exhibit13_hailStandReduction"
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing: return
        
        # Simplified Data: 7th to 10th leaf
        # Input: Percent Stand Reduction -> Output: Percent Damage
        # Example: 10% reduction -> 3% damage (plants recover)
        stages = ["7thLeaf", "8thLeaf", "9thLeaf", "10thLeaf"]
        chart_data = {
            10: {s: 3.0 for s in stages}, 
            50: {s: 48.0 for s in stages}, # Almost 1:1 at high loss
            100: {s: 100.0 for s in stages}
        }
        for inp, vals in chart_data.items():
            for s, out in vals.items():
                db.add(LookupTable(table_name=table_name, input_value=float(inp), stage_or_condition=s, output_value=float(out)))
        db.commit()

    @staticmethod
    async def seed_exhibit_14(db: Session):
        table_name = "exhibit14_hailStandReduction"
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing: return
        
        # 11th Leaf to Tassel: Usually nearly 1-to-1 damage
        stages = ["11thLeaf", "15thLeaf", "tasseled"]
        chart_data = {
            10: {s: 9.0 for s in stages}, 
            50: {s: 50.0 for s in stages}, 
            100: {s: 100.0 for s in stages}
        }
        for inp, vals in chart_data.items():
            for s, out in vals.items():
                db.add(LookupTable(table_name=table_name, input_value=float(inp), stage_or_condition=s, output_value=float(out)))
        db.commit()

    @staticmethod
    async def seed_exhibit_15(db: Session):
        table_name = "exhibit15_leafLoss"
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing: return
        
        # Leaf Loss (Defoliation)
        # Input: % Defoliation -> Output: % Yield Loss
        # Varies heavily by stage. Tassel stage is most critical.
        data = [
            # 7th Leaf: 100% de-foliation = 9% yield loss
            (100.0, "7thLeaf", 9.0), (50.0, "7thLeaf", 4.0),
            # 10th Leaf: 100% = 16% loss
            (100.0, "10thLeaf", 16.0), (50.0, "10thLeaf", 7.0),
            # Tasseled: 100% = 100% loss (Critical)
            (100.0, "tasseled", 100.0), (50.0, "tasseled", 32.0),
        ]
        for inp, s, out in data:
            db.add(LookupTable(table_name=table_name, input_value=inp, stage_or_condition=s, output_value=out))
        db.commit()
