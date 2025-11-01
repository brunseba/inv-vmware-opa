# PDF Export Feature

## Overview
The PDF Export feature generates comprehensive, professional PDF reports from your VMware inventory data. Perfect for sharing with stakeholders, archiving, and presentations.

## Installation

### Dependencies
The PDF export feature requires these packages (already installed):
```bash
uv add reportlab pillow matplotlib
```

## Features

### Report Sections

#### 1. **Title Page**
- Report title
- Generation timestamp
- Database information

#### 2. **Executive Summary**
- Total VMs (powered on/off)
- Total vCPUs and Memory
- Infrastructure counts (datacenters, clusters, hosts)
- Summary paragraph with key insights
- **Chart**: Power State Distribution (pie chart)

#### 3. **Infrastructure Overview**
- Top 10 Datacenters by VM count
- Top 10 Clusters with resource allocation
- Detailed tables with VM counts, vCPUs, and memory
- **Charts**: 
  - VMs per Datacenter (horizontal bar chart)
  - Top 10 Clusters by VM Count (horizontal bar chart)
  - vCPU Allocation by Cluster (horizontal bar chart)

#### 4. **Resource Analysis**
- vCPU allocation distribution
- Memory allocation by size ranges
- Percentage breakdowns
- Resource consumption patterns
- **Charts**:
  - vCPU Distribution (bar chart)
  - Memory Distribution by Range (bar chart)

#### 5. **Storage Analysis**
- Total provisioned storage
- Total in-use storage
- Storage efficiency metrics
- Thin provisioning savings
- **Charts**:
  - Storage Breakdown (bar chart: Provisioned, In Use, Unshared)
  - Storage Efficiency (horizontal bar comparison)

#### 6. **Folder Analysis**
- Top 15 folders by VM count
- Resource allocation per folder
- vCPU and memory distribution
- **Chart**: Top 12 Folders by VM Count (horizontal bar chart)

#### 7. **Data Quality Report**
- Field completeness metrics
- Missing data identification
- Data quality recommendations

## Usage

### From Dashboard

1. Navigate to **📊 Export** → **📄 PDF Report** in the sidebar
2. Review the report contents preview
3. Click **🎯 Generate PDF Report**
4. Wait for generation (typically 5-30 seconds)
5. Click **⬇️ Download PDF Report** to save

### Programmatically

```python
from src.report_generator import VMwareInventoryReport

# Initialize report generator
report = VMwareInventoryReport("sqlite:///data/vmware_inventory.db")

# Generate PDF
pdf_buffer = report.generate_report()

# Save to file
with open("report.pdf", "wb") as f:
    f.write(pdf_buffer.getvalue())

# Clean up
report.close()
```

## Report Format

### Specifications
- **Format**: PDF
- **Page Size**: Letter (8.5" × 11")
- **Layout**: Portrait
- **Margins**: 0.75 inch
- **Font**: Helvetica family
- **Colors**: Professional color scheme (blues, greens, oranges)

