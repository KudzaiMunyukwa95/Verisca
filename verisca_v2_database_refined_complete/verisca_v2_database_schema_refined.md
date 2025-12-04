# Verisca V2 Database Schema - Refined Version (with Growth Stage Ranges & Peril Severity)

## 1. ENTITY RELATIONSHIP DIAGRAM (Text Representation)

```
TENANTS ||--o{ USERS
TENANTS ||--o{ TENANT_CONFIGURATIONS
TENANTS ||--o{ CLAIMS

USERS }o--|| ROLES
USERS ||--o{ ASSESSMENT_SESSIONS
USERS ||--o{ AUDIT_LOGS

CROPS ||--o{ CROP_VARIETIES
CROPS ||--o{ GROWTH_STAGES
CROPS ||--o{ CROP_PERIL_METHODS
CROPS ||--o{ SAMPLING_RULES
CROPS ||--o{ LOOKUP_TABLE_DEFINITIONS

PERILS ||--o{ CROP_PERIL_METHODS
PERILS }o--|| LOOKUP_TABLE_DEFINITIONS [peril_severity_lookup_id]
ASSESSMENT_METHODS ||--o{ CROP_PERIL_METHODS

GROWTH_STAGES ||--o{ METHOD_GROWTH_STAGE_RULES
GROWTH_STAGES ||--o{ VARIETY_GROWTH_STAGE_RANGES
CROP_VARIETIES ||--o{ VARIETY_GROWTH_STAGE_RANGES

ASSESSMENT_METHODS ||--o{ METHOD_GROWTH_STAGE_RULES

LOOKUP_TABLE_DEFINITIONS ||--o{ LOOKUP_TABLE_DATA
LOOKUP_TABLE_DEFINITIONS ||--o{ LOOKUP_TABLE_VERSIONS

FARMS ||--o{ FIELDS
TENANTS ||--o{ FARMS
USERS ||--o{ FARMS

FIELDS ||--o{ CLAIMS
CROPS ||--o{ CLAIMS
CROP_VARIETIES ||--o{ CLAIMS

CLAIMS ||--o{ ASSESSMENT_SESSIONS
ASSESSMENT_METHODS ||--o{ ASSESSMENT_SESSIONS
GROWTH_STAGES ||--o{ ASSESSMENT_SESSIONS

ASSESSMENT_SESSIONS ||--o{ SAMPLE_POINTS
ASSESSMENT_SESSIONS ||--o{ EVIDENCE
ASSESSMENT_SESSIONS ||--o{ CALCULATIONS
ASSESSMENT_SESSIONS ||--o{ REPORTS

SAMPLE_POINTS ||--o{ SAMPLE_DATA
SAMPLE_POINTS ||--o{ EVIDENCE

METHODOLOGY_VERSIONS ||--o{ ASSESSMENT_SESSIONS
METHODOLOGY_VERSIONS ||--o{ LOOKUP_TABLE_VERSIONS
METHODOLOGY_VERSIONS ||--o{ CALCULATION_FORMULAS

SYNC_QUEUE ||--o{ DEVICE_REGISTRATIONS
USERS ||--o{ DEVICE_REGISTRATIONS

ASSESSMENT_SESSIONS ||--o{ SYNC_QUEUE
EVIDENCE ||--o{ SYNC_QUEUE
CALCULATIONS ||--o{ SYNC_QUEUE
```

## 2. FULL TABLE DEFINITIONS (PostgreSQL with PostGIS)

### Core Multi-Tenant Structure

