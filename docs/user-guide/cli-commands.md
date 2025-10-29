# CLI Commands

The `vmware-inv` CLI provides several commands for managing VMware inventory data.

## load

Load VMware inventory data from an Excel file into the database.

```bash
uv run python -m src.cli load <excel_file> [OPTIONS]
```

### Arguments

- `excel_file`: Path to the Excel file containing VMware inventory data

### Options

- `--db-url TEXT`: Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--clear`: Clear existing data before loading
- `--help`: Show help message

### Examples

```bash
# Load data with default database
uv run python -m src.cli load inputs/vmware-inv.xlsx

# Load data and clear existing records
uv run python -m src.cli load inputs/vmware-inv.xlsx --clear

# Load data to PostgreSQL
uv run python -m src.cli load inputs/vmware-inv.xlsx --db-url postgresql://user:pass@localhost/vmware
```

## stats

Display statistics about the inventory database.

```bash
uv run python -m src.cli stats [OPTIONS]
```

### Options

- `--db-url TEXT`: Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--help`: Show help message

### Examples

```bash
# Show stats from default database
uv run python -m src.cli stats

# Show stats from PostgreSQL
uv run python -m src.cli stats --db-url postgresql://user:pass@localhost/vmware
```

### Output

The stats command displays:
- Total number of VMs
- Number of powered on/off VMs
- Number of datacenters, clusters, and hosts

## datacenters

List all datacenters with VM counts and statistics.

```bash
vmware-inv datacenters [OPTIONS]
```

### Options

- `--db-url TEXT`: Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--help`: Show help message

### Examples

```bash
# List all datacenters with stats
vmware-inv datacenters
```

### Output

Displays a table with:
- Datacenter name
- VM count (total, powered on, powered off)
- Cluster count
- Host count
- Total vCPUs, RAM, and storage

## clusters

List all clusters with VM counts and statistics.

```bash
vmware-inv clusters [OPTIONS]
```

### Options

- `--db-url TEXT`: Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--datacenter TEXT`: Filter by datacenter name
- `--filter TEXT`: Regex pattern to filter cluster names
- `--help`: Show help message

### Examples

```bash
# List all clusters
vmware-inv clusters

# Filter by datacenter
vmware-inv clusters --datacenter "PROD-DC"

# Filter clusters with regex
vmware-inv clusters --filter "^prod-"
vmware-inv clusters --filter "cluster-[0-9]+"
```

### Output

Displays a table with:
- Datacenter
- Cluster name
- VM count (total, powered on, powered off)
- Host count
- Total vCPUs, RAM, and storage

## vm list

List virtual machines from the inventory.

```bash
vmware-inv vm list [OPTIONS]
```

### Options

- `--db-url TEXT`: Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--datacenter TEXT`: Filter by datacenter name
- `--cluster TEXT`: Filter by cluster name
- `--limit INTEGER`: Number of records to show (default: 10)
- `--help`: Show help message

### Examples

```bash
# List first 10 VMs
vmware-inv vm list

# List 50 VMs
vmware-inv vm list --limit 50

# Filter by datacenter
vmware-inv vm list --datacenter "PROD-WNG-WRK-HPI"

# Filter by cluster
vmware-inv vm list --cluster "GCAB-POD-DMX-NO"

# Combine filters
vmware-inv vm list --datacenter "PROD-WNG-WRK-HPI" --cluster "GCAB-POD-DMX-NO" --limit 20
```

### Output

The list command displays a table with:
- VM Name
- Power State
- Datacenter
- Cluster

## vm search

Search for VMs using regex pattern matching.

```bash
vmware-inv vm search PATTERN [OPTIONS]
```

### Arguments

- `PATTERN`: Regex pattern to match VM names

### Options

- `--db-url TEXT`: Database URL (default: `sqlite:///data/vmware_inventory.db`)
- `--datacenter TEXT`: Filter by datacenter
- `--cluster TEXT`: Filter by cluster
- `--powerstate TEXT`: Filter by power state (poweredOn/poweredOff)
- `--limit INTEGER`: Maximum results to return (default: 50)
- `--case-sensitive`: Make regex search case-sensitive
- `--help`: Show help message

### Examples

```bash
# Search VMs starting with "prod-"
vmware-inv vm search "^prod-"

# Search VMs containing "web"
vmware-inv vm search "web"

# Search with filters
vmware-inv vm search "database" --datacenter "DC1" --powerstate poweredOn

# Case-sensitive search
vmware-inv vm search "PROD" --case-sensitive

# Search with custom limit
vmware-inv vm search "vm-.*" --limit 100
```

