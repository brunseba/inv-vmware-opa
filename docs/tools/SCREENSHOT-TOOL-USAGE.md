# Screenshot Tool Usage

## Overview

The screenshot tool now captures all **20 dashboard pages** as documented in `docs/API-ENDPOINTS.md`. It has been updated to provide comprehensive visual documentation for the entire application.

## Changes in This Update

### URI-Based Navigation (Latest)

The tool now uses **direct URI navigation** from `docs/API-ENDPOINTS.md`:
- **Faster**: No need to click through UI menus
- **More reliable**: Direct page access via query parameters
- **Consistent**: Uses documented URIs from API-ENDPOINTS.md
- **Fallback**: Can still use UI button navigation if needed

**Navigation Methods:**
- `--use-uri` (default): Direct URI navigation (e.g., `?page=Data_Explorer`)
- `--use-ui`: Traditional UI button clicking

### Extended Page Coverage

The tool now captures all pages organized by category:

**Main Navigation (1 page):**
- Overview

**Explore & Analyze (7 pages):**
- Data Explorer
- Advanced Explorer
- VM Explorer
- VM Search
- Analytics
- Comparison
- Data Quality

**Infrastructure (4 pages):**
- Resources
- Infrastructure
- Folder Analysis
- Folder Labelling

**Migration (4 pages):**
- Migration Targets
- Strategy Configuration
- Migration Planning
- Migration Scenarios

**Management (2 pages):**
- Data Import
- Database Backup

**Export & Help (2 pages):**
- PDF Export
- Documentation

### Total Screenshots

- **Pages**: 20
- **Themes**: 2 (light & dark)
- **Total Screenshots**: 40 (when capturing all pages in both themes)

## Quick Start

### 1. Automated Capture (All Pages, Both Themes)

```bash
# Easiest option - fully automated
vmware-screenshot auto

# Custom output directory
vmware-screenshot auto --output docs/images/v0.7.1
```

This will:
1. Start the dashboard server
2. Load all 20 pages from API-ENDPOINTS.md (same list as `vmware-screenshot pages`)
3. Capture all pages in both themes using URI navigation (40 screenshots)
4. Stop the server
5. Save screenshots with proper naming

### 2. Manual Capture (Server Already Running)

```bash
# Terminal 1: Start dashboard
streamlit run src/dashboard/app.py

# Terminal 2: Capture all pages
vmware-screenshot capture --all

# Or capture specific page
vmware-screenshot capture --page "Data Explorer" --theme both
```

### 3. List Available Pages

```bash
# Show all 20 pages with descriptions
vmware-screenshot pages

# Discover pages from live dashboard
vmware-screenshot pages --live
```

## Commands Reference

### `auto` - Fully Automated

```bash
vmware-screenshot auto [OPTIONS]
```

**Options:**
- `--port` - Dashboard port (default: 8501)
- `--output` - Output directory (default: `docs/images/screenshots`)
- `--theme` - Theme(s): light, dark, both (default: both)
- `--wait-server` - Seconds to wait for server (default: 5)
- `--wait-page` - Seconds to wait after page load (default: 2)

**Example:**
```bash
# Capture all pages in both themes
vmware-screenshot auto --output docs/images/v0.7.1
```

**Note:** The `auto` command uses the same page list as `vmware-screenshot pages`, loaded directly from API-ENDPOINTS.md. It uses fast URI navigation by default.

### `capture` - Capture Screenshots

```bash
vmware-screenshot capture [OPTIONS]
```

