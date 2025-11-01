# pyproject.toml Phase 3 Enhancements Summary

**Date:** 2025-10-30  
**Phase:** 3 - Advanced Tooling & Profiling  
**Status:** ✅ Complete

---

## 🎯 Overview

Phase 3 adds advanced development tools focused on performance profiling, code quality analysis, and documentation management. This phase completes the professional development environment setup.

---

## 📦 What Was Added

### 1. **New Dependency Group: `performance`**

Added professional profiling tools for performance optimization:

```toml
[dependency-groups]
performance = [
    "py-spy>=0.3.0,<1.0.0",      # Sampling profiler (no code changes needed)
    "memray>=1.15.0,<2.0.0",     # Memory profiler by Bloomberg
    "scalene>=1.5.0,<2.0.0",     # CPU+GPU+memory profiler
]
```

**Why These Tools?**

| Tool | Purpose | Key Feature |
|------|---------|-------------|
| **py-spy** | CPU profiling | Zero-overhead sampling, works on running processes |
| **memray** | Memory profiling | Track memory allocations, find leaks |
| **scalene** | Comprehensive | CPU, GPU, memory - all in one with AI-powered suggestions |

**Usage:**
```bash
# Install
uv pip install --group performance

# py-spy: Profile running process
py-spy record -o profile.svg --pid <PID>
py-spy top --pid <PID>

# memray: Track memory
memray run script.py
memray flamegraph memray-results.bin

# scalene: Comprehensive profiling
scalene script.py
```

---

### 2. **Enhanced Testing Dependencies**

```toml
dev = [
    # Existing...
    "pytest-benchmark>=5.1.0,<6.0.0",  # NEW: Performance benchmarking
    "pytest-mock>=3.14.0,<4.0.0",      # NEW: Enhanced mocking
    "mkdocs-mermaid2-plugin>=1.1.0,<2.0.0",  # NEW: Diagram support
]
```

**New Capabilities:**

**pytest-benchmark:**
```python
def test_function_performance(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result == expected
```

**pytest-mock:**
```python
def test_with_mock(mocker):
    mock = mocker.patch('module.function')
    mock.return_value = 42
    assert my_code() == 42
```

**Mermaid Diagrams in Docs:**
```markdown
```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```\n```

---

### 3. **Enhanced Security Tools**

```toml
security = [
    "bandit>=1.7.0,<2.0.0",
    "safety>=3.0.0,<4.0.0",
    "pip-audit>=2.8.0,<3.0.0",  # NEW: Audit dependencies for vulnerabilities
]
```

**pip-audit:**
- Scans dependencies for known vulnerabilities
- Checks against OSV and PyPI databases
- Auto-fix capable with `--fix`

**Usage:**
```bash
pip-audit
pip-audit --fix
pip-audit --format json > audit-report.json
```

---

### 4. **Advanced Linting Tools**

```toml
lint = [
    # Existing ruff, mypy, type stubs...
    "vulture>=2.14.0,<3.0.0",      # NEW: Dead code detection
    "interrogate>=1.7.0,<2.0.0",   # NEW: Docstring coverage
]
```

#### **Vulture - Dead Code Detection**

Finds unused code that can be safely removed:

```toml
[tool.vulture]
min_confidence = 80
paths = ["src", "tests"]
exclude = ["*.venv*", "build/", "dist/"]
ignore_decorators = ["@app.route", "@require_*"]
ignore_names = ["visit_*", "do_*"]
```

**Usage:**
```bash
vulture src/
vulture src/ --min-confidence 90
vulture src/ --sort-by-size
```

**Benefits:**
- Identify unused functions, classes, variables
- Reduce code bloat
- Improve maintainability
- Find typos in variable names

#### **Interrogate - Docstring Coverage**

Measures and enforces docstring coverage:

```toml
[tool.interrogate]
ignore-init-method = true
ignore-init-module = true
ignore-magic = true
fail-under = 50
exclude = ["setup.py", "docs", "build", "tests"]
generate-badge = "."
badge-format = "svg"
```

**Usage:**
```bash
interrogate src/
interrogate -v src/  # Verbose
interrogate --generate-badge docs/
```

**Generates:**
- Coverage percentage
- List of missing docstrings
- SVG badge for README

---

### 5. **Additional Entry Points**

