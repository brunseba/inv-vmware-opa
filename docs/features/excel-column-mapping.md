# Excel Column Mapping for Anonymization

> ⚠️ **BETA Feature**: The anonymization and column mapping features are currently in beta. Please test thoroughly and validate results before using in production environments.

The anonymization tool supports flexible column mapping to handle Excel files with custom or non-standard column names.

## Overview

When anonymizing Excel files, the tool needs to identify which columns contain sensitive data (VM names, IP addresses, infrastructure details, etc.). By default, it recognizes common column naming patterns, but you can provide custom mappings for files with unique column names.

## Quick Start

### 1. Generate a Mapping Template

First, generate a template configuration file from your Excel file:

```bash
cli anonymize excel your-file.xlsx --generate-mapping-template mapping.yaml
```

This creates a `mapping.yaml` file with:
- All column names from your Excel file
- Suggested mappings based on column names
- Sample data for each column (as comments in YAML)
- Complete list of available internal field names

### 2. Edit the Mapping Configuration

Open `mapping.yaml` and review the mappings:

```yaml
description: Column mappings for your-file.xlsx
case_insensitive: true
strip_whitespace: true
mappings:
  # Map your Excel columns to internal field names
  "Virtual Machine Name": "vm"
  "DNS Hostname": "dns_name"
  "IP Address": "primary_ip_address"
  "Data Center": "datacenter"
  "ESXi Cluster": "cluster"
  # Leave empty for columns you don't want to map
  "Comments": ""
  "Owner": ""
```

**Key points:**
- **Left side**: Exact column name from your Excel file
- **Right side**: Internal field name (see reference below)
- **Empty string** (`""`): Columns you don't want to map
- `case_insensitive: true`: Makes matching case-insensitive
- `strip_whitespace: true`: Ignores leading/trailing spaces

### 3. Run Anonymization with Custom Mapping

Use the custom mapping configuration:

```bash
cli anonymize excel your-file.xlsx -o anonymized.xlsx --mapping-config mapping.yaml
```

The tool will:
- Load your custom mappings
- Show which columns were mapped
- Warn about any conflicts or unmapped columns
- Anonymize only the mapped fields

## Available Internal Field Names

### Identity & Naming
- `vm` - Virtual machine name
- `dns_name` - DNS hostname
- `vm_id` - VM identifier
- `vm_uuid` - VM UUID

### Network
- `primary_ip_address` - Primary IP address
- `network_1` through `network_8` - Network names (up to 8)

### Infrastructure
- `datacenter` - Datacenter name
- `cluster` - Cluster name
- `host` - ESXi host name
- `folder` - Folder path
- `resource_pool` - Resource pool name
- `vapp` - vApp name

### Storage Paths
- `path` - VM path
- `log_directory` - Log directory path
- `snapshot_directory` - Snapshot directory path
- `suspend_directory` - Suspend directory path

### Text/Notes
- `annotation` - VM annotations/notes
- `cluster_rules` - Cluster rules
- `cluster_rule_names` - Cluster rule names

### Custom Fields
- `code_ccx` - Custom field: Code CCX
- `vm_nbu` - Custom field: VM NBU (Backup)
- `vm_orchid` - Custom field: VM Orchid
- `licence_enforcement` - Custom field: License enforcement
- `env` - Custom field: Environment

### SDK/Server Info
- `vi_sdk_server_type` - vCenter server type
- `vi_sdk_api_version` - vCenter API version

## Configuration File Formats

### YAML Format (Recommended)

```yaml
description: "Custom VMware export mapping"
case_insensitive: true
strip_whitespace: true
mappings:
  "Virtual Machine": "vm"
  "DNS Hostname": "dns_name"
  "IP Address": "primary_ip_address"
```

**Advantages:**
- Human-readable
- Supports comments
- Auto-generated templates include helpful comments

### JSON Format

```json
{
  "description": "Custom VMware export mapping",
  "case_insensitive": true,
  "strip_whitespace": true,
  "mappings": {
    "Virtual Machine": "vm",
    "DNS Hostname": "dns_name",
    "IP Address": "primary_ip_address"
  }
}
```

## Advanced Usage

### Mapping Multiple Sheets

If your Excel file has multiple sheets, specify the sheet when generating the template:

```bash
# List available sheets
cli anonymize excel your-file.xlsx --list-sheets

# Generate template for specific sheet
cli anonymize excel your-file.xlsx --sheet "VM Inventory" -t mapping.yaml

# Anonymize with custom mapping
cli anonymize excel your-file.xlsx --sheet "VM Inventory" -c mapping.yaml -o output.xlsx
```

### Handling Conflicts

If multiple Excel columns map to the same internal field:

```yaml
mappings:
  "VM Name": "vm"
  "Virtual Machine": "vm"  # Conflict!
```

The tool will:
- Warn you about the conflict
- Use the first occurrence
- Continue with anonymization

**Resolution:** Edit your mapping to keep only one column per internal field.

