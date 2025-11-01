"""VMware vSphere Inventory Dashboard - Main Application."""

import os
import sys
import streamlit as st
from pathlib import Path
from streamlit_extras.add_vertical_space import add_vertical_space

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import version
try:
    from src import __version__
except ImportError:
    __version__ = "0.6.0"  # Fallback

# Import utilities
from utils.state import StateManager, SessionKeys, PageNavigator
from utils.database import DatabaseManager
from utils.cache import get_vm_counts, CacheManager
from utils.errors import ErrorHandler

# Page configuration
st.set_page_config(
    page_title="VMware Inventory Dashboard",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with StateManager
StateManager.init_state()

# Sidebar
with st.sidebar:
    # Display logo using HTML/SVG for better reliability
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <svg width="180" height="60" xmlns="http://www.w3.org/2000/svg">
            <rect width="180" height="60" rx="8" fill="#607078"/>
            <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="20" 
                  font-weight="bold" fill="white" text-anchor="middle" 
                  dominant-baseline="middle">VMware</text>
            <text x="50%" y="75%" font-family="Arial, sans-serif" font-size="10" 
                  fill="#cccccc" text-anchor="middle" 
                  dominant-baseline="middle">Inventory</text>
        </svg>
    </div>
    """, unsafe_allow_html=True)
    
    add_vertical_space(1)
    
    # Database configuration (collapsible)
    with st.expander("⚙️ Configuration", expanded=False):
        db_url = st.text_input(
            "Database URL",
            value=StateManager.get(SessionKeys.DB_URL),
            help="SQLite or other SQLAlchemy connection string",
            label_visibility="collapsed"
        )
        StateManager.set(SessionKeys.DB_URL, db_url)
        
        # Quick connection test using DatabaseManager
        success, error = DatabaseManager.test_connection(db_url)
        if success:
            ErrorHandler.show_success("Connected", icon="✓")
        else:
            ErrorHandler.show_error(Exception(error or "Connection failed"), show_details=False, context="connecting to database")
    
    add_vertical_space(1)
    
    # Get current page from StateManager
    current_page = PageNavigator.get_current_page()
    
    # === PRIMARY NAVIGATION (Always visible) ===
    st.markdown("### 🏠 Main")
    if st.button("📊 Overview", key="btn_Overview", use_container_width=True):
        PageNavigator.navigate_to("Overview")
    
    st.divider()
    
    # === EXPLORE & ANALYZE (Collapsible) ===
    with st.expander("🔍 Explore & Analyze", expanded=True):
        explore_pages = [
            ("🔬 Data Explorer", "Data Explorer"),  # NEW: PyGWalker explorer
            ("🖥️ VM Explorer", "VM Explorer"),
            ("🔎 VM Search", "VM Search"),
            ("📈 Analytics", "Analytics"),
            ("⚖️ Comparison", "Comparison"),
            ("✅ Data Quality", "Data Quality"),
        ]
        for display_name, page_name in explore_pages:
            if st.button(display_name, key=f"btn_{page_name}", use_container_width=True):
                PageNavigator.navigate_to(page_name)
    
    # === INFRASTRUCTURE (Collapsible) ===
    with st.expander("🏗️ Infrastructure", expanded=False):
        infra_pages = [
            ("💻 Resources", "Resources"),
            ("🌐 Infrastructure", "Infrastructure"),
            ("📁 Folder Analysis", "Folder Analysis"),
            ("🏷️ Folder Labelling", "Folder Labelling"),
        ]
        for display_name, page_name in infra_pages:
            if st.button(display_name, key=f"btn_{page_name}", use_container_width=True):
                PageNavigator.navigate_to(page_name)
    
    # === MIGRATION (Collapsible) ===
    with st.expander("🚀 Migration", expanded=False):
        migration_pages = [
            ("🎯 Migration Targets", "Migration Targets"),
            ("⚙️ Strategy Configuration", "Strategy Configuration"),
            ("📋 Migration Planning", "Migration Planning"),
            ("🔄 Migration Scenarios", "Migration Scenarios"),
        ]
        for display_name, page_name in migration_pages:
            if st.button(display_name, key=f"btn_{page_name}", use_container_width=True):
                PageNavigator.navigate_to(page_name)
    
    # === MANAGEMENT (Collapsible) ===
    with st.expander("⚙️ Management", expanded=False):
        mgmt_pages = [
            ("📥 Data Import", "Data Import"),
            ("💾 Database Backup", "Database Backup"),
        ]
        for display_name, page_name in mgmt_pages:
            if st.button(display_name, key=f"btn_{page_name}", use_container_width=True):
                PageNavigator.navigate_to(page_name)
    
    # === EXPORT & HELP (Always visible at bottom) ===
    st.divider()
    
    export_help_pages = [
        ("📄 PDF Report", "PDF Export"),
        ("📚 Documentation", "Help"),
    ]
    for display_name, page_name in export_help_pages:
        if st.button(display_name, key=f"btn_{page_name}", use_container_width=True):
            PageNavigator.navigate_to(page_name)
    
    # Get the active page
    page = current_page
    
    add_vertical_space(1)
    
    # Quick stats (using cached data)
    with st.expander("📈 Quick Stats", expanded=False):
        try:
            db_url = StateManager.get(SessionKeys.DB_URL)
            counts = get_vm_counts(db_url)
            
            st.metric("Total VMs", f"{counts['total']:,}")
            st.metric("Powered On", f"{counts['powered_on']:,}")
        except Exception as e:
            st.caption("Load data to see stats")
    
    # Cache controls
    with st.expander("🔄 Cache Controls", expanded=False):
        CacheManager.show_cache_controls()
    
    add_vertical_space(1)
    
    # Info section
    st.caption("VMware vSphere Inventory")
    st.caption(f"Version {__version__}")

# Main content area
try:
    db_url = StateManager.get(SessionKeys.DB_URL)
    
    if page == "Overview":
        from pages import overview
        overview.render(db_url)
        
    elif page == "Resources":
        from pages import resources
        resources.render(st.session_state.db_url)
        
    elif page == "Infrastructure":
        from pages import infrastructure
        infrastructure.render(st.session_state.db_url)
        
    elif page == "Folder Analysis":
        from pages import folder_analysis
        folder_analysis.render(st.session_state.db_url)
        
    elif page == "Data Explorer":
        from pages import data_explorer
        data_explorer.render(st.session_state.db_url)
        
    elif page == "VM Explorer":
        from pages import vm_explorer
        vm_explorer.render(st.session_state.db_url)
        
    elif page == "VM Search":
        from pages import vm_search
        vm_search.render(st.session_state.db_url)
        
    elif page == "Folder Labelling":
        from pages import folder_labelling
        folder_labelling.render(st.session_state.db_url)
        
    elif page == "Data Import":
        from pages import data_import
        data_import.render(st.session_state.db_url)
        
    elif page == "Database Backup":
        from pages import backup
        backup.render(st.session_state.db_url)
        
    elif page == "Analytics":
        from pages import analytics
        analytics.render(st.session_state.db_url)
        
    elif page == "Comparison":
        from pages import comparison
        comparison.render(st.session_state.db_url)
        
    elif page == "Data Quality":
        from pages import data_quality
        data_quality.render(st.session_state.db_url)
        
    elif page == "Migration Targets":
        from pages import migration_targets
        migration_targets.render(st.session_state.db_url)
        
    elif page == "Strategy Configuration":
        from pages import strategy_config
        strategy_config.render(st.session_state.db_url)
        
    elif page == "Migration Planning":
        from pages import migration_planning
        migration_planning.render(st.session_state.db_url)
        
    elif page == "Migration Scenarios":
        from pages import migration_scenarios
        migration_scenarios.render(st.session_state.db_url)
        
    elif page == "PDF Export":
        from pages import pdf_export
        pdf_export.render(st.session_state.db_url)
        
    elif page == "Help":
        from pages import help
        help.render(st.session_state.db_url)
        
except Exception as e:
    st.error(f"❌ Error loading page: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
