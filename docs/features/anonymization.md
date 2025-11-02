# Data Anonymization

The anonymization feature allows you to create sanitized versions of your VMware inventory data for demos, documentation, testing, and sharing purposes.

## Overview

**Key Benefits:**
- 🔐 **Protect sensitive data** - Remove PII and confidential information
- 🎯 **Consistent results** - Same seed produces same anonymization
- 🔄 **Reversible** - Optionally save mapping for potential reversal
- 📊 **Preserve structure** - Maintains relationships and patterns
- ⚡ **Flexible** - Anonymize database or Excel files directly

## What Gets Anonymized

### Names & Identifiers
- **VM Names**: `PROD-APP-01` → `PROD-VM-001` (preserves environment prefixes)
- **DNS Names**: `server1.company.com` → `host3f2a8b.company.com`
- **VM UUIDs**: Replaced with consistent hashes

### Network Information
- **IP Addresses**: `192.168.10.50` → `192.168.142.73` (optionally preserves subnet)
- **Network Names**: `VLAN-Production` → `Network-3f2a8b`

### Infrastructure
- **Datacenters**: `NYC-DataCenter-01` → `DC01`
- **Clusters**: `Production-Cluster-A` → `Cluster01`
- **Hosts**: `esxi-prod-01.company.com` → `esxi-host-01.local`
- **Folders**: `/Production/Applications/Web` → `/folder3f/folder2a/folder8b`

### Sensitive Text
- **Annotations**: Fully redacted or sanitized (emails, IPs, phone numbers removed)
- **File Paths**: `/vmfs/volumes/prod-datastore-01/vm/...` → `/vmfs/volumes/datastore/a3f2b8...`
- **Custom Fields**: Cleared (code_ccx, vm_nbu, vm_orchid)

## What's Preserved

✅ **Resource Metrics** - CPU, memory, storage values remain unchanged  
✅ **Relationships** - Datacenter → Cluster → Host → VM hierarchy maintained  
✅ **Power States** - poweredOn, poweredOff, suspended  
✅ **OS Types** - Operating system configurations  
✅ **Timestamps** - Creation dates, power-on times  
✅ **Hardware Configs** - Hardware version, firmware, boot settings  
✅ **Statistics** - All numeric metrics for analytics  

## Commands

### Anonymize Database

Create an anonymized copy of your entire database:

```bash
# Basic anonymization
uv run python -m src.cli anonymize database --output data/demo.db

# With mapping file (for potential reversal)
uv run python -m src.cli anonymize database \
  --output data/demo.db \
  --mapping-file data/mapping.json

# Full anonymization (don't preserve subnets)
uv run python -m src.cli anonymize database \
  --output data/demo.db \
  --anonymize-subnet

# Fully redact annotations
uv run python -m src.cli anonymize database \
  --output data/demo.db \
  --redact-annotations

# Custom seed for consistency
uv run python -m src.cli anonymize database \
  --output data/demo.db \
  --seed "my-custom-seed-2024"
```

### Anonymize Excel File

Anonymize Excel export directly without database import:

```bash
# Anonymize Excel file
uv run python -m src.cli anonymize excel \
  inputs/vmware-inv.xlsx \
  --output inputs/demo-data.xlsx

# With mapping file
uv run python -m src.cli anonymize excel \
  inputs/vmware-inv.xlsx \
  --output inputs/demo-data.xlsx \
  --mapping-file data/mapping.json
```

### View Mapping

Display anonymization mapping from saved file:

```bash
uv run python -m src.cli anonymize show-mapping data/mapping.json
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--keep-subnet` | `True` | Preserve first 2 octets of IP addresses |
| `--anonymize-subnet` | `False` | Fully anonymize IPs (10.x.x.x) |
| `--redact-annotations` | `False` | Fully redact all annotations |
| `--sanitize-annotations` | `True` | Sanitize sensitive patterns in annotations |
| `--preserve-env` | `True` | Keep PROD/DEV/TEST prefixes in VM names |
| `--seed` | `"vmware-anon"` | Seed for consistent anonymization |

## Use Cases

### 1. Demo Database

Create a sanitized database for product demonstrations:

```bash
# Create demo database
uv run python -m src.cli anonymize database --output data/demo.db

# Use demo database for dashboard
streamlit run src/dashboard/app.py -- --db-url sqlite:///data/demo.db
```

### 2. Documentation Screenshots

Anonymize before capturing screenshots:

```bash
# Anonymize data
uv run python -m src.cli anonymize database --output data/docs.db

# Generate screenshots with anonymized data
export DB_URL="sqlite:///data/docs.db"
vmware-screenshot auto --output docs/images/
```

