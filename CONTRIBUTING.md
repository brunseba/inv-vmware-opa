# Contributing to inv-vmware-opa

Thank you for your interest in contributing to inv-vmware-opa! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/inv-vmware-opa.git
   cd inv-vmware-opa
   ```

2. **Install Dependencies**
   ```bash
   # Install all dependencies including dev tools
   uv sync --all-extras --dev
   
   # Or with pip
   pip install -e ".[all,dev]"
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

4. **Verify Setup**
   ```bash
   # Run tests
   uv run pytest
   
   # Check formatting
   uv run black --check src tests
   
   # Run linter
   uv run flake8 src tests
   ```

## 📝 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add docstrings to functions and classes
- Keep functions focused and small

### 3. Write Tests

We aim for high test coverage on core functionality:

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_your_feature.py -v
```

**Testing Guidelines:**
- Write unit tests for all new functions
- Add integration tests for complex features
- Use fixtures for common test setup
- Mock external dependencies (database, files, network)
- Aim for >90% coverage on new code

### 4. Update Documentation

- Add docstrings to new functions/classes
- Update README.md if adding new features
- Add examples if applicable
- Update CHANGELOG.md following Keep a Changelog format

### 5. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in loader"
git commit -m "docs: update installation guide"
git commit -m "test: add tests for label service"
```

**Commit Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks
- `ci:` CI/CD changes

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title following conventional commit format
- Description of changes
- Link to related issues
- Screenshots (if UI changes)

## 🧪 Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_models.py

# Specific test class
uv run pytest tests/test_models.py::TestVirtualMachineModel

# Specific test function
uv run pytest tests/test_models.py::TestVirtualMachineModel::test_create_vm

# With coverage
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Skip slow tests
uv run pytest -m "not slow"

# Skip integration tests
uv run pytest -m "not integration"
```

### Writing Tests

**Example Unit Test:**
```python
def test_create_label(mock_session):
    """Test creating a new label."""
    service = LabelService(mock_session)
    mock_session.query.return_value.filter.return_value.first.return_value = None
    
    result = service.create_label("env", "prod", "Production")
    
    assert result.key == "env"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
```

**Example Integration Test:**
```python
@pytest.mark.integration
def test_load_excel_file(tmp_path):
    """Test loading VM data from Excel file."""
    # Create test Excel file
    test_file = tmp_path / "test.xlsx"
    # ... setup test data
    
    records = load_excel_to_db(test_file, "sqlite:///:memory:")
    
    assert records > 0
```

## 🎨 Code Style

### Python Style Guide

We follow PEP 8 with some modifications:
- Line length: 120 characters
- Use Black for formatting
- Use Flake8 for linting

```bash
# Format code
uv run black src tests

# Check formatting
uv run black --check src tests

# Run linter
uv run flake8 src tests
```

### Imports

Organize imports in this order:
1. Standard library
2. Third-party packages
3. Local application imports

```python
import os
from datetime import datetime

import click
from sqlalchemy import create_engine

from src.models import VirtualMachine
from src.services import LabelService
```

### Naming Conventions

- **Functions/variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_leading_underscore`

## 📚 Documentation

### Docstrings

Use Google-style docstrings:

```python
def create_label(key: str, value: str, description: str = None) -> Label:
    """Create a new label definition.
    
    Args:
        key: Label key (e.g., "environment")
        value: Label value (e.g., "production")
        description: Optional label description
        
    Returns:
        The created Label instance
        
    Raises:
        ValueError: If key or value is empty
    """
    pass
```

### Building Documentation

```bash
# Serve docs locally
uv run mkdocs serve

# Build docs
uv run mkdocs build

# View at http://127.0.0.1:8000
```

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description:** Clear description of the issue
2. **Steps to Reproduce:** Detailed steps
3. **Expected Behavior:** What should happen
4. **Actual Behavior:** What actually happens
5. **Environment:**
   - OS version
   - Python version
   - inv-vmware-opa version
6. **Logs:** Relevant error messages or logs

## 💡 Suggesting Features

Feature requests are welcome! Please include:

1. **Use Case:** Why is this feature needed?
2. **Proposed Solution:** How should it work?
3. **Alternatives:** Other approaches considered
4. **Additional Context:** Screenshots, examples, etc.

## 🔍 Code Review Process

All submissions require review:

1. **Automated Checks:** Must pass CI/CD
   - Tests pass
   - Code coverage meets threshold
   - Linting passes
   - Pre-commit hooks pass

2. **Manual Review:** Maintainer will review
   - Code quality
   - Test coverage
   - Documentation
   - Design decisions

3. **Feedback:** Address review comments
4. **Approval:** Once approved, maintainer will merge

## 🏗️ Project Structure

```
inv-vmware-opa/
├── src/                    # Source code
│   ├── cli.py             # Main CLI entry point
│   ├── commands/          # CLI command modules
│   ├── dashboard/         # Streamlit dashboard
│   ├── models.py          # Database models
│   ├── services/          # Business logic services
│   ├── loader.py          # Excel data loading
│   └── report_generator.py
├── tests/                 # Test files
│   ├── test_models.py
│   ├── test_services.py
│   └── ...
├── docs/                  # Documentation
├── pyproject.toml         # Project configuration
├── README.md
└── CHANGELOG.md
```

## 📦 Optional Dependencies

The project uses optional dependencies:

```bash
# Install CLI only (minimal)
pip install inv-vmware-opa

# Install with dashboard
pip install inv-vmware-opa[dashboard]

# Install with reports
pip install inv-vmware-opa[reports]

# Install everything
pip install inv-vmware-opa[all]

# Development
pip install inv-vmware-opa[all,dev]
```

## 🔒 Security

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email the maintainers directly
3. Provide detailed information
4. Allow time for a fix before public disclosure

## 📋 Checklist Before Submitting PR

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Code formatted with Black
- [ ] Linting passes (Flake8)
- [ ] Pre-commit hooks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow conventional commits
- [ ] PR description is clear and complete

## 🎯 Areas Needing Help

We especially welcome contributions in:

- [ ] Test coverage for dashboard pages
- [ ] Test coverage for report generator
- [ ] Performance optimization for large datasets
- [ ] Additional export formats
- [ ] Internationalization (i18n)
- [ ] Documentation improvements
- [ ] Bug fixes

## 💬 Getting Help

- **Questions:** Open a GitHub Discussion
- **Bugs:** Open a GitHub Issue
- **Chat:** Check if there's a community chat channel

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make this project better. Thank you for taking the time to contribute!
