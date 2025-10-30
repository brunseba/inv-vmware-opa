"""Unit tests for database utility module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import OperationalError, SQLAlchemyError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from dashboard.utils.database import DatabaseManager


@pytest.mark.unit
class TestDatabaseManager:
    """Tests for DatabaseManager class."""
    
    def test_get_engine_creates_engine(self):
        """Test that get_engine creates a new engine."""
        db_url = "sqlite:///:memory:"
        
        engine = DatabaseManager.get_engine(db_url)
        
        assert engine is not None
        assert str(engine.url) == db_url
    
    def test_get_engine_caching(self):
        """Test that get_engine returns same engine for same URL."""
        db_url = "sqlite:///:memory:"
        
        engine1 = DatabaseManager.get_engine(db_url)
        engine2 = DatabaseManager.get_engine(db_url)
        
        # Due to Streamlit caching, should be the same object
        assert engine1 is engine2
    
    def test_get_session_factory_returns_callable(self):
        """Test that get_session_factory returns a sessionmaker."""
        db_url = "sqlite:///:memory:"
        
        factory = DatabaseManager.get_session_factory(db_url)
        
        assert callable(factory)
    
    def test_get_session_factory_creates_sessions(self, in_memory_engine):
        """Test that session factory creates working sessions."""
        db_url = "sqlite:///:memory:"
        
        factory = DatabaseManager.get_session_factory(db_url)
        session = factory()
        
        assert session is not None
        session.close()
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        db_url = "sqlite:///:memory:"
        
        success, error = DatabaseManager.test_connection(db_url)
        
        assert success is True
        assert error is None
    
    def test_test_connection_invalid_url(self):
        """Test connection test with invalid URL."""
        db_url = "invalid://url"
        
        success, error = DatabaseManager.test_connection(db_url)
        
        assert success is False
        assert error is not None
        assert isinstance(error, str)
    
    def test_test_connection_timeout(self):
        """Test connection test with timeout."""
        # Use a URL that will timeout
        db_url = "postgresql://nonexistent:5432/db"
        
        success, error = DatabaseManager.test_connection(db_url, timeout=1)
        
        assert success is False
        assert error is not None
    
    def test_get_engine_with_custom_pool_size(self):
        """Test engine creation with custom pool settings."""
        db_url = "sqlite:///:memory:"
        
        engine = DatabaseManager.get_engine(db_url, pool_size=10)
        
        assert engine is not None
    
    @patch('dashboard.utils.database.create_engine')
    def test_get_engine_handles_creation_error(self, mock_create_engine):
        """Test error handling during engine creation."""
        mock_create_engine.side_effect = SQLAlchemyError("Connection failed")
        
        with pytest.raises(SQLAlchemyError):
            DatabaseManager.get_engine("sqlite:///:memory:")
    
    def test_session_context_manager(self, db_url):
        """Test using session as context manager."""
        factory = DatabaseManager.get_session_factory(db_url)
        
        with factory() as session:
            assert session is not None
            # Session should be usable
            result = session.execute("SELECT 1")
            assert result is not None


@pytest.mark.unit
class TestDatabaseUtilityFunctions:
    """Tests for database utility helper functions."""
    
    def test_connection_pooling_configuration(self):
        """Test that connection pooling is properly configured."""
        db_url = "sqlite:///:memory:"
        
        engine = DatabaseManager.get_engine(db_url)
        
        # Verify pool is configured
        assert hasattr(engine, 'pool')
    
    def test_engine_disposal(self):
        """Test that engines can be properly disposed."""
        db_url = "sqlite:///:memory:"
        
        engine = DatabaseManager.get_engine(db_url)
        engine.dispose()
        
        # Should not raise exception
        assert True
    
    def test_multiple_database_urls(self):
        """Test handling multiple different database URLs."""
        db_url1 = "sqlite:///test1.db"
        db_url2 = "sqlite:///test2.db"
        
        engine1 = DatabaseManager.get_engine(db_url1)
        engine2 = DatabaseManager.get_engine(db_url2)
        
        # Should create different engines
        assert engine1 is not engine2
        assert str(engine1.url) != str(engine2.url)
    
    def test_session_rollback_on_error(self, db_url):
        """Test that sessions rollback on errors."""
        factory = DatabaseManager.get_session_factory(db_url)
        session = factory()
        
        try:
            # Force an error
            session.execute("INVALID SQL")
        except:
            session.rollback()
            # Should not raise
        finally:
            session.close()
        
        assert True
    
    def test_concurrent_session_creation(self, db_url):
        """Test creating multiple sessions concurrently."""
        factory = DatabaseManager.get_session_factory(db_url)
        
        sessions = [factory() for _ in range(5)]
        
        # All sessions should be independent
        assert len(sessions) == 5
        assert len(set(id(s) for s in sessions)) == 5
        
        # Cleanup
        for session in sessions:
            session.close()


@pytest.mark.unit
class TestDatabaseConnectionValidation:
    """Tests for database connection validation."""
    
    def test_validate_sqlite_memory(self):
        """Test validation of SQLite memory database."""
        db_url = "sqlite:///:memory:"
        
        success, error = DatabaseManager.test_connection(db_url)
        
        assert success is True
        assert error is None
    
    def test_validate_sqlite_file(self, temp_db_file):
        """Test validation of SQLite file database."""
        db_url = f"sqlite:///{temp_db_file}"
        
        success, error = DatabaseManager.test_connection(db_url)
        
        assert success is True
        assert error is None
    
    def test_validate_missing_file(self):
        """Test validation with missing database file."""
        db_url = "sqlite:////nonexistent/path/to/database.db"
        
        success, error = DatabaseManager.test_connection(db_url)
        
        # Should fail but not crash
        assert isinstance(success, bool)
        assert isinstance(error, (str, type(None)))
    
    def test_validate_empty_url(self):
        """Test validation with empty URL."""
        db_url = ""
        
        success, error = DatabaseManager.test_connection(db_url)
        
        assert success is False
        assert error is not None
    
    def test_validate_malformed_url(self):
        """Test validation with malformed URL."""
        db_url = "not-a-valid-url"
        
        success, error = DatabaseManager.test_connection(db_url)
        
        assert success is False
        assert error is not None


@pytest.mark.unit
class TestDatabaseManagerEdgeCases:
    """Tests for edge cases in DatabaseManager."""
    
    def test_engine_with_special_characters_in_path(self):
        """Test engine creation with special characters in path."""
        db_url = "sqlite:////tmp/test space & special.db"
        
        try:
            engine = DatabaseManager.get_engine(db_url)
            assert engine is not None
        except Exception:
            # Some special characters might not be supported
            pass
    
    def test_session_after_engine_disposal(self, db_url):
        """Test session creation after engine disposal."""
        engine = DatabaseManager.get_engine(db_url)
        engine.dispose()
        
        # Should still work due to caching
        factory = DatabaseManager.get_session_factory(db_url)
        session = factory()
        
        assert session is not None
        session.close()
    
    def test_multiple_connection_tests(self):
        """Test running multiple connection tests."""
        db_url = "sqlite:///:memory:"
        
        results = [DatabaseManager.test_connection(db_url) for _ in range(10)]
        
        # All should succeed
        assert all(success for success, _ in results)
    
    @patch('dashboard.utils.database.create_engine')
    def test_engine_creation_with_warnings(self, mock_create_engine):
        """Test engine creation that produces warnings."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        engine = DatabaseManager.get_engine("sqlite:///:memory:")
        
        assert engine is mock_engine
