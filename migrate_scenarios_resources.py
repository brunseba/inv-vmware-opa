#!/usr/bin/env python3
"""Migration script to add VM resource metrics columns to migration_scenarios table."""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str):
    """Add VM resource metrics columns to migration_scenarios table."""
    
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(migration_scenarios)")
        columns = [row[1] for row in cursor.fetchall()]
        
        migrations = []
        
        if 'vm_count' not in columns:
            migrations.append(
                "ALTER TABLE migration_scenarios ADD COLUMN vm_count INTEGER"
            )
        
        if 'total_vcpus' not in columns:
            migrations.append(
                "ALTER TABLE migration_scenarios ADD COLUMN total_vcpus INTEGER"
            )
        
        if 'total_memory_gb' not in columns:
            migrations.append(
                "ALTER TABLE migration_scenarios ADD COLUMN total_memory_gb REAL"
            )
        
        if 'total_storage_gb' not in columns:
            migrations.append(
                "ALTER TABLE migration_scenarios ADD COLUMN total_storage_gb REAL"
            )
        
        if not migrations:
            print("✅ Database is already up to date!")
            return True
        
        # Execute migrations
        for migration in migrations:
            print(f"Executing: {migration}")
            cursor.execute(migration)
        
        conn.commit()
        print(f"✅ Successfully added {len(migrations)} column(s)")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(migration_scenarios)")
        print("\nUpdated schema:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "data/vmware_inventory.db"
    
    # Remove sqlite:/// prefix if present
    db_path = db_path.replace("sqlite:///", "")
    
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} [database_path]")
        print(f"\nExample:")
        print(f"  python {sys.argv[0]} data/vmware_inventory.db")
        sys.exit(1)
    
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
