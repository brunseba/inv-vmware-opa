"""Pytest fixtures for dashboard testing."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import tempfile
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.models import Base, VirtualMachine


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def in_memory_engine():
    """Create an in-memory SQLite engine with foreign key support."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Enable foreign key constraints
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    
    yield engine
    
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(in_memory_engine):
    """Create a database session for testing."""
    SessionLocal = sessionmaker(bind=in_memory_engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def empty_db_session(db_session):
    """Provide an empty database session."""
    return db_session


@pytest.fixture(scope="function")
def populated_db_session(db_session):
    """Provide a database session with sample VM data."""
    # Add sample VMs with diverse configurations
    vms = [
        VirtualMachine(
            vm="vm-prod-web-01",
            powerstate="poweredOn",
            cpus=4,
            memory=8192,
            datacenter="DC-PROD",
            cluster="CL-WEB",
            host="esxi01.prod.example.com",
            os_config="Ubuntu Linux (64-bit)",
            creation_date=datetime(2023, 1, 15),
            in_use_mib=51200,
            provisioned_mib=102400,
            dns_name="web01.prod.example.com",
            primary_ip_address="10.0.1.10",
            folder="/PROD/Web Servers"
        ),
        VirtualMachine(
            vm="vm-prod-db-01",
            powerstate="poweredOn",
            cpus=8,
            memory=16384,
            datacenter="DC-PROD",
            cluster="CL-DB",
            host="esxi02.prod.example.com",
            os_config="Red Hat Enterprise Linux 8 (64-bit)",
            creation_date=datetime(2023, 3, 20),
            in_use_mib=81920,
            provisioned_mib=163840,
            dns_name="db01.prod.example.com",
            primary_ip_address="10.0.2.10",
            folder="/PROD/Databases"
        ),
        VirtualMachine(
            vm="vm-dev-app-01",
            powerstate="poweredOff",
            cpus=2,
            memory=4096,
            datacenter="DC-DEV",
            cluster="CL-DEV",
            host="esxi03.dev.example.com",
            os_config="CentOS 7 (64-bit)",
            creation_date=datetime(2023, 6, 10),
            in_use_mib=20480,
            provisioned_mib=40960,
            dns_name="app01.dev.example.com",
            primary_ip_address="10.1.1.10",
            folder="/DEV/Applications"
        ),
        VirtualMachine(
            vm="vm-test-win-01",
            powerstate="poweredOn",
            cpus=4,
            memory=8192,
            datacenter="DC-TEST",
            cluster="CL-TEST",
            host="esxi04.test.example.com",
            os_config="Microsoft Windows Server 2022 (64-bit)",
            creation_date=datetime(2024, 1, 5),
            in_use_mib=40960,
            provisioned_mib=81920,
            dns_name="win01.test.example.com",
            primary_ip_address="10.2.1.10",
            folder="/TEST/Windows"
        ),
        VirtualMachine(
            vm="vm-test-orphan-01",
            powerstate="suspended",
            cpus=2,
            memory=4096,
            datacenter="DC-TEST",
            cluster="CL-TEST",
            host="esxi04.test.example.com",
            os_config="Ubuntu Linux (64-bit)",
            creation_date=datetime(2024, 2, 15),
            # Missing critical data
            dns_name=None,
            primary_ip_address=None,
            folder=None,
            in_use_mib=None,
            provisioned_mib=None
        ),
    ]
    
    for vm in vms:
        db_session.add(vm)
    db_session.commit()
    
    return db_session


@pytest.fixture(scope="function")
def temp_db_file():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Create database with schema
    engine = create_engine(f"sqlite:///{path}", echo=False)
    Base.metadata.create_all(engine)
    engine.dispose()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture(scope="function")
def db_url(temp_db_file):
    """Provide a database URL for testing."""
    return f"sqlite:///{temp_db_file}"


# ============================================================================
# Streamlit Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit module for testing pages."""
    with patch('streamlit.session_state', {}) as mock_state, \
         patch('streamlit.title') as mock_title, \
         patch('streamlit.header') as mock_header, \
         patch('streamlit.subheader') as mock_subheader, \
         patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.write') as mock_write, \
         patch('streamlit.metric') as mock_metric, \
         patch('streamlit.columns') as mock_columns, \
         patch('streamlit.dataframe') as mock_dataframe, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.expander') as mock_expander, \
         patch('streamlit.spinner') as mock_spinner, \
         patch('streamlit.cache_data') as mock_cache_data, \
         patch('streamlit.cache_resource') as mock_cache_resource:
        
        # Setup mock returns
        mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()
        mock_spinner.return_value.__enter__ = MagicMock()
        mock_spinner.return_value.__exit__ = MagicMock()
        
        # Make cache decorators pass-through
        mock_cache_data.side_effect = lambda **kwargs: lambda f: f
        mock_cache_resource.side_effect = lambda **kwargs: lambda f: f
        
        yield {
            'session_state': mock_state,
            'title': mock_title,
            'header': mock_header,
            'subheader': mock_subheader,
            'markdown': mock_markdown,
            'write': mock_write,
            'metric': mock_metric,
            'columns': mock_columns,
            'dataframe': mock_dataframe,
            'error': mock_error,
            'warning': mock_warning,
            'success': mock_success,
            'info': mock_info,
            'expander': mock_expander,
            'spinner': mock_spinner,
        }


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    state = {
        'db_url': 'sqlite:///:memory:',
        'current_page': 'Overview',
    }
    
    with patch('streamlit.session_state', state):
        yield state


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_vms():
    """Provide sample VM data as dictionaries."""
    return [
        {
            'vm': 'vm-prod-01',
            'powerstate': 'poweredOn',
            'cpus': 4,
            'memory': 8192,
            'datacenter': 'DC1',
            'cluster': 'CL1',
            'host': 'host1.example.com',
        },
        {
            'vm': 'vm-prod-02',
            'powerstate': 'poweredOn',
            'cpus': 8,
            'memory': 16384,
            'datacenter': 'DC1',
            'cluster': 'CL1',
            'host': 'host2.example.com',
        },
        {
            'vm': 'vm-dev-01',
            'powerstate': 'poweredOff',
            'cpus': 2,
            'memory': 4096,
            'datacenter': 'DC2',
            'cluster': 'CL2',
            'host': 'host3.example.com',
        },
    ]


