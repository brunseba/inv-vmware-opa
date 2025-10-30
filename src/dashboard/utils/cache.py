"""Caching utilities for Streamlit dashboard.

This module provides cached query functions for common database operations
to improve performance and reduce database load.
"""

import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.models import VirtualMachine, Label
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


# Cache TTL constants (in seconds)
CACHE_TTL_SHORT = 60        # 1 minute - for frequently changing data
CACHE_TTL_MEDIUM = 300      # 5 minutes - for moderately stable data
CACHE_TTL_LONG = 1800       # 30 minutes - for rarely changing data


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def get_datacenters(db_url: str) -> List[str]:
    """Get list of unique datacenters with caching.
    
    Args:
        db_url: Database URL
        
    Returns:
        List of datacenter names
    """
    from .database import DatabaseManager
    
    with DatabaseManager.session_scope(db_url) as session:
        result = session.query(VirtualMachine.datacenter).distinct().all()
        return [dc[0] for dc in result if dc[0]]


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def get_clusters(db_url: str) -> List[str]:
    """Get list of unique clusters with caching.
    
    Args:
        db_url: Database URL
        
    Returns:
        List of cluster names
    """
    from .database import DatabaseManager
    
    with DatabaseManager.session_scope(db_url) as session:
        result = session.query(VirtualMachine.cluster).distinct().all()
        return [cluster[0] for cluster in result if cluster[0]]


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def get_power_states(db_url: str) -> List[str]:
    """Get list of unique power states with caching.
    
    Args:
        db_url: Database URL
        
    Returns:
        List of power state names
    """
    from .database import DatabaseManager
    
    with DatabaseManager.session_scope(db_url) as session:
        result = session.query(VirtualMachine.powerstate).distinct().all()
        return [ps[0] for ps in result if ps[0]]


@st.cache_data(ttl=CACHE_TTL_SHORT)
def get_vm_counts(db_url: str) -> Dict[str, int]:
    """Get VM counts with caching.
    
    Args:
        db_url: Database URL
        
    Returns:
        Dictionary with count metrics:
        - total: Total VM count
        - powered_on: Count of powered-on VMs
        - powered_off: Count of powered-off VMs
        - suspended: Count of suspended VMs
    """
    from .database import DatabaseManager
    from sqlalchemy import inspect
    
    try:
        with DatabaseManager.session_scope(db_url) as session:
            # Check if virtual_machines table exists
            inspector = inspect(session.bind)
            if 'virtual_machines' not in inspector.get_table_names():
                return {
                    "total": 0,
                    "powered_on": 0,
                    "powered_off": 0,
                    "suspended": 0
                }
            
            total = session.query(func.count(VirtualMachine.id)).scalar() or 0
            
            powered_on = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.powerstate == "poweredOn"
            ).scalar() or 0
            
            powered_off = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.powerstate == "poweredOff"
            ).scalar() or 0
            
            suspended = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.powerstate == "suspended"
            ).scalar() or 0
            
            return {
                "total": total,
                "powered_on": powered_on,
                "powered_off": powered_off,
                "suspended": suspended
            }
    except Exception as e:
        logger.warning(f"Error getting VM counts: {e}")
        return {
            "total": 0,
            "powered_on": 0,
            "powered_off": 0,
            "suspended": 0
        }


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def get_resource_totals(db_url: str) -> Dict[str, Any]:
    """Get total resources with caching.
    
    Args:
        db_url: Database URL
        
    Returns:
        Dictionary with resource metrics:
        - total_cpus: Total vCPUs
        - total_memory_gb: Total memory in GB
        - datacenter_count: Number of datacenters
        - cluster_count: Number of clusters
        - host_count: Number of hosts
    """
    from .database import DatabaseManager
    
    with DatabaseManager.session_scope(db_url) as session:
        total_cpus = session.query(func.sum(VirtualMachine.cpus)).scalar() or 0
        total_memory_mb = session.query(func.sum(VirtualMachine.memory)).scalar() or 0
        
        dc_count = session.query(func.count(func.distinct(VirtualMachine.datacenter))).scalar() or 0
        cluster_count = session.query(func.count(func.distinct(VirtualMachine.cluster))).scalar() or 0
        host_count = session.query(func.count(func.distinct(VirtualMachine.host))).scalar() or 0
        
        return {
            "total_cpus": int(total_cpus),
            "total_memory_gb": round(total_memory_mb / 1024, 2),
            "datacenter_count": dc_count,
            "cluster_count": cluster_count,
            "host_count": host_count
        }


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def get_data_quality_metrics(db_url: str) -> Dict[str, int]:
    """Get data quality metrics with caching.
    
    Args:
        db_url: Database URL
        
    Returns:
        Dictionary with quality metrics:
        - missing_dns: Count of VMs without DNS name
        - missing_ip: Count of VMs without IP address
        - templates: Count of template VMs
    """
    from .database import DatabaseManager
    
    with DatabaseManager.session_scope(db_url) as session:
        missing_dns = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.dns_name.is_(None)
        ).scalar() or 0
        
        missing_ip = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.primary_ip_address.is_(None)
        ).scalar() or 0
        
        templates = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.template.is_(True)
        ).scalar() or 0
        
        return {
            "missing_dns": missing_dns,
            "missing_ip": missing_ip,
            "templates": templates
        }


