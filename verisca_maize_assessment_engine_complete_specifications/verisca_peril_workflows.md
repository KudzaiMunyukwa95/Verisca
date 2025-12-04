# 2. PERIL-BY-PERIL WORKFLOW MAP

## Drought (Insufficient Soil Moisture)

### Workflow Steps
```json
{
  "droughtAssessmentWorkflow": {
    "step1_fieldInspection": {
      "action": "Conduct general field survey",
      "measurements": [
        "soilMoistureLevel", "plantWiltingStatus", "leafRollingObservation",
        "lowerLeafCondition", "rootZoneInspection"
      ],
      "evidenceCapture": [
        "geotaggedPhotos_plantWilting", "geotaggedPhotos_soilCondition",
        "geotaggedPhotos_leafRolling", "fieldOverviewVideo"
      ]
    },
    "step2_growthStageIdentification": {
      "action": "Determine current growth stage",
      "method": "leafCountMethod_or_nodeIdentification",
      "charts": ["exhibit25_stageCharacteristics"],
      "specialCases": {
        "preEmergence": "assess_nonEmergedSeed",
        "postTasseled": "assess_pollinationImpact"
      }
    },
    "step3_methodSelection": {
      "logic": "SELECT method FROM methodSelectionMatrix WHERE growthStage = current_stage AND peril = 'drought'",
      "primaryMethod": "standReduction",
      "specialModifications": [
        "noPollinationModification", "poorPollinationModification", 
        "severelyDroughtStuntedModification", "permanentWiltModification"
      ]
    },
    "step4_sampling": {
      "sampleGeneration": "generateRandomSamplingPoints(fieldBoundary, minimumSamples)",
      "measurements": [
        "rowWidth", "normalPlantPopulation", "survivingPlantCount",
        "plantHeight", "leafCondition", "rootDevelopment"
      ],
      "qualityChecks": [
        "validateSampleRepresentativeness", "checkSampleSpacing", 
        "verifyMinimumSampleCount"
      ]
    },
    "step5_specialCaseEvaluation": {
      "permanentWiltCheck": {
        "criteria": [
          "leavesRolledThroughoutNight", "lowerLeavesDryAndBrittle",
          "plantWillNotRecoverWithMoisture"
        ],
        "action": "IF permanent_wilt THEN enter_zero_appraisal"
      },
      "noPollinationCheck": {
        "criteria": [
          "noEarShoots_pollinationComplete", "blistersCob_enlarged",
          "silkEatenByInsects_belowHusk"
        ],
        "action": "IF no_pollination THEN enter_zero_appraisal"
      }
    },
    "step6_calculations": {
      "standReductionCalculation": "calculateStandReduction(survivingPlants, normalPopulation)",
      "potentialLookup": "lookupPotentialPercentage(standPercentage, growthStage)",
      "yieldAppraisal": "calculateYieldAppraisal(potentialPercentage, baseYield)",
      "finalAppraisal": "averageAllSamples(sampleAppraisals)"
    },
    "step7_qualityAdjustments": {
      "moistureAdjustment": "applyMoistureFactors_if_applicable",
      "testWeightAdjustment": "applyTestWeightFactors_if_applicable"
    },
    "step8_documentation": {
      "required": [
        "growthStageAtDamage", "weatherConditionsAtInspection",
        "soilType", "irrigationStatus", "plantPopulationCounts",
        "detailedCalculations", "photographicEvidence"
      ]
    }
  }
}
```

## Hail Damage

