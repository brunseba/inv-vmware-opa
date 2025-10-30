"""Error handling utilities for Streamlit dashboard.

This module provides standardized error display and logging for the dashboard.
"""

import streamlit as st
import traceback
import logging
from typing import Optional
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Standardized error handling for Streamlit pages."""
    
    @staticmethod
    def show_error(error: Exception, show_details: bool = True, context: Optional[str] = None):
        """Display error with consistent formatting.
        
        Args:
            error: The exception that occurred
            show_details: Whether to show detailed traceback
            context: Optional context string (e.g., "loading data", "saving backup")
            
        Example:
            try:
                # Some operation
                pass
            except Exception as e:
                ErrorHandler.show_error(e, context="loading data")
        """
        # Log the error
        logger.error(f"Error{f' in {context}' if context else ''}: {str(error)}", exc_info=True)
        
        # Display user-friendly message
        context_msg = f" {context}" if context else ""
        st.error(f"❌ Error{context_msg}: {str(error)}")
        
        # Show details if requested
        if show_details:
            with st.expander("🔍 Show error details"):
                st.code(traceback.format_exc())
                
                # Add helpful hints based on error type
                ErrorHandler._show_hints(error)
    
    @staticmethod
    def _show_hints(error: Exception):
        """Show context-specific hints based on error type."""
        error_type = type(error).__name__
        
        hints = {
            "OperationalError": "💡 **Hint:** This might be a database connection issue. Try:\n- Checking the database URL\n- Verifying the database file exists\n- Checking file permissions",
            "IntegrityError": "💡 **Hint:** This is a database integrity issue. The data might be corrupted or have constraint violations.",
            "FileNotFoundError": "💡 **Hint:** The file doesn't exist. Check:\n- The file path is correct\n- The file hasn't been moved\n- You have permission to access it",
            "PermissionError": "💡 **Hint:** Permission denied. Check:\n- File/folder permissions\n- You have write access (if saving)\n- The file isn't locked by another process",
        }
        
        if error_type in hints:
            st.info(hints[error_type])
    
    @staticmethod
    def show_warning(message: str, icon: str = "⚠️"):
        """Display standardized warning message.
        
        Args:
            message: Warning message to display
            icon: Icon to show (default: ⚠️)
        """
        st.warning(f"{icon} {message}")
        logger.warning(message)
    
    @staticmethod
    def show_info(message: str, icon: str = "ℹ️"):
        """Display standardized info message.
        
        Args:
            message: Info message to display
            icon: Icon to show (default: ℹ️)
        """
        st.info(f"{icon} {message}")
        logger.info(message)
    
    @staticmethod
    def show_success(message: str, icon: str = "✅"):
        """Display standardized success message.
        
        Args:
            message: Success message to display
            icon: Icon to show (default: ✅)
        """
        st.success(f"{icon} {message}")
        logger.info(f"Success: {message}")
    
    @staticmethod
    def handle_page_error(func):
        """Decorator to handle errors in page render functions.
        
        Wraps page render functions with standardized error handling.
        
        Example:
            @ErrorHandler.handle_page_error
            def render(db_url: str):
                # Page logic that might fail
                pass
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                page_name = func.__module__.split('.')[-1]
                ErrorHandler.show_error(e, context=f"rendering {page_name} page")
        return wrapper


class DataValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_not_empty(value: str, field_name: str = "Field") -> tuple[bool, str]:
        """Validate that a string is not empty.
        
        Args:
            value: String to validate
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value or not value.strip():
            return False, f"{field_name} cannot be empty"
        return True, ""
    
    @staticmethod
    def validate_positive_number(value: float, field_name: str = "Value") -> tuple[bool, str]:
        """Validate that a number is positive.
        
        Args:
            value: Number to validate
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if value <= 0:
            return False, f"{field_name} must be positive"
        return True, ""
    
    @staticmethod
    def validate_date_range(start, end) -> tuple[bool, str]:
        """Validate date range.
        
        Args:
            start: Start date
            end: End date
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if start and end and start > end:
            return False, "Start date must be before end date"
        return True, ""
    
    @staticmethod
    def validate_file_size(file, max_size_mb: int = 100) -> tuple[bool, str]:
        """Validate uploaded file size.
        
        Args:
            file: Streamlit uploaded file
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if file and file.size > max_size_mb * 1024 * 1024:
            return False, f"File too large (max {max_size_mb}MB)"
        return True, ""
    
    @staticmethod
    def validate_regex(pattern: str, max_length: int = 1000) -> tuple[bool, str]:
        """Validate regex pattern.
        
        Args:
            pattern: Regex pattern to validate
            max_length: Maximum pattern length
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
            
        Example:
            is_valid, error_msg = DataValidator.validate_regex("^test.*")
            if not is_valid:
                st.error(error_msg)
        """
        import re
        
        if not pattern:
            return False, "Pattern cannot be empty"
        
        if len(pattern) > max_length:
            return False, f"Pattern too long (max {max_length} characters)"
        
        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, f"Invalid regex pattern: {str(e)}"
    
    @staticmethod
    def validate_string_length(value: str, max_length: int, 
                              field_name: str = "Field") -> tuple[bool, str]:
        """Validate string length.
        
        Args:
            value: String to validate
            max_length: Maximum allowed length
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
            
        Example:
            is_valid, error = DataValidator.validate_string_length(name, 100, "VM Name")
        """
        if not value:
            return True, ""  # Empty is OK, use validate_not_empty separately if needed
        
        if len(value) > max_length:
            return False, f"{field_name} too long (max {max_length} characters, got {len(value)})"
        
        return True, ""
    
    @staticmethod
    def validate_number_range(value: float, min_val: float, max_val: float,
                             field_name: str = "Value") -> tuple[bool, str]:
        """Validate number is within range.
        
        Args:
            value: Number to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
            
        Example:
            is_valid, error = DataValidator.validate_number_range(cpu_count, 1, 64, "CPUs")
        """
        if value < min_val or value > max_val:
            return False, f"{field_name} must be between {min_val} and {max_val} (got {value})"
        
        return True, ""
    
    @staticmethod
    def validate_choice(value: str, choices: list, field_name: str = "Value") -> tuple[bool, str]:
        """Validate value is in allowed choices.
        
        Args:
            value: Value to validate
            choices: List of allowed choices
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
            
        Example:
            is_valid, error = DataValidator.validate_choice(state, ["poweredOn", "poweredOff"], "Power State")
        """
        if value not in choices:
            return False, f"{field_name} must be one of: {', '.join(map(str, choices))}"
        
        return True, ""


def safe_query(func):
    """Decorator for safe database queries with error handling.
    
    Example:
        @safe_query
        def get_vm_count(session):
            return session.query(VirtualMachine).count()
        
        # Returns None if query fails
        count = get_vm_count(session)
        if count is None:
            st.error("Failed to get VM count")
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Query failed in {func.__name__}: {e}")
            return None
    return wrapper