### Styling
- **Headers**: Blue (#1f77b4) for main headers, Green (#2e8b57) for section headers
- **Tables**: Alternating row colors (white/light grey)
- **Borders**: Clean grid lines for readability
- **Spacing**: Consistent padding and margins

### File Size
- Typically 100-400 KB depending on:
  - Number of VMs
  - Number of unique values (datacenters, clusters, folders)
  - Data completeness
  - Number of charts (8+ charts included)

## Use Cases

### 1. Management Presentations
- **Executive Summary** provides high-level overview
- Professional formatting suitable for board meetings
- Key metrics at-a-glance

### 2. Capacity Planning
- **Resource Analysis** shows current utilization
- Identify VMs with unusual resource allocations
- Storage analysis reveals thin provisioning opportunities

### 3. Audit & Compliance
- Archive reports for compliance purposes
- Track infrastructure changes over time
- Document current state for audits

### 4. Team Collaboration
- Share with team members without dashboard access
- Attach to emails or tickets
- Include in documentation

### 5. Vendor Communications
- Professional reports for VMware support
- Share with consultants for assessments
- Provide to managed service providers

## Best Practices

### Regular Generation
- **Weekly**: For active environments
- **Monthly**: For stable environments
- **On-Demand**: Before/after major changes

### Archival
```bash
# Organize reports by date
mkdir -p reports/2025/01
mv vmware_inventory_report_*.pdf reports/2025/01/
```

### Version Control
- Include reports in git (if appropriate)
- Or store in document management system
- Tag with environment name (prod, dev, test)

### Naming Convention
Auto-generated filenames include timestamp:
```
vmware_inventory_report_20250127_143052.pdf
                        YYYYMMDD_HHMMSS
```

## Customization

### Modify Report Contents

Edit `src/report_generator.py`:

```python
def generate_report(self) -> BytesIO:
    story = []
    
    # Add your custom sections
    story.extend(self._create_custom_section())
    
    # Build PDF
    doc.build(story)
    return buffer

def _create_custom_section(self) -> list:
    elements = []
    elements.append(Paragraph("Custom Section", self.heading_style))
    # Add custom content
    return elements
```

### Change Page Size

```python
from reportlab.lib.pagesizes import A4

doc = SimpleDocTemplate(buffer, pagesize=A4)  # Change to A4
```

### Modify Colors

```python
self.heading_style = ParagraphStyle(
    'CustomHeading',
    fontSize=16,
    textColor=colors.HexColor('#YOUR_COLOR'),  # Custom color
)
```

## Troubleshooting

### "No data found in database"
- Load data first: `vmware-inv load <excel_file>`
- Check database URL in configuration

### "Error generating report"
- Check database connectivity
- Ensure all required fields are present
- Check console for detailed error messages

### Report is too large
- Large inventories (>50,000 VMs) may generate larger PDFs
- Consider filtering data or generating separate reports per datacenter

### Missing fonts
reportlab uses standard PDF fonts, which should always be available

## Performance

### Generation Time
- **Small** (< 100 VMs): 2-3 seconds
- **Medium** (100-1,000 VMs): 3-8 seconds
- **Large** (1,000-10,000 VMs): 8-20 seconds
- **Very Large** (> 10,000 VMs): 20-45 seconds

*Note: Chart generation adds 1-2 seconds per chart (8+ charts total)*

### Optimization Tips
- Database queries are optimized with indexes
- Tables limited to top N items to keep report concise
- Charts are generated as PNG images at 150 DPI
- Matplotlib uses 'Agg' backend for server-side rendering

## API Reference

### VMwareInventoryReport Class

```python
class VMwareInventoryReport:
    """Generate comprehensive PDF reports for VMware inventory."""
    
    def __init__(self, db_url: str):
        """Initialize report generator.
        
        Args:
            db_url: SQLAlchemy database URL
        """
    
    def generate_report(self) -> BytesIO:
        """Generate complete PDF report.
        
        Returns:
            BytesIO: PDF file content
        """
    
    def close(self):
        """Close database session."""
```

## Examples

### Basic Usage

```python
from src.report_generator import VMwareInventoryReport

report = VMwareInventoryReport("sqlite:///data/vmware_inventory.db")
pdf = report.generate_report()

with open("report.pdf", "wb") as f:
    f.write(pdf.getvalue())

report.close()
```

### Multiple Reports

```python
datacenters = ["DC1", "DC2", "DC3"]

for dc in datacenters:
    report = VMwareInventoryReport(f"sqlite:///data/{dc}.db")
    pdf = report.generate_report()
    
    with open(f"report_{dc}.pdf", "wb") as f:
        f.write(pdf.getvalue())
    
    report.close()
```

### Email Report

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

report = VMwareInventoryReport("sqlite:///data/vmware_inventory.db")
pdf = report.generate_report()

# Create email
msg = MIMEMultipart()
msg['Subject'] = 'VMware Inventory Report'
msg['From'] = 'sender@example.com'
msg['To'] = 'recipient@example.com'

# Attach PDF
part = MIMEBase('application', 'pdf')
part.set_payload(pdf.getvalue())
encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment', filename='report.pdf')
msg.attach(part)

# Send email (configure SMTP server)
# smtp.send_message(msg)

report.close()
```

## Support

For issues or questions:
1. Check this documentation
2. Review error messages in the dashboard
3. Check logs for detailed information
4. Open an issue on the project repository
