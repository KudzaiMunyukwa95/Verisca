-- =============================================
-- VERISCA V2 DATABASE SCHEMA - REFINED VERSION
-- Pure SQL Implementation with Growth Stage Ranges & Peril Severity
-- =============================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- TENANTS & AUTHENTICATION
-- =============================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code VARCHAR(20) UNIQUE NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    tenant_type VARCHAR(20) NOT NULL CHECK (tenant_type IN ('insurer', 'assessor_company', 'system_admin')),
    contact_email VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20),
    address JSONB,
    billing_info JSONB,
    tenant_config JSONB DEFAULT '{}',
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
    role_name VARCHAR(50) UNIQUE NOT NULL,
    role_description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
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
    employee_id VARCHAR(50),
    assessor_license VARCHAR(50),
    specializations JSONB DEFAULT '[]',
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
    crop_code VARCHAR(20) UNIQUE NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(100),
    crop_family VARCHAR(50),
    typical_growing_season JSONB,
    physiological_characteristics JSONB,
    standard_units JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    methodology_source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_crops_code ON crops(crop_code);
CREATE INDEX idx_crops_active ON crops(is_active) WHERE is_active = true;

CREATE TABLE crop_varieties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    variety_code VARCHAR(30) NOT NULL,
    variety_name VARCHAR(100) NOT NULL,
    variety_type VARCHAR(50),
    maturity_days INTEGER,
    maturity_category VARCHAR(20),
    growth_stage_range JSONB NOT NULL,
    characteristics JSONB,
    growing_regions JSONB,
    yield_potential_range JSONB,
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
    stage_code VARCHAR(30) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    stage_order INTEGER NOT NULL,
    base_days_from_planting INTEGER NOT NULL,
    stage_characteristics JSONB NOT NULL,
    assessment_implications JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(crop_id, stage_code),
    UNIQUE(crop_id, stage_order)
);

CREATE INDEX idx_growth_stages_crop ON growth_stages(crop_id);
CREATE INDEX idx_growth_stages_order ON growth_stages(crop_id, stage_order);

CREATE TABLE variety_growth_stage_ranges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variety_id UUID NOT NULL REFERENCES crop_varieties(id) ON DELETE CASCADE,
    growth_stage_id UUID NOT NULL REFERENCES growth_stages(id) ON DELETE CASCADE,
    days_from_planting_min INTEGER NOT NULL,
    days_from_planting_max INTEGER NOT NULL,
    days_from_planting_typical INTEGER NOT NULL,
    stage_duration_days INTEGER DEFAULT 3,
    temperature_adjustments JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(variety_id, growth_stage_id),
    CHECK (days_from_planting_min <= days_from_planting_typical),
    CHECK (days_from_planting_typical <= days_from_planting_max)
);

CREATE INDEX idx_variety_stages_variety ON variety_growth_stage_ranges(variety_id);
CREATE INDEX idx_variety_stages_stage ON variety_growth_stage_ranges(growth_stage_id);

-- =============================================
-- LOOKUP TABLE SYSTEM (must come before perils)
-- =============================================

CREATE TABLE lookup_table_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_code VARCHAR(50) UNIQUE NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    table_description TEXT,
    crop_id UUID REFERENCES crops(id),
    method_id UUID,
    table_category VARCHAR(30),
    source_reference VARCHAR(100),
    table_structure JSONB NOT NULL,
    interpolation_rules JSONB,
    validation_rules JSONB,
    table_type VARCHAR(30) NOT NULL,
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
    input_values JSONB NOT NULL,
    output_value DECIMAL(10,4) NOT NULL,
    output_label VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    row_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_lookup_data_table ON lookup_table_data(table_definition_id);
CREATE INDEX idx_lookup_data_inputs ON lookup_table_data USING GIN (input_values);
CREATE INDEX idx_lookup_data_output ON lookup_table_data(output_value);

CREATE TABLE lookup_table_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_definition_id UUID NOT NULL REFERENCES lookup_table_definitions(id),
    version_number VARCHAR(20) NOT NULL,
    methodology_version_id UUID,
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
-- PERIL & ASSESSMENT METHOD SYSTEM
-- =============================================

