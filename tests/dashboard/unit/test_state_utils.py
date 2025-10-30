"""Unit tests for state management utility module."""

import pytest
from unittest.mock import patch, MagicMock
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from dashboard.utils.state import StateManager, SessionKeys, PageNavigator


@pytest.mark.unit
class TestSessionKeys:
    """Tests for SessionKeys enum."""
    
    def test_session_keys_defined(self):
        """Test that all expected session keys are defined."""
        assert hasattr(SessionKeys, 'DB_URL')
        assert hasattr(SessionKeys, 'CURRENT_PAGE')
    
    def test_session_keys_have_values(self):
        """Test that session keys have string values."""
        assert isinstance(SessionKeys.DB_URL.value, str)
        assert isinstance(SessionKeys.CURRENT_PAGE.value, str)
    
    def test_session_keys_unique(self):
        """Test that all session key values are unique."""
        values = [key.value for key in SessionKeys]
        assert len(values) == len(set(values))


@pytest.mark.unit
class TestStateManager:
    """Tests for StateManager class."""
    
    @patch('streamlit.session_state', {})
    def test_init_state_creates_defaults(self):
        """Test that init_state creates default values."""
        with patch('streamlit.session_state', {}) as mock_state:
            StateManager.init_state()
            
            assert SessionKeys.DB_URL.value in mock_state
            assert SessionKeys.CURRENT_PAGE.value in mock_state
    
    @patch('streamlit.session_state', {})
    def test_init_state_preserves_existing(self):
        """Test that init_state preserves existing values."""
        existing_url = "sqlite:///custom.db"
        
        with patch('streamlit.session_state', {SessionKeys.DB_URL.value: existing_url}) as mock_state:
            StateManager.init_state()
            
            assert mock_state[SessionKeys.DB_URL.value] == existing_url
    
    @patch('streamlit.session_state', {})
    def test_init_state_uses_environment_variable(self):
        """Test that init_state uses environment variable for DB_URL."""
        custom_url = "postgresql://localhost/testdb"
        
        with patch.dict(os.environ, {'VMWARE_INV_DB_URL': custom_url}):
            with patch('streamlit.session_state', {}) as mock_state:
                StateManager.init_state()
                
                assert mock_state[SessionKeys.DB_URL.value] == custom_url
    
    @patch('streamlit.session_state', {})
    def test_get_returns_value(self):
        """Test that get returns stored value."""
        test_value = "test_value"
        
        with patch('streamlit.session_state', {SessionKeys.DB_URL.value: test_value}) as mock_state:
            result = StateManager.get(SessionKeys.DB_URL)
            
            assert result == test_value
    
    @patch('streamlit.session_state', {})
    def test_get_returns_default_when_missing(self):
        """Test that get returns default when key is missing."""
        default_value = "default"
        
        with patch('streamlit.session_state', {}) as mock_state:
            result = StateManager.get(SessionKeys.DB_URL, default=default_value)
            
            assert result == default_value
    
    @patch('streamlit.session_state', {})
    def test_get_returns_none_when_missing_no_default(self):
        """Test that get returns None when key is missing and no default."""
        with patch('streamlit.session_state', {}) as mock_state:
            result = StateManager.get(SessionKeys.DB_URL)
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_set_stores_value(self):
        """Test that set stores value in session state."""
        test_value = "new_value"
        
        with patch('streamlit.session_state', {}) as mock_state:
            StateManager.set(SessionKeys.DB_URL, test_value)
            
            assert mock_state[SessionKeys.DB_URL.value] == test_value
    
    @patch('streamlit.session_state', {})
    def test_set_overwrites_existing_value(self):
        """Test that set overwrites existing value."""
        old_value = "old"
        new_value = "new"
        
        with patch('streamlit.session_state', {SessionKeys.DB_URL.value: old_value}) as mock_state:
            StateManager.set(SessionKeys.DB_URL, new_value)
            
            assert mock_state[SessionKeys.DB_URL.value] == new_value
    
    @patch('streamlit.session_state', {})
    def test_has_returns_true_when_exists(self):
        """Test that has returns True when key exists."""
        with patch('streamlit.session_state', {SessionKeys.DB_URL.value: "test"}) as mock_state:
            result = StateManager.has(SessionKeys.DB_URL)
            
            assert result is True
    
    @patch('streamlit.session_state', {})
    def test_has_returns_false_when_missing(self):
        """Test that has returns False when key doesn't exist."""
        with patch('streamlit.session_state', {}) as mock_state:
            result = StateManager.has(SessionKeys.DB_URL)
            
            assert result is False
    
    @patch('streamlit.session_state', {})
    def test_delete_removes_key(self):
        """Test that delete removes key from session state."""
        with patch('streamlit.session_state', {SessionKeys.DB_URL.value: "test"}) as mock_state:
            StateManager.delete(SessionKeys.DB_URL)
            
            assert SessionKeys.DB_URL.value not in mock_state
    
    @patch('streamlit.session_state', {})
    def test_delete_does_not_error_when_missing(self):
        """Test that delete doesn't error when key doesn't exist."""
        with patch('streamlit.session_state', {}) as mock_state:
            # Should not raise
            StateManager.delete(SessionKeys.DB_URL)
            
            assert True
    
    @patch('streamlit.session_state', {})
    def test_clear_all_removes_all_keys(self):
        """Test that clear_all removes all managed keys."""
        with patch('streamlit.session_state', {
            SessionKeys.DB_URL.value: "test1",
            SessionKeys.CURRENT_PAGE.value: "test2",
            'other_key': 'value'
        }) as mock_state:
            StateManager.clear_all()
            
            # Managed keys should be gone
            assert SessionKeys.DB_URL.value not in mock_state
            assert SessionKeys.CURRENT_PAGE.value not in mock_state
            # Other keys might remain (implementation dependent)


