# 3. DATABASE SCHEMA DESIGN EXPLANATION

## Overall Architecture Philosophy

The Verisca V2 database schema is designed around **separation of concerns** and **maximum extensibility**. Each component serves a specific purpose while maintaining loose coupling with other components.

### Core Design Principles

1. **Crop-Agnostic Foundation**: The system can handle any crop without code changes
2. **Method Independence**: Assessment methods are configurable, not hard-coded
3. **Tenant Isolation**: Complete data segregation between insurers
4. **Offline-First**: Built for rural mobile use with intermittent connectivity
5. **Audit Compliance**: Every change is tracked for regulatory requirements
6. **Version Control**: Methodologies can evolve while maintaining historical accuracy

## Component Architecture Explanations

### 1. Multi-Tenant Structure

**Why This Design:**
```sql
tenants -> users -> claims/farms
```

**Rationale:**
- **Complete Isolation**: Each insurer (tenant) has isolated data
- **Scalable Security**: Row-level security can be enforced by tenant_id
- **Flexible Billing**: Different subscription tiers per tenant
- **Custom Configuration**: Each insurer can have unique business rules

**Key Features:**
- `tenant_code` provides human-readable identification
- `tenant_config` JSONB allows unlimited customization without schema changes
- Foreign keys ensure data cannot leak between tenants

### 2. Generic Crop Management System

**Why This Design:**
```sql
crops -> crop_varieties
crops -> growth_stages
crops -> crop_peril_methods
```

**Rationale:**
- **Future-Proof**: Adding wheat, soybeans, tobacco requires only data, not code
- **Variety-Specific**: Each variety can have different timing and characteristics
- **Growth Stage Flexibility**: Different crops have different stage definitions
- **Method Mapping**: Links perils to appropriate assessment methods per crop

**Key Features:**
- `physiological_characteristics` JSONB stores crop-specific data
- `standard_units` defines measurement units (metric for Zimbabwe)
- `growth_stages.stage_order` ensures proper temporal sequencing
- `assessment_implications` guides method selection

### 3. Peril and Method Management

**Why This Design:**
```sql
perils }--{ crop_peril_methods {--{ assessment_methods
```

**Rationale:**
- **Many-to-Many Flexibility**: One peril can use multiple methods
- **Growth Stage Dependency**: Methods apply only at certain growth stages
- **Crop-Specific Adaptations**: Same peril may need different methods per crop
- **Priority Ordering**: Preferred method selection based on conditions

**Key Features:**
- `applicable_growth_stages` JSONB array defines when method applies
- `method_modifications` allows crop-specific adjustments
- `priority_order` enables automatic method selection
- `special_conditions` handles complex business rules

### 4. Revolutionary Lookup Table Architecture

**Why This Generic Design:**
```sql
lookup_table_definitions -> lookup_table_data
                        -> lookup_table_versions
```

**Rationale:**
- **Universal Application**: Works for USDA exhibits, FAO standards, local tables
- **Version Control**: Historical accuracy when methodologies change
- **Interpolation Ready**: Built-in support for value interpolation
- **Multi-Dimensional**: Handles complex chart structures (growth stage + stand percentage)

**Key Features:**
- `table_structure` JSONB defines schema for each table type
- `input_values` JSONB allows complex multi-parameter lookups
- `interpolation_rules` defines how to calculate intermediate values
- `validation_rules` ensures data integrity

**Example Usage:**
```json
{
  "table_code": "MAIZE_STAND_REDUCTION_EARLY",
  "input_values": {"stand_percent": 85, "growth_stage": "V6"},
  "output_value": 92.5
}
```

### 5. Spatial Data Management

**Why PostGIS Integration:**
```sql
farms.farm_location GEOMETRY(POINT, 4326)
fields.field_boundary GEOMETRY(POLYGON, 4326)
sample_points.gps_location GEOMETRY(POINT, 4326)
```

**Rationale:**
- **GPS Accuracy**: Native spatial operations for distance, area, containment
- **Field Validation**: Automatic area calculation from GPS boundaries
- **Sample Quality**: Distance-from-edge calculations for sample validation
- **Mapping Integration**: Direct compatibility with mapping services

**Key Features:**
- WGS84 (EPSG:4326) for global GPS compatibility
- Automatic area calculation triggers
- Spatial indexes for fast geographic queries
- Field center point calculation for navigation

### 6. Assessment Session Architecture

**Why Session-Based Design:**
```sql
claims -> assessment_sessions -> sample_points -> sample_data
                            -> evidence
                            -> calculations
```

**Rationale:**
- **Multiple Visits**: Claims may require follow-up assessments
- **Complete Audit Trail**: Every measurement tracked to source
- **Quality Control**: Session-level quality scoring and validation
- **Offline Capability**: Sessions can be created offline and synced later

**Key Features:**
- `session_number` allows multiple assessments per claim
- `sampling_plan` JSONB stores complete sampling configuration
- `raw_assessment_data` preserves original field measurements
- `methodology_version_id` ensures historical accuracy

### 7. Evidence Management System

**Why Comprehensive Evidence Tracking:**
```sql
evidence -> sample_points (optional)
        -> assessment_sessions
```

**Rationale:**
- **Regulatory Compliance**: Insurance claims require thorough documentation
- **Quality Assurance**: Photo evidence validates field measurements
- **Dispute Resolution**: Complete evidence chain for claim disputes
- **AI Enhancement**: Structured data for future computer vision integration

