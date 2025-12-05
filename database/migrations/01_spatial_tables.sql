-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create FARMS table with spatial column
CREATE TABLE IF NOT EXISTS farms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    owner_user_id UUID REFERENCES users(id),
    
    farm_code VARCHAR(50) NOT NULL,
    farm_name VARCHAR(100) NOT NULL,
    farmer_name VARCHAR(100),
    farmer_contact JSONB,
    
    -- Spatial column for farm location (Point)
    farm_location GEOMETRY(POINT, 4326),
    
    farm_address JSONB,
    total_farm_area DECIMAL(10,2),
    operational_area DECIMAL(10,2),
    
    farm_characteristics JSONB,
    registration_numbers JSONB,
    insurance_history JSONB,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT unique_tenant_farm_code UNIQUE (tenant_id, farm_code)
);

-- Create spatial index for farm location
CREATE INDEX IF NOT EXISTS idx_farms_location ON farms USING GIST (farm_location);
CREATE INDEX IF NOT EXISTS idx_farms_tenant ON farms(tenant_id);

-- Create FIELDS table with spatial columns
CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    
    field_code VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    
    -- Spatial columns (Polygon boundary and Center point)
    field_boundary GEOMETRY(POLYGON, 4326) NOT NULL,
    field_center GEOMETRY(POINT, 4326),
    field_area DECIMAL(8,2) NOT NULL,
    
    soil_characteristics JSONB,
    irrigation_type VARCHAR(30),
    elevation_meters INTEGER,
    slope_characteristics JSONB,
    
    access_notes TEXT,
    historical_yields JSONB,
    land_use_restrictions JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_farm_field_code UNIQUE (farm_id, field_code)
);

-- Create spatial indexes for fields
CREATE INDEX IF NOT EXISTS idx_fields_boundary ON fields USING GIST (field_boundary);
CREATE INDEX IF NOT EXISTS idx_fields_center ON fields USING GIST (field_center);
CREATE INDEX IF NOT EXISTS idx_fields_farm ON fields(farm_id);