@pytest.mark.unit
class TestPageNavigator:
    """Tests for PageNavigator class."""
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_navigate_to_sets_page(self, mock_rerun):
        """Test that navigate_to sets current page."""
        page_name = "Analytics"
        
        with patch('streamlit.session_state', {}) as mock_state:
            PageNavigator.navigate_to(page_name)
            
            assert mock_state[SessionKeys.CURRENT_PAGE.value] == page_name
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_navigate_to_calls_rerun(self, mock_rerun):
        """Test that navigate_to calls st.rerun()."""
        with patch('streamlit.session_state', {}):
            PageNavigator.navigate_to("Overview")
            
            mock_rerun.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_get_current_page_returns_default(self):
        """Test that get_current_page returns default when not set."""
        with patch('streamlit.session_state', {}) as mock_state:
            page = PageNavigator.get_current_page()
            
            assert page == "Overview"
    
    @patch('streamlit.session_state', {})
    def test_get_current_page_returns_stored(self):
        """Test that get_current_page returns stored page."""
        stored_page = "Analytics"
        
        with patch('streamlit.session_state', {SessionKeys.CURRENT_PAGE.value: stored_page}) as mock_state:
            page = PageNavigator.get_current_page()
            
            assert page == stored_page
    
    @patch('streamlit.session_state', {})
    def test_is_current_page_true(self):
        """Test is_current_page returns True for current page."""
        current = "Overview"
        
        with patch('streamlit.session_state', {SessionKeys.CURRENT_PAGE.value: current}) as mock_state:
            result = PageNavigator.is_current_page(current)
            
            assert result is True
    
    @patch('streamlit.session_state', {})
    def test_is_current_page_false(self):
        """Test is_current_page returns False for different page."""
        with patch('streamlit.session_state', {SessionKeys.CURRENT_PAGE.value: "Overview"}) as mock_state:
            result = PageNavigator.is_current_page("Analytics")
            
            assert result is False
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_go_home_navigates_to_overview(self, mock_rerun):
        """Test that go_home navigates to Overview."""
        with patch('streamlit.session_state', {SessionKeys.CURRENT_PAGE.value: "Analytics"}) as mock_state:
            PageNavigator.go_home()
            
            assert mock_state[SessionKeys.CURRENT_PAGE.value] == "Overview"
            mock_rerun.assert_called_once()


