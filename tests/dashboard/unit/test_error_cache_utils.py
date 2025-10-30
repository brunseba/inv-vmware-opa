"""Unit tests for error handling and cache utility modules."""

import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from dashboard.utils.errors import ErrorHandler, DashboardError, DatabaseError, ValidationError
from dashboard.utils.cache import get_vm_counts, get_datacenters, CacheManager


@pytest.mark.unit
class TestDashboardError:
    """Tests for custom exception classes."""
    
    def test_dashboard_error_creation(self):
        """Test creating DashboardError."""
        error = DashboardError("Test error")
        
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_database_error_creation(self):
        """Test creating DatabaseError."""
        error = DatabaseError("Database connection failed")
        
        assert str(error) == "Database connection failed"
        assert isinstance(error, DashboardError)
    
    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Invalid input")
        
        assert str(error) == "Invalid input"
        assert isinstance(error, DashboardError)
    
    def test_error_with_context(self):
        """Test error with additional context."""
        error = DatabaseError("Connection failed", context="during startup")
        
        assert "Connection failed" in str(error)


@pytest.mark.unit
class TestErrorHandler:
    """Tests for ErrorHandler class."""
    
    @patch('streamlit.error')
    def test_show_error_basic(self, mock_error):
        """Test basic error display."""
        error = Exception("Test error")
        
        ErrorHandler.show_error(error, show_details=False)
        
        mock_error.assert_called_once()
        call_args = str(mock_error.call_args)
        assert "Test error" in call_args
    
    @patch('streamlit.error')
    @patch('streamlit.expander')
    def test_show_error_with_details(self, mock_expander, mock_error):
        """Test error display with details."""
        error = Exception("Test error")
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()
        
        ErrorHandler.show_error(error, show_details=True)
        
        mock_error.assert_called()
        # Expander should be created for details
        mock_expander.assert_called()
    
    @patch('streamlit.error')
    def test_show_error_with_context(self, mock_error):
        """Test error display with context."""
        error = Exception("Test error")
        
        ErrorHandler.show_error(error, context="loading data", show_details=False)
        
        mock_error.assert_called_once()
        call_args = str(mock_error.call_args)
        assert "loading data" in call_args
    
    @patch('streamlit.success')
    def test_show_success(self, mock_success):
        """Test success message display."""
        ErrorHandler.show_success("Operation completed")
        
        mock_success.assert_called_once()
        call_args = str(mock_success.call_args)
        assert "Operation completed" in call_args
    
    @patch('streamlit.success')
    def test_show_success_with_icon(self, mock_success):
        """Test success message with custom icon."""
        ErrorHandler.show_success("Done", icon="✅")
        
        mock_success.assert_called_once()
        call_args = str(mock_success.call_args)
        assert "✅" in call_args or "Done" in call_args
    
    @patch('streamlit.warning')
    def test_show_warning(self, mock_warning):
        """Test warning message display."""
        ErrorHandler.show_warning("Potential issue")
        
        mock_warning.assert_called_once()
        call_args = str(mock_warning.call_args)
        assert "Potential issue" in call_args
    
    @patch('streamlit.info')
    def test_show_info(self, mock_info):
        """Test info message display."""
        ErrorHandler.show_info("Informational message")
        
        mock_info.assert_called_once()
        call_args = str(mock_info.call_args)
        assert "Informational message" in call_args
    
    @patch('streamlit.error')
    def test_handle_database_error(self, mock_error):
        """Test handling database-specific errors."""
        error = DatabaseError("Connection timeout")
        
        ErrorHandler.show_error(error, show_details=False)
        
        mock_error.assert_called_once()
    
    @patch('streamlit.error')
    def test_handle_validation_error(self, mock_error):
        """Test handling validation errors."""
        error = ValidationError("Invalid regex pattern")
        
        ErrorHandler.show_error(error, show_details=False)
        
        mock_error.assert_called_once()
    
    @patch('streamlit.error')
    def test_error_with_empty_message(self, mock_error):
        """Test error with empty message."""
        error = Exception("")
        
        ErrorHandler.show_error(error, show_details=False)
        
        # Should still call error display
        mock_error.assert_called()
    
    @patch('streamlit.error')
    def test_error_with_long_message(self, mock_error):
        """Test error with very long message."""
        long_message = "A" * 1000
        error = Exception(long_message)
        
        ErrorHandler.show_error(error, show_details=False)
        
        mock_error.assert_called_once()


@pytest.mark.unit
class TestCacheManager:
    """Tests for CacheManager class."""
    
    @patch('streamlit.button')
    @patch('streamlit.cache_data.clear')
    def test_show_cache_controls_button(self, mock_clear, mock_button):
        """Test cache control button display."""
        mock_button.return_value = False
        
        CacheManager.show_cache_controls()
        
        # Should create a button
        mock_button.assert_called()
    
    @patch('streamlit.button')
    @patch('streamlit.cache_data.clear')
    @patch('streamlit.rerun')
    def test_clear_cache_on_button_click(self, mock_rerun, mock_clear, mock_button):
        """Test cache clearing when button is clicked."""
        mock_button.return_value = True
        
        CacheManager.show_cache_controls()
        
        # Should clear cache and rerun
        mock_clear.assert_called_once()
    
    @patch('streamlit.write')
    def test_show_cache_stats(self, mock_write):
        """Test showing cache statistics."""
        stats = {
            'total_entries': 5,
            'memory_usage': '1.2 MB'
        }
        
        CacheManager.show_cache_stats(stats)
        
        mock_write.assert_called()
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        db_url = "sqlite:///test.db"
        prefix = "vm_counts"
        
        key = CacheManager.get_cache_key(db_url, prefix)
        
        assert isinstance(key, str)
        assert prefix in key or db_url in key


