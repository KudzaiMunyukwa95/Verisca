-- Quick fix for schema - Run this in pgAdmin to drop and recreate the problematic table

-- First, drop the foreign key constraint
ALTER TABLE lookup_table_definitions DROP CONSTRAINT IF EXISTS fk_lookup_method;

-- Drop the assessment_methods table
DROP TABLE IF EXISTS assessment_methods CASCADE;

-- Recreate with default values for JSONB fields
CREATE TABLE assessment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_code VARCHAR(30) UNIQUE NOT NULL,
    method_name VARCHAR(100) NOT NULL,
    method_description TEXT,
    methodology_source VARCHAR(100),
    calculation_type VARCHAR(30) NOT NULL,
    required_measurements JSONB NOT NULL DEFAULT '[]',
    required_calculations JSONB NOT NULL DEFAULT '[]',
    quality_requirements JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_methods_code ON assessment_methods(method_code);

-- Re-add the foreign key constraint
ALTER TABLE lookup_table_definitions ADD CONSTRAINT fk_lookup_method 
FOREIGN KEY (method_id) REFERENCES assessment_methods(id);
