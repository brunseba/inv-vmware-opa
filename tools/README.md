# Dashboard Screenshot Tool

Automated screenshot capture tool for VMware Inventory Dashboard documentation using Selenium.

## Features

- 🎯 **Automated Capture**: Captures screenshots of all dashboard pages automatically
- 🌙 **Theme Support**: Takes screenshots in both light and dark modes
- 📸 **Full Page**: Option to capture full-page scrolling screenshots
- 🖥️ **Headless Mode**: Runs without opening a browser window
- 🎨 **High Quality**: 1920x1080 resolution screenshots

## Installation

### Option 1: Using UV (Recommended)

```bash
# Install with uv (handles dependencies automatically)
uv pip install -r tools/requirements-screenshots.txt

# Run directly
./screenshot-cli --help
```

### Option 2: Using Virtual Environment

```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r tools/requirements-screenshots.txt

# Run CLI
./screenshot-cli --help
```

### Option 3: Using pipx (Isolated)

```bash
# Install pipx if not already installed
brew install pipx  # macOS
# OR: python3 -m pip install --user pipx

# Install CLI in isolated environment
cd tools
pipx install -r requirements-screenshots.txt
cd ..

# Run from anywhere
screenshot-cli --help
```

### Option 4: Direct Python Call

```bash
# No installation needed, but dependencies must be available
python3 tools/screenshot_cli.py --help
```

## Prerequisites

1. **Chrome Browser**: Must be installed on your system
2. **ChromeDriver**: Automatically managed by `webdriver-manager`
3. **Running Dashboard**: Dashboard must be running locally

## Usage

### Option 1: CLI (Recommended)

The easiest way to use the tool is via the `screenshot-cli` command:

```bash
# Capture all pages automatically
screenshot-cli capture --all

# Capture specific page
screenshot-cli capture --page "Overview" --theme dark

# Fully automated (starts server, captures, stops)
screenshot-cli auto

# List available pages
screenshot-cli pages

# View captured screenshots
screenshot-cli list
```

### Option 2: Python Script

```bash
# Terminal 1: Start the dashboard
streamlit run src/dashboard/app.py --server.port 8501

# Terminal 2: Capture all pages in both themes
python tools/screenshot_dashboard.py
```

### Advanced Options

```bash
# Capture specific page
python tools/screenshot_dashboard.py --page "Overview"

# Capture only dark mode
python tools/screenshot_dashboard.py --theme dark

# Custom URL and output directory
python tools/screenshot_dashboard.py \
  --url http://localhost:8502 \
  --output docs/images/v0.7.0

# Run in visible mode (see browser)
python tools/screenshot_dashboard.py --headless=false
```

## CLI Commands

### `screenshot-cli capture`

Capture dashboard screenshots.

