# PDF Export Guide

Generate comprehensive, professional PDF reports from your VMware inventory data with rich visualizations and detailed analytics.

## Overview

The PDF Export feature allows you to create offline reports with multiple visualization types and customization options. Perfect for presentations, archival, and sharing with stakeholders who don't have dashboard access.

## Report Types

### Standard Report (Default)

Balanced report with key charts and comprehensive tables:

- **File Size**: ~100-200 KB
- **Generation Time**: 5-15 seconds
- **Sections**: 7 core sections
- **Charts**: 6-8 essential visualizations
- **Best For**: Regular reporting, quick overviews, email distribution

**Includes**:
- Executive Summary with power state chart
- Infrastructure overview with datacenter/cluster charts
- Resource analysis (CPU/memory distribution)
- Storage analysis with efficiency metrics
- Folder analysis (top 15 folders)
- Data quality report

### Extended Report (All Charts)

Comprehensive report with ALL analytics from the dashboard:

- **File Size**: ~200-500 KB
- **Generation Time**: 20-40 seconds
- **Sections**: 10 sections (standard + 3 extended)
- **Charts**: 20+ visualizations
- **Best For**: Executive presentations, detailed analysis, audit reports

**Includes everything in Standard plus**:

Extended Analytics section:
- CPU vs Memory scatter plots (by power state)
- Top 10 resource configurations
- Operating system distribution (bar + pie)
- Cluster efficiency metrics
- VMs per host by cluster
- Cluster resource bubble charts
- Environment distribution

Infrastructure Comparison section:
- Datacenter VM count comparison
- Power state distribution comparison
- Normalized resource comparison
- Cluster VM distribution
- Cluster resource allocation scatter plots

Extended Folder Analytics section:
- Folder size distribution histogram
- Resource allocation grouped bars
- Average resource profile scatter plots
- Top folders by provisioned storage
- Storage utilization comparison
- Storage efficiency scatter plots
- Average provisioned storage per VM

### Summary Report (Tables Only)

Minimalist report with tables and no charts:

- **File Size**: ~50-100 KB
- **Generation Time**: 2-5 seconds
- **Sections**: All standard sections
- **Charts**: None
- **Best For**: Data archival, text-based analysis, minimal file size

## Configuration Options

### Report Type

Select the level of detail:

```python
Report Type:
- Standard         # Balanced charts and tables
- Extended (All Charts)  # Complete analytics
- Summary Only     # Tables only
```

### Page Size

Choose document format:

- **Letter** (8.5" × 11"): Standard US format
- **A4** (210mm × 297mm): International standard

### Chart Quality (DPI)

Control image resolution (applies only when charts are included):

- **100 DPI**: Small file size, screen viewing
- **150 DPI**: Balanced (recommended)
- **200 DPI**: High quality, printing
- **300 DPI**: Maximum quality, professional printing

**Impact**:
- Higher DPI = Better quality + Larger file size + Longer generation time
- Lower DPI = Faster generation + Smaller files + Lower quality

### Advanced Options

#### Detailed Tables

Toggle to include/exclude extended table information:

- **Enabled**: Full VM details, extra columns
- **Disabled**: Essential information only

#### Color Scheme

Choose visualization color palette:

- **Default**: Blue/green professional theme
- **Vibrant**: High-contrast colors
- **Monochrome**: Grayscale for B&W printing

#### Max Items

Control number of items in top-N lists:

- **10**: Quick overview
- **15**: Standard (default)
- **20**: Detailed
- **25**: Comprehensive

#### Include Null Values

Option to show or hide VMs with missing data:

- **Enabled**: Show all VMs
- **Disabled**: Filter out incomplete records

## Report Sections

### Executive Summary

High-level metrics and key statistics:

- Total VMs, powered on/off counts
- Total vCPUs and memory allocation
- Datacenter, cluster, and host counts
- Power state distribution pie chart
- Summary narrative

### Infrastructure Overview

Datacenter and cluster analysis:

- Top 10 datacenters by VM count (table + bar chart)
- Top 10 clusters with resource breakdown (table + charts)
- Resource allocation visualization

### Resource Analysis

CPU and memory allocation patterns:

- vCPU distribution table and bar chart
- Memory allocation by size ranges
- Resource consumption analysis

