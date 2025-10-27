# Quick Start Guide

This guide will help you get started with the VMware Inventory CLI.

## Prerequisites

- Python 3.10 or higher installed
- VMware inventory Excel export file
- Basic command-line knowledge

## Step 1: Install the CLI

```bash
# Using uv (recommended for development)
uv pip install inv-vmware-opa

# Or using pipx
pipx install inv-vmware-opa
```

## Step 2: Prepare Your Data

Export your VMware inventory to Excel format. The tool expects a file with VM information including:

- VM name, power state, configuration
- CPU, memory, disk, network information
- Datacenter, cluster, host details
- And 75+ other attributes

## Step 3: Load Data

Load your Excel file into the database:

```bash
uv run python -m src.cli load inputs/vmware-inv.xlsx --clear
```

Expected output:
```
Loading data from inputs/vmware-inv.xlsx...
✓ Successfully loaded 5 records into database
Database: sqlite:///data/vmware_inventory.db
```

## Step 4: View Statistics

Check your inventory statistics:

```bash
uv run python -m src.cli stats
```

Expected output:
```
=== VMware Inventory Statistics ===

Total VMs: 5
  - Powered On:  5
  - Powered Off: 0

Infrastructure:
  - Datacenters: 1
  - Clusters:    3
  - Hosts:       4
```

## Step 5: List VMs

View your virtual machines:

```bash
# List first 10 VMs
uv run python -m src.cli list

# List more VMs
uv run python -m src.cli list --limit 50

# Filter by datacenter
uv run python -m src.cli list --datacenter "PROD-WNG-WRK-HPI"
```

## Next Steps

- Explore [CLI Commands](../user-guide/cli-commands.md) for advanced usage
- Learn about [Database Schema](../user-guide/database-schema.md)
- Configure different database backends (PostgreSQL, MySQL)

## Common Tasks

### Update Inventory

To refresh your inventory data:

```bash
uv run python -m src.cli load inputs/vmware-inv.xlsx --clear
```

### Query Specific Clusters

```bash
uv run python -m src.cli list --cluster "GCAB-POD-DMX-NO" --limit 20
```

### Export to Different Database

```bash
# PostgreSQL
uv run python -m src.cli load inputs/vmware-inv.xlsx \
  --db-url postgresql://user:password@localhost/vmware_inv

# MySQL
uv run python -m src.cli load inputs/vmware-inv.xlsx \
  --db-url mysql://user:password@localhost/vmware_inv
```

## Troubleshooting

### Module Not Found

If you see `ModuleNotFoundError`, ensure you're running commands with `uv run`:

```bash
uv run python -m src.cli --help
```

### Database Locked

If you encounter database lock errors, ensure no other process is accessing the database file.

### Excel File Not Found

Make sure the path to your Excel file is correct:

```bash
# Use absolute path if needed
uv run python -m src.cli load /path/to/vmware-inv.xlsx
```
