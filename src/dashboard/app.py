"""VMware vSphere Inventory Dashboard - Main Application."""

import os
import sys
import streamlit as st
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

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

# Initialize session state
if "db_url" not in st.session_state:
    # Use environment variable if set, otherwise default
    st.session_state.db_url = os.environ.get('VMWARE_INV_DB_URL', 'sqlite:///data/vmware_inventory.db')

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/607078/ffffff?text=VMware", width=200)
    st.title("🖥️ VMware Inventory")
    
    # Database configuration (collapsible)
    with st.expander("⚙️ Configuration", expanded=False):
        db_url = st.text_input(
            "Database URL",
            value=st.session_state.db_url,
            help="SQLite or other SQLAlchemy connection string",
            label_visibility="collapsed"
        )
        st.session_state.db_url = db_url
        
        # Quick connection test
        from sqlalchemy import create_engine
        try:
            engine = create_engine(st.session_state.db_url, echo=False)
            with engine.connect() as conn:
                st.success("✓ Connected")
        except Exception as e:
            st.error(f"✗ Connection failed")
            st.caption(str(e)[:50])
    
    st.divider()
    
    # Navigation with better grouping
    st.subheader("Navigation")
    
    # Main dashboards
    st.markdown("**📊 Dashboards**")
    dashboard_pages = ["Overview", "Resources", "Infrastructure", "Folder Analysis"]
    selected_dashboard = st.radio(
        "Dashboards",
        dashboard_pages,
        label_visibility="collapsed",
        key="dashboards"
    )
    
    st.markdown("**🔍 Analysis Tools**")
    analysis_pages = ["VM Explorer", "Analytics", "Comparison", "Data Quality"]
    selected_analysis = st.radio(
        "Analysis",
        analysis_pages,
        label_visibility="collapsed",
        key="analysis"
    )
    
    # Determine which page is selected
    if selected_dashboard:
        page = selected_dashboard
        # Clear other selection
        st.session_state.selected_page_type = "dashboard"
    else:
        page = selected_analysis
        st.session_state.selected_page_type = "analysis"
    
    st.divider()
    
    # Quick stats
    with st.expander("📈 Quick Stats", expanded=False):
        try:
            from sqlalchemy import func
            from sqlalchemy.orm import sessionmaker
            from src.models import VirtualMachine
            
            engine = create_engine(st.session_state.db_url, echo=False)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            
            total = session.query(func.count(VirtualMachine.id)).scalar() or 0
            powered_on = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.powerstate == "poweredOn"
            ).scalar() or 0
            
            st.metric("Total VMs", f"{total:,}")
            st.metric("Powered On", f"{powered_on:,}")
            
            session.close()
        except:
            st.caption("Load data to see stats")
    
    st.divider()
    
    # Info section
    st.caption("VMware vSphere Inventory")
    st.caption("Version 0.1.0")

# Main content area
try:
    if page == "Overview":
        from pages import overview
        overview.render(st.session_state.db_url)
        
    elif page == "Resources":
        from pages import resources
        resources.render(st.session_state.db_url)
        
    elif page == "Infrastructure":
        from pages import infrastructure
        infrastructure.render(st.session_state.db_url)
        
    elif page == "Folder Analysis":
        from pages import folder_analysis
        folder_analysis.render(st.session_state.db_url)
        
    elif page == "VM Explorer":
        from pages import vm_explorer
        vm_explorer.render(st.session_state.db_url)
        
    elif page == "Analytics":
        from pages import analytics
        analytics.render(st.session_state.db_url)
        
    elif page == "Comparison":
        from pages import comparison
        comparison.render(st.session_state.db_url)
        
    elif page == "Data Quality":
        from pages import data_quality
        data_quality.render(st.session_state.db_url)
except Exception as e:
    st.error(f"❌ Error loading page: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
