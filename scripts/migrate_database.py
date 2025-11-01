#!/usr/bin/env python3
"""
Unified database migration manager with version tracking.

This script manages all database schema migrations and tracks applied versions.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime


# Define all migrations with version numbers
MIGRATIONS = {
    "1.0.0": {
        "description": "Add cost separation (migration vs runtime)",
        "table": "migration_scenarios",
        "columns": [
            ("estimated_migration_cost", "REAL"),
            ("estimated_runtime_cost_monthly", "REAL"),
            ("migration_cost_breakdown", "TEXT"),
            ("runtime_cost_breakdown", "TEXT"),
        ]
    },
    "1.1.0": {
        "description": "Add VM resource metrics",
        "table": "migration_scenarios",
        "columns": [
            ("vm_count", "INTEGER"),
            ("total_vcpus", "INTEGER"),
            ("total_memory_gb", "REAL"),
            ("total_storage_gb", "REAL"),
        ]
    },
    "1.4.0": {
        "description": "Add replication efficiency parameters for realistic duration calculations",
        "tables": {
            "migration_targets": [
                ("compression_ratio", "REAL DEFAULT 0.6"),
                ("dedup_ratio", "REAL DEFAULT 0.8"),
                ("change_rate_percent", "REAL DEFAULT 0.10"),
                ("network_protocol_overhead", "REAL DEFAULT 1.2"),
                ("delta_sync_count", "INTEGER DEFAULT 2"),
            ],
            "migration_strategy_configs": [
                ("replication_efficiency", "REAL DEFAULT 1.0"),
                ("parallel_replication_factor", "REAL DEFAULT 1.0"),
            ]
        }
    }
}


def create_schema_version_table(cursor):
    """Create schema_versions table if it doesn't exist (uses plural for consistency with SQLAlchemy model)."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(500) NOT NULL,
            applied_at DATETIME NOT NULL,
            applied_by VARCHAR(100) DEFAULT 'migration_script',
            migration_script VARCHAR(255),
            tables_added TEXT,
            tables_modified TEXT,
            tables_removed TEXT,
            is_current BOOLEAN NOT NULL DEFAULT 0,
            rollback_available BOOLEAN NOT NULL DEFAULT 0,
            rollback_script VARCHAR(255),
            notes TEXT
        )
    """)


def get_current_version(cursor):
    """Get the current schema version."""
    try:
        cursor.execute("SELECT version FROM schema_versions WHERE is_current = 1 LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]
        # Fallback to latest if no current version marked
        cursor.execute("SELECT version FROM schema_versions ORDER BY applied_at DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.OperationalError:
        # schema_versions table doesn't exist
        return None


def get_applied_versions(cursor):
    """Get list of all applied versions."""
    try:
        cursor.execute("SELECT version FROM schema_versions ORDER BY applied_at")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def get_table_columns(cursor, table_name):
    """Get list of columns for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def apply_migration(cursor, version, migration_info):
    """Apply a single migration."""
    print(f"\n📦 Applying migration {version}: {migration_info['description']}")
    
    migrations_applied = 0
    
    # Handle old format (single table with "columns" key)
    if "columns" in migration_info:
        table_name = migration_info.get("table", "migration_scenarios")
        existing_columns = get_table_columns(cursor, table_name)
        
        for column_name, column_type in migration_info["columns"]:
            if column_name not in existing_columns:
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                print(f"  ✓ Adding column to {table_name}: {column_name} ({column_type})")
                cursor.execute(sql)
                migrations_applied += 1
            else:
                print(f"  ⊘ Column already exists in {table_name}: {column_name}")
    
    # Handle new format (multiple tables with "tables" key)
    elif "tables" in migration_info:
        for table_name, columns in migration_info["tables"].items():
            print(f"\n  📋 Table: {table_name}")
            
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",(table_name,))
            if not cursor.fetchone():
                print(f"  ⚠️  Table {table_name} does not exist - skipping")
                continue
            
            existing_columns = get_table_columns(cursor, table_name)
            
            for column_name, column_type in columns:
                if column_name not in existing_columns:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    print(f"    ✓ Adding column: {column_name} ({column_type})")
                    cursor.execute(sql)
                    migrations_applied += 1
                else:
                    print(f"    ⊘ Column already exists: {column_name}")
    
    # Record version in schema_versions table
    # Mark all previous versions as not current
    cursor.execute("UPDATE schema_versions SET is_current = 0")
    
    # Insert new version and mark as current
    cursor.execute("""
        INSERT INTO schema_versions 
        (version, description, applied_at, applied_by, is_current, rollback_available, tables_modified)
        VALUES (?, ?, datetime('now'), 'migration_script', 1, 0, ?)
    """, (
        version, 
        migration_info['description'],
        ','.join(migration_info.get('tables', {}).keys()) if 'tables' in migration_info else migration_info.get('table', 'migration_scenarios')
    ))
    
    return migrations_applied


