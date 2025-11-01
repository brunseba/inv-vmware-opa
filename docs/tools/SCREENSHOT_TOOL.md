# Screenshot Automation Tool

Comprehensive documentation for the `vmware-screenshot` CLI tool integrated into the inv-vmware-opa package.

## Overview

The screenshot automation tool provides automated capture of dashboard screenshots for documentation, using Selenium WebDriver with a beautiful Rich CLI interface.

## Installation

### Option 1: Full Suite (Recommended)
```bash
pipx install '.[dashboard,screenshots]'
```
Includes: dashboard server + screenshot automation

### Option 2: Screenshots Only
```bash
pipx install '.[screenshots]'
```
Note: Requires manually starting the dashboard

### Option 3: Everything
```bash
pipx install '.[all]'
```
Includes: dashboard, reports, and screenshots

## Commands

### `vmware-screenshot pages`

List all available dashboard pages that can be captured.

```bash
vmware-screenshot pages
```

**Output**: Rich table showing page names and descriptions

### `vmware-screenshot capture`

Capture screenshots with full control.

**Options:**
- `--url` - Dashboard URL (default: http://localhost:8501)
- `--output, -o` - Output directory (default: docs/images/screenshots)
- `--page, -p` - Specific page to capture
- `--theme, -t` - Theme: light, dark, both (default: both)
- `--all, -a` - Capture all pages
- `--headless/--no-headless` - Browser mode (default: headless)
- `--wait, -w` - Wait time after load in seconds (default: 2)

**Examples:**
```bash
# Capture all pages in both themes
vmware-screenshot capture --all

# Specific page, dark mode only
vmware-screenshot capture --page "Overview" --theme dark

# Custom output directory
vmware-screenshot capture --all --output docs/images/v0.7.0

# See browser (not headless)
vmware-screenshot capture --all --no-headless
```

### `vmware-screenshot auto`

Fully automated: starts server, captures, stops server.

**Options:**
- `--port, -p` - Dashboard port (default: 8501)
- `--output, -o` - Output directory (default: docs/images/screenshots)
- `--theme, -t` - Theme to capture (default: both)
- `--wait-server` - Seconds to wait for server (default: 5)
- `--wait-page` - Seconds to wait after page load (default: 2)

**Examples:**
```bash
# Fully automated capture
vmware-screenshot auto

# Light theme only, custom output
vmware-screenshot auto --theme light --output docs/images/v0.7.0

# Slower server startup
vmware-screenshot auto --wait-server 20
```

**Requirements:** Needs `streamlit` available (install with dashboard dependencies)

### `vmware-screenshot serve`

Start the dashboard server manually.

**Options:**
- `--port, -p` - Port to run on (default: 8501)
- `--wait, -w` - Seconds to wait before ready (default: 5)

**Examples:**
```bash
# Start on default port
vmware-screenshot serve

# Custom port
vmware-screenshot serve --port 8502
```

### `vmware-screenshot list`

List captured screenshots in table format.

**Options:**
- `--output, -o` - Screenshots directory (default: docs/images/screenshots)

**Examples:**
```bash
# List all screenshots
vmware-screenshot list

# List from custom directory
vmware-screenshot list --output docs/images/v0.7.0
```

**Output**: Rich table showing pages, themes available, and file sizes

## Architecture

### Components

1. **screenshot_cli.py** (535 lines)
   - Click-based CLI interface
   - Rich console output
   - 5 main commands
   - Error handling and validation

2. **screenshot_dashboard.py** (313 lines)
   - Selenium WebDriver automation
   - Chrome browser control
   - Navigation logic
   - Screenshot capture

3. **Integration**
   - Part of `inv-vmware-opa` package
   - Optional `screenshots` dependency group
   - Entry point: `vmware-screenshot`

### Dependencies

- **selenium** - Browser automation
- **webdriver-manager** - Automatic ChromeDriver management
- **pillow** - Image processing
- **rich** - Beautiful terminal output
- **click** - CLI framework
- **requests** - HTTP connectivity checks

### Technical Details

- **Browser**: Chrome (headless by default)
- **Resolution**: 1920x1080
- **Format**: PNG
- **Naming**: `{page_name}_{theme}.png`

## Usage Patterns

### Documentation Updates

```bash
# Capture all pages for new release
vmware-screenshot auto --output docs/images/v0.7.0 --theme light

# Update specific page screenshots
vmware-screenshot capture --page "Data Explorer" --all-themes
```

### CI/CD Integration

```bash
# In GitHub Actions
- name: Capture screenshots
  run: |
    pipx install '.[dashboard,screenshots]'
    vmware-screenshot auto --output artifacts/screenshots
```

### Manual Testing

```bash
# Terminal 1: Start dashboard
vmware-dashboard

# Terminal 2: Capture screenshots
vmware-screenshot capture --all --no-headless
```

## Troubleshooting

### ChromeDriver Issues

```bash
# Clear webdriver cache
rm -rf ~/.wdm/

# Reinstall
pipx reinstall inv-vmware-opa
```

### Dashboard Not Accessible

```bash
# Check if dashboard is running
curl http://localhost:8501

# Check process
ps aux | grep streamlit
```

### Streamlit Not Found (pipx)

```bash
# Install with dashboard dependencies
pipx install --force '.[dashboard,screenshots]'
```

### Screenshots Not Captured

1. Check dashboard has data loaded
2. Increase wait times: `--wait-server 20 --wait-page 3`
3. Run without headless to see browser: `--no-headless`
4. Check navigation buttons are visible

### Navigation Button Not Found

Some pages may be in collapsed expanders. The tool attempts to:
1. Find button by exact text match
2. Case-insensitive search
3. Partial text match

If a page isn't captured, it may need to be expanded manually first.

## Best Practices

1. **Always test locally first** before CI/CD
2. **Use appropriate wait times** for slow systems
3. **Capture light theme** for documentation (better readability)
4. **Version screenshots** by output directory (e.g., v0.7.0)
5. **Check screenshots** after capture for quality
6. **Keep browser updated** (Chrome auto-updates)

## Known Limitations

- Requires Chrome browser installed
- Dashboard must have data for meaningful screenshots
- Some pages may be in collapsed navigation sections
- Full-page scrolling screenshots not yet implemented
- No video capture support

## Future Enhancements

- [ ] Automatic expander expansion for navigation
- [ ] Full-page scrolling screenshots
- [ ] Custom page resolution support
- [ ] Multiple browser support (Firefox, Edge)
- [ ] Screenshot comparison/diff
- [ ] Video recording capability
- [ ] Parallel page capture
- [ ] Screenshot optimization/compression

## Contributing

To improve the screenshot tool:

1. Update `src/tools/screenshot_cli.py` for CLI changes
2. Update `src/tools/screenshot_dashboard.py` for automation logic
3. Add tests in `tests/tools/`
4. Update this documentation
5. Follow conventional commits

## License

Part of the inv-vmware-opa project. See main LICENSE file.

## Support

- **Issues**: https://github.com/brunseba/inv-vmware-opa/issues
- **Discussions**: https://github.com/brunseba/inv-vmware-opa/discussions
- **Documentation**: https://github.com/brunseba/inv-vmware-opa/docs
