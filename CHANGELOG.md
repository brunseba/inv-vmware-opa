## Unreleased

## v0.6.2 (2025-11-01)

### Fix

- fix(ui): migrate use_container_width to width parameter and fix duration calculation (0ba8712)
- fix(models): add __init__.py and fix imports in UI pages (3e956fb)
- fix(ui): register migration pages in PageNavigator (beae752)

### Feat

- feat(ui): add migration targets and scenarios UI pages (3e96a11)
- feat(migration): add multi-target migration planning with 6Rs framework (3380bd0)

### Improvements

- Replace deprecated `use_container_width` parameter with `width` across all Streamlit components
- Fix duration calculation to show live-calculated values instead of stale database values
- Add column descriptions info bubble for better UX clarity in scenarios table
- Separate migration and runtime cost displays for clearer cost analysis
- Enhance replication duration calculation with multi-phase modeling

## v0.6.0 (2025-10-30)

### Feat

- implement technical debt improvements - pagination, state management, and validation
- add centralized state management with SessionKeys enum and StateManager class
- add pagination utilities with PaginationHelper for large datasets (10,000+ records)
- add input validation framework with DataValidator and ErrorHandler classes
- add comprehensive caching utilities with DatabaseManager
- integrate pagination into vm_explorer and data_quality pages
- add pytest configuration and test infrastructure
- reorganize documentation into docs/ directory

### Improvements

- enhance error handling across the dashboard
- optimize performance for queries with large datasets (2-5s → <500ms per page)
- add unit and integration tests for utility modules
- improve memory usage from ~500MB to ~50MB for large datasets

### Technical Debt

- resolve inconsistent state management issues
- resolve performance issues with large datasets through pagination
- create input validation utilities (partially integrated)

## v0.5.0 (2025-10-29)

### Feat

- Backup/Restore and Label Quality Features (#1)

## v0.4.0 (2025-10-28)

### Feat

- **migration-planning**: add regex filtering for folder selection

## v0.3.0 (2025-10-28)

### Feat

- **dashboard**: add comprehensive help system and improve migration planning UI

## v0.2.1 (2025-10-27)

### BREAKING CHANGE

- PDF export now requires chart configuration parameters

### Feat

- add migration strategy synthesis table with editable values
- add folder-based migration selection strategy
- add migration planning tool with time estimation
- add extended PDF export with all analytics charts

### Fix

- **dashboard**: correct Excel chart data range references
- move batch assignment before folder tab to prevent KeyError

## v0.2.0 (2025-10-27)

### BREAKING CHANGE

- None
- Database schema updated with new indexes

### Feat

- add comprehensive PDF export with charts and enhance UI
- add Excel sheet selection for data import
- add clean command to remove all database records
- add comprehensive Streamlit dashboard with analytics and performance optimizations
- initial implementation of VMware inventory CLI
