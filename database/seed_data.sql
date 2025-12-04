-- =============================================
-- VERISCA DATABASE - SEED DATA
-- Run this AFTER the main schema is loaded
-- =============================================

-- Insert default roles
INSERT INTO roles (role_name, role_description, permissions, is_system_role) VALUES
('system_admin', 'System Administrator', '["manage_all", "admin_panel", "user_management", "tenant_management"]', true),
('tenant_admin', 'Tenant Administrator', '["manage_tenant", "user_management", "claim_management", "report_access"]', true),
('assessor', 'Field Assessor', '["create_assessment", "edit_assessment", "capture_evidence", "submit_report"]', true),
('supervisor', 'Assessment Supervisor', '["review_assessment", "approve_report", "quality_control", "assign_claims"]', true),
('viewer', 'Report Viewer', '["view_reports", "view_claims", "basic_access"]', true);

-- Insert Maize crop
INSERT INTO crops (crop_code, crop_name, scientific_name, crop_family, standard_units, methodology_source) VALUES
('MAIZE', 'Maize (Corn)', 'Zea mays', 'Cereals', 
 '{"yield": "tonnes_per_hectare", "weight": "kg", "area": "hectares", "moisture": "percent"}',
 'USDA_FCIC25080');

-- Get the maize crop ID for use in other inserts
DO $$
DECLARE
    maize_id UUID;
BEGIN
    SELECT id INTO maize_id FROM crops WHERE crop_code = 'MAIZE';
    
    -- Insert maize growth stages
    INSERT INTO growth_stages (crop_id, stage_code, stage_name, stage_order, base_days_from_planting, stage_characteristics) VALUES
    (maize_id, 'EMERGENCE', 'Emergence', 1, 7, '{"description": "Seedling emerges from soil", "identification": "Coleoptile visible above soil surface"}'),
    (maize_id, 'V3', 'Third Leaf', 2, 21, '{"description": "Three leaf collars visible", "identification": "Count leaf collars, not leaf tips"}'),
    (maize_id, 'V6', 'Sixth Leaf', 3, 35, '{"description": "Six leaf collars visible", "identification": "Growing point still below soil surface"}'),
    (maize_id, 'V10', 'Tenth Leaf', 4, 49, '{"description": "Ten leaf collars visible", "identification": "Growing point above soil surface"}'),
    (maize_id, 'VT', 'Tasseling', 5, 63, '{"description": "Tassel fully emerged", "identification": "Tassel visible, shedding pollen"}'),
    (maize_id, 'R1', 'Silking', 6, 66, '{"description": "Silks visible outside husks", "identification": "First silks emerge from ear shoot"}'),
    (maize_id, 'R6', 'Physiological Maturity', 7, 120, '{"description": "Black layer visible at kernel base", "identification": "Maximum dry matter accumulation"}');
END $$;

-- Insert perils
INSERT INTO perils (peril_code, peril_name, peril_category, description, has_severity_levels) VALUES
('DROUGHT', 'Drought/Insufficient Moisture', 'weather', 'Insufficient soil moisture for normal plant development', true),
('HAIL', 'Hail Damage', 'weather', 'Direct and indirect damage from hailstorms', true),
('HEAT_STRESS', 'Heat Stress/Hot Winds', 'weather', 'Excessive heat causing plant stress and yield reduction', false);

-- Insert assessment methods with proper JSONB values
INSERT INTO assessment_methods (method_code, method_name, method_description, methodology_source, calculation_type, required_measurements, required_calculations) VALUES
('STAND_REDUCTION', 'Stand Reduction Method', 'Assessment based on surviving plant population', 'USDA_FCIC25080', 'percentage_potential',
 '["surviving_plants", "normal_plant_population", "row_width", "row_length"]',
 '["percent_stand", "percent_potential", "sample_appraisal"]'),
 
('HAIL_DAMAGE', 'Hail Damage Method', 'Assessment of direct and indirect hail damage', 'USDA_FCIC25080', 'percentage_potential',
 '["destroyed_plants", "crippled_plants", "leaf_defoliation", "ear_damage"]',
 '["direct_damage", "indirect_damage", "total_damage_percent"]');

-- Insert methodology version
INSERT INTO methodology_versions (version_code, version_name, methodology_source, release_date, effective_date, 
                                 version_description, included_crops, included_methods, is_current_version, approval_status) VALUES
('USDA_2025.1', 'USDA Corn Loss Adjustment Standards 2025', 'USDA_FCIC25080', '2024-11-18', '2025-01-01',
 'Complete digitization of USDA FCIC-25080 with variety timing and severity scaling',
 '["MAIZE"]', '["STAND_REDUCTION", "HAIL_DAMAGE"]',
 true, 'approved');

-- Create a test tenant
INSERT INTO tenants (tenant_code, tenant_name, tenant_type, contact_email, is_active) VALUES
('DEMO', 'Demo Insurance Company', 'insurer', 'admin@demo.com', true);

-- Create a test user (password is 'password123')
DO $$
DECLARE
    demo_tenant_id UUID;
    assessor_role_id UUID;
BEGIN
    SELECT id INTO demo_tenant_id FROM tenants WHERE tenant_code = 'DEMO';
    SELECT id INTO assessor_role_id FROM roles WHERE role_name = 'assessor';
    
    INSERT INTO users (tenant_id, role_id, username, email, password_hash, first_name, last_name, is_active, email_verified) VALUES
    (demo_tenant_id, assessor_role_id, 'demo_assessor', 'assessor@demo.com', 
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7TLvxRKxNu', -- password: password123
     'Demo', 'Assessor', true, true);
END $$;