### 3. Share with External Teams

Create anonymized dataset for external consultants or support:

```bash
uv run python -m src.cli anonymize database \
  --output data/external-share.db \
  --anonymize-subnet \
  --redact-annotations \
  --mapping-file data/mapping-DO-NOT-SHARE.json
```

### 4. Testing and Development

Generate consistent test data:

```bash
# Always produces same anonymization
uv run python -m src.cli anonymize database \
  --output data/test.db \
  --seed "test-seed-2024"
```

## Anonymization Patterns

### VM Name Patterns

| Original | Anonymized | Pattern |
|----------|------------|---------|
| `PROD-WEB-01` | `PROD-VM-001` | Environment preserved |
| `DEV-DB-SERVER` | `DEV-VM-002` | Environment preserved |
| `test-app` | `vm-003` | No prefix |
| `UAT-APP-CLUSTER-01` | `UAT-VM-004` | Environment preserved |

### IP Address Patterns

**With --keep-subnet (default):**
| Original | Anonymized | Notes |
|----------|------------|-------|
| `192.168.10.50` | `192.168.142.73` | Subnet preserved |
| `10.20.30.40` | `10.20.89.156` | First 2 octets kept |

**With --anonymize-subnet:**
| Original | Anonymized | Notes |
|----------|------------|-------|
| `192.168.10.50` | `10.142.73.89` | Fully anonymized |
| `10.20.30.40` | `10.89.156.203` | 10.x.x.x range |

### Infrastructure Naming

| Type | Original | Anonymized |
|------|----------|------------|
| Datacenter | `NYC-Production-DC` | `DC01` |
| Cluster | `Cluster-WebApps-A` | `Cluster01` |
| Host | `esxi-prod-web-01.corp.com` | `esxi-host-01.local` |
| Folder | `/Production/Web/Frontend` | `/folder3f/folder2a/folder8b` |

## Mapping File

The mapping file (JSON format) contains all anonymization transformations:

```json
{
  "vm_names": {
    "PROD-WEB-01": "PROD-VM-001",
    "DEV-DB-01": "DEV-VM-002"
  },
  "ip_addresses": {
    "192.168.10.50": "192.168.142.73",
    "10.20.30.40": "10.20.89.156"
  },
  "datacenters": {
    "NYC-Production": "DC01"
  },
  "clusters": {
    "Production-Cluster-A": "Cluster01"
  },
  "hosts": {
    "esxi-prod-01.company.com": "esxi-host-01.local"
  }
}
```

**⚠️ Security Note**: Keep mapping files secure! They can be used to reverse the anonymization.

## Best Practices

1. **Use Consistent Seeds** - Same seed = reproducible anonymization for testing
2. **Save Mapping Files Securely** - Store separately from anonymized data
3. **Test First** - Verify anonymized data works with your application
4. **Document Seed** - Record seed used for each anonymized dataset
5. **Review Output** - Spot-check anonymized data for any missed sensitive info
6. **Delete Mapping** - Remove mapping files after verification if not needed

## Limitations

- **UUID Uniqueness**: Anonymized UUIDs are hash-based but still unique
- **Statistics**: Numeric distributions unchanged (CPU, memory patterns visible)
- **Relationships**: Infrastructure topology remains identifiable
- **Timestamps**: Creation dates and patterns preserved
- **One-way by default**: Without mapping file, anonymization cannot be reversed

## Security Considerations

✅ **Safe to Share:**
- Anonymized database files
- Screenshots from anonymized data
- Analytics/reports from anonymized data

⚠️ **Keep Secure:**
- Original database
- Mapping files (JSON)
- Seed values (if you need consistent anonymization)

❌ **Never Share Together:**
- Anonymized database + mapping file = easily reversible!

## Example Workflow

```bash
# 1. Load production data
uv run python -m src.cli load inputs/vmware-inventory.xlsx --clear

# 2. Create anonymized copy
uv run python -m src.cli anonymize database \
  --output data/demo.db \
  --mapping-file data/mapping.json

# 3. Test dashboard with anonymized data
export DB_URL="sqlite:///data/demo.db"
streamlit run src/dashboard/app.py

# 4. Generate documentation screenshots
vmware-screenshot auto --output docs/images/

# 5. Securely store or delete mapping
mv data/mapping.json ~/secure-vault/vmware-mapping-2024.json
# OR
rm data/mapping.json  # if you don't need reversal
```

## See Also

- [Database Management](../database/README.md)
- [CLI Reference](../cli/README.md)
- [Screenshot Automation](../tools/screenshots.md)
