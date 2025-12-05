# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-12-05

### Features

- *(naming-convention)* Add database models and service layer
- *(naming-convention)* Add CLI commands
- *(ui)* Add Naming Convention Manager Streamlit page
- *(ui)* Add Naming Analysis Streamlit page
- *(migrations)* Add naming convention tables migration
- *(cli)* Enhance naming-convention show with detailed field information
- *(cli)* Display all naming_convention_fields schema columns in show command
- *(webui)* Add edit convention capability
- *(cli)* Add import and export commands for naming conventions
- *(analysis)* Add multi-convention analysis capability
- *(webui)* Add multi-convention analysis to naming convention manager
- *(webui)* Add multi-convention analysis to naming analysis page
- *(labels)* Add label generation from naming convention fields
- *(ui)* Add label management UI and VM Label Analysis page
- *(cli)* Add --auto-label flag to analyze commands
- *(db)* Add migration 004 for label source tracking

### Bug Fixes

- *(dashboard)* Resolve module import errors for pipx installation
- *(dashboard)* Prevent recursive streamlit launch in main()
- *(dashboard)* Correct page import paths for installed package
- *(dashboard)* Register naming pages in page navigator
- *(dashboard)* Make JSON field access SQLite-compatible in naming analysis
- *(ui)* Add VM Label Analysis to valid pages list
- *(ui)* Correct VirtualMachine attribute name in VM Label Analysis
- *(ui)* Resolve ambiguous column error when filtering by ALL labels

### Documentation

- *(naming-convention)* Add example JSON configurations
- *(contributing)* Add contributing guide with conventional commits info

### Testing

- *(naming-convention)* Add comprehensive CLI testing documentation

### Miscellaneous Tasks

- Bump version to 0.8.0
- Add conventional commits workflow and documentation
- *(dashboard)* Suppress harmless ScriptRunContext warnings
- Apply black formatting and update dependencies
- Update gitignore to exclude generated docs and temp files
- *(release)* Bump version to 0.9.0 and update changelog

## [0.8.0] - 2025-11-02

### Features

- Add docker dual-variant system with slim and full images

## [0.7.2] - 2025-11-02

### Features

- PyGWalker Data Explorer & Dark Mode (v0.7.0) (#3)
- *(tools)* Add automated screenshot tool for documentation
- *(tools)* Add rich CLI for screenshot tool
- *(tools)* Add pipx support for screenshot-cli installation
- *(packaging)* Integrate screenshot-cli into main inv-vmware-opa package
- Add query parameter navigation and enhance screenshot tool
- *(docker)* Add automated versioning with git tags

### Bug Fixes

- *(tools)* Add standalone CLI wrapper and improve installation docs
- *(tools)* Improve error handling for missing streamlit dependency
- *(tools)* Use sys.executable for streamlit in pipx venv
- *(tools)* Enable software WebGL rendering in headless Chrome

### Documentation

- Update changelog and documentation for v0.6.2 release
- Add WebAssembly frontend evaluation plan
- Move all markdown files to docs folder except README and CHANGELOG
- Reorganize documentation into logical subdirectories
- Add streamlit-timeline evaluation for migration visualizations
- Add pygwalker evaluation for data exploration
- *(tools)* Add comprehensive screenshot tool documentation
- *(screenshots)* Add v0.7.0 dashboard screenshots

### Refactor

- Move utility and migration scripts to scripts folder

### Miscellaneous Tasks

- Remove orphaned files from root directory
- *(licenses)* Update license information for all dependencies
- Bump version to 0.7.0

## [0.6.2] - 2025-10-30

### Features

- *(migration)* Add multi-target migration planning with 6Rs framework
- *(ui)* Add migration targets and scenarios UI pages

### Bug Fixes

- *(ui)* Register migration pages in PageNavigator
- *(models)* Add __init__.py and fix imports in UI pages
- *(ui)* Migrate use_container_width to width parameter and fix duration calculation

## [0.6.1] - 2025-10-30

### Features

- *(cli)* Add support for viewing label tables schema
- *(dashboard)* Reorganize sidebar menu for enhanced UX
- *(labelling)* Add VM retrieval by OS and resource categories
- *(dashboard)* Add batch VM labelling capabilities
- *(labelling)* Add Specific OS filtering for precise VM targeting
- *(dashboard)* Add Data Import & Database Management page
- *(cli)* Add fullweb command for web-only database creation and data loading
- *(dashboard)* Add flexible clear data options with label preservation
- *(database)* Add schema version tracking system
- *(docker)* Add containerized deployment with multi-stage build

### Bug Fixes

- Update version to 0.6.0 across all components
- Resolve database connection test and PaginationHelper import errors
- *(labelling)* Align resource criteria with database schema
- *(dashboard)* Register Data Import page in PageNavigator
- *(dashboard)* Handle empty database gracefully in fullweb mode
- *(docker)* Resolve Streamlit permission errors and enhance configuration…

### Documentation

- Update CHANGELOG for v0.6.0 release
- Add comprehensive Folder Labelling documentation

### Refactor

- *(dashboard)* Reorganize menu - Infrastructure and Migration grouping

### Miscellaneous Tasks

- Bump version to 0.6.0
- Upgrade streamlit to v1.51.0 and update documentation

## [0.6.0] - 2025-10-30

### Features

- Backup/Restore and Label Quality Features (v0.5.0) (#1)
- Implement technical debt improvements - pagination, state management, and validation

### Documentation

- Update documentation for v0.5.0 release
- Add CHANGELOG.md for project history tracking

### Testing

- Add comprehensive unit test suite with 151 tests

### Miscellaneous Tasks

- Bump version to 0.4.0
- Bump version to 0.5.0
- Update pyproject.toml to v0.5.0
- Apply technical debt recommendations and improve project configuration

## [0.4.0] - 2025-10-28

### Features

- *(migration-planning)* Add regex filtering for folder selection

### Miscellaneous Tasks

- Bump version to 0.3.0
- Update pyproject.toml version to 0.3.0

## [0.3.0] - 2025-10-28

### Features

- *(dashboard)* Add comprehensive help system and improve migration planning UI

## [0.2.1] - 2025-10-27

### Features

- Add extended PDF export with all analytics charts
- Add migration planning tool with time estimation
- Add folder-based migration selection strategy
- Add migration strategy synthesis table with editable values

### Bug Fixes

- Move batch assignment before folder tab to prevent KeyError
- *(dashboard)* Correct Excel chart data range references

### Miscellaneous Tasks

- Add GitHub Actions workflow for MkDocs deployment

## [0.2.0] - 2025-10-27

### Features

- Initial implementation of VMware inventory CLI
- Add comprehensive Streamlit dashboard with analytics and performance optimizations
- Add clean command to remove all database records
- Add Excel sheet selection for data import
- Add comprehensive PDF export with charts and enhance UI

### Miscellaneous Tasks

- Add sensitive file to gitignore
- Cleanup duplicate dashboard files
- Reorganize database location to data/ directory

<!-- generated by git-cliff -->