### Case Sensitivity

Control case-sensitive matching:

```yaml
case_insensitive: false  # Exact case match required
mappings:
  "VM": "vm"
  "vm": "dns_name"  # Different because case-sensitive
```

### Whitespace Handling

Control whitespace stripping:

```yaml
strip_whitespace: false  # Preserve leading/trailing spaces
mappings:
  " VM Name ": "vm"  # Exact match including spaces
```

## CLI Options Reference

### Generate Template

```bash
cli anonymize excel EXCEL_FILE --generate-mapping-template OUTPUT_FILE
```

Options:
- `-t, --generate-mapping-template PATH` - Generate template and exit
- `--sheet NAME/INDEX` - Sheet to analyze (default: "Sheet1")

### Use Custom Mapping

```bash
cli anonymize excel EXCEL_FILE -o OUTPUT --mapping-config CONFIG_FILE
```

Options:
- `-c, --mapping-config PATH` - Custom mapping configuration (.yaml/.yml/.json)
- `-o, --output PATH` - Output Excel file (required)
- `--sheet NAME/INDEX` - Sheet to anonymize
- `-f, --fields FIELD` - Specific fields to anonymize (repeatable)

### Inspect Excel File

```bash
# List all sheets
cli anonymize excel your-file.xlsx --list-sheets

# Show all columns with sample data
cli anonymize excel your-file.xlsx --list-columns

# Show which fields will be anonymized
cli anonymize excel your-file.xlsx --show-fields
```

## Examples

### Example 1: RVTools Export

RVTools exports often have column names like "VM", "DNS Name", "Datacenter", etc.

```bash
# Generate template
cli anonymize excel rvtools-export.xlsx -t rvtools-mapping.yaml

# Edit rvtools-mapping.yaml:
# mappings:
#   "VM": "vm"
#   "DNS Name": "dns_name"
#   "Datacenter": "datacenter"
#   "Cluster": "cluster"
#   "Host": "host"

# Anonymize
cli anonymize excel rvtools-export.xlsx -c rvtools-mapping.yaml -o anonymized.xlsx
```

### Example 2: Custom Export with Unusual Names

Your organization might have custom column names:

```bash
# Generate template
cli anonymize excel custom-export.xlsx -t custom-mapping.yaml

# Edit custom-mapping.yaml:
# mappings:
#   "Server Name": "vm"
#   "FQDN": "dns_name"
#   "IP Addr": "primary_ip_address"
#   "DC Location": "datacenter"
#   "Compute Cluster": "cluster"

# Anonymize
cli anonymize excel custom-export.xlsx -c custom-mapping.yaml -o anonymized.xlsx
```

### Example 3: Selective Anonymization

Only anonymize specific fields:

```bash
# Generate template (to understand structure)
cli anonymize excel data.xlsx -t mapping.yaml

# Anonymize only VM names and IPs
cli anonymize excel data.xlsx -c mapping.yaml -o output.xlsx -f vm -f primary_ip_address
```

### Example 4: Multiple Network Columns

Handle files with multiple network interfaces:

```yaml
mappings:
  "Network 1": "network_1"
  "Network 2": "network_2"
  "VLAN 1": "network_3"
  "VLAN 2": "network_4"
```

## Default Behavior

Without a custom mapping configuration, the tool uses **built-in default mappings** that recognize common column name variations:

- Case-insensitive matching
- Common patterns like "VM Name", "Virtual Machine", "Name" → `vm`
- Variations like "IP Address", "Primary IP", "IP" → `primary_ip_address`

This works well for standard exports from tools like:
- VMware vSphere PowerCLI
- RVTools (most columns)
- VMware vCenter exports

## Troubleshooting

### No Columns Mapped

**Problem:** "No matching fields found to anonymize!"

**Solution:**
1. Run `--list-columns` to see actual column names
2. Generate a template with `-t`
3. Edit the template to add correct mappings
4. Run anonymization with `-c`

### Conflicts Detected

**Problem:** Multiple columns map to the same internal field

**Solution:**
Edit your mapping file and keep only one column per internal field, or rename one column in Excel before processing.

### Missing Dependencies

**Problem:** `ModuleNotFoundError: No module named 'yaml'`

**Solution:**
```bash
uv pip install pyyaml
```

## Best Practices

1. **Always generate a template first** - Understand your data structure
2. **Review sample data** - Template shows sample values to help identify columns
3. **Use YAML format** - More readable with comments
4. **Version control mappings** - Reuse for similar files
5. **Test with small dataset** - Use `--sheet` with a small sheet first
6. **Combine with --fields** - Map all columns, then selectively anonymize

## Related Commands

- [`anonymize database`](../cli/anonymize.md#database) - Anonymize SQLite database
- [`anonymize show-mapping`](../cli/anonymize.md#show-mapping) - Display anonymization mapping

## See Also

- [Anonymization Fields Reference](anonymization-fields.md)
- [CLI Reference](../cli/anonymize.md)
