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
            # e.g., Ear Damage, Crippled Plants - usually calculated as direct % addition
            direct_damage_input = float(sample.get('direct_damage_pct', 0.0))
            
            # Total Sample Damage
            # Note: USDA adds them, but total cannot exceed 100%
            # Detailed formula: (100 - StandLoss) * (DefoliationLoss) ... ? 
            # USDA usually sums them: Total = Stand Reduction + Defoliation + Direct
            sample_total_loss = stand_damage_pct + defoliation_damage_pct + direct_damage_input
            sample_total_loss = min(100.0, sample_total_loss)
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "percent_stand_reduction_input": round(percent_reduction, 1),
                "stand_damage_pct": round(stand_damage_pct, 1),
                "defoliation_input_pct": round(percent_defoliation, 1),
                "defoliation_damage_pct": round(defoliation_damage_pct, 1),
                "direct_damage_pct": round(direct_damage_input, 1),
                "total_sample_loss": round(sample_total_loss, 1)
            })
            
            total_damage_pct += sample_total_loss

        avg_loss = total_damage_pct / len(samples) if samples else 0
        
        # Seed Exhibit 17 (Shelling percentage)
        await CalculationService.seed_exhibit_17(db)
        # Seed Exhibit 23 (Moisture Adjustment)
        await CalculationService.seed_exhibit_23(db)
        # Seed Exhibit 24 (Test Weight)
        await CalculationService.seed_exhibit_24(db)

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
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "raw_weight_lbs": weight_lbs,
                "shelled_weight_lbs": round(shelled_weight, 1),
                "yield_bu_acre_raw": round(bushels_per_acre_raw, 1),
                "yield_bu_acre_adj": round(bushels_adjusted, 1)
            })
            
            total_bushels_per_acre += bushels_adjusted
            
        avg_yield = total_bushels_per_acre / len(samples) if samples else 0
        
        return {
            "method": "weight_method",
            "avg_yield_bu_acre": round(avg_yield, 1),
            "moisture_factor": moisture_factor,
            "test_weight_factor": test_weight_factor,
            "sample_details": processed_samples
        }

    # --- Seeding Helpers (Additional) ---
    
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
        
        # Test Weight Factors (Lbs/Bu) - Standard 56 lbs
        # <50 lbs reduces yield
        data = [
            (56.0, 1.0), (54.0, 0.98), (52.0, 0.96), (50.0, 0.94), (45.0, 0.89)
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
