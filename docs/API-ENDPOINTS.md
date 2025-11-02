# Application Endpoints & Pages

## Overview

This application is built with **Streamlit**, which uses a page-based navigation system rather than traditional REST API endpoints. All pages are accessed through the web interface at the base URL (default: `http://localhost:8501`).

## Base URL

```
http://localhost:8501
```

## Dashboard Pages (Streamlit)

### 🏠 Main Navigation

| Page Name | Internal Route | Description | Icon |
|-----------|---------------|-------------|------|
| Overview | `Overview` | Main dashboard with key metrics and visualizations | 📊 |

### 🔍 Explore & Analyze

| Page Name | Internal Route | Description | Icon |
|-----------|---------------|-------------|------|
| Data Explorer | `Data Explorer` | PyGWalker-based interactive data exploration | 🔬 |
| Advanced Explorer | `Advanced Explorer` | SQL query interface with PyGWalker visualization | 🔬 |
| VM Explorer | `VM Explorer` | Detailed VM inspection and analysis | 🖥️ |
| VM Search | `VM Search` | Advanced VM search and filtering | 🔎 |
| Analytics | `Analytics` | Resource allocation and OS analysis | 📈 |
| Comparison | `Comparison` | Side-by-side datacenter/cluster comparisons | ⚖️ |
| Data Quality | `Data Quality` | Field completeness and data quality analysis | ✅ |

### 🏗️ Infrastructure

| Page Name | Internal Route | Description | Icon |
|-----------|---------------|-------------|------|
| Resources | `Resources` | Resource metrics and allocation | 💻 |
| Infrastructure | `Infrastructure` | Infrastructure topology and details | 🌐 |
| Folder Analysis | `Folder Analysis` | Folder-level resource and storage analytics | 📁 |
| Folder Labelling | `Folder Labelling` | Label management and assignment | 🏷️ |

### 🚀 Migration

| Page Name | Internal Route | Description | Icon |
|-----------|---------------|-------------|------|
| Migration Targets | `Migration Targets` | Define and manage migration targets | 🎯 |
| Strategy Configuration | `Strategy Configuration` | Configure migration strategies | ⚙️ |
| Migration Planning | `Migration Planning` | Plan and schedule migrations | 📋 |
| Migration Scenarios | `Migration Scenarios` | Create and analyze migration scenarios | 🔄 |

### ⚙️ Management

| Page Name | Internal Route | Description | Icon |
|-----------|---------------|-------------|------|
| Data Import | `Data Import` | Import data from Excel files | 📥 |
| Database Backup | `Database Backup` | Backup and restore database | 💾 |

### 📄 Export & Help

| Page Name | Internal Route | Description | Icon |
|-----------|---------------|-------------|------|
| PDF Export | `PDF Export` | Generate PDF reports | 📄 |
|| Documentation | `Help` | Built-in help and documentation | 📚 |

## Left Menu URI List

All dashboard pages are accessible via Streamlit's page navigation system. The URIs below represent the query parameter format that can be used to directly access each page.

### Complete URI List

```
# Base URL
http://localhost:8501/

# Main Navigation
http://localhost:8501/?page=Overview

# Explore & Analyze
http://localhost:8501/?page=Data_Explorer
http://localhost:8501/?page=Advanced_Explorer
http://localhost:8501/?page=VM_Explorer
http://localhost:8501/?page=VM_Search
http://localhost:8501/?page=Analytics
http://localhost:8501/?page=Comparison
http://localhost:8501/?page=Data_Quality

# Infrastructure
http://localhost:8501/?page=Resources
http://localhost:8501/?page=Infrastructure
http://localhost:8501/?page=Folder_Analysis
http://localhost:8501/?page=Folder_Labelling

# Migration
http://localhost:8501/?page=Migration_Targets
http://localhost:8501/?page=Strategy_Configuration
http://localhost:8501/?page=Migration_Planning
http://localhost:8501/?page=Migration_Scenarios

# Management
http://localhost:8501/?page=Data_Import
http://localhost:8501/?page=Database_Backup

# Export & Help
http://localhost:8501/?page=PDF_Export
http://localhost:8501/?page=Help
```

### URI Format Notes

1. **Spaces to Underscores**: Page names with spaces use underscores in URIs (e.g., "Data Explorer" → `Data_Explorer`)
2. **Case Sensitive**: Page names are case-sensitive
3. **Query Parameter**: The `page` query parameter determines which page to display
4. **Default Page**: Accessing the base URL without parameters shows the Overview page
5. **Deep Linking**: These URIs can be bookmarked or shared for direct page access

### Navigation Groups

| Group | Page Count | URI Prefix Pattern |
|-------|------------|--------------------|
| Main Navigation | 1 | `?page=Overview` |
| Explore & Analyze | 7 | `?page=<Explorer|Search|Analytics|Comparison|Data_Quality>` |
| Infrastructure | 4 | `?page=<Resources|Infrastructure|Folder_*>` |
| Migration | 4 | `?page=<Migration_*|Strategy_Configuration>` |
| Management | 2 | `?page=<Data_Import|Database_Backup>` |
| Export & Help | 2 | `?page=<PDF_Export|Help>` |
| **Total** | **20** | |

### Programmatic Access

To navigate programmatically within the application:

```python
import streamlit as st

# Set query parameter
st.query_params["page"] = "VM_Explorer"

# Or use the PageNavigator utility
from src.utils.navigation import PageNavigator
PageNavigator.navigate_to("VM Explorer")
```

