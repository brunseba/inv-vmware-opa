# Unit Test Coverage

This document summarizes the unit test coverage for the inv-vmware-opa project.

## ✅ Completed Test Suites

### 1. **test_loader.py** (Existing)
- Tests for Excel data loading utilities
- Column name normalization
- Data type parsing (date, bool, int, float)

### 2. **test_backup_service.py** (Integration Tests)
- Label export/import with real database
- VM and folder assignment handling
- Backup file listing
- Database backup and restore
- **Note**: These are integration tests using in-memory SQLite

### 3. **test_backup_service_unit.py** (Pure Unit Tests) ✨
Pure unit tests with complete mocking:
- Export labels logic (7 tests)
- Import labels logic (7 tests)
- List backups logic (4 tests)
- Database backup logic (3 tests)
- Database restore logic (3 tests)
- **Total: 24 tests**

### 4. **test_label_service.py** (Pure Unit Tests) ✨
Pure unit tests for LabelService:
- Label CRUD operations (11 tests)
- VM label operations (7 tests)
- Folder label operations (6 tests)
- Folder operations (2 tests)
- Label inheritance logic (4 tests)
- Helper methods (4 tests)
- **Total: 34 tests**

### 5. **test_models.py** (Model Tests) ✨
Database model tests with in-memory SQLite:
- VirtualMachine model (4 tests)
- Label model (4 tests)
- VMLabel model (5 tests)
- FolderLabel model (4 tests)
- Model relationships (2 tests)
- **Total: 19 tests**

### 6. **test_cli_label.py** (CLI Tests) ✨
CLI command tests using Click's test runner:
- Label service helper (1 test)
- Create label command (3 tests)
- List labels command (3 tests)
- Delete label command (2 tests)
- List keys command (2 tests)
- Assign VM label command (4 tests)
- Remove VM label command (3 tests)
- CLI integration (2 tests)
- **Total: 20 tests**

### 7. **test_dashboard_data.py** (Dashboard Data Tests) ✨
Data processing tests for dashboard pages:
- Overview page data calculations (12 tests)
- Analytics page data processing (5 tests)
- Infrastructure page data calculations (5 tests)
- Data quality checks (3 tests)
- Data aggregation functions (3 tests)
- **Total: 27 tests**

## 📊 Coverage Summary

| Component | Test File | Type | Status | Test Count |
|-----------|-----------|------|--------|------------|
| Loader utilities | test_loader.py | Unit | ✅ Complete | 5 |
| BackupService | test_backup_service_unit.py | Pure Unit | ✅ Complete | 24 |
| LabelService | test_label_service.py | Pure Unit | ✅ Complete | 34 |
| Database Models | test_models.py | Integration | ✅ Complete | 19 |
| CLI Commands | test_cli_label.py | Unit | ✅ Complete | 20 |
| Dashboard Data | test_dashboard_data.py | Integration | ✅ Complete | 27 |
| **Total** | | | | **129** |

## 🔧 Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test file:
```bash
pytest tests/test_label_service.py -v
```

### Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run only unit tests (exclude integration):
```bash
pytest tests/ -m "not integration"
```

## 🚧 Remaining Work

The following components still need comprehensive unit test coverage:

### High Priority

1. **Report Generator** (`src/report_generator.py`)
   - PDF generation logic
   - Chart creation
   - Data aggregation
   - Section builders

2. **Dashboard Pages** (`src/dashboard/pages/`)
   - Analytics page
   - Comparison page
   - Data quality page
   - Folder analysis page
   - Folder labelling page
   - Infrastructure page
   - Migration planning page
   - Overview page
   - Resources page
   - VM explorer page
   - VM search page

### Medium Priority

3. **Dashboard App** (`src/dashboard/app.py`)
   - Dash app initialization
   - Layout generation
   - Callback registrations

4. **Dashboard Utils** (`src/dashboard/utils/`)
   - Help utilities

### Lower Priority

5. **CLI Main** (`src/cli.py`)
   - Main CLI group
   - Command registration

## 📝 Test Guidelines

### Pure Unit Tests
Tests should:
- Mock all external dependencies (database, file system, network)
- Test business logic in isolation
- Be fast and deterministic
- Not require actual resources

### Integration Tests
Tests that:
- Use in-memory databases
- Test component interactions
- Verify end-to-end workflows
- Should be marked with `@pytest.mark.integration`

### Best Practices
1. Use descriptive test names
2. One assertion per test when possible
3. Use fixtures for common setup
4. Mock external dependencies
5. Test edge cases and error conditions
6. Maintain high coverage for critical paths

## 🎯 Coverage Goals

- **Critical Components**: 90%+ coverage
  - Services (LabelService, BackupService) ✅
  - Models ✅
  - CLI commands ✅

- **Dashboard Pages**: 70%+ coverage
  - Callback logic
  - Data transformations
  - Error handling

- **Report Generator**: 70%+ coverage
  - PDF generation
  - Data aggregation
  - Chart creation

## 🔍 Testing Dashboard Pages

Dashboard pages use Plotly Dash, which requires special testing approaches:

### Recommended Approach:
1. **Unit test callback functions** separately from Dash
2. **Mock Dash dependencies** (dcc.Store, callback context)
3. **Test data transformations** in isolation
4. **Use Dash testing framework** for integration tests

### Example:
```python
from unittest.mock import Mock, patch
from src.dashboard.pages.overview import get_summary_data

def test_get_summary_data():
    mock_session = Mock()
    # Setup mocks
    result = get_summary_data(mock_session)
    # Assertions
```

## 🐛 Known Testing Challenges

1. **Dash Callbacks**: Require Dash testing framework or careful mocking
2. **Matplotlib/Plotly**: Generate visual output; test data preparation instead
3. **ReportLab PDF**: Binary output; test structure and data rather than rendering
4. **SQLAlchemy Queries**: Use in-memory SQLite for model tests

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Dash Testing](https://dash.plotly.com/testing)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
