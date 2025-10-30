# Dashboard Tests

This directory contains tests for the VMware Inventory Dashboard Streamlit application.

## Structure

```
tests/dashboard/
├── README.md              # This file
├── conftest.py            # Shared fixtures and pytest configuration
├── unit/                  # Unit tests (fast, isolated)
│   ├── test_database_utils.py
│   ├── test_state_utils.py
│   └── test_error_cache_utils.py
└── integration/           # Integration tests (slower, full workflows)
    └── test_overview_page.py
```

## Quick Start

```bash
# Run all dashboard tests
pytest tests/dashboard/

# Run only unit tests (fast)
pytest tests/dashboard/unit/ -m unit

# Run with coverage
pytest tests/dashboard/ --cov=src/dashboard
```

## Test Categories

### Unit Tests (`unit/`)
- **Purpose:** Test individual functions and classes in isolation
- **Speed:** Fast (<1s per test)
- **Marker:** `@pytest.mark.unit`
- **Dependencies:** Minimal, heavily mocked

### Integration Tests (`integration/`)
- **Purpose:** Test complete workflows and page rendering
- **Speed:** Medium (1-5s per test)
- **Marker:** `@pytest.mark.integration`
- **Dependencies:** Database, fixtures

## Available Fixtures

See `conftest.py` for all available fixtures. Common ones include:

### Database
- `empty_db_session` - Empty database for testing
- `populated_db_session` - Database with sample VM data
- `db_url` - Database URL for connection strings

### Mocking
- `mock_streamlit` - Mock Streamlit UI functions
- `mock_session_state` - Mock session state
- `mock_database_manager` - Mock database manager
- `mock_state_manager` - Mock state manager

### Sample Data
- `sample_vms` - Sample VM dictionaries
- `mock_query_result` - Mock query results

## Writing New Tests

1. **Choose the right location:**
   - `unit/` for isolated function/class tests
   - `integration/` for page rendering or workflow tests

2. **Add appropriate markers:**
   ```python
   @pytest.mark.unit
   def test_my_feature():
       ...
   ```

3. **Use descriptive names:**
   ```python
   # Good
   def test_database_manager_creates_connection_pool():
       ...
   
   # Bad
   def test_db():
       ...
   ```

4. **Group related tests:**
   ```python
   class TestDatabaseManager:
       def test_get_engine_creates_engine(self):
           ...
       
       def test_get_engine_caching(self):
           ...
   ```

## Running Tests

### Basic Commands

```bash
# All dashboard tests
pytest tests/dashboard/

# Specific file
pytest tests/dashboard/unit/test_database_utils.py

# Specific class
pytest tests/dashboard/unit/test_database_utils.py::TestDatabaseManager

# Specific test
pytest tests/dashboard/unit/test_database_utils.py::TestDatabaseManager::test_get_engine_creates_engine
```

### By Marker

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Dashboard tests only
pytest -m dashboard

# Exclude slow tests
pytest -m "not slow"
```

### With Options

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed
pytest --lf

# Coverage report
pytest --cov=src/dashboard --cov-report=html
```

## Test Coverage

Current coverage targets:

| Module | Target Coverage |
|--------|----------------|
| `utils/database.py` | 90% |
| `utils/state.py` | 85% |
| `utils/errors.py` | 80% |
| `utils/cache.py` | 85% |
| `pages/*.py` | 60-70% |

Check coverage:
```bash
pytest --cov=src/dashboard --cov-report=term-missing
```

## Best Practices

1. **Keep tests independent** - Each test should work in isolation
2. **Use fixtures** - Reuse common setup code
3. **Mock external dependencies** - Don't rely on actual Streamlit rendering
4. **Test edge cases** - Include tests for null, empty, invalid inputs
5. **Write clear assertions** - Be specific about what you're testing
6. **Document complex tests** - Add docstrings explaining the test

## Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Full diff on assertion failures
pytest -vv

# Increase timeout for slow tests
pytest --timeout=600
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example: GitHub Actions
- name: Run Dashboard Tests
  run: |
    pytest tests/dashboard/ -m unit
    pytest tests/dashboard/ -m integration
```

## Additional Documentation

- [Comprehensive Testing Guide](../../docs/DASHBOARD_TESTING.md)
- [Phase 3 Summary](../../docs/PHASE_3_SUMMARY.md)
- [Technical Debt Analysis](../../docs/STREAMLIT_TECHNICAL_DEBT.md)

## Support

For questions or issues with tests:
1. Check the [Testing Guide](../../docs/DASHBOARD_TESTING.md)
2. Review existing tests for examples
3. Consult the team

---

**Last Updated:** 2025-10-30  
**Maintained By:** Development Team
