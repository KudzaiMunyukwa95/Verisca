# 4. FORMULAS CONVERTED TO PSEUDO-CODE

## Stand Reduction Calculation Engine

```javascript
class StandReductionCalculator {

  calculateStandReduction(sampleData, growthStage, baseYield) {
    const results = {
      percentStand: 0,
      percentPotential: 0,
      appraisalPerSample: 0,
      samples: []
    };

    // Process each sample
    for(const sample of sampleData) {
      const sampleResult = this.processSingleSample(sample, growthStage, baseYield);
      results.samples.push(sampleResult);
    }

    // Calculate final appraisal as average
    results.finalAppraisal = this.calculateAverageAppraisal(results.samples);
    
    return results;
  }

  processSingleSample(sample, growthStage, baseYield) {
    // Step 1: Calculate percent of stand
    const percentStand = (sample.survivingPlants / sample.normalPlantPopulation) * 100;
    const roundedPercentStand = this.roundToNearest5Percent(percentStand);

    // Step 2: Lookup percent of potential based on growth stage
    const percentPotential = this.lookupPercentPotential(roundedPercentStand, growthStage);

    // Step 3: Calculate appraisal for this sample
    const appraisalPerSample = (percentPotential / 100) * baseYield;

    return {
      sampleNumber: sample.sampleNumber,
      normalPlantPopulation: sample.normalPlantPopulation,
      survivingPlants: sample.survivingPlants,
      percentStand: percentStand,
      roundedPercentStand: roundedPercentStand,
      percentPotential: percentPotential,
      appraisalPerSample: Math.round(appraisalPerSample * 10) / 10 // Round to tenths
    };
  }

  lookupPercentPotential(standPercentage, growthStage) {
    // Route to appropriate chart based on growth stage
    if(this.isEarlyStage(growthStage)) {
      return this.lookupExhibit11(standPercentage, growthStage);
    } else if(this.isMidStage(growthStage)) {
      return this.lookupExhibit12(standPercentage, growthStage);
    } else if(this.isLateStage(growthStage)) {
      // Silked to milk stage: one-to-one basis
      return standPercentage;
    }
  }

  lookupExhibit11(standPercentage, growthStage) {
    // Emergence through 10th Leaf Stages Chart
    const chartData = this.getExhibit11Data();
    return this.interpolateChartValue(chartData, standPercentage, growthStage);
  }

  lookupExhibit12(standPercentage, growthStage) {
    // 11th Leaf through Tasseled Stages Chart  
    const chartData = this.getExhibit12Data();
    return this.interpolateChartValue(chartData, standPercentage, growthStage);
  }

  interpolateChartValue(chartData, standPercentage, growthStage) {
    // Find appropriate row and column in chart
    const stageColumn = this.getStageColumn(growthStage);
    const standRows = this.findSurroundingStandPercentages(chartData, standPercentage);

    if(standRows.exact) {
      return chartData[standRows.exact][stageColumn];
    }

    // Linear interpolation between surrounding values
    const lowerValue = chartData[standRows.lower][stageColumn];
    const upperValue = chartData[standRows.upper][stageColumn];
    const interpolationFactor = (standPercentage - standRows.lowerStand) / 
                               (standRows.upperStand - standRows.lowerStand);
    
    const interpolatedValue = lowerValue + (interpolationFactor * (upperValue - lowerValue));
    return Math.round(interpolatedValue); // Round to whole percent
  }

  roundToNearest5Percent(value) {
    return Math.round(value / 5) * 5;
  }

  calculateAverageAppraisal(samples) {
    const total = samples.reduce((sum, sample) => sum + sample.appraisalPerSample, 0);
    return Math.round((total / samples.length) * 10) / 10; // Round to tenths
  }
}
```

## Hail Damage Calculation Engine

