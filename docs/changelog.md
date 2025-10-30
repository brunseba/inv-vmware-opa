# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- N/A

### Changed
- N/A

### Fixed
- N/A

## [0.5.0] - 2025-10-30

### Added
- **Backup & Restore**: Full database backup and restore functionality
  - `vmware-inv backup` command for SQLite database backup
  - `vmware-inv restore` command with automatic safety backup
  - Dedicated backup page in web interface with download capability
- **Label Backup & Restore**: JSON-based label export/import
  - `vmware-inv label backup` for exporting labels to JSON
  - `vmware-inv label restore` with three import modes (merge, skip_duplicates, replace)
  - `vmware-inv label list-backups` to view available backups
  - Smart ID mapping during restore
- **Label Quality Analysis**: Comprehensive label quality reporting
  - New "Labels" category in Data Quality page
  - Label coverage metrics and statistics
  - Quality issue detection (unused labels, low coverage, single-value keys)
  - Folder-level label coverage analysis
  - Four analysis tabs: Coverage, Keys Analysis, Quality Issues, Coverage by Folder
- **Label Filtering**: Filter VMs and folders by labels
  - Label key and value filters in VM Explorer
  - Label filtering in Folder Analysis
  - Support for key-only or key=value filtering
  - Works alongside existing filters
- **Bulk Operations**: Mass folder labeling capabilities
  - `vmware-inv label assign-all-folders` command
  - Pattern matching support (glob-style)
  - Dry-run mode to preview changes
  - Progress tracking with progress bars
  - Confirmation prompts for safety
- **Label Integration**: Labels now visible across all tools
  - Label count column in Folder Analysis
  - Labels tab in VM Explorer details view
  - Label coverage metrics in summary statistics
  - Direct and inherited labels clearly distinguished
- **Enhanced Services**: New BackupService for all backup operations
  - Automatic backup before restore
  - List available backups
  - Export/import with error tracking

### Changed
- Folder Analysis now includes label count in folder table
- VM Explorer details now has dedicated Labels tab
- Data Quality page expanded with label-specific analysis
- Summary metrics now include label coverage statistics

### Fixed
- Label count calculation timing in Folder Analysis
- Path import missing in label commands

## [0.1.0] - 2025-10-27

### Added
- Initial release
- Basic CLI functionality
- Database storage support
- Excel import capability
