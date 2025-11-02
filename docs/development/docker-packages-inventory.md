# Docker Image Package Inventory

## Original Dockerfile (vmware-inventory-dashboard:v0.7.2)

**Image Size:** 859MB  
**Python Version:** 3.12  
**Total Packages:** 176

## Complete Package List

```
Faker==37.12.0
GitPython==3.1.45
Jinja2==3.1.6
Markdown==3.9
MarkupSafe==3.0.3
PyJWT==2.10.1
PyYAML==6.0.3
Pygments==2.19.2
SQLAlchemy==2.0.44
altair==5.5.0
altex==0.2.0
annotated-types==0.7.0
anywidget==0.9.18
appdirs==1.4.4
arrow==1.4.0
asn1crypto==1.5.1
astor==0.8.1
asttokens==3.0.0
attrs==25.4.0
backoff==2.2.1
beautifulsoup4==4.14.2
blinker==1.9.0
boto3==1.40.64
botocore==1.40.64
cachetools==6.2.1
certifi==2025.10.5
cffi==2.0.0
charset-normalizer==3.4.4
click==8.3.0
cloudpickle==3.1.1
comm==0.2.3
contourpy==1.3.3
cryptography==46.0.3
cycler==0.12.1
dateutils==0.6.12
decorator==5.2.1
duckdb==1.4.1
entrypoints==0.4
et_xmlfile==2.0.0
executing==2.2.1
favicon==0.7.0
filelock==3.20.0
fonttools==4.60.1
gitdb==4.0.12
greenlet==3.2.4
gw_dsl_parser==********
htbuilder==0.9.0
idna==3.11
importlib_resources==6.5.2
inv-vmware-opa==0.7.2
ipylab==1.0.0
ipython==9.6.0
ipython_pygments_lexers==1.1.1
ipywidgets==8.1.8
jedi==0.19.2
jmespath==1.0.1
jsonschema-specifications==2025.9.1
jsonschema==4.25.1
jupyterlab_widgets==3.0.16
kanaries_track==0.0.5
kiwisolver==1.4.9
lxml==6.0.2
markdown-it-py==4.0.0
markdownlit==0.0.7
matplotlib-inline==0.2.1
matplotlib==3.10.7
mdurl==0.1.2
monotonic==1.6
narwhals==2.10.1
numpy==2.3.4
openpyxl==3.1.5
packaging==25.0
pandas==2.3.3
parso==0.8.5
pexpect==4.9.0
pillow==12.0.0
pip==25.0.1
platformdirs==4.5.0
plotly==6.3.1
prometheus_client==0.23.1
prompt_toolkit==3.0.52
protobuf==6.31.1
psutil==7.1.3
psygnal==0.15.0
ptyprocess==0.7.0
pure_eval==0.2.3
pyOpenSSL==25.3.0
pyarrow==21.0.0
pycparser==2.23
pydantic==2.12.3
pydantic_core==2.41.4
pydeck==0.9.1
pygwalker==********
pymdown-extensions==10.16.1
pyparsing==3.2.5
python-dateutil==2.9.0.post0
pytz==2025.2
quickjs==1.19.4
referencing==0.37.0
requests==2.32.5
rich==13.9.4
rpds-py==0.28.0
s3transfer==0.14.0
segment-analytics-python==2.2.3
setuptools==80.9.0
six==1.17.0
smmap==5.0.2
snowflake-connector-python==4.0.0
snowflake-snowpark-python==1.42.0
sortedcontainers==2.4.0
soupsieve==2.8
sqlglot==27.29.0
st-annotated-text==4.0.2
st-theme==1.2.3
stack-data==0.6.3
streamlit-avatar==0.1.3
streamlit-camera-input-live==0.2.0
streamlit-card==1.0.2
streamlit-embedcode==0.1.2
streamlit-extras==0.7.8
streamlit-image-coordinates==0.4.0
streamlit-keyup==0.3.0
streamlit-notify==0.3.1
streamlit-toggle-switch==1.0.2
streamlit-vertical-slider==2.5.5
streamlit==1.51.0
streamlit_faker==0.0.4
tabulate==0.9.0
tenacity==9.1.2
toml==0.10.2
tomlkit==0.13.3
tornado==6.5.2
traitlets==5.14.3
typing-inspection==0.4.2
typing_extensions==4.15.0
tzdata==2025.2
tzlocal==5.3.1
urllib3==2.5.0
uv==0.5.18
validators==0.35.0
wasmtime==38.0.0
watchdog==6.0.0
wcwidth==0.2.14
wheel==0.45.1
widgetsnbextension==4.0.15
xlsxwriter==3.2.9
```

## Package Categories

### Core Application (Direct Dependencies)
- `inv-vmware-opa==0.7.2` - Main application
- `click==8.3.0` - CLI framework
- `openpyxl==3.1.5` - Excel file handling
- `pandas==2.3.3` - Data manipulation
- `SQLAlchemy==2.0.44` - Database ORM
- `xlsxwriter==3.2.9` - Excel writing
- `tabulate==0.9.0` - Table formatting
- `rich==13.9.4` - Rich text formatting (added for anonymize command)

