# VMware Inventory OPA

A Python CLI tool for managing VMware inventory data from Excel exports into a structured database.

![Dashboard Overview](docs/images/v0.7.0/overview_light.png)

## Screenshots

<details>
<summary>📊 View Dashboard Screenshots</summary>

### Overview Dashboard
![Overview](docs/images/v0.7.0/overview_light.png)
*Interactive overview with key metrics and visualizations*

### Data Explorer
![Data Explorer](docs/images/v0.7.0/data_explorer_light.png)
*PyGWalker-based interactive data exploration with drag-and-drop analytics*

### Advanced Explorer
![Advanced Explorer](docs/images/v0.7.0/advanced_explorer_light.png)
*SQL query interface with PyGWalker visualization*

### VM Explorer
![VM Explorer](docs/images/v0.7.0/vm_explorer_light.png)
*Detailed VM inspection and analysis with rich tabbed interface*

### VM Search
![VM Search](docs/images/v0.7.0/vm_search_light.png)
*Advanced VM search and filtering capabilities*

### Analytics
![Analytics](docs/images/v0.7.0/analytics_light.png)
*Resource allocation patterns and OS analysis*

### Comparison
![Comparison](docs/images/v0.7.0/comparison_light.png)
*Side-by-side datacenter and cluster comparisons*

### Data Quality
![Data Quality](docs/images/v0.7.0/data_quality_light.png)
*Field completeness and data quality analysis*

### Resources
![Resources](docs/images/v0.7.0/resources_light.png)
*Resource metrics and allocation dashboard*

### Infrastructure
![Infrastructure](docs/images/v0.7.0/infrastructure_light.png)
*Infrastructure topology and details*

### Folder Analysis
![Folder Analysis](docs/images/v0.7.0/folder_analysis_light.png)
*Folder-level resource and storage analytics*

### Folder Labelling
![Folder Labelling](docs/images/v0.7.0/folder_labelling_light.png)
*Label management and assignment interface*

### Migration Targets
![Migration Targets](docs/images/v0.7.0/migration_targets_light.png)
*Define and manage migration targets*

### Strategy Configuration
![Strategy Configuration](docs/images/v0.7.0/strategy_configuration_light.png)
*Configure migration strategies*

### Migration Planning
![Migration Planning](docs/images/v0.7.0/migration_planning_light.png)
*Plan and schedule migrations*

### Migration Scenarios
![Migration Scenarios](docs/images/v0.7.0/migration_scenarios_light.png)
*Create and analyze migration scenarios*

### Data Import
![Data Import](docs/images/v0.7.0/data_import_light.png)
*Import data from Excel files*

### Database Backup
![Database Backup](docs/images/v0.7.0/database_backup_light.png)
*Backup and restore database*

### PDF Export
![PDF Export](docs/images/v0.7.0/pdf_export_light.png)
*Generate professional PDF reports*

### Documentation
![Help](docs/images/v0.7.0/help_light.png)
*Built-in help and documentation*

</details>

## What's New in v0.7.2

### 🔗 Query Parameter Navigation
Direct URL navigation support:
- **Direct Page Access**: Navigate to any page via URL (e.g., `?page=Data_Explorer`)
- **Browser Bookmarks**: Save and share direct links to specific pages
- **Screenshot Automation**: Fast URI-based screenshot capture
- **20 Pages**: Complete coverage of all dashboard pages

### 📸 Screenshot Tool Enhancement
Automated screenshot capture improvements:
- **URI Navigation**: 3-5x faster page navigation
- **Centralized Page List**: Single source from API-ENDPOINTS.md
- **All Pages**: Captures all 20 dashboard pages
- **Screenshot CLI**: Enhanced `vmware-screenshot` command

### 🔐 Anonymization (BETA)
New anonymization capabilities for creating sanitized demo data:
- **Excel Anonymization**: Anonymize Excel files with custom column mapping
- **Database Anonymization**: Anonymize entire SQLite databases
- **Column Mapping**: Flexible YAML/JSON configuration for custom Excel formats
- **Smart Anonymization**: Preserves relationships, metrics, and structure
- **Reproducible**: Seed-based anonymization for consistent results

### 📊 Enhanced Dashboard
- **20 Specialized Pages**: Complete dashboard coverage
- **Data Exploration**: PyGWalker integration with SQL query interface
- **Migration Planning**: Full migration workflow (targets, strategies, planning, scenarios)
- **Folder Management**: Enhanced folder analysis and labeling
- **Performance**: Query parameter navigation and optimizations

### 📝 Documentation
- Complete screenshot gallery (all 20 pages)
- Query parameter navigation guide
- Screenshot tool automation docs
- Comprehensive anonymization guides
- Updated API endpoints documentation

## Features

### Core Functionality
- 📥 **Excel Import**: Load VMware inventory data from Excel files
- 💾 **Database Storage**: Store inventory in SQLite, PostgreSQL, or MySQL
- ⚡ **CLI Interface**: Simple command-line interface for data management
- 📊 **Statistics**: Query and analyze inventory data
- 🔍 **Filtering**: Filter VMs by datacenter, cluster, and other attributes

### Interactive Dashboard
- 🖥️ **Web Interface**: Rich Streamlit-based dashboard with **20 specialized pages**
- 🔬 **Data Exploration**: PyGWalker-based interactive explorer with SQL query interface
- 📊 **Overview & Analytics**: Resource allocation patterns, OS analysis, cluster efficiency
- ⚖️ **Comparison Tools**: Side-by-side datacenter, cluster, and host comparisons
- 📁 **Folder Management**: Comprehensive folder-level analytics and labeling system
- 🔎 **VM Tools**: Advanced search, detailed inspection, and quality analysis
- 🚀 **Migration Planning**: Full migration workflow from targets to scenarios
- 📊 **Data Quality**: Field completeness analysis with recommendations

### PDF Export
- 📄 **Professional Reports**: Generate comprehensive PDF reports with 25+ visualizations
- 🎨 **Multiple Formats**: Standard (6-8 charts), Extended (all charts), or Summary (tables only)
- ⚙️ **Customizable**: Configurable page size, chart quality (100-300 DPI), color schemes
- 📑 **Rich Content**: Executive summaries, infrastructure comparisons, resource analytics, storage efficiency

### Anonymization (BETA)
- 🔐 **Data Privacy**: Anonymize sensitive data for demos and documentation
- 📊 **Excel & Database**: Anonymize Excel files or entire SQLite databases
- 🗺️ **Column Mapping**: Flexible column mapping with YAML/JSON configuration
- 🎯 **Selective**: Choose specific fields to anonymize
- 🔄 **Reproducible**: Consistent results with seed-based anonymization

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

### anonymize (BETA)

Anonymize sensitive data:

```bash
# Anonymize Excel file
uv run python -m src.cli anonymize excel input.xlsx -o anonymized.xlsx

# Anonymize with custom column mapping
uv run python -m src.cli anonymize excel input.xlsx \
  --generate-mapping-template mapping.yaml  # Generate template
uv run python -m src.cli anonymize excel input.xlsx \
  -o output.xlsx --mapping-config mapping.yaml  # Use custom mapping

# Anonymize database
uv run python -m src.cli anonymize database \
  --output data/anonymized.db --mapping-file mapping.json
```

See [Anonymization Documentation](docs/features/excel-column-mapping.md) for details.

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