@pytest.mark.unit
class TestStateManagerEdgeCases:
    """Tests for edge cases in state management."""
    
    @patch('streamlit.session_state', {})
    def test_get_with_none_value(self):
        """Test getting a key that has None as value."""
        with patch('streamlit.session_state', {SessionKeys.DB_URL.value: None}) as mock_state:
            result = StateManager.get(SessionKeys.DB_URL, default="default")
            
            # Should return None, not default
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_set_with_none_value(self):
        """Test setting a key to None."""
        with patch('streamlit.session_state', {}) as mock_state:
            StateManager.set(SessionKeys.DB_URL, None)
            
            assert SessionKeys.DB_URL.value in mock_state
            assert mock_state[SessionKeys.DB_URL.value] is None
    
    @patch('streamlit.session_state', {})
    def test_concurrent_operations(self):
        """Test multiple state operations in sequence."""
        with patch('streamlit.session_state', {}) as mock_state:
            StateManager.set(SessionKeys.DB_URL, "url1")
            assert StateManager.get(SessionKeys.DB_URL) == "url1"
            
            StateManager.set(SessionKeys.DB_URL, "url2")
            assert StateManager.get(SessionKeys.DB_URL) == "url2"
            
            StateManager.delete(SessionKeys.DB_URL)
            assert StateManager.get(SessionKeys.DB_URL) is None
    
    @patch('streamlit.session_state', {})
    def test_init_state_idempotent(self):
        """Test that calling init_state multiple times is safe."""
        with patch('streamlit.session_state', {}) as mock_state:
            StateManager.init_state()
            first_url = mock_state[SessionKeys.DB_URL.value]
            
            StateManager.init_state()
            second_url = mock_state[SessionKeys.DB_URL.value]
            
            assert first_url == second_url
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_navigate_to_same_page(self, mock_rerun):
        """Test navigating to the same page."""
        page = "Overview"
        
        with patch('streamlit.session_state', {SessionKeys.CURRENT_PAGE.value: page}) as mock_state:
            PageNavigator.navigate_to(page)
            
            # Should still work
            assert mock_state[SessionKeys.CURRENT_PAGE.value] == page
            mock_rerun.assert_called_once()
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_navigate_with_empty_string(self, mock_rerun):
        """Test navigating to empty string page name."""
        with patch('streamlit.session_state', {}) as mock_state:
            PageNavigator.navigate_to("")
            
            assert mock_state[SessionKeys.CURRENT_PAGE.value] == ""
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_navigate_with_special_characters(self, mock_rerun):
        """Test navigating to page with special characters."""
        page_name = "Test/Page-01_Special"
        
        with patch('streamlit.session_state', {}) as mock_state:
            PageNavigator.navigate_to(page_name)
            
            assert mock_state[SessionKeys.CURRENT_PAGE.value] == page_name


@pytest.mark.unit
class TestStateManagerIntegration:
    """Integration tests for state management components."""
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_full_navigation_flow(self, mock_rerun):
        """Test complete navigation flow."""
        with patch('streamlit.session_state', {}) as mock_state:
            # Initialize
            StateManager.init_state()
            
            # Check default page
            assert PageNavigator.get_current_page() == "Overview"
            
            # Navigate to different page
            PageNavigator.navigate_to("Analytics")
            assert PageNavigator.get_current_page() == "Analytics"
            assert PageNavigator.is_current_page("Analytics")
            
            # Navigate home
            PageNavigator.go_home()
            assert PageNavigator.get_current_page() == "Overview"
    
    @patch('streamlit.session_state', {})
    def test_state_persistence_across_operations(self):
        """Test that state persists across operations."""
        with patch('streamlit.session_state', {}) as mock_state:
            StateManager.init_state()
            
            # Set multiple values
            StateManager.set(SessionKeys.DB_URL, "sqlite:///test.db")
            
            # Verify they persist
            assert StateManager.get(SessionKeys.DB_URL) == "sqlite:///test.db"
            assert StateManager.has(SessionKeys.DB_URL)
            
            # Change one value
            StateManager.set(SessionKeys.DB_URL, "sqlite:///new.db")
            
            # Verify change
            assert StateManager.get(SessionKeys.DB_URL) == "sqlite:///new.db"