### Workflow Steps
```json
{
  "hailDamageWorkflow": {
    "step1_delayRequirement": {
      "rule": "DELAY assessment minimum 7 days after hail damage",
      "reason": "Allow accurate damage assessment development"
    },
    "step2_damageTypeIdentification": {
      "directDamageTypes": [
        "standReduction", "cripplePlants", "earDamage", "stalkDamage"
      ],
      "indirectDamageTypes": ["defoliation"]
    },
    "step3_directDamageAssessment": {
      "standReduction": {
        "method": "countDestroyedPlants",
        "charts": ["exhibit13_7thTo10thLeaf", "exhibit14_11thToTasseled"],
        "calculation": "deadPlants / totalPlants * 100"
      },
      "crippledPlants": {
        "definition": "plants_grow_normal_height_but_no_harvestable_ear",
        "evaluation": "individualPlantAssessment",
        "calculation": "evaluateCrippleContribution(crippleCount, averageEarEquivalent)",
        "example": "IF 3_ears_needed_for_1_average THEN cripple_factor = 0.67"
      },
      "earDamage": {
        "sampleSize": "10_consecutive_representative_plants",
        "measurement": "countDamagedKernels / totalKernels",
        "calculation": "earDamagePercentage"
      },
      "stalkDamage": {
        "assessment": "evaluateStalkBruising",
        "rule": "DO_NOT_count_as_destroyed_until_actually_fallen",
        "deferral": "defer_if_considerable_bruising_evident"
      }
    },
    "step4_indirectDamageAssessment": {
      "defoliationEvaluation": {
        "step1": "selectRepresentativePlants",
        "step2": "removeExposedLeavesAtDamageTime", 
        "step3": "determinePercentLeafAreaDestroyed_per_leaf",
        "step4": "totalPercentages",
        "step5": "divideByNumberOfLeaves_for_average",
        "step6": "applyToLeafLossChart"
      },
      "stageModification": {
        "condition": "shortSeasonVarieties_lessThan19to21Leaves",
        "method": "determineUltimateLeafNumber_byPlantDissection",
        "chart": "exhibit16_stageModification",
        "rule": "IF cannot_determine_defer_until_determinable"
      }
    },
    "step5_totalDamageCalculation": {
      "formula": "totalDamage = directDamage + indirectDamage",
      "directDamage": "standReduction% + crippleDamage% + earDamage%",
      "indirectDamage": "leafLossChartLookup(averageDefoliationPercentage)"
    },
    "step6_evidenceCapture": {
      "required": [
        "overallFieldCondition", "representativePlantDamage",
        "leafDefoliationExamples", "earDamageExamples",
        "crippledPlantExamples", "stalkDamageEvidence"
      ]
    }
  }
}
```

## Heat Stress / No Pollination

### Workflow Steps  
```json
{
  "heatStressPollinationWorkflow": {
    "step1_pollinationStatusCheck": {
      "timing": "duringOrAfterPollinationPeriod",
      "indicators": [
        "tasselFullyExtended", "earShootCondition", "silkCondition",
        "pollenShedStatus", "temperatureHistory"
      ]
    },
    "step2_noPollinationCriteria": {
      "withEarShoots": {
        "pollinationEnded": "blistersCob_enlarged_wartLike",
        "pollinationInProgress": "blistersCob_notEnlarged AND allSilk_eatenByInsects"
      },
      "withoutEarShoots": {
        "pollinationInProgressOrEnded": "obvious_condition", 
        "pollinationNotBegun": "tasselExposed AND earBud_lessThan2Inches"
      }
    },
    "step3_poorPollinationAssessment": {
      "condition": "partialPollinationEvident",
      "method": "individualEarEvaluation",
      "calculation": "IF 3_ears_equal_1_normal THEN count_only_1/3_of_plants",
      "rule": "barrenStalks_not_counted_as_surviving"
    },
    "step4_appraisalMethod": {
      "noPollinationAppraisal": "enter_ZERO_for_affected_acreage",
      "poorPollinationAppraisal": "standReductionMethod_with_earAdjustment"
    },
    "step5_documentation": {
      "required": [
        "temperatureRecords", "pollinationTimeline", 
        "earShootCondition", "silkCondition", "tasselCondition",
        "insectDamageEvidence", "droughtStressIndicators"
      ]
    }
  }
}
```

## Flooding / Excessive Moisture

### Workflow Steps
```json
{
  "floodingWorkflow": {
    "step1_floodingAssessment": {
      "measurements": [
        "floodDuration", "floodDepth", "waterStandingTime",
        "soilSaturationLevel", "plantSubmersionTime"
      ],
      "evidenceCapture": [
        "floodMarkPhotos", "fieldConditionPhotos", 
        "plantDamagePhotos", "soilConditionPhotos"
      ]
    },
    "step2_damageEvaluation": {
      "drowning": "plantsKilled_by_waterSubmersion",
      "rootDamage": "rootSystemDamage_from_saturation",
      "diseaseSecondary": "secondaryDiseaseFrom_excessiveMoisture",
      "nutrientLeaching": "nutrientLoss_from_soilSaturation"
    },
    "step3_methodSelection": {
      "primaryMethod": "standReduction",
      "specialConsiderations": [
        "deferralIfRecoveryPossible", "secondaryDiseaseMonitoring"
      ]
    },
    "step4_samplingAndCalculation": {
      "method": "standardStandReductionProtocol",
      "adjustments": "accountFor_potentialRecovery"
    }
  }
}
```

