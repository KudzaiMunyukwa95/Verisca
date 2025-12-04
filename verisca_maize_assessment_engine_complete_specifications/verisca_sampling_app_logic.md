# 3. SAMPLING RULES CONVERTED TO APP LOGIC

## Sample Size Determination Engine

```javascript
// Sample Size Calculator
class SamplingEngine {
  
  calculateMinimumSamples(fieldAreaHectares) {
    if (fieldAreaHectares >= 0.04 && fieldAreaHectares <= 4.0) {
      return 3;
    }
    // Additional samples: +1 for each additional 16 hectares
    const additionalHectares = fieldAreaHectares - 4.0;
    const additionalSamples = Math.ceil(additionalHectares / 16.0);
    return 3 + Math.max(0, additionalSamples);
  }

  calculateSampleArea(assessmentMethod, expectedYield) {
    const sampleAreas = {
      standReduction: 0.004047,  // 1/250 hectare (fixed)
      
      maturityLineWeight: {
        lowYield: 0.004047,   // 1/250 hectare if ≤5 tonnes/ha
        highYield: 0.0004047  // 1/2500 hectare if >5 tonnes/ha
      },
      
      weightMethod: {
        lowYield: 0.004047,   // 1/250 hectare if ≤5 tonnes/ha  
        highYield: 0.0004047  // 1/2500 hectare if >5 tonnes/ha
      },
      
      tonnageMethod: {
        uniformHighTonnage: 0.0002024,  // 1/5000 hectare
        other: 0.0004047               // 1/2500 hectare
      }
    };

    switch(assessmentMethod) {
      case 'standReduction':
      case 'hailDamage':
        return sampleAreas.standReduction;
        
      case 'maturityLineWeight':
        return expectedYield <= 5.0 ? 
          sampleAreas.maturityLineWeight.lowYield : 
          sampleAreas.maturityLineWeight.highYield;
          
      case 'weightMethod':
        return expectedYield <= 5.0 ? 
          sampleAreas.weightMethod.lowYield : 
          sampleAreas.weightMethod.highYield;
          
      case 'tonnageMethod':
        // Logic to determine if uniform/high tonnage
        return this.isUniformHighTonnage() ? 
          sampleAreas.tonnageMethod.uniformHighTonnage : 
          sampleAreas.tonnageMethod.other;
    }
  }
}
```

## Row Length Calculator

```javascript
class RowLengthCalculator {
  
  calculateRowLength(sampleAreaHectares, rowWidthMetres) {
    // Convert sample area from hectares to square metres
    const sampleAreaM2 = sampleAreaHectares * 10000;
    
    // Calculate required row length
    const rowLengthM = sampleAreaM2 / rowWidthMetres;
    
    // Round to nearest 0.1m for practical measurement
    return Math.round(rowLengthM * 10) / 10;
  }

  validateRowWidth(rowWidthCm) {
    // Convert to metres and validate reasonable range
    const rowWidthM = rowWidthCm / 100;
    
    if (rowWidthM < 0.30 || rowWidthM > 1.50) {
      throw new Error(`Row width ${rowWidthCm}cm is outside normal range (30-150cm)`);
    }
    
    // Round to nearest 2.5cm for standardization
    const roundedCm = Math.round(rowWidthCm / 2.5) * 2.5;
    return roundedCm;
  }
}
```

## GPS Sampling Point Generation

