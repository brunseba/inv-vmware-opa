# Column Mapping Feature - Implementation Summary

> ⚠️ **BETA Feature**: This feature is currently in beta status.

## Overview

Added flexible Excel column mapping capabilities to the anonymization system, allowing users to customize how Excel columns are mapped to internal data model fields for anonymization.

## What's New

### 1. Column Mapping Service (`src/services/column_mapper.py`)

A new service that handles:
- **Loading** custom column mappings from YAML/JSON configuration files
- **Normalizing** column names (case-insensitive, whitespace handling)
- **Mapping** DataFrame columns to internal field names
- **Detecting** conflicts (multiple columns mapping to same field)
- **Generating** template mapping configurations from Excel files

### 2. Enhanced CLI Commands

#### Generate Mapping Template
```bash
cli anonymize excel data.xlsx --generate-mapping-template mapping.yaml
```
- Analyzes Excel file structure
- Suggests mappings based on column names
- Includes sample data for context
- Creates ready-to-edit YAML or JSON configuration

#### Use Custom Mapping
```bash
cli anonymize excel data.xlsx -o output.xlsx --mapping-config mapping.yaml
```
- Applies custom column mappings
- Shows which columns were mapped/unmapped
- Warns about conflicts
- Combines with existing CLI options (`--fields`, `--sheet`, etc.)

### 3. Configuration File Support

**YAML Format** (recommended):
```yaml
description: "Custom VMware export mapping"
case_insensitive: true
strip_whitespace: true
mappings:
  "Virtual Machine Name": "vm"
  "IP Address": "primary_ip_address"
  "Data Center": "datacenter"
```

**JSON Format**:
```json
{
  "description": "Custom mapping",
  "mappings": {
    "Virtual Machine Name": "vm"
  }
}
```

### 4. Comprehensive Documentation

- **User Guide**: `docs/features/excel-column-mapping.md`
  - Quick start guide
  - Configuration file formats
  - CLI options reference
  - Examples and use cases
  - Troubleshooting

### 5. Unit Tests

- 25 comprehensive tests covering:
  - Configuration loading/saving (YAML/JSON)
  - Column normalization (case sensitivity, whitespace)
  - Mapping application
  - Conflict detection
  - Template generation
  - End-to-end workflows

## Benefits

### For Users

1. **Flexible Data Import**: Handle Excel files with any column naming convention
2. **No Manual Preprocessing**: No need to rename columns in Excel before anonymizing
3. **Reusable Configurations**: Save and reuse mappings for similar files
4. **Better Visibility**: Clear feedback on what was mapped and what wasn't
5. **Safer Operations**: Conflict detection prevents unexpected results

### For the System

1. **Backwards Compatible**: Default mappings still work for standard exports
2. **Extensible**: Easy to add new field types
3. **Well-Tested**: Comprehensive test coverage
4. **Maintainable**: Clean separation of concerns

## Use Cases

### 1. RVTools Exports
Standard RVTools column names map automatically with defaults, but custom mappings handle variations.

### 2. Custom Organization Exports
Organizations with custom export formats can create mapping files once and reuse them.

### 3. Multiple Data Sources
Different source systems (vCenter, PowerCLI, third-party tools) can each have their own mapping configuration.

### 4. Multilingual Exports
Handle exports with column names in different languages.

## Technical Details

### Architecture

```
┌─────────────────────────────────────────┐
│  CLI Command (anonymize excel)          │
│  src/commands/anonymize.py              │
└────────────────┬────────────────────────┘
                 │
                 ├─ Generate Template
                 │  └─> ColumnMapper.generate_template()
                 │
                 └─ Anonymize with Mapping
                    │
                    ├─> ColumnMappingConfig.from_file()
                    ├─> ColumnMapper(custom_config)
                    ├─> mapper.map_columns(df)
                    └─> AnonymizationService.anonymize_vm_record()
```

### Key Classes

- **`ColumnMappingConfig`**: Configuration data class with YAML/JSON I/O
- **`ColumnMapper`**: Main mapping service with normalization logic
- **`MappingResult`**: Result object with mapping details and diagnostics

### Data Flow

1. **User creates/edits** mapping configuration
2. **CLI loads** configuration into `ColumnMappingConfig`
3. **ColumnMapper** normalizes Excel columns and applies mappings
4. **Mapped DataFrame** passed to `AnonymizationService`
5. **Feedback** provided on mappings, conflicts, missing fields

## Examples

### Example 1: Simple Custom Export

```bash
# 1. Generate template
cli anonymize excel custom.xlsx -t mapping.yaml

# 2. Edit mapping.yaml (customize mappings)

# 3. Anonymize with custom mapping
cli anonymize excel custom.xlsx -c mapping.yaml -o anonymized.xlsx
```

### Example 2: Selective Anonymization

```bash
# Only anonymize VM names and IPs, using custom column names
cli anonymize excel data.xlsx \\
  -c my-mappings.yaml \\
  -o output.xlsx \\
  -f vm -f primary_ip_address
```

## Files Changed/Added

### New Files
- `src/services/column_mapper.py` - Core mapping service
- `tests/test_column_mapper.py` - Unit tests
- `docs/features/excel-column-mapping.md` - User documentation
- `docs/features/column-mapping-changelog.md` - This file

### Modified Files
- `src/commands/anonymize.py`:
  - Added `--mapping-config` option
  - Added `--generate-mapping-template` option
  - Integrated `ColumnMapper` into excel command
  - Enhanced feedback for mapping results

## Dependencies

- **PyYAML** (already included): For YAML configuration file support
- **pandas** (already included): For DataFrame operations

## Testing

Run tests:
```bash
uv run pytest tests/test_column_mapper.py -v
```

All 25 tests passing:
- Configuration I/O (YAML/JSON)
- Normalization (case, whitespace)
- Mapping application
- Conflict detection
- Template generation
- Integration workflows

## Future Enhancements

Potential improvements for future versions:

1. **Interactive Mapping**: CLI wizard to guide users through mapping creation
2. **Mapping Validation**: Pre-validate mappings against known field types
3. **Fuzzy Matching**: Suggest best matches for unmapped columns
4. **Mapping Repository**: Shared repository of common mapping configurations
5. **Multi-Sheet Support**: Apply different mappings to different sheets
6. **Column Transformations**: Support for data transformations during mapping

## Migration Notes

### For Existing Users

No action required! The feature is fully backwards compatible:
- Default mappings still work as before
- Existing commands continue to function
- Custom mappings are optional

### For New Users

Start with:
1. Try default behavior first
2. If columns aren't recognized, generate a template
3. Customize the template as needed
4. Reuse for similar files

## Support

- **Documentation**: `docs/features/excel-column-mapping.md`
- **Examples**: See documentation Examples section
- **Issues**: Check troubleshooting section in docs
