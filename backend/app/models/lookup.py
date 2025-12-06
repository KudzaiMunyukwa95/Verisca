from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, Index, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class LookupTable(Base):
    """
    Stores USDA assessment charts and tables (Exhibits 11, 12, etc.)
    Designed for flexible storage of multi-dimensional lookup data.
    """
    __tablename__ = "lookup_tables"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name = Column(String(50), nullable=False) # e.g., "exhibit11_standReduction"
    description = Column(String(200))
    
    # Generic schema fields to handle different table structures
    # For Exhibit 11/12: input_value might be "percentStand"
    input_value = Column(Float, nullable=False) # The row identifier (e.g., Stand %, Moisture %)
    
    # For Exhibit 11/12: stage_or_condition might be "8thLeaf"
    stage_or_condition = Column(String(50)) # The column identifier
    
    # The result value from the chart
    output_value = Column(Float, nullable=False) # The cell value (Percent Potential, Factor, etc.)
    
    # Metadata for complex logic (e.g., interpolation grouping)
    metadata_json = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('table_name', 'input_value', 'stage_or_condition', name='unique_lookup_cell'),
        Index('idx_lookup_query', 'table_name', 'input_value', 'stage_or_condition'),
    )
