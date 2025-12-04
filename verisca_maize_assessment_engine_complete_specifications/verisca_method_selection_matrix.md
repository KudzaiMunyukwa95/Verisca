# Verisca Maize Assessment Engine: Complete Digital Methodology

## 1. METHOD SELECTION MATRIX

### Primary Assessment Method Selection Logic

```json
{
  "methodSelectionMatrix": {
    "standReduction": {
      "growthStageRange": ["emergence", "10thLeaf", "11thLeaf", "tasseled", "silked", "milk"],
      "applicablePerils": [
        "drought", "flooding", "coldDamage", "heatStress", "disease", 
        "pestDamage", "nutrientDeficiency", "herbicideDamage", 
        "mechanicalDamage", "poorGermination", "irregularGermination"
      ],
      "requiredSamplingMethod": {
        "sampleSize": "1/250_hectare",
        "minimumSamples": 3,
        "additionalSamplesRule": "plus_1_per_16_hectares"
      },
      "requiredDataInputs": [
        "rowWidthCm", "fieldAreaHectares", "normalPlantPopulation", 
        "survivingPlantCount", "growthStageAtDamage", "baseYieldTonnesHa"
      ],
      "requiredCalculations": [
        "percentStand", "percentPotential", "appraisalPerSample", "finalAppraisal"
      ],
      "requiredCharts": [
        "exhibit11_emergenceTo10thLeaf", "exhibit12_11thLeafToTasseled"
      ]
    },
    
    "hailDamage": {
      "growthStageRange": ["7thLeaf", "8thLeaf", "9thLeaf", "10thLeaf", "11thLeaf", "tasseled", "silked", "milk"],
      "applicablePerils": ["hailDamage"],
      "requiredSamplingMethod": {
        "sampleSize": "1/250_hectare",
        "minimumSamples": 3,
        "additionalSamplesRule": "plus_1_per_16_hectares",
        "specialRequirement": "7_day_delay_after_damage"
      },
      "requiredDataInputs": [
        "rowWidthCm", "fieldAreaHectares", "directDamageMetrics", 
        "indirectDamageMetrics", "defoliationPercentage", "crippleEvaluation"
      ],
      "requiredCalculations": [
        "directDamage", "indirectDamage", "totalDamage", "standReduction", 
        "crippleDamage", "earDamage", "defoliationDamage"
      ],
      "requiredCharts": [
        "exhibit13_hailStandReduction7thTo10thLeaf", 
        "exhibit14_hailStandReduction11thToTasseled",
        "exhibit15_leafLossChart", "exhibit16_stageModification"
      ]
    },
    
    "maturityLineWeight": {
      "growthStageRange": ["milk", "lateMilk", "softDough", "earlyDent"],
      "applicablePerils": ["allPerilsAtMilkStage"],
      "requiredSamplingMethod": {
        "sampleSize": "conditional",
        "sampleSizeLogic": {
          "if_yield_le_5_tonnes_ha": "1/250_hectare",
          "if_yield_gt_5_tonnes_ha": "1/2500_hectare"
        }
      },
      "requiredDataInputs": [
        "earSampleWeight", "maturityStageDistribution", 
        "moistureContent", "fieldAreaHectares"
      ],
      "requiredCalculations": [
        "stageWeightMultiplier", "matureProductionEquivalent", "moistureAdjustment"
      ],
      "requiredCharts": ["maturityLineFactors", "exhibit26_kernelCharacteristics"]
    },
    
    "weightMethod": {
      "growthStageRange": ["dent", "lateDent", "nearlyMature", "fullyMature"],
      "applicablePerils": ["allPerilsPostPhysiologicalMaturity"],
      "moistureRequirement": "below_40_percent",
      "requiredSamplingMethod": {
        "sampleSize": "conditional",
        "sampleSizeLogic": {
          "if_yield_le_5_tonnes_ha": "1/250_hectare",
          "if_yield_gt_5_tonnes_ha": "1/2500_hectare"
        }
      },
      "requiredDataInputs": [
        "earWeight", "shellingPercentage", "testWeight", 
        "moistureContent", "fieldAreaHectares"
      ],
      "requiredCalculations": [
        "productionCalculation", "shellingFactor", "qualityAdjustment", "finalYield"
      ],
      "requiredCharts": [
        "exhibit17_shellingPercentageFactors", 
        "exhibit23_moistureAdjustmentFactors",
        "exhibit24_testWeightAndPackFactors"
      ]
    },
    
    "tonnageMethod": {
      "growthStageRange": ["milk", "lateMilk", "softDough", "earlyDent", "dent", "maturity"],
      "applicablePerils": ["silageProduction"],
      "requiredSamplingMethod": {
        "sampleSize": "conditional",
        "sampleSizeLogic": {
          "if_uniform_high_tonnage": "1/5000_hectare",
          "if_other_silage": "1/2500_hectare"
        }
      },
      "requiredDataInputs": [
        "freshWeight", "moistureContent", "cuttingHeight", "fieldAreaHectares"
      ],
      "requiredCalculations": [
        "tonnageProduction", "moistureAdjustment", "grainDeficientAdjustment"
      ],
      "requiredCharts": [
        "exhibit21_silageMoistureFactors", 
        "exhibit22_grainDeficientSilageFactors"
      ]
    }
  }
}
```

### Growth Stage-Based Method Decision Tree

```json
{
  "growthStageMethodSelection": {
    "preEmergence": {
      "primaryMethod": "standReduction",
      "specialCase": "nonEmergedSeed",
      "deferralRule": "defer_until_emergence_determination_possible"
    },
    "emergence_to_6thLeaf": {
      "primaryMethod": "standReduction",
      "allowedMethods": ["standReduction"],
      "charts": ["exhibit11_emergenceTo10thLeaf"]
    },
    "7thLeaf_to_10thLeaf": {
      "primaryMethod": "standReduction",
      "allowedMethods": ["standReduction", "hailDamage"],
      "charts": ["exhibit11_emergenceTo10thLeaf", "exhibit13_hailStandReduction"]
    },
    "11thLeaf_to_tasseled": {
      "primaryMethod": "standReduction", 
      "allowedMethods": ["standReduction", "hailDamage"],
      "charts": ["exhibit12_11thLeafToTasseled", "exhibit14_hailStandReduction"]
    },
    "silked_to_milk": {
      "primaryMethod": "standReduction",
      "calculationRule": "oneToOneStandReduction",
      "allowedMethods": ["standReduction", "hailDamage"]
    },
    "milk_to_40percentMoisture": {
      "primaryMethod": "maturityLineWeight",
      "allowedMethods": ["maturityLineWeight", "tonnageMethod"],
      "deferralPreference": "defer_to_weight_method_if_possible"
    },
    "below_40percentMoisture": {
      "primaryMethod": "weightMethod",
      "allowedMethods": ["weightMethod", "tonnageMethod"]
    }
  }
}
```
