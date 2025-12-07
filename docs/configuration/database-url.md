# Database URL Configuration

## Overview

The VMware Inventory CLI supports flexible database URL configuration through environment variables, allowing you to run commands from any directory without specifying the `--db-url` parameter each time.

## Environment Variable

### `VMWARE_INV_DB_URL`

Set this environment variable to specify the default database URL for all CLI commands.

**Format:**
```bash
export VMWARE_INV_DB_URL="sqlite:////absolute/path/to/database.db"
```

Note: SQLite URLs with absolute paths require **four slashes** (`////`):
- `sqlite:///` (3 slashes) = relative path
- `sqlite:////` (4 slashes) = absolute path

## Configuration Methods

### 1. Shell Configuration (Recommended)

Add to your shell configuration file (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
# VMware Inventory Database Path
export VMWARE_INV_DB_URL="sqlite:////Users/brun_s/sandbox/inv-vmware-opa/data/vmware_inventory.db"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### 2. Project .env File

Update the `.env` file in your project root:

```bash
VMWARE_INV_DB_URL=sqlite:////Users/brun_s/sandbox/inv-vmware-opa/data/vmware_inventory.db
```

Then source it before running commands:
```bash
source .env
vmware-inv schema-info
```

### 3. Session-Specific

Set for the current session only:

```bash
export VMWARE_INV_DB_URL="sqlite:////path/to/database.db"
vmware-inv schema-info
```

### 4. Per-Command Override

Override the environment variable for a single command:

```bash
vmware-inv schema-info --db-url sqlite:////other/path/database.db
```

## Fallback Behavior

If `VMWARE_INV_DB_URL` is not set, the CLI defaults to:
```
sqlite:///data/vmware_inventory.db
```

This relative path requires running commands from the project root directory.

## Troubleshooting

### Error: `unable to open database file`

**Symptoms:**
```
✗ Error: (sqlite3.OperationalError) unable to open database file
```

**Causes:**
1. Running command from wrong directory with relative path
2. Database file doesn't exist at specified path
3. Insufficient permissions on database directory

**Solutions:**

1. **Use absolute path with environment variable:**
   ```bash
   export VMWARE_INV_DB_URL="sqlite:////absolute/path/to/vmware_inventory.db"
   ```

2. **Run from project root:**
   ```bash
   cd /path/to/inv-vmware-opa
   vmware-inv schema-info
   ```

3. **Verify database exists:**
   ```bash
   ls -la /path/to/data/vmware_inventory.db
   ```

4. **Check permissions:**
   ```bash
   chmod 600 /path/to/data/vmware_inventory.db
   chmod 755 /path/to/data/
   ```

## Commands Supporting Environment Variable

The following commands support the `VMWARE_INV_DB_URL` environment variable:

- ✅ `schema-info` - Show database schema information
- 🔜 `schema-version` - Show schema version (coming soon)
- 🔜 `schema-upgrade` - Upgrade database schema (coming soon)
- 🔜 `backup` - Create database backup (coming soon)
- 🔜 `restore` - Restore from backup (coming soon)
- 🔜 `stats` - Show inventory statistics (coming soon)
- 🔜 `load` - Load data from Excel (coming soon)

## Example Usage

### Before (Required --db-url flag)
```bash
cd /Users/brun_s/sandbox/inv-vmware-opa/scripts
vmware-inv schema-info --db-url sqlite:////Users/brun_s/sandbox/inv-vmware-opa/data/vmware_inventory.db
```

### After (With environment variable)
```bash
export VMWARE_INV_DB_URL="sqlite:////Users/brun_s/sandbox/inv-vmware-opa/data/vmware_inventory.db"
cd anywhere
vmware-inv schema-info  # Works from any directory!
```

## Related

- [CLI Commands](../user-guide/cli-commands.md)
- [Database Backup & Restore](../user-guide/backup-restore.md)
- [Schema Management](../migration/SCHEMA_CLI_COMMANDS.md)
