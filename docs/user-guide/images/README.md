# User Guide Images

This directory contains screenshots used in the user guide documentation.

## Structure

```
docs/user-guide/images/
└── v0.7.0/ → ../../images/v0.7.0 (symbolic link)
```

## Images Available

All 20 dashboard page screenshots are accessible via the symbolic link:

### Main Navigation (1)
- `overview_light.png` - Overview dashboard

### Explore & Analyze (7)
- `data_explorer_light.png` - PyGWalker data exploration
- `advanced_explorer_light.png` - SQL query interface
- `vm_explorer_light.png` - Detailed VM inspection
- `vm_search_light.png` - Advanced VM search
- `analytics_light.png` - Resource analytics
- `comparison_light.png` - Side-by-side comparisons
- `data_quality_light.png` - Data quality analysis

### Infrastructure (4)
- `resources_light.png` - Resource metrics
- `infrastructure_light.png` - Infrastructure topology
- `folder_analysis_light.png` - Folder-level analytics
- `folder_labelling_light.png` - Label management

### Migration (4)
- `migration_targets_light.png` - Migration targets
- `strategy_configuration_light.png` - Strategy configuration
- `migration_planning_light.png` - Migration planning
- `migration_scenarios_light.png` - Migration scenarios

### Management (2)
- `data_import_light.png` - Data import interface
- `database_backup_light.png` - Database backup

### Export & Help (2)
- `pdf_export_light.png` - PDF report generation
- `help_light.png` - Help and documentation

## Usage in Documentation

### Relative Path
```markdown
![Overview](images/v0.7.0/overview_light.png)
```

### In visual-guide.md
All 20 screenshots are embedded with descriptions and usage instructions.

### In dashboard.md
Key screenshots are embedded in relevant sections:
- Overview page
- VM Explorer
- Folder Analysis
- Data Import
- Folder Labelling
- PDF Export

## Source Location

The actual image files are stored at:
```
docs/images/v0.7.0/
```

The symbolic link allows user-guide documents to reference images with shorter, local paths.

## Updating Images

To update screenshots:

1. Generate new screenshots:
   ```bash
   vmware-screenshot auto --output docs/images/v0.7.X
   ```

2. Update the symbolic link:
   ```bash
   cd docs/user-guide/images
   rm v0.7.0
   ln -s ../../images/v0.7.X v0.7.X
   ```

3. Update image references in documentation:
   ```bash
   cd docs/user-guide
   sed -i '' 's|v0.7.0|v0.7.X|g' *.md
   ```

## File Sizes

All images are PNG format, approximately 70-170 KB each, totaling ~2.3 MB for the complete set.

## Best Practices

- Keep images at reasonable resolution (current: 1920x1080)
- Use consistent naming: `{page_name}_light.png`
- Compress images if size exceeds 200 KB
- Update all references when changing image paths
- Maintain version directories for historical reference

## Related Documentation

- [Visual Guide](../visual-guide.md) - Complete guide with all screenshots
- [Dashboard Guide](../dashboard.md) - Detailed feature documentation
- [Screenshot Tool](../../tools/SCREENSHOT-TOOL-USAGE.md) - Screenshot automation