### Browser Bookmarks

Create browser bookmarks for quick access to frequently used pages:

```
📊 Overview          → http://localhost:8501/?page=Overview
🔬 Data Explorer     → http://localhost:8501/?page=Data_Explorer
🖥️ VM Explorer       → http://localhost:8501/?page=VM_Explorer
📁 Folder Analysis   → http://localhost:8501/?page=Folder_Analysis
🎯 Migration Targets → http://localhost:8501/?page=Migration_Targets
```

## CLI Endpoints

The CLI provides command-line access to functionality:

### Data Management

```bash
# Load data
cli load <excel_file> [--db-url <url>] [--clear]

# View statistics
cli stats [--db-url <url>]

# List VMs
cli list [--db-url <url>] [--datacenter <name>] [--cluster <name>] [--limit <n>]
```

### Labeling

```bash
# List labels
cli label list [--db-url <url>]

# Create label
cli label create <key> <value> [--description <desc>] [--color <hex>]

# Assign labels
cli label assign <label_key:value> --folder <path>
cli label assign <label_key:value> --vm-id <id>

# Propagate labels
cli label propagate [--dry-run]
```

### Anonymization (BETA)

```bash
# Anonymize database
cli anonymize database --output <file> [--mapping-file <file>]

# Anonymize Excel
cli anonymize excel <input> --output <output> [--mapping-config <config>]

# Generate mapping template
cli anonymize excel <input> --generate-mapping-template <output>

# Show mapping
cli anonymize show-mapping <mapping_file>
```

## Page Navigation System

### Internal Navigation

Streamlit pages are navigated using the `PageNavigator` utility:

```python
# Navigate to a page
PageNavigator.navigate_to("Overview")
PageNavigator.navigate_to("VM Explorer")

# Get current page
current_page = PageNavigator.get_current_page()
```

### URL Parameters

Streamlit doesn't use traditional URL routing, but state is managed through:
- **Session State**: `st.session_state`
- **Query Parameters**: Can be set via `st.query_params` (Streamlit 1.30+)

### State Management Keys

The application uses the following session state keys:

| Key | Type | Description |
|-----|------|-------------|
| `db_url` | `str` | Database connection URL |
| `page` | `str` | Current active page |
| `theme` | `str` | UI theme (light/dark) |
| `cache_cleared` | `bool` | Cache clear flag |
| `vm_counts` | `dict` | Cached VM counts |

## API Architecture

### No REST API

This application **does not expose a REST API**. All functionality is accessed through:

1. **Web Dashboard** (Streamlit) - Interactive web interface
2. **CLI** (Click) - Command-line interface
3. **Python API** - Direct module imports

### Direct Database Access

The application connects directly to databases:

**Supported Databases:**
- SQLite (default): `sqlite:///data/vmware_inventory.db`
- PostgreSQL: `postgresql://user:pass@host/db`
- MySQL: `mysql://user:pass@host/db`

### Authentication

- **Dashboard**: No authentication by default (runs locally)
- **CLI**: No authentication (local file system access)
- **Database**: Uses database-specific authentication

## Deployment URLs

### Local Development

```
http://localhost:8501
```

### Production Deployment

When deployed (e.g., via Docker, cloud platforms), the base URL would be:

```
http://<your-domain>:8501
```

Or with reverse proxy:

```
https://<your-domain>/
```

## WebSocket Connection

Streamlit uses WebSocket for real-time updates:

```
ws://localhost:8501/_stcore/stream
```

## Static Assets

Streamlit serves static assets at:

```
http://localhost:8501/static/
```

## Health Check

Streamlit provides a health check endpoint:

```
http://localhost:8501/_stcore/health
```

## Configuration Endpoints

These are internal Streamlit endpoints:

| Endpoint | Purpose |
|----------|---------|
| `/_stcore/stream` | WebSocket stream for live updates |
| `/_stcore/health` | Health check |
| `/_stcore/allowed-message-origins` | CORS configuration |
| `/media/` | Media file serving |

## File Upload Endpoints

Data import uses Streamlit's file uploader component, which handles:
- Excel files (`.xlsx`, `.xls`)
- CSV files (`.csv`)
- Max file size: Configurable (default: 200MB)

## Notes

1. **No REST API**: This is a desktop/local web application, not a REST API service
2. **Single User**: Designed for single-user local deployment
3. **No Authentication**: Authentication not included by default
4. **Page-Based**: Uses Streamlit's page navigation, not URL routing
5. **WebSocket**: Real-time updates via WebSocket connection
6. **Database Direct**: Connects directly to databases, no API layer

## Future Endpoints (Potential)

If a REST API were to be added in the future, potential endpoints might include:

```
GET    /api/v1/vms                    # List VMs
GET    /api/v1/vms/{id}               # Get VM details
GET    /api/v1/stats                  # Get statistics
POST   /api/v1/import                 # Import data
GET    /api/v1/labels                 # List labels
POST   /api/v1/labels                 # Create label
POST   /api/v1/anonymize              # Anonymize data
GET    /api/v1/export/pdf             # Export PDF report
```

**Note**: These are hypothetical and not currently implemented.

## Related Documentation

- [Dashboard User Guide](features/dashboard-guide.md)
- [CLI Reference](cli/README.md)
- [Anonymization](features/excel-column-mapping.md)
- [Database Schema](development/database-schema.md)
