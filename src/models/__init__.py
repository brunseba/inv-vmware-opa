"""Models package for VMware Inventory application."""

# Import base
from src.models.base import Base

# Import VMware models
from src.models.vmware import (
    VirtualMachine,
    Label,
    VMLabel,
    FolderLabel,
    SchemaVersion
)

# Import migration target models
from src.models.migration_target import (
    MigrationTarget,
    MigrationScenario,
    MigrationWave,
    MigrationStrategyConfig,
    PlatformType,
    MigrationStrategy
)
from src.models.schema_version import SchemaVersion

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
]
