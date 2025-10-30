"""State management utilities for Streamlit dashboard.

This module provides centralized session state management with
standardized keys and initialization patterns.
"""

import streamlit as st
import os
from enum import Enum
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class SessionKeys(Enum):
    """Centralized session state keys.
    
    Using an Enum prevents typos and provides autocomplete support.
    """
    # Core application state
    DB_URL = "db_url"
    CURRENT_PAGE = "current_page"
    
    # UI state
    SHOW_SIDEBAR = "show_sidebar"
    THEME = "theme"
    
    # User preferences
    RESULTS_PER_PAGE = "results_per_page"
    DEFAULT_DATACENTER = "default_datacenter"
    SHOW_TEMPLATES = "show_templates"
    
    # Cache management
    CACHE_TIMESTAMP = "cache_timestamp"
    LAST_REFRESH = "last_refresh"
    
    # Backup/Restore state
    CONFIRM_DB_RESTORE = "confirm_db_restore"
    CONFIRM_LABEL_DELETE = "confirm_label_delete"
    
    # Filter state
    SELECTED_DATACENTER = "selected_datacenter"
    SELECTED_CLUSTER = "selected_cluster"
    SELECTED_POWER_STATE = "selected_power_state"
    
    # Search state
    LAST_SEARCH_TERM = "last_search_term"
    USE_REGEX_SEARCH = "use_regex_search"


class StateManager:
    """Manage Streamlit session state with standardized patterns."""
    
    # Default values for session state
    DEFAULTS = {
        SessionKeys.DB_URL: os.environ.get('VMWARE_INV_DB_URL', 'sqlite:///data/vmware_inventory.db'),
        SessionKeys.CURRENT_PAGE: "Overview",
        SessionKeys.SHOW_SIDEBAR: True,
        SessionKeys.THEME: "light",
        SessionKeys.RESULTS_PER_PAGE: 25,
        SessionKeys.SHOW_TEMPLATES: False,
        SessionKeys.USE_REGEX_SEARCH: False,
    }
    
    @staticmethod
    def init_state():
        """Initialize all required session state with defaults.
        
        Call this once at app startup (in app.py).
        
        Example:
            # In app.py
            StateManager.init_state()
        """
        logger.debug("Initializing session state")
        
        for key, default_value in StateManager.DEFAULTS.items():
            if key.value not in st.session_state:
                st.session_state[key.value] = default_value
                logger.debug(f"Initialized {key.value} = {default_value}")
    
    @staticmethod
    def get(key: SessionKeys, default: Any = None) -> Any:
        """Get session state value safely.
        
        Args:
            key: SessionKeys enum value
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
            
        Example:
            db_url = StateManager.get(SessionKeys.DB_URL)
            page_size = StateManager.get(SessionKeys.RESULTS_PER_PAGE, 25)
        """
        return st.session_state.get(key.value, default)
    
    @staticmethod
    def set(key: SessionKeys, value: Any):
        """Set session state value.
        
        Args:
            key: SessionKeys enum value
            value: Value to set
            
        Example:
            StateManager.set(SessionKeys.CURRENT_PAGE, "Overview")
            StateManager.set(SessionKeys.DB_URL, new_url)
        """
        logger.debug(f"Setting {key.value} = {value}")
        st.session_state[key.value] = value
    
    @staticmethod
    def has(key: SessionKeys) -> bool:
        """Check if key exists in session state.
        
        Args:
            key: SessionKeys enum value
            
        Returns:
            True if key exists, False otherwise
            
        Example:
            if StateManager.has(SessionKeys.LAST_SEARCH_TERM):
                # Use cached search term
                pass
        """
        return key.value in st.session_state
    
    @staticmethod
    def delete(key: SessionKeys):
        """Delete key from session state.
        
        Args:
            key: SessionKeys enum value
            
        Example:
            StateManager.delete(SessionKeys.CONFIRM_DB_RESTORE)
        """
        if key.value in st.session_state:
            logger.debug(f"Deleting {key.value}")
            del st.session_state[key.value]
    
    @staticmethod
    def clear_filters():
        """Clear all filter-related state.
        
        Example:
            if st.button("Clear Filters"):
                StateManager.clear_filters()
                st.rerun()
        """
        logger.info("Clearing filter state")
        filter_keys = [
            SessionKeys.SELECTED_DATACENTER,
            SessionKeys.SELECTED_CLUSTER,
            SessionKeys.SELECTED_POWER_STATE,
            SessionKeys.LAST_SEARCH_TERM,
        ]
        
        for key in filter_keys:
            StateManager.delete(key)
    
    @staticmethod
    def clear_confirmations():
        """Clear all confirmation state.
        
        Use this after operations that required confirmation.
        
        Example:
            # After successful restore
            StateManager.clear_confirmations()
        """
        logger.info("Clearing confirmation state")
        confirmation_keys = [
            SessionKeys.CONFIRM_DB_RESTORE,
            SessionKeys.CONFIRM_LABEL_DELETE,
        ]
        
        for key in confirmation_keys:
            StateManager.delete(key)
    
    @staticmethod
    def reset_to_defaults():
        """Reset all state to default values.
        
        Example:
            if st.button("Reset App"):
                StateManager.reset_to_defaults()
                st.rerun()
        """
        logger.warning("Resetting state to defaults")
        
        for key, default_value in StateManager.DEFAULTS.items():
            StateManager.set(key, default_value)
    
    @staticmethod
    def get_state_summary() -> dict:
        """Get summary of current session state.
        
        Useful for debugging and diagnostics.
        
        Returns:
            Dictionary with state information
            
        Example:
            if st.checkbox("Show State"):
                summary = StateManager.get_state_summary()
                st.json(summary)
        """
        return {
            "initialized_keys": [
                key.value for key in SessionKeys 
                if key.value in st.session_state
            ],
            "total_keys": len(st.session_state),
            "current_page": StateManager.get(SessionKeys.CURRENT_PAGE, "Unknown"),
            "db_url_set": StateManager.has(SessionKeys.DB_URL),
        }
    
    @staticmethod
    def show_debug_info():
        """Display debug information about session state.
        
        Use in a sidebar expander for development/debugging.
        
        Example:
            # In app.py sidebar
            if os.environ.get('DEBUG'):
                with st.expander("🐛 Debug Info"):
                    StateManager.show_debug_info()
        """
        st.markdown("**Session State Debug**")
        
        summary = StateManager.get_state_summary()
        st.json(summary)
        
        # Show all state (careful with sensitive data)
        with st.expander("Full State"):
            st.write(dict(st.session_state))