```sql
-- =============================================
-- TENANTS & AUTHENTICATION
-- =============================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code VARCHAR(20) UNIQUE NOT NULL, -- e.g., 'ZIMRE', 'FIRST_MUTUAL'
    tenant_name VARCHAR(100) NOT NULL,
    tenant_type VARCHAR(20) NOT NULL CHECK (tenant_type IN ('insurer', 'assessor_company', 'system_admin')),
    contact_email VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20),
    address JSONB,
    billing_info JSONB,
    tenant_config JSONB DEFAULT '{}', -- Custom tenant configurations
    subscription_tier VARCHAR(20) DEFAULT 'standard',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

CREATE INDEX idx_tenants_code ON tenants(tenant_code);
CREATE INDEX idx_tenants_active ON tenants(is_active) WHERE is_active = true;

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) UNIQUE NOT NULL, -- 'admin', 'assessor', 'supervisor', 'viewer'
    role_description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]', -- Array of permission strings
    is_system_role BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    employee_id VARCHAR(50), -- Optional employee identifier
    assessor_license VARCHAR(50), -- For licensed assessors
    specializations JSONB DEFAULT '[]', -- Array of crop/peril specializations
    profile_image_url VARCHAR(500),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active, tenant_id) WHERE is_active = true;

-- =============================================
-- CROP MANAGEMENT SYSTEM
-- =============================================

CREATE TABLE crops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_code VARCHAR(20) UNIQUE NOT NULL, -- 'MAIZE', 'WHEAT', 'SOYBEANS'
    crop_name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(100),
    crop_family VARCHAR(50), -- 'Cereals', 'Legumes', 'Cash Crops'
    typical_growing_season JSONB, -- {'planting_months': [10,11,12], 'harvest_months': [4,5,6]}
    physiological_characteristics JSONB, -- Growth patterns, maturity info
    standard_units JSONB NOT NULL, -- {'yield': 'tonnes_per_hectare', 'weight': 'kg', 'moisture': 'percent'}
    is_active BOOLEAN DEFAULT true,
    methodology_source VARCHAR(100), -- 'USDA', 'FAO', 'Custom'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_crops_code ON crops(crop_code);
CREATE INDEX idx_crops_active ON crops(is_active) WHERE is_active = true;

CREATE TABLE crop_varieties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    variety_code VARCHAR(30) NOT NULL, -- 'SC403', 'SC719', 'PIONEER_3253'
    variety_name VARCHAR(100) NOT NULL,
    variety_type VARCHAR(50), -- 'hybrid', 'open_pollinated', 'synthetic'
    maturity_days INTEGER, -- Days to physiological maturity
    maturity_category VARCHAR(20), -- 'early', 'medium', 'late', 'full_season'
    growth_stage_range JSONB NOT NULL, -- {'early_factor': 0.85, 'late_factor': 1.15, 'base_days': []} 
    characteristics JSONB, -- Disease resistance, drought tolerance, etc.
    growing_regions JSONB, -- Array of applicable regions
    yield_potential_range JSONB, -- {'min': 4.0, 'max': 8.0, 'units': 'tonnes_per_hectare'}
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(crop_id, variety_code)
);

CREATE INDEX idx_varieties_crop ON crop_varieties(crop_id);
CREATE INDEX idx_varieties_code ON crop_varieties(variety_code);
CREATE INDEX idx_varieties_maturity ON crop_varieties(maturity_category);

CREATE TABLE growth_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    stage_code VARCHAR(30) NOT NULL, -- 'EMERGENCE', 'V3', 'VT', 'R1', 'R6'
    stage_name VARCHAR(100) NOT NULL, -- 'Third Leaf', 'Tasseling', 'Silking'
    stage_order INTEGER NOT NULL, -- Sequential order of stages
    base_days_from_planting INTEGER NOT NULL, -- Base timing for standard variety
    stage_characteristics JSONB NOT NULL, -- Physical description, identification guide
    assessment_implications JSONB, -- Which methods are applicable at this stage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(crop_id, stage_code),
    UNIQUE(crop_id, stage_order)
);

CREATE INDEX idx_growth_stages_crop ON growth_stages(crop_id);
CREATE INDEX idx_growth_stages_order ON growth_stages(crop_id, stage_order);

-- NEW: Junction table for variety-specific growth stage timing
CREATE TABLE variety_growth_stage_ranges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variety_id UUID NOT NULL REFERENCES crop_varieties(id) ON DELETE CASCADE,
    growth_stage_id UUID NOT NULL REFERENCES growth_stages(id) ON DELETE CASCADE,
    days_from_planting_min INTEGER NOT NULL, -- Earliest expected timing
    days_from_planting_max INTEGER NOT NULL, -- Latest expected timing  
    days_from_planting_typical INTEGER NOT NULL, -- Most common timing
    stage_duration_days INTEGER DEFAULT 3, -- How long stage typically lasts
    temperature_adjustments JSONB, -- Temperature-based timing adjustments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(variety_id, growth_stage_id),
    CHECK (days_from_planting_min <= days_from_planting_typical),
    CHECK (days_from_planting_typical <= days_from_planting_max)
);

CREATE INDEX idx_variety_stages_variety ON variety_growth_stage_ranges(variety_id);
CREATE INDEX idx_variety_stages_stage ON variety_growth_stage_ranges(growth_stage_id);

-- =============================================
-- PERIL & ASSESSMENT METHOD SYSTEM
-- =============================================

CREATE TABLE perils (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peril_code VARCHAR(30) UNIQUE NOT NULL, -- 'DROUGHT', 'HAIL', 'DISEASE_FUNGAL'
    peril_name VARCHAR(100) NOT NULL,
    peril_category VARCHAR(50) NOT NULL, -- 'weather', 'biological', 'mechanical'
    description TEXT,
    typical_indicators JSONB, -- Visual and physical indicators
    seasonality JSONB, -- When this peril typically occurs
    has_severity_levels BOOLEAN DEFAULT false, -- Whether this peril uses severity scaling
    peril_severity_lookup_id UUID REFERENCES lookup_table_definitions(id), -- NEW: Modular severity scales
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_perils_code ON perils(peril_code);
CREATE INDEX idx_perils_category ON perils(peril_category);
CREATE INDEX idx_perils_severity_lookup ON perils(peril_severity_lookup_id);

CREATE TABLE assessment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_code VARCHAR(30) UNIQUE NOT NULL, -- 'STAND_REDUCTION', 'HAIL_DAMAGE', 'WEIGHT_METHOD'
    method_name VARCHAR(100) NOT NULL,
    method_description TEXT,
    methodology_source VARCHAR(100), -- 'USDA_FCIC25080', 'FAO_STANDARD'
    calculation_type VARCHAR(30) NOT NULL, -- 'percentage_potential', 'direct_weight', 'quality_adjustment'
    required_measurements JSONB NOT NULL, -- Array of required field measurements
    required_calculations JSONB NOT NULL, -- Array of calculation steps
    quality_requirements JSONB, -- Minimum quality standards
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_methods_code ON assessment_methods(method_code);

CREATE TABLE crop_peril_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crops(id),
    peril_id UUID NOT NULL REFERENCES perils(id),
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    applicable_growth_stages JSONB NOT NULL, -- Array of applicable stage codes
    severity_thresholds JSONB, -- When severity affects method choice
    priority_order INTEGER DEFAULT 1, -- Method preference order
    special_conditions JSONB, -- Additional conditions for method applicability
    method_modifications JSONB, -- Crop-specific modifications to standard method
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(crop_id, peril_id, method_id)
);

CREATE INDEX idx_crop_peril_methods_crop ON crop_peril_methods(crop_id);
CREATE INDEX idx_crop_peril_methods_peril ON crop_peril_methods(peril_id);
CREATE INDEX idx_crop_peril_methods_method ON crop_peril_methods(method_id);

CREATE TABLE method_growth_stage_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    growth_stage_id UUID NOT NULL REFERENCES growth_stages(id),
    is_applicable BOOLEAN NOT NULL,
    special_considerations JSONB, -- Special rules for this stage
    calculation_modifications JSONB, -- Stage-specific calculation changes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(method_id, growth_stage_id)
);

-- =============================================
-- GENERIC LOOKUP TABLE ARCHITECTURE
-- =============================================

CREATE TABLE lookup_table_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_code VARCHAR(50) UNIQUE NOT NULL, -- 'STAND_REDUCTION_EARLY', 'HAIL_LEAF_LOSS', 'DROUGHT_SEVERITY'
    table_name VARCHAR(100) NOT NULL,
    table_description TEXT,
    crop_id UUID REFERENCES crops(id), -- NULL for crop-agnostic tables
    method_id UUID REFERENCES assessment_methods(id),
    table_category VARCHAR(30), -- 'assessment', 'severity', 'quality', 'conversion'
    source_reference VARCHAR(100), -- 'USDA_EXHIBIT_11', 'FAO_TABLE_3', 'CUSTOM_SEVERITY'
    table_structure JSONB NOT NULL, -- Schema definition
    interpolation_rules JSONB, -- How to interpolate between values
    validation_rules JSONB, -- Input validation requirements
    table_type VARCHAR(30) NOT NULL, -- 'matrix', 'key_value', 'multi_dimensional', 'severity_scale'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_lookup_defs_code ON lookup_table_definitions(table_code);
CREATE INDEX idx_lookup_defs_crop ON lookup_table_definitions(crop_id);
CREATE INDEX idx_lookup_defs_method ON lookup_table_definitions(method_id);
CREATE INDEX idx_lookup_defs_category ON lookup_table_definitions(table_category);

CREATE TABLE lookup_table_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_definition_id UUID NOT NULL REFERENCES lookup_table_definitions(id) ON DELETE CASCADE,
    input_values JSONB NOT NULL, -- Input parameters (e.g., {'stand_percent': 85, 'growth_stage': 'V6'})
    output_value DECIMAL(10,4) NOT NULL, -- Result value
    output_label VARCHAR(100), -- Text label for severity levels, etc.
    metadata JSONB DEFAULT '{}', -- Additional data, notes, conditions
    row_order INTEGER, -- For ordered tables
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_lookup_data_table ON lookup_table_data(table_definition_id);
CREATE INDEX idx_lookup_data_inputs ON lookup_table_data USING GIN (input_values);
CREATE INDEX idx_lookup_data_output ON lookup_table_data(output_value);

CREATE TABLE lookup_table_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_definition_id UUID NOT NULL REFERENCES lookup_table_definitions(id),
    version_number VARCHAR(20) NOT NULL, -- 'v1.0', 'v1.1', '2024.1'
    methodology_version_id UUID, -- Links to methodology_versions
    effective_date DATE NOT NULL,
    deprecated_date DATE,
    change_description TEXT,
    is_current_version BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(table_definition_id, version_number)
);

CREATE INDEX idx_lookup_versions_table ON lookup_table_versions(table_definition_id);
CREATE INDEX idx_lookup_versions_current ON lookup_table_versions(is_current_version) WHERE is_current_version = true;

-- =============================================
-- SAMPLING RULES & CALCULATION SYSTEM
-- =============================================

CREATE TABLE sampling_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crops(id),
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    rule_name VARCHAR(100) NOT NULL,
    field_area_min DECIMAL(8,2), -- Minimum field size (hectares)
    field_area_max DECIMAL(8,2), -- Maximum field size (hectares)
    sample_size_formula JSONB NOT NULL, -- Formula for calculating sample area
    minimum_samples INTEGER NOT NULL, -- Minimum number of samples
    additional_sample_rule JSONB, -- Rules for additional samples
    sampling_pattern VARCHAR(30) DEFAULT 'random', -- 'random', 'systematic', 'stratified'
    exclusion_zones JSONB, -- Areas to avoid (edges, waterways)
    quality_requirements JSONB, -- Sample quality standards
    tenant_overrides JSONB DEFAULT '{}', -- Tenant-specific modifications
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(crop_id, method_id, rule_name)
);

CREATE INDEX idx_sampling_rules_crop_method ON sampling_rules(crop_id, method_id);

CREATE TABLE calculation_formulas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formula_code VARCHAR(50) UNIQUE NOT NULL, -- 'STAND_REDUCTION_BASIC', 'HAIL_TOTAL_DAMAGE'
    formula_name VARCHAR(100) NOT NULL,
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    formula_expression TEXT NOT NULL, -- Mathematical expression or algorithm reference
    input_parameters JSONB NOT NULL, -- Required input parameters
    output_parameters JSONB NOT NULL, -- Output parameters and units
    validation_rules JSONB, -- Input validation and range checks
    rounding_rules JSONB, -- Precision and rounding requirements
    formula_version VARCHAR(20) DEFAULT 'v1.0',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_formulas_code ON calculation_formulas(formula_code);
CREATE INDEX idx_formulas_method ON calculation_formulas(method_id);

CREATE TABLE quality_factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_code VARCHAR(50) UNIQUE NOT NULL, -- 'MOISTURE_ADJUSTMENT', 'TEST_WEIGHT'
    factor_name VARCHAR(100) NOT NULL,
    crop_id UUID REFERENCES crops(id), -- NULL for universal factors
    factor_type VARCHAR(30) NOT NULL, -- 'moisture', 'test_weight', 'foreign_material', 'damage'
    adjustment_table_id UUID REFERENCES lookup_table_definitions(id),
    default_value DECIMAL(8,4),
    value_range JSONB, -- Valid range for this factor
    units VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_quality_factors_crop ON quality_factors(crop_id);
CREATE INDEX idx_quality_factors_type ON quality_factors(factor_type);

-- =============================================
-- FARM & FIELD MANAGEMENT (Spatial)
-- =============================================

CREATE TABLE farms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    owner_user_id UUID REFERENCES users(id), -- Farm owner/manager
    farm_code VARCHAR(50) NOT NULL, -- Tenant-specific farm identifier
    farm_name VARCHAR(100) NOT NULL,
    farmer_name VARCHAR(100),
    farmer_contact JSONB, -- Phone, email, etc.
    farm_location GEOMETRY(POINT, 4326), -- Farm center point
    farm_address JSONB,
    total_farm_area DECIMAL(10,2), -- Total farm size in hectares
    operational_area DECIMAL(10,2), -- Area under cultivation
    farm_characteristics JSONB, -- Soil types, elevation, climate zone, etc.
    registration_numbers JSONB, -- Government registration, tax numbers
    insurance_history JSONB, -- Historical insurance information
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    UNIQUE(tenant_id, farm_code)
);

CREATE INDEX idx_farms_tenant ON farms(tenant_id);
CREATE INDEX idx_farms_owner ON farms(owner_user_id);
CREATE INDEX idx_farms_location ON farms USING GIST (farm_location);

CREATE TABLE fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    field_code VARCHAR(50) NOT NULL, -- Field identifier within farm
    field_name VARCHAR(100),
    field_boundary GEOMETRY(POLYGON, 4326) NOT NULL, -- Field boundary polygon
    field_area DECIMAL(8,2) NOT NULL, -- Calculated from boundary (hectares)
    field_center GEOMETRY(POINT, 4326), -- Calculated center point
    soil_characteristics JSONB, -- Soil type, fertility, drainage
    irrigation_type VARCHAR(30), -- 'rainfed', 'sprinkler', 'drip', 'flood'
    elevation_meters INTEGER,
    slope_characteristics JSONB,
    access_notes TEXT, -- How to access the field
    historical_yields JSONB, -- Previous season yield data
    land_use_restrictions JSONB, -- Any restrictions or easements
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(farm_id, field_code)
);

CREATE INDEX idx_fields_farm ON fields(farm_id);
CREATE INDEX idx_fields_boundary ON fields USING GIST (field_boundary);
CREATE INDEX idx_fields_center ON fields USING GIST (field_center);

-- =============================================
-- CLAIMS & ASSESSMENT SESSIONS
-- =============================================

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    claim_number VARCHAR(50) UNIQUE NOT NULL, -- Auto-generated claim number
    policy_number VARCHAR(100) NOT NULL,
    insured_name VARCHAR(100) NOT NULL,
    farm_id UUID NOT NULL REFERENCES farms(id),
    field_id UUID NOT NULL REFERENCES fields(id),
    crop_id UUID NOT NULL REFERENCES crops(id),
    variety_id UUID REFERENCES crop_varieties(id),
    planting_date DATE NOT NULL,
    expected_harvest_date DATE,
    expected_yield DECIMAL(8,2) NOT NULL, -- Expected yield (tonnes/hectare)
    insured_area DECIMAL(8,2) NOT NULL, -- Insured area (hectares)
    sum_insured DECIMAL(12,2), -- Total sum insured
    
    -- Loss Information
    loss_notification_date DATE NOT NULL,
    suspected_peril_id UUID REFERENCES perils(id),
    peril_severity_level VARCHAR(20), -- Links to peril severity lookup
    loss_description TEXT,
    estimated_loss_percentage DECIMAL(5,2), -- Initial estimate
    
    -- Claim Status
    claim_status VARCHAR(30) DEFAULT 'reported', -- 'reported', 'assigned', 'in_progress', 'completed', 'settled'
    priority VARCHAR(20) DEFAULT 'normal', -- 'urgent', 'high', 'normal', 'low'
    assigned_assessor_id UUID REFERENCES users(id),
    
    -- Key Dates
    assignment_date TIMESTAMP WITH TIME ZONE,
    target_completion_date DATE,
    actual_completion_date TIMESTAMP WITH TIME ZONE,
    
    -- Final Results (populated after assessment)
    final_loss_percentage DECIMAL(5,2),
    final_yield_estimate DECIMAL(8,2), -- Final yield estimate (tonnes/hectare)
    settlement_amount DECIMAL(12,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_claims_tenant ON claims(tenant_id);
CREATE INDEX idx_claims_number ON claims(claim_number);
CREATE INDEX idx_claims_policy ON claims(policy_number);
CREATE INDEX idx_claims_status ON claims(claim_status);
CREATE INDEX idx_claims_assessor ON claims(assigned_assessor_id);
CREATE INDEX idx_claims_farm_field ON claims(farm_id, field_id);
CREATE INDEX idx_claims_variety ON claims(variety_id);

CREATE TABLE assessment_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    session_number INTEGER NOT NULL DEFAULT 1, -- Multiple sessions per claim possible
    assessor_id UUID NOT NULL REFERENCES users(id),
    
    -- Assessment Method & Configuration
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    peril_id UUID NOT NULL REFERENCES perils(id),
    growth_stage_id UUID NOT NULL REFERENCES growth_stages(id),
    methodology_version_id UUID REFERENCES methodology_versions(id),
    
    -- Session Status
    session_status VARCHAR(30) DEFAULT 'planned', -- 'planned', 'in_progress', 'field_complete', 'calculated', 'completed'
    session_type VARCHAR(30) DEFAULT 'primary', -- 'primary', 'follow_up', 'quality_check'
    
    -- Field Visit Information
    visit_date DATE,
    visit_start_time TIMESTAMP WITH TIME ZONE,
    visit_end_time TIMESTAMP WITH TIME ZONE,
    weather_conditions JSONB, -- Weather during visit
    field_access_notes TEXT,
    
    -- Growth Stage Assessment
    assessed_growth_stage_confidence DECIMAL(3,2), -- Confidence in growth stage ID
    variety_stage_adjustment JSONB, -- Variety-specific timing adjustments applied
    
    -- Sampling Plan
    sampling_plan JSONB NOT NULL, -- Generated sampling configuration
    actual_samples_collected INTEGER,
    sampling_quality_score DECIMAL(3,2), -- Quality score for sampling
    
    -- Assessment Results
    raw_assessment_data JSONB, -- All raw field measurements
    calculation_results JSONB, -- Intermediate calculation results
    final_appraisal DECIMAL(8,2), -- Final appraisal (tonnes/hectare)
    confidence_score DECIMAL(3,2), -- Assessment confidence (0.0-1.0)
    quality_flags JSONB DEFAULT '[]', -- Array of quality issues
    
    -- Evidence & Documentation
    total_photos_captured INTEGER DEFAULT 0,
    total_gps_points_captured INTEGER DEFAULT 0,
    evidence_quality_score DECIMAL(3,2),
    field_notes TEXT,
    
    -- Technical Information
    app_version VARCHAR(20), -- Version of mobile app used
    device_info JSONB, -- Device and technical information
    gps_accuracy_meters DECIMAL(5,2), -- Average GPS accuracy
    
    -- Sync & Offline Information
    session_created_offline BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'syncing', 'synced', 'conflict'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(claim_id, session_number)
);

CREATE INDEX idx_sessions_claim ON assessment_sessions(claim_id);
CREATE INDEX idx_sessions_assessor ON assessment_sessions(assessor_id);
CREATE INDEX idx_sessions_status ON assessment_sessions(session_status);
CREATE INDEX idx_sessions_sync ON assessment_sessions(sync_status);
CREATE INDEX idx_sessions_visit_date ON assessment_sessions(visit_date);
CREATE INDEX idx_sessions_growth_stage ON assessment_sessions(growth_stage_id);

-- =============================================
-- SAMPLING & EVIDENCE SYSTEM
-- =============================================

CREATE TABLE sample_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    sample_number INTEGER NOT NULL, -- Sequential sample number
    
    -- GPS Information
    gps_location GEOMETRY(POINT, 4326) NOT NULL, -- Sample location
    gps_accuracy_meters DECIMAL(5,2),
    gps_altitude_meters DECIMAL(7,2),
    gps_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Sampling Details
    sample_type VARCHAR(30) DEFAULT 'primary', -- 'primary', 'backup', 'additional'
    sample_area_hectares DECIMAL(8,6) NOT NULL, -- Actual sample area
    row_width_cm DECIMAL(5,1),
    row_length_meters DECIMAL(6,2),
    
    -- Quality Validation
    sample_quality_score DECIMAL(3,2), -- Quality assessment of this sample
    distance_from_edge_meters DECIMAL(5,1), -- Distance from field edge
    representative_score DECIMAL(3,2), -- How representative this sample is
    validation_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sample_points_session ON sample_points(session_id);
CREATE INDEX idx_sample_points_location ON sample_points USING GIST (gps_location);
CREATE INDEX idx_sample_points_number ON sample_points(session_id, sample_number);

CREATE TABLE sample_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sample_point_id UUID NOT NULL REFERENCES sample_points(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL, -- 'plant_count', 'ear_weight', 'moisture_reading'
    measurement_category VARCHAR(30) NOT NULL, -- 'population', 'damage', 'quality', 'growth'
    
    -- Measurement Values
    numeric_value DECIMAL(12,4), -- Numeric measurements
    text_value VARCHAR(500), -- Text observations
    boolean_value BOOLEAN, -- Yes/No observations
    json_value JSONB, -- Complex structured data
    
    -- Measurement Context
    measurement_unit VARCHAR(20), -- 'plants_per_sample', 'kg', 'percent'
    measurement_method VARCHAR(50), -- How measurement was taken
    measurement_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Quality & Validation
    measurement_confidence DECIMAL(3,2), -- Confidence in measurement
    validation_status VARCHAR(20) DEFAULT 'pending', -- 'valid', 'flagged', 'invalid'
    validation_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sample_data_point ON sample_data(sample_point_id);
CREATE INDEX idx_sample_data_type ON sample_data(data_type);
CREATE INDEX idx_sample_data_category ON sample_data(measurement_category);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    sample_point_id UUID REFERENCES sample_points(id), -- NULL for general evidence
    
    -- Evidence Details
    evidence_type VARCHAR(30) NOT NULL, -- 'photo', 'video', 'audio', 'gps_track'
    evidence_category VARCHAR(30) NOT NULL, -- 'overview', 'damage', 'sample', 'growth_stage'
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- Cloud storage path
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    
    -- Spatial Information
    gps_location GEOMETRY(POINT, 4326), -- Where evidence was captured
    gps_accuracy_meters DECIMAL(5,2),
    compass_direction DECIMAL(5,1), -- Direction camera was pointing
    
    -- Content Information
    caption TEXT, -- User-provided description
    auto_tags JSONB DEFAULT '[]', -- AI-generated tags
    manual_tags JSONB DEFAULT '[]', -- User-provided tags
    analysis_results JSONB, -- AI analysis results
    
    -- Technical Metadata
    device_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    server_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    device_info JSONB, -- Camera, device specs
    camera_settings JSONB, -- ISO, exposure, etc.
    
    -- Sync Information
    uploaded_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'uploading', 'uploaded', 'failed'
    thumbnail_path VARCHAR(500), -- Thumbnail for photos/videos
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evidence_session ON evidence(session_id);
CREATE INDEX idx_evidence_sample ON evidence(sample_point_id);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);
CREATE INDEX idx_evidence_location ON evidence USING GIST (gps_location);
CREATE INDEX idx_evidence_sync ON evidence(sync_status);

-- =============================================
-- CALCULATIONS & REPORTING
-- =============================================

CREATE TABLE calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    calculation_step INTEGER NOT NULL, -- Order of calculation steps
    
    -- Calculation Details
    formula_id UUID REFERENCES calculation_formulas(id),
    calculation_type VARCHAR(50) NOT NULL, -- 'sample_appraisal', 'quality_adjustment', 'final_estimate'
    calculation_name VARCHAR(100) NOT NULL,
    
    -- Input Data
    input_data JSONB NOT NULL, -- All input values used
    lookup_table_references JSONB, -- References to lookup tables used
    
    -- Calculation Results
    intermediate_results JSONB, -- Step-by-step calculations
    final_result DECIMAL(12,4) NOT NULL,
    result_units VARCHAR(20) NOT NULL,
    
    -- Validation & Quality
    validation_status VARCHAR(20) DEFAULT 'valid', -- 'valid', 'warning', 'error'
    validation_messages JSONB DEFAULT '[]',
    calculation_confidence DECIMAL(3,2),
    
    -- Audit Trail
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calculation_version VARCHAR(20), -- Version of calculation engine used
    recalculated_count INTEGER DEFAULT 0, -- How many times recalculated
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_calculations_session ON calculations(session_id);
CREATE INDEX idx_calculations_step ON calculations(session_id, calculation_step);
CREATE INDEX idx_calculations_type ON calculations(calculation_type);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id),
    claim_id UUID NOT NULL REFERENCES claims(id), -- Denormalized for quick access
    tenant_id UUID NOT NULL REFERENCES tenants(id), -- For multi-tenant isolation
    
    -- Report Details
    report_type VARCHAR(30) NOT NULL, -- 'assessment', 'summary', 'detailed', 'regulatory'
    report_template VARCHAR(50), -- Template used for generation
    report_status VARCHAR(20) DEFAULT 'generating', -- 'generating', 'ready', 'delivered', 'failed'
    
    -- Generated Files
    pdf_file_path VARCHAR(500), -- Main PDF report
    pdf_file_size_bytes BIGINT,
    excel_file_path VARCHAR(500), -- Detailed data export
    raw_data_path VARCHAR(500), -- Raw JSON data export
    
    -- Report Content Summary
    report_summary JSONB NOT NULL, -- Key findings and results
    executive_summary TEXT, -- Human-readable summary
    recommendations TEXT, -- Assessor recommendations
    
    -- Signatures & Approvals
    assessor_signature JSONB, -- Digital signature
    supervisor_approval JSONB, -- If required
    insured_acknowledgment JSONB, -- Insured sign-off
    
    -- Distribution
    auto_sent_to_insurer BOOLEAN DEFAULT false,
    distribution_log JSONB DEFAULT '[]', -- Who received the report when
    
    -- Generation Information
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by UUID REFERENCES users(id),
    generation_duration_seconds INTEGER, -- How long it took to generate
    template_version VARCHAR(20),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reports_session ON reports(session_id);
CREATE INDEX idx_reports_claim ON reports(claim_id);
CREATE INDEX idx_reports_tenant ON reports(tenant_id);
CREATE INDEX idx_reports_status ON reports(report_status);

-- =============================================
-- MOBILE SYNC & OFFLINE SYSTEM
-- =============================================

CREATE TABLE device_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    device_id VARCHAR(100) UNIQUE NOT NULL, -- Unique device identifier
    device_name VARCHAR(100), -- User-friendly device name
    device_type VARCHAR(30), -- 'android', 'ios', 'tablet'
    device_os_version VARCHAR(50),
    app_version VARCHAR(20),
    
    -- Device Capabilities
    gps_capable BOOLEAN DEFAULT true,
    camera_capable BOOLEAN DEFAULT true,
    offline_storage_mb INTEGER, -- Available offline storage
    last_location GEOMETRY(POINT, 4326), -- Last known location
    
    -- Registration Status
    is_active BOOLEAN DEFAULT true,
    registration_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_assessments_completed INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_devices_user ON device_registrations(user_id);
CREATE INDEX idx_devices_id ON device_registrations(device_id);
CREATE INDEX idx_devices_active ON device_registrations(is_active);

CREATE TABLE sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES device_registrations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Sync Item Details
    sync_type VARCHAR(30) NOT NULL, -- 'session_data', 'evidence', 'calculations', 'lookups'
    entity_type VARCHAR(50) NOT NULL, -- 'assessment_session', 'evidence', 'sample_data'
    entity_id UUID NOT NULL, -- ID of the entity being synced
    
    -- Sync Direction & Priority
    sync_direction VARCHAR(10) NOT NULL, -- 'up', 'down'
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    
    -- Sync Status & Attempts
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'syncing', 'completed', 'failed', 'conflict'
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    next_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Data & Conflict Resolution
    sync_data JSONB, -- Data to be synced
    conflict_data JSONB, -- Conflicting data if conflict detected
    conflict_resolution VARCHAR(30), -- 'server_wins', 'client_wins', 'manual'
    
    -- Error Information
    error_message TEXT,
    error_details JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sync_queue_device ON sync_queue(device_id);
CREATE INDEX idx_sync_queue_user ON sync_queue(user_id);
CREATE INDEX idx_sync_queue_status ON sync_queue(sync_status);
CREATE INDEX idx_sync_queue_priority ON sync_queue(priority, next_attempt_at);

CREATE TABLE offline_data_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    package_type VARCHAR(30) NOT NULL, -- 'lookup_tables', 'crop_data', 'full_offline'
    package_version VARCHAR(20) NOT NULL,
    
    -- Package Contents
    included_crops JSONB, -- Array of crop IDs included
    included_tables JSONB, -- Array of lookup table IDs
    package_size_mb DECIMAL(8,2),
    file_path VARCHAR(500), -- Download path
    checksum VARCHAR(64), -- For integrity verification
    
    -- Versioning & Lifecycle
    effective_date DATE NOT NULL,
    expiry_date DATE,
    superseded_by UUID REFERENCES offline_data_packages(id),
    is_current BOOLEAN DEFAULT true,
    download_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_offline_packages_tenant ON offline_data_packages(tenant_id);
CREATE INDEX idx_offline_packages_type ON offline_data_packages(package_type);
CREATE INDEX idx_offline_packages_current ON offline_data_packages(is_current) WHERE is_current = true;

-- =============================================
-- VERSIONING & AUDIT SYSTEM
-- =============================================

CREATE TABLE methodology_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_code VARCHAR(30) UNIQUE NOT NULL, -- 'USDA_2025.1', 'ZIMBABWE_2024.2'
    version_name VARCHAR(100) NOT NULL,
    methodology_source VARCHAR(100) NOT NULL, -- 'USDA_FCIC25080', 'ZBS_STANDARD'
    
    -- Version Details
    release_date DATE NOT NULL,
    effective_date DATE NOT NULL,
    deprecation_date DATE,
    version_description TEXT,
    
    -- What's Included
    included_crops JSONB, -- Array of crop codes
    included_methods JSONB, -- Array of method codes
    major_changes JSONB, -- Significant changes from previous version
    
    -- Compliance & Approval
    approval_status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'approved', 'active', 'deprecated'
    approved_by VARCHAR(100), -- Approving authority
    regulatory_reference VARCHAR(100), -- Regulation or standard reference
    
    is_current_version BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_methodology_versions_code ON methodology_versions(version_code);
CREATE INDEX idx_methodology_versions_current ON methodology_versions(is_current_version) WHERE is_current_version = true;

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id), -- For tenant isolation
    user_id UUID REFERENCES users(id),
    
    -- Action Details
    action_type VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'calculate', 'sync'
    entity_type VARCHAR(50) NOT NULL, -- 'claim', 'assessment_session', 'sample_data'
    entity_id UUID, -- ID of affected entity
    
    -- Change Details
    old_values JSONB, -- Previous values (for updates)
    new_values JSONB, -- New values
    changed_fields JSONB, -- Array of field names that changed
    
    -- Context Information
    session_id UUID, -- Assessment session if applicable
    device_id VARCHAR(100), -- Device used for action
    ip_address INET, -- IP address of request
    user_agent TEXT, -- Browser/app information
    
    -- Additional Metadata
    business_context VARCHAR(100), -- Why the action was taken
    risk_level VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high'
    compliance_flags JSONB DEFAULT '[]', -- Compliance-related flags
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_action ON audit_logs(action_type);
CREATE INDEX idx_audit_timestamp ON audit_logs(created_at);

-- =============================================
-- CONFIGURATION & SYSTEM TABLES
-- =============================================

CREATE TABLE tenant_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Assessment Configurations
    default_sampling_overrides JSONB DEFAULT '{}', -- Custom sampling rules
    quality_thresholds JSONB DEFAULT '{}', -- Custom quality requirements
    calculation_overrides JSONB DEFAULT '{}', -- Custom calculation parameters
    
    -- Report Configurations
    report_templates JSONB DEFAULT '{}', -- Custom report templates
    branding_config JSONB DEFAULT '{}', -- Logo, colors, etc.
    required_signatures JSONB DEFAULT '[]', -- Who must sign reports
    
    -- Operational Configurations
    assessment_sla_hours INTEGER DEFAULT 72, -- Target completion time
    quality_control_level VARCHAR(20) DEFAULT 'standard', -- 'basic', 'standard', 'strict'
    auto_routing_rules JSONB DEFAULT '{}', -- Automatic claim assignment rules
    
    -- Integration Configurations
    external_api_configs JSONB DEFAULT '{}', -- Third-party integrations
    notification_settings JSONB DEFAULT '{}', -- Email, SMS, webhook settings
    data_retention_days INTEGER DEFAULT 2555, -- 7 years default
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id)
);

CREATE INDEX idx_tenant_configs_tenant ON tenant_configurations(tenant_id);

-- =============================================
-- TRIGGERS FOR AUTOMATED FIELDS
-- =============================================

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_farms_updated_at BEFORE UPDATE ON farms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fields_updated_at BEFORE UPDATE ON fields FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assessment_sessions_updated_at BEFORE UPDATE ON assessment_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Calculate field area from boundary
CREATE OR REPLACE FUNCTION calculate_field_area()
RETURNS TRIGGER AS $$
BEGIN
    NEW.field_area = ST_Area(ST_Transform(NEW.field_boundary, 3857)) / 10000; -- Convert to hectares
    NEW.field_center = ST_Centroid(NEW.field_boundary);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_field_area_trigger BEFORE INSERT OR UPDATE ON fields FOR EACH ROW EXECUTE FUNCTION calculate_field_area();

-- =============================================
-- REFINED VIEWS FOR COMMON QUERIES
-- =============================================

-- Active Claims with Variety Information
CREATE VIEW active_claims_with_varieties AS
SELECT 
    c.id,
    c.claim_number,
    c.insured_name,
    c.claim_status,
    cr.crop_name,
    cv.variety_name,
    cv.maturity_category,
    cv.maturity_days,
    c.insured_area,
    c.expected_yield,
    c.loss_notification_date,
    u.first_name || ' ' || u.last_name AS assessor_name,
    f.farm_name,
    fd.field_name,
    p.peril_name,
    c.peril_severity_level,
    c.created_at
FROM claims c
LEFT JOIN crops cr ON c.crop_id = cr.id
LEFT JOIN crop_varieties cv ON c.variety_id = cv.id
LEFT JOIN users u ON c.assigned_assessor_id = u.id
LEFT JOIN farms f ON c.farm_id = f.id
LEFT JOIN fields fd ON c.field_id = fd.id
LEFT JOIN perils p ON c.suspected_peril_id = p.id
WHERE c.claim_status NOT IN ('completed', 'settled', 'cancelled');

-- Assessment Sessions with Growth Stage Timing
CREATE VIEW assessment_sessions_with_timing AS
SELECT 
    s.id,
    s.claim_id,
    c.claim_number,
    s.session_number,
    s.session_status,
    cr.crop_name,
    cv.variety_name,
    cv.maturity_category,
    p.peril_name,
    m.method_name,
    g.stage_name AS growth_stage,
    vgr.days_from_planting_typical AS expected_stage_days,
    (s.visit_date - c.planting_date) AS actual_days_from_planting,
    s.visit_date,
    s.final_appraisal,
    s.confidence_score,
    u.first_name || ' ' || u.last_name AS assessor_name,
    s.created_at
FROM assessment_sessions s
JOIN claims c ON s.claim_id = c.id
JOIN crops cr ON c.crop_id = cr.id
LEFT JOIN crop_varieties cv ON c.variety_id = cv.id
JOIN perils p ON s.peril_id = p.id
JOIN assessment_methods m ON s.method_id = m.id
JOIN growth_stages g ON s.growth_stage_id = g.id
LEFT JOIN variety_growth_stage_ranges vgr ON cv.id = vgr.variety_id AND g.id = vgr.growth_stage_id
JOIN users u ON s.assessor_id = u.id;

-- Peril Severity Summary
CREATE VIEW peril_severity_summary AS
SELECT 
    p.peril_code,
    p.peril_name,
    p.has_severity_levels,
    ltd.table_name AS severity_table_name,
    COUNT(c.id) AS total_claims,
    AVG(c.final_loss_percentage) AS avg_loss_percentage
FROM perils p
LEFT JOIN lookup_table_definitions ltd ON p.peril_severity_lookup_id = ltd.id
LEFT JOIN claims c ON p.id = c.suspected_peril_id
WHERE p.is_active = true
GROUP BY p.peril_code, p.peril_name, p.has_severity_levels, ltd.table_name
ORDER BY total_claims DESC;

-- =============================================
-- INITIAL DATA SETUP SCRIPT (REFINED)
-- =============================================

-- Insert System Roles
INSERT INTO roles (role_name, role_description, permissions, is_system_role) VALUES
('system_admin', 'System Administrator', '["manage_all", "admin_panel", "user_management", "tenant_management"]', true),
('tenant_admin', 'Tenant Administrator', '["manage_tenant", "user_management", "claim_management", "report_access"]', true),
('assessor', 'Field Assessor', '["create_assessment", "edit_assessment", "capture_evidence", "submit_report"]', true),
('supervisor', 'Assessment Supervisor', '["review_assessment", "approve_report", "quality_control", "assign_claims"]', true),
('viewer', 'Report Viewer', '["view_reports", "view_claims", "basic_access"]', true);

-- Insert Base Crops (Starting with Maize)
INSERT INTO crops (crop_code, crop_name, scientific_name, crop_family, standard_units, methodology_source) VALUES
('MAIZE', 'Maize (Corn)', 'Zea mays', 'Cereals', 
 '{"yield": "tonnes_per_hectare", "weight": "kg", "area": "hectares", "moisture": "percent"}',
 'USDA_FCIC25080');

-- Get maize crop ID for subsequent inserts
-- INSERT INTO crop_varieties - will be done with actual variety data

-- Insert Core Perils with Severity Lookup Integration
INSERT INTO perils (peril_code, peril_name, peril_category, description, has_severity_levels) VALUES
('DROUGHT', 'Drought/Insufficient Moisture', 'weather', 'Insufficient soil moisture for normal plant development', true),
('HAIL', 'Hail Damage', 'weather', 'Direct and indirect damage from hailstorms', true),
('HEAT_STRESS', 'Heat Stress/Hot Winds', 'weather', 'Excessive heat causing plant stress and yield reduction', false),
('COLD_DAMAGE', 'Cold Weather/Frost', 'weather', 'Low temperatures causing plant damage or death', false),
('DISEASE_FUNGAL', 'Fungal Disease', 'biological', 'Damage from fungal pathogens', true),
('DISEASE_BACTERIAL', 'Bacterial Disease', 'biological', 'Damage from bacterial pathogens', false),
('DISEASE_VIRAL', 'Viral Disease', 'biological', 'Damage from viral pathogens', false),
('PEST_INSECT', 'Insect Pest Damage', 'biological', 'Damage from insect pests', true),
('PEST_WILDLIFE', 'Wildlife Damage', 'biological', 'Damage from birds, mammals, and other wildlife', false),
('FLOODING', 'Flooding/Excessive Moisture', 'weather', 'Damage from standing water and excessive soil moisture', true),
('EMERGENCE_FAILURE', 'Emergence Failure', 'environmental', 'Poor or failed crop emergence', false);

-- Insert Assessment Methods
INSERT INTO assessment_methods (method_code, method_name, method_description, methodology_source, calculation_type) VALUES
('STAND_REDUCTION', 'Stand Reduction Method', 'Assessment based on surviving plant population', 'USDA_FCIC25080', 'percentage_potential'),
('HAIL_DAMAGE', 'Hail Damage Method', 'Assessment of direct and indirect hail damage', 'USDA_FCIC25080', 'percentage_potential'),
('MATURITY_LINE_WEIGHT', 'Maturity Line Weight Method', 'Assessment based on ear maturity and weight', 'USDA_FCIC25080', 'direct_weight'),
('WEIGHT_METHOD', 'Weight Method', 'Assessment based on ear weight after physiological maturity', 'USDA_FCIC25080', 'direct_weight'),
('TONNAGE_METHOD', 'Tonnage Method (Silage)', 'Assessment based on fresh tonnage for silage production', 'USDA_FCIC25080', 'direct_weight');

-- Create the current methodology version
INSERT INTO methodology_versions (version_code, version_name, methodology_source, release_date, effective_date, 
                                 version_description, included_crops, included_methods, is_current_version, approval_status) VALUES
('USDA_2025.1', 'USDA Corn Loss Adjustment Standards 2025', 'USDA_FCIC25080', '2024-11-18', '2025-01-01',
 'Complete digitization of USDA FCIC-25080 Corn Loss Adjustment Standards Handbook with variety timing and severity scaling',
 '["MAIZE"]', '["STAND_REDUCTION", "HAIL_DAMAGE", "MATURITY_LINE_WEIGHT", "WEIGHT_METHOD", "TONNAGE_METHOD"]',
 true, 'approved');
```