@st.cache_data(ttl=CACHE_TTL_LONG)
def get_label_keys(db_url: str) -> List[str]:
    """Get list of unique label keys with caching.
    
    Args:
        db_url: Database URL
        
    Returns:
        List of label key names
    """
    from .database import DatabaseManager
    
    with DatabaseManager.session_scope(db_url) as session:
        result = session.query(Label.key).distinct().all()
        return [key[0] for key in result if key[0]]


@st.cache_data(ttl=CACHE_TTL_LONG)
def get_label_values(db_url: str, key: str) -> List[str]:
    """Get list of values for a specific label key with caching.
    
    Args:
        db_url: Database URL
        key: Label key to get values for
        
    Returns:
        List of label values
    """
    from .database import DatabaseManager
    
    with DatabaseManager.session_scope(db_url) as session:
        result = session.query(Label.value).filter(Label.key == key).distinct().all()
        return [value[0] for value in result if value[0]]


def clear_all_caches():
    """Clear all cached data.
    
    Use this when data changes or to force refresh.
    
    Example:
        if st.button("🔄 Refresh Data"):
            clear_all_caches()
            st.rerun()
    """
    logger.info("Clearing all caches")
    st.cache_data.clear()
    
    # Also clear resource cache if needed
    from .database import DatabaseManager
    DatabaseManager.clear_cache()


def clear_cache_for_function(func):
    """Clear cache for a specific function.
    
    Args:
        func: The function whose cache to clear
        
    Example:
        clear_cache_for_function(get_vm_counts)
    """
    logger.info(f"Clearing cache for {func.__name__}")
    func.clear()


class CacheManager:
    """Manage cache lifecycle and statistics."""
    
    @staticmethod
    def get_cache_info():
        """Get information about cached functions.
        
        Returns:
            Dictionary with cache statistics
        """
        cached_functions = [
            get_datacenters,
            get_clusters,
            get_power_states,
            get_vm_counts,
            get_resource_totals,
            get_data_quality_metrics,
            get_label_keys,
            get_label_values
        ]
        
        return {
            "total_functions": len(cached_functions),
            "function_names": [f.__name__ for f in cached_functions]
        }
    
    @staticmethod
    def show_cache_controls():
        """Display cache control UI in sidebar.
        
        Example:
            # In app.py sidebar
            with st.expander("🔄 Cache Controls"):
                CacheManager.show_cache_controls()
        """
        st.markdown("**Cache Management**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Clear Data Cache", key="clear_data_cache"):
                st.cache_data.clear()
                st.success("✅ Data cache cleared!")
                logger.info("Data cache cleared by user")
        
        with col2:
            if st.button("🔄 Clear DB Cache", key="clear_db_cache"):
                from .database import DatabaseManager
                DatabaseManager.clear_cache()
                st.success("✅ Database cache cleared!")
                logger.info("Database cache cleared by user")
        
        # Show cache info
        info = CacheManager.get_cache_info()
        st.caption(f"Cached functions: {info['total_functions']}")