**Key Features:**
- `evidence_category` classifies photos by purpose
- `auto_tags` and `manual_tags` for AI and user annotations
- `analysis_results` JSONB for future AI integration
- `compass_direction` for photo orientation context

### 8. Mobile-First Sync Architecture

**Why Offline-First Design:**
```sql
device_registrations -> sync_queue
                   -> offline_data_packages
```

**Rationale:**
- **Rural Reality**: African farms often lack reliable internet
- **Seamless UX**: Assessors work normally whether online or offline
- **Conflict Resolution**: Handles data conflicts when multiple devices sync
- **Bandwidth Optimization**: Only sync changed data

**Key Features:**
- `sync_queue` manages bidirectional data flow
- `conflict_resolution` handles merge conflicts
- `offline_data_packages` provide complete offline capability
- `priority` system ensures critical data syncs first

### 9. Calculation Engine Integration

**Why Separate Calculations Table:**
```sql
assessment_sessions -> calculations -> formula_id
                                 -> input_data
                                 -> lookup_table_references
```

**Rationale:**
- **Audit Trail**: Every calculation step is recorded
- **Recalculation**: Values can be recalculated with updated formulas
- **Validation**: Step-by-step verification of results
- **Transparency**: Complete visibility into how results were derived

**Key Features:**
- `calculation_step` preserves order of operations
- `intermediate_results` JSONB stores all calculation steps
- `validation_status` flags suspicious results
- `recalculated_count` tracks formula updates

### 10. Versioning and Compliance System

**Why Complete Version Control:**
```sql
methodology_versions -> lookup_table_versions
                   -> assessment_sessions
                   -> audit_logs
```

**Rationale:**
- **Regulatory Compliance**: Insurance regulations require methodology documentation
- **Historical Accuracy**: Claims must use methodology valid at time of assessment
- **Change Management**: Controlled rollout of methodology updates
- **Legal Defensibility**: Complete audit trail for dispute resolution

**Key Features:**
- `methodology_version_id` links all data to specific methodology version
- `effective_date` and `deprecation_date` control methodology lifecycle
- `approval_status` ensures only approved methodologies are used
- `audit_logs` capture every system change with context

## Scalability Considerations

### Index Strategy
- **Primary Indexes**: On all foreign keys and frequently queried fields
- **Spatial Indexes**: GIST indexes on all geometry columns
- **Composite Indexes**: Multi-column indexes for common query patterns
- **Partial Indexes**: Only index active records where applicable

### Performance Optimizations
- **Denormalization**: Strategic denormalization in reports table
- **JSON Indexes**: GIN indexes on JSONB columns for fast JSON queries
- **View Materialization**: Common queries pre-computed as materialized views
- **Partitioning Ready**: Schema supports table partitioning by tenant or date

### Storage Considerations
- **Binary Data**: Evidence files stored in cloud storage, not database
- **JSON Compression**: JSONB provides automatic compression
- **Archive Strategy**: Old data can be archived while maintaining referential integrity
- **Backup Strategy**: Schema supports point-in-time recovery

## Multi-Tenant Security Architecture

### Data Isolation
- **Row-Level Security**: Every table includes tenant_id for isolation
- **API Layer**: Application enforces tenant-based access control
- **Cross-Tenant Prevention**: Foreign key constraints prevent data leakage

### Access Control
- **Role-Based Permissions**: Flexible permission system per role
- **User Context**: All operations include user context for audit
- **Device Registration**: Known devices only for security

## Future Enhancement Support

### AI/ML Integration Ready
- **Evidence Analysis**: `analysis_results` JSONB for computer vision results
- **Quality Scoring**: Confidence scores throughout for ML training
- **Feature Engineering**: Rich structured data for model development

### Blockchain Integration Ready
- **Audit Trail**: Complete change history for blockchain verification
- **Hash Fields**: Schema can add hash fields for blockchain anchoring
- **Immutable Records**: Methodology versions provide immutable reference points

### API Development Ready
- **RESTful Design**: Schema maps cleanly to REST endpoints
- **GraphQL Ready**: Relationships support efficient GraphQL queries
- **Event Sourcing**: Audit logs support event-driven architectures

## Migration and Deployment Strategy

### Schema Versioning
- **Database Migrations**: Each schema change has a numbered migration
- **Backward Compatibility**: New features don't break existing functionality
- **Rollback Support**: All migrations include rollback procedures

### Data Migration
- **Tenant Onboarding**: New insurers can be added without downtime
- **Lookup Table Updates**: New methodology versions deployed seamlessly
- **Historical Preservation**: Legacy data remains accessible during upgrades

## Conclusion

This schema design provides a robust, scalable foundation for Verisca that can:

1. **Scale Globally**: Multi-tenant architecture supports unlimited insurers
2. **Add Crops Easily**: New crops require only configuration, not code changes  
3. **Handle Complexity**: Generic lookup tables support any assessment methodology
4. **Work Offline**: Complete mobile-first sync architecture
5. **Ensure Compliance**: Comprehensive audit trails and version control
6. **Enable Innovation**: Extensible design ready for AI/ML enhancement

The schema strikes the optimal balance between flexibility and structure, providing a solid foundation for building the world's leading digital crop assessment platform.