## 3. KEY REFINEMENTS EXPLANATION

### Refinement 1: Growth Stage Range for Varieties

**New Table: `variety_growth_stage_ranges`**
```sql
CREATE TABLE variety_growth_stage_ranges (
    variety_id UUID NOT NULL REFERENCES crop_varieties(id),
    growth_stage_id UUID NOT NULL REFERENCES growth_stages(id),
    days_from_planting_min INTEGER NOT NULL,
    days_from_planting_max INTEGER NOT NULL,  
    days_from_planting_typical INTEGER NOT NULL,
    stage_duration_days INTEGER DEFAULT 3,
    temperature_adjustments JSONB
);
```

**Updated: `crop_varieties` table**
```sql
ALTER TABLE crop_varieties ADD COLUMN growth_stage_range JSONB NOT NULL;
ALTER TABLE crop_varieties ADD COLUMN maturity_category VARCHAR(20);
```

**Why This Improves the Schema:**
- **Accurate Growth Stage Estimation**: SC403 (early) vs SC719 (late) have different timing
- **Better Method Selection**: Growth stage determines applicable assessment methods
- **Climate Adjustment**: Temperature effects on variety timing
- **Quality Control**: Validates field assessments against expected timing

**Usage Example:**
```sql
-- Get expected growth stage for a variety on a specific date
SELECT gs.stage_name, vgsr.days_from_planting_typical
FROM variety_growth_stage_ranges vgsr
JOIN growth_stages gs ON vgsr.growth_stage_id = gs.id
WHERE vgsr.variety_id = 'sc403_variety_id'
AND 45 BETWEEN vgsr.days_from_planting_min AND vgsr.days_from_planting_max;
```

