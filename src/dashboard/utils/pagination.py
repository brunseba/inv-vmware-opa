"""Pagination utilities for Streamlit dashboard.

This module provides pagination functionality for handling large datasets
efficiently without loading everything into memory.
"""

import streamlit as st
from sqlalchemy.orm import Query
from typing import Any, Callable, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# Configuration constants
MAX_RESULTS_DISPLAY = 1000  # Maximum results to display without warning
MAX_FETCH_SIZE = 10000      # Maximum results to fetch from database
DEFAULT_PAGE_SIZE = 25       # Default items per page
PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 200]  # Available page size options


class PaginationConfig:
    """Configuration for pagination behavior."""
    
    def __init__(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_display: int = MAX_RESULTS_DISPLAY,
        max_fetch: int = MAX_FETCH_SIZE,
        show_total: bool = True,
        show_page_selector: bool = True
    ):
        """Initialize pagination configuration.
        
        Args:
            page_size: Items per page
            max_display: Max items to display (show warning if exceeded)
            max_fetch: Max items to fetch from database
            show_total: Whether to show total count
            show_page_selector: Whether to show page selector UI
        """
        self.page_size = page_size
        self.max_display = max_display
        self.max_fetch = max_fetch
        self.show_total = show_total
        self.show_page_selector = show_page_selector


class PaginatedResult:
    """Result of a paginated query."""
    
    def __init__(self, items: list, total: int, page: int, page_size: int):
        """Initialize paginated result.
        
        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number (1-indexed)
            page_size: Items per page
        """
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        self.has_next = page < self.total_pages
        self.has_prev = page > 1
        self.start_idx = (page - 1) * page_size + 1
        self.end_idx = min(page * page_size, total)
    
    def __repr__(self):
        return f"<PaginatedResult page={self.page}/{self.total_pages} items={len(self.items)} total={self.total}>"


def paginate_query(
    query: Query,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    count_query: Optional[Query] = None
) -> PaginatedResult:
    """Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query to paginate
        page: Page number (1-indexed)
        page_size: Items per page
        count_query: Optional separate query for counting (for optimization)
        
    Returns:
        PaginatedResult with items and metadata
        
    Example:
        query = session.query(VirtualMachine).filter(...)
        result = paginate_query(query, page=2, page_size=50)
        
        for vm in result.items:
            st.write(vm.vm)
            
        st.write(f"Showing {result.start_idx}-{result.end_idx} of {result.total}")
    """
    # Get total count
    if count_query:
        total = count_query.count()
    else:
        total = query.count()
    
    # Ensure page is valid
    page = max(1, page)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    page = min(page, total_pages)
    
    # Get items for current page
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    logger.debug(f"Paginated query: page={page}, size={page_size}, total={total}, fetched={len(items)}")
    
    return PaginatedResult(items, total, page, page_size)


def show_pagination_controls(
    result: PaginatedResult,
    key_prefix: str = "pagination"
) -> int:
    """Display pagination controls and return selected page.
    
    Args:
        result: PaginatedResult from paginate_query
        key_prefix: Prefix for Streamlit widget keys (for multiple paginations on same page)
        
    Returns:
        Selected page number
        
    Example:
        result = paginate_query(query, page, page_size)
        new_page = show_pagination_controls(result)
        if new_page != page:
            st.rerun()
    """
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        # Page size selector
        page_size = st.selectbox(
            "Per page",
            options=PAGE_SIZE_OPTIONS,
            index=PAGE_SIZE_OPTIONS.index(result.page_size) if result.page_size in PAGE_SIZE_OPTIONS else 1,
            key=f"{key_prefix}_page_size"
        )
    
    with col2:
        # Page number input
        new_page = st.number_input(
            f"Page (1-{result.total_pages})",
            min_value=1,
            max_value=result.total_pages,
            value=result.page,
            key=f"{key_prefix}_page_num"
        )
    
    with col3:
        # Navigation buttons
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            if st.button("◀ Prev", disabled=not result.has_prev, key=f"{key_prefix}_prev"):
                new_page = result.page - 1
        with subcol2:
            if st.button("Next ▶", disabled=not result.has_next, key=f"{key_prefix}_next"):
                new_page = result.page + 1
    
    # Show info
    st.caption(f"Showing {result.start_idx:,}-{result.end_idx:,} of {result.total:,} results")
    
    return new_page


