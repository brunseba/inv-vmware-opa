# Schema CLI Update Summary

## Date
October 30, 2025

## Overview
Enhanced the `vmware-inv` CLI with two new schema management commands to improve database schema visibility and maintenance.

## Changes Made

### 1. New CLI Commands

#### `vmware-inv schema-version`
- **Purpose**: Display current database schema version and compatibility status
- **Features**:
  - Shows current version installed in the database
  - Shows expected version from the application
  - Displays compatibility status with clear indicators (✅/⚠️)
  - Shows when and by whom the schema was applied
  - Optional `--history` flag to view complete migration history
- **Location**: `src/cli.py` lines 891-970

#### `vmware-inv schema-info`
- **Purpose**: Display comprehensive database schema information
- **Features**:
  - Shows version compatibility
  - Lists all tables in the database
  - Displays schema tracking status
  - Shows version history count
  - Shows last update timestamp
- **Location**: `src/cli.py` lines 972-1024

### 2. Documentation

#### Created `SCHEMA_CLI_COMMANDS.md`
Comprehensive documentation covering:
- Command usage and options
- Practical examples
- Workflow examples
- Current schema version details
- Schema version tracking explanation
- Cross-references to related commands

### 3. Testing

#### Created `tests/test_schema_cli.py`
Unit tests for the new commands:
- `test_schema_version_command` - Basic functionality test
- `test_schema_version_with_history` - Test history flag
- `test_schema_info_command` - Test schema info display
- `test_schema_upgrade_command` - Test upgrade with force flag
- `test_schema_commands_with_nonexistent_db` - Error handling test

**Test Results**: ✅ All 5 tests passing

### 4. Installation
Updated the package with pipx:
```bash
pipx uninstall inv-vmware-opa
pipx install -e .
```

## Command Examples

### Check Current Schema Version
```bash
$ vmware-inv schema-version

📊 Schema Version Information
Database: sqlite:///data/vmware_inventory.db

Current version:  1.4.0
Applied at:       2025-10-30 22:26:08
Applied by:       N/A
Expected version: 1.4.0

✅ Status: Compatible
```

### View Version History
```bash
$ vmware-inv schema-version --history

📊 Schema Version Information
Database: sqlite:///data/vmware_inventory.db

Current version:  1.4.0
Applied at:       2025-10-30 22:26:08
Applied by:       N/A
Expected version: 1.4.0

✅ Status: Compatible

📜 Version History (4 versions):

Version    Description                                                      Applied           By                Status
---------  ---------------------------------------------------------------  ----------------  ----------------  ---------
1.4.0      Added replication efficiency parameters for realistic migrat...  2025-10-30 22:26  N/A               ✓ Current
1.2.0      Add cost separation (migration vs runtime) to migration_scen...  2025-10-30 21:43  manual_migration
1.3.0      Add VM resource metrics (count, vCPUs, RAM, storage) to migr...  2025-10-30 21:43  manual_migration
1.1.0      Initial database schema with VM inventory and labelling supp...  2025-10-30 20:43  system
```

### View Detailed Schema Information
```bash
$ vmware-inv schema-info

📋 Database Schema Information
Database: sqlite:///data/vmware_inventory.db

Version:
  Current:  1.4.0
  Expected: 1.4.0
  Status:   ✅ Compatible

Tables (10):
  #  Table Name
---  --------------------------
  1  folder_labels
  2  labels
  3  migration_scenarios
  4  migration_strategy_configs
  5  migration_targets
  6  migration_waves
  7  schema_version
  8  schema_versions
  9  virtual_machines
 10  vm_labels

Metadata:
  Schema tracking: ✅ Enabled
  Version history: 4 record(s)
  Last update:     2025-10-30 22:26:08
```

## Benefits

1. **Improved Visibility**: Users can quickly check schema version and compatibility
2. **Better Debugging**: Schema information helps troubleshoot database issues
3. **Migration Tracking**: Full history of schema changes is easily accessible
4. **User-Friendly**: Clear visual indicators and formatted output
5. **Comprehensive**: Both quick checks and detailed information available

## Integration

The new commands integrate seamlessly with existing schema management:
- `vmware-inv schema` - View datamodel schema (columns, types)
- `vmware-inv schema-version` - **NEW** - Check version and compatibility
- `vmware-inv schema-info` - **NEW** - View detailed schema information
- `vmware-inv schema-upgrade` - Upgrade to latest version

## Files Modified

1. `src/cli.py` - Added 2 new CLI commands
2. `SCHEMA_CLI_COMMANDS.md` - New documentation file
3. `tests/test_schema_cli.py` - New test file
4. `SCHEMA_CLI_UPDATE_SUMMARY.md` - This summary

## Dependencies

No new dependencies were added. The commands use existing packages:
- `click` - CLI framework
- `sqlalchemy` - Database interaction
- `tabulate` - Table formatting (already used)

## Backward Compatibility

✅ Fully backward compatible - no breaking changes to existing commands or APIs.

## Next Steps

Consider:
1. Add these commands to the README.md
2. Update main documentation with schema management workflow
3. Add schema version check to dashboard startup
4. Create GitHub workflow to validate schema on PR

## Testing Checklist

- [x] Unit tests created and passing
- [x] Commands work with default database
- [x] Commands work with custom database paths
- [x] Error handling tested
- [x] Help text verified
- [x] Documentation created
- [x] Package reinstalled and verified

## Conclusion

The schema CLI has been successfully updated with two new commands that provide better visibility into database schema version and status. All tests pass and the commands are ready for use.