```toml
[project.scripts]
vmware-inv = "src.cli:cli"
vmware-dashboard = "src.dashboard.app:main"      # NEW
vmware-report = "src.report_generator:main"      # NEW

[project.entry-points.console_scripts]
vmware-inv-test = "pytest:main"   # NEW: Quick test runner
vmware-inv-lint = "ruff:main"     # NEW: Quick linter
```

**Benefits:**
- Direct CLI access to dashboard and reports
- Convenient shortcuts for common tasks
- Professional package structure

---

### 6. **Extended Pytest Markers**

```toml
markers = [
    # Existing: integration, slow, unit, e2e, smoke, database, vmware, dashboard
    "performance: marks tests that benchmark performance",  # NEW
    "security: marks security-related tests",              # NEW
    "regression: marks regression tests",                  # NEW
    "wip: marks work-in-progress tests (skip in CI)",     # NEW
    "flaky: marks tests that are occasionally flaky",      # NEW
]
```

**Usage Examples:**

```bash
# Run performance benchmarks
pytest -m performance

# Run security tests
pytest -m security

# Skip WIP tests in CI
pytest -m "not wip"

# Run stable tests only (skip flaky)
pytest -m "not flaky"

# Regression test suite
pytest -m regression
```

**In Test Code:**
```python
@pytest.mark.performance
@pytest.mark.benchmark
def test_query_performance(benchmark):
    result = benchmark(complex_query)
    
@pytest.mark.security
def test_sql_injection_protection():
    # Security test
    
@pytest.mark.wip
@pytest.mark.skip(reason="Feature in development")
def test_new_feature():
    pass
```

---

### 7. **Advanced Pytest Configuration**

```toml
[tool.pytest.ini_options]
# Existing config...

filterwarnings = [
    "error",                        # Treat warnings as errors
    "ignore::UserWarning",          # Except UserWarnings
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]

# Performance benchmarking
[tool.pytest.ini_options.benchmark]
min_rounds = 5
max_time = 1.0
min_time = 0.000005
timer = "time.perf_counter"
```

**Benefits:**
- Catch issues from warnings
- Configurable benchmark parameters
- Better test isolation

---

### 8. **Documentation Tools**

```toml
[tool.pydocstyle]
convention = "google"
add-ignore = ["D100", "D101", "D102", "D103", "D104", "D105", "D107"]
match = "(?!test_).*\\.py"
match-dir = "(?!tests|migrations)[^\\.].*"
```

**Google Style Docstrings:**
```python
def function(arg1: str, arg2: int) -> bool:
    """Short description.
    
    Longer description with more details.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is wrong
    """
```

---

### 9. **Dynamic Metadata Support**

```toml
[project]
readme = {file = "README.md", content-type = "text/markdown"}  # NEW: Explicit format
requires-python = ">=3.10,<4.0"  # NEW: Upper bound

[tool.setuptools.dynamic]
# Uncomment to enable dynamic versioning from git tags
# version = {attr = "src.__version__.__version__"}
# Or use setuptools-scm:
# [tool.setuptools_scm]
# write_to = "src/_version.py"
# version_scheme = "post-release"
# local_scheme = "no-local-version"
```

**Benefits:**
- Automatic versioning from git tags
- Cleaner version management
- No manual version updates needed

---

### 10. **Memray Configuration**

```toml
[tool.memray]
output = "memray-results"
format = "html"
```

**Usage:**
```bash
# Run with memray
memray run script.py

# Generate flamegraph
memray flamegraph memray-results.bin

# Generate HTML report
memray table memray-results.bin --html > memory-report.html

# Compare runs
memray stats memray-results-1.bin memray-results-2.bin
```

---

## 📊 Tool Comparison Matrix

### Profiling Tools

| Tool | Type | Overhead | Features | Best For |
|------|------|----------|----------|----------|
| **py-spy** | Sampling | ~0% | CPU profiling, live processes | Production debugging |
| **memray** | Tracking | Low | Memory allocations, leaks | Memory optimization |
| **scalene** | Sampling | ~10-20% | CPU+GPU+memory+AI hints | Development profiling |

### Code Quality Tools

| Tool | Purpose | Output | Integration |
|------|---------|--------|-------------|
| **ruff** | Linting | Terminal/JSON | Pre-commit, CI |
| **mypy** | Type checking | Terminal/HTML | Pre-commit, CI |
| **vulture** | Dead code | Terminal | CI, manual |
| **interrogate** | Docstrings | Terminal/Badge | CI |
| **bandit** | Security | Terminal/JSON | Pre-commit, CI |
| **pip-audit** | Dependencies | Terminal/JSON | CI |

