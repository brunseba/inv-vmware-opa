"""Tests for column mapping service."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import yaml
import json

from src.services.column_mapper import (
    ColumnMapper,
    ColumnMappingConfig,
    MappingResult,
)


class TestColumnMappingConfig:
    """Tests for ColumnMappingConfig class."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = ColumnMappingConfig()
        assert config.mappings == {}
        assert config.case_insensitive is True
        assert config.strip_whitespace is True
        assert config.description == ""
    
    def test_custom_config(self):
        """Test custom configuration."""
        mappings = {"VM Name": "vm", "IP Address": "primary_ip_address"}
        config = ColumnMappingConfig(
            mappings=mappings,
            case_insensitive=False,
            strip_whitespace=False,
            description="Test config"
        )
        assert config.mappings == mappings
        assert config.case_insensitive is False
        assert config.strip_whitespace is False
        assert config.description == "Test config"
    
    def test_load_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        yaml_content = """
description: Test YAML config
case_insensitive: true
strip_whitespace: true
mappings:
  "VM Name": "vm"
  "IP Address": "primary_ip_address"
  "Datacenter": "datacenter"
"""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(yaml_content)
        
        config = ColumnMappingConfig.from_file(yaml_file)
        assert config.description == "Test YAML config"
        assert config.case_insensitive is True
        assert config.strip_whitespace is True
        assert len(config.mappings) == 3
        assert config.mappings["VM Name"] == "vm"
        assert config.mappings["IP Address"] == "primary_ip_address"
        assert config.mappings["Datacenter"] == "datacenter"
    
    def test_load_from_json(self, tmp_path):
        """Test loading configuration from JSON file."""
        json_content = {
            "description": "Test JSON config",
            "case_insensitive": False,
            "strip_whitespace": True,
            "mappings": {
                "VM Name": "vm",
                "IP Address": "primary_ip_address"
            }
        }
        json_file = tmp_path / "config.json"
        with open(json_file, 'w') as f:
            json.dump(json_content, f)
        
        config = ColumnMappingConfig.from_file(json_file)
        assert config.description == "Test JSON config"
        assert config.case_insensitive is False
        assert config.strip_whitespace is True
        assert len(config.mappings) == 2
    
    def test_save_to_yaml(self, tmp_path):
        """Test saving configuration to YAML file."""
        config = ColumnMappingConfig(
            description="Test save",
            mappings={"VM": "vm", "IP": "primary_ip_address"},
            case_insensitive=True,
            strip_whitespace=False
        )
        
        yaml_file = tmp_path / "output.yaml"
        config.to_file(yaml_file)
        
        assert yaml_file.exists()
        
        # Load and verify
        loaded_config = ColumnMappingConfig.from_file(yaml_file)
        assert loaded_config.description == config.description
        assert loaded_config.mappings == config.mappings
        assert loaded_config.case_insensitive == config.case_insensitive
        assert loaded_config.strip_whitespace == config.strip_whitespace
    
    def test_save_to_json(self, tmp_path):
        """Test saving configuration to JSON file."""
        config = ColumnMappingConfig(
            description="Test save JSON",
            mappings={"VM": "vm"},
        )
        
        json_file = tmp_path / "output.json"
        config.to_file(json_file)
        
        assert json_file.exists()
        
        # Load and verify
        loaded_config = ColumnMappingConfig.from_file(json_file)
        assert loaded_config.description == config.description
        assert loaded_config.mappings == config.mappings
    
    def test_unsupported_format(self, tmp_path):
        """Test that unsupported file formats raise error."""
        config = ColumnMappingConfig()
        txt_file = tmp_path / "config.txt"
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            config.to_file(txt_file)


