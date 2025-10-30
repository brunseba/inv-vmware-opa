"""Schema version tracking for database migrations."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from src.models.base import Base


class SchemaVersion(Base):
    """Track database schema versions and migrations."""
    
    __tablename__ = "schema_versions"  # Match existing table name (plural)
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    version = Column(String(50), nullable=False)
    description = Column(String(500), nullable=False)
    applied_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    applied_by = Column(String(100))
    migration_script = Column(String(255))
    tables_added = Column(Text)
    tables_modified = Column(Text)
    tables_removed = Column(Text)
    is_current = Column(Boolean, nullable=False, default=False)
    rollback_available = Column(Boolean, nullable=False, default=False)
    rollback_script = Column(String(255))
    notes = Column(Text)
    
    def __repr__(self):
        return f"<SchemaVersion(version={self.version}, is_current={self.is_current}, applied_at={self.applied_at})>"
