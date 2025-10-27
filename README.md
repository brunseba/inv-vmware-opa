# VMware Inventory OPA

A Python CLI tool for managing VMware inventory data from Excel exports into a structured database.

## Features

- 📥 **Excel Import**: Load VMware inventory data from Excel files
- 💾 **Database Storage**: Store inventory in SQLite or other SQL databases  
- ⚡ **CLI Interface**: Simple command-line interface for data management
- 📊 **Statistics**: Query and analyze inventory data
- 🔍 **Filtering**: Filter VMs by datacenter, cluster, and other attributes

## Installation

```bash
# Using pipx (recommended)
pipx install inv-vmware-opa

# Or using uv
uv pip install inv-vmware-opa
```

## Quick Start

```bash
# Load data from Excel
uv run python -m src.cli load inputs/vmware-inv.xlsx --clear

# View statistics
uv run python -m src.cli stats

# List VMs
uv run python -m src.cli list --limit 10

# Filter by datacenter
uv run python -m src.cli list --datacenter "PROD-WNG-WRK-HPI"
```

## CLI Commands

### load

Load VMware inventory from Excel file:

```bash
uv run python -m src.cli load <excel_file> [--db-url <url>] [--clear]
```

### stats

Show inventory statistics:

```bash
uv run python -m src.cli stats [--db-url <url>]
```

### list

List virtual machines:

```bash
uv run python -m src.cli list [--db-url <url>] [--datacenter <name>] [--cluster <name>] [--limit <n>]
```

## Database Support

By default, data is stored in SQLite (`vmware_inventory.db`). You can use other databases:

```bash
# PostgreSQL
--db-url postgresql://user:password@localhost/vmware_inv

# MySQL
--db-url mysql://user:password@localhost/vmware_inv

# SQLite with custom path
--db-url sqlite:///path/to/database.db
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/brun_s/inv-vmware-opa.git
cd inv-vmware-opa

# Install with uv
uv sync

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src tests/
```

### Documentation

```bash
# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mkdocs build
```

## Requirements

- Python >= 3.10
- SQLAlchemy >= 2.0
- Click >= 8.0
- Pandas >= 2.0
- OpenPyXL >= 3.0

## License

MIT License

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit using conventional commits
4. Submit a pull request

See [CONTRIBUTING.md](docs/development/contributing.md) for details.