### Dashboard Framework (streamlit + extras)
- `streamlit==1.51.0` - Main dashboard framework
- `streamlit-extras==0.7.8` - Additional Streamlit components
- `streamlit-avatar==0.1.3`
- `streamlit-camera-input-live==0.2.0`
- `streamlit-card==1.0.2`
- `streamlit-embedcode==0.1.2`
- `streamlit-image-coordinates==0.4.0`
- `streamlit-keyup==0.3.0`
- `streamlit-notify==0.3.1`
- `streamlit-toggle-switch==1.0.2`
- `streamlit-vertical-slider==2.5.5`
- `streamlit_faker==0.0.4`
- `st-annotated-text==4.0.2`
- `st-theme==1.2.3`

### Visualization & Data Analysis
- `plotly==6.3.1` - Interactive plotting
- `pygwalker==********` - Visual data exploration (requires quickjs)
- `matplotlib==3.10.7` - Static plotting
- `altair==5.5.0` - Declarative visualization
- `pydeck==0.9.1` - Deck.gl for maps

### Data Processing
- `numpy==2.3.4` - Numerical computing
- `pyarrow==21.0.0` - Arrow columnar format
- `duckdb==1.4.1` - Embedded analytical database
- `sqlglot==27.29.0` - SQL parser and transpiler

### Compiled Extensions (Require GCC)
- `quickjs==1.19.4` ⚠️ - JavaScript engine (C extension)
- `duckdb==1.4.1` ⚠️ - May require compilation
- `pyarrow==21.0.0` ⚠️ - Arrow C++ bindings
- `cryptography==46.0.3` ⚠️ - OpenSSL bindings
- `lxml==6.0.2` ⚠️ - XML parser (libxml2)
- `Pillow==12.0.0` ⚠️ - Image processing
- `cffi==2.0.0` ⚠️ - C Foreign Function Interface
- `greenlet==3.2.4` ⚠️ - Lightweight coroutines
- `psutil==7.1.3` ⚠️ - System utilities
- `wasmtime==38.0.0` ⚠️ - WebAssembly runtime

### Cloud Integrations
- `snowflake-connector-python==4.0.0` - Snowflake database
- `snowflake-snowpark-python==1.42.0` - Snowflake data processing
- `boto3==1.40.64` - AWS SDK
- `botocore==1.40.64` - AWS core functionality
- `s3transfer==0.14.0` - S3 transfer utilities

### Python Interactive Environment
- `ipython==9.6.0` - Enhanced Python shell
- `ipywidgets==8.1.8` - Interactive widgets
- `ipylab==1.0.0` - JupyterLab integration
- `jupyterlab_widgets==3.0.16` - Jupyter widgets
- `widgetsnbextension==4.0.15` - Notebook widget extension

### Security & Cryptography
- `cryptography==46.0.3` - Cryptographic recipes
- `pyOpenSSL==25.3.0` - OpenSSL wrapper
- `PyJWT==2.10.1` - JSON Web Token
- `asn1crypto==1.5.1` - ASN.1 parsing
- `certifi==2025.10.5` - Root certificates

### Utilities & Supporting Libraries
- `requests==2.32.5` - HTTP library
- `urllib3==2.5.0` - HTTP client
- `Jinja2==3.1.6` - Template engine
- `Markdown==3.9` - Markdown parser
- `PyYAML==6.0.3` - YAML parser
- `toml==0.10.2` - TOML parser
- `attrs==25.4.0` - Classes without boilerplate
- `pydantic==2.12.3` - Data validation
- `validators==0.35.0` - Data validators
- `tenacity==9.1.2` - Retry library
- `backoff==2.2.1` - Backoff/retry decorator

### Development Tools
- `uv==0.5.18` - Fast Python package installer
- `pip==25.0.1` - Package installer
- `setuptools==80.9.0` - Build system
- `wheel==0.45.1` - Built package format

### Version Control & Git
- `GitPython==3.1.45` - Git library
- `gitdb==4.0.12` - Git database
- `smmap==5.0.2` - Memory-mapped file support

### Testing & Mock Data
- `Faker==37.12.0` - Fake data generator

### File Monitoring
- `watchdog==6.0.0` - File system event monitoring

### Date/Time Utilities
- `python-dateutil==2.9.0.post0` - Date extensions
- `pytz==2025.2` - Timezone definitions
- `tzdata==2025.2` - Timezone database
- `tzlocal==5.3.1` - Local timezone
- `arrow==1.4.0` - Date/time handling
- `dateutils==0.6.12` - Date utilities

### Data Schema & Validation
- `jsonschema==4.25.1` - JSON schema validation
- `jsonschema-specifications==2025.9.1` - JSON schema specs
- `referencing==0.37.0` - JSON reference resolution
- `rpds-py==0.28.0` - Persistent data structures

