"""Data anonymization service for VMware inventory.

This service provides consistent, reversible anonymization of sensitive data
for demos, documentation, and testing purposes.
"""

import hashlib
import re
import random
import string
from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class AnonymizationMapping:
    """Stores anonymization mappings for potential reversal."""
    
    vm_names: Dict[str, str] = field(default_factory=dict)
    vm_ids: Dict[str, str] = field(default_factory=dict)
    vm_uuids: Dict[str, str] = field(default_factory=dict)
    dns_names: Dict[str, str] = field(default_factory=dict)
    ip_addresses: Dict[str, str] = field(default_factory=dict)
    datacenters: Dict[str, str] = field(default_factory=dict)
    clusters: Dict[str, str] = field(default_factory=dict)
    hosts: Dict[str, str] = field(default_factory=dict)
    folders: Dict[str, str] = field(default_factory=dict)
    resource_pools: Dict[str, str] = field(default_factory=dict)
    vapps: Dict[str, str] = field(default_factory=dict)
    networks: Dict[str, str] = field(default_factory=dict)
    cluster_rule_names: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    paths: Dict[str, str] = field(default_factory=dict)
    sdk_server_types: Dict[str, str] = field(default_factory=dict)
    sdk_api_versions: Dict[str, str] = field(default_factory=dict)
    
    def save(self, filepath: Path) -> None:
        """Save mapping to JSON file for potential reversal."""
        data = {
            'vm_names': self.vm_names,
            'vm_ids': self.vm_ids,
            'vm_uuids': self.vm_uuids,
            'dns_names': self.dns_names,
            'ip_addresses': self.ip_addresses,
            'datacenters': self.datacenters,
            'clusters': self.clusters,
            'hosts': self.hosts,
            'folders': self.folders,
            'resource_pools': self.resource_pools,
            'vapps': self.vapps,
            'networks': self.networks,
            'cluster_rule_names': self.cluster_rule_names,
            'annotations': self.annotations,
            'paths': self.paths,
            'sdk_server_types': self.sdk_server_types,
            'sdk_api_versions': self.sdk_api_versions,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'AnonymizationMapping':
        """Load mapping from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


class AnonymizationService:
    """Service for anonymizing VMware inventory data."""
    
    def __init__(self, seed: str = "vmware-anon"):
        """Initialize anonymization service.
        
        Args:
            seed: Seed for consistent hash-based anonymization
        """
        self.seed = seed
        self.mapping = AnonymizationMapping()
        self._vm_counter = 0
        self._dc_counter = 0
        self._cluster_counter = 0
        self._host_counter = 0
        # Initialize random generator with seed for reproducibility
        self._random = random.Random(seed)
    
    def _hash_name(self, value: str, prefix: str = "") -> str:
        """Generate consistent hash-based name."""
        hash_obj = hashlib.md5(f"{self.seed}:{value}".encode())
        hash_hex = hash_obj.hexdigest()[:8]
        return f"{prefix}{hash_hex}" if prefix else hash_hex
    
    def _anonymize_vm_name(self, vm_name: str) -> str:
        """Anonymize VM name with pattern preservation.
        
        Examples:
            PROD-APP-01 -> PROD-VM-001
            DEV-WEB-SERVER -> DEV-VM-002
            db-server -> vm-003
        """
        if vm_name in self.mapping.vm_names:
            return self.mapping.vm_names[vm_name]
        
        self._vm_counter += 1
        
        # Try to preserve environment prefix (PROD, DEV, TEST, etc.)
        env_match = re.match(r'^(PROD|DEV|TEST|PREPROD|UAT|STAGING|QA)[-_]', vm_name, re.IGNORECASE)
        if env_match:
            env_prefix = env_match.group(1).upper()
            anon_name = f"{env_prefix}-VM-{self._vm_counter:03d}"
        else:
            anon_name = f"vm-{self._vm_counter:03d}"
        
        self.mapping.vm_names[vm_name] = anon_name
        return anon_name
    
    def _anonymize_dns_name(self, dns_name: str) -> str:
        """Anonymize DNS name."""
        if not dns_name or dns_name in self.mapping.dns_names:
            return self.mapping.dns_names.get(dns_name, dns_name)
        
        # Replace hostname but keep domain structure
        parts = dns_name.split('.')
        if len(parts) > 1:
            # Keep domain, anonymize hostname
            hostname = parts[0]
            domain = '.'.join(parts[1:])
            anon_hostname = self._hash_name(hostname, "host")
            anon_dns = f"{anon_hostname}.{domain}"
        else:
            anon_dns = self._hash_name(dns_name, "host")
        
        self.mapping.dns_names[dns_name] = anon_dns
        return anon_dns
    
    def _anonymize_ip_address(self, ip: str, keep_subnet: bool = True) -> str:
        """Anonymize IP address.
        
        Args:
            ip: Original IP address
            keep_subnet: If True, keep first 2 octets (e.g., 10.20.x.x)
        """
        if not ip or ip in self.mapping.ip_addresses:
            return self.mapping.ip_addresses.get(ip, ip)
        
        # IPv4 pattern
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            octets = ip.split('.')
            if keep_subnet:
                # Keep first 2 octets, anonymize last 2
                hash_suffix = self._hash_name(ip)[:4]
                third = int(hash_suffix[:2], 16) % 256
                fourth = int(hash_suffix[2:4], 16) % 256
                anon_ip = f"{octets[0]}.{octets[1]}.{third}.{fourth}"
            else:
                # Fully anonymize with 10.x.x.x range
                hash_val = self._hash_name(ip)[:6]
                second = int(hash_val[:2], 16) % 256
                third = int(hash_val[2:4], 16) % 256
                fourth = int(hash_val[4:6], 16) % 256
                anon_ip = f"10.{second}.{third}.{fourth}"
        else:
            anon_ip = ip  # Keep non-standard formats
        
        self.mapping.ip_addresses[ip] = anon_ip
        return anon_ip
    
    def _anonymize_datacenter(self, dc_name: str) -> str:
        """Anonymize datacenter name."""
        if not dc_name or dc_name in self.mapping.datacenters:
            return self.mapping.datacenters.get(dc_name, dc_name)
        
        self._dc_counter += 1
        anon_name = f"DC{self._dc_counter:02d}"
        self.mapping.datacenters[dc_name] = anon_name
        return anon_name
    
    def _anonymize_cluster(self, cluster_name: str) -> str:
        """Anonymize cluster name."""
        if not cluster_name or cluster_name in self.mapping.clusters:
            return self.mapping.clusters.get(cluster_name, cluster_name)
        
        self._cluster_counter += 1
        anon_name = f"Cluster{self._cluster_counter:02d}"
        self.mapping.clusters[cluster_name] = anon_name
        return anon_name
    
    def _anonymize_host(self, host_name: str) -> str:
        """Anonymize host name."""
        if not host_name or host_name in self.mapping.hosts:
            return self.mapping.hosts.get(host_name, host_name)
        
        self._host_counter += 1
        anon_name = f"esxi-host-{self._host_counter:02d}.local"
        self.mapping.hosts[host_name] = anon_name
        return anon_name
    
    def _anonymize_folder(self, folder_path: str) -> str:
        """Anonymize folder path."""
        if not folder_path or folder_path in self.mapping.folders:
            return self.mapping.folders.get(folder_path, folder_path)
        
        # Split path and anonymize each component
        parts = folder_path.split('/')
        anon_parts = []
        for part in parts:
            if part:
                anon_part = self._hash_name(part, "folder")[:8]
                anon_parts.append(anon_part)
            else:
                anon_parts.append('')
        
        anon_path = '/'.join(anon_parts)
        self.mapping.folders[folder_path] = anon_path
        return anon_path
    
    def _anonymize_network(self, network_name: str) -> str:
        """Anonymize network name."""
        if not network_name or network_name in self.mapping.networks:
            return self.mapping.networks.get(network_name, network_name)
        
        anon_name = f"Network-{self._hash_name(network_name)[:6]}"
        self.mapping.networks[network_name] = anon_name
        return anon_name
    
    def _anonymize_annotation(self, annotation: str, redact: bool = True) -> str:
        """Anonymize annotation text.
        
        Args:
            annotation: Original annotation
            redact: If True, fully redact. If False, just sanitize sensitive patterns
        """
        if not annotation:
            return annotation
        
        if redact:
            # Full redaction for sensitive annotations
            return "[REDACTED]"
        
        # Sanitize patterns: IPs, emails, hostnames
        anon = annotation
        
        # Replace IPs
        anon = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            lambda m: self._anonymize_ip_address(m.group(0)),
            anon
        )
        
        # Replace emails
        anon = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'user@example.com',
            anon
        )
        
        # Replace phone numbers
        anon = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'XXX-XXX-XXXX',
            anon
        )
        
        return anon
    
    def anonymize_vm_record(self, vm_data: dict, options: Optional[dict] = None) -> dict:
        """Anonymize a single VM record.
        
        Args:
            vm_data: Dictionary containing VM attributes
            options: Anonymization options:
                - keep_subnet: Keep IP subnet structure (default: True)
                - redact_annotations: Fully redact annotations (default: False)
                - preserve_env: Preserve environment prefixes (default: True)
                - anonymize_paths: Anonymize file paths (default: True)
                - selected_fields: Set of field names to anonymize (default: all)
        
        Returns:
            Anonymized VM record
        """
        options = options or {}
        keep_subnet = options.get('keep_subnet', True)
        redact_annotations = options.get('redact_annotations', False)
        anonymize_paths = options.get('anonymize_paths', True)
        selected_fields = options.get('selected_fields', None)  # None means all fields
        
        anon_data = vm_data.copy()
        
        # Helper to check if field should be anonymized
        def should_anonymize(field_name: str) -> bool:
            if selected_fields is None:
                return True  # Anonymize all by default
            return field_name in selected_fields
        
        # Anonymize VM name
        if 'vm' in anon_data and anon_data['vm'] and should_anonymize('vm'):
            anon_data['vm'] = self._anonymize_vm_name(anon_data['vm'])
        
        # Anonymize DNS name
        if 'dns_name' in anon_data and anon_data['dns_name'] and should_anonymize('dns_name'):
            anon_data['dns_name'] = self._anonymize_dns_name(anon_data['dns_name'])
        
        # Anonymize IP address
        if 'primary_ip_address' in anon_data and anon_data['primary_ip_address'] and should_anonymize('primary_ip_address'):
            anon_data['primary_ip_address'] = self._anonymize_ip_address(
                anon_data['primary_ip_address'], 
                keep_subnet=keep_subnet
            )
        
        # Anonymize infrastructure
        if 'datacenter' in anon_data and anon_data['datacenter'] and should_anonymize('datacenter'):
            anon_data['datacenter'] = self._anonymize_datacenter(anon_data['datacenter'])
        
        if 'cluster' in anon_data and anon_data['cluster'] and should_anonymize('cluster'):
            anon_data['cluster'] = self._anonymize_cluster(anon_data['cluster'])
        
        if 'host' in anon_data and anon_data['host'] and should_anonymize('host'):
            anon_data['host'] = self._anonymize_host(anon_data['host'])
        
        # Anonymize folder
        if 'folder' in anon_data and anon_data['folder'] and should_anonymize('folder'):
            anon_data['folder'] = self._anonymize_folder(anon_data['folder'])
        
        # Anonymize networks
        for i in range(1, 9):
            network_field = f'network_{i}'
            if network_field in anon_data and anon_data[network_field] and should_anonymize(network_field):
                anon_data[network_field] = self._anonymize_network(anon_data[network_field])
        
        # Anonymize annotation
        if 'annotation' in anon_data and anon_data['annotation'] and should_anonymize('annotation'):
            anon_data['annotation'] = self._anonymize_annotation(
                str(anon_data['annotation']),
                redact=redact_annotations
            )
        
        # Anonymize paths if requested
        if anonymize_paths:
            for path_field in ['path', 'log_directory', 'snapshot_directory', 'suspend_directory']:
                if path_field in anon_data and anon_data[path_field] and should_anonymize(path_field):
                    anon_data[path_field] = f"/vmfs/volumes/datastore/{self._hash_name(anon_data[path_field])[:16]}"
        
        # Anonymize custom fields with random values
        # code_ccx: Application/service code (e.g., APP-001)
        if 'code_ccx' in anon_data and anon_data['code_ccx'] and should_anonymize('code_ccx'):
            original = str(anon_data['code_ccx'])
            # Generate random alphanumeric code (e.g., APP-ABC-123)
            prefix = self._random.choice(['APP', 'SVC', 'PRD', 'SYS'])
            code = ''.join(self._random.choices(string.ascii_uppercase + string.digits, k=6))
            anon_data['code_ccx'] = f"{prefix}-{code[:3]}-{code[3:]}"
        
        # vm_nbu: Backup policy (e.g., POLICY-GOLD, POLICY-SILVER)
        if 'vm_nbu' in anon_data and anon_data['vm_nbu'] and should_anonymize('vm_nbu'):
            original = str(anon_data['vm_nbu'])
            policy_tier = self._random.choice(['GOLD', 'SILVER', 'BRONZE', 'STANDARD'])
            retention = self._random.choice(['7D', '14D', '30D', '90D'])
            anon_data['vm_nbu'] = f"POLICY-{policy_tier}-{retention}"
        
        # vm_orchid: Monitoring/management tag (e.g., MON-A1B2C3)
        if 'vm_orchid' in anon_data and anon_data['vm_orchid'] and should_anonymize('vm_orchid'):
            original = str(anon_data['vm_orchid'])
            tag = ''.join(self._random.choices(string.ascii_uppercase + string.digits, k=6))
            anon_data['vm_orchid'] = f"MON-{tag}"
        
        # Anonymize VM ID
        if 'vm_id' in anon_data and anon_data['vm_id'] and should_anonymize('vm_id'):
            original_id = str(anon_data['vm_id'])
            if original_id not in self.mapping.vm_ids:
                self.mapping.vm_ids[original_id] = self._hash_name(original_id, "vm-")
            anon_data['vm_id'] = self.mapping.vm_ids[original_id]
        
        # Anonymize VM UUID
        if 'vm_uuid' in anon_data and anon_data['vm_uuid'] and should_anonymize('vm_uuid'):
            if anon_data['vm_uuid'] not in self.mapping.vm_uuids:
                self.mapping.vm_uuids[anon_data['vm_uuid']] = self._hash_name(anon_data['vm_uuid'], "uuid-")
            anon_data['vm_uuid'] = self.mapping.vm_uuids[anon_data['vm_uuid']]
        
        # Anonymize resource pool
        if 'resource_pool' in anon_data and anon_data['resource_pool'] and should_anonymize('resource_pool'):
            if anon_data['resource_pool'] not in self.mapping.resource_pools:
                self.mapping.resource_pools[anon_data['resource_pool']] = f"ResourcePool-{self._hash_name(anon_data['resource_pool'])[:8]}"
            anon_data['resource_pool'] = self.mapping.resource_pools[anon_data['resource_pool']]
        
        # Anonymize vApp
        if 'vapp' in anon_data and anon_data['vapp'] and should_anonymize('vapp'):
            if anon_data['vapp'] not in self.mapping.vapps:
                self.mapping.vapps[anon_data['vapp']] = f"vApp-{self._hash_name(anon_data['vapp'])[:8]}"
            anon_data['vapp'] = self.mapping.vapps[anon_data['vapp']]
        
        # Anonymize cluster rules (full redaction)
        if 'cluster_rules' in anon_data and anon_data['cluster_rules'] and should_anonymize('cluster_rules'):
            anon_data['cluster_rules'] = "[REDACTED]"
        
        # Anonymize cluster rule names
        if 'cluster_rule_names' in anon_data and anon_data['cluster_rule_names'] and should_anonymize('cluster_rule_names'):
            # Split comma-separated names and anonymize each
            rule_names = [name.strip() for name in str(anon_data['cluster_rule_names']).split(',')]
            anon_rule_names = []
            for name in rule_names:
                if name:
                    if name not in self.mapping.cluster_rule_names:
                        self.mapping.cluster_rule_names[name] = f"Rule-{self._hash_name(name)[:6]}"
                    anon_rule_names.append(self.mapping.cluster_rule_names[name])
            anon_data['cluster_rule_names'] = ', '.join(anon_rule_names)
        
        # Anonymize additional custom fields
        # licence_enforcement: License type (e.g., ENT-001, STD-002)
        if 'licence_enforcement' in anon_data and anon_data['licence_enforcement'] and should_anonymize('licence_enforcement'):
            original = str(anon_data['licence_enforcement'])
            lic_type = self._random.choice(['ENT', 'STD', 'PRO', 'BAS'])
            lic_num = self._random.randint(100, 999)
            anon_data['licence_enforcement'] = f"{lic_type}-{lic_num}"
        
        # env: Environment (preserve common patterns: PROD, DEV, TEST, etc.)
        if 'env' in anon_data and anon_data['env'] and should_anonymize('env'):
            original = str(anon_data['env']).upper()
            # Try to preserve environment type if recognizable
            if any(env in original for env in ['PROD', 'PRD']):
                anon_data['env'] = 'PROD'
            elif any(env in original for env in ['DEV', 'DEVELOP']):
                anon_data['env'] = 'DEV'
            elif any(env in original for env in ['TEST', 'TST', 'QA']):
                anon_data['env'] = 'TEST'
            elif any(env in original for env in ['UAT', 'PREPROD', 'STAGING', 'STG']):
                anon_data['env'] = 'UAT'
            else:
                # Unknown pattern, assign random but realistic value
                anon_data['env'] = self._random.choice(['PROD', 'DEV', 'TEST', 'UAT'])
        
        # Anonymize vCenter SDK info
        if 'vi_sdk_server_type' in anon_data and anon_data['vi_sdk_server_type'] and should_anonymize('vi_sdk_server_type'):
            if anon_data['vi_sdk_server_type'] not in self.mapping.sdk_server_types:
                self.mapping.sdk_server_types[anon_data['vi_sdk_server_type']] = f"vCenter-{self._hash_name(anon_data['vi_sdk_server_type'])[:6]}"
            anon_data['vi_sdk_server_type'] = self.mapping.sdk_server_types[anon_data['vi_sdk_server_type']]
        
        if 'vi_sdk_api_version' in anon_data and anon_data['vi_sdk_api_version'] and should_anonymize('vi_sdk_api_version'):
            version_str = str(anon_data['vi_sdk_api_version'])
            if version_str not in self.mapping.sdk_api_versions:
                self.mapping.sdk_api_versions[version_str] = f"api-{self._hash_name(version_str)[:6]}"
            anon_data['vi_sdk_api_version'] = self.mapping.sdk_api_versions[version_str]
        
        return anon_data
