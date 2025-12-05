"""Schema version management service."""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import List, Dict, Optional
import logging

from src.models import SchemaVersion

logger = logging.getLogger(__name__)

# Migration to semver mapping
# Maps migration number to corresponding application version
MIGRATION_TO_SEMVER = {
    "001": "1.2.0",  # Initial labelling system
    "002": "1.3.0",  # Migration planning tables
    "003": "1.4.0",  # Naming convention tables
    "004": "1.5.0",  # Label source tracking
}

# Current schema - the latest migration number
CURRENT_SCHEMA_VERSION = "004"

# Current application version in semver
CURRENT_APP_VERSION = "0.9.0"


class SchemaService:
    """Service for managing database schema versions."""
    
    def __init__(self, session: Session):
        """Initialize schema service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    @staticmethod
    def migration_to_semver(migration: str) -> str:
        """Convert migration number to semver.
        
        Args:
            migration: Migration number (e.g., "004")
            
        Returns:
            Semver version (e.g., "1.5.0")
        """
        return MIGRATION_TO_SEMVER.get(migration, "unknown")
    
    @staticmethod
    def get_latest_migration() -> str:
        """Get the latest migration number.
        
        Returns:
            Latest migration number
        """
        return CURRENT_SCHEMA_VERSION
    
    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """Compare two migration version numbers.
        
        Args:
            v1: First version (e.g., "003")
            v2: Second version (e.g., "004")
            
        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        try:
            n1 = int(v1)
            n2 = int(v2)
            if n1 < n2:
                return -1
            elif n1 > n2:
                return 1
            return 0
        except (ValueError, TypeError):
            # Fallback to string comparison
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            return 0
    
    def get_current_version(self) -> Optional[SchemaVersion]:
        """Get the current schema version from database.
        
        Returns:
            Current SchemaVersion object or None if not set
        """
        try:
            return self.session.query(SchemaVersion).filter(
                SchemaVersion.is_current == True
            ).order_by(SchemaVersion.applied_at.desc()).first()
        except Exception as e:
            logger.warning(f"Could not retrieve current schema version: {e}")
            return None
    
    def get_all_versions(self) -> List[SchemaVersion]:
        """Get all schema versions ordered by application date.
        
        Returns:
            List of SchemaVersion objects
        """
        return self.session.query(SchemaVersion).order_by(
            SchemaVersion.applied_at.desc()
        ).all()
    
    def get_version_history(self) -> List[Dict]:
        """Get schema version history as a list of dictionaries.
        
        Returns:
            List of dictionaries containing version information
        """
        versions = self.get_all_versions()
        return [{
            'version': v.version,
            'description': v.description,
            'applied_at': v.applied_at,
            'applied_by': v.applied_by,
            'is_current': v.is_current,
            'tables_added': v.tables_added,
            'tables_modified': v.tables_modified,
            'tables_removed': v.tables_removed
        } for v in versions]
    
    def record_version(
        self,
        version: str,
        description: str,
        applied_by: str = "system",
        migration_script: str = None,
        tables_added: str = None,
        tables_modified: str = None,
        tables_removed: str = None,
        notes: str = None,
        rollback_available: bool = False,
        rollback_script: str = None
    ) -> SchemaVersion:
        """Record a new schema version.
        
        Args:
            version: Version string (e.g., "1.0.0", "1.1.0")
            description: Human-readable description of changes
            applied_by: Who applied the migration
            migration_script: Name of migration script
            tables_added: Comma-separated list of tables added
            tables_modified: Comma-separated list of tables modified
            tables_removed: Comma-separated list of tables removed
            notes: Additional notes
            rollback_available: Whether rollback is possible
            rollback_script: Name of rollback script
            
        Returns:
            Created SchemaVersion object
        """
        # Create new version record (is_current will be determined after)
        schema_version = SchemaVersion(
            version=version,
            description=description,
            applied_by=applied_by,
            migration_script=migration_script,
            tables_added=tables_added,
            tables_modified=tables_modified,
            tables_removed=tables_removed,
            is_current=False,  # Will be updated below
            rollback_available=rollback_available,
            rollback_script=rollback_script,
            notes=notes
        )
        
        self.session.add(schema_version)
        self.session.flush()  # Flush to get the record in the database
        
        # Now determine which version should be marked as current (highest migration number)
        all_versions = self.session.query(SchemaVersion).all()
        highest_version = None
        highest_num = -1
        
        for v in all_versions:
            try:
                num = int(v.version)
                if num > highest_num:
                    highest_num = num
                    highest_version = v
            except (ValueError, TypeError):
                # Skip non-numeric versions
                pass
        
        # Mark all as not current first
        self.session.query(SchemaVersion).update({'is_current': False})
        
        # Mark the highest as current
        if highest_version:
            highest_version.is_current = True
        
        self.session.commit()
        
        logger.info(f"Recorded schema version {version}: {description}")
        return schema_version
    
    def initialize_schema_tracking(self) -> SchemaVersion:
        """Initialize schema version tracking with current version.
        
        This should be called after creating all tables for the first time.
        
        Returns:
            Created SchemaVersion object
        """
        # Check if already initialized
        existing = self.get_current_version()
        if existing:
            logger.info(f"Schema tracking already initialized at version {existing.version}")
            return existing
        
        # Record initial version
        return self.record_version(
            version=CURRENT_SCHEMA_VERSION,
            description="Initial database schema with VM inventory and labelling support",
            applied_by="system",
            tables_added="virtual_machines,labels,vm_labels,folder_labels,schema_versions",
            notes="Base schema includes: VirtualMachine model with full RVTools support, "
                  "Label system with VM and folder labelling, Schema version tracking"
        )
    
    def check_schema_compatibility(self) -> Dict[str, any]:
        """Check if database schema is compatible with application.
        
        Returns:
            Dictionary with compatibility information:
            - compatible: bool
            - current_version: str or None
            - current_semver: str or None
            - expected_version: str
            - expected_semver: str
            - message: str
        """
        current = self.get_current_version()
        expected_semver = self.migration_to_semver(CURRENT_SCHEMA_VERSION)
        
        if not current:
            return {
                'compatible': False,
                'current_version': None,
                'current_semver': None,
                'expected_version': CURRENT_SCHEMA_VERSION,
                'expected_semver': expected_semver,
                'message': 'No schema version recorded in database. Schema tracking needs initialization.'
            }
        
        # Get current semver
        current_semver = self.migration_to_semver(current.version)
        
        # Check if versions match
        comparison = self.compare_versions(current.version, CURRENT_SCHEMA_VERSION)
        
        if comparison < 0:
            # Database is behind
            return {
                'compatible': False,
                'current_version': current.version,
                'current_semver': current_semver,
                'expected_version': CURRENT_SCHEMA_VERSION,
                'expected_semver': expected_semver,
                'message': f'Schema version outdated. Database is at migration {current.version} '
                          f'({current_semver}), application expects {CURRENT_SCHEMA_VERSION} '
                          f'({expected_semver}). Run schema-upgrade to apply pending migrations.'
            }
        elif comparison > 0:
            # Database is ahead (shouldn't happen normally)
            return {
                'compatible': False,
                'current_version': current.version,
                'current_semver': current_semver,
                'expected_version': CURRENT_SCHEMA_VERSION,
                'expected_semver': expected_semver,
                'message': f'Schema version ahead of application. Database is at migration {current.version} '
                          f'({current_semver}), application expects {CURRENT_SCHEMA_VERSION} '
                          f'({expected_semver}). Please upgrade the application.'
            }
        
        # Versions match
        return {
            'compatible': True,
            'current_version': current.version,
            'current_semver': current_semver,
            'expected_version': CURRENT_SCHEMA_VERSION,
            'expected_semver': expected_semver,
            'message': f'Schema is up to date at migration {CURRENT_SCHEMA_VERSION} ({expected_semver})'
        }
    
    def get_schema_info(self) -> Dict:
        """Get comprehensive schema information.
        
        Returns:
            Dictionary with schema details including version, tables, and compatibility
        """
        inspector = inspect(self.session.bind)
        tables = inspector.get_table_names()
        
        current_version = self.get_current_version()
        compatibility = self.check_schema_compatibility()
        
        return {
            'current_version': current_version.version if current_version else None,
            'current_semver': compatibility.get('current_semver'),
            'expected_version': CURRENT_SCHEMA_VERSION,
            'expected_semver': compatibility.get('expected_semver'),
            'app_version': CURRENT_APP_VERSION,
            'compatible': compatibility['compatible'],
            'tables_count': len(tables),
            'tables': tables,
            'schema_tracking_enabled': 'schema_versions' in tables,
            'version_history_count': len(self.get_all_versions()),
            'last_update': current_version.applied_at if current_version else None
        }