```javascript
class HailDamageCalculator {

  calculateHailDamage(hailData, growthStage, baseYield) {
    const directDamage = this.calculateDirectDamage(hailData, growthStage);
    const indirectDamage = this.calculateIndirectDamage(hailData, growthStage);
    
    const totalDamagePercent = directDamage.totalPercent + indirectDamage.defoliationPercent;
    const remainingPotential = 100 - totalDamagePercent;
    const finalAppraisal = (remainingPotential / 100) * baseYield;

    return {
      directDamage: directDamage,
      indirectDamage: indirectDamage,
      totalDamagePercent: totalDamagePercent,
      remainingPotential: Math.max(0, remainingPotential),
      finalAppraisal: Math.round(finalAppraisal * 10) / 10
    };
  }

  calculateDirectDamage(hailData, growthStage) {
    const standReductionDamage = this.calculateHailStandReduction(
      hailData.destroyedPlants, hailData.totalPlants, growthStage
    );
    
    const crippleDamage = this.calculateCrippleDamage(
      hailData.crippleEvaluation
    );
    
    const earDamage = this.calculateEarDamage(
      hailData.earDamageAssessment
    );
    
    const stalkDamage = this.calculateStalkDamage(
      hailData.stalkDamageAssessment
    );

    return {
      standReductionPercent: standReductionDamage,
      cripplePercent: crippleDamage, 
      earPercent: earDamage,
      stalkPercent: stalkDamage,
      totalPercent: standReductionDamage + crippleDamage + earDamage + stalkDamage
    };
  }

  calculateHailStandReduction(destroyedPlants, totalPlants, growthStage) {
    const standReductionPercent = (destroyedPlants / totalPlants) * 100;
    
    // Use hail-specific charts (Exhibits 13 & 14)
    if(this.isEarlyToMidStage(growthStage)) {
      return this.lookupExhibit13(standReductionPercent, growthStage);
    } else if(this.isMidToLateStage(growthStage)) {
      return this.lookupExhibit14(standReductionPercent, growthStage);
    } else {
      // Silked to milk stage: one-to-one basis
      return standReductionPercent;
    }
  }

  calculateCrippleDamage(crippleEvaluation) {
    // Individual evaluation of crippled plants
    const crippleFactor = this.evaluateCrippleContribution(crippleEvaluation);
    const cripplePercent = (crippleEvaluation.crippleCount / crippleEvaluation.totalPlants) * 100;
    
    return cripplePercent * crippleFactor;
  }

  evaluateCrippleContribution(evaluation) {
    // Example: if 3 crippled ears = 1 normal ear, factor = 0.67 (2/3 damage)
    const normalEarEquivalent = evaluation.normalEarEquivalent || 1;
    const crippledEarsPerNormal = evaluation.crippledEarsPerNormal || 1;
    
    return (crippledEarsPerNormal - 1) / crippledEarsPerNormal;
  }

  calculateEarDamage(earAssessment) {
    // Based on 10 consecutive representative plants
    const totalKernels = earAssessment.totalKernels;
    const damagedKernels = earAssessment.damagedKernels;
    
    return (damagedKernels / totalKernels) * 100;
  }

  calculateIndirectDamage(hailData, growthStage) {
    const defoliationData = hailData.defoliationAssessment;
    const averageDefoliation = this.calculateAverageDefoliation(defoliationData);
    
    // Apply stage modification if needed for short-season varieties
    const modifiedStage = this.applyStageModification(growthStage, defoliationData.ultimateLeafCount);
    
    // Lookup defoliation damage from Leaf Loss Chart (Exhibit 15)
    const defoliationPercent = this.lookupLeafLossChart(averageDefoliation, modifiedStage);
    
    return {
      averageDefoliation: averageDefoliation,
      modifiedStage: modifiedStage,
      defoliationPercent: defoliationPercent
    };
  }

  calculateAverageDefoliation(defoliationData) {
    const totalDefoliation = defoliationData.leafAssessments.reduce(
      (sum, leaf) => sum + leaf.percentDestroyed, 0
    );
    
    return totalDefoliation / defoliationData.leafAssessments.length;
  }

  lookupLeafLossChart(defoliationPercent, growthStage) {
    const leafLossChart = this.getExhibit15Data();
    return this.interpolateChartValue(leafLossChart, defoliationPercent, growthStage);
  }
}
```

## Maturity Line Weight Method