### Refinement 2: Peril Severity Lookup Integration

**Updated: `perils` table**
```sql
ALTER TABLE perils ADD COLUMN has_severity_levels BOOLEAN DEFAULT false;
ALTER TABLE perils ADD COLUMN peril_severity_lookup_id UUID REFERENCES lookup_table_definitions(id);
```

**Updated: `claims` table**
```sql
ALTER TABLE claims ADD COLUMN peril_severity_level VARCHAR(20);
```

**Why This Improves the Schema:**
- **Modular Severity Scales**: Each peril can have its own severity methodology
- **Extensible Design**: Easy to add new severity scales without schema changes
- **Method Selection**: Severity level affects which assessment method to use
- **Better Loss Estimation**: Severity-adjusted calculations

**Example Severity Lookup Tables:**
```sql
-- Drought Severity Scale
INSERT INTO lookup_table_definitions (table_code, table_name, table_category) VALUES
('DROUGHT_SEVERITY_SCALE', 'Drought Severity Classification', 'severity');

-- Hail Severity Scale  
INSERT INTO lookup_table_definitions (table_code, table_name, table_category) VALUES
('HAIL_SEVERITY_SCALE', 'Hail Damage Severity Scale', 'severity');

-- Link to perils
UPDATE perils SET peril_severity_lookup_id = (
  SELECT id FROM lookup_table_definitions WHERE table_code = 'DROUGHT_SEVERITY_SCALE'
) WHERE peril_code = 'DROUGHT';
```

