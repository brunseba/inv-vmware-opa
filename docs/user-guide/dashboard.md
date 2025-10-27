# Dashboard User Guide

Interactive web-based dashboard for analyzing VMware vSphere inventory data using Streamlit and Plotly.

## Overview

The VMware Inventory Dashboard provides a rich, interactive web interface for exploring and analyzing your VMware infrastructure. It features multiple specialized pages for different aspects of your inventory.

## Getting Started

### Launch the Dashboard

```bash
# Using the CLI (recommended)
vmware-inv dashboard

# With custom options
vmware-inv dashboard --port 8080 --db-url sqlite:///custom.db

# Don't open browser automatically
vmware-inv dashboard --no-browser

# Bind to all interfaces
vmware-inv dashboard --host 0.0.0.0
```

The dashboard will automatically open at `http://localhost:8501`.

## Pages

### 📊 Overview Page

High-level view of your VMware infrastructure:

- **Key Metrics**: Total VMs, powered on/off counts, total vCPUs and memory
- **Power State Distribution**: Visual breakdown of VM power states
- **Datacenter Distribution**: VMs distributed across datacenters
- **Cluster Analysis**: Top clusters by VM count
- **OS Configuration**: Most common operating systems

### 💾 Resources Page

Deep dive into resource allocation and utilization:

- **CPU Distribution**: vCPU allocation patterns across VMs
- **Memory Analysis**: Memory allocation by size ranges
- **Storage Metrics**:
  - Total provisioned vs. in-use storage
  - Storage efficiency metrics
  - Thin provisioning savings
- **Top Consumers**: Largest VMs by CPU, memory, and storage
- **Interactive Filters**: Filter by datacenter, cluster, and power state

### 🏗️ Infrastructure Page

Hierarchical view of your VMware infrastructure:

- **Datacenter Overview**: VMs and resources per datacenter
- **Cluster Metrics**: Cluster capacity and efficiency
- **Host Analysis**: Host-level resource distribution
- **Capacity Planning**: Resource utilization trends

### 🔍 VM Explorer

Advanced search and detailed VM inspection:

- **Search Functionality**: Find VMs by name, IP, or DNS
- **Detailed Views**:
  - General information (name, power state, UUID)
  - Resources (CPU, memory, storage)
  - Network configuration (IPs, DNS)
  - Infrastructure placement (datacenter, cluster, host)
- **Pagination**: Navigate large VM lists efficiently
- **Filters**: By datacenter, cluster, and power state

### 📈 Analytics Page

Advanced analytics and trend analysis:

- **Resource Allocation Patterns**:
  - CPU vs Memory scatter plots
  - Top 10 resource configurations
- **VM Creation Timeline**: Track VM provisioning over time
- **OS Distribution Analysis**:
  - Treemap visualizations
  - Sunburst charts
  - CPU allocation by OS
- **Cluster Efficiency Metrics**:
  - VMs per host ratios
  - Resource distribution bubble charts
- **Environment Classification**: VM distribution by environment

### ⚖️ Comparison View

Side-by-side infrastructure comparison:

- **Datacenter Comparison**:
  - VM count comparison
  - Resource allocation comparison
  - Radar charts for overall comparison
- **Cluster Comparison**:
  - VM distribution
  - Power state comparison
  - Resource allocation profiles
- **Host Comparison**:
  - VM density per host
  - Resource utilization

### 📁 Folder Analysis

Comprehensive folder-level analytics:

- **Folder Distribution**: VM counts per folder
- **Resource Analysis**:
  - CPU and memory allocation
  - Average resource profiles
- **Storage Analysis**:
  - Provisioned storage by folder
  - Storage utilization comparison
  - Efficiency metrics
- **Aggregation Options**:
  - Hierarchy level selection
  - Minimum VM filtering
  - Custom sorting

### 📊 Data Quality

Data completeness and quality metrics:

- **Field Completeness**: Percentage of populated fields
- **Missing Data Analysis**: Identify incomplete records
- **Recommendations**: Suggestions for data quality improvement

### 📄 PDF Export

Generate comprehensive PDF reports:

- **Report Types**:
  - **Standard**: Key charts and tables
  - **Extended (All Charts)**: Complete analytics with 20+ visualizations
  - **Summary Only**: Tables without charts
