# Technical Debt & pyproject.toml Review

**Date:** 2025-10-30  
**Project:** inv-vmware-opa v0.5.0  
**Python:** >=3.10

## 📋 Executive Summary

**Overall Health:** 🟢 Good  
**Critical Issues:** 0  
**High Priority:** 3  
**Medium Priority:** 5  
**Low Priority:** 4

The project is generally well-structured with modern Python tooling (uv, pytest, pre-commit). Main areas for improvement are dependency management, missing documentation, and test coverage gaps.

---

## 🔍 pyproject.toml Analysis

### ✅ What's Good

1. **Modern Python** - Requires Python >=3.10
2. **Clear Dependencies** - Well-defined dependency list
3. **Build System** - Uses modern setuptools
4. **CLI Entry Point** - Properly configured
5. **Dev Dependencies** - Separated dev tools
6. **Package Structure** - Correct package discovery

### ⚠️ Issues & Recommendations

#### 1. Missing Dependency Version Constraints (HIGH)

**Current:**
```toml
dependencies = [
    "click>=8.3.0",
    "pandas>=2.3.3",
    # ...
]
```

**Problem:** Only lower bounds specified. No upper bounds = future breaking changes.

**Recommendation:**
```toml
dependencies = [
    "click>=8.3.0,<9.0.0",
    "pandas>=2.3.3,<3.0.0",
    "sqlalchemy>=2.0.44,<3.0.0",
    "streamlit>=1.40.0,<2.0.0",
    "plotly>=5.24.0,<6.0.0",
    # ...
]
```

**Impact:** Prevents breaking changes from major version bumps

#### 2. Missing Optional Dependencies (MEDIUM)

**Current:** All dependencies are required

**Recommendation:** Group dependencies by feature:
```toml
[project.optional-dependencies]
dashboard = [
    "streamlit>=1.40.0,<2.0.0",
    "plotly>=5.24.0,<6.0.0",
    "streamlit-extras>=0.7.8,<1.0.0",
]
reports = [
    "reportlab>=4.4.4,<5.0.0",
    "pillow>=11.3.0,<12.0.0",
    "matplotlib>=3.10.7,<4.0.0",
]
all = ["inv-vmware-opa[dashboard,reports]"]
```

**Benefits:**
- CLI-only users don't need heavy UI dependencies
- Faster installation for CI/CD
- Better separation of concerns

#### 3. Missing Faker in Dev Dependencies (LOW)

**Current:** Tests use Faker but it's not in dev dependencies

**Issue:** `pytest-Faker-37.12.0` is installed but not listed

**Recommendation:**
```toml
[dependency-groups]
dev = [
    "pytest>=8.4.2",
    "pytest-cov>=7.0.0",
    "pytest-faker>=2.0.0",  # Add this
    "mkdocs>=1.6.1",
    # ...
]
```

#### 4. Missing Project Metadata (MEDIUM)

**Current:** Minimal metadata

**Recommendation:**
```toml
[project]
name = "inv-vmware-opa"
version = "0.5.0"
description = "VMware inventory management CLI with backup/restore and label quality analysis"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["vmware", "inventory", "cli", "dashboard", "analytics"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: System Administrators",
    "Topic :: System :: Systems Administration",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.urls]
Homepage = "https://github.com/brunseba/inv-vmware-opa"
Documentation = "https://github.com/brunseba/inv-vmware-opa/docs"
Repository = "https://github.com/brunseba/inv-vmware-opa"
Issues = "https://github.com/brunseba/inv-vmware-opa/issues"
Changelog = "https://github.com/brunseba/inv-vmware-opa/blob/main/CHANGELOG.md"
```

#### 5. pytest Configuration Missing (MEDIUM)

**Current:** No pytest configuration in pyproject.toml

**Recommendation:**
```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "-v"
]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

#### 6. Coverage Configuration Missing (LOW)

**Recommendation:**
```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "tests/*",
    "src/dashboard/*",  # UI code hard to test
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
precision = 2
show_missing = true
skip_covered = false