def show_results_warning(total: int, config: PaginationConfig):
    """Show warning if result set is large.
    
    Args:
        total: Total number of results
        config: Pagination configuration
    """
    if total > config.max_display:
        st.warning(
            f"⚠️ Large result set ({total:,} items). "
            f"Showing first {config.max_display:,} results. "
            f"Use filters to narrow down your search for better performance.",
            icon="⚠️"
        )
    elif total > config.max_fetch:
        st.error(
            f"❌ Result set too large ({total:,} items exceeds limit of {config.max_fetch:,}). "
            f"Please use filters to narrow down your search.",
            icon="❌"
        )


def limit_query(query: Query, config: PaginationConfig) -> Query:
    """Apply hard limit to query based on configuration.
    
    Args:
        query: SQLAlchemy query
        config: Pagination configuration
        
    Returns:
        Query with limit applied
    """
    return query.limit(config.max_fetch)


@st.cache_data(ttl=60)
def paginate_with_cache(
    query_func: Callable,
    query_key: str,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    **query_kwargs
) -> dict:
    """Cached pagination function.
    
    Args:
        query_func: Function that returns a SQLAlchemy query
        query_key: Unique key for caching
        page: Page number
        page_size: Items per page
        **query_kwargs: Additional arguments to pass to query_func
        
    Returns:
        Dictionary with items, total, page, page_size
        
    Example:
        def get_vms_query(db_url, datacenter):
            engine = create_engine(db_url)
            session = Session(engine)
            query = session.query(VirtualMachine)
            if datacenter:
                query = query.filter(VirtualMachine.datacenter == datacenter)
            return query
        
        result = paginate_with_cache(
            get_vms_query,
            query_key=f"vms_{datacenter}",
            page=page,
            page_size=25,
            db_url=db_url,
            datacenter=datacenter
        )
    """
    query = query_func(**query_kwargs)
    result = paginate_query(query, page, page_size)
    
    return {
        'items': result.items,
        'total': result.total,
        'page': result.page,
        'page_size': result.page_size,
        'total_pages': result.total_pages,
        'has_next': result.has_next,
        'has_prev': result.has_prev,
        'start_idx': result.start_idx,
        'end_idx': result.end_idx
    }


class PaginationState:
    """Manage pagination state in session state."""
    
    def __init__(self, key: str, default_page_size: int = DEFAULT_PAGE_SIZE):
        """Initialize pagination state manager.
        
        Args:
            key: Unique key for this pagination instance
            default_page_size: Default page size
        """
        self.key = key
        self.default_page_size = default_page_size
        self._init_state()
    
    def _init_state(self):
        """Initialize session state for pagination."""
        page_key = f"{self.key}_page"
        size_key = f"{self.key}_page_size"
        
        if page_key not in st.session_state:
            st.session_state[page_key] = 1
        
        if size_key not in st.session_state:
            st.session_state[size_key] = self.default_page_size
    
    @property
    def page(self) -> int:
        """Get current page number."""
        return st.session_state.get(f"{self.key}_page", 1)
    
    @page.setter
    def page(self, value: int):
        """Set current page number."""
        st.session_state[f"{self.key}_page"] = max(1, value)
    
    @property
    def page_size(self) -> int:
        """Get current page size."""
        return st.session_state.get(f"{self.key}_page_size", self.default_page_size)
    
    @page_size.setter
    def page_size(self, value: int):
        """Set current page size."""
        st.session_state[f"{self.key}_page_size"] = value
        # Reset to page 1 when page size changes
        self.page = 1
    
    def reset(self):
        """Reset pagination state to defaults."""
        self.page = 1
        self.page_size = self.default_page_size
