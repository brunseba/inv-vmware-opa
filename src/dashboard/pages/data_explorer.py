"""Data Explorer page - Interactive self-service data exploration with PyGWalker."""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import VirtualMachine
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space


def render(db_url: str):
    """Render the data explorer page with PyGWalker interactive visualization."""
    
    st.markdown('<h1 class="main-header">🔬 Data Explorer</h1>', unsafe_allow_html=True)
    
    # Introduction
    colored_header(
        label="Interactive Data Exploration",
        description="Create custom visualizations using drag-and-drop",
        color_name="blue-70"
    )
    
    st.markdown("""
    **Welcome to the Data Explorer!** This tool empowers you to create custom visualizations without writing code.
    
    ### How to Use:
    1. **Configure Options**: Set the maximum rows and filters below
    2. **Drag & Drop**: Use the interactive interface to build charts
       - Drag fields to X/Y axes
       - Add colors, sizes, and filters
       - Switch between 20+ chart types
    3. **Explore**: Pan, zoom, and interact with your visualizations
    4. **Export**: Save your insights as images or data
    
    💡 **Tip**: Start with the "Data" tab to see your dataset, then switch to "Explore" to create charts.
    """)
    
    add_vertical_space(2)
    
    # Configuration options
    colored_header(
        label="Load Configuration",
        description="Configure data loading options",
        color_name="violet-70"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        limit = st.selectbox(
            "Maximum Rows",
            options=[1000, 5000, 10000, 25000, 50000],
            index=2,
            help="Limit the number of VMs to load. Larger datasets may take longer."
        )
    
    with col2:
        include_templates = st.checkbox(
            "Include Templates",
            value=False,
            help="Include VM templates in the dataset"
        )
    
    with col3:
        power_filter = st.selectbox(
            "Power State Filter",
            options=["All", "poweredOn", "poweredOff", "suspended"],
            index=0,
            help="Filter VMs by power state"
        )
    
    add_vertical_space(1)
    
    # Load button
    if st.button("🔄 Load Data", type="primary", use_container_width=True):
        load_and_render_explorer(db_url, limit, include_templates, power_filter)
    else:
        st.info("👆 Click 'Load Data' to start exploring your VM inventory")


def load_and_render_explorer(db_url: str, limit: int, include_templates: bool, power_filter: str):
    """Load VM data and render the PyGWalker explorer."""
    
    with st.spinner(f"Loading up to {limit:,} VMs..."):
        try:
            # Create database session
            engine = create_engine(db_url, echo=False)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            
            # Build query
            query = session.query(VirtualMachine)
            
            if not include_templates:
                query = query.filter(VirtualMachine.template == False)
            
            if power_filter != "All":
                query = query.filter(VirtualMachine.powerstate == power_filter)
            
            # Execute query
            vms = query.limit(limit).all()
            
            if not vms:
                st.warning("No VMs found with the selected filters.")
                session.close()
                return
            
            # Prepare DataFrame
            df = pd.DataFrame([{
                'VM_Name': vm.vm or 'Unknown',
                'CPUs': vm.cpus or 0,
                'Memory_GB': round((vm.memory or 0) / 1024, 2),
                'Storage_Provisioned_GB': round((vm.provisioned_mib or 0) / 1024, 2),
                'Storage_InUse_GB': round((vm.in_use_mib or 0) / 1024, 2),
                'Storage_Unshared_GB': round((vm.unshared_mib or 0) / 1024, 2),
                'Datacenter': vm.datacenter or 'Unknown',
                'Cluster': vm.cluster or 'Unknown',
                'Host': vm.host or 'Unknown',
                'Folder': vm.folder or 'Unknown',
                'PowerState': vm.powerstate or 'Unknown',
                'OS': (vm.os_config or 'Unknown')[:50],
                'Is_Template': bool(vm.template),
                'Primary_IP': vm.primary_ip_address or 'N/A',
                'DNS_Name': vm.dns_name or 'N/A'
            } for vm in vms])
            
            session.close()
            
            # Display metrics
            add_vertical_space(1)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 VMs Loaded", f"{len(df):,}")
            
            with col2:
                total_cpus = df['CPUs'].sum()
                st.metric("⚡ Total vCPUs", f"{total_cpus:,}")
            
            with col3:
                total_memory = df['Memory_GB'].sum()
                st.metric("💾 Total RAM", f"{total_memory:,.1f} GB")
            
            with col4:
                total_storage = df['Storage_Provisioned_GB'].sum()
                st.metric("💿 Total Storage", f"{total_storage:,.1f} GB")
            
            add_vertical_space(2)
            
            # Render PyGWalker explorer
            colored_header(
                label="Interactive Explorer",
                description="Drag and drop fields to create visualizations",
                color_name="green-70"
            )
            
            try:
                import pygwalker as pyg
                
                # Render PyGWalker with Streamlit
                # This automatically creates the interactive explorer
                pyg.walk(
                    df,
                    env='Streamlit',
                    spec="./configs/data_explorer.json",
                    use_kernel_calc=True,  # Use DuckDB for better performance
                    dark='media'  # Auto dark mode based on theme
                )
                
            except ImportError:
                st.error("""
                ❌ **PyGWalker not installed**
                
                Please install the required dependencies:
                ```bash
                uv pip install pygwalker streamlit-pygwalker
                ```
                """)
                
                # Fallback to simple dataframe view
                st.subheader("Data Preview (Fallback)")
                st.dataframe(df, width='stretch', height=600)
                
            except Exception as e:
                st.error(f"Error rendering explorer: {e}")
                st.info("Falling back to simple dataframe view")
                st.dataframe(df, width='stretch', height=600)
        
        except Exception as e:
            st.error(f"Error loading data: {e}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())
