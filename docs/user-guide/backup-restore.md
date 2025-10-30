# Backup & Restore

The VMware Inventory tool provides comprehensive backup and restore capabilities for both the entire database and label-specific data.

## Overview

Two types of backups are supported:

1. **Full Database Backup**: Complete SQLite database backup (all VMs, labels, and assignments)
2. **Label Backup**: JSON export of label definitions and assignments

## Database Backup & Restore

### Creating a Database Backup (CLI)

```bash
# Create full database backup
vmware-inv backup data/backups/database_backup_20251030.db

# Backup with custom location
vmware-inv backup /path/to/backup/mybackup.db
```

### Restoring a Database (CLI)

```bash
# Restore from backup (with confirmation)
vmware-inv restore data/backups/database_backup_20251030.db

# The current database is automatically backed up before restore
```

**⚠️ Warning**: Database restore will replace ALL data. A safety backup is created automatically.

### Creating a Database Backup (Web UI)

1. Navigate to **Database Backup** in the left sidebar
2. Enter a filename (or use the default timestamp-based name)
3. Click **💾 Create Backup**
4. Download the backup file using the download button

### Restoring a Database (Web UI)

1. Navigate to **Database Backup** → **Restore Database** tab
2. Upload a backup file (.db, .sqlite, .sqlite3)
3. Review the backup information
4. Click **🔄 Restore Database** (click twice to confirm)
5. Refresh the page to see the restored data

## Label Backup & Restore

### Creating a Label Backup (CLI)

```bash
# Backup all labels to JSON
vmware-inv label backup data/backups/labels_backup.json

# Backup with custom location
vmware-inv label backup /path/to/backup/my_labels.json
```

The JSON backup includes:
- Label definitions (key, value, description, color)
- VM label assignments (direct and inherited)
- Folder label assignments with inheritance settings

### Restoring Labels (CLI)

```bash
# Restore labels with merge mode (default)
vmware-inv label restore data/backups/labels_backup.json

# Restore with specific mode
vmware-inv label restore data/backups/labels_backup.json --mode skip_duplicates
vmware-inv label restore data/backups/labels_backup.json --mode replace

# Clear existing labels before restore (DANGEROUS!)
vmware-inv label restore data/backups/labels_backup.json --clear-existing
```

#### Import Modes

- **merge** (default): Update existing labels, add new ones
- **skip_duplicates**: Keep existing labels, only add new ones
- **replace**: Delete existing label and recreate

### Listing Backups (CLI)

```bash
# List all backup files in default directory
vmware-inv label list-backups

# List backups in custom directory
vmware-inv label list-backups --backup-dir /path/to/backups
```

### Creating a Label Backup (Web UI)

1. Navigate to **Folder Labelling** → **Management** tab
2. Scroll to **💾 Backup & Restore** section
3. Enter a filename (or use the default)
4. Click **💾 Create Backup**
5. Download the JSON file

### Restoring Labels (Web UI)

1. Navigate to **Folder Labelling** → **Management** tab
2. Scroll to **Restore from Backup** section
3. Upload a JSON backup file
4. Review the backup contents
5. Select import mode (merge, skip_duplicates, replace)
6. Click **🔄 Restore from Backup** (click twice to confirm)

## Backup File Formats

### Database Backup Format

- **Type**: SQLite database file
- **Extension**: .db, .sqlite, .sqlite3
- **Contains**: All tables (virtual_machines, labels, vm_labels, folder_labels)
- **Size**: Varies based on inventory size

### Label Backup Format

- **Type**: JSON
- **Extension**: .json
- **Structure**:
```json
{
  "version": "1.0",
  "exported_at": "2025-10-30T12:00:00",
  "labels": [
    {
      "id": 1,
      "key": "environment",
      "value": "production",
      "description": "Production environment",
      "color": "#FF0000"
    }
  ],
  "vm_assignments": [
    {
      "vm_name": "vm-web-01",
      "label_id": 1,
      "inherited_from_folder": false,
      "assigned_by": "admin"
    }
  ],
  "folder_assignments": [
    {
      "folder_path": "/datacenter/prod",
      "label_id": 1,
      "inherit_to_vms": true,
      "inherit_to_subfolders": false,
      "assigned_by": "admin"
    }
  ]
}
```

## Best Practices

### Backup Strategy

1. **Regular Backups**: Schedule regular database backups (daily/weekly)
2. **Before Major Changes**: Always backup before bulk operations
3. **Version Control**: Use timestamps in backup filenames
4. **Off-site Storage**: Store backups in a separate location
5. **Test Restores**: Periodically test restore procedures

### Backup Naming Convention

```bash
# Recommended naming pattern
database_backup_YYYYMMDD_HHMMSS.db
labels_backup_YYYYMMDD_HHMMSS.json

# Examples
database_backup_20251030_143022.db
labels_backup_20251030_143022.json
```

### Before Restoring

1. **Verify Backup**: Check backup file size and date
2. **Current Backup**: Create a backup of current data
3. **Confirm Source**: Ensure you're restoring the correct backup
4. **Test Environment**: Test restore in non-production first if possible

## Backup Locations

### Default Locations

- **Database backups**: `data/backups/*.db`
- **Label backups**: `data/backups/*.json`

### Custom Locations

You can specify any location for backups:

```bash
# Backup to custom location
vmware-inv backup ~/Documents/backups/vmware_$(date +%Y%m%d).db
vmware-inv label backup ~/Documents/backups/labels_$(date +%Y%m%d).json
```

## Troubleshooting

### Database Restore Issues

**Issue**: "Database file not found"
```bash
# Check if backup file exists
ls -la data/backups/database_backup.db
```

**Issue**: "Permission denied"
```bash
# Check file permissions
chmod 644 data/backups/database_backup.db
```

### Label Restore Issues

**Issue**: "VM not found"
- The backup references VMs that don't exist in the current database
- These assignments will be skipped (check error list)

**Issue**: "Label ID not found in mapping"
- Indicates a corrupted backup file
- Try using a different backup

### Recovery from Failed Restore

If a database restore fails, the automatic safety backup can be found at:
```
data/vmware_inventory.db.backup
```

To recover:
```bash
# Stop the application
# Restore the safety backup
cp data/vmware_inventory.db.backup data/vmware_inventory.db
```

## Automation

### Automated Backups with Cron

```bash
# Daily database backup at 2 AM
0 2 * * * cd /path/to/inv-vmware-opa && vmware-inv backup data/backups/db_$(date +\%Y\%m\%d).db

# Weekly label backup on Sundays at 3 AM
0 3 * * 0 cd /path/to/inv-vmware-opa && vmware-inv label backup data/backups/labels_$(date +\%Y\%m\%d).json
```

### Backup Retention Script

```bash
#!/bin/bash
# Keep only last 7 daily backups and last 4 weekly backups

# Daily backups (keep 7 days)
find data/backups/ -name "database_backup_*.db" -mtime +7 -delete
find data/backups/ -name "labels_backup_*.json" -mtime +7 -delete

# Archive weekly backups
# Add your archive logic here
```

## Security Considerations

1. **Backup Encryption**: Consider encrypting backup files
2. **Access Control**: Restrict backup directory permissions
3. **Secure Transfer**: Use secure protocols (SCP, SFTP) for transfers
4. **Audit Trail**: Log all backup and restore operations
5. **Data Sanitization**: Remove sensitive data before external backups

## Related Documentation

- [CLI Commands](cli-commands.md) - Complete CLI reference
- [Folder Labelling](folder-labelling.md) - Label management guide
- [Data Quality](data-quality.md) - Label quality analysis
