# Dashboard Testing Guide

**Last Updated:** 2025-10-30  
**Phase:** 3 - Testing & Documentation  
**Status:** ✅ Complete

---

## 📋 Overview

This document describes the testing approach, best practices, and guidelines for testing the VMware Inventory Dashboard Streamlit application.

### Test Coverage Goals

- **Unit Tests:** >80% coverage for utility modules
- **Integration Tests:** Key user flows and page rendering
- **Performance Tests:** Large dataset handling
- **Error Handling:** Edge cases and error scenarios

---

## 🏗️ Test Structure

```
tests/
├── dashboard/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── unit/                    # Fast, isolated unit tests
│   │   ├── __init__.py
│   │   ├── test_database_utils.py
│   │   ├── test_state_utils.py
│   │   └── test_error_cache_utils.py
│   └── integration/             # Integration and page tests
│       ├── __init__.py
│       └── test_overview_page.py
├── test_dashboard_data.py       # Existing data logic tests
└── ...
```

---

## 🚀 Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only
pytest -m integration

# Dashboard tests
pytest -m dashboard

# Exclude slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Run unit tests for database utilities
pytest tests/dashboard/unit/test_database_utils.py

# Run integration tests for overview page
pytest tests/dashboard/integration/test_overview_page.py

# Run specific test class
pytest tests/dashboard/unit/test_state_utils.py::TestStateManager

# Run specific test
pytest tests/dashboard/unit/test_database_utils.py::TestDatabaseManager::test_get_engine_creates_engine
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=src/dashboard --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
# Show all test names and outcomes
pytest -v

# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Show full diff on assertion failures
pytest -vv
```

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run tests on 4 cores
pytest -n 4
```

---

## 🧪 Test Categories

### Unit Tests

**Purpose:** Test individual functions and classes in isolation  
**Marker:** `@pytest.mark.unit`  
**Speed:** Fast (<1s per test)  
**Dependencies:** Minimal (mocked)

**Example:**

```python
@pytest.mark.unit
def test_state_manager_get_returns_value():
    """Test that StateManager.get returns stored value."""
    with patch('streamlit.session_state', {'db_url': 'test.db'}):
        result = StateManager.get(SessionKeys.DB_URL)
        assert result == 'test.db'
```

### Integration Tests

**Purpose:** Test complete workflows and page rendering  
**Marker:** `@pytest.mark.integration`  
**Speed:** Medium (1-5s per test)  
**Dependencies:** Database, fixtures

**Example:**

```python
@pytest.mark.integration
@pytest.mark.dashboard
def test_overview_displays_with_data(populated_db_session, db_url):
    """Test that overview page displays correctly with data."""
    from dashboard.pages import overview
    
    with patch('streamlit.title'), patch('streamlit.metric'):
        overview.render(db_url)
        # Assertions...
```

### Slow Tests

**Purpose:** Performance tests with large datasets  
**Marker:** `@pytest.mark.slow`  
**Speed:** Slow (>5s per test)  
**Skip By Default:** Yes

**Example:**

```python
@pytest.mark.slow
def test_overview_renders_with_many_vms(db_session, db_url):
    """Test overview performance with 100+ VMs."""
    # Create 100 VMs and test rendering time
    ...
```

---

## 🔧 Fixtures

### Database Fixtures

```python
# Empty in-memory database
def test_empty_database(empty_db_session):
    ...

# Populated database with sample VMs
def test_with_data(populated_db_session):
    ...

# Temporary database file
def test_file_database(temp_db_file):
    ...

# Database URL
def test_with_url(db_url):
    ...
```

### Streamlit Mocking Fixtures

```python
# Mock Streamlit functions
def test_page_rendering(mock_streamlit):
    # mock_streamlit provides mocked st.title, st.metric, etc.
    ...

# Mock session state
def test_state_management(mock_session_state):
    ...
```

### Utility Fixtures