CREATE TABLE perils (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peril_code VARCHAR(30) UNIQUE NOT NULL,
    peril_name VARCHAR(100) NOT NULL,
    peril_category VARCHAR(50) NOT NULL,
    description TEXT,
    typical_indicators JSONB,
    seasonality JSONB,
    has_severity_levels BOOLEAN DEFAULT false,
    peril_severity_lookup_id UUID REFERENCES lookup_table_definitions(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_perils_code ON perils(peril_code);
CREATE INDEX idx_perils_category ON perils(peril_category);
CREATE INDEX idx_perils_severity_lookup ON perils(peril_severity_lookup_id);

CREATE TABLE assessment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_code VARCHAR(30) UNIQUE NOT NULL,
    method_name VARCHAR(100) NOT NULL,
    method_description TEXT,
    methodology_source VARCHAR(100),
    calculation_type VARCHAR(30) NOT NULL,
    required_measurements JSONB NOT NULL,
    required_calculations JSONB NOT NULL,
    quality_requirements JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_methods_code ON assessment_methods(method_code);

-- Add foreign key constraint for method_id in lookup_table_definitions
ALTER TABLE lookup_table_definitions ADD CONSTRAINT fk_lookup_method 
FOREIGN KEY (method_id) REFERENCES assessment_methods(id);

CREATE TABLE crop_peril_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crops(id),
    peril_id UUID NOT NULL REFERENCES perils(id),
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    applicable_growth_stages JSONB NOT NULL,
    severity_thresholds JSONB,
    priority_order INTEGER DEFAULT 1,
    special_conditions JSONB,
    method_modifications JSONB,
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
    special_considerations JSONB,
    calculation_modifications JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(method_id, growth_stage_id)
);

-- =============================================
-- SAMPLING RULES & CALCULATION SYSTEM
-- =============================================

CREATE TABLE sampling_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crops(id),
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    rule_name VARCHAR(100) NOT NULL,
    field_area_min DECIMAL(8,2),
    field_area_max DECIMAL(8,2),
    sample_size_formula JSONB NOT NULL,
    minimum_samples INTEGER NOT NULL,
    additional_sample_rule JSONB,
    sampling_pattern VARCHAR(30) DEFAULT 'random',
    exclusion_zones JSONB,
    quality_requirements JSONB,
    tenant_overrides JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(crop_id, method_id, rule_name)
);

CREATE INDEX idx_sampling_rules_crop_method ON sampling_rules(crop_id, method_id);

CREATE TABLE calculation_formulas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formula_code VARCHAR(50) UNIQUE NOT NULL,
    formula_name VARCHAR(100) NOT NULL,
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    formula_expression TEXT NOT NULL,
    input_parameters JSONB NOT NULL,
    output_parameters JSONB NOT NULL,
    validation_rules JSONB,
    rounding_rules JSONB,
    formula_version VARCHAR(20) DEFAULT 'v1.0',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_formulas_code ON calculation_formulas(formula_code);
CREATE INDEX idx_formulas_method ON calculation_formulas(method_id);

CREATE TABLE quality_factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_code VARCHAR(50) UNIQUE NOT NULL,
    factor_name VARCHAR(100) NOT NULL,
    crop_id UUID REFERENCES crops(id),
    factor_type VARCHAR(30) NOT NULL,
    adjustment_table_id UUID REFERENCES lookup_table_definitions(id),
    default_value DECIMAL(8,4),
    value_range JSONB,
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
    owner_user_id UUID REFERENCES users(id),
    farm_code VARCHAR(50) NOT NULL,
    farm_name VARCHAR(100) NOT NULL,
    farmer_name VARCHAR(100),
    farmer_contact JSONB,
    farm_location GEOMETRY(POINT, 4326),
    farm_address JSONB,
    total_farm_area DECIMAL(10,2),
    operational_area DECIMAL(10,2),
    farm_characteristics JSONB,
    registration_numbers JSONB,
    insurance_history JSONB,
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
    field_code VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    field_boundary GEOMETRY(POLYGON, 4326) NOT NULL,
    field_area DECIMAL(8,2) NOT NULL,
    field_center GEOMETRY(POINT, 4326),
    soil_characteristics JSONB,
    irrigation_type VARCHAR(30),
    elevation_meters INTEGER,
    slope_characteristics JSONB,
    access_notes TEXT,
    historical_yields JSONB,
    land_use_restrictions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(farm_id, field_code)
);

