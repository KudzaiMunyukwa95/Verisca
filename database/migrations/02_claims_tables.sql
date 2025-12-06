-- CLEANUP (for dev/testing phase)
DROP TABLE IF EXISTS assessment_samples CASCADE;
DROP TABLE IF EXISTS assessment_sessions CASCADE;
DROP TABLE IF EXISTS claims CASCADE;

-- Create CLAIMS table
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    claim_number VARCHAR(50) NOT NULL,
    
    farm_id UUID NOT NULL REFERENCES farms(id),
    field_id UUID NOT NULL REFERENCES fields(id),
    
    peril_type VARCHAR(50) NOT NULL,
    date_of_loss TIMESTAMPTZ NOT NULL,
    loss_description TEXT,
    
    status VARCHAR(20) DEFAULT 'reported',
    assigned_assessor_id UUID REFERENCES users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id),
    
    CONSTRAINT unique_claim_number UNIQUE (claim_number)
);

CREATE INDEX IF NOT EXISTS idx_claims_tenant_status ON claims(tenant_id, status);

-- Create ASSESSMENT SESSIONS table
CREATE TABLE IF NOT EXISTS assessment_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    assessor_id UUID NOT NULL REFERENCES users(id),
    
    date_started TIMESTAMPTZ DEFAULT NOW(),
    date_completed TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'in_progress',
    
    assessment_method VARCHAR(50) NOT NULL,
    growth_stage VARCHAR(50),
    
    weather_conditions JSONB,
    crop_conditions JSONB,
    
    calculated_result JSONB,
    assessor_notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_claim ON assessment_sessions(claim_id);

-- Create ASSESSMENT SAMPLES table (Spatial)
CREATE TABLE IF NOT EXISTS assessment_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    
    sample_number INTEGER NOT NULL,
    
    -- Precise location of sample
    sample_location GEOMETRY(POINT, 4326),
    gps_accuracy_meters FLOAT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Dynamic measurements (JSONB for flexibility aka NoSQL-in-SQL)
    measurements JSONB NOT NULL,
    
    evidence_refs JSONB,
    notes TEXT,
    
    CONSTRAINT unique_session_sample_num UNIQUE (session_id, sample_number)
);

CREATE INDEX IF NOT EXISTS idx_samples_session ON assessment_samples(session_id);
-- Spatial index
CREATE INDEX IF NOT EXISTS idx_samples_location ON assessment_samples USING GIST (sample_location);