```javascript
class GPSSamplingGenerator {

  generateSamplingPoints(fieldBoundary, assessmentMethod, minimumSamples, rowDirection = null) {
    const samplePoints = [];
    const fieldArea = this.calculatePolygonArea(fieldBoundary);
    
    // Determine actual number of samples needed
    const samplesNeeded = Math.max(minimumSamples, this.calculateMinimumSamples(fieldArea));
    
    switch(this.getSamplingPattern(assessmentMethod)) {
      case 'random':
        return this.generateRandomPoints(fieldBoundary, samplesNeeded);
      case 'systematic':
        return this.generateSystematicGrid(fieldBoundary, samplesNeeded);
      case 'stratified':
        return this.generateStratifiedPoints(fieldBoundary, samplesNeeded);
      case 'insurerSpecific':
        return this.generateInsurerPattern(fieldBoundary, samplesNeeded, this.insurerTemplate);
    }
  }

  generateRandomPoints(fieldBoundary, count) {
    const points = [];
    let attempts = 0;
    const maxAttempts = count * 50;

    while(points.length < count && attempts < maxAttempts) {
      const candidatePoint = this.generateRandomPointInPolygon(fieldBoundary);
      
      if (this.isValidSamplePoint(candidatePoint, points)) {
        points.push({
          id: `sample_${points.length + 1}`,
          latitude: candidatePoint.lat,
          longitude: candidatePoint.lng,
          sampleNumber: points.length + 1,
          distanceFromField边ge: this.calculateDistanceFromEdge(candidatePoint, fieldBoundary)
        });
      }
      attempts++;
    }

    return points;
  }

  isValidSamplePoint(candidatePoint, existingPoints) {
    // Minimum distance between samples (prevent clustering)
    const minimumDistance = 20; // metres
    
    for(const existingPoint of existingPoints) {
      const distance = this.calculateDistance(candidatePoint, existingPoint);
      if(distance < minimumDistance) {
        return false;
      }
    }

    // Must be at least 5m from field edge
    const edgeDistance = this.calculateDistanceFromEdge(candidatePoint, this.fieldBoundary);
    return edgeDistance >= 5;
  }

  generateSystematicGrid(fieldBoundary, samplesNeeded) {
    // Generate evenly spaced grid pattern
    const boundingBox = this.getBoundingBox(fieldBoundary);
    const gridSpacing = this.calculateOptimalGridSpacing(boundingBox, samplesNeeded);
    
    const gridPoints = [];
    for(let lat = boundingBox.south; lat <= boundingBox.north; lat += gridSpacing.lat) {
      for(let lng = boundingBox.west; lng <= boundingBox.east; lng += gridSpacing.lng) {
        const point = {lat, lng};
        if(this.isPointInPolygon(point, fieldBoundary)) {
          gridPoints.push(point);
        }
      }
    }

    // Select subset if more points than needed
    return this.selectBestGridPoints(gridPoints, samplesNeeded);
  }
}
```

## Subfield Splitting Logic

```javascript
class SubfieldManager {

  evaluateSplittingNeeds(fieldAssessment, damageVariability, insuredPreferences) {
    const splittingReasons = [];

    // Rule 1: Variable damage assessment
    if(this.hasSignificantDamageVariability(damageVariability)) {
      splittingReasons.push({
        reason: 'variable_damage',
        description: 'Crop potential appears significantly different within field',
        recommendedSplits: this.identifyDamageZones(damageVariability)
      });
    }

    // Rule 2: Insured destruction request  
    if(insuredPreferences.partialDestruction) {
      splittingReasons.push({
        reason: 'partial_destruction',
        description: 'Insured wishes to destroy portion of field',
        destructionArea: insuredPreferences.destructionBoundary
      });
    }

    return splittingReasons;
  }

  hasSignificantDamageVariability(damageData) {
    // Analyze damage pattern across field
    const damageCoefficient = this.calculateDamageCoefficient(damageData);
    
    // If coefficient of variation > 25%, consider splitting
    return damageCoefficient > 0.25;
  }

  createSubfields(fieldBoundary, splittingCriteria) {
    const subfields = [];

    for(const criteria of splittingCriteria) {
      switch(criteria.reason) {
        case 'variable_damage':
          subfields.push(...this.splitByDamageZones(fieldBoundary, criteria.recommendedSplits));
          break;
        case 'partial_destruction':  
          subfields.push(...this.splitByDestructionArea(fieldBoundary, criteria.destructionArea));
          break;
      }
    }

    // Validate each subfield meets minimum requirements
    return subfields.filter(subfield => this.validateSubfield(subfield));
  }

  validateSubfield(subfield) {
    const minArea = 0.02; // hectares (minimum practical subfield size)
    const area = this.calculatePolygonArea(subfield.boundary);
    
    return area >= minArea;
  }
}
```

## Sample Adequacy Validation