CREATE INDEX idx_fields_farm ON fields(farm_id);
CREATE INDEX idx_fields_boundary ON fields USING GIST (field_boundary);
CREATE INDEX idx_fields_center ON fields USING GIST (field_center);

-- =============================================
-- VERSIONING SYSTEM (needed before claims)
-- =============================================

CREATE TABLE methodology_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_code VARCHAR(30) UNIQUE NOT NULL,
    version_name VARCHAR(100) NOT NULL,
    methodology_source VARCHAR(100) NOT NULL,
    release_date DATE NOT NULL,
    effective_date DATE NOT NULL,
    deprecation_date DATE,
    version_description TEXT,
    included_crops JSONB,
    included_methods JSONB,
    major_changes JSONB,
    approval_status VARCHAR(20) DEFAULT 'draft',
    approved_by VARCHAR(100),
    regulatory_reference VARCHAR(100),
    is_current_version BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_methodology_versions_code ON methodology_versions(version_code);
CREATE INDEX idx_methodology_versions_current ON methodology_versions(is_current_version) WHERE is_current_version = true;

-- =============================================
-- CLAIMS & ASSESSMENT SESSIONS
-- =============================================

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    policy_number VARCHAR(100) NOT NULL,
    insured_name VARCHAR(100) NOT NULL,
    farm_id UUID NOT NULL REFERENCES farms(id),
    field_id UUID NOT NULL REFERENCES fields(id),
    crop_id UUID NOT NULL REFERENCES crops(id),
    variety_id UUID REFERENCES crop_varieties(id),
    planting_date DATE NOT NULL,
    expected_harvest_date DATE,
    expected_yield DECIMAL(8,2) NOT NULL,
    insured_area DECIMAL(8,2) NOT NULL,
    sum_insured DECIMAL(12,2),
    loss_notification_date DATE NOT NULL,
    suspected_peril_id UUID REFERENCES perils(id),
    peril_severity_level VARCHAR(20),
    loss_description TEXT,
    estimated_loss_percentage DECIMAL(5,2),
    claim_status VARCHAR(30) DEFAULT 'reported',
    priority VARCHAR(20) DEFAULT 'normal',
    assigned_assessor_id UUID REFERENCES users(id),
    assignment_date TIMESTAMP WITH TIME ZONE,
    target_completion_date DATE,
    actual_completion_date TIMESTAMP WITH TIME ZONE,
    final_loss_percentage DECIMAL(5,2),
    final_yield_estimate DECIMAL(8,2),
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
    session_number INTEGER NOT NULL DEFAULT 1,
    assessor_id UUID NOT NULL REFERENCES users(id),
    method_id UUID NOT NULL REFERENCES assessment_methods(id),
    peril_id UUID NOT NULL REFERENCES perils(id),
    growth_stage_id UUID NOT NULL REFERENCES growth_stages(id),
    methodology_version_id UUID REFERENCES methodology_versions(id),
    session_status VARCHAR(30) DEFAULT 'planned',
    session_type VARCHAR(30) DEFAULT 'primary',
    visit_date DATE,
    visit_start_time TIMESTAMP WITH TIME ZONE,
    visit_end_time TIMESTAMP WITH TIME ZONE,
    weather_conditions JSONB,
    field_access_notes TEXT,
    assessed_growth_stage_confidence DECIMAL(3,2),
    variety_stage_adjustment JSONB,
    sampling_plan JSONB NOT NULL,
    actual_samples_collected INTEGER,
    sampling_quality_score DECIMAL(3,2),
    raw_assessment_data JSONB,
    calculation_results JSONB,
    final_appraisal DECIMAL(8,2),
    confidence_score DECIMAL(3,2),
    quality_flags JSONB DEFAULT '[]',
    total_photos_captured INTEGER DEFAULT 0,
    total_gps_points_captured INTEGER DEFAULT 0,
    evidence_quality_score DECIMAL(3,2),
    field_notes TEXT,
    app_version VARCHAR(20),
    device_info JSONB,
    gps_accuracy_meters DECIMAL(5,2),
    session_created_offline BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'pending',
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
    sample_number INTEGER NOT NULL,
    gps_location GEOMETRY(POINT, 4326) NOT NULL,
    gps_accuracy_meters DECIMAL(5,2),
    gps_altitude_meters DECIMAL(7,2),
    gps_timestamp TIMESTAMP WITH TIME ZONE,
    sample_type VARCHAR(30) DEFAULT 'primary',
    sample_area_hectares DECIMAL(8,6) NOT NULL,
    row_width_cm DECIMAL(5,1),
    row_length_meters DECIMAL(6,2),
    sample_quality_score DECIMAL(3,2),
    distance_from_edge_meters DECIMAL(5,1),
    representative_score DECIMAL(3,2),
    validation_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sample_points_session ON sample_points(session_id);