def migrate_database(db_path: str, target_version: str = None):
    """
    Migrate database to target version or latest.
    
    Args:
        db_path: Path to the database file
        target_version: Specific version to migrate to, or None for latest
    """
    print(f"🗄️  Database Migration Manager")
    print(f"=" * 60)
    print(f"Database: {db_path}")
    print(f"Target: {target_version or 'latest'}")
    print(f"=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create schema_version table
        create_schema_version_table(cursor)
        
        # Get current state
        current_version = get_current_version(cursor)
        applied_versions = get_applied_versions(cursor)
        
        print(f"\n📌 Current version: {current_version or 'None (fresh database)'}")
        
        if applied_versions:
            print(f"📜 Applied versions: {', '.join(applied_versions)}")
        
        # Determine which migrations to apply
        versions_to_apply = []
        for version in sorted(MIGRATIONS.keys()):
            if version not in applied_versions:
                versions_to_apply.append(version)
                if target_version and version == target_version:
                    break
        
        if not versions_to_apply:
            print("\n✅ Database is up to date! No migrations needed.")
            
            # Show current schema
            print("\n📋 Current migration_scenarios schema:")
            columns = get_table_columns(cursor, "migration_scenarios")
            for col in columns:
                print(f"  - {col}")
            
            return True
        
        print(f"\n🔄 Migrations to apply: {', '.join(versions_to_apply)}")
        
        # Apply migrations
        total_changes = 0
        for version in versions_to_apply:
            changes = apply_migration(cursor, version, MIGRATIONS[version])
            total_changes += changes
        
        conn.commit()
        
        # Show final state
        new_version = get_current_version(cursor)
        print(f"\n✅ Migration complete!")
        print(f"   Previous version: {current_version or 'None'}")
        print(f"   Current version: {new_version}")
        print(f"   Changes applied: {total_changes}")
        
        # Show updated schema
        print("\n📋 Updated migration_scenarios schema:")
        columns = get_table_columns(cursor, "migration_scenarios")
        for col in columns:
            print(f"  - {col}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


def show_status(db_path: str):
    """Show current database migration status."""
    print(f"🗄️  Database Migration Status")
    print(f"=" * 60)
    print(f"Database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        create_schema_version_table(cursor)
        
        current_version = get_current_version(cursor)
        applied_versions = get_applied_versions(cursor)
        
        print(f"📌 Current version: {current_version or 'None'}")
        print(f"\n📜 Migration History:")
        
        if applied_versions:
            cursor.execute("SELECT version, description, applied_at, is_current FROM schema_versions ORDER BY applied_at")
            for version, description, applied_at, is_current in cursor.fetchall():
                current_marker = " (CURRENT)" if is_current else ""
                print(f"  ✓ {version}: {description}{current_marker}")
                print(f"    Applied: {applied_at}")
        else:
            print("  No migrations applied yet")
        
        print(f"\n📦 Available migrations:")
        for version in sorted(MIGRATIONS.keys()):
            status = "✓ Applied" if version in applied_versions else "○ Pending"
            print(f"  {status} {version}: {MIGRATIONS[version]['description']}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("database", nargs="?", default="data/vmware_inventory.db",
                       help="Path to database file (default: data/vmware_inventory.db)")
    parser.add_argument("--status", action="store_true",
                       help="Show migration status without applying changes")
    parser.add_argument("--version", type=str,
                       help="Migrate to specific version")
    
    args = parser.parse_args()
    
    # Remove sqlite:/// prefix if present
    db_path = args.database.replace("sqlite:///", "")
    
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} [database_path]")
        print(f"  python {sys.argv[0]} --status              # Show status")
        print(f"  python {sys.argv[0]} --version 1.0.0       # Migrate to specific version")
        sys.exit(1)
    
    if args.status:
        show_status(db_path)
    else:
        success = migrate_database(db_path, args.version)
        sys.exit(0 if success else 1)
