# VMware Inventory OPA

A Python CLI tool for managing VMware inventory data from Excel exports into a structured database.

## Features

### Core Functionality
- **📥 Excel Import**: Load VMware inventory data from Excel files
- **💾 Database Storage**: Store inventory in SQLite, PostgreSQL, or MySQL
- **⚡ CLI Interface**: Simple command-line interface for data management
- **📊 Statistics**: Query and analyze inventory data
- **🔍 Filtering**: Filter VMs by datacenter, cluster, and other attributes

### Interactive Dashboard
- **🖥️ Web Interface**: Rich Streamlit-based dashboard with multiple views
- **📈 Advanced Analytics**: CPU vs Memory patterns, OS distribution, cluster efficiency
- **⚖️ Comparison Tools**: Side-by-side datacenter, cluster, and host comparisons
- **📁 Folder Analysis**: Comprehensive folder-level resource and storage analytics
- **🔎 VM Explorer**: Advanced search and detailed VM inspection
- **📊 Data Quality**: Field completeness analysis and recommendations

### PDF Export
- **📄 Professional Reports**: Generate comprehensive PDF reports with 20+ visualizations
- **🎨 Multiple Formats**: Standard, Extended (all charts), or Summary (tables only)
- **⚙️ Customizable**: Configurable page size, chart quality (DPI), color schemes
- **📑 Rich Content**: Executive summaries, infrastructure analysis, resource metrics, storage efficiency

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
