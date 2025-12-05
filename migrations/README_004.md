# Migration 004: Label Source Tracking

**Version:** 004
**Date:** 2025-12-05
**Status:** Ready to Apply

## Overview

This migration enhances the label system by adding source tracking capabilities. It allows the system to track where labels came from (naming conventions, manual assignment, folder inheritance) and provides better label organization.

## Changes

### Labels Table
- **New Column**: `name` (VARCHAR(255)) - Combined key=value display name
- **New Column**: `category` (VARCHAR(100)) - Label category for grouping
- **New Indexes**:
  - `idx_labels_name`
  - `idx_labels_category`

### VM Labels Table
- **New Column**: `label_source` (VARCHAR(50)) - Source type: 'naming_convention', 'manual', 'folder_inheritance'
- **New Column**: `source_convention_id` (INTEGER) - ID of naming convention (if applicable)
- **New Column**: `source_field_name` (VARCHAR(100)) - Field name from naming convention (if applicable)
- **New Column**: `auto_created` (BOOLEAN) - Whether label was automatically created
- **New Indexes**:
  - `idx_vm_labels_label_source`
  - `idx_vm_labels_source_convention_id`
  - `idx_vm_labels_auto_created`

## Benefits

1. **Traceability**: Track which labels were created from naming conventions vs manually assigned
2. **Better Organization**: Group and categorize labels more effectively
3. **Audit Trail**: See which naming convention and field generated each label
4. **Cleanup**: Easily identify and remove auto-generated labels
5. **Reporting**: Generate reports on label sources and usage

## How to Apply

### Option 1: Using Python Script (Recommended)
```bash
cd migrations
python apply_004_migration.py
```

### Option 2: Manual SQL Application
```bash
sqlite3 data/vmware_inventory.db < migrations/004_add_label_source_tracking.sql
```

### Option 3: Using Custom Database URL
```bash
export VMWARE_INV_DB_URL="sqlite:///path/to/your/database.db"
python migrations/apply_004_migration.py
```

## Verification

After applying the migration, verify the changes:

```sql
-- Check labels table schema
PRAGMA table_info(labels);

-- Check vm_labels table schema
PRAGMA table_info(vm_labels);

-- Check schema_versions
SELECT * FROM schema_versions WHERE version = '004';

-- Check existing naming convention labels
SELECT COUNT(*) FROM vm_labels WHERE label_source = 'naming_convention';
```

## Rollback

To rollback this migration (not recommended in production):

1. The migration file contains a commented rollback script at the end
2. Extract and execute the rollback SQL
3. Note: This requires table recreation in SQLite and may result in data loss

## Compatibility

- **Backward Compatible**: Yes - new columns are nullable
- **Forward Compatible**: Applications not aware of new columns will continue to work
- **Required Actions**: None - migration populates existing data automatically

## Impact

- **Database Size**: Minimal increase (< 1% for typical databases)
- **Performance**: No negative impact - new indexes may improve query performance
- **Downtime**: None - can be applied while system is running (SQLite allows ALTER TABLE)
- **Application**: Updated models in `src/models/vmware.py` to include new fields

## Post-Migration

After applying this migration:

1. All existing naming convention labels (key starting with 'nc:') will be automatically marked as `label_source='naming_convention'`
2. Future labels created by naming conventions will include full source tracking
3. The `name` field will be populated for existing labels
4. New label creation code will set the `category` field appropriately

## Notes

- This migration is idempotent - it can be run multiple times safely
- Foreign key constraint for `source_convention_id` is not enforced at database level (SQLite limitation)
- Application code enforces referential integrity