```javascript
class MaturityLineWeightCalculator {

  calculateMaturityLineWeight(weightData, sampleArea) {
    const stageDistribution = this.categorizeEarsByMaturity(weightData.ears);
    const productionByStage = this.calculateProductionByStage(stageDistribution, sampleArea);
    const totalProduction = this.sumStageProductions(productionByStage);
    
    return {
      stageDistribution: stageDistribution,
      productionByStage: productionByStage,
      totalProductionTonnesPerHa: Math.round(totalProduction * 10) / 10
    };
  }

  categorizeEarsByMaturity(ears) {
    const stages = {
      stage1: { ears: [], totalWeight: 0 }, // 0-25% maturity line
      stage2: { ears: [], totalWeight: 0 }, // 25-50% maturity line  
      stage3: { ears: [], totalWeight: 0 }, // 50-75% maturity line
      stage4: { ears: [], totalWeight: 0 }, // 75-100% maturity line
      stage5: { ears: [], totalWeight: 0 }  // 100% mature (black layer visible)
    };

    for(const ear of ears) {
      const maturityStage = this.determineMaturityStage(ear);
      stages[maturityStage].ears.push(ear);
      stages[maturityStage].totalWeight += ear.weight;
    }

    return stages;
  }

  determineMaturityStage(ear) {
    // Examine kernel development to determine maturity line position
    const maturityLinePosition = ear.maturityLinePosition; // 0-100%
    
    if(maturityLinePosition <= 25) return 'stage1';
    if(maturityLinePosition <= 50) return 'stage2';
    if(maturityLinePosition <= 75) return 'stage3';
    if(maturityLinePosition < 100) return 'stage4';
    return 'stage5';
  }

  calculateProductionByStage(stageDistribution, sampleAreaHectares) {
    const conversionFactors = this.getMaturityLineConversionFactors();
    const sampleMultiplier = 1 / sampleAreaHectares; // Convert to per hectare
    
    const productionByStage = {};
    
    for(const [stage, data] of Object.entries(stageDistribution)) {
      if(data.totalWeight > 0) {
        const matureEquivalent = data.totalWeight * conversionFactors[stage];
        productionByStage[stage] = matureEquivalent * sampleMultiplier;
      } else {
        productionByStage[stage] = 0;
      }
    }
    
    return productionByStage;
  }

  getMaturityLineConversionFactors() {
    // Factors to convert stage weight to mature production equivalent
    return {
      stage1: 2.5,  // 0-25% mature
      stage2: 2.0,  // 25-50% mature
      stage3: 1.5,  // 50-75% mature
      stage4: 1.2,  // 75-100% mature
      stage5: 1.0   // Fully mature
    };
  }
}
```

## Weight Method Calculator

```javascript
class WeightMethodCalculator {

  calculateWeightMethod(weightData, sampleArea, qualityFactors) {
    // Step 1: Calculate raw production
    const rawProduction = this.calculateRawProduction(weightData, sampleArea);
    
    // Step 2: Apply shelling factor
    const shellingFactor = this.calculateShellingFactor(weightData.shellingTest);
    const shelledProduction = rawProduction * shellingFactor;
    
    // Step 3: Apply quality adjustments
    const adjustedProduction = this.applyQualityAdjustments(shelledProduction, qualityFactors);
    
    return {
      rawProductionTonnesPerHa: Math.round(rawProduction * 10) / 10,
      shellingFactor: shellingFactor,
      shelledProductionTonnesPerHa: Math.round(shelledProduction * 10) / 10,
      qualityAdjustments: qualityFactors,
      finalProductionTonnesPerHa: Math.round(adjustedProduction * 10) / 10
    };
  }

  calculateRawProduction(weightData, sampleAreaHectares) {
    const sampleMultiplier = 1 / sampleAreaHectares;
    const averageWeight = weightData.totalWeight / weightData.sampleCount;
    
    // Convert to tonnes per hectare
    return (averageWeight / 1000) * sampleMultiplier;
  }

  calculateShellingFactor(shellingTest) {
    if(shellingTest.method === 'direct') {
      // Direct measurement: 5 lb sample shelled and weighed
      const shellingPercentage = (shellingTest.shelledWeight / shellingTest.earWeight) * 100;
      return this.getShellingFactor(shellingPercentage);
    } else {
      // Use Exhibit 17 lookup table
      return this.lookupExhibit17(shellingTest.earWeight, shellingTest.shelledWeight);
    }
  }

  getShellingFactor(shellingPercentage) {
    // Standard: 80% shelling = 1.00 factor
    return shellingPercentage / 80.0;
  }

  lookupExhibit17(earWeight, shelledWeight) {
    const exhibit17Data = this.getExhibit17Data();
    
    // Find matching weights in chart or interpolate
    for(const entry of exhibit17Data) {
      if(entry.earWeight === earWeight && entry.shelledWeight === shelledWeight) {
        return entry.shellingFactor;
      }
    }
    
    // If not exact match, interpolate
    return this.interpolateShellingFactor(earWeight, shelledWeight, exhibit17Data);
  }
}
```

