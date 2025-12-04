# 5. LOOKUP TABLE SPECIFICATIONS

## Required Lookup Tables from USDA Handbook

### Table 1: Exhibit 11 - Stand Reduction (Emergence to 10th Leaf)

```json
{
  "exhibit11_standReduction": {
    "name": "Corn Stand Reduction - Percent of Potential Remaining from Emergence through 10th Leaf Stages",
    "usage": "standReductionMethod",
    "growthStages": ["emergence", "2ndLeaf", "3rdLeaf", "4thLeaf", "5thLeaf", "6thLeaf", "7thLeaf", "8thLeaf", "9thLeaf", "10thLeaf"],
    "structure": {
      "rows": "percentStand", // 0-100% in 5% increments
      "columns": "growthStage",
      "values": "percentPotentialRemaining",
      "interpolation": "required",
      "roundingRule": "nearestWholePercent"
    },
    "dataSchema": {
      "percentStand": "INTEGER", // 0, 5, 10, 15, ..., 100
      "growthStage": "VARCHAR(20)",
      "potentialRemaining": "INTEGER" // 0-100
    },
    "sampleData": [
      {"percentStand": 100, "emergence": 100, "2ndLeaf": 100, "3rdLeaf": 100},
      {"percentStand": 95, "emergence": 95, "2ndLeaf": 96, "3rdLeaf": 97},
      {"percentStand": 90, "emergence": 90, "2ndLeaf": 92, "3rdLeaf": 94},
      {"percentStand": 85, "emergence": 85, "2ndLeaf": 88, "3rdLeaf": 91}
    ],
    "interpolationNote": "Linear interpolation required between table values"
  }
}
```

### Table 2: Exhibit 12 - Stand Reduction (11th Leaf to Tasseled)

```json
{
  "exhibit12_standReduction": {
    "name": "Corn Stand Reduction - Percent of Potential Remaining 11th through Tasseled Stages",
    "usage": "standReductionMethod",
    "growthStages": ["11thLeaf", "12thLeaf", "13thLeaf", "14thLeaf", "15thLeaf", "16thLeaf", "tasseled"],
    "structure": {
      "rows": "percentStand",
      "columns": "growthStage", 
      "values": "percentPotentialRemaining",
      "interpolation": "required",
      "roundingRule": "nearestWholePercent"
    },
    "specialNote": "DO NOT USE BEFORE 11TH LEAF STAGE",
    "dataSchema": {
      "percentStand": "INTEGER",
      "growthStage": "VARCHAR(20)",
      "potentialRemaining": "INTEGER"
    }
  }
}
```

### Table 3: Exhibit 13 - Hail Stand Reduction (7th to 10th Leaf)

```json
{
  "exhibit13_hailStandReduction": {
    "name": "Hail Stand Reduction Loss - Corn for 7th Leaf through 10th Leaf Stages",
    "usage": "hailDamageMethod",
    "growthStages": ["7thLeaf", "8thLeaf", "9thLeaf", "10thLeaf"],
    "structure": {
      "rows": "percentStandReduction",
      "columns": "growthStage",
      "values": "percentDamage",
      "interpolation": "required",
      "roundingRule": "nearestWholePercent"
    },
    "specialNote": "Use ONLY for hail damage assessment, different from regular stand reduction",
    "dataSchema": {
      "percentStandReduction": "INTEGER",
      "growthStage": "VARCHAR(20)", 
      "damagePercent": "INTEGER"
    }
  }
}
```

### Table 4: Exhibit 14 - Hail Stand Reduction (11th Leaf to Tasseled)

```json
{
  "exhibit14_hailStandReduction": {
    "name": "Hail Stand Reduction Loss - Corn for 11th through Tasseled Stages",
    "usage": "hailDamageMethod", 
    "growthStages": ["11thLeaf", "12thLeaf", "13thLeaf", "14thLeaf", "15thLeaf", "16thLeaf", "tasseled"],
    "structure": {
      "rows": "percentStandReduction",
      "columns": "growthStage",
      "values": "percentDamage", 
      "interpolation": "required",
      "roundingRule": "nearestWholePercent"
    },
    "specialNote": "DO NOT USE BEFORE 11TH LEAF STAGE",
    "dataSchema": {
      "percentStandReduction": "INTEGER",
      "growthStage": "VARCHAR(20)",
      "damagePercent": "INTEGER"
    }
  }
}
```

