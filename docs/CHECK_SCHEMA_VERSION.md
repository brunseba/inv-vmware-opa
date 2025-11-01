# Check Database Schema Version

## Quick Check

```bash
sqlite3 data/vmware_inventory.db "SELECT version, description, is_current FROM schema_versions ORDER BY version;"
```

## Current Schema Version

**Version**: 1.3.0

## Version History

| Version | Description | Date |
|---------|-------------|------|
| 1.1.0 | Initial database schema with VM inventory and labelling support | 2025-10-30 |
| 1.2.0 | Add cost separation (migration vs runtime) to migration_scenarios | 2025-10-30 |
| 1.3.0 | Add VM resource metrics (count, vCPUs, RAM, storage) to migration_scenarios | 2025-10-30 |

## What Each Version Includes

### Version 1.1.0 (Base)
- Virtual Machine inventory tables
- VM labelling support
- Folder analysis
- Basic migration targets

### Version 1.2.0 (Cost Separation)
**New columns in `migration_scenarios`:**
- `estimated_migration_cost` - One-time migration costs
- `estimated_runtime_cost_monthly` - Monthly operational costs
- `migration_cost_breakdown` - Detailed migration costs (JSON)
- `runtime_cost_breakdown` - Detailed runtime costs (JSON)

### Version 1.3.0 (Resource Metrics) ⭐ Current
**New columns in `migration_scenarios`:**
- `vm_count` - Total number of VMs
- `total_vcpus` - Total vCPUs
- `total_memory_gb` - Total RAM in GB
- `total_storage_gb` - Total storage in GB

## Detailed Schema Info

### View Current Version
```bash
sqlite3 data/vmware_inventory.db "SELECT * FROM schema_versions WHERE is_current = 1;"
```

### View All Migrations
```bash
sqlite3 data/vmware_inventory.db "SELECT version, description, applied_at, applied_by FROM schema_versions ORDER BY applied_at;"
```

### View migration_scenarios Schema
```bash
sqlite3 data/vmware_inventory.db "PRAGMA table_info(migration_scenarios);"
```

## Schema Version Table Structure

```sql
CREATE TABLE schema_versions (
    id INTEGER PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description VARCHAR(500) NOT NULL,
    applied_at DATETIME NOT NULL,
    applied_by VARCHAR(100),
    migration_script VARCHAR(255),
    tables_added TEXT,
    tables_modified TEXT,
    tables_removed TEXT,
    is_current BOOLEAN NOT NULL DEFAULT 0,
    rollback_available BOOLEAN NOT NULL DEFAULT 0,
    rollback_script VARCHAR(255),
    notes TEXT
);
```

## Verifying Your Database

Run this command to verify your database has all the latest columns:

```bash
sqlite3 data/vmware_inventory.db << 'EOF'
.mode column
.headers on
SELECT 
    'migration_scenarios' as table_name,
    COUNT(*) as column_count
FROM pragma_table_info('migration_scenarios');

SELECT name as column_name 
FROM pragma_table_info('migration_scenarios')
WHERE name IN (
    'estimated_migration_cost',
    'estimated_runtime_cost_monthly', 
    'migration_cost_breakdown',
    'runtime_cost_breakdown',
    'vm_count',
    'total_vcpus',
    'total_memory_gb',
    'total_storage_gb'
);
EOF
```

Expected output: All 8 columns should be listed.
