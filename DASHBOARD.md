# VMware vSphere Inventory Dashboard

Interactive web-based dashboard for analyzing VMware vSphere inventory data using Streamlit and Plotly.

## Features

### 📊 Overview Page
- High-level statistics (total VMs, powered on/off, resources)
- Power state distribution
- VM distribution by datacenter and cluster
- OS configuration analysis
- Infrastructure summary

### 💾 Resources Page
- CPU and memory distribution analysis
- Top resource consumers
- Storage analysis (provisioned, in-use, utilization)
- Interactive filters by datacenter, cluster, and power state

### 🏗️ Infrastructure Page
- Datacenter, cluster, and host hierarchy
- Resource distribution across infrastructure
- Cluster efficiency metrics
- Host capacity analysis

### 🔍 VM Explorer
- Advanced search functionality
- VM details with tabs (General, Resources, Network, Infrastructure)
- Pagination support
- Filter by datacenter and power state

### 📈 Analytics Page
- Resource allocation patterns
- VM creation timeline
- OS distribution treemaps and sunburst charts
- Cluster efficiency metrics
- Environment classification

## Installation

Install dependencies using uv:

```bash
uv sync
```

Or install the package:

```bash
pipx install .
```

## Running the Dashboard

### Option 1: Using CLI (Recommended)

```bash
vmware-inv dashboard
```

This will start the dashboard on `http://localhost:8501`

### Option 2: CLI with custom options

```bash
# Custom port and database
vmware-inv dashboard --port 8080 --db-url sqlite:///custom.db

# Don't open browser automatically
vmware-inv dashboard --no-browser

# Bind to all interfaces
vmware-inv dashboard --host 0.0.0.0
```

### Option 3: Direct execution

```bash
streamlit run app.py
```

Then configure the database URL in the sidebar.

## Usage

1. **Load Data**: First, load your VMware inventory data into the database:
   ```bash
   vmware-inv load input.xlsx --db-url sqlite:///data/vmware_inventory.db
   ```

2. **Launch Dashboard**: Start the web dashboard:
   ```bash
   vmware-inv dashboard
   ```

3. **Access**: Your browser will automatically open to `http://localhost:8501`

4. **Navigate**: Use the sidebar to:
   - Change the database URL if needed
   - Switch between different views (Overview, Resources, Infrastructure, etc.)

## Pages Overview

### Navigation
Use the sidebar radio buttons to switch between pages:
- **📊 Overview**: Quick insights and key metrics
- **💾 Resources**: Deep dive into CPU, memory, and storage
- **🏗️ Infrastructure**: Analyze datacenters, clusters, and hosts
- **🔍 VM Explorer**: Search and inspect individual VMs
- **📈 Analytics**: Advanced analytics and trends

## Configuration

### Database Connection
The dashboard supports any SQLAlchemy-compatible database URL:

- SQLite: `sqlite:///data/vmware_inventory.db`
- PostgreSQL: `postgresql://user:pass@host:5432/db`
- MySQL: `mysql://user:pass@host:3306/db`

### Customization
Modify `app.py` to:
- Change page layout
- Add custom CSS
- Modify navigation options
- Add new pages

## Requirements

- Python >= 3.10
- streamlit >= 1.40.0
- plotly >= 5.24.0
- pandas >= 2.3.3
- sqlalchemy >= 2.0.44

## Tips

- Use filters to focus on specific datacenters or clusters
- Hover over charts for detailed information
- Use the search function in VM Explorer for quick lookups
- Export dataframes to CSV using Streamlit's built-in functionality

## Troubleshooting

### No data displayed
- Ensure data has been loaded using `vmware-inv load`
- Verify the database URL in the sidebar
- Check database file permissions

### Performance issues
- For large datasets (>10,000 VMs), consider using PostgreSQL
- Adjust page size in VM Explorer
- Use filters to reduce result sets

### Port already in use
```bash
streamlit run app.py --server.port 8502
```

## Development

To add a new page:

1. Create a new file in `pages/` directory
2. Implement a `render(db_url: str)` function
3. Add the page to the navigation in `app.py`

Example:
```python
# pages/my_page.py
import streamlit as st

def render(db_url: str):
    st.title("My Custom Page")
    # Your code here
```

## License

See LICENSE file for details.