```python
# Mock DatabaseManager
def test_with_db_manager(mock_database_manager):
    ...

# Mock StateManager
def test_with_state_manager(mock_state_manager):
    ...

# Mock ErrorHandler
def test_error_handling(mock_error_handler):
    ...
```

### Sample Data Fixtures

```python
# Sample VM dictionaries
def test_with_sample_vms(sample_vms):
    ...

# Mock query results
def test_with_mock_results(mock_query_result):
    ...
```

---

## ✅ Best Practices

### Test Naming

```python
# Good: Descriptive, action-oriented
def test_database_manager_creates_connection_pool():
    ...

def test_state_manager_preserves_existing_values():
    ...

def test_overview_page_handles_empty_database():
    ...

# Bad: Vague, unclear
def test_db():
    ...

def test_function1():
    ...
```

### Test Organization

```python
# Group related tests in classes
class TestDatabaseManager:
    """Tests for DatabaseManager class."""
    
    def test_get_engine_creates_engine(self):
        ...
    
    def test_get_engine_caching(self):
        ...
    
    def test_test_connection_success(self):
        ...
```

### Assertions

```python
# Good: Specific, clear assertions
def test_vm_count_calculation():
    result = get_vm_counts(db_url)
    
    assert 'total' in result
    assert 'powered_on' in result
    assert result['total'] == 5
    assert result['powered_on'] == 3
    assert result['powered_on'] <= result['total']

# Bad: Vague assertions
def test_vm_count():
    result = get_vm_counts(db_url)
    assert result  # What does this test?
```

### Error Testing

```python
# Test error conditions explicitly
def test_database_connection_failure():
    """Test handling of database connection failures."""
    success, error = DatabaseManager.test_connection("invalid://url")
    
    assert success is False
    assert error is not None
    assert isinstance(error, str)

# Test exception raising
def test_invalid_input_raises_error():
    """Test that invalid input raises ValidationError."""
    with pytest.raises(ValidationError):
        validate_regex("[invalid")
```

### Mocking

```python
# Mock external dependencies
@patch('streamlit.error')
def test_error_display(mock_error):
    """Test error message display."""
    ErrorHandler.show_error(Exception("Test"))
    
    mock_error.assert_called_once()

# Use context managers for multiple mocks
def test_page_rendering():
    with patch('streamlit.title') as mock_title, \
         patch('streamlit.metric') as mock_metric:
        overview.render(db_url)
        
        mock_title.assert_called()
        assert mock_metric.call_count > 0
```

### Test Independence

```python
# Good: Tests are independent
def test_create_vm(db_session):
    vm = VirtualMachine(vm="test-vm")
    db_session.add(vm)
    db_session.commit()
    
    assert db_session.query(VirtualMachine).count() == 1

def test_delete_vm(db_session):
    # Each test gets a fresh db_session
    # Previous test data doesn't affect this test
    ...

# Bad: Tests depend on each other
class TestVMOperations:
    def test_01_create_vm(self):
        # Creates VM...
        pass
    
    def test_02_update_vm(self):
        # Assumes VM from test_01 exists...
        pass
```

---

## 📊 Coverage Guidelines

### What to Test

✅ **High Priority:**
- Database connection and session management
- State management (get/set/delete)
- Error handling and display
- Cache operations
- Data transformations and calculations
- Input validation

✅ **Medium Priority:**
- Page rendering with valid data
- Navigation flows
- Filter and search functionality
- Data quality checks

⚠️ **Low Priority:**
- UI styling and layout
- Static content display
- Simple getter/setter methods

❌ **Don't Test:**
- Third-party libraries (Streamlit, SQLAlchemy)
- Python built-ins
- Trivial code (pass, return None)

### Coverage Metrics

```bash
# Check current coverage
pytest --cov=src/dashboard --cov-report=term-missing

# Target coverage by module
src/dashboard/utils/
  database.py      90%
  state.py         85%
  errors.py        80%
  cache.py         85%

src/dashboard/pages/
  overview.py      70%
  analytics.py     65%
  (other pages)    50-70%
```