CREATE INDEX idx_sample_points_location ON sample_points USING GIST (gps_location);
CREATE INDEX idx_sample_points_number ON sample_points(session_id, sample_number);

CREATE TABLE sample_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sample_point_id UUID NOT NULL REFERENCES sample_points(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    measurement_category VARCHAR(30) NOT NULL,
    numeric_value DECIMAL(12,4),
    text_value VARCHAR(500),
    boolean_value BOOLEAN,
    json_value JSONB,
    measurement_unit VARCHAR(20),
    measurement_method VARCHAR(50),
    measurement_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    measurement_confidence DECIMAL(3,2),
    validation_status VARCHAR(20) DEFAULT 'pending',
    validation_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sample_data_point ON sample_data(sample_point_id);
CREATE INDEX idx_sample_data_type ON sample_data(data_type);
CREATE INDEX idx_sample_data_category ON sample_data(measurement_category);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    sample_point_id UUID REFERENCES sample_points(id),
    evidence_type VARCHAR(30) NOT NULL,
    evidence_category VARCHAR(30) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    gps_location GEOMETRY(POINT, 4326),
    gps_accuracy_meters DECIMAL(5,2),
    compass_direction DECIMAL(5,1),
    caption TEXT,
    auto_tags JSONB DEFAULT '[]',
    manual_tags JSONB DEFAULT '[]',
    analysis_results JSONB,
    device_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    server_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    device_info JSONB,
    camera_settings JSONB,
    uploaded_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'pending',
    thumbnail_path VARCHAR(500),
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
    calculation_step INTEGER NOT NULL,
    formula_id UUID REFERENCES calculation_formulas(id),
    calculation_type VARCHAR(50) NOT NULL,
    calculation_name VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    lookup_table_references JSONB,
    intermediate_results JSONB,
    final_result DECIMAL(12,4) NOT NULL,
    result_units VARCHAR(20) NOT NULL,
    validation_status VARCHAR(20) DEFAULT 'valid',
    validation_messages JSONB DEFAULT '[]',
    calculation_confidence DECIMAL(3,2),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calculation_version VARCHAR(20),
    recalculated_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_calculations_session ON calculations(session_id);
CREATE INDEX idx_calculations_step ON calculations(session_id, calculation_step);
CREATE INDEX idx_calculations_type ON calculations(calculation_type);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id),
    claim_id UUID NOT NULL REFERENCES claims(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    report_type VARCHAR(30) NOT NULL,
    report_template VARCHAR(50),
    report_status VARCHAR(20) DEFAULT 'generating',
    pdf_file_path VARCHAR(500),
    pdf_file_size_bytes BIGINT,
    excel_file_path VARCHAR(500),
    raw_data_path VARCHAR(500),
    report_summary JSONB NOT NULL,
    executive_summary TEXT,
    recommendations TEXT,
    assessor_signature JSONB,
    supervisor_approval JSONB,
    insured_acknowledgment JSONB,
    auto_sent_to_insurer BOOLEAN DEFAULT false,
    distribution_log JSONB DEFAULT '[]',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by UUID REFERENCES users(id),
    generation_duration_seconds INTEGER,
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
    device_id VARCHAR(100) UNIQUE NOT NULL,
    device_name VARCHAR(100),
    device_type VARCHAR(30),
    device_os_version VARCHAR(50),
    app_version VARCHAR(20),
    gps_capable BOOLEAN DEFAULT true,
    camera_capable BOOLEAN DEFAULT true,
    offline_storage_mb INTEGER,
    last_location GEOMETRY(POINT, 4326),
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
    sync_type VARCHAR(30) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    sync_direction VARCHAR(10) NOT NULL,
    priority INTEGER DEFAULT 5,
    sync_status VARCHAR(20) DEFAULT 'pending',
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    next_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_data JSONB,
    conflict_data JSONB,
    conflict_resolution VARCHAR(30),
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
    package_type VARCHAR(30) NOT NULL,
    package_version VARCHAR(20) NOT NULL,
    included_crops JSONB,
    included_tables JSONB,
    package_size_mb DECIMAL(8,2),
    file_path VARCHAR(500),
    checksum VARCHAR(64),
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
-- AUDIT SYSTEM
-- =============================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB,
    session_id UUID,
    device_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    business_context VARCHAR(100),
    risk_level VARCHAR(20) DEFAULT 'low',
    compliance_flags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_action ON audit_logs(action_type);
CREATE INDEX idx_audit_timestamp ON audit_logs(created_at);

-- =============================================
-- CONFIGURATION TABLES
-- =============================================

CREATE TABLE tenant_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    default_sampling_overrides JSONB DEFAULT '{}',
    quality_thresholds JSONB DEFAULT '{}',
    calculation_overrides JSONB DEFAULT '{}',
    report_templates JSONB DEFAULT '{}',
    branding_config JSONB DEFAULT '{}',
    required_signatures JSONB DEFAULT '[]',
    assessment_sla_hours INTEGER DEFAULT 72,
    quality_control_level VARCHAR(20) DEFAULT 'standard',
    auto_routing_rules JSONB DEFAULT '{}',
    external_api_configs JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    data_retention_days INTEGER DEFAULT 2555,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id)
);

