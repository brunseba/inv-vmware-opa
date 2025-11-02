"""Column mapping service for Excel file anonymization.

This service allows flexible mapping of Excel column names to internal data model fields.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class ColumnMappingConfig:
    """Configuration for column name mappings."""
    
    # Direct mappings: excel_column -> internal_field
    mappings: Dict[str, str] = field(default_factory=dict)
    
    # Case-insensitive matching
    case_insensitive: bool = True
    
    # Strip whitespace from column names
    strip_whitespace: bool = True
    
    # Description for documentation
    description: str = ""
    
    @classmethod
    def from_file(cls, filepath: Path) -> 'ColumnMappingConfig':
        """Load mapping configuration from YAML or JSON file.
        
        Args:
            filepath: Path to configuration file (.yaml, .yml, or .json)
            
        Returns:
            ColumnMappingConfig instance
            
        Example YAML format:
            description: "Custom VMware export mapping"
            case_insensitive: true
            strip_whitespace: true
            mappings:
              "Virtual Machine": "vm"
              "DNS Hostname": "dns_name"
              "IP Address": "primary_ip_address"
              "vCenter Datacenter": "datacenter"
        """
        with open(filepath, 'r') as f:
            if filepath.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif filepath.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {filepath.suffix}. Use .yaml, .yml, or .json")
        
        return cls(
            mappings=data.get('mappings', {}),
            case_insensitive=data.get('case_insensitive', True),
            strip_whitespace=data.get('strip_whitespace', True),
            description=data.get('description', ''),
        )
    
    def to_file(self, filepath: Path) -> None:
        """Save mapping configuration to file.
        
        Args:
            filepath: Path to save configuration (.yaml, .yml, or .json)
        """
        data = {
            'description': self.description,
            'case_insensitive': self.case_insensitive,
            'strip_whitespace': self.strip_whitespace,
            'mappings': self.mappings,
        }
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            if filepath.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif filepath.suffix == '.json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported file format: {filepath.suffix}")


@dataclass
class MappingResult:
    """Result of applying column mappings."""
    
    # Successfully mapped: excel_column -> internal_field
    mapped: Dict[str, str] = field(default_factory=dict)
    
    # Unmapped Excel columns
    unmapped_excel: List[str] = field(default_factory=list)
    
    # Expected fields not found in Excel
    missing_fields: List[str] = field(default_factory=list)
    
    # Columns mapped to the same internal field (potential conflict)
    conflicts: Dict[str, List[str]] = field(default_factory=dict)


class ColumnMapper:
    """Service for mapping Excel column names to internal field names."""
    
    # Default built-in mappings (backwards compatible)
    DEFAULT_MAPPINGS = {
        # VM/Name variations
        'vm': 'vm',
        'vm name': 'vm',
        'name': 'vm',
        'virtual machine': 'vm',
        'virtual machine name': 'vm',
        
        # DNS variations
        'dns_name': 'dns_name',
        'dns name': 'dns_name',
        'dns': 'dns_name',
        'hostname': 'dns_name',
        'host name': 'dns_name',
        
        # IP variations
        'primary_ip_address': 'primary_ip_address',
        'primary ip address': 'primary_ip_address',
        'ip address': 'primary_ip_address',
        'ip': 'primary_ip_address',
        'primary ip': 'primary_ip_address',
        
        # VM ID/UUID
        'vm_id': 'vm_id',
        'vm id': 'vm_id',
        'vm_uuid': 'vm_uuid',
        'vm uuid': 'vm_uuid',
        'uuid': 'vm_uuid',
        
        # Infrastructure
        'datacenter': 'datacenter',
        'data center': 'datacenter',
        'dc': 'datacenter',
        'cluster': 'cluster',
        'host': 'host',
        'esxi host': 'host',
        'esx host': 'host',
        'folder': 'folder',
        'resource_pool': 'resource_pool',
        'resource pool': 'resource_pool',
        'vapp': 'vapp',
        'v app': 'vapp',
        
        # Networks (1-8)
        'network_1': 'network_1',
        'network 1': 'network_1',
        'network_2': 'network_2',
        'network 2': 'network_2',
        'network_3': 'network_3',
        'network 3': 'network_3',
        'network_4': 'network_4',
        'network 4': 'network_4',
        'network_5': 'network_5',
        'network 5': 'network_5',
        'network_6': 'network_6',
        'network 6': 'network_6',
        'network_7': 'network_7',
        'network 7': 'network_7',
        'network_8': 'network_8',
        'network 8': 'network_8',
        
        # Paths
        'path': 'path',
        'vm path': 'path',
        'log_directory': 'log_directory',
        'log directory': 'log_directory',
        'snapshot_directory': 'snapshot_directory',
        'snapshot directory': 'snapshot_directory',
        'suspend_directory': 'suspend_directory',
        'suspend directory': 'suspend_directory',
        
        # Text/Notes
        'annotation': 'annotation',
        'annotations': 'annotation',
        'notes': 'annotation',
        'cluster_rules': 'cluster_rules',
        'cluster rules': 'cluster_rules',
        'cluster_rule_names': 'cluster_rule_names',
        'cluster rule names': 'cluster_rule_names',
        
        # Custom fields
        'code_ccx': 'code_ccx',
        'code ccx': 'code_ccx',
        'vm_nbu': 'vm_nbu',
        'vm nbu': 'vm_nbu',
        'vm_orchid': 'vm_orchid',
        'vm orchid': 'vm_orchid',
        'licence_enforcement': 'licence_enforcement',
        'licence enforcement': 'licence_enforcement',
        'license enforcement': 'licence_enforcement',
        'env': 'env',
        'environment': 'env',
        
        # SDK/Server
        'vi_sdk_server_type': 'vi_sdk_server_type',
        'vi sdk server type': 'vi_sdk_server_type',
        'sdk server type': 'vi_sdk_server_type',
        'vi_sdk_api_version': 'vi_sdk_api_version',
        'vi sdk api version': 'vi_sdk_api_version',
        'sdk api version': 'vi_sdk_api_version',
    }
    
    def __init__(
        self,
        custom_config: Optional[ColumnMappingConfig] = None,
        use_defaults: bool = True
    ):
        """Initialize column mapper.
        
        Args:
            custom_config: Optional custom mapping configuration
            use_defaults: If True, include default mappings (custom overrides defaults)
        """
        self.config = custom_config or ColumnMappingConfig()
        self.use_defaults = use_defaults
        
        # Build combined mapping dictionary
        self._mapping_dict = {}
        if use_defaults:
            self._mapping_dict.update(self.DEFAULT_MAPPINGS)
        
        # Custom mappings override defaults - normalize keys first
        if custom_config and custom_config.mappings:
            for key, value in custom_config.mappings.items():
                # Skip empty mappings
                if value:
                    normalized_key = self._normalize_column_name(key)
                    self._mapping_dict[normalized_key] = value
    
    def _normalize_column_name(self, column: str) -> str:
        """Normalize column name for matching.
        
        Args:
            column: Original column name
            
        Returns:
            Normalized column name
        """
        normalized = column
        
        if self.config.strip_whitespace:
            normalized = normalized.strip()
        
        if self.config.case_insensitive:
            normalized = normalized.lower()
        
        return normalized
    
    def map_columns(
        self,
        df: pd.DataFrame,
        expected_fields: Optional[Set[str]] = None
    ) -> Tuple[pd.DataFrame, MappingResult]:
        """Map DataFrame columns to internal field names.
        
        Args:
            df: DataFrame with original column names
            expected_fields: Optional set of expected internal field names
            
        Returns:
            Tuple of (mapped DataFrame, MappingResult)
        """
        result = MappingResult()
        
        # Store original column names for reference
        original_columns = {col: col for col in df.columns}
        
        # Normalize column names for matching
        normalized_to_original = {
            self._normalize_column_name(col): col
            for col in df.columns
        }
        
        # Build mapping: original_column -> internal_field
        column_rename_map = {}
        internal_to_excel = {}  # Track reverse mapping for conflict detection
        
        for norm_col, orig_col in normalized_to_original.items():
            # Check if we have a mapping for this normalized column
            if norm_col in self._mapping_dict:
                internal_field = self._mapping_dict[norm_col]
                column_rename_map[orig_col] = internal_field
                result.mapped[orig_col] = internal_field
                
                # Track for conflict detection
                if internal_field not in internal_to_excel:
                    internal_to_excel[internal_field] = []
                internal_to_excel[internal_field].append(orig_col)
            else:
                # No mapping found - keep original
                result.unmapped_excel.append(orig_col)
        
        # Detect conflicts (multiple Excel columns mapping to same internal field)
        for internal_field, excel_columns in internal_to_excel.items():
            if len(excel_columns) > 1:
                result.conflicts[internal_field] = excel_columns
        
        # Check for missing expected fields
        if expected_fields:
            mapped_fields = set(column_rename_map.values())
            result.missing_fields = sorted(expected_fields - mapped_fields)
        
        # Apply renaming
        df_mapped = df.rename(columns=column_rename_map)
        
        return df_mapped, result
    
    @staticmethod
    def generate_template(
        excel_file: Path,
        output_file: Path,
        sheet: str | int = 0,
        include_samples: bool = True
    ) -> None:
        """Generate a template mapping configuration file from an Excel file.
        
        Args:
            excel_file: Path to Excel file
            output_file: Path to save template configuration
            sheet: Sheet name or index
            include_samples: If True, include sample values as comments
        """
        # Read Excel to get column names
        df = pd.read_excel(excel_file, sheet_name=sheet, nrows=3 if include_samples else 0)
        
        # Build template mappings
        template_mappings = {}
        for col in df.columns:
            # Try to suggest a mapping based on column name
            normalized = col.lower().strip()
            suggested = ColumnMapper.DEFAULT_MAPPINGS.get(normalized, "")
            
            if include_samples and len(df) > 0:
                # Get sample values (non-null)
                samples = df[col].dropna().head(3).tolist()
                sample_str = ', '.join([str(s)[:50] for s in samples])
                comment = f"  # Sample values: {sample_str}" if samples else "  # (empty)"
            else:
                comment = ""
            
            # Add to mappings with suggestion or empty string
            template_mappings[col] = suggested
        
        # Create config
        config = ColumnMappingConfig(
            description=f"Column mappings for {excel_file.name}",
            mappings=template_mappings,
            case_insensitive=True,
            strip_whitespace=True,
        )
        
        # Save to file
        config.to_file(output_file)
        
        # If YAML, add helpful comments manually
        if output_file.suffix in ['.yaml', '.yml']:
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Add header comment
            header = f"""# Column Mapping Configuration for {excel_file.name}
#
# Instructions:
# 1. Review the Excel column names below (left side)
# 2. Map each to an internal field name (right side)
# 3. Leave empty ("") for columns you don't want to map
# 4. Available internal fields are listed at the bottom
#
# Format:
#   "Excel Column Name": "internal_field_name"
#

"""
            
            # Add available fields reference at the end
            footer = f"""

# === Available Internal Field Names ===
# Use these values on the right side of the mappings above.
#
# Identity & Naming:
#   vm, dns_name, vm_id, vm_uuid
#
# Network:
#   primary_ip_address, network_1 through network_8
#
# Infrastructure:
#   datacenter, cluster, host, folder, resource_pool, vapp
#
# Storage Paths:
#   path, log_directory, snapshot_directory, suspend_directory
#
# Text/Notes:
#   annotation, cluster_rules, cluster_rule_names
#
# Custom Fields:
#   code_ccx, vm_nbu, vm_orchid, licence_enforcement, env
#
# SDK/Server:
#   vi_sdk_server_type, vi_sdk_api_version
"""
            
            with open(output_file, 'w') as f:
                f.write(header + content + footer)
