# Schema CLI Commands

This document describes the schema management commands available in the `vmware-inv` CLI.

## Overview

Three commands are available for managing and inspecting the database schema:

1. **`schema-version`** - Check current schema version and compatibility
2. **`schema-info`** - View detailed schema information including tables
3. **`schema-upgrade`** - Upgrade database schema to the latest version

## Commands

### `vmware-inv schema-version`

Show database schema version information including current version, expected version, and compatibility status.

**Usage:**
```bash
vmware-inv schema-version [OPTIONS]
```

**Options:**
- `--db-url TEXT` - Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--history` - Show complete version history with all migrations
- `--help` - Show help message

**Examples:**

Check current schema version:
```bash
vmware-inv schema-version
```

View complete version history:
```bash
vmware-inv schema-version --history
```

Check schema version for a specific database:
```bash
vmware-inv schema-version --db-url sqlite:///path/to/custom.db
```

**Output:**
- Current version installed in the database
- Expected version from the application
- Compatibility status (✅ Compatible or ⚠️ Incompatible)
- Applied timestamp and user
- Version history (when `--history` flag is used)

---

### `vmware-inv schema-info`

Show detailed schema information including all tables, metadata, and compatibility.

**Usage:**
```bash
vmware-inv schema-info [OPTIONS]
```

**Options:**
- `--db-url TEXT` - Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--help` - Show help message

**Examples:**

View schema information:
```bash
vmware-inv schema-info
```

Check schema for a specific database:
```bash
vmware-inv schema-info --db-url sqlite:///path/to/custom.db
```

**Output:**
- Version information (current vs expected)
- Compatibility status
- Complete list of tables in the database
- Schema tracking status
- Number of version history records
- Last update timestamp

---

### `vmware-inv schema-upgrade`

Upgrade the database schema to the current application version.

**Usage:**
```bash
vmware-inv schema-upgrade [OPTIONS]
```

**Options:**
- `--db-url TEXT` - Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--force` - Skip confirmation prompt
- `--help` - Show help message

**Examples:**

Upgrade schema with confirmation:
```bash
vmware-inv schema-upgrade
```

Upgrade schema without confirmation:
```bash
vmware-inv schema-upgrade --force
```

Upgrade specific database:
```bash
vmware-inv schema-upgrade --db-url sqlite:///path/to/custom.db
```

**What it does:**
- Creates any missing tables
- Updates schema version tracking
- Records migration metadata
- Confirms action before executing (unless `--force` is used)

---

## Workflow Examples

### Check if upgrade is needed

```bash
# First, check current version and compatibility
vmware-inv schema-version

# If incompatible, view detailed schema info
vmware-inv schema-info

# Perform upgrade if needed
vmware-inv schema-upgrade
```

### View migration history

```bash
# See all schema changes over time
vmware-inv schema-version --history
```

### Verify upgrade success

```bash
# After upgrade, verify the new version
vmware-inv schema-version

# Check that all tables exist
vmware-inv schema-info
```

---

## Current Schema Version

**Version:** 1.4.0

**Tables:**
- `virtual_machines` - VM inventory data
- `labels` - Label definitions
- `vm_labels` - VM-to-label associations
- `folder_labels` - Folder-to-label associations
- `migration_targets` - Migration target platforms
- `migration_scenarios` - Migration scenarios and costs
- `migration_waves` - Migration wave planning
- `migration_strategy_configs` - Strategy configurations
- `schema_versions` - Schema version tracking

---

## Schema Version Tracking

The application uses the `schema_versions` table to track all schema changes:

- **version** - Version identifier (e.g., "1.4.0")
- **description** - Human-readable change description
- **applied_at** - Timestamp of when the migration was applied
- **applied_by** - User/system that applied the migration
- **migration_script** - Script filename (if applicable)
- **tables_added** - Comma-separated list of added tables
- **tables_modified** - Comma-separated list of modified tables
- **tables_removed** - Comma-separated list of removed tables
- **is_current** - Boolean flag for current version
- **rollback_available** - Whether rollback is possible
- **rollback_script** - Rollback script filename (if applicable)
- **notes** - Additional notes about the migration

---

## See Also

- `vmware-inv schema` - View datamodel schema with filtering
- `vmware-inv stats` - Show database statistics
- `vmware-inv backup` - Create database backup before upgrades