CREATE INDEX idx_tenant_configs_tenant ON tenant_configurations(tenant_id);

-- =============================================
-- TRIGGERS FOR AUTOMATED FIELDS
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_farms_updated_at BEFORE UPDATE ON farms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fields_updated_at BEFORE UPDATE ON fields FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assessment_sessions_updated_at BEFORE UPDATE ON assessment_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION calculate_field_area()
RETURNS TRIGGER AS $$
BEGIN
    NEW.field_area = ST_Area(ST_Transform(NEW.field_boundary, 3857)) / 10000;
    NEW.field_center = ST_Centroid(NEW.field_boundary);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_field_area_trigger BEFORE INSERT OR UPDATE ON fields FOR EACH ROW EXECUTE FUNCTION calculate_field_area();

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

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
    ABS(vgr.days_from_planting_typical - (s.visit_date - c.planting_date)) AS timing_variance_days,
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

CREATE VIEW peril_severity_summary AS
SELECT 
    p.peril_code,
    p.peril_name,
    p.has_severity_levels,
    ltd.table_name AS severity_table_name,
    c.peril_severity_level,
    COUNT(c.id) AS total_claims,
    AVG(c.final_loss_percentage) AS avg_loss_percentage,
    COUNT(*) OVER (PARTITION BY p.peril_code, c.peril_severity_level) as claims_by_severity
FROM perils p
LEFT JOIN lookup_table_definitions ltd ON p.peril_severity_lookup_id = ltd.id
LEFT JOIN claims c ON p.id = c.suspected_peril_id
WHERE p.is_active = true
GROUP BY p.peril_code, p.peril_name, p.has_severity_levels, ltd.table_name, c.peril_severity_level
ORDER BY total_claims DESC;

-- =============================================
-- INITIAL DATA SETUP
-- =============================================
