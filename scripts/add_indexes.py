#!/usr/bin/env python3
"""Add performance indexes to existing database.

This script adds indexes to frequently queried columns to improve
dashboard performance for large inventories.

Usage:
    python scripts/add_indexes.py [--db-url DATABASE_URL]
"""

import argparse
import sys
from sqlalchemy import create_engine, text, inspect


def add_indexes(db_url: str):
    """Add performance indexes to the database."""
    print(f"Connecting to database: {db_url}")
    engine = create_engine(db_url, echo=False)
    inspector = inspect(engine)
    
    # Get existing indexes
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('virtual_machines')}
    print(f"Found {len(existing_indexes)} existing indexes")
    
    # Define indexes to create (column_name, index_name)
    indexes_to_create = [
        ('powerstate', 'ix_virtual_machines_powerstate'),
        ('template', 'ix_virtual_machines_template'),
        ('creation_date', 'ix_virtual_machines_creation_date'),
        ('resource_pool', 'ix_virtual_machines_resource_pool'),
        ('folder', 'ix_virtual_machines_folder'),
        ('os_config', 'ix_virtual_machines_os_config'),
    ]
    
    created_count = 0
    skipped_count = 0
    
    with engine.begin() as conn:
        for column_name, index_name in indexes_to_create:
            if index_name in existing_indexes:
                print(f"⏭️  Index '{index_name}' already exists, skipping")
                skipped_count += 1
                continue
            
            try:
                print(f"➕ Creating index '{index_name}' on column '{column_name}'...")
                sql = text(f"CREATE INDEX {index_name} ON virtual_machines ({column_name})")
                conn.execute(sql)
                created_count += 1
                print(f"   ✅ Created successfully")
            except Exception as e:
                print(f"   ⚠️  Failed to create index '{index_name}': {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} indexes")
    print(f"   Skipped: {skipped_count} indexes")
    print(f"   Total:   {len(indexes_to_create)} indexes")
    
    # Show final index count
    inspector = inspect(engine)
    final_indexes = inspector.get_indexes('virtual_machines')
    print(f"\n✅ Database now has {len(final_indexes)} indexes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Add performance indexes to VMware inventory database")
    parser.add_argument(
        '--db-url',
        default='sqlite:///data/vmware_inventory.db',
        help='Database URL (default: sqlite:///data/vmware_inventory.db)'
    )
    
    args = parser.parse_args()
    
    try:
        add_indexes(args.db_url)
        print("\n🎉 Index creation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