## Quality Adjustment Calculator

```javascript
class QualityAdjustmentCalculator {

  applyQualityAdjustments(baseProduction, qualityData) {
    let adjustedProduction = baseProduction;
    const adjustments = [];

    // Moisture adjustment
    if(qualityData.moistureContent !== 12.5) { // Standard moisture
      const moistureFactor = this.getMoistureFactor(qualityData.moistureContent);
      adjustedProduction *= moistureFactor;
      adjustments.push({
        type: 'moisture',
        factor: moistureFactor,
        description: `Adjusted for ${qualityData.moistureContent}% moisture`
      });
    }

    // Test weight adjustment  
    if(qualityData.testWeight) {
      const testWeightFactor = this.getTestWeightFactor(qualityData.testWeight);
      adjustedProduction *= testWeightFactor;
      adjustments.push({
        type: 'testWeight',
        factor: testWeightFactor,
        description: `Adjusted for test weight ${qualityData.testWeight} kg/hl`
      });
    }

    // Foreign material discount
    if(qualityData.foreignMaterial > 2.0) { // Standard allowance
      const fmDiscount = this.getForeignMaterialDiscount(qualityData.foreignMaterial);
      adjustedProduction *= fmDiscount;
      adjustments.push({
        type: 'foreignMaterial',
        factor: fmDiscount,
        description: `Discount for ${qualityData.foreignMaterial}% foreign material`
      });
    }

    // Damage discount
    if(qualityData.damagedKernels > 5.0) { // Grade 1 standard
      const damageDiscount = this.getDamageDiscount(qualityData.damagedKernels);
      adjustedProduction *= damageDiscount;
      adjustments.push({
        type: 'damage',
        factor: damageDiscount,
        description: `Discount for ${qualityData.damagedKernels}% damaged kernels`
      });
    }

    return {
      adjustedProduction: Math.round(adjustedProduction * 10) / 10,
      adjustments: adjustments,
      totalAdjustmentFactor: adjustments.reduce((product, adj) => product * adj.factor, 1.0)
    };
  }

  getMoistureFactor(moistureContent) {
    // Exhibit 23 - Moisture Adjustment Factors
    const exhibit23 = this.getExhibit23Data();
    return this.interpolateTableValue(exhibit23, moistureContent, 'moisture', 'factor');
  }

  getTestWeightFactor(testWeight) {
    // Exhibit 24 - Test Weight and Pack Factors
    const exhibit24 = this.getExhibit24Data();
    return this.interpolateTableValue(exhibit24, testWeight, 'testWeight', 'packFactor');
  }

  getForeignMaterialDiscount(fmPercent) {
    // Standard discount table
    if(fmPercent <= 2.0) return 1.00;
    if(fmPercent <= 3.0) return 0.99;
    if(fmPercent <= 4.0) return 0.98;
    if(fmPercent <= 5.0) return 0.97;
    return 0.95; // Higher than 5%
  }

  getDamageDiscount(damagePercent) {
    // Standard damage discount table
    if(damagePercent <= 5.0) return 1.00;
    if(damagePercent <= 7.0) return 0.98;
    if(damagePercent <= 10.0) return 0.95;
    if(damagePercent <= 15.0) return 0.92;
    return 0.90; // Higher than 15%
  }
}
```

## Tonnage Method Calculator (Silage)