class TestColumnMapper:
    """Tests for ColumnMapper class."""
    
    def test_default_mapper(self):
        """Test mapper with default mappings only."""
        mapper = ColumnMapper()
        assert mapper.use_defaults is True
        assert len(mapper._mapping_dict) > 0
        
        # Check some default mappings
        assert mapper._mapping_dict.get("vm") == "vm"
        assert mapper._mapping_dict.get("vm name") == "vm"
        assert mapper._mapping_dict.get("primary ip address") == "primary_ip_address"
    
    def test_custom_mapper(self):
        """Test mapper with custom configuration."""
        custom_config = ColumnMappingConfig(
            mappings={"Server Name": "vm", "Server IP": "primary_ip_address"}
        )
        mapper = ColumnMapper(custom_config=custom_config)
        
        # Custom mappings should override defaults
        assert "server name" in mapper._mapping_dict
        assert mapper._mapping_dict["server name"] == "vm"
    
    def test_mapper_without_defaults(self):
        """Test mapper with only custom mappings."""
        custom_config = ColumnMappingConfig(
            mappings={"Custom VM": "vm"}
        )
        mapper = ColumnMapper(custom_config=custom_config, use_defaults=False)
        
        # Should only have custom mappings
        assert len(mapper._mapping_dict) == 1
        assert mapper._mapping_dict.get("custom vm") == "vm"
    
    def test_normalize_column_name_case_insensitive(self):
        """Test column name normalization with case insensitivity."""
        config = ColumnMappingConfig(case_insensitive=True, strip_whitespace=True)
        mapper = ColumnMapper(custom_config=config)
        
        assert mapper._normalize_column_name("VM Name") == "vm name"
        assert mapper._normalize_column_name("  VM Name  ") == "vm name"
        assert mapper._normalize_column_name("vm name") == "vm name"
    
    def test_normalize_column_name_case_sensitive(self):
        """Test column name normalization with case sensitivity."""
        config = ColumnMappingConfig(case_insensitive=False, strip_whitespace=True)
        mapper = ColumnMapper(custom_config=config)
        
        assert mapper._normalize_column_name("VM Name") == "VM Name"
        assert mapper._normalize_column_name("vm name") == "vm name"
    
    def test_normalize_column_name_preserve_whitespace(self):
        """Test column name normalization preserving whitespace."""
        config = ColumnMappingConfig(case_insensitive=True, strip_whitespace=False)
        mapper = ColumnMapper(custom_config=config)
        
        assert mapper._normalize_column_name("  VM Name  ") == "  vm name  "
    
    def test_map_columns_basic(self):
        """Test basic column mapping."""
        df = pd.DataFrame({
            "VM Name": ["vm1", "vm2"],
            "IP Address": ["10.0.0.1", "10.0.0.2"],
            "Owner": ["Alice", "Bob"]
        })
        
        mapper = ColumnMapper()
        mapped_df, result = mapper.map_columns(df)
        
        # Check that known columns were mapped
        assert "vm" in mapped_df.columns
        assert "primary_ip_address" in mapped_df.columns
        
        # Check mapping result
        assert "VM Name" in result.mapped
        assert result.mapped["VM Name"] == "vm"
        assert "IP Address" in result.mapped
        
        # Owner should be unmapped (not in defaults)
        assert "Owner" in result.unmapped_excel
    
    def test_map_columns_with_expected_fields(self):
        """Test column mapping with expected fields."""
        df = pd.DataFrame({
            "VM": ["vm1"],
            "Datacenter": ["DC01"]
        })
        
        expected_fields = {"vm", "datacenter", "cluster"}  # cluster is missing
        
        mapper = ColumnMapper()
        mapped_df, result = mapper.map_columns(df, expected_fields=expected_fields)
        
        assert "vm" in result.mapped.values()
        assert "datacenter" in result.mapped.values()
        assert "cluster" in result.missing_fields
    
    def test_map_columns_conflicts(self):
        """Test detection of mapping conflicts."""
        df = pd.DataFrame({
            "VM Name": ["vm1"],
            "Virtual Machine": ["vm2"]  # Both map to "vm"
        })
        
        mapper = ColumnMapper()
        mapped_df, result = mapper.map_columns(df)
        
        # Should detect conflict
        assert "vm" in result.conflicts
        assert len(result.conflicts["vm"]) == 2
        assert "VM Name" in result.conflicts["vm"]
        assert "Virtual Machine" in result.conflicts["vm"]
    
    def test_map_columns_case_insensitive(self):
        """Test case-insensitive column mapping."""
        df = pd.DataFrame({
            "vm name": ["vm1"],
            "VM NAME": ["vm2"],
            "Vm Name": ["vm3"]
        })
        
        custom_config = ColumnMappingConfig(
            mappings={"VM Name": "vm"},
            case_insensitive=True
        )
        mapper = ColumnMapper(custom_config=custom_config)
        mapped_df, result = mapper.map_columns(df)
        
        # With case-insensitive, all three normalized to same key, so first one wins
        # Pandas keeps first column when there are duplicate names after rename
        assert "vm" in mapped_df.columns
        # The first occurrence will be mapped, others will have same normalized key
        # But DataFrame will only keep first occurrence
    
    def test_map_columns_custom_mapping(self):
        """Test column mapping with custom configuration."""
        df = pd.DataFrame({
            "Server Name": ["server1"],
            "Server IP": ["192.168.1.1"],
            "Location": ["Building A"]
        })
        
        custom_config = ColumnMappingConfig(
            mappings={
                "Server Name": "vm",
                "Server IP": "primary_ip_address",
                "Location": "datacenter"
            }
        )
        mapper = ColumnMapper(custom_config=custom_config, use_defaults=False)
        mapped_df, result = mapper.map_columns(df)
        
        assert "vm" in mapped_df.columns
        assert "primary_ip_address" in mapped_df.columns
        assert "datacenter" in mapped_df.columns
        
        assert len(result.unmapped_excel) == 0
        assert len(result.mapped) == 3