### Table 5: Exhibit 15 - Leaf Loss Chart (Defoliation)

```json
{
  "exhibit15_leafLoss": {
    "name": "Leaf Loss Chart",
    "usage": "hailDamageMethod_indirectDamage",
    "description": "Converts defoliation percentage to yield loss percentage",
    "structure": {
      "rows": "percentDefoliation", // 0-100%
      "columns": "growthStage",
      "values": "percentYieldLoss",
      "interpolation": "required"
    },
    "growthStages": ["7thLeaf", "8thLeaf", "9thLeaf", "10thLeaf", "11thLeaf", "12thLeaf", "tasseled", "silked"],
    "dataSchema": {
      "percentDefoliation": "INTEGER", // 0, 10, 20, 30, ..., 100
      "growthStage": "VARCHAR(20)",
      "yieldLossPercent": "DECIMAL(4,1)"
    },
    "criticalNote": "Must be used with stage modification for short-season varieties"
  }
}
```

### Table 6: Exhibit 16 - Stage Modification

```json
{
  "exhibit16_stageModification": {
    "name": "Stage Modification",
    "usage": "hailDamageMethod_shortSeasonVarieties",
    "description": "Adjusts growth stages for varieties with less than 19-21 leaves",
    "structure": {
      "actualStage": "currentGrowthStage",
      "ultimateLeafCount": "totalLeavesToBeProduced", 
      "modifiedStage": "adjustedStageForChart"
    },
    "dataSchema": {
      "actualStage": "VARCHAR(20)",
      "ultimateLeafCount": "INTEGER", // 15-23 typical range
      "modifiedStage": "VARCHAR(20)"
    },
    "applicationRule": "Use only when ultimate leaf count differs from standard 19-21 leaves"
  }
}
```

### Table 7: Exhibit 17 - Shelling Percentage Factors

```json
{
  "exhibit17_shellingFactors": {
    "name": "Shelling Percentage Factors - Ear Corn",
    "usage": "weightMethod",
    "description": "Converts ear corn weight to shelled corn equivalent",
    "structure": {
      "earCornWeight": "5.0", // Standard 5 lb sample
      "shelledCornWeight": "variableWeight",
      "shellingFactor": "conversionMultiplier"
    },
    "dataSchema": {
      "earCornSampleLbs": "DECIMAL(3,1)", // Always 5.0
      "shelledCornSampleLbs": "DECIMAL(3,1)", // 2.8 to 4.4
      "shellingFactor": "DECIMAL(3,2)" // 0.70 to 1.10
    },
    "conversionNote": "For weights not in chart, calculate as (shelledWeight/4) rounded to 2 decimal places",
    "sampleData": [
      {"earWeight": 5.0, "shelledWeight": 4.4, "factor": 1.10},
      {"earWeight": 5.0, "shelledWeight": 4.0, "factor": 1.00},
      {"earWeight": 5.0, "shelledWeight": 3.6, "factor": 0.90},
      {"earWeight": 5.0, "shelledWeight": 3.2, "factor": 0.80}
    ]
  }
}
```

### Table 8: Exhibit 21 - Silage Moisture Factors

```json
{
  "exhibit21_silageMoisture": {
    "name": "Silage Moisture Factors",
    "usage": "tonnageMethod",
    "description": "Converts silage to 65% moisture equivalent",
    "structure": {
      "moistureContent": "actualMoisturePercent",
      "conversionFactor": "adjustmentMultiplier"
    },
    "dataSchema": {
      "moisturePercent": "DECIMAL(4,1)", // 30.0 to 85.0
      "conversionFactor": "DECIMAL(5,3)" // Precision required
    },
    "standardMoisture": 65.0,
    "interpolation": "linear_required"
  }
}
```

### Table 9: Exhibit 22 - Grain-Deficient Silage Factors

