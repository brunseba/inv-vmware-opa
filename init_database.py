#!/usr/bin/env python3
"""
Initialize database with all tables including new replication parameters.
Run this once to set up the database schema.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from src.models.base import Base
from src.models import VirtualMachine, Label, VMLabel, FolderLabel
from src.models.migration_target import (
    MigrationTarget, 
    MigrationScenario, 
    MigrationWave,
    MigrationStrategyConfig
)
from src.models.schema_version import SchemaVersion
from src.services.schema_service import SchemaService, CURRENT_SCHEMA_VERSION

def initialize_database(db_path="vmware_inventory.db"):
    """Initialize database with all tables."""
    print(f"Initializing database: {db_path}")
    
    # Create engine
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    
    # Create all tables
    print("\nCreating tables...")
    Base.metadata.create_all(engine)
    
    print("\n✅ All tables created successfully!")
    
    # Initialize schema version tracking
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        schema_service = SchemaService(session)
        schema_version = schema_service.initialize_schema_tracking()
        
        print(f"\n✅ Schema version initialized: {schema_version.version}")
        print(f"   Description: {schema_version.description}")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            print(f"   • {table} ({len(columns)} columns)")
        
        session.close()
        
        print("\n✅ Database initialization complete!")
        print(f"\nSchema Version: {CURRENT_SCHEMA_VERSION}")
        print("\nYou can now start the application:")
        print("  streamlit run src/dashboard/app.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing schema version: {e}")
        session.rollback()
        session.close()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize VMware inventory database")
    parser.add_argument(
        "--db",
        default="vmware_inventory.db",
        help="Database file path (default: vmware_inventory.db)"
    )
    
    args = parser.parse_args()
    
    success = initialize_database(args.db)
    sys.exit(0 if success else 1)