**Options:**
- `--url` - Dashboard URL (default: http://localhost:8501)
- `--output, -o` - Output directory
- `--page, -p` - Specific page to capture
- `--theme, -t` - Theme: light, dark, both (default: both)
- `--all, -a` - Capture all pages
- `--headless/--no-headless` - Run browser in headless mode (default: true)
- `--wait, -w` - Wait time after page load (default: 2)
- `--use-uri/--use-ui` - Navigation method: URI (faster, default) or UI buttons

**Examples:**
```bash
# Capture all pages in both themes (uses URI navigation by default)
vmware-screenshot capture --all

# Capture specific page in dark mode
vmware-screenshot capture --page "VM Explorer" --theme dark

# Capture with custom wait time
vmware-screenshot capture --all --wait 3

# Use UI button navigation instead of URI (slower but may work if URIs change)
vmware-screenshot capture --all --use-ui

# Capture single page with URI navigation (fast)
vmware-screenshot capture --page "Data Explorer" --use-uri
```

### `pages` - List Available Pages

```bash
vmware-screenshot pages [OPTIONS]
```

**Options:**
- `--url` - Dashboard URL (default: http://localhost:8501)
- `--live` - Discover pages from live dashboard

**Examples:**
```bash
# Show known pages
vmware-screenshot pages

# Discover all pages from running dashboard
vmware-screenshot pages --live
```

### `list` - List Captured Screenshots

```bash
vmware-screenshot list [OPTIONS]
```

**Options:**
- `--output, -o` - Screenshots directory (default: `docs/images/screenshots`)

**Example:**
```bash
# List screenshots in default directory
vmware-screenshot list

# List screenshots in custom directory
vmware-screenshot list --output docs/images/v0.7.1
```

### `serve` - Start Dashboard Server

```bash
vmware-screenshot serve [OPTIONS]
```

**Options:**
- `--port, -p` - Port to run dashboard on (default: 8501)
- `--wait, -w` - Seconds to wait before dashboard is ready (default: 5)

**Example:**
```bash
# Start on default port
vmware-screenshot serve

# Start on custom port
vmware-screenshot serve --port 8502
```

## File Naming Convention

Screenshots are saved with the following naming pattern:

```
{page_name}_{theme}.png
```

Examples:
- `overview_light.png`
- `overview_dark.png`
- `data_explorer_light.png`
- `vm_search_dark.png`
- `migration_targets_light.png`

## Output Directory Structure

```
docs/images/screenshots/  (or custom directory)
├── overview_light.png
├── overview_dark.png
├── data_explorer_light.png
├── data_explorer_dark.png
├── advanced_explorer_light.png
├── advanced_explorer_dark.png
├── vm_explorer_light.png
├── vm_explorer_dark.png
├── vm_search_light.png
├── vm_search_dark.png
├── analytics_light.png
├── analytics_dark.png
├── comparison_light.png
├── comparison_dark.png
├── data_quality_light.png
├── data_quality_dark.png
├── resources_light.png
├── resources_dark.png
├── infrastructure_light.png
├── infrastructure_dark.png
├── folder_analysis_light.png
├── folder_analysis_dark.png
├── folder_labelling_light.png
├── folder_labelling_dark.png
├── migration_targets_light.png
├── migration_targets_dark.png
├── strategy_configuration_light.png
├── strategy_configuration_dark.png
├── migration_planning_light.png
├── migration_planning_dark.png
├── migration_scenarios_light.png
├── migration_scenarios_dark.png
├── data_import_light.png
├── data_import_dark.png
├── database_backup_light.png
├── database_backup_dark.png
├── pdf_export_light.png
├── pdf_export_dark.png
├── documentation_light.png
└── documentation_dark.png
```

## Recommended Workflows

### For Documentation Updates

```bash
# 1. Fully automated capture
vmware-screenshot auto --output docs/images/v0.7.1

# 2. Verify captured screenshots
vmware-screenshot list --output docs/images/v0.7.1

# 3. Update documentation references
```

### For Testing New Features

```bash
# 1. Start dashboard manually
streamlit run src/dashboard/app.py

# 2. Capture specific page being tested
vmware-screenshot capture --page "New Feature" --theme both

# 3. Verify visually
open docs/images/screenshots/new_feature_light.png
```

### For CI/CD Pipeline

```bash
# Use headless mode with automated capture
vmware-screenshot auto \
  --output build/screenshots \
  --theme both \
  --wait-server 10 \
  --wait-page 3
```

## Troubleshooting

### Dashboard Not Accessible

**Error:** `❌ Dashboard not accessible at http://localhost:8501`

**Solution:**
```bash
# Start the dashboard first
streamlit run src/dashboard/app.py --server.port 8501
```

### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'selenium'`

**Solution:**
```bash
# Install screenshot dependencies
pip install inv-vmware-opa[screenshots]

# Or manually
pip install selenium webdriver-manager pillow
```

### Navigation Failed

**Warning:** `⚠ Navigation button for 'Page Name' not found` or `⚠ Failed to load Page Name via URI`

**Possible causes:**
1. Page name spelling mismatch
2. Page URI has changed (if using `--use-uri`)
3. Page is in collapsed menu (if using `--use-ui`)
4. Page requires data to be loaded first

**Solution:**
- **With URI navigation (default):** Check `docs/API-ENDPOINTS.md` for correct page name
- **With UI navigation:** Use `vmware-screenshot pages --live` to discover exact page names
- **Fallback:** Try alternate navigation method:
  - If URI fails: `vmware-screenshot capture --page "Page Name" --use-ui`
  - If UI fails: `vmware-screenshot capture --page "Page Name" --use-uri`
- Increase wait time: `--wait 5`
- Ensure dashboard has data loaded

### Theme Toggle Not Working

**Warning:** `⚠ Theme toggle button not found`

**Solution:**
- Check that theme toggle is visible in sidebar
- Verify theme toggle button selector is correct
- May need to update theme toggle detection logic

## Advanced Usage

### Custom Browser Options

Edit `src/tools/screenshot_dashboard.py` to add custom Chrome options:

```python
self.chrome_options.add_argument("--window-size=2560,1440")  # Higher resolution
self.chrome_options.add_argument("--force-device-scale-factor=2")  # Retina display
```

### Custom Wait Conditions

For pages with dynamic content:

```bash
vmware-screenshot capture --page "Data Explorer" --wait 5
```

### Batch Processing

```bash
# Capture only explore pages
for page in "Data Explorer" "Advanced Explorer" "VM Explorer" "VM Search"; do
  vmware-screenshot capture --page "$page" --theme both
done
```

## Integration with Documentation

### Using Screenshots in Markdown

```markdown
![Overview Dashboard](docs/images/screenshots/overview_light.png)
*Main dashboard in light mode*

![Dark Mode](docs/images/screenshots/overview_dark.png)
*Main dashboard in dark mode*
```

### Using in README

```markdown
## Screenshots

### Dashboard Overview
![Dashboard](docs/images/v0.7.1/overview_light.png)

<details>
<summary>View More Screenshots</summary>

### Data Explorer
![Data Explorer](docs/images/v0.7.1/data_explorer_light.png)

### VM Explorer
![VM Explorer](docs/images/v0.7.1/vm_explorer_light.png)

</details>
```

## Page Synchronization

The screenshot tool is **fully synchronized** with `docs/API-ENDPOINTS.md`:

- All 20 pages from API-ENDPOINTS.md are included
- Page names match exactly (spaces converted to underscores in URIs)
- URIs follow the documented format: `?page=Page_Name`
- Descriptions match the documentation
- Categories are preserved
- Navigation uses direct URIs from API-ENDPOINTS.md

**URI Mapping:**
```
Page Name           → URI Parameter
"Data Explorer"     → ?page=Data_Explorer
"VM Search"         → ?page=VM_Search
"Migration Targets" → ?page=Migration_Targets
```

When adding new pages:
1. Update `docs/API-ENDPOINTS.md` (add page and URI)
2. Screenshot tool will automatically use the new page name
3. Update this documentation with any special considerations

## Related Documentation

- [API Endpoints](../API-ENDPOINTS.md) - Full list of all pages
- [Pages Quick Reference](../PAGES-QUICK-REFERENCE.md) - Quick reference guide
- [Dashboard User Guide](../features/dashboard-guide.md) - Dashboard usage

## Version History

- **v0.7.0**: Initial screenshot tool with 7 pages
- **v0.7.1**: Extended to all 20 pages from API-ENDPOINTS.md
- **v0.7.2** (Latest): Added URI-based navigation using API-ENDPOINTS.md URIs
  - Direct URI navigation (faster, more reliable)
  - Synchronized with API-ENDPOINTS.md URI list
  - Fallback to UI button navigation
  - Enhanced `pages` command with URI display
  - Updated CLI with `--use-uri` / `--use-ui` options