class PageNavigator:
    """Helper for page navigation management."""
    
    PAGES = {
        "dashboards": ["Overview", "Resources", "Infrastructure", "Folder Analysis"],
        "analysis": ["VM Explorer", "VM Search", "Analytics", "Comparison", "Data Quality"],
        "tools": ["Folder Labelling"],
        "system": ["Data Import", "Database Backup", "Migration Planning", "PDF Export", "Help"],
    }
    
    @staticmethod
    def navigate_to(page_name: str):
        """Navigate to a specific page.
        
        Args:
            page_name: Name of the page to navigate to
            
        Example:
            if st.button("Go to Overview"):
                PageNavigator.navigate_to("Overview")
        """
        if PageNavigator.is_valid_page(page_name):
            StateManager.set(SessionKeys.CURRENT_PAGE, page_name)
            st.rerun()
        else:
            logger.warning(f"Attempted to navigate to invalid page: {page_name}")
    
    @staticmethod
    def get_current_page() -> str:
        """Get current page name.
        
        Returns:
            Current page name
        """
        return StateManager.get(SessionKeys.CURRENT_PAGE, "Overview")
    
    @staticmethod
    def is_valid_page(page_name: str) -> bool:
        """Check if page name is valid.
        
        Args:
            page_name: Page name to check
            
        Returns:
            True if valid page, False otherwise
        """
        all_pages = [
            page for pages in PageNavigator.PAGES.values() 
            for page in pages
        ]
        return page_name in all_pages
    
    @staticmethod
    def get_page_category(page_name: str) -> Optional[str]:
        """Get category for a page.
        
        Args:
            page_name: Page name
            
        Returns:
            Category name or None if not found
        """
        for category, pages in PageNavigator.PAGES.items():
            if page_name in pages:
                return category
        return None
