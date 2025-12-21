"""Models package for VMware Inventory application."""

# Import base
from src.models.base import Base

# Import migration target models
from src.models.migration_target import (
    MigrationScenario,
    MigrationStrategy,
    MigrationStrategyConfig,
    MigrationTarget,
    MigrationWave,
    PlatformType,
)

# Import naming convention models
from src.models.naming_convention import NamingConvention, NamingConventionField, VMNamingAnalysis
from src.models.schema_version import SchemaVersion

# Import VMware models
from src.models.vmware import FolderLabel, Label, SchemaVersion, VirtualMachine, VMLabel

__all__ = [
    "Base",
    "VirtualMachine",
    "Label",
    "VMLabel",
    "FolderLabel",
    "SchemaVersion",
    "MigrationTarget",
    "MigrationScenario",
    "MigrationWave",
    "MigrationStrategyConfig",
    "PlatformType",
    "MigrationStrategy",
    "NamingConvention",
    "NamingConventionField",
    "VMNamingAnalysis",
]
