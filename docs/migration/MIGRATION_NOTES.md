# Database Migration Notes

## Schema Version Tracking

The database uses a `schema_versions` table to track all migrations:

```sql
SELECT version, description, is_current 
FROM schema_versions 
ORDER BY version;
```

**Current Version**: 1.3.0

---

## Migration: Separate Migration and Runtime Costs

**Version**: 1.2.0  
**Date**: 2025-10-30  
**Script**: `migrate_scenarios_costs.py`

### Purpose
Separated migration costs (one-time) from runtime costs (ongoing) in the `migration_scenarios` table to provide better cost visibility and TCO analysis.

### Changes Made

#### New Columns Added:
1. **`estimated_migration_cost`** (REAL)
   - One-time migration costs (labor + data transfer)

2. **`estimated_runtime_cost_monthly`** (REAL)
   - Monthly operational costs (compute + memory + storage + SaaS)

3. **`migration_cost_breakdown`** (TEXT/JSON)
   - Detailed breakdown: `{"labor": X, "network_transfer": Y, "total": Z}`

4. **`runtime_cost_breakdown`** (TEXT/JSON)
   - Detailed breakdown: `{"compute": A, "memory": B, "storage": C, "saas": D, "total": E}`

### Running the Migration

```bash
# Migrate main database
python migrate_scenarios_costs.py data/vmware_inventory.db

# Migrate a different database
python migrate_scenarios_costs.py /path/to/database.db
```

### Impact

- **Existing scenarios**: Will have `NULL` values for new columns until recalculated
- **New scenarios**: Will automatically populate all cost fields
- **Backward compatibility**: Original `estimated_cost_total` and `estimated_cost_breakdown` fields remain for legacy support

### Verification

After migration, verify the schema:

```bash
sqlite3 data/vmware_inventory.db "PRAGMA table_info(migration_scenarios);"
```

You should see the four new columns at the end of the schema.

### Rollback

If needed, the columns can be removed (though SQLite doesn't support DROP COLUMN directly):

```sql
-- Not recommended, but possible via table recreation
-- Backup database first!
```

### Next Steps

1. ✅ Migration script created and executed
2. ✅ Service layer updated to calculate separated costs
3. ✅ UI updated to display migration vs runtime costs
4. 📝 Consider recalculating existing scenarios for complete data

---

## Migration: Add VM Resource Metrics

**Version**: 1.3.0  
**Date**: 2025-10-30  
**Script**: `migrate_scenarios_resources.py`

### Purpose
Added VM resource metrics (count, vCPUs, RAM, storage) to migration scenarios for better resource visibility and capacity planning.

### Changes Made

#### New Columns Added:
1. **`vm_count`** (INTEGER)
   - Total number of VMs in the scenario

2. **`total_vcpus`** (INTEGER)
   - Total vCPUs across all VMs

3. **`total_memory_gb`** (REAL)
   - Total RAM in GB

4. **`total_storage_gb`** (REAL)
   - Total storage in GB

### Running the Migration

```bash
# Migrate main database
python migrate_scenarios_resources.py data/vmware_inventory.db

# Migrate a different database
python migrate_scenarios_resources.py /path/to/database.db
```

### UI Updates

- **Scenarios List**: Added VMs, vCPUs, RAM, Storage columns to summary table
- **Scenario Details**: Added "Resource Summary" section with metrics
- **Comparison View**: Included resource metrics in side-by-side comparison

### Impact

- **Existing scenarios**: Will have `NULL` values until recalculated
- **New scenarios**: Automatically calculate and store resource metrics

### Related Files

- Model: `src/models/migration_target.py`
- Service: `src/services/migration_scenarios.py`
- UI: `src/dashboard/pages/migration_scenarios.py`
- Migration: `migrate_scenarios_costs.py`
