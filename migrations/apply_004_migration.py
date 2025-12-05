#!/usr/bin/env python3
"""Apply database migration 004: Label Source Tracking."""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def apply_migration(db_url: str):
    """Apply migration 004 to add label source tracking."""
    print("=" * 70)
    print("Migration 004: Add Label Source Tracking")
    print("=" * 70)
    print(f"\nDatabase: {db_url}")
    print("\nThis migration will:")
    print("  - Add 'name' and 'category' columns to labels table")
    print("  - Add source tracking columns to vm_labels table:")
    print("    * label_source (where label came from)")
    print("    * source_convention_id (naming convention ID)")
    print("    * source_field_name (field name)")
    print("    * auto_created (whether auto-created)")
    print()

    # Create engine
    engine = create_engine(db_url)

    # Read migration file
    migration_path = Path(__file__).parent / "004_add_label_source_tracking.sql"
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        sys.exit(1)

    with open(migration_path, "r") as f:
        sql_content = f.read()

    # Remove comments and split into statements
    lines = sql_content.split("\n")
    clean_lines = []
    in_comment_block = False

    for line in lines:
        # Skip single-line comments
        if line.strip().startswith("--"):
            continue
        # Handle multi-line comments
        if "/*" in line:
            in_comment_block = True
        if "*/" in line:
            in_comment_block = False
            continue
        if not in_comment_block:
            clean_lines.append(line)

    # Join and split by semicolon
    clean_sql = " ".join(clean_lines)
    statements = [s.strip() for s in clean_sql.split(";") if s.strip()]

    print(f"Found {len(statements)} SQL statements to execute\n")

    try:
        with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                # Show what we're doing
                stmt_preview = statement[:80] + "..." if len(statement) > 80 else statement
                print(f"  [{i}/{len(statements)}] {stmt_preview}")

                try:
                    conn.execute(text(statement))
                except Exception as e:
                    # Some statements might fail if column already exists (idempotent)
                    if "duplicate column name" in str(e).lower():
                        print("      ⚠️  Column already exists (skipping)")
                    else:
                        raise

        print("\n" + "=" * 70)
        print("✅ Migration 004 applied successfully!")
        print("=" * 70)
        print("\nNew features available:")
        print("  - Labels now have 'name' and 'category' fields for better organization")
        print("  - VM labels track their source (naming convention, manual, etc.)")
        print("  - Can query which labels were auto-created from naming conventions")
        print("  - Can trace back to specific naming convention and field")
        print()
        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ Error applying migration: {e}")
        print("=" * 70)
        print("\nMigration failed. Database may be in partial state.")
        print("Please check the error and try again.")
        print()
        return False


def main():
    """Main entry point."""
    # Get database URL from environment or use default
    db_url = os.environ.get("VMWARE_INV_DB_URL", "sqlite:///data/vmware_inventory.db")

    # Check if database exists
    if db_url.startswith("sqlite:///"):
        db_path = Path(db_url.replace("sqlite:///", ""))
        if not db_path.exists():
            print(f"❌ Database file not found: {db_path}")
            print("Please create the database first.")
            sys.exit(1)

    success = apply_migration(db_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
