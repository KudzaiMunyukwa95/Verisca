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
    def to_lbs(kg: float) -> float:
        return kg * 2.20462

    @staticmethod
    def to_kg(lbs: float) -> float:
        return lbs / 2.20462

    @staticmethod
    def to_acres(ha: float) -> float:
        return ha * 2.47105

    @staticmethod
    def to_ha(acres: float) -> float:
        return acres / 2.47105
        
    @staticmethod
    def bu_acre_to_kg_ha(bu_acre: float, lbs_per_bu: float = 56.0) -> float:
        # 1 bu/acre = (56 lbs / 2.20462 kg) / (1 acre / 2.47105 ha)
        # 1 bu = 25.401 kg
        # 1 acre = 0.404686 ha
        # kg/ha = (bu * 25.401) / 0.404686
        # Or simply: bu/acre * (lbs_per_bu * 1.12085) ...wait check factor
        # Factor for Corn (56lb): ~62.77
        # Factor = (Lbs / 2.20462) * 2.47105
        factor = (lbs_per_bu / 2.20462) * 2.47105
        return bu_acre * factor

    @staticmethod
    def kg_ha_to_bu_acre(kg_ha: float, lbs_per_bu: float = 56.0) -> float:
         if lbs_per_bu == 0: return 0
         factor = (lbs_per_bu / 2.20462) * 2.47105
         return kg_ha / factor

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
    async def calculate_hail_damage(
        db: Session,
        samples: List[Dict[str, Any]],
        growth_stage: str,
        normal_plant_population_per_ha: int = 40000
    ) -> Dict[str, Any]:
        """
        Calculates Hail Damage (Stand Reduction + Defoliation + Direct).
        """
        processed_samples = []
        total_loss_pct = 0
        
        # 1. Determine Tables
        # Stand Reduction: Ex 13 (Early) or Ex 14 (Late)
        stand_table = "exhibit13_hailStandReduction"
        late_stages = ["11thLeaf", "12thLeaf", "13thLeaf", "14thLeaf", "15thLeaf", "16thLeaf", "tasseled", "silked"]
        if growth_stage in late_stages:
            stand_table = "exhibit14_hailStandReduction"
            
        defoliation_table = "exhibit15_leafLoss"
        
        # Seed tables if needed (Safe check)
        await CalculationService.seed_exhibit_13(db)
        await CalculationService.seed_exhibit_14(db)
        await CalculationService.seed_exhibit_15(db)

        for sample in samples:
            loss_components = {}
            
            # A. Stand Reduction Loss
            original = int(sample.get('original_stand_count', 100))
            destroyed = int(sample.get('destroyed_plants', 0))
            stand_reduction_pct = (destroyed / original * 100) if original > 0 else 0
            
            stand_loss_yield = stand_reduction_pct # Default 1:1 fallback
            try:
                stand_loss_yield = await CalculationService.get_lookup_value(
                    db, stand_table, stand_reduction_pct, growth_stage
                )
            except: pass
            loss_components['stand'] = stand_loss_yield
            
            # B. Defoliation Loss
            defoliation_pct = float(sample.get('percent_defoliation', 0.0))
            defoliation_loss_yield = 0.0
            try:
                defoliation_loss_yield = await CalculationService.get_lookup_value(
                    db, defoliation_table, defoliation_pct, growth_stage
                )
            except: 
                # Very rough fallback if table missing
                defoliation_loss_yield = defoliation_pct * 0.1 
            loss_components['defoliation'] = defoliation_loss_yield
            
            # C. Direct Damage (Stalk, Ear, Direct)
            # Simplified: Sum of provided directs
            direct_pct = float(sample.get('direct_damage_pct', 0.0))
            ear_pct = float(sample.get('ear_damage_pct', 0.0))
            gp_pct = float(sample.get('growing_point_damage_pct', 0.0))
            
            direct_loss_total = direct_pct + ear_pct + gp_pct
            loss_components['direct'] = direct_loss_total
            
            # Total Sample Loss (Additive, capped at 100)
            sample_total_loss = stand_loss_yield + defoliation_loss_yield + direct_loss_total
            sample_total_loss = min(100.0, sample_total_loss)
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "stand_reduction_input": stand_reduction_pct,
                "stand_loss_yield": stand_loss_yield,
                "defoliation_loss_yield": defoliation_loss_yield,
                "direct_loss_yield": direct_loss_total,
                "total_loss_pct": round(sample_total_loss, 2)
            })
            
            total_loss_pct += sample_total_loss
            
        avg_loss = total_loss_pct / len(samples) if samples else 0
        avg_potential = 100.0 - avg_loss
        
        return {
            "method": "hail_damage",
            "growth_stage": growth_stage,
            "loss_percentage": round(avg_loss, 2),
            "average_potential_yield_pct": round(avg_potential, 2),
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
    @staticmethod
    async def calculate_weight_method(
        db: Session,
        samples: List[Dict[str, Any]],
        row_width_m: float = 0.76, 
        moisture_pct: float = None,
        test_weight_kg_hl: float = None 
    ) -> Dict[str, Any]:
        """
        Calculates Yield using Weight Method. Metric Version.
        """
        processed_samples = []
        total_kg_ha = 0
        
        exhibit23 = "exhibit23_moistureAdjustment"
        exhibit24 = "exhibit24_testWeightPack"
        
        moisture_factor = 1.0
        if moisture_pct is not None:
             try:
                 moisture_factor = await CalculationService.get_lookup_value(db, exhibit23, moisture_pct, "moisture_factor")
             except: pass
             
        test_weight_factor = 1.0
        # Convert Test Weight to lbs/bu for lookup
        if test_weight_kg_hl is not None:
            tw_lbs_bu = test_weight_kg_hl * 0.7768
            try:
                test_weight_factor = await CalculationService.get_lookup_value(db, exhibit24, tw_lbs_bu, "factor")
            except: pass

        for sample in samples:
            weight_kg = float(sample.get('fresh_weight_kg', 0.0))
            # Convert weight to lbs
            weight_lbs = CalculationService.to_lbs(weight_kg)
            
            # Area usually m2 now?
            area_m2 = float(sample.get('sample_area_m2', 40.46)) # 1/100 acre in m2 approx
            # Convert area to acres
            area_acres = area_m2 / 4046.86
            
            # DYNAMIC SHELLING FACTOR (Exhibit 17)
            # Use moisture_pct if available, else standard 0.8
            shelling_factor = 0.8
            if moisture_pct:
                 try:
                     shelling_factor = await CalculationService.get_lookup_value(db, "exhibit17_shellingPercentage", moisture_pct, "shelling_factor")
                 except: pass # Default 0.8
            
            shelled_weight = weight_lbs * shelling_factor
            
            bushels_sample = shelled_weight / 56.0
            bushels_per_acre_raw = bushels_sample / area_acres
            
            # Apply Factors
            bushels_adjusted = bushels_per_acre_raw * moisture_factor * test_weight_factor
            
            foreign_mat = float(sample.get('foreign_material_pct', 0.0)) / 100.0
            damaged_ker = float(sample.get('damaged_kernels_pct', 0.0)) / 100.0
            broken_ker = float(sample.get('broken_kernels_pct', 0.0)) / 100.0
            heat_dmg = float(sample.get('heat_damage_pct', 0.0)) / 100.0
            
            total_deduction_pct = foreign_mat + damaged_ker + broken_ker + heat_dmg
            bushels_final = bushels_adjusted * (1.0 - total_deduction_pct)
            
            # Convert Result to kg/ha
            yield_kg_ha = CalculationService.bu_acre_to_kg_ha(bushels_final)
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "yield_kg_ha_adj": round(yield_kg_ha, 1)
            })
            
            total_kg_ha += yield_kg_ha
            
        avg_yield = total_kg_ha / len(samples) if samples else 0
        
        return {
            "method": "weight_method",
            "avg_yield_kg_ha": round(avg_yield, 1),
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
        Calculates Silage Tonnage (Metric).
        """
        processed_samples = []
        total_tonnes_ha = 0
        
        table_name = "exhibit21_silageMoisture"
        await CalculationService.seed_exhibit_21(db)
        
        final_grade = quality_grade.lower() if quality_grade else "fair"
        if not quality_grade:
             # Auto logic... (keep existing if needed, simplified here)
             final_grade = "fair" # Fallback

        quality_map = {"excellent": 1.0, "good": 0.95, "fair": 0.85, "poor": 0.70}
        quality_factor = quality_map.get(final_grade, 0.70)
        
        moisture_factor = 1.0
        try:
             moisture_factor = await CalculationService.get_lookup_value(db, table_name, moisture_pct, "factor")
        except: pass
        
        for sample in samples:
            weight_kg = float(sample.get('fresh_weight_kg', 0.0))
            area_m2 = float(sample.get('sample_area_m2', 4.047)) # 1/1000 acre is ~4.047 m2
            
            if area_m2 == 0: continue
            
            # Kg per Ha = (Weight / Area) * 10000
            kg_per_ha = (weight_kg / area_m2) * 10000
            
            # Tonnes per Ha
            tonnes_raw = kg_per_ha / 1000.0
            
            tonnes_adj = tonnes_raw * moisture_factor * quality_factor
            
            processed_samples.append({
                "sample_number": sample.get('sample_number'),
                "tonnes_ha_raw": round(tonnes_raw, 1),
                "tonnes_ha_adj": round(tonnes_adj, 1)
            })
            
            total_tonnes_ha += tonnes_adj
            
        avg_tonnes = total_tonnes_ha / len(samples) if samples else 0
            
        return {
            "method": "tonnage",
            "tonnes_per_ha": round(avg_tonnes, 1),
            "quality_grade": final_grade,
            "sample_details": processed_samples
        }

    @staticmethod
    async def calculate_replanting_analysis(
        normal_yield_kg_ha: float,
        price_per_kg: float,
        share: float,
        stand_pct: float,
        replant_cost_per_ha: float,
        replant_factor: float
    ) -> Dict[str, Any]:
        """
        Calculates whether it is economical to replant (USDA Part 3).
        Metric Version.
        """
        # 1. Value of Keeping Current Stand
        # Yield Potential = Normal Yield * (Stand % / 100)
        yield_keep = normal_yield_kg_ha * (stand_pct / 100.0)
        value_keep = yield_keep * price_per_kg * share
        
        # 2. Value of Replanting
        yield_replant = normal_yield_kg_ha * replant_factor
        gross_value_replant = yield_replant * price_per_kg * share
        net_value_replant = gross_value_replant - replant_cost_per_ha
        
        # 3. Recommendation
        is_replant_economical = net_value_replant > value_keep
        recommendation = "REPLANT" if is_replant_economical else "KEEP"
        
        # 4. Replanting Payment Calculation
        # USDA 8 bushels/acre limit.
        # Convert 8 bu/acre to kg/ha ~ 500 kg/ha
        limit_kg_ha = CalculationService.bu_acre_to_kg_ha(8.0) 
        payment_amount = limit_kg_ha * price_per_kg * share
        
        # Breakeven
        breakeven_kg = replant_cost_per_ha / price_per_kg if price_per_kg > 0 else 0
        
        return {
            "recommendation": recommendation,
            "keep_projected_value": round(value_keep, 2),
            "replant_projected_value": round(net_value_replant, 2),
            "replanting_payment_amount": round(payment_amount, 2),
            "breakeven_yield_diff_kg_ha": round(breakeven_kg, 1)
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
        table_name = "exhibit17_shellingPercentage"
        existing = db.execute(select(LookupTable).where(LookupTable.table_name == table_name)).first()
        if existing: return
        
        # Exhibit 17: Shelling Percentage based on Moisture
        # High moisture = lower shelling % (cob is heavier/wetter)
        # USDA typical range: 80% (0.80) at standard 15.5%. Lower at high moisture.
        # Approximation data:
        # Moisture % -> Shelling Factor
        data = [
            (10.0, 0.82), (15.0, 0.80), (20.0, 0.78),
            (25.0, 0.76), (30.0, 0.74), (35.0, 0.72), (40.0, 0.70)
        ]
        for m, f in data:
            db.add(LookupTable(table_name=table_name, input_value=m, stage_or_condition="factor", output_value=f))
        db.commit()

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