---

## 🚀 New Workflows

### Performance Profiling Workflow

```bash
# 1. Identify slow code with py-spy
py-spy record -o profile.svg -- python script.py
# Opens profile.svg in browser

# 2. Memory profiling with memray
memray run script.py
memray flamegraph memray-results.bin -o memory.html

# 3. Comprehensive analysis with scalene
scalene script.py
# AI-powered suggestions for optimization

# 4. Benchmark specific functions
pytest tests/ -m performance --benchmark-only
```

### Code Quality Workflow

```bash
# 1. Fast linting
ruff check . --fix

# 2. Type checking
mypy src/

# 3. Find dead code
vulture src/ --min-confidence 80

# 4. Check docstring coverage
interrogate src/

# 5. Security scan
bandit -r src/
pip-audit

# All at once
ruff check . && mypy src/ && vulture src/ && interrogate src/ && bandit -r src/
```

### Documentation Workflow

```bash
# 1. Check docstring coverage
interrogate src/ -v

# 2. Generate badge
interrogate --generate-badge docs/

# 3. Build docs with Mermaid support
mkdocs serve

# 4. Check style
pydocstyle src/
```

---

## 📈 Impact Metrics

### Code Quality

| Metric | Before | After Phase 3 | Tool |
|--------|--------|---------------|------|
| Dead code detection | Manual | Automated | vulture |
| Docstring coverage | Unknown | Tracked | interrogate |
| Security scanning | 1 tool | 3 tools | bandit, safety, pip-audit |
| Dependency auditing | Manual | Automated | pip-audit |

### Performance Analysis

| Capability | Before | After Phase 3 |
|------------|--------|---------------|
| CPU profiling | None | py-spy, scalene |
| Memory profiling | None | memray, scalene |
| Function benchmarking | None | pytest-benchmark |
| Production profiling | Not possible | py-spy (zero overhead) |

### Documentation

| Feature | Before | After Phase 3 |
|---------|--------|---------------|
| Diagram support | None | Mermaid |
| Docstring coverage | Unknown | Measured |
| Coverage badge | None | Generated |
| Style enforcement | None | pydocstyle |

---

## 🎓 New Commands Reference

### Profiling

```bash
# py-spy - CPU profiling
py-spy top --pid <PID>                    # Live CPU usage
py-spy record -o profile.svg python app.py  # Record profile
py-spy dump --pid <PID>                   # Thread dump

# memray - Memory profiling
memray run script.py                      # Track memory
memray flamegraph output.bin              # Visualize
memray table output.bin                   # Statistics
memray tree output.bin                    # Call tree

# scalene - Comprehensive profiling
scalene script.py                         # Full profile
scalene --html script.py                  # HTML report
scalene --cpu-only script.py              # CPU only
```

### Code Quality

```bash
# vulture - Dead code
vulture src/                              # Find dead code
vulture src/ --min-confidence 90          # High confidence only
vulture src/ --sort-by-size               # Sort by code size

# interrogate - Docstrings
interrogate src/                          # Check coverage
interrogate -v src/                       # Verbose
interrogate --generate-badge docs/        # Generate badge
interrogate --fail-under 80 src/          # Enforce threshold

# pip-audit - Dependencies
pip-audit                                 # Scan dependencies
pip-audit --fix                           # Auto-fix
pip-audit --format json                   # JSON output
```

### Testing

```bash
# With new markers
pytest -m performance                     # Performance tests
pytest -m security                        # Security tests
pytest -m "not wip"                       # Skip WIP
pytest -m "not flaky"                     # Skip flaky tests

# Benchmarking
pytest --benchmark-only                   # Only benchmarks
pytest --benchmark-compare                # Compare results
pytest --benchmark-histogram              # Generate histogram
```

---

## 📚 Documentation Updates

### New Documentation Created

1. **docs/README.md** (301 lines)
   - Comprehensive documentation index
   - Organized by role, topic, and type
   - Learning paths and reading orders
   - Status tracking for all docs

### Documentation Organization

All major documentation moved to `docs/` folder:
- ✅ CONTRIBUTING.md
- ✅ SECURITY.md
- ✅ TECHNICAL_DEBT_REVIEW.md
- ✅ PYPROJECT_ENHANCEMENTS.md
- ✅ PYPROJECT_PHASE2_SUMMARY.md
- ✅ IMPROVEMENTS_SUMMARY.md
- ✅ QUICK_REFERENCE.md