- **Configuration Options**:
  - Page size (Letter/A4)
  - Chart quality (DPI: 100-300)
  - Detailed tables toggle
  - Color scheme selection
- **Content Sections**:
  - Executive Summary
  - Infrastructure Overview
  - Resource Analysis
  - Storage Analysis
  - Folder Analysis
  - Extended Analytics (extended mode only)
  - Infrastructure Comparison (extended mode only)
  - Extended Folder Analytics (extended mode only)
  - Data Quality Report

See [PDF Export Guide](pdf-export.md) for detailed information.

## Configuration

### Database Connection

The dashboard supports any SQLAlchemy-compatible database:

```python
# SQLite (default)
sqlite:///vmware_inventory.db

# PostgreSQL
postgresql://user:password@host:5432/dbname

# MySQL
mysql://user:password@host:3306/dbname
```

Configure the database URL in the sidebar or via CLI:

```bash
vmware-inv dashboard --db-url "postgresql://user:pass@localhost/vmware"
```

### Performance Tips

For optimal performance with large datasets:

1. **Use PostgreSQL**: For inventories with >10,000 VMs
2. **Apply Filters**: Use datacenter/cluster filters to reduce result sets
3. **Adjust Page Size**: In VM Explorer, use appropriate pagination
4. **Index Database**: Ensure database indexes are created:
   ```bash
   python scripts/add_indexes.py
   ```

## Navigation

Use the sidebar to:

- Switch between pages
- Configure database connection
- Apply global filters
- Access help and documentation

## Tips & Best Practices

### Visualization Interactions

- **Hover**: Hover over charts for detailed tooltips
- **Zoom**: Click and drag to zoom on Plotly charts
- **Pan**: Hold Shift and drag to pan
- **Reset**: Double-click to reset view
- **Download**: Use camera icon to save charts as images

### Data Exploration

1. **Start with Overview**: Get a high-level understanding
2. **Drill Down**: Use Infrastructure page for hierarchy
3. **Deep Dive**: Use Resources page for detailed analysis
4. **Search**: Use VM Explorer for specific VMs
5. **Compare**: Use Comparison view for side-by-side analysis

### Reporting

1. **Generate PDF**: Use PDF Export for offline reports
2. **Export Data**: Use Streamlit's built-in CSV export
3. **Share Insights**: Share dashboard URL with team members
4. **Schedule**: Consider automating report generation

## Troubleshooting

### No Data Displayed

- Verify data has been loaded: `vmware-inv stats`
- Check database URL in sidebar
- Ensure database file exists and has correct permissions

### Performance Issues

- For large datasets, use PostgreSQL instead of SQLite
- Apply filters to reduce data volume
- Increase pagination page size
- Consider adding database indexes

### Port Already in Use

```bash
# Use a different port
vmware-inv dashboard --port 8502
```

### Connection Refused

- Check that database server is running (PostgreSQL/MySQL)
- Verify network connectivity
- Confirm firewall rules allow connection

## Advanced Features

### Custom Styling

The dashboard includes custom CSS for a polished appearance:

- Dark mode support
- Metric cards with visual indicators
- Consistent color schemes
- Responsive layouts

### Interactive Elements

- **Expandable Sections**: Click to expand/collapse
- **Tabs**: Organize related content
- **Tooltips**: Hover for explanations
- **Toggle Controls**: Show/hide advanced options

### Data Refresh

To refresh data:

1. Reload inventory: `vmware-inv load input.xlsx`
2. Refresh browser page
3. Dashboard automatically queries latest data

## Integration

### With CI/CD

```yaml
# Example GitHub Actions workflow
- name: Generate Dashboard Report
  run: |
    vmware-inv load data.xlsx
    vmware-inv dashboard --no-browser &
    sleep 5
    # Take screenshot or generate PDF
```

### With Monitoring

Integrate dashboard with monitoring systems:

- Export metrics to Prometheus
- Create alerting rules based on inventory data
- Track infrastructure changes over time

## Next Steps

- [PDF Export Guide](pdf-export.md) - Learn about comprehensive PDF reporting
- [CLI Commands](cli-commands.md) - Explore command-line features
- [API Reference](../api/reference.md) - Programmatic access to data

## Support

For issues or questions:

- Check [Troubleshooting](../troubleshooting.md)
- Review [FAQ](../faq.md)
- Open an issue on GitHub