### Storage Analysis

Storage metrics and efficiency:

- Total provisioned vs. in-use storage
- Storage efficiency percentage
- Thin provisioning savings
- Storage breakdown visualizations

### Folder Analysis

VM organization by folders:

- Top 15 folders by VM count
- Resource allocation per folder
- Folder-level metrics table
- Horizontal bar chart visualization

### Extended Analytics

*(Extended mode only)*

Advanced resource and OS analysis:

- CPU vs Memory scatter plots colored by power state
- Top 10 VM resource configurations
- Operating system distribution (bar + pie charts)
- Cluster efficiency: VMs per host
- Cluster resource bubble charts
- Environment distribution pie chart

### Infrastructure Comparison

*(Extended mode only)*

Side-by-side infrastructure comparisons:

- Datacenter comparison (VM count, power state, resources)
- Top clusters comparison (VMs, powered on, resources)
- Resource allocation scatter plots
- Multi-panel comparison visualizations

### Extended Folder Analytics

*(Extended mode only)*

Comprehensive folder-level insights:

- Folder size distribution histogram
- Top folders resource allocation (grouped bars)
- Average resource profiles (scatter plots)
- Storage analysis:
  - Provisioned storage by folder
  - Storage utilization comparison
  - Storage efficiency metrics
  - Average provisioned per VM

### Data Quality Report

Field completeness analysis:

- Completeness percentage for key fields
- Missing data counts
- Data quality recommendations
- Field-by-field breakdown table

## Usage

### Via Dashboard

1. Navigate to **📄 PDF Export** page in the dashboard
2. Review current inventory statistics
3. Select **Report Type** (Standard/Extended/Summary)
4. Configure **Page Size** (Letter/A4)
5. Adjust **Chart Quality** (DPI slider)
6. Toggle **Advanced Options** as needed
7. Click **🎯 Generate PDF Report**
8. Download the generated PDF

### Quick Presets

Use the **"📊 Extended Report"** button for instant configuration:
- Sets report type to Extended
- Uses recommended DPI (200)
- Enables detailed tables
- Shows 15 items per list

### Via Code

```python
from src.report_generator import VMwareInventoryReport

# Standard report
report = VMwareInventoryReport(
    db_url="sqlite:///vmware_inventory.db",
    include_charts=True,
    extended=False,
    chart_dpi=150
)
pdf_buffer = report.generate_report()
report.close()

# Extended report with high quality
report = VMwareInventoryReport(
    db_url="sqlite:///vmware_inventory.db",
    include_charts=True,
    extended=True,
    chart_dpi=200
)
pdf_buffer = report.generate_report()
report.close()

# Summary only (no charts)
report = VMwareInventoryReport(
    db_url="sqlite:///vmware_inventory.db",
    include_charts=False,
    extended=False
)
pdf_buffer = report.generate_report()
report.close()

# Save to file
with open('report.pdf', 'wb') as f:
    f.write(pdf_buffer.getvalue())
```

## Best Practices

### Choosing Report Type

**Use Standard when**:
- Regular weekly/monthly reporting
- Quick management updates
- Email distribution
- File size is a concern

**Use Extended when**:
- Executive presentations
- Quarterly business reviews
- Audit and compliance reports
- Comprehensive documentation
- Deep-dive analysis needed

**Use Summary when**:
- Data archival
- Text-focused analysis
- Minimal storage requirements
- Network bandwidth limitations

### Chart Quality Guidelines

| DPI | Use Case | File Size Impact |
|-----|----------|------------------|
| 100 | Screen viewing only | Minimal |
| 150 | General use (recommended) | Small |
| 200 | High-quality printing | Moderate |
| 300 | Professional printing | Significant |

### Performance Considerations

For large inventories (>5,000 VMs):

- Start with Standard report to estimate generation time
- Use lower DPI (100-150) for faster generation
- Consider Summary report for quick data export
- Schedule extended reports during off-hours

### File Management

Recommended naming convention:

```
vmware_inventory_{type}_{date}_{time}.pdf

Examples:
vmware_inventory_standard_20250127_1430.pdf
vmware_inventory_extended_20250127_QBR.pdf
vmware_inventory_summary_20250127_archive.pdf
```

