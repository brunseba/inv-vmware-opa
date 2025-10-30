# Quick Reference Card 🚀

## Installation

```bash
# Minimal CLI only
pip install inv-vmware-opa

# With dashboard
pip install inv-vmware-opa[dashboard]

# With reports
pip install inv-vmware-opa[reports]

# Everything
pip install inv-vmware-opa[all]

# Development (from source)
uv pip install -e ".[all]" --group dev --group lint --group security
```

## Testing

```bash
# Run all tests
pytest

# Parallel execution (2-4x faster)
pytest -n auto

# With coverage
pytest --cov

# By marker
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest -m smoke          # Quick sanity checks
pytest -m "not slow"     # Skip slow tests
pytest -m "not vmware"   # Skip VMware API tests

# Enable logging
pytest --log-cli-level=DEBUG

# Specific file/test
pytest tests/test_cli.py
pytest tests/test_cli.py::test_function
```

## Linting & Formatting

```bash
# Ruff (fast!)
ruff check .              # Check all files
ruff check --fix .        # Auto-fix issues
ruff check src/           # Check specific directory
ruff format .             # Format code

# Type checking
mypy src/                 # Check types
mypy --strict src/        # Strict mode

# Security scanning
bandit -r src/            # Scan for vulnerabilities

# All checks
ruff check . && mypy src/ && bandit -r src/
```

## Coverage

```bash
# Generate reports
pytest --cov=src

# Specific format
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=json
pytest --cov=src --cov-report=lcov

# View HTML report
open htmlcov/index.html

# Parse JSON
cat coverage.json | jq '.totals.percent_covered'
```

## Test Markers

| Marker | Purpose | Usage |
|--------|---------|-------|
| `unit` | Unit tests | `pytest -m unit` |
| `integration` | Integration tests | `pytest -m integration` |
| `e2e` | End-to-end tests | `pytest -m e2e` |
| `slow` | Slow tests | `pytest -m "not slow"` |
| `smoke` | Quick sanity checks | `pytest -m smoke` |
| `database` | Requires database | `pytest -m database` |
| `vmware` | VMware API interaction | `pytest -m "not vmware"` |
| `dashboard` | Dashboard functionality | `pytest -m dashboard` |

## Git Workflow

```bash
# Commit with conventional commits
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update README"
git commit -m "test: add unit tests"
git commit -m "refactor: improve code structure"

# Run pre-commit hooks
pre-commit run --all-files

# Tag for release
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

## Common Workflows

### Local Development
```bash
# Setup
git clone <repo>
cd inv-vmware-opa
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e ".[all]" --group dev --group lint

# Work cycle
ruff check --fix .         # Fix linting issues
pytest -n auto             # Run tests
git commit -m "feat: ..."  # Commit changes
```

### Before Committing
```bash
ruff check --fix .
pytest
git add .
git commit -m "..."
```

### CI/CD Simulation
```bash
# What CI will run
pytest -m smoke                    # Smoke tests
pytest -m unit -n auto            # Unit tests (parallel)
pytest -m integration             # Integration tests
ruff check .                      # Linting
mypy src/                         # Type checking
bandit -r src/                    # Security scan
```

### Documentation
```bash
# Build docs
mkdocs serve          # Local preview at http://127.0.0.1:8000
mkdocs build          # Build static site
mkdocs gh-deploy      # Deploy to GitHub Pages
```

## Troubleshooting

### Tests failing
```bash
# Run with verbose output
pytest -vv

# Run with full traceback
pytest --tb=long

# Run single test
pytest tests/test_cli.py::test_function -vv

# With logging
pytest --log-cli-level=DEBUG
```

### Coverage incomplete
```bash
# Ensure parallel coverage is enabled
# Check pyproject.toml: [tool.coverage.run] parallel = true

# Combine coverage data if using -n
coverage combine
coverage report
```

### Ruff/mypy errors
```bash
# Show all rules
ruff check . --show-settings

# Ignore specific error
# Add to pyproject.toml [tool.ruff.lint] ignore = [...]

# mypy specific module
mypy --show-error-codes src/cli.py
```

## Environment Variables

```bash
# Database URL
export DATABASE_URL=sqlite:///data/vmware.db

# VMware credentials (use env vars, never hardcode!)
export VMWARE_HOST=vcenter.example.com
export VMWARE_USER=administrator@vsphere.local
export VMWARE_PASSWORD=your-password-here

# Testing
export PYTEST_TIMEOUT=300
export COVERAGE_FILE=.coverage
```

## File Structure

```
inv-vmware-opa/
├── src/                    # Source code
│   ├── cli.py             # CLI entry point
│   ├── models.py          # Database models
│   ├── services/          # Business logic
│   └── dashboard/         # Streamlit app
├── tests/                  # Tests
│   ├── test_cli.py
│   └── conftest.py        # Pytest fixtures
├── docs/                   # Documentation
├── migrations/             # Database migrations
├── pyproject.toml         # Project config (⭐ IMPORTANT!)
├── .pre-commit-config.yaml # Git hooks
├── .gitignore
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CHANGELOG.md
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | **All project configuration** |
| `.pre-commit-config.yaml` | Git hooks |
| `CONTRIBUTING.md` | Developer guide |
| `SECURITY.md` | Security policy |
| `PYPROJECT_ENHANCEMENTS.md` | Detailed tool documentation |

## Configuration Sections

`pyproject.toml` contains:
- ✅ Project metadata (name, version, authors)
- ✅ Dependencies (core, optional, dev, lint, security)
- ✅ Entry points (CLI commands)
- ✅ Pytest configuration
- ✅ Coverage configuration
- ✅ Ruff linting rules
- ✅ mypy type checking
- ✅ Black formatting
- ✅ isort import sorting
- ✅ Bandit security scanning

## Tool Comparison

| Tool | Speed | Purpose |
|------|-------|---------|
| **Ruff** | ⚡️⚡️⚡️ | Linting (replaces flake8, isort, etc.) |
| **pytest-xdist** | ⚡️⚡️⚡️ | Parallel testing (2-4x faster) |
| **mypy** | ⚡️⚡️ | Type checking |
| **Bandit** | ⚡️⚡️ | Security scanning |

## Tips & Tricks

### Run tests faster
```bash
# Parallel + skip slow
pytest -n auto -m "not slow"

# Only failed tests
pytest --lf

# Only unit tests (fastest)
pytest -m unit -n auto
```

### Auto-fix everything
```bash
ruff check --fix .
ruff format .
```

### Watch mode (auto-run tests)
```bash
# Requires pytest-watch
ptw -- -n auto
```

### Coverage badge
```bash
# Generate badge for README
coverage-badge -o coverage.svg
```

### Pre-commit on all files
```bash
pre-commit run --all-files
```

## Links

- 📖 **Full Documentation**: [PYPROJECT_ENHANCEMENTS.md](PYPROJECT_ENHANCEMENTS.md)
- 🤝 **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- 🔒 **Security**: [SECURITY.md](SECURITY.md)
- 📝 **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- 🐛 **Issues**: https://github.com/brunseba/inv-vmware-opa/issues

---

**Need help?** Check [PYPROJECT_ENHANCEMENTS.md](PYPROJECT_ENHANCEMENTS.md) for detailed explanations!