---

## 🐛 Debugging Tests

### Show Print Output

```bash
pytest -s
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Run Failed Tests First

```bash
pytest --ff
```

### Show Full Diff

```bash
pytest -vv
```

### Increase Verbosity

```bash
pytest -vvv
```

---

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-timeout
    
    - name: Run unit tests
      run: pytest -m unit --cov=src/dashboard
    
    - name: Run integration tests
      run: pytest -m integration
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 📝 Writing New Tests

### Step 1: Choose Test Type

- **Unit test** if testing a single function/class in isolation
- **Integration test** if testing page rendering or workflows
- **Slow test** if test takes >5 seconds

### Step 2: Use Appropriate Fixtures

```python
# For database tests
def test_my_feature(populated_db_session, db_url):
    ...

# For page tests
def test_my_page(page_test_context):
    ...

# For utility tests
def test_my_util(mock_streamlit):
    ...
```

### Step 3: Follow Naming Convention

```python
@pytest.mark.unit  # or integration, slow, etc.
class TestMyFeature:
    """Tests for MyFeature functionality."""
    
    def test_feature_does_expected_thing(self):
        """Test that feature behaves as expected."""
        ...
    
    def test_feature_handles_edge_case(self):
        """Test that feature handles edge case."""
        ...
    
    def test_feature_raises_error_on_invalid_input(self):
        """Test that feature raises error for invalid input."""
        ...
```

### Step 4: Add Assertions

```python
def test_example():
    result = my_function()
    
    # Test return type
    assert isinstance(result, dict)
    
    # Test required keys
    assert 'total' in result
    assert 'count' in result
    
    # Test values
    assert result['total'] > 0
    assert result['count'] <= result['total']
```

### Step 5: Run and Verify

```bash
# Run your new test
pytest tests/dashboard/unit/test_my_feature.py -v

# Check coverage
pytest tests/dashboard/unit/test_my_feature.py --cov=src/dashboard/my_module
```

---

## 🎯 Testing Checklist

When adding new features, ensure:

- [ ] Unit tests for new utility functions
- [ ] Integration tests for new pages
- [ ] Error handling tests for edge cases
- [ ] Tests for null/empty/invalid inputs
- [ ] Performance tests for large datasets (if applicable)
- [ ] All tests pass: `pytest`
- [ ] Coverage meets targets: `pytest --cov`
- [ ] Code follows existing patterns
- [ ] Tests are independent and can run in any order
- [ ] Fixtures are reused where appropriate
- [ ] Test names are descriptive
- [ ] Documentation is updated

---

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/how-to/mark.html)
- [Testing Streamlit Apps](https://docs.streamlit.io/knowledge-base/using-streamlit/how-do-i-test-streamlit-apps)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/core/testing.html)

---

## 🆘 Troubleshooting

### Import Errors

```bash
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
pytest
```

### Fixture Not Found

```bash
# Check conftest.py is in correct location
tests/dashboard/conftest.py  # ✅
tests/conftest.py            # ❌ (won't be found by dashboard tests)
```

### Database Locked

```bash
# Clean up any stale database connections
rm -f /tmp/*.db
pytest
```

### Streamlit Import Errors

```bash
# Install Streamlit in test environment
pip install streamlit
```

---

## 📈 Test Metrics

Track these metrics over time:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total Tests | 100+ | 150+ | 🟢 |
| Unit Test Coverage | 75% | 80% | 🟡 |
| Integration Test Coverage | 60% | 70% | 🟡 |
| Test Execution Time | <60s | <90s | 🟢 |
| Flaky Tests | 0 | 0 | 🟢 |

---

**Last Review:** 2025-10-30  
**Next Review:** 2025-11-30  
**Maintained By:** Development Team
