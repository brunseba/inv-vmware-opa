# PDF Report Charts Guide

## Overview
The PDF report includes **8+ professional charts** that visualize your VMware inventory data. Each chart matches the visualizations from the web dashboard.

## Charts Included

### 1. Executive Summary Section

#### Power State Distribution (Pie Chart)
**Purpose**: Shows the ratio of powered on vs powered off VMs  
**Type**: Pie chart  
**Colors**: Green (powered on), Red (powered off)  
**Data**: Actual VM counts with percentages  

```
┌─────────────────────────────────┐
│  Power State Distribution       │
│                                 │
│     ╱─────╲  46.2%             │
│    │  ON   │ Powered On         │
│    │ 3,691 │                    │
│     ╲─────╱                     │
│                                 │
│     ╱─────╲  53.8%             │
│    │ OFF   │ Powered Off        │
│    │ 4,298 │                    │
│     ╲─────╱                     │
└─────────────────────────────────┘
```

---

### 2. Infrastructure Overview Section

#### VMs per Datacenter (Horizontal Bar Chart)
**Purpose**: Compare VM distribution across datacenters  
**Type**: Horizontal bar chart  
**Color**: Blue (#3498db)  
**Data**: Top 10 datacenters by VM count  

```
┌──────────────────────────────────────────┐
│  VMs per Datacenter                      │
│                                          │
│  DC-EAST    ████████████████ 4,521      │
│  DC-WEST    ████████████ 2,891          │
│  DC-NORTH   ████████ 577                │
│  DC-SOUTH   ███ 200                     │
└──────────────────────────────────────────┘
```

#### Top 10 Clusters by VM Count (Horizontal Bar Chart)
**Purpose**: Identify largest clusters  
**Type**: Horizontal bar chart  
**Color**: Purple (#9b59b6)  
**Data**: Cluster name and VM count  

#### vCPU Allocation by Cluster (Horizontal Bar Chart)
**Purpose**: Show total vCPUs per cluster  
**Type**: Horizontal bar chart  
**Color**: Orange (#e67e22)  
**Data**: Total vCPUs allocated to each cluster  

```
┌─────────────────────────────────────────────────────────────┐
│  Top 10 Clusters            │  vCPU Allocation by Cluster   │
│                             │                               │
│  PROD-CL01  ████████ 2,341  │  PROD-CL01  ████████ 9,364   │
│  PROD-CL02  ██████ 1,892    │  PROD-CL02  ██████ 7,568     │
│  DEV-CL01   ████ 891        │  DEV-CL01   ████ 3,564       │
│  TEST-CL01  ██ 445          │  TEST-CL01  ██ 1,780         │
└─────────────────────────────────────────────────────────────┘
```

---

### 3. Resource Analysis Section

#### vCPU Distribution (Bar Chart)
**Purpose**: Show how many VMs have each vCPU count  
**Type**: Vertical bar chart  
**Color**: Blue (#3498db)  
**Data**: Top 15 vCPU configurations  

```
┌──────────────────────────────────┐
│  vCPU Distribution               │
│                                  │
│   █                              │
│   █    █                         │
│   █    █    █                    │
│   █    █    █    █               │
│   █    █    █    █    █          │
│  ─┴────┴────┴────┴────┴─────    │
│   1    2    4    8   16  ...     │
│ vCPU Configuration               │
└──────────────────────────────────┘
```

#### Memory Distribution (Bar Chart)
**Purpose**: Show VM distribution across memory ranges  
**Type**: Vertical bar chart  
**Color**: Red (#e74c3c)  
**Data**: 6 memory ranges (< 2GB, 2-4GB, 4-8GB, 8-16GB, 16-32GB, > 32GB)  

```
┌──────────────────────────────────┐
│  Memory Distribution             │
│                                  │
│        █                         │
│        █    █                    │
│   █    █    █    █               │
│   █    █    █    █    █          │
│   █    █    █    █    █    █     │
│  ─┴────┴────┴────┴────┴────┴──  │
│  <2  2-4  4-8 8-16 16-32 >32    │
│          Memory (GB)             │
└──────────────────────────────────┘
```

---

### 4. Storage Analysis Section

#### Storage Breakdown (Bar Chart)
**Purpose**: Compare provisioned, in-use, and unshared storage  
**Type**: Vertical bar chart  
**Colors**: Blue (provisioned), Green (in use), Orange (unshared)  
**Data**: Total storage in GB for each category  

#### Storage Efficiency (Horizontal Bar Comparison)
**Purpose**: Visualize storage efficiency percentage  
**Type**: Horizontal bar chart  
**Colors**: Grey (provisioned), Green (actually used)  
**Data**: Total provisioned vs actual usage  

```
┌─────────────────────────────────────────────────────────────┐
│  Storage Breakdown          │  Storage Efficiency: 67.3%    │
│                             │                               │
│   █                         │  Provisioned  ████████ 45,892│
│   █      █                  │                               │
│   █      █      █           │  Used         █████ 30,876   │
│   █      █      █           │                               │
│  ─┴──────┴──────┴───        │                               │
│  Prov  In Use Unshd         │                               │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Folder Analysis Section

#### Top 12 Folders by VM Count (Horizontal Bar Chart)
**Purpose**: Identify folders with most VMs  
**Type**: Horizontal bar chart  
**Color**: Purple (#9b59b6)  
**Data**: Folder path (truncated to 25 chars) and VM count  

```
┌────────────────────────────────────────┐
│  Top 12 Folders by VM Count            │
│                                        │
│  vm/prod/web-servers   ████████ 1,234 │
│  vm/prod/app-servers   ███████ 987    │
│  vm/prod/db-servers    █████ 654      │
│  vm/dev/test           ████ 432       │
│  vm/uat/staging        ███ 321        │
│  ...                                   │
└────────────────────────────────────────┘
```

---

## Chart Specifications

### Technical Details
- **Format**: PNG images embedded in PDF
- **Resolution**: 150 DPI (high quality for printing)
- **Rendering**: Server-side using Matplotlib 'Agg' backend
- **Size**: Optimized for Letter (8.5" × 11") page layout
- **Colors**: Professional palette matching web dashboard

### Chart Dimensions
| Chart Type | Width | Height | Location |
|------------|-------|--------|----------|
| Pie Chart | 4.5" | 3" | Executive Summary |
| Datacenter Bar | 5" | 3" | Infrastructure |
| Cluster Charts | 6.5" | 3" | Infrastructure |
| vCPU Bar | 5.5" | 3" | Resource Analysis |
| Memory Bar | 5.5" | 3" | Resource Analysis |
| Storage Charts | 6.5" | 2.8" | Storage Analysis |
| Folder Bar | 6" | 3.5" | Folder Analysis |

### Color Palette
| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Blue | #3498db | Primary charts, datacenters, vCPU |
| Green | #2ecc71 | Powered on, in-use storage |
| Red | #e74c3c | Powered off, memory |
| Purple | #9b59b6 | Clusters, folders |
| Orange | #e67e22, #f39c12 | CPU allocation, unshared storage |
| Grey | #95a5a6 | Reference/comparison |

---

## Value Labels

All charts include **value labels** showing exact numbers:
- Bar charts: Labels at end of bars
- Pie charts: Percentages and values
- Font size: 7-8pt for readability

Example:
```
████████ 4,521
```
The number shows exact count, making data easy to reference.

---

## Page Layout

### Chart Placement Strategy
1. **One chart per concept** - Each chart tells a complete story
2. **Balanced pages** - Charts don't create empty space
3. **Context before charts** - Tables provide data context
4. **Charts supplement tables** - Visual and tabular data together

### Typical Page Structure
```
┌─────────────────────────────────┐
│ Section Header                  │
│ ─────────────────────────────── │
│                                 │
│ Summary Text/Paragraph          │
│                                 │
│ ┌───────────────────────────┐   │
│ │                           │   │
│ │     Data Table            │   │
│ │                           │   │
│ └───────────────────────────┘   │
│                                 │
│ ┌───────────────────────────┐   │
│ │                           │   │
│ │     Chart/Graph           │   │
│ │                           │   │
│ └───────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
```

---

## Best Practices

### Reading the Charts
1. **Start with titles** - Understand what each chart shows
2. **Check axes** - Note units (count, GB, percentage)
3. **Compare bars** - Identify outliers and patterns
4. **Read labels** - Get exact numbers when needed

### Sharing Reports
- Charts are print-friendly (150 DPI)
- Black & white printing: Still readable
- Digital viewing: Crisp and clear
- Presentations: Extract pages as needed

### Interpretation Tips
- **Long bars** = High values (more VMs, more resources)
- **Green colors** = Active/in-use
- **Red colors** = Inactive/unused
- **Compare heights** = Relative sizing

---

## Chart Generation Process

### How It Works
1. **Query data** from database
2. **Generate matplotlib figure** in memory
3. **Render to PNG** at 150 DPI
4. **Embed in PDF** using reportlab
5. **Close figure** to free memory

### Performance
- Each chart adds ~1-2 seconds to generation time
- 8+ charts = 8-16 seconds additional processing
- Charts are generated sequentially
- Memory efficient (figures closed after use)

---

## Customization

### Modify Chart Colors
Edit `src/report_generator.py`:
```python
colors_pie = ['#2ecc71', '#e74c3c']  # Change these hex codes
```

### Adjust Chart Sizes
```python
fig, ax = plt.subplots(figsize=(6, 4))  # Width, height in inches
```

### Change Chart Type
Replace matplotlib calls:
```python
# Bar chart
ax.bar(x, y, color='#3498db')

# Horizontal bar
ax.barh(y, x, color='#9b59b6')

# Pie chart
ax.pie(data, labels=labels, autopct='%1.1f%%')
```

### Add New Charts
Create new method:
```python
def _create_custom_chart(self):
    fig, ax = plt.subplots(figsize=(6, 4))
    # Your chart code here
    return self._create_chart(fig)
```

---

## Troubleshooting

### Charts Not Appearing
- Check matplotlib installation: `uv pip list | grep matplotlib`
- Verify 'Agg' backend: `matplotlib.use('Agg')`
- Check for exceptions in PDF generation

### Charts Look Blurry
- Increase DPI: `fig.savefig(..., dpi=200)`
- Adjust figure size: `figsize=(8, 5)`

### Memory Issues
- Charts are closed after rendering with `plt.close(fig)`
- Check memory if generating 100+ charts

---

## Examples

### Simple Usage
```python
from src.report_generator import VMwareInventoryReport

report = VMwareInventoryReport("sqlite:///data/vmware_inventory.db")
pdf = report.generate_report()  # Includes all charts automatically

with open("report.pdf", "wb") as f:
    f.write(pdf.getvalue())

report.close()
```

### Chart-Only Test
```python
# Test individual chart generation
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(['A', 'B', 'C'], [10, 20, 15], color='#3498db')
ax.set_title('Test Chart')
plt.savefig('test_chart.png', dpi=150, bbox_inches='tight')
plt.close(fig)
```

---

## Summary

✅ **8+ professional charts** included  
✅ **High quality** (150 DPI PNG)  
✅ **Consistent styling** with dashboard  
✅ **Value labels** on all charts  
✅ **Print-friendly** for presentations  
✅ **Optimized** for Letter size pages  

The charts transform your inventory data into clear visual insights that are easy to understand and share with stakeholders.