**Root folder kept clean:**
- README.md (project overview)
- CHANGELOG.md (version history)
- pyproject.toml (configuration)

---

## ✅ Files Modified

| File | Changes | Impact |
|------|---------|--------|
| `pyproject.toml` | +89 lines | Advanced tools configured |
| **New Files** | | |
| `docs/README.md` | 301 lines | Documentation index |
| `docs/PYPROJECT_PHASE3_SUMMARY.md` | This file | Phase 3 summary |

**Total Phase 3 Impact:** +390+ lines of configuration and documentation

---

## 🎯 Migration Checklist

### Immediate
- [x] ✅ Added performance dependency group
- [x] ✅ Added advanced linting tools
- [x] ✅ Enhanced pytest markers
- [x] ✅ Organized documentation
- [x] ✅ Created docs index
- [ ] Install performance tools: `uv pip install --group performance`
- [ ] Install new lint tools: `uv pip install --group lint`

### Short-term (This Week)
- [ ] Try py-spy on running dashboard: `py-spy top --pid <PID>`
- [ ] Run dead code detection: `vulture src/`
- [ ] Check docstring coverage: `interrogate src/`
- [ ] Audit dependencies: `pip-audit`

### Medium-term (This Month)
- [ ] Benchmark critical functions with pytest-benchmark
- [ ] Profile memory with memray
- [ ] Add docstrings to improve coverage
- [ ] Remove dead code found by vulture

### Long-term (Ongoing)
- [ ] Regular performance profiling
- [ ] Maintain docstring coverage >80%
- [ ] Monthly dependency audits
- [ ] Keep documentation updated

---

## 💡 Best Practices Enabled

### Performance Optimization

**Before:**
```python
# Hope it's fast enough
def process_data(data):
    # implementation
```

**After:**
```python
@pytest.mark.performance
def test_process_data_performance(benchmark):
    result = benchmark(process_data, test_data)
    assert result.mean < 0.1  # < 100ms
```

### Code Quality

**Before:**
```python
# No dead code detection
# No docstring enforcement
# Manual security reviews
```

**After:**
```bash
# Automated checks in CI
vulture src/
interrogate --fail-under 80 src/
bandit -r src/
pip-audit
```

### Production Debugging

**Before:**
```bash
# Add print statements
# Restart application
# Hope to reproduce issue
```

**After:**
```bash
# Profile running application
py-spy record -o profile.svg --pid <PID>
# No restart needed!
# Zero overhead!
```

---

## 🔗 Integration Examples

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: vulture
        name: Dead Code Detection
        entry: vulture
        args: [src/, --min-confidence, "80"]
        language: system
        
      - id: interrogate
        name: Docstring Coverage
        entry: interrogate
        args: [src/, --fail-under, "50"]
        language: system
```

### CI/CD Pipeline

```yaml
# .github/workflows/quality.yml
- name: Check dead code
  run: vulture src/ --min-confidence 80

- name: Check docstrings
  run: interrogate src/ --fail-under 50

- name: Audit dependencies
  run: pip-audit

- name: Run performance tests
  run: pytest -m performance --benchmark-only
```

---

## 🎉 Summary

Phase 3 completes the professional development environment by adding:

### Performance Tools
- ⚡️ **py-spy**: Zero-overhead production profiling
- 🧠 **memray**: Memory leak detection
- 📊 **scalene**: AI-powered optimization hints

### Code Quality
- 🧹 **vulture**: Dead code detection
- 📝 **interrogate**: Docstring coverage
- 🔒 **pip-audit**: Dependency auditing

### Testing
- 📈 **pytest-benchmark**: Performance testing
- 🎭 **pytest-mock**: Enhanced mocking
- 🏷️ **5 new markers**: Better test organization

### Documentation
- 📚 **Organized structure**: All docs in `docs/`
- 📖 **Comprehensive index**: Easy navigation
- 🎨 **Mermaid support**: Diagram generation

**The project now has a complete, professional-grade Python development environment!**

---

**Completed:** 2025-10-30  
**Phase:** 3 - Advanced Tooling  
**Status:** ✅ Complete & Production Ready  
**Next Phase:** CI/CD Automation & GitHub Actions

---

## 📞 Questions?

- **Profiling**: See tool documentation for py-spy, memray, scalene
- **Dead Code**: `vulture --help`
- **Docstrings**: `interrogate --help`
- **All Tools**: See docs/PYPROJECT_ENHANCEMENTS.md
