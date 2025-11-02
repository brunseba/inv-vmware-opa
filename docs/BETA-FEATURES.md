# Beta Features

## Anonymization (BETA)

> ⚠️ **Status**: Beta  
> **Added**: v0.7.0  
> **Stability**: Testing phase - please validate all results

The anonymization feature allows you to create sanitized versions of VMware inventory data for demos, documentation, and testing purposes.

### What's Beta?

This feature is currently in beta, which means:

- ✅ **Core functionality works** - The anonymization logic is functional and tested
- ⚠️ **Limited production use** - Not recommended for critical production workflows yet
- 🧪 **Testing encouraged** - We encourage testing and feedback
- 📝 **May change** - APIs and behavior may change based on feedback
- ✓ **Well documented** - Full documentation available despite beta status

### Beta Limitations

- **Data validation**: Always validate anonymized output before sharing
- **Edge cases**: Some unusual data patterns may not anonymize as expected
- **Performance**: Not optimized for very large datasets (>100k VMs)
- **Reversibility**: Mapping files help track changes but reversal isn't guaranteed

### Features Available

#### Database Anonymization
```bash
cli anonymize database --output data/anonymized.db --mapping-file mapping.json
```

Anonymizes an entire SQLite database while preserving:
- Resource metrics (CPU, memory, storage)
- Relationships (datacenter → cluster → host → VM)
- Power states, OS types, configurations
- Timestamps and dates

#### Excel Anonymization
```bash
cli anonymize excel input.xlsx -o output.xlsx --mapping-config column-mapping.yaml
```

Anonymizes Excel files directly with:
- Custom column mapping support
- Selective field anonymization
- Template generation for custom formats
- YAML/JSON configuration files

#### Column Mapping (BETA)
```bash
# Generate mapping template
cli anonymize excel data.xlsx --generate-mapping-template mapping.yaml

# Use custom mapping
cli anonymize excel data.xlsx -c mapping.yaml -o output.xlsx
```

Map custom Excel column names to internal fields for flexible anonymization.

### Providing Feedback

If you encounter issues or have suggestions:

1. **Test thoroughly** - Validate anonymized output
2. **Document issues** - Note what didn't work as expected
3. **Share feedback** - Create GitHub issues with details
4. **Suggest improvements** - Ideas for better anonymization strategies

### When Will It Be Stable?

The feature will move from beta to stable when:

- ✅ Community testing validates core scenarios
- ✅ No critical bugs reported for 2+ release cycles
- ✅ Performance is acceptable for typical datasets
- ✅ Documentation covers all common use cases
- ✅ Test coverage reaches 90%+ for anonymization code

Current progress: ~80% complete

### Migration Path

When the feature becomes stable:
- No breaking changes to configuration files
- Existing mapping files will continue to work
- CLI commands will remain the same
- Only improvements and new features added

### Getting Help

- **Documentation**: See `docs/features/excel-column-mapping.md`
- **Examples**: Check `configs/example-column-mapping.yaml`
- **Issues**: Report on GitHub issue tracker
- **Questions**: Use GitHub Discussions

### Thank You

Thank you for being an early adopter of the anonymization feature! Your feedback helps make it better for everyone.