## Disease Assessment

### Workflow Steps
```json
{
  "diseaseAssessmentWorkflow": {
    "step1_diseaseIdentification": {
      "leafDiseases": [
        "northernCornLeafBlight", "southernCornLeafBlight", 
        "commonRust", "southernRust", "grayLeafSpot"
      ],
      "stalkDiseases": [
        "stalkRot", "charcoalRot", "antracnose"
      ],
      "rootDiseases": [
        "rootRot", "nematodeDamage"
      ],
      "earDiseases": [
        "gibberella", "diplodia", "fusarium"
      ]
    },
    "step2_severityAssessment": {
      "leafDiseaseSeverity": "percentLeafAreaAffected",
      "stalkDiseaseSeverity": "lodgingPotential_and_harvestability",
      "rootDiseaseSeverity": "plantVigor_and_standLoss",
      "earDiseaseSeverity": "grainQuality_and_yieldImpact"
    },
    "step3_methodSelection": {
      "earlyToMidSeason": "standReductionMethod",
      "lateSeasonEarDiseases": "qualityAdjustmentMethod"
    },
    "step4_evidenceRequirements": {
      "diseasePhotos": "closeUpSymptoms_and_overallFieldCondition",
      "samplingForConfirmation": "collectSamples_for_labConfirmation_if_needed"
    }
  }
}
```

## Pest Damage Assessment

### Workflow Steps
```json
{
  "pestDamageWorkflow": {
    "step1_pestIdentification": {
      "rootworms": "rootSystemDamage_and_lodging",
      "cornBorer": "stalkTunneling_and_earDamage", 
      "armyworm": "foliageConsumption",
      "cutworm": "plantCutting_at_soilLevel",
      "aphids": "plantWeakening_and_virusTransmission",
      "wildlife": "deer_bird_rodent_damage"
    },
    "step2_damageQuantification": {
      "standsLoss": "plantsKilled_or_severelyDamaged",
      "foliageLoss": "percentDefoliation", 
      "rootDamage": "rootPruning_scale_0to3",
      "stalkDamage": "tunneling_severity_and_lodgingPotential",
      "earDamage": "kernelLoss_and_qualityReduction"
    },
    "step3_methodApplication": {
      "standLoss": "standReductionMethod",
      "foliageReduction": "hailDamageMethod_defoliationProtocol",
      "earDamage": "qualityAdjustmentMethod"
    }
  }
}
```

## Cold Weather Damage

### Workflow Steps
```json
{
  "coldDamageWorkflow": {
    "step1_freezeEventDocumentation": {
      "freezeDate": "dateOfDamagingFreeze",
      "temperatureReached": "minimumTemperatureRecorded",
      "freezeDuration": "hoursBelow_damagingThreshold",
      "plantStageAtFreeze": "growthStageWhenFreezeOccurred"
    },
    "step2_damageAssessment": {
      "leafDamage": "percentLeafAreaKilled",
      "stalkDamage": "stalkFreezeDamage",
      "earDamage": "kernelDevelopmentArrested",
      "pollinationImpact": "pollenViability_reduced"
    },
    "step3_specialModification": {
      "earlyFreezeModification": "applyEarlyFreezeFactors",
      "maturityStageAdjustment": "useStageAtFreeze_not_currentStage"
    }
  }
}
```

## Poor Germination / Emergence Failure

### Workflow Steps
```json
{
  "germinationFailureWorkflow": {
    "step1_causeIdentification": {
      "soilConditions": [
        "soilTemperatureTooLow", "soilMoistureTooLow_or_tooHigh",
        "soilCrusting", "plantingDepthProblems"
      ],
      "seedQuality": [
        "poorSeedViability", "seedDamage", "fungalAttack"
      ]
    },
    "step2_emergenceEvaluation": {
      "plantedSeedRate": "seedsPerHectare_planted",
      "emergedPopulation": "plantsPerHectare_emerged",
      "germinationPercentage": "emerged / planted * 100"
    },
    "step3_methodApplication": {
      "primaryMethod": "standReductionMethod",
      "specialCase": "nonEmergedSeed_deferralRules"
    }
  }
}
```
