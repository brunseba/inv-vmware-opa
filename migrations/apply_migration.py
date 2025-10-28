#!/usr/bin/env python3
"""Apply database migrations for VMware Inventory."""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def apply_migration(db_url: str, migration_file: str):
    """Apply a SQL migration file to the database."""
    print(f"Applying migration: {migration_file}")
    
    # Create engine
    engine = create_engine(db_url)
    
    # Read migration file
    migration_path = Path(__file__).parent / migration_file
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        sys.exit(1)
    
    with open(migration_path, 'r') as f:
        sql_content = f.read()
    
    # Remove comments and split into statements
    lines = sql_content.split('\n')
    clean_lines = []
    in_comment = False
    
    for line in lines:
        # Skip single-line comments
        if line.strip().startswith('--'):
            continue
        # Handle multi-line comments
        if '/*' in line:
            in_comment = True
        if '*/' in line:
            in_comment = False
            continue
        if not in_comment:
            clean_lines.append(line)
    
    # Join and split by semicolon
    clean_sql = ' '.join(clean_lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    
    try:
        with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                print(f"  Executing statement {i}/{len(statements)}...")
                conn.execute(text(statement))
        
        print(f"✅ Migration applied successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        return False


def main():
    """Main entry point."""
    # Get database URL from environment or use default
    db_url = os.environ.get('VMWARE_INV_DB_URL', 'sqlite:///data/vmware_inventory.db')
    
    print(f"Database: {db_url}")
    print("=" * 60)
    
    # Apply migrations in order
    migrations = [
        '001_add_labelling_tables.sql',
    ]
    
    success = True
    for migration in migrations:
        if not apply_migration(db_url, migration):
            success = False
            break
    
    if success:
        print("\n✅ All migrations applied successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