[tool.coverage.html]
directory = "htmlcov"
```

#### 7. Black/Flake8 Configuration (LOW)

**Recommendation:** Add consistency with pre-commit:
```toml
[tool.black]
line-length = 120
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''

[tool.flake8]
max-line-length = 120
extend-ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "dist", "build", ".venv"]
```

---

## 🐛 Technical Debt Inventory

### High Priority (3 items)

#### 1. Dashboard UI Code Untested (0% coverage)
- **Location:** `src/dashboard/pages/*.py`
- **Lines:** ~2,500 lines
- **Impact:** High - no validation of UI logic
- **Effort:** Medium - requires Streamlit testing framework
- **Recommendation:**
  - Add data processing tests (DONE ✅)
  - Add integration tests with Streamlit testing
  - Document manual testing procedures

#### 2. Report Generator Untested (0% coverage)
- **Location:** `src/report_generator.py`
- **Lines:** 594 lines
- **Impact:** High - critical feature for users
- **Effort:** Medium - mock PDF generation
- **Recommendation:**
  - Test data aggregation logic
  - Test chart data preparation
  - Mock ReportLab calls
  - Validate report structure

#### 3. Missing Dependency Version Locks
- **Impact:** High - production stability risk
- **Effort:** Low - just add constraints
- **Recommendation:** Add upper bounds to all dependencies (see above)

### Medium Priority (5 items)

#### 1. CLI Main Entry Point (451 lines, 0% coverage)
- **Location:** `src/cli.py`
- **Impact:** Medium - main entry point
- **Effort:** Low-Medium
- **Recommendation:**
  - Test command registration
  - Test option parsing
  - Mock actual command execution

#### 2. Incomplete CLI Label Commands (42% coverage)
- **Location:** `src/commands/label.py`
- **Lines Missing:** 252 lines
- **Impact:** Medium - folder operations untested
- **Effort:** Low
- **Recommendation:**
  - Add tests for folder label commands
  - Add tests for bulk operations
  - Add tests for sync commands

#### 3. Loader Integration Tests Missing
- **Location:** `src/loader.py`
- **Coverage:** 59% (31 lines missing)
- **Impact:** Medium - data import reliability
- **Effort:** Medium
- **Recommendation:**
  - Add full Excel loading integration test
  - Test error handling for malformed files
  - Test large file handling

#### 4. Missing CONTRIBUTING.md
- **Impact:** Medium - contributor confusion
- **Effort:** Low
- **Recommendation:** Create contributor guidelines

#### 5. No CI/CD Pipeline
- **Impact:** Medium - manual testing burden
- **Effort:** Medium
- **Recommendation:**
  - Add GitHub Actions workflow
  - Run tests on PR
  - Check coverage
  - Lint and format check

### Low Priority (4 items)

#### 1. Missing Type Hints
- **Location:** Various files
- **Impact:** Low - but improves IDE support
- **Effort:** Medium
- **Recommendation:**
  - Add `mypy` to dev dependencies
  - Gradually add type hints
  - Configure mypy in pyproject.toml

#### 2. No Security Scanning
- **Impact:** Low - but important for production
- **Effort:** Low
- **Recommendation:**
  - Add `bandit` to pre-commit
  - Add `safety` for dependency scanning
  - Add GitHub Dependabot

#### 3. Documentation Gaps
- **Location:** Various
- **Issues:**
  - API documentation missing
  - Architecture diagrams missing
  - Deployment guide missing
- **Effort:** Medium

#### 4. No Performance Tests
- **Impact:** Low - but helpful for large inventories
- **Effort:** Medium
- **Recommendation:**
  - Add pytest-benchmark
  - Test query performance
  - Test Excel loading speed

---

## 📊 Dependency Analysis

### Current Dependencies (11 production)

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| click | >=8.3.0 | CLI framework | ✅ Good |
| openpyxl | >=3.1.5 | Excel reading | ✅ Good |
| pandas | >=2.3.3 | Data analysis | ⚠️ Heavy |
| sqlalchemy | >=2.0.44 | Database ORM | ✅ Good |
| streamlit | >=1.40.0 | Dashboard UI | ⚠️ Heavy |
| plotly | >=5.24.0 | Charts | ⚠️ Heavy |
| xlsxwriter | >=3.2.0 | Excel writing | ✅ Good |
| streamlit-extras | >=0.7.8 | UI components | ✅ Good |
| watchdog | >=6.0.0 | File watching | ⚠️ Unused? |
| reportlab | >=4.4.4 | PDF generation | ✅ Good |
| pillow | >=11.3.0 | Image handling | ✅ Good |
| matplotlib | >=3.10.7 | Charts for PDF | ✅ Good |
| tabulate | >=0.9.0 | Table formatting | ✅ Good |

### Recommendations:

1. **Make optional:** streamlit, plotly, streamlit-extras (dashboard-only)
2. **Make optional:** reportlab, pillow, matplotlib (reports-only)
3. **Consider removing:** watchdog (if unused)
4. **Add:** python-dotenv (for configuration)

---

## 🔒 Security Considerations

### Current State
- ✅ Pre-commit hook checks for private keys
- ❌ No dependency vulnerability scanning
- ❌ No security policy (SECURITY.md)
- ❌ No input validation documentation

### Recommendations

1. **Add Security Scanning**
```toml
[dependency-groups]
security = [
    "bandit>=1.7.0",
    "safety>=3.0.0",
]
```

2. **Add to pre-commit:**
```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.7
  hooks:
    - id: bandit
      args: ['-c', 'pyproject.toml']
```

3. **Create SECURITY.md:**
- Vulnerability reporting process
- Security best practices
- Database security recommendations

---

## 🚀 Recommended Action Plan

### Phase 1: Quick Wins (1-2 days)
1. ✅ Add dependency version upper bounds
2. ✅ Add pytest configuration to pyproject.toml
3. ✅ Add coverage configuration
4. ✅ Create CONTRIBUTING.md
5. ✅ Add security scanning to pre-commit

### Phase 2: Testing (2-3 days)
1. ⏳ Complete CLI command tests (folder operations)
2. ⏳ Add loader integration tests
3. ⏳ Add report generator tests (at least data preparation)
4. ⏳ Document manual testing procedures for dashboard

### Phase 3: Infrastructure (1-2 days)
1. ⏳ Setup GitHub Actions CI/CD
2. ⏳ Add Dependabot configuration
3. ⏳ Setup coverage tracking (codecov.io)
4. ⏳ Add status badges to README

### Phase 4: Quality (2-3 days)
1. ⏳ Add type hints to critical modules
2. ⏳ Setup mypy
3. ⏳ Add performance benchmarks
4. ⏳ Complete API documentation

---

## 📈 Metrics & Goals

### Current State
- **Test Coverage:** 13% overall (98% for core services)
- **Test Count:** 151 tests
- **Code Quality:** Good (pre-commit hooks)
- **Documentation:** Basic (README + MkDocs)

### Target State (3-6 months)
- **Test Coverage:** 60-70% overall
- **Test Count:** 200+ tests
- **Code Quality:** Excellent (type hints + mypy)
- **Documentation:** Comprehensive (API docs + guides)
- **CI/CD:** Fully automated
- **Security:** Vulnerability scanning active

---

## 🎯 Priority Matrix

```
High Impact / Low Effort:
- Add dependency constraints ✅
- Add pytest config ✅
- Create CONTRIBUTING.md
- Setup CI/CD

High Impact / High Effort:
- Report generator tests
- Dashboard integration tests
- Type hints across codebase

Low Impact / Low Effort:
- Add security scanning
- Add status badges
- Update README

Low Impact / High Effort:
- Full UI testing with Streamlit
- Performance optimization
- Internationalization
```

---

## 💡 Conclusion

The project is in **good health** with modern tooling and solid core test coverage (98% for services). Main technical debt is:

1. **Missing test coverage** for UI and report generation (acceptable for now)
2. **Loose dependency constraints** (easy fix)
3. **Missing CI/CD pipeline** (important for scaling)

**Recommendation:** Follow Phase 1 immediately, then prioritize based on user needs and team capacity.

---

**Last Updated:** 2025-10-30  
**Next Review:** 2025-12-30 or after v1.0.0 release