### Analytics & Tracking
- `segment-analytics-python==2.2.3` - Segment analytics
- `kanaries_track==0.0.5` - Kanaries tracking (pygwalker)
- `prometheus_client==0.23.1` - Prometheus metrics

### Text Processing & Markdown
- `Pygments==2.19.2` - Syntax highlighting
- `markdown-it-py==4.0.0` - Markdown parser
- `markdownlit==0.0.7` - Markdown in Streamlit
- `pymdown-extensions==10.16.1` - Markdown extensions
- `mdurl==0.1.2` - URL utilities for markdown

### UI/UX Components
- `htbuilder==0.9.0` - HTML builder
- `favicon==0.7.0` - Favicon support
- `beautifulsoup4==4.14.2` - HTML parser
- `soupsieve==2.8` - CSS selectors
- `lxml==6.0.2` - XML/HTML parser

### Core Python Extensions
- `typing_extensions==4.15.0` - Typing backports
- `typing-inspection==0.4.2` - Runtime type inspection
- `importlib_resources==6.5.2` - Resource access
- `platformdirs==4.5.0` - Platform directories

### Miscellaneous
- `blinker==1.9.0` - Signal/event system
- `cloudpickle==3.1.1` - Extended pickle
- `filelock==3.20.0` - File locking
- `monotonic==1.6` - Monotonic time
- `six==1.17.0` - Python 2/3 compatibility
- `protobuf==6.31.1` - Protocol buffers
- `tornado==6.5.2` - Async networking
- `sortedcontainers==2.4.0` - Sorted collections

## Size Impact by Category

| Category | Estimated Size | Key Contributors |
|----------|----------------|------------------|
| Streamlit + Extensions | ~150MB | streamlit, plotly, altair |
| pygwalker Dependencies | ~100MB | pygwalker, quickjs, duckdb |
| Data Processing | ~80MB | pandas, numpy, pyarrow |
| Visualization | ~70MB | matplotlib, plotly |
| Cloud Integrations | ~60MB | snowflake, boto3 |
| Python Environment | ~50MB | ipython, ipywidgets |
| Security/Crypto | ~40MB | cryptography, pyOpenSSL |
| Core App | ~30MB | SQLAlchemy, openpyxl |
| WebAssembly | ~30MB | wasmtime |
| Utilities | ~100MB | All other packages |
| **Total** | **~710MB** | Python packages only |

*Note: Base image (python:3.12-slim) adds ~150MB*

## Packages Requiring Compilation

These packages contain C/C++ extensions and need gcc in the builder stage:

1. **quickjs** - JavaScript engine (pygwalker dependency)
2. **duckdb** - Analytical database
3. **pyarrow** - Apache Arrow
4. **cryptography** - OpenSSL bindings
5. **lxml** - libxml2/libxslt
6. **Pillow** - Image processing (libjpeg, libpng)
7. **cffi** - Foreign function interface
8. **greenlet** - Coroutines
9. **psutil** - System utilities
10. **wasmtime** - WebAssembly runtime
11. **numpy** - Usually has wheels but can compile
12. **pydantic_core** - Rust-based core

## Reduction Opportunities

### Remove Snowflake (~60MB savings)
If not using Snowflake:
```toml
# Remove from dependencies
snowflake-connector-python
snowflake-snowpark-python
```

### Make pygwalker Optional (~100MB savings)
```toml
[project.optional-dependencies]
dashboard-advanced = ["pygwalker>=0.4.0,<1.0.0"]
```

### Remove Jupyter Components (~30MB savings)
If not using notebooks:
```toml
# These come as pygwalker dependencies
ipython, ipywidgets, ipylab, jupyterlab_widgets
```

### Total Potential Savings: ~190MB (22%)
**Optimized size: ~670MB** (from 859MB)

## Verification Commands

```bash
# List all packages
docker run --rm --entrypoint /bin/sh vmware-inventory-dashboard:v0.7.2 -c "python -m pip list --format=freeze"

# Count packages
docker run --rm --entrypoint /bin/sh vmware-inventory-dashboard:v0.7.2 -c "python -m pip list --format=freeze | wc -l"

# Find compiled extensions
docker run --rm --entrypoint /bin/sh vmware-inventory-dashboard:v0.7.2 -c "find /usr/local/lib/python3.12/site-packages -name '*.so' | wc -l"

# Check specific package
docker run --rm --entrypoint /bin/sh vmware-inventory-dashboard:v0.7.2 -c "python -m pip show streamlit"
```

## Comparison with pipx Approach

| Metric | Original Dockerfile | pipx + mounts |
|--------|---------------------|---------------|
| **Size** | 859MB | 1.02GB |
| **Packages** | 176 | 176 (same) |
| **Complexity** | Low | High |
| **Build Time** | ~2m30s | ~3m00s |
| **Maintainability** | Easy | Complex |

**Conclusion:** Original Dockerfile is optimal for this use case.
