# Verisca Metric Conversion Reference - Zimbabwe Maize Assessment

## Quick Reference: USDA to Zimbabwe Metric Conversions

### Core Area/Yield Conversions

| USDA Original | Zimbabwe Metric | Conversion Factor | Usage in Verisca |
|---------------|----------------|------------------|------------------|
| 1 acre | 0.4047 hectares | ×0.4047 | Field size entry |
| 1 bushel/acre | 0.0628 tonnes/hectare | ×0.0628 | Yield calculations |
| 56 lbs/bushel | 25.4 kg/hectolitre | Standard conversion | Test weight |

### Sampling Area Conversions

| USDA Sample Size | Zimbabwe Equivalent | Row Length Calculation |
|------------------|--------------------|-----------------------|
| 1/100 acre | 1/250 hectare (40.47m²) | 40m ÷ row width (metres) |
| 1/1000 acre | 1/2500 hectare (4.047m²) | 4m ÷ row width (metres) |
| 1/2000 acre | 1/5000 hectare (2.024m²) | 2m ÷ row width (metres) |

### Linear Measurement Conversions

| USDA Measurement | Zimbabwe Metric | Precision |
|------------------|-----------------|-----------|
| Row width (inches) | Row width (cm) | To nearest 2.5cm |
| Row length (feet) | Row length (metres) | To nearest 0.1m |
| Field dimensions (feet) | Field dimensions (metres) | To nearest 1m |

### Weight/Volume Conversions

| USDA Unit | Zimbabwe Unit | Conversion | Application |
|-----------|---------------|------------|-------------|
| Pounds (lbs) | Kilograms (kg) | ×0.4536 | Sample weights |
| Tons (US) | Tonnes (metric) | ×0.9072 | Silage production |
| Bushel | Hectolitre | ×0.3524 | Volume measurements |

## Verisca Implementation Notes

### Field Data Entry
- **Field Size**: Input in hectares (0.1 to 400+ ha range)
- **Row Spacing**: Input in centimetres (common Zimbabwe spacings: 75cm, 90cm)
- **Plant Population**: Input as plants per hectare
- **Yield Targets**: Input in tonnes per hectare

### Sample Calculation Engine
```javascript
// Sample row length calculation (metric)
function calculateRowLength(sampleSize, rowWidthCm) {
    const areaM2 = {
        '1/250': 40.47,    // 1/250 hectare
        '1/2500': 4.047,   // 1/2500 hectare  
        '1/5000': 2.024    // 1/5000 hectare
    };
    
    const rowWidthM = rowWidthCm / 100;
    return areaM2[sampleSize] / rowWidthM;
}
```

### Yield Calculation Engine
```javascript
// Convert USDA chart values to metric
function convertYieldToMetric(usdaBushelsPerAcre) {
    return usdaBushelsPerAcre * 0.0628; // tonnes/hectare
}

// Calculate final yield assessment
function calculateYieldAssessment(percentPotential, baseYieldTonnesHa) {
    return (percentPotential / 100) * baseYieldTonnesHa;
}
```

### Database Schema Adaptations

#### Assessment_Methods Table
```sql
CREATE TABLE assessment_methods (
    id SERIAL PRIMARY KEY,
    method_name VARCHAR(100),
    growth_stage_min VARCHAR(50),
    growth_stage_max VARCHAR(50),
    sample_size_hectare DECIMAL(8,6), -- e.g., 0.004047 for 1/250th
    min_field_size_ha DECIMAL(6,2),
    max_field_size_ha DECIMAL(6,2),
    yield_units VARCHAR(20) DEFAULT 'tonnes_per_hectare'
);
```

#### Lookup_Charts Table
```sql
CREATE TABLE lookup_charts (
    id SERIAL PRIMARY KEY,
    chart_name VARCHAR(100),
    growth_stage VARCHAR(50),
    stand_percentage INTEGER,
    potential_percentage INTEGER,
    units VARCHAR(20) DEFAULT 'metric'
);
```

## Zimbabwe-Specific Adaptations

### Common Maize Varieties & Growth Stages
| Variety Type | Maturity Days | Leaf Count | Growth Adjustment |
|--------------|---------------|------------|-------------------|
| SC varieties (e.g., SC403, SC719) | 125-135 days | 19-21 leaves | Standard timing |
| Open pollinated (e.g., Hickory King) | 140-150 days | 21-23 leaves | +5 days per stage |
| Hybrid varieties (e.g., Pioneer) | 115-125 days | 18-20 leaves | -2 days per stage |

### Local Weather Integration
- **Frost Dates**: Use Zimbabwe Met Services data
- **Growing Season**: October - May planting window
- **Heat Stress**: >35°C for 3+ consecutive days
- **Drought Stress**: <25mm rainfall for 21+ days during critical periods

### Quality Factors for Zimbabwe Market
| Factor | Local Standard | Adjustment |
|--------|----------------|------------|
| Moisture Content | 12.5% (safe storage) | Standard |
| Test Weight | 720-780 kg/hectolitre | Quality grade factor |
| Foreign Matter | <2% for Grade 1 | Discount table |
| Damaged Kernels | <5% for Grade 1 | Discount table |

## Implementation Priority for MVP

1. **Stand Reduction Method** (Core)
   - Metric sample calculations
   - Plant count methodology  
   - Growth stage lookup charts
   - Percentage potential calculations

2. **GPS Integration**
   - Field boundary mapping (hectares)
   - Sample point generation
   - Row direction measurement

3. **Form Builder**
   - Multi-language support (English/Shona/Ndebele)
   - Metric unit validation
   - Photo evidence capture

4. **Calculation Engine**
   - All USDA formulas in metric
   - Local variety adjustments
   - Quality factor integration

This reference ensures Verisca speaks the language of Zimbabwe agriculture while maintaining the scientific rigor of USDA standards.