## 4. ENHANCED VIEWS AND FUNCTIONALITY

### New View: Assessment Sessions with Timing Analysis
```sql
CREATE VIEW assessment_sessions_with_timing AS
SELECT 
    s.id,
    c.claim_number,
    cv.variety_name,
    cv.maturity_category,
    g.stage_name AS growth_stage,
    vgr.days_from_planting_typical AS expected_stage_days,
    (s.visit_date - c.planting_date) AS actual_days_from_planting,
    ABS(vgr.days_from_planting_typical - (s.visit_date - c.planting_date)) AS timing_variance_days,
    s.final_appraisal,
    s.confidence_score
FROM assessment_sessions s
JOIN claims c ON s.claim_id = c.id
LEFT JOIN crop_varieties cv ON c.variety_id = cv.id
JOIN growth_stages g ON s.growth_stage_id = g.id
LEFT JOIN variety_growth_stage_ranges vgr ON cv.id = vgr.variety_id AND g.id = vgr.growth_stage_id;
```

### New View: Peril Severity Analysis
```sql
CREATE VIEW peril_severity_summary AS
SELECT 
    p.peril_code,
    p.peril_name,
    p.has_severity_levels,
    ltd.table_name AS severity_table_name,
    COUNT(c.id) AS total_claims,
    AVG(c.final_loss_percentage) AS avg_loss_percentage,
    c.peril_severity_level,
    COUNT(*) OVER (PARTITION BY c.peril_severity_level) as claims_by_severity
FROM perils p
LEFT JOIN lookup_table_definitions ltd ON p.peril_severity_lookup_id = ltd.id
LEFT JOIN claims c ON p.id = c.suspected_peril_id
WHERE p.is_active = true
GROUP BY p.peril_code, p.peril_name, p.has_severity_levels, ltd.table_name, c.peril_severity_level;
```

## Summary of Improvements

These refinements make the schema even more robust:

✅ **Variety-Specific Timing** - Accurate growth stage estimation for early/late varieties  
✅ **Modular Severity Scaling** - Extensible severity classification system  
✅ **Better Assessment Accuracy** - Variety timing validates field assessments  
✅ **Enhanced Analytics** - Severity-based loss analysis and reporting  
✅ **Future-Proof Design** - Easy to add new varieties and severity scales  

The schema now perfectly handles the nuances of different crop varieties and the complexity of peril severity assessment, making it even more scientifically rigorous and operationally excellent.