```javascript
class TonnageMethodCalculator {

  calculateSilageProduction(tonnageData, sampleArea, moistureContent) {
    // Step 1: Calculate raw tonnage
    const rawTonnage = this.calculateRawTonnage(tonnageData, sampleArea);
    
    // Step 2: Apply moisture adjustment
    const adjustedTonnage = this.applyMoistureAdjustment(rawTonnage, moistureContent);
    
    // Step 3: Check for grain-deficient silage adjustment
    const grainDeficientAdjustment = this.checkGrainDeficientSilage(tonnageData);
    const finalTonnage = adjustedTonnage * grainDeficientAdjustment.factor;
    
    return {
      rawTonnesPerHa: Math.round(rawTonnage * 10) / 10,
      moistureAdjustedTonnesPerHa: Math.round(adjustedTonnage * 10) / 10,
      grainDeficientAdjustment: grainDeficientAdjustment,
      finalTonnesPerHa: Math.round(finalTonnage * 10) / 10
    };
  }

  calculateRawTonnage(tonnageData, sampleAreaHectares) {
    const sampleMultiplier = 1 / sampleAreaHectares;
    const averageWeight = tonnageData.totalFreshWeight / tonnageData.sampleCount;
    
    // Convert to tonnes per hectare
    return (averageWeight / 1000) * sampleMultiplier;
  }

  applyMoistureAdjustment(tonnage, moistureContent) {
    // Convert to 65% moisture equivalent using Exhibit 21
    const standardMoisture = 65.0;
    
    if(moistureContent === standardMoisture) {
      return tonnage;
    }
    
    const moistureFactor = this.getSilageMoistureFactor(moistureContent);
    return tonnage * moistureFactor;
  }

  getSilageMoistureFactor(moistureContent) {
    // Exhibit 21 - Silage Moisture Factors
    const exhibit21 = this.getExhibit21Data();
    return this.interpolateTableValue(exhibit21, moistureContent, 'moisture', 'factor');
  }

  checkGrainDeficientSilage(tonnageData) {
    if(!tonnageData.grainAssessment) {
      return { factor: 1.0, description: 'No grain assessment available' };
    }
    
    const bushelsPerTon = tonnageData.grainAssessment.bushelsPerHa / tonnageData.tonnesPerHa;
    
    if(bushelsPerTon >= 4.5) {
      return { factor: 1.0, description: 'Normal grain content' };
    }
    
    // Apply grain-deficient factors from Exhibit 22
    const deficientFactor = this.getGrainDeficientFactor(bushelsPerTon);
    return { 
      factor: deficientFactor, 
      description: `Grain-deficient silage: ${bushelsPerTon} bushels/tonne` 
    };
  }

  getGrainDeficientFactor(bushelsPerTon) {
    // Exhibit 22 - Grain-Deficient Silage Factors
    const exhibit22 = this.getExhibit22Data();
    return this.interpolateTableValue(exhibit22, bushelsPerTon, 'bushelsPerTon', 'adjustmentFactor');
  }
}
```

## Universal Helper Functions

```javascript
class CalculationHelpers {

  interpolateTableValue(tableData, inputValue, inputColumn, outputColumn) {
    // Find surrounding values for interpolation
    const sorted = tableData.sort((a, b) => a[inputColumn] - b[inputColumn]);
    
    // Check for exact match
    const exactMatch = sorted.find(row => row[inputColumn] === inputValue);
    if(exactMatch) {
      return exactMatch[outputColumn];
    }
    
    // Find surrounding values
    let lowerRow = null, upperRow = null;
    
    for(let i = 0; i < sorted.length - 1; i++) {
      if(sorted[i][inputColumn] <= inputValue && sorted[i + 1][inputColumn] >= inputValue) {
        lowerRow = sorted[i];
        upperRow = sorted[i + 1];
        break;
      }
    }
    
    if(!lowerRow || !upperRow) {
      throw new Error(`Cannot interpolate value ${inputValue} - outside table range`);
    }
    
    // Linear interpolation
    const factor = (inputValue - lowerRow[inputColumn]) / 
                   (upperRow[inputColumn] - lowerRow[inputColumn]);
    
    const interpolatedValue = lowerRow[outputColumn] + 
                             (factor * (upperRow[outputColumn] - lowerRow[outputColumn]));
    
    return Math.round(interpolatedValue * 1000) / 1000; // Round to 3 decimal places
  }

  roundToNearestTenth(value) {
    return Math.round(value * 10) / 10;
  }

  roundToWholePercent(value) {
    return Math.round(value);
  }
}
```