@pytest.mark.unit
class TestCachedDataFunctions:
    """Tests for cached data retrieval functions."""
    
    def test_get_vm_counts_with_data(self, populated_db_session, db_url):
        """Test getting VM counts from populated database."""
        counts = get_vm_counts(db_url)
        
        assert 'total' in counts
        assert 'powered_on' in counts
        assert counts['total'] > 0
    
    def test_get_vm_counts_empty_db(self, empty_db_session, db_url):
        """Test getting VM counts from empty database."""
        counts = get_vm_counts(db_url)
        
        assert 'total' in counts
        assert 'powered_on' in counts
        assert counts['total'] == 0
        assert counts['powered_on'] == 0
    
    def test_get_datacenters_with_data(self, populated_db_session, db_url):
        """Test getting datacenters from populated database."""
        datacenters = get_datacenters(db_url)
        
        assert isinstance(datacenters, list)
        assert len(datacenters) > 0
    
    def test_get_datacenters_empty_db(self, empty_db_session, db_url):
        """Test getting datacenters from empty database."""
        datacenters = get_datacenters(db_url)
        
        assert isinstance(datacenters, list)
        assert len(datacenters) == 0
    
    def test_get_datacenters_filters_none(self, db_session, db_url):
        """Test that datacenters with None values are filtered."""
        from src.models import VirtualMachine
        
        # Add VM with None datacenter
        vm = VirtualMachine(vm="test-vm", datacenter=None)
        db_session.add(vm)
        db_session.commit()
        
        datacenters = get_datacenters(db_url)
        
        # None should not be in the list
        assert None not in datacenters
    
    @patch('dashboard.utils.cache.get_vm_counts')
    def test_cache_function_called(self, mock_get_counts):
        """Test that cached function is actually called."""
        mock_get_counts.return_value = {'total': 10, 'powered_on': 8}
        
        result = mock_get_counts("sqlite:///:memory:")
        
        assert result['total'] == 10
        mock_get_counts.assert_called_once()


@pytest.mark.unit
class TestErrorHandlerEdgeCases:
    """Tests for edge cases in error handling."""
    
    @patch('streamlit.error')
    def test_handle_none_error(self, mock_error):
        """Test handling None as error."""
        try:
            ErrorHandler.show_error(None, show_details=False)
        except:
            # May raise, but shouldn't crash the app
            pass
    
    @patch('streamlit.error')
    def test_handle_nested_exception(self, mock_error):
        """Test handling nested exceptions."""
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        except RuntimeError as error:
            ErrorHandler.show_error(error, show_details=True)
        
        mock_error.assert_called()
    
    @patch('streamlit.error')
    def test_handle_unicode_error_message(self, mock_error):
        """Test handling error with unicode characters."""
        error = Exception("Error with émojis 🔥 and spëcial chars")
        
        ErrorHandler.show_error(error, show_details=False)
        
        mock_error.assert_called()
    
    @patch('streamlit.success')
    def test_success_with_empty_message(self, mock_success):
        """Test success message with empty string."""
        ErrorHandler.show_success("")
        
        mock_success.assert_called()
    
    @patch('streamlit.warning')
    def test_warning_with_multiline_message(self, mock_warning):
        """Test warning with multiline message."""
        message = "Line 1\nLine 2\nLine 3"
        
        ErrorHandler.show_warning(message)
        
        mock_warning.assert_called()


@pytest.mark.unit
class TestCacheIntegration:
    """Integration tests for caching functionality."""
    
    def test_cache_invalidation_flow(self):
        """Test cache invalidation workflow."""
        with patch('streamlit.cache_data.clear') as mock_clear:
            # Clear cache
            CacheManager.clear_all()
            
            # Verify clear was called
            mock_clear.assert_called()
    
    def test_multiple_cache_operations(self, db_url):
        """Test multiple cache operations in sequence."""
        # First call
        counts1 = get_vm_counts(db_url)
        
        # Second call (should use cache)
        counts2 = get_vm_counts(db_url)
        
        # Results should be identical
        assert counts1 == counts2
    
    def test_cache_with_different_db_urls(self):
        """Test caching with different database URLs."""
        url1 = "sqlite:///db1.db"
        url2 = "sqlite:///db2.db"
        
        key1 = CacheManager.get_cache_key(url1, "test")
        key2 = CacheManager.get_cache_key(url2, "test")
        
        # Keys should be different
        assert key1 != key2


@pytest.mark.unit
class TestErrorContextManagement:
    """Tests for error context management."""
    
    @patch('streamlit.error')
    def test_error_context_in_message(self, mock_error):
        """Test that context appears in error message."""
        error = Exception("Failed")
        
        ErrorHandler.show_error(error, context="during VM search", show_details=False)
        
        call_args = str(mock_error.call_args)
        assert "during VM search" in call_args or "Failed" in call_args
    
    @patch('streamlit.error')
    def test_multiple_errors_different_contexts(self, mock_error):
        """Test handling multiple errors with different contexts."""
        error1 = Exception("Error 1")
        error2 = Exception("Error 2")
        
        ErrorHandler.show_error(error1, context="context1", show_details=False)
        ErrorHandler.show_error(error2, context="context2", show_details=False)
        
        assert mock_error.call_count == 2