### Output

Displays:
- Total matches found
- Summary metrics (powered on, vCPUs, memory)
- Table with VM details (name, power, datacenter, cluster, resources)

## Label Commands

The `label` command group provides comprehensive label management capabilities.

### label create

Create a new label definition.

```bash
vmware-inv label create KEY VALUE [OPTIONS]
```

### Arguments

- `KEY`: Label key (e.g., "environment", "owner", "project")
- `VALUE`: Label value (e.g., "production", "john.doe", "web-app")

### Options

- `--description TEXT`: Label description
- `--color TEXT`: Hex color code (e.g., #FF0000)
- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# Create a simple label
vmware-inv label create environment production

# Create with description and color
vmware-inv label create environment staging \
  --description "Staging environment" \
  --color "#ffc107"

# Create owner labels
vmware-inv label create owner platform-team --color "#007bff"
vmware-inv label create owner database-team --color "#28a745"
```

### label list

List all label definitions.

```bash
vmware-inv label list [OPTIONS]
```

### Options

- `--key TEXT`: Filter by label key
- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# List all labels
vmware-inv label list

# List labels for specific key
vmware-inv label list --key environment
```

### label assign-vm

Assign a label to a VM.

```bash
vmware-inv label assign-vm VM_NAME KEY VALUE [OPTIONS]
```

### Arguments

- `VM_NAME`: Name of the VM
- `KEY`: Label key
- `VALUE`: Label value

### Options

- `--by TEXT`: Assigned by (user name)
- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# Assign environment label to VM
vmware-inv label assign-vm "web-server-01" environment production

# Assign with user tracking
vmware-inv label assign-vm "db-server-01" owner database-team --by "john.doe"
```

### label assign-folder

Assign a label to a folder with inheritance options.

```bash
vmware-inv label assign-folder FOLDER_PATH KEY VALUE [OPTIONS]
```

### Arguments

- `FOLDER_PATH`: Folder path (e.g., "/datacenter1/vm/production")
- `KEY`: Label key
- `VALUE`: Label value

### Options

- `--inherit-vms` / `--no-inherit-vms`: Apply to VMs in folder (default: yes)
- `--inherit-subfolders` / `--no-inherit-subfolders`: Apply to subfolders (default: no)
- `--by TEXT`: Assigned by (user name)
- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# Assign label to folder and VMs
vmware-inv label assign-folder "/dc1/vm/production" environment production

# Assign without inheriting to VMs
vmware-inv label assign-folder "/dc1/vm/test" environment test --no-inherit-vms

# Assign with recursive subfolder inheritance
vmware-inv label assign-folder "/dc1/vm/apps" project web-services \
  --inherit-subfolders --by "admin"
```

### label list-vm

List all labels for a VM.

```bash
vmware-inv label list-vm VM_NAME [OPTIONS]
```

### Arguments

- `VM_NAME`: Name of the VM

### Options

- `--inherited` / `--no-inherited`: Include inherited labels (default: yes)
- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# List all labels for a VM
vmware-inv label list-vm "web-server-01"

# List only direct labels
vmware-inv label list-vm "web-server-01" --no-inherited
```

### label list-folder

List all labels for a folder.

```bash
vmware-inv label list-folder FOLDER_PATH [OPTIONS]
```

### Arguments

- `FOLDER_PATH`: Folder path

### Options

- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# List folder labels
vmware-inv label list-folder "/dc1/vm/production"
```

### label find-vms

Find all VMs with a specific label.

```bash
vmware-inv label find-vms KEY VALUE [OPTIONS]
```

### Arguments

- `KEY`: Label key
- `VALUE`: Label value

### Options

- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# Find all production VMs
vmware-inv label find-vms environment production

# Find VMs owned by a team
vmware-inv label find-vms owner platform-team
```

### label find-folders

Find all folders with a specific label.

```bash
vmware-inv label find-folders KEY VALUE [OPTIONS]
```

### Arguments

- `KEY`: Label key
- `VALUE`: Label value

### Options

- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# Find all production folders
vmware-inv label find-folders environment production
```

### label sync-inherited

Re-sync inherited labels from folders to VMs.

```bash
vmware-inv label sync-inherited [OPTIONS]
```

### Options

- `--folder TEXT`: Sync only specific folder
- `--db-url TEXT`: Database URL
- `--help`: Show help message

### Examples

```bash
# Sync all inherited labels
vmware-inv label sync-inherited

# Sync labels for specific folder
vmware-inv label sync-inherited --folder "/dc1/vm/production"
```