```json
{
  "exhibit22_grainDeficient": {
    "name": "Grain-Deficient Silage: Appraisal Factors", 
    "usage": "tonnageMethod_qualityAdjustment",
    "description": "Adjusts silage value when grain content < 4.5 bushels/ton",
    "structure": {
      "bushelsPerTon": "grainContentRatio",
      "adjustmentFactor": "reductionMultiplier"
    },
    "threshold": 4.5, // bushels per ton minimum for normal silage
    "dataSchema": {
      "bushelsPerTon": "DECIMAL(3,1)", // 0.0 to 4.4
      "adjustmentFactor": "DECIMAL(4,3)" // 0.600 to 0.999
    },
    "applicationNote": "Only applies to silage insured as silage with concurrent grain assessment"
  }
}
```

### Table 10: Exhibit 23 - Moisture Adjustment Factors

```json
{
  "exhibit23_moistureAdjustment": {
    "name": "Corn Moisture Adjustment Factors",
    "usage": "qualityAdjustment_allMethods",
    "description": "Adjusts yield for moisture content deviation from 12.5% standard",
    "standardMoisture": 12.5,
    "structure": {
      "moistureContent": "actualMoisturePercent",
      "adjustmentFactor": "yieldMultiplier"
    },
    "dataSchema": {
      "moisturePercent": "DECIMAL(4,1)", // 8.0 to 30.0
      "adjustmentFactor": "DECIMAL(6,4)" // High precision required
    },
    "interpolation": "linear_required",
    "roundingRule": "4_decimal_places"
  }
}
```

### Table 11: Exhibit 24 - Test Weight and Pack Factors

```json
{
  "exhibit24_testWeightPack": {
    "name": "Corn - Combined Test Weight and Pack Factors",
    "usage": "qualityAdjustment_allMethods",
    "description": "Adjusts yield based on test weight (bulk density)",
    "structure": {
      "testWeightKgPerHl": "bulkDensity",
      "packFactor": "qualityMultiplier"
    },
    "standardTestWeight": 750, // kg/hectolitre (approximate)
    "dataSchema": {
      "testWeightKgPerHl": "INTEGER", // 600 to 800
      "packFactor": "DECIMAL(5,3)" // 0.900 to 1.100
    },
    "measurementUnits": {
      "metric": "kg_per_hectolitre",
      "imperial_original": "lbs_per_bushel"
    },
    "conversionFactor": "1_lb_per_bushel = 12.87_kg_per_hectolitre"
  }
}
```

### Table 12: Exhibit 25 - Growth Stage Characteristics

```json
{
  "exhibit25_stageCharacteristics": {
    "name": "Corn Stage Characteristics",
    "usage": "growthStageIdentification_allMethods",
    "description": "Detailed characteristics for identifying corn growth stages",
    "structure": {
      "stageName": "growthStageIdentifier",
      "timeInterval": "daysToNextStage",
      "characteristics": "physicalDescriptors",
      "percentLeafAreaExposed": "leafAreaPercent"
    },
    "dataSchema": {
      "stageName": "VARCHAR(30)",
      "averageTimeInterval": "INTEGER", // days
      "characteristics": "TEXT",
      "leafAreaPercent": "INTEGER" // 0-100
    },
    "stages": [
      "emergence", "2ndLeaf", "3rdLeaf", "4thLeaf", "5thLeaf", "6thLeaf",
      "7thLeaf", "8thLeaf", "9thLeaf", "10thLeaf", "11thLeaf", "12thLeaf",
      "13thLeaf", "14thLeaf", "15thLeaf", "16thLeaf", "17thLeaf", "tasseled",
      "silked", "silksBrown", "preBlister", "blister", "earlyMilk", "milk",
      "lateMilk", "softDough", "earlyDent", "dent", "lateDent", "nearlyMature", "fullyMature"
    ],
    "specialNote": "Critical for method selection - stage determines applicable assessment method"
  }
}
```

## Lookup Table Implementation Structure

### Database Schema Template

