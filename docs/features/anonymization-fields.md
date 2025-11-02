# Field-by-Field Anonymization Guide

This document explains exactly how each field is anonymized in the VMware inventory data.

## Table of Contents
- [Identity & Naming](#identity--naming)
- [Network](#network)
- [Infrastructure](#infrastructure)
- [Storage Paths](#storage-paths)
- [Text/Notes](#textnotes)
- [Custom Fields](#custom-fields)
- [SDK/Server Info](#sdkserver-info)
- [Non-Anonymized Fields](#non-anonymized-fields)

---

## Identity & Naming

### `vm` (VM Name)
**Anonymization Logic:** Pattern-preserving sequential naming

**How it works:**
1. Detects environment prefix (PROD, DEV, TEST, UAT, QA, STAGING, PREPROD)
2. If prefix found: preserves it, replaces rest with sequential number
3. If no prefix: uses generic sequential naming

**Examples:**
```
PROD-WEB-SERVER-01  → PROD-VM-001
DEV-DATABASE-MAIN   → DEV-VM-002
test-app            → vm-003
UAT-CLUSTER-APP-05  → UAT-VM-004
myserver            → vm-005
```

**Code:**
```python
def _anonymize_vm_name(self, vm_name: str) -> str:
    env_match = re.match(r'^(PROD|DEV|TEST|PREPROD|UAT|STAGING|QA)[-_]', 
                         vm_name, re.IGNORECASE)
    if env_match:
        return f"{env_match.group(1).upper()}-VM-{counter:03d}"
    return f"vm-{counter:03d}"
```

---

### `dns_name` (DNS Name)
**Anonymization Logic:** Hash hostname, preserve domain structure

**How it works:**
1. Splits DNS name by dots
2. Hashes the hostname (first part)
3. Keeps the domain suffix unchanged

**Examples:**
```
webserver1.company.com     → host3f2a8b45.company.com
db-primary.prod.local      → host8b7e2f19.prod.local
app.example.org            → hostc4d9e1a2.example.org
standalone                 → hostf8b2c7d3
```

**Reasoning:** Preserves domain structure for network topology analysis while hiding actual server names.

**Code:**
```python
def _anonymize_dns_name(self, dns_name: str) -> str:
    parts = dns_name.split('.')
    if len(parts) > 1:
        hostname = parts[0]
        domain = '.'.join(parts[1:])
        anon_hostname = self._hash_name(hostname, "host")
        return f"{anon_hostname}.{domain}"
    return self._hash_name(dns_name, "host")
```

---

### `vm_id` (VM ID)
**Anonymization Logic:** Hash-based transformation

**How it works:**
1. Takes original VM ID
2. Generates consistent hash
3. Prefixes with "vm-"

**Examples:**
```
vm-1234         → vm-3f2a8b45
500             → vm-8b7e2f19
VirtualMachine  → vm-c4d9e1a2
```

**Note:** Uses same hashing function as other fields for consistency.

---

### `vm_uuid` (VM UUID)
**Anonymization Logic:** Hash-based UUID replacement

**How it works:**
1. Hashes the original UUID
2. Prefixes with "uuid-"
3. Maintains uniqueness via MD5

**Examples:**
```
42305ca4-3c8d-7f9a-1234-567890abcdef  → uuid-3f2a8b45c7d9e1f2
50123456-789a-bcde-f012-3456789abcde  → uuid-8b7e2f19a4c6d8e0
```

**Reasoning:** Preserves UUID uniqueness for relationship tracking while removing actual UUID values.

---

## Network

### `primary_ip_address` (Primary IP)
**Anonymization Logic:** Subnet-preserving or full anonymization

**Option 1: --keep-subnet (default)**
- Keeps first 2 octets
- Anonymizes last 2 octets using hash

**Option 2: --anonymize-subnet**
- Fully anonymizes to 10.x.x.x range
- All octets derived from hash

**Examples (--keep-subnet):**
```
192.168.10.50   → 192.168.142.73
10.20.30.40     → 10.20.89.156
172.16.5.100    → 172.16.203.45
```

**Examples (--anonymize-subnet):**
```
192.168.10.50   → 10.142.73.89
10.20.30.40     → 10.89.156.203
172.16.5.100    → 10.203.45.178
```

**Code:**
```python
def _anonymize_ip_address(self, ip: str, keep_subnet: bool = True) -> str:
    octets = ip.split('.')
    if keep_subnet:
        hash_suffix = self._hash_name(ip)[:4]
        third = int(hash_suffix[:2], 16) % 256
        fourth = int(hash_suffix[2:4], 16) % 256
        return f"{octets[0]}.{octets[1]}.{third}.{fourth}"
    else:
        hash_val = self._hash_name(ip)[:6]
        second = int(hash_val[:2], 16) % 256
        third = int(hash_val[2:4], 16) % 256
        fourth = int(hash_val[4:6], 16) % 256
        return f"10.{second}.{third}.{fourth}"
```

**Reasoning:** Subnet preservation helps maintain network topology visibility for analysis.

---

### `network_1` through `network_8` (Network Names)
**Anonymization Logic:** Hash-based network naming

**How it works:**
1. Takes original network name
2. Creates consistent hash (6 chars)
3. Prefixes with "Network-"

**Examples:**
```
VLAN-Production-100     → Network-3f2a8b
DMZ-External            → Network-8b7e2f
Internal-Management     → Network-c4d9e1
VM Network              → Network-f8b2c7
```

**Reasoning:** Removes internal network naming conventions while preserving network count and structure.

---

## Infrastructure

### `datacenter` (Datacenter)
**Anonymization Logic:** Sequential naming

**How it works:**
1. Assigns sequential numbers to datacenters
2. Uses format "DC##"
3. First seen = DC01, second = DC02, etc.

**Examples:**
```
NYC-Production-DC       → DC01
London-DataCenter-1     → DC02
APAC-Singapore-DC       → DC03
Paris-Backup            → DC04
```

**Reasoning:** Simple sequential naming is sufficient; relationships are preserved via consistency.

---

### `cluster` (Cluster)
**Anonymization Logic:** Sequential naming

**How it works:**
1. Assigns sequential numbers to clusters
2. Uses format "Cluster##"
3. Maintains per-datacenter relationships

**Examples:**
```
Production-Cluster-A    → Cluster01
Dev-Cluster-West        → Cluster02
Test-Environment-01     → Cluster03
DR-Cluster-Primary      → Cluster04
```

---

### `host` (ESXi Host)
**Anonymization Logic:** Sequential naming with .local domain

**How it works:**
1. Assigns sequential numbers to hosts
2. Uses format "esxi-host-##.local"
3. Maintains cluster membership

**Examples:**
```
esxi-prod-web-01.company.com      → esxi-host-01.local
esx-database-primary.prod.local   → esxi-host-02.local
host-123.datacenter.org           → esxi-host-03.local
```

**Reasoning:** Standard naming removes organizational patterns while keeping host count visible.

---

### `folder` (Folder Path)
**Anonymization Logic:** Per-component hashing

**How it works:**
1. Splits path by `/`
2. Hashes each folder component
3. Rebuilds path with hashed names

**Examples:**
```
/Production/WebServers/Frontend
  → /folder3f/folder2a/folder8b

/Dev/Applications/Database
  → /folder9c/folder5d/folder1e

/VM/Templates/Linux
  → /folder4f/folder7a/folder3c
```

**Reasoning:** Preserves folder hierarchy depth and structure for analysis.

---

### `resource_pool` (Resource Pool)
**Anonymization Logic:** Hash-based naming

**How it works:**
1. Hashes the resource pool name
2. Prefixes with "ResourcePool-"
3. Takes first 8 characters of hash

**Examples:**
```
Production-HighPriority     → ResourcePool-3f2a8b45
Development-Standard        → ResourcePool-8b7e2f19
Test-LowPriority           → ResourcePool-c4d9e1a2
```

---

### `vapp` (vApp)
**Anonymization Logic:** Hash-based naming

**How it works:**
1. Hashes the vApp name
2. Prefixes with "vApp-"
3. Takes first 8 characters of hash

**Examples:**
```
WebApplication-Stack        → vApp-3f2a8b45
Database-Cluster            → vApp-8b7e2f19
Monitoring-Suite            → vApp-c4d9e1a2
```

---

## Storage Paths

All storage path fields use the same logic:
- `path` (VM Path)
- `log_directory` (Log Directory)
- `snapshot_directory` (Snapshot Directory)
- `suspend_directory` (Suspend Directory)

**Anonymization Logic:** Hash-based datastore paths

**How it works:**
1. Hashes the entire path
2. Creates new path: `/vmfs/volumes/datastore/{hash16}`
3. Removes all folder structure information

**Examples:**
```
/vmfs/volumes/prod-datastore-01/vm123/vm123.vmx
  → /vmfs/volumes/datastore/3f2a8b45c7d9e1f2

[datastore-production] VMs/webserver/logs
  → /vmfs/volumes/datastore/8b7e2f19a4c6d8e0

/vmfs/volumes/backup-ssd/snapshots/db-01
  → /vmfs/volumes/datastore/c4d9e1a2f5b8d4c7
```

**Reasoning:** Completely removes datastore naming and structure while maintaining uniqueness.

---

## Text/Notes

### `annotation` (Annotation/Notes)
**Anonymization Logic:** Full redaction or pattern sanitization

**Option 1: --redact-annotations (secure)**
```
Contact: john.doe@company.com, IP: 192.168.1.100
  → [REDACTED]
```

**Option 2: --sanitize-annotations (default)**
Sanitizes specific patterns:
- **IP Addresses**: Anonymized using IP anonymization logic
- **Emails**: Replaced with `user@example.com`
- **Phone Numbers**: Replaced with `XXX-XXX-XXXX`

```
Server managed by john.doe@company.com
IP: 192.168.10.50, Tel: 555-123-4567
Deployed 2024-01-15
  
  → Server managed by user@example.com
     IP: 192.168.142.73, Tel: XXX-XXX-XXXX
     Deployed 2024-01-15
```

**Code:**
```python
def _anonymize_annotation(self, annotation: str, redact: bool = False):
    if redact:
        return "[REDACTED]"
    
    # Replace IPs
    anon = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                  lambda m: self._anonymize_ip_address(m.group(0)), anon)
    
    # Replace emails
    anon = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                  'user@example.com', anon)
    
    # Replace phone numbers
    anon = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                  'XXX-XXX-XXXX', anon)
    
    return anon
```

---

### `cluster_rules` (Cluster Rules)
**Anonymization Logic:** Full redaction

**How it works:**
- Complex rule text fully redacted
- Prevents exposure of VM relationships and policies

**Examples:**
```
AntiAffinity: VM1, VM2, VM3; Affinity: VM4, VM5
  → [REDACTED]
```

---

### `cluster_rule_names` (Cluster Rule Names)
**Anonymization Logic:** Hash-based naming

**How it works:**
1. Splits comma-separated rule names
2. Hashes each rule name
3. Prefixes with "Rule-"

**Examples:**
```
WebServerAntiAffinity, DatabaseAffinity
  → Rule-3f2a8b, Rule-8b7e2f
```

---

## Custom Fields

### `code_ccx` (Custom Field: Code CCX)
**Anonymization Logic:** Random Code Generation

**How it works:**
- Generates random application/service code
- Format: `PREFIX-ABC-123` (prefix + 3 chars + 3 digits)
- Prefixes: APP, SVC, PRD, SYS (randomly chosen)
- Uses seed for reproducibility

**Examples:**
```
CCX-PROD-12345  → APP-K7M-D3G
APP-DB-001      → SVC-R2P-8N1
```

---

### `vm_nbu` (Custom Field: VM NBU - Backup)
**Anonymization Logic:** Random Backup Policy Generation

**How it works:**
- Generates random backup policy name
- Format: `POLICY-{TIER}-{RETENTION}`
- Tiers: GOLD, SILVER, BRONZE, STANDARD
- Retention: 7D, 14D, 30D, 90D

**Examples:**
```
NBU-Policy-WebServers  → POLICY-GOLD-30D
BACKUP-DAILY-001       → POLICY-SILVER-14D
```

---

### `vm_orchid` (Custom Field: VM Orchid)
**Anonymization Logic:** Random Monitoring Tag Generation

**How it works:**
- Generates random monitoring/management tag
- Format: `MON-{6 alphanumeric characters}`

**Examples:**
```
ORCHID-PROD-WEB  → MON-A1B2C3
TRACKING-DB-01   → MON-X7Y9Z4
```

---

### `licence_enforcement` (Custom Field: License)
**Anonymization Logic:** Random License Code Generation

**How it works:**
- Generates random license identifier
- Format: `{TYPE}-{3 digits}`
- Types: ENT, STD, PRO, BAS

**Examples:**
```
ENTERPRISE-2024  → ENT-457
STANDARD-PLUS    → STD-892
```

---

### `env` (Custom Field: Environment)
**Anonymization Logic:** Environment Normalization

**How it works:**
- Detects common environment patterns
- Normalizes to: PROD, DEV, TEST, UAT
- Preserves environment semantics

**Examples:**
```
production       → PROD
PROD-CLUSTER     → PROD
development      → DEV
test-env         → TEST
staging          → UAT
QA-ENVIRONMENT   → TEST
```

---

## SDK/Server Info

### `vi_sdk_server_type` (vCenter Server Type)
**Anonymization Logic:** Hash-based naming

**How it works:**
1. Hashes the server type
2. Prefixes with "vCenter-"

**Examples:**
```
vpx            → vCenter-3f2a8b
embeddedEsx    → vCenter-8b7e2f
vcsa           → vCenter-c4d9e1
```

---

### `vi_sdk_api_version` (vCenter API Version)
**Anonymization Logic:** Hash-based version string

**How it works:**
1. Hashes the version string
2. Prefixes with "api-"

**Examples:**
```
7.0.3    → api-3f2a8b
8.0.1    → api-8b7e2f
6.7.0    → api-c4d9e1
```

**Reasoning:** Removes specific version information while maintaining uniqueness.

---

## Non-Anonymized Fields

These fields are **NOT** anonymized as they contain technical metrics, not sensitive data:

### Resource Metrics
- `cpus` - CPU count
- `memory` - Memory size
- `nics` - NIC count
- `disks` - Disk count
- `provisioned_mib` - Provisioned storage
- `in_use_mib` - Used storage
- `unshared_mib` - Unshared storage

### States & Status
- `powerstate` - poweredOn, poweredOff, suspended
- `template` - Is template boolean
- `connection_state` - connected, disconnected
- `guest_state` - running, not running
- `config_status` - green, yellow, red
- `heartbeat` - heartbeat status

### OS & Hardware
- `os_config` - Operating system type (Windows, Linux, etc.)
- `os_vmware_tools` - VMware Tools version/status
- `hw_version` - Hardware version (vmx-14, etc.)
- `firmware` - bios, efi

### Dates & Times
- `creation_date` - When VM was created
- `poweron` - Last power on time
- `suspend_time` - Last suspend time
- `nb_last_backup` - Last backup timestamp
- `imported_at` - Data import timestamp

### Configuration
- `boot_delay`, `boot_retry_delay` - Boot timings
- `boot_required`, `boot_retry_enabled`, `boot_bios_setup` - Boot config
- `latency_sensitivity` - Latency setting
- `enable_uuid` - UUID enabled boolean
- `cbt` - Changed Block Tracking
- `consolidation_needed` - Consolidation flag

### HA/FT Configuration
- `das_protection` - HA protection status
- `ha_restart_priority` - HA restart priority
- `ha_isolation_response` - HA isolation response
- `ha_vm_monitoring` - HA monitoring status
- `ft_state` - Fault Tolerance state
- `ft_latency`, `ft_bandwidth`, `ft_sec_latency` - FT metrics

### Display
- `num_monitors` - Monitor count
- `video_ram_kib` - Video RAM size

### Other
- `srm_placeholder` - SRM status
- `min_required_evc_mode_key` - EVC mode
- `change_version` - Change version number
- `hw_upgrade_status`, `hw_upgrade_policy`, `hw_target` - Upgrade settings

**Reasoning:** These are technical configurations and metrics that don't reveal organizational structure or sensitive information. They're essential for analysis and reporting.

---

## Consistency Guarantees

All anonymization methods use **deterministic processing** with a seed:

### Hash-Based Methods
```python
def _hash_name(self, value: str, prefix: str = "") -> str:
    hash_obj = hashlib.md5(f"{seed}:{value}".encode())
    hash_hex = hash_obj.hexdigest()[:8]
    return f"{prefix}{hash_hex}"
```

### Random Generation Methods
```python
# Initialize random generator with seed
self._random = random.Random(seed)

# Generate reproducible random values
prefix = self._random.choice(['APP', 'SVC', 'PRD', 'SYS'])
```

**This means:**
- Same input + same seed = **same output** (repeatable)
- Different inputs = **different outputs** (unique)
- Same datacenter always gets same anonymized name across all VMs
- Custom fields get same random values with same seed
- Relationships are preserved perfectly

---

## Summary Table

| Field Type | Method | Preserves | Example |
|------------|--------|-----------|---------|
| VM Names | Pattern + Sequential | Environment prefix | `PROD-WEB-01` → `PROD-VM-001` |
| DNS Names | Hash hostname, keep domain | Domain structure | `web1.corp.com` → `host3f2a.corp.com` |
| IP Addresses | Hash or subnet preserve | Network topology | `192.168.1.50` → `192.168.142.73` |
| Infrastructure | Sequential | Relationships | `NYC-DC` → `DC01` |
| Paths | Hash components | Hierarchy depth | `/Prod/Web` → `/folder3f/folder2a` |
| Networks | Hash | Network count | `VLAN-100` → `Network-3f2a8b` |
| Annotations | Redact or sanitize | Dates, non-PII | Email/IP removed |
| Custom Fields | Random generation | Format & semantics | `CCX-PROD-01` → `APP-K7M-D3G` |
| UUIDs/IDs | Hash | Uniqueness | → `uuid-3f2a8b45` |
| Metrics | **Not anonymized** | Everything | `4 CPUs` → `4 CPUs` |