```javascript
class SampleValidation {

  validateSampleAdequacy(samples, fieldCharacteristics, assessmentMethod) {
    const validationResults = {
      isAdequate: true,
      warnings: [],
      errors: []
    };

    // Check minimum sample count
    const minRequired = this.calculateMinimumSamples(fieldCharacteristics.area);
    if(samples.length < minRequired) {
      validationResults.errors.push({
        type: 'insufficient_samples',
        message: `Minimum ${minRequired} samples required, only ${samples.length} collected`,
        severity: 'error'
      });
      validationResults.isAdequate = false;
    }

    // Check sample distribution
    const distributionScore = this.analyzeSampleDistribution(samples, fieldCharacteristics);
    if(distributionScore < 0.7) {
      validationResults.warnings.push({
        type: 'poor_distribution',
        message: 'Samples may not be well distributed across field',
        severity: 'warning',
        score: distributionScore
      });
    }

    // Check edge effects
    const edgeProximity = this.checkEdgeProximity(samples, fieldCharacteristics.boundary);
    if(edgeProximity.tooClose > 0) {
      validationResults.warnings.push({
        type: 'edge_proximity',
        message: `${edgeProximity.tooClose} samples may be too close to field edge`,
        severity: 'warning'
      });
    }

    // Method-specific validation
    this.performMethodSpecificValidation(samples, assessmentMethod, validationResults);

    return validationResults;
  }

  performMethodSpecificValidation(samples, method, results) {
    switch(method) {
      case 'hailDamage':
        this.validateHailSamples(samples, results);
        break;
      case 'standReduction':
        this.validateStandReductionSamples(samples, results);
        break;
      case 'weightMethod':
        this.validateWeightMethodSamples(samples, results);
        break;
    }
  }

  validateHailSamples(samples, results) {
    // Check that hail assessment was delayed appropriately
    const damageDate = this.getDamageDate();
    const assessmentDate = new Date();
    const daysSinceDamage = (assessmentDate - damageDate) / (1000 * 60 * 60 * 24);

    if(daysSinceDamage < 7) {
      results.errors.push({
        type: 'premature_assessment',
        message: `Hail assessment should be delayed minimum 7 days after damage. Only ${daysSinceDamage} days elapsed.`,
        severity: 'error'
      });
      results.isAdequate = false;
    }
  }
}
```

## Real-Time Sample Guidance

```javascript
class SampleGuidanceSystem {

  provideSamplingGuidance(currentLocation, fieldBoundary, existingSamples, targetSampleCount) {
    const guidance = {
      nextSampleLocation: null,
      distanceToNext: null,
      completionPercentage: (existingSamples.length / targetSampleCount) * 100,
      qualityScore: this.calculateCurrentQualityScore(existingSamples),
      recommendations: []
    };

    // Calculate optimal next sample location
    guidance.nextSampleLocation = this.calculateOptimalNextSample(
      currentLocation, fieldBoundary, existingSamples
    );
    guidance.distanceToNext = this.calculateDistance(currentLocation, guidance.nextSampleLocation);

    // Generate recommendations
    if(guidance.completionPercentage < 100) {
      guidance.recommendations.push({
        type: 'navigate',
        message: `Navigate ${guidance.distanceToNext}m to next sample point`,
        priority: 'high'
      });
    }

    if(guidance.qualityScore < 0.8) {
      guidance.recommendations.push({
        type: 'distribution',
        message: 'Consider additional samples in underrepresented areas',
        priority: 'medium'
      });
    }

    return guidance;
  }

  calculateOptimalNextSample(currentLocation, fieldBoundary, existingSamples) {
    // Use algorithm to find location that maximizes field coverage
    const candidates = this.generateCandidateLocations(fieldBoundary, existingSamples);
    
    // Score each candidate based on:
    // 1. Distance from existing samples (maximize)
    // 2. Distance from current location (minimize for efficiency)
    // 3. Field coverage optimization
    
    let bestCandidate = null;
    let bestScore = -1;

    for(const candidate of candidates) {
      const score = this.calculateCandidateScore(candidate, currentLocation, existingSamples);
      if(score > bestScore) {
        bestScore = score;
        bestCandidate = candidate;
      }
    }

    return bestCandidate;
  }
}
```