class TestColumnMapperTemplateGeneration:
    """Tests for template generation functionality."""
    
    def test_generate_template_yaml(self, tmp_path):
        """Test generating YAML template from Excel file."""
        # Create test Excel file
        excel_file = tmp_path / "test.xlsx"
        df = pd.DataFrame({
            "VM Name": ["vm1", "vm2"],
            "IP Address": ["10.0.0.1", "10.0.0.2"],
            "Datacenter": ["DC01", "DC02"]
        })
        df.to_excel(excel_file, index=False)
        
        # Generate template
        template_file = tmp_path / "template.yaml"
        ColumnMapper.generate_template(
            excel_file=excel_file,
            output_file=template_file,
            include_samples=True
        )
        
        assert template_file.exists()
        
        # Load and verify
        config = ColumnMappingConfig.from_file(template_file)
        assert "VM Name" in config.mappings
        assert "IP Address" in config.mappings
        assert "Datacenter" in config.mappings
        
        # Check that default mappings were suggested
        assert config.mappings["VM Name"] == "vm"
        assert config.mappings["IP Address"] == "primary_ip_address"
        assert config.mappings["Datacenter"] == "datacenter"
    
    def test_generate_template_json(self, tmp_path):
        """Test generating JSON template."""
        excel_file = tmp_path / "test.xlsx"
        df = pd.DataFrame({"VM": ["vm1"]})
        df.to_excel(excel_file, index=False)
        
        template_file = tmp_path / "template.json"
        ColumnMapper.generate_template(
            excel_file=excel_file,
            output_file=template_file,
            include_samples=False
        )
        
        assert template_file.exists()
        
        config = ColumnMappingConfig.from_file(template_file)
        assert "VM" in config.mappings
    
    def test_generate_template_with_sheet_index(self, tmp_path):
        """Test generating template from specific sheet by index."""
        excel_file = tmp_path / "test.xlsx"
        
        # Create Excel with multiple sheets
        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame({"Sheet1Col": [1]}).to_excel(writer, sheet_name="Sheet1", index=False)
            pd.DataFrame({"Sheet2Col": [2]}).to_excel(writer, sheet_name="Sheet2", index=False)
        
        template_file = tmp_path / "template.yaml"
        ColumnMapper.generate_template(
            excel_file=excel_file,
            output_file=template_file,
            sheet=1,  # Sheet2
            include_samples=False
        )
        
        config = ColumnMappingConfig.from_file(template_file)
        assert "Sheet2Col" in config.mappings
        assert "Sheet1Col" not in config.mappings