@pytest.fixture
def mock_query_result():
    """Provide mock query results."""
    mock_vm = Mock(spec=VirtualMachine)
    mock_vm.vm = "test-vm"
    mock_vm.powerstate = "poweredOn"
    mock_vm.cpus = 4
    mock_vm.memory = 8192
    mock_vm.datacenter = "DC1"
    mock_vm.cluster = "CL1"
    mock_vm.host = "host1.example.com"
    
    return [mock_vm]


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_database_manager():
    """Mock DatabaseManager for testing."""
    with patch('dashboard.utils.database.DatabaseManager') as mock_dm:
        mock_engine = MagicMock()
        mock_session = MagicMock()
        
        mock_dm.get_engine.return_value = mock_engine
        mock_dm.get_session_factory.return_value = lambda: mock_session
        mock_dm.test_connection.return_value = (True, None)
        
        yield mock_dm


@pytest.fixture
def mock_state_manager():
    """Mock StateManager for testing."""
    with patch('dashboard.utils.state.StateManager') as mock_sm:
        state = {
            'db_url': 'sqlite:///:memory:',
            'current_page': 'Overview',
        }
        
        mock_sm.get.side_effect = lambda key, default=None: state.get(key.value if hasattr(key, 'value') else key, default)
        mock_sm.set.side_effect = lambda key, value: state.update({key.value if hasattr(key, 'value') else key: value})
        mock_sm.init_state.return_value = None
        
        yield mock_sm


@pytest.fixture
def mock_error_handler():
    """Mock ErrorHandler for testing."""
    with patch('dashboard.utils.errors.ErrorHandler') as mock_eh:
        mock_eh.show_error.return_value = None
        mock_eh.show_success.return_value = None
        mock_eh.show_warning.return_value = None
        
        yield mock_eh


# ============================================================================
# Page Test Helpers
# ============================================================================

@pytest.fixture
def page_test_context(mock_streamlit, populated_db_session, db_url):
    """Provide complete context for testing pages."""
    return {
        'streamlit': mock_streamlit,
        'session': populated_db_session,
        'db_url': db_url,
    }


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "dashboard: mark test as dashboard-related"
    )
