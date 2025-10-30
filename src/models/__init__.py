"""Models package for VMware Inventory application."""

# Import migration target models
from src.models.migration_target import (
    MigrationTarget,
    MigrationScenario,
    MigrationWave,
    PlatformType,
    MigrationStrategy
)

__all__ = [
    "MigrationTarget",
    "MigrationScenario",
    "MigrationWave",
    "PlatformType",
    "MigrationStrategy",
]
