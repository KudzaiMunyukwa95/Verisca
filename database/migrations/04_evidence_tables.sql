-- Clean up
DROP TABLE IF EXISTS evidence CASCADE;

-- Create EVIDENCE table
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    uploaded_by_id UUID REFERENCES users(id),
    
    claim_id UUID REFERENCES claims(id),
    session_id UUID REFERENCES assessment_sessions(id),
    
    -- Geotagging
    location GEOMETRY(POINT, 4326),
    gps_accuracy_meters FLOAT,
    
    filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    content_type VARCHAR(100),
    file_size_bytes INTEGER,
    
    url VARCHAR(500),
    
    description VARCHAR(500),
    tags JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_session ON evidence(session_id);
