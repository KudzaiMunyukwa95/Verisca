-- Create LOOKUP TABLES table
CREATE TABLE IF NOT EXISTS lookup_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(50) NOT NULL,
    description VARCHAR(200),
    
    -- Generic schema
    input_value FLOAT NOT NULL,
    stage_or_condition VARCHAR(50),
    output_value FLOAT NOT NULL,
    metadata_json JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_lookup_cell UNIQUE (table_name, input_value, stage_or_condition)
);

CREATE INDEX IF NOT EXISTS idx_lookup_query ON lookup_tables(table_name, input_value, stage_or_condition);
