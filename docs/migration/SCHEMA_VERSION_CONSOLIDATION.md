# Schema Version Management - Consolidation Complete

## ✅ Status: CONSOLIDATED

**Date:** 2025-10-30  
**Action:** Consolidated from 2 tables to 1 table

---

## Summary

The database previously had **two** schema version tracking tables:
- `schema_version` (singular) - Created by `migrate_database.py`
- `schema_versions` (plural) - Used by SQLAlchemy models

This has been consolidated to use **only** `schema_versions` (plural).

---

## Changes Made

### 1. Updated `migrate_database.py`

- ✅ Now creates `schema_versions` (plural) table
- ✅ Uses full schema with all SQLAlchemy model columns:
  - `id`, `version`, `description`, `applied_at`, `applied_by`
  - `migration_script`, `tables_added`, `tables_modified`, `tables_removed`
  - `is_current`, `rollback_available`, `rollback_script`, `notes`
- ✅ Marks current version with `is_current = 1`
- ✅ All queries updated to use `schema_versions`

### 2. Dropped Old Table

```sql
DROP TABLE IF EXISTS schema_version;
```

---

## Current State

### Schema Version Table

**Table Name:** `schema_versions` (plural only)

**Current Version:** 1.4.0

**Version History:**
```
1.1.0 - Initial database schema with VM inventory and labelling support
1.2.0 - Add cost separation (migration vs runtime) to migration_scenarios
1.3.0 - Add VM resource metrics (count, vCPUs, RAM, storage) to migration_scenarios
1.4.0 - Add replication efficiency parameters (CURRENT) ✅
```

---

## How to Use

### Check Migration Status

```bash
python migrate_database.py data/vmware_inventory.db --status
```

### Apply Migrations

```bash
python migrate_database.py data/vmware_inventory.db
```

### Check Current Version

```bash
sqlite3 data/vmware_inventory.db "SELECT version FROM schema_versions WHERE is_current = 1;"
```

---

## Benefits of Consolidation

1. **Single Source of Truth** - Only one table tracks schema versions
2. **Consistency** - Migration script uses same table as SQLAlchemy models
3. **Better Tracking** - Full feature set (rollback support, current marking, etc.)
4. **No Conflicts** - No risk of two tables getting out of sync

---

## Migration Script Features

The updated `migrate_database.py` now supports:

- ✅ Multi-table migrations (v1.4.0 updates 2 tables)
- ✅ Backward compatible with old single-table format
- ✅ Current version marking (`is_current` field)
- ✅ Tables modified tracking
- ✅ Full SQLAlchemy model compatibility

---

## For Developers

### Adding New Migrations

Add to the `MIGRATIONS` dictionary in `migrate_database.py`:

```python
"1.5.0": {
    "description": "Your migration description",
    "tables": {
        "table_name": [
            ("column_name", "COLUMN_TYPE DEFAULT value"),
        ]
    }
}
```

### Single Table Migration (Old Format)

Still supported for backward compatibility:

```python
"1.5.0": {
    "description": "Your migration description",
    "table": "migration_scenarios",
    "columns": [
        ("column_name", "COLUMN_TYPE"),
    ]
}
```

---

## Verification

Run these commands to verify consolidation:

```bash
# Should show only 1 table
sqlite3 data/vmware_inventory.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'schema%';"
# Output: schema_versions

# Should show 1.4.0 as current
sqlite3 data/vmware_inventory.db "SELECT version, is_current FROM schema_versions WHERE is_current = 1;"
# Output: 1.4.0|1

# Should show all 4 versions
sqlite3 data/vmware_inventory.db "SELECT COUNT(*) FROM schema_versions;"
# Output: 4
```

---

✅ **Schema version management is now fully consolidated and operational!**

**Last Updated:** 2025-10-30  
**Status:** Complete