class TestMappingResult:
    """Tests for MappingResult dataclass."""
    
    def test_empty_result(self):
        """Test empty mapping result."""
        result = MappingResult()
        assert result.mapped == {}
        assert result.unmapped_excel == []
        assert result.missing_fields == []
        assert result.conflicts == {}
    
    def test_result_with_data(self):
        """Test mapping result with data."""
        result = MappingResult(
            mapped={"VM Name": "vm", "IP": "primary_ip_address"},
            unmapped_excel=["Owner", "Comments"],
            missing_fields=["cluster", "host"],
            conflicts={"vm": ["VM Name", "Virtual Machine"]}
        )
        
        assert len(result.mapped) == 2
        assert len(result.unmapped_excel) == 2
        assert len(result.missing_fields) == 2
        assert "vm" in result.conflicts


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_end_to_end_mapping_workflow(self, tmp_path):
        """Test complete workflow: generate template, modify, apply."""
        # Create test Excel file with custom column names
        excel_file = tmp_path / "custom_export.xlsx"
        df = pd.DataFrame({
            "Server Name": ["server1", "server2"],
            "Server IP": ["10.0.0.1", "10.0.0.2"],
            "Data Center": ["DC01", "DC02"],
            "Notes": ["Important", "Test"]
        })
        df.to_excel(excel_file, index=False)
        
        # Step 1: Generate template
        template_file = tmp_path / "mapping.yaml"
        ColumnMapper.generate_template(
            excel_file=excel_file,
            output_file=template_file,
            include_samples=True
        )
        
        # Step 2: Load and verify template
        config = ColumnMappingConfig.from_file(template_file)
        assert "Server Name" in config.mappings
        
        # Step 3: Customize template (simulate user editing)
        config.mappings["Server Name"] = "vm"
        config.mappings["Server IP"] = "primary_ip_address"
        config.mappings["Data Center"] = "datacenter"
        config.mappings["Notes"] = ""  # Don't map this
        config.to_file(template_file)
        
        # Step 4: Apply mapping
        df_input = pd.read_excel(excel_file)
        custom_config = ColumnMappingConfig.from_file(template_file)
        mapper = ColumnMapper(custom_config=custom_config)
        mapped_df, result = mapper.map_columns(df_input)
        
        # Verify results
        assert "vm" in mapped_df.columns
        assert "primary_ip_address" in mapped_df.columns
        assert "datacenter" in mapped_df.columns
        # Notes was mapped to empty string, but default mapper also has 'notes' -> 'annotation'
        # So it gets mapped to 'annotation' by default mapping
        # If we don't want this, user should use use_defaults=False
        
        assert len(result.mapped) == 4  # All 4 columns got mapped (Notes -> annotation via defaults)
        assert result.mapped["Server Name"] == "vm"
        assert result.mapped["Notes"] == "annotation"  # Mapped by defaults
    
    def test_handling_empty_mappings(self, tmp_path):
        """Test that empty string mappings are ignored."""
        df = pd.DataFrame({
            "VM": ["vm1"],
            "Owner": ["Alice"]
        })
        
        custom_config = ColumnMappingConfig(
            mappings={
                "VM": "vm",
                "Owner": ""  # Empty - should not map
            }
        )
        mapper = ColumnMapper(custom_config=custom_config, use_defaults=False)
        mapped_df, result = mapper.map_columns(df)
        
        # VM should be mapped, Owner should stay as-is
        assert "vm" in mapped_df.columns
        assert "Owner" in mapped_df.columns
        assert "Owner" in result.unmapped_excel or "owner" in result.unmapped_excel
