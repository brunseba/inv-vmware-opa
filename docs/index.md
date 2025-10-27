# VMware Inventory OPA

A Python CLI tool for managing VMware inventory data from Excel exports into a structured database.

## Features

- **Excel Import**: Load VMware inventory data from Excel files
- **Database Storage**: Store inventory in SQLite or other SQL databases
- **CLI Interface**: Simple command-line interface for data management
- **Statistics**: Query and analyze inventory data
- **Filtering**: Filter VMs by datacenter, cluster, and other attributes

## Architecture

```mermaid
graph LR
    A[Excel File] --> B[CLI Loader]
    B --> C[Parser]
    C --> D[SQLAlchemy Models]
    D --> E[Database]
    E --> F[Query/Stats]
```

## Quick Start

```bash
# Install the package
pipx install inv-vmware-opa

# Load data from Excel
uv run python -m src.cli load inputs/vmware-inv.xlsx --clear

# View statistics
uv run python -m src.cli stats

# List VMs
uv run python -m src.cli list --limit 10
```

## Use Cases

- **Inventory Management**: Track and organize VMware infrastructure
- **Reporting**: Generate statistics and reports from inventory data
- **Analysis**: Query and filter VMs by various attributes
- **Migration Planning**: Analyze VM distributions and resource usage

## Requirements

- Python 3.10 or higher
- SQLAlchemy 2.0+
- Click 8.0+
- Pandas 2.0+
- OpenPyXL 3.0+

## License

MIT License
