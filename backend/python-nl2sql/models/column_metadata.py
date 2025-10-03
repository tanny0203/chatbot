from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class ColumnMetadata(Base):
    __tablename__ = "column_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(50), nullable=False)  # INTEGER, FLOAT, TEXT, BOOLEAN, DATE
    sql_type = Column(String(50), nullable=False)   # INTEGER, DOUBLE, VARCHAR, BOOLEAN, DATE
    nullable = Column(Boolean, nullable=False)
    is_category = Column(Boolean, nullable=False)
    is_boolean = Column(Boolean, nullable=False)
    is_date = Column(Boolean, nullable=False)
    unique_count = Column(Integer, nullable=False)
    null_count = Column(Integer, nullable=False)
    
    # Numeric statistics (NULL for non-numeric columns)
    min_value = Column(Float)
    max_value = Column(Float)
    mean_value = Column(Float)
    median_value = Column(Float)
    std_value = Column(Float)
    
    # JSONB fields for flexible storage
    sample_values = Column(JSONB)  # Array of up to 5 examples
    top_values = Column(JSONB)     # Array of {value, count} objects
    enum_values = Column(JSONB)    # Array of all categorical values
    value_mappings = Column(JSONB) # code -> human readable
    synonym_mappings = Column(JSONB) # query synonyms
    example_queries = Column(JSONB) # dataset-specific examples
    description = Column(String, nullable=False)
    
    # Add created_at for tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to file
    file = relationship("File", back_populates="columns")

# Update File model to include the relationship
from .file import File
File.columns = relationship("ColumnMetadata", back_populates="file", cascade="all, delete-orphan")