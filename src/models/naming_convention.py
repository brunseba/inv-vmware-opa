"""Database models for VM naming conventions."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class NamingConvention(Base):
    """Model representing a VM naming convention definition.
    
    A naming convention defines a pattern for parsing VM names into structured fields.
    Example pattern: <D><Y><K><S><XXX><YYY> where each segment has a fixed length.
    """
    
    __tablename__ = "naming_conventions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    total_length: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100))
    
    # Relationships
    fields: Mapped[list["NamingConventionField"]] = relationship(
        "NamingConventionField",
        back_populates="convention",
        cascade="all, delete-orphan",
        order_by="NamingConventionField.position"
    )
    analyses: Mapped[list["VMNamingAnalysis"]] = relationship(
        "VMNamingAnalysis",
        back_populates="convention",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<NamingConvention(name='{self.name}', pattern='{self.pattern}', active={self.is_active})>"


class NamingConventionField(Base):
    """Model representing a field within a naming convention.
    
    Each field represents a segment of the VM name pattern with:
    - Fixed position in the name
    - Fixed length
    - Optional list of possible values
    - Semantic meaning (e.g., datacenter, environment, application)
    """
    
    __tablename__ = "naming_convention_fields"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    convention_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('naming_conventions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    length: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    possible_values: Mapped[dict | None] = mapped_column(JSON)
    is_required: Mapped[bool] = mapped_column(default=True)
    validation_regex: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    convention: Mapped["NamingConvention"] = relationship(
        "NamingConvention",
        back_populates="fields"
    )
    
    __table_args__ = (
        UniqueConstraint('convention_id', 'field_name', name='_convention_field_name_uc'),
        UniqueConstraint('convention_id', 'position', name='_convention_field_position_uc'),
    )
    
    def __repr__(self) -> str:
        return f"<NamingConventionField(name='{self.field_name}', position={self.position}, length={self.length})>"


class VMNamingAnalysis(Base):
    """Model storing parsed VM name analysis results.
    
    This table stores the results of parsing VM names according to a naming convention.
    The field_values JSON contains the extracted values for each field in the convention.
    """
    
    __tablename__ = "vm_naming_analysis"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vm_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('virtual_machines.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    convention_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('naming_conventions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    vm_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    field_values: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_valid: Mapped[bool] = mapped_column(default=True, index=True)
    validation_errors: Mapped[dict | None] = mapped_column(JSON)
    match_confidence: Mapped[int | None] = mapped_column(Integer)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    convention: Mapped["NamingConvention"] = relationship(
        "NamingConvention",
        back_populates="analyses"
    )
    
    __table_args__ = (
        UniqueConstraint('vm_id', 'convention_id', name='_vm_convention_analysis_uc'),
    )
    
    def __repr__(self) -> str:
        return f"<VMNamingAnalysis(vm_name='{self.vm_name}', convention_id={self.convention_id}, valid={self.is_valid})>"
