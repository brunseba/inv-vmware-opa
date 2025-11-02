# Pages Quick Reference

## All Dashboard Pages (20 Total)

| # | Icon | Page Name | Category | Description |
|---|------|-----------|----------|-------------|
| 1 | 📊 | **Overview** | Main | Main dashboard with key metrics and visualizations |
| 2 | 🔬 | **Data Explorer** | Explore & Analyze | PyGWalker-based interactive data exploration |
| 3 | 🔬 | **Advanced Explorer** | Explore & Analyze | SQL query interface with PyGWalker visualization |
| 4 | 🖥️ | **VM Explorer** | Explore & Analyze | Detailed VM inspection and analysis |
| 5 | 🔎 | **VM Search** | Explore & Analyze | Advanced VM search and filtering |
| 6 | 📈 | **Analytics** | Explore & Analyze | Resource allocation and OS analysis |
| 7 | ⚖️ | **Comparison** | Explore & Analyze | Side-by-side datacenter/cluster comparisons |
| 8 | ✅ | **Data Quality** | Explore & Analyze | Field completeness and data quality analysis |
| 9 | 💻 | **Resources** | Infrastructure | Resource metrics and allocation |
| 10 | 🌐 | **Infrastructure** | Infrastructure | Infrastructure topology and details |
| 11 | 📁 | **Folder Analysis** | Infrastructure | Folder-level resource and storage analytics |
| 12 | 🏷️ | **Folder Labelling** | Infrastructure | Label management and assignment |
| 13 | 🎯 | **Migration Targets** | Migration | Define and manage migration targets |
| 14 | ⚙️ | **Strategy Configuration** | Migration | Configure migration strategies |
| 15 | 📋 | **Migration Planning** | Migration | Plan and schedule migrations |
| 16 | 🔄 | **Migration Scenarios** | Migration | Create and analyze migration scenarios |
| 17 | 📥 | **Data Import** | Management | Import data from Excel files |
| 18 | 💾 | **Database Backup** | Management | Backup and restore database |
| 19 | 📄 | **PDF Export** | Export & Help | Generate PDF reports |
| 20 | 📚 | **Documentation** | Export & Help | Built-in help and documentation |

## CLI Commands Summary

### Data Operations (3 commands)
```bash
load     # Import Excel data to database
stats    # Display inventory statistics
list     # List and filter VMs
```

### Label Operations (5 commands)
```bash
label list       # List all labels
label create     # Create new label
label assign     # Assign label to folder/VM
label remove     # Remove label assignment
label propagate  # Propagate folder labels to VMs
```

### Anonymization Operations (4 commands) - BETA
```bash
anonymize database              # Anonymize database
anonymize excel                 # Anonymize Excel file
anonymize show-mapping          # Display mapping details
[excel --generate-mapping-template]  # Generate template
```

## Access Points

| Access Method | URL/Command | Type |
|---------------|-------------|------|
| **Web Dashboard** | `http://localhost:8501` | Streamlit Web UI |
| **CLI** | `vmware-inv` or `cli` | Command Line |
| **Dashboard Script** | `vmware-dashboard` | Launch Script |
| **Report Generator** | `vmware-report` | PDF Export |
| **Screenshot Tool** | `vmware-screenshot` | Screenshot Utility |

## Internal Routes

Streamlit pages are accessed via session state, not URL routes:

```python
st.session_state.page = "Overview"
st.session_state.page = "VM Explorer"
st.session_state.page = "Data Quality"
# etc.
```

## Page Categories

| Category | Page Count | Pages |
|----------|------------|-------|
| **Main** | 1 | Overview |
| **Explore & Analyze** | 7 | Data Explorer, Advanced Explorer, VM Explorer, VM Search, Analytics, Comparison, Data Quality |
| **Infrastructure** | 4 | Resources, Infrastructure, Folder Analysis, Folder Labelling |
| **Migration** | 4 | Migration Targets, Strategy Configuration, Migration Planning, Migration Scenarios |
| **Management** | 2 | Data Import, Database Backup |
| **Export & Help** | 2 | PDF Export, Documentation |

## Common Workflows

### 1. Initial Setup
```
1. Launch Dashboard → Data Import
2. Import Excel file
3. Navigate to Overview
```

### 2. Data Analysis
```
1. Overview (quick stats)
2. VM Explorer (detailed inspection)
3. Analytics (trends and patterns)
4. Comparison (side-by-side analysis)
```

### 3. Infrastructure Review
```
1. Infrastructure (topology)
2. Resources (metrics)
3. Folder Analysis (organization)
4. Data Quality (completeness)
```

### 4. Migration Planning
```
1. Migration Targets (define targets)
2. Strategy Configuration (set strategies)
3. Migration Planning (create plan)
4. Migration Scenarios (analyze options)
```

### 5. Export & Share
```
1. Anonymize data (if needed)
2. PDF Export (generate report)
3. Database Backup (archive)
```

## Quick Navigation Tips

1. **Sidebar Navigation**: All pages accessible from left sidebar
2. **Collapsible Sections**: Categories can be collapsed to save space
3. **Quick Stats**: Bottom of sidebar shows key metrics
4. **Cache Controls**: Clear cache to refresh data
5. **Theme Toggle**: Switch between light/dark mode
6. **Help Page**: Built-in documentation available

## File Support

### Import Formats
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`
- Max Size: 200MB (configurable)

### Export Formats
- PDF: Reports with charts
- Excel: Anonymized data
- SQLite: Database backups
- JSON: Mapping files

## Database Support

- **SQLite** (default): Local file-based
- **PostgreSQL**: Network database
- **MySQL**: Network database
- **Connection**: Configure in sidebar

## Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| Core Dashboard | ✅ Stable | Production ready |
| VM Management | ✅ Stable | Full featured |
| Analytics | ✅ Stable | Comprehensive |
| Migration Tools | ✅ Stable | Fully functional |
| PDF Export | ✅ Stable | Multiple formats |
| **Anonymization** | ⚠️ BETA | Testing phase |
| **Column Mapping** | ⚠️ BETA | New in v0.7.0 |

## Version Info

- **Current Version**: v0.7.0
- **Total Pages**: 20
- **CLI Commands**: 12+
- **Supported Databases**: 3
- **Export Formats**: 4
