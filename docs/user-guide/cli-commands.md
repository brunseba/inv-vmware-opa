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

## list

List virtual machines from the inventory.

```bash
uv run python -m src.cli list [OPTIONS]
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
uv run python -m src.cli list

# List 50 VMs
uv run python -m src.cli list --limit 50

# Filter by datacenter
uv run python -m src.cli list --datacenter "PROD-WNG-WRK-HPI"

# Filter by cluster
uv run python -m src.cli list --cluster "GCAB-POD-DMX-NO"

# Combine filters
uv run python -m src.cli list --datacenter "PROD-WNG-WRK-HPI" --cluster "GCAB-POD-DMX-NO" --limit 20
```

### Output

The list command displays a table with:
- VM Name
- Power State
- Datacenter
- Cluster