```sql
-- Generic structure for all lookup tables
CREATE TABLE lookup_table_{exhibit_number} (
    id SERIAL PRIMARY KEY,
    input_value DECIMAL(6,2), -- Row identifier (stand %, moisture %, etc.)
    stage_or_condition VARCHAR(30), -- Column identifier (growth stage, etc.)
    output_value DECIMAL(8,4), -- Chart value (potential %, factor, etc.)
    interpolation_group VARCHAR(50), -- For grouping interpolation ranges
    metadata JSONB, -- Additional chart-specific data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_lookup_{exhibit}_input_stage ON lookup_table_{exhibit_number}(input_value, stage_or_condition);
```

### Chart Data Loading Structure

```json
{
  "chartDataLoader": {
    "exhibit11": {
      "source": "usda_handbook_exhibit_11", 
      "format": "csv_matrix",
      "validation": {
        "rowRange": [0, 100],
        "columnCount": 10,
        "valueRange": [0, 100],
        "interpolationRequired": true
      }
    },
    "exhibit17": {
      "source": "usda_handbook_exhibit_17",
      "format": "key_value_pairs", 
      "validation": {
        "earWeight": 5.0,
        "shelledWeightRange": [2.8, 4.4],
        "factorRange": [0.70, 1.10]
      }
    }
  }
}
```

## Row Width Conversion Table (Exhibit 10)

```json
{
  "exhibit10_rowWidthFactors": {
    "name": "Row Length Factors",
    "usage": "samplingCalculation_allMethods",
    "description": "Converts row width to sample row length for various sample sizes",
    "structure": {
      "rowWidthCm": "plantingRowSpacing",
      "rowLength_1_250_hectare": "lengthForStandardSample",
      "rowLength_1_2500_hectare": "lengthForSmallSample",
      "rowLength_1_5000_hectare": "lengthForSilageSample"
    },
    "dataSchema": {
      "rowWidthCm": "INTEGER", // 35-105 cm typical
      "length_1_250_ha_metres": "DECIMAL(5,1)",
      "length_1_2500_ha_metres": "DECIMAL(4,1)", 
      "length_1_5000_ha_metres": "DECIMAL(4,1)"
    },
    "calculationFormula": {
      "sampleAreaM2": "sampleAreaHa * 10000",
      "rowLengthM": "sampleAreaM2 / rowWidthM"
    },
    "metricConversion": "Critical for Zimbabwe implementation"
  }
}
```

## Table Access Pattern for Developers

```javascript
// Standard lookup pattern for all tables
class LookupTableManager {
  
  async lookupValue(exhibitNumber, inputValue, stage, interpolate = true) {
    const query = `
      SELECT output_value 
      FROM lookup_table_${exhibitNumber} 
      WHERE input_value = $1 AND stage_or_condition = $2
    `;
    
    const result = await db.query(query, [inputValue, stage]);
    
    if(result.rows.length > 0) {
      return result.rows[0].output_value;
    }
    
    if(interpolate) {
      return this.interpolateValue(exhibitNumber, inputValue, stage);
    }
    
    throw new Error(`No value found for ${inputValue} at ${stage} in exhibit ${exhibitNumber}`);
  }
  
  async interpolateValue(exhibitNumber, inputValue, stage) {
    // Find surrounding values for interpolation
    const surroundingQuery = `
      SELECT input_value, output_value
      FROM lookup_table_${exhibitNumber}
      WHERE stage_or_condition = $1
      AND input_value <= $2
      ORDER BY input_value DESC
      LIMIT 1
    `;
    
    // Implementation continues with linear interpolation logic
  }
}
```

## Critical Implementation Notes

1. **Data Precision**: All lookup tables require high precision decimal storage due to interpolation requirements
2. **Interpolation Logic**: Linear interpolation is required for all charts when exact values aren't found
3. **Metric Conversion**: All imperial measurements in original charts must be converted to metric equivalents
4. **Validation Rules**: Each table needs input validation to prevent lookup errors
5. **Performance**: Indexed access patterns critical for mobile app responsiveness
6. **Offline Storage**: All tables must be downloadable for offline assessment capability
7. **Version Control**: Tables need versioning for when USDA updates handbook standards