Archive strategy:
- Keep last 3 standard reports
- Archive monthly extended reports
- Store quarterly reports permanently

## Troubleshooting

### Generation Fails

**Symptoms**: Error during PDF generation

**Solutions**:
1. Check database connection
2. Verify sufficient memory
3. Try Summary report first
4. Reduce DPI setting
5. Check Python dependencies (reportlab, matplotlib)

### Charts Not Displaying

**Symptoms**: PDF generated but charts are missing

**Solutions**:
1. Verify `include_charts=True`
2. Check matplotlib backend configuration
3. Ensure chart_dpi is within 100-300 range
4. Review error logs for matplotlib warnings

### Large File Size

**Symptoms**: PDF exceeds expected size

**Solutions**:
1. Reduce DPI from 300 to 150 or 200
2. Use Standard instead of Extended
3. Consider Summary report
4. Limit max_items to 10 or 15

### Slow Generation

**Symptoms**: Takes >60 seconds to generate

**Solutions**:
1. Reduce chart_dpi to 100 or 150
2. Use Standard report instead of Extended
3. Check database performance
4. Add database indexes: `python scripts/add_indexes.py`
5. Consider using PostgreSQL for large datasets

### Missing Data in Report

**Symptoms**: Some VMs or metrics not showing

**Solutions**:
1. Check `include_nulls` setting
2. Verify data loaded correctly: `vmware-inv stats`
3. Review Data Quality section in report
4. Reload inventory data
5. Check for database connectivity issues

## Examples

### Monthly Infrastructure Report

```python
# Standard report, optimized for email
report = VMwareInventoryReport(
    db_url="sqlite:///vmware_inventory.db",
    include_charts=True,
    extended=False,
    chart_dpi=150
)
pdf = report.generate_report()
report.close()

# Email friendly: ~100-150 KB
```

### Quarterly Executive Review

```python
# Extended report with high quality
report = VMwareInventoryReport(
    db_url="sqlite:///vmware_inventory.db",
    include_charts=True,
    extended=True,
    chart_dpi=200
)
pdf = report.generate_report()
report.close()

# Comprehensive: 20+ charts, ~300-400 KB
```

### Audit Archive

```python
# Summary only for compliance
report = VMwareInventoryReport(
    db_url="sqlite:///vmware_inventory.db",
    include_charts=False,
    extended=False
)
pdf = report.generate_report()
report.close()

# Minimal: Tables only, ~50-75 KB
```

## Chart Reference

### Standard Report Charts

1. Power State Distribution (Pie)
2. VMs per Datacenter (Horizontal Bar)
3. Cluster Resource Allocation (Grouped Bar)
4. vCPU Distribution (Bar)
5. Memory Distribution (Bar)
6. Storage Breakdown (Bar + Horizontal Bar)
7. Top Folders by VM Count (Horizontal Bar)

### Extended Report Additional Charts

8. CPU vs Memory Scatter (by Power State)
9. Top 10 Resource Configurations (Horizontal Bar)
10. Operating Systems (Bar + Pie)
11. Cluster Efficiency - VMs per Host (Bar)
12. Cluster Resource Bubble Chart (Scatter)
13. Environment Distribution (Pie)
14. Datacenter Comparison (Multiple Bars)
15. Datacenter Power State (Grouped Bar)
16. Datacenter Resource Comparison (Grouped Bar)
17. Cluster VM Distribution (Grouped Bar)
18. Cluster Resource Scatter (Bubble)
19. Folder Size Distribution (Histogram)
20. Folder Resource Allocation (Grouped Bar)
21. Average Resource Profile (Scatter)
22. Folder Provisioned Storage (Horizontal Bar)
23. Folder Storage Utilization (Grouped Bar)
24. Storage Efficiency (Scatter)
25. Avg Provisioned per VM (Horizontal Bar)

**Total in Extended Mode: 25+ visualizations**

## Related Documentation

- [Dashboard User Guide](dashboard.md) - Web interface overview
- [CLI Commands](cli-commands.md) - Command-line tools
- [Data Quality](data-quality.md) - Improving data completeness

## Support

For issues or feature requests:
- Open a GitHub issue
- Check existing documentation
- Review error logs in the dashboard