**Options:**
- `--url` - Dashboard URL (default: http://localhost:8501)
- `--output, -o` - Output directory (default: docs/images/screenshots)
- `--page, -p` - Specific page to capture
- `--theme, -t` - Theme(s): light, dark, both (default: both)
- `--all, -a` - Capture all pages (tour mode)
- `--headless/--no-headless` - Run browser in headless mode (default: True)
- `--wait, -w` - Wait time after page load in seconds (default: 2)

**Examples:**
```bash
# Capture all pages
screenshot-cli capture --all

# Specific page, dark mode only
screenshot-cli capture --page "Data Explorer" --theme dark

# Custom output directory
screenshot-cli capture --all --output docs/images/v0.7.0

# Visible browser (not headless)
screenshot-cli capture --all --no-headless
```

### `screenshot-cli auto`

Fully automated: start server, capture, stop server.

**Options:**
- `--port, -p` - Dashboard port (default: 8501)
- `--output, -o` - Output directory (default: docs/images/screenshots)
- `--theme, -t` - Theme(s) to capture (default: both)
- `--wait-server` - Seconds to wait for server start (default: 5)
- `--wait-page` - Seconds to wait after page load (default: 2)

**Examples:**
```bash
# One command to rule them all
screenshot-cli auto

# Custom output
screenshot-cli auto --output docs/images/release-0.7.0
```

### `screenshot-cli serve`

Start the dashboard server.

**Options:**
- `--port, -p` - Port to run on (default: 8501)
- `--wait, -w` - Seconds to wait before ready (default: 5)

**Examples:**
```bash
# Start on default port
screenshot-cli serve

# Custom port
screenshot-cli serve --port 8502
```

### `screenshot-cli list`

List captured screenshots.

**Options:**
- `--output, -o` - Screenshots directory (default: docs/images/screenshots)

**Examples:**
```bash
# List all screenshots
screenshot-cli list

# List from custom directory
screenshot-cli list --output docs/images/v0.7.0
```

### `screenshot-cli pages`

Show available dashboard pages.

**Examples:**
```bash
screenshot-cli pages
```

## Python Script Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | Dashboard URL | `http://localhost:8501` |
| `--output` | Output directory | `docs/images/screenshots` |
| `--headless` | Run without UI | `True` |
| `--page` | Specific page to capture | All pages |
| `--theme` | Theme(s) to capture | `both` |

## Output

Screenshots are saved as PNG files with naming pattern:
- `{page_name}_light.png` - Light mode screenshot
- `{page_name}_dark.png` - Dark mode screenshot

Example output:
```
docs/images/screenshots/
├── overview_light.png
├── overview_dark.png
├── data_explorer_light.png
├── data_explorer_dark.png
├── advanced_explorer_light.png
├── advanced_explorer_dark.png
├── analytics_light.png
├── analytics_dark.png
└── ...
```

## Pages Captured

The tool automatically captures screenshots of:

1. **Overview** - Dashboard home page
2. **Data Explorer** - PyGWalker interactive explorer
3. **Advanced Explorer** - SQL query explorer
4. **Analytics** - Built-in analytics and charts
5. **Resources** - Resource allocation views
6. **Infrastructure** - Infrastructure topology
7. **Folder Analysis** - Folder-based analysis

## Customization

### Add Custom Pages

Edit `capture_dashboard_tour()` method in the script:

```python
pages = [
    "Overview",
    "Data Explorer",
    "Your Custom Page",  # Add here
]
```

### Adjust Wait Times

Modify wait times for slow-loading pages:

```python
def wait_for_streamlit(self, timeout: int = 10):  # Increase timeout
    # ...
    time.sleep(2)  # Increase wait time
```

### Custom Resolutions

Change browser window size:

```python
self.chrome_options.add_argument("--window-size=2560,1440")  # 2K resolution
```

## Troubleshooting

### Browser Not Found
```bash
# Install Chrome
# macOS: brew install --cask google-chrome
# Linux: sudo apt-get install google-chrome-stable
```

### ChromeDriver Issues
```bash
# Clear webdriver cache
rm -rf ~/.wdm/

# Reinstall
pip uninstall selenium webdriver-manager
pip install selenium webdriver-manager
```

### Dashboard Not Loading
```bash
# Check if dashboard is running
curl http://localhost:8501

# Check correct port
ps aux | grep streamlit
```

### Theme Toggle Not Working
- Ensure theme toggle button is visible in sidebar
- Check button selector in `toggle_theme()` method
- Try increasing wait time after theme toggle

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Documentation Screenshots

on:
  push:
    branches: [main]

jobs:
  screenshots:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tools/requirements-screenshots.txt
      
      - name: Start dashboard
        run: |
          streamlit run src/dashboard/app.py &
          sleep 10
      
      - name: Capture screenshots
        run: python tools/screenshot_dashboard.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: screenshots
          path: docs/images/screenshots/
```

## Best Practices

1. **Always test locally first** before running in CI/CD
2. **Use headless mode** for automated environments
3. **Increase timeouts** if pages load slowly
4. **Verify screenshots** after capture for quality
5. **Version screenshots** by output directory (e.g., `docs/images/v0.7.0/`)

## Advanced Features

### Full Page Screenshots

```python
# Capture full scrollable page
screenshotter.capture_screenshot("page_name", full_page=True)
```

### Custom Workflows

```python
from tools.screenshot_dashboard import DashboardScreenshotter

# Create custom capture workflow
screenshotter = DashboardScreenshotter(
    base_url="http://localhost:8501",
    output_dir="custom/path"
)

screenshotter.start_browser()
screenshotter.driver.get("http://localhost:8501")
screenshotter.wait_for_streamlit()

# Custom navigation and capture
screenshotter.navigate_to_page("Overview")
screenshotter.capture_screenshot("custom_overview")

screenshotter.stop_browser()
```

## License

Part of the inv-vmware-opa project. See main LICENSE file.
