"""Advanced Data Explorer - Custom SQL queries with PyGWalker visualization."""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space


def render(db_url: str):
    """Render advanced explorer with custom SQL support."""
    
    st.markdown('<h1 class="main-header">🔬 Advanced Data Explorer</h1>', unsafe_allow_html=True)
    
    colored_header(
        label="Custom SQL Query Explorer",
        description="Execute custom SQL queries and visualize results with PyGWalker",
        color_name="blue-70"
    )
    
    st.markdown("""
    **Advanced Features:**
    - ✍️ Write custom SQL queries
    - 📊 Visualize query results interactively
    - 💾 Save query results for analysis
    - 🔗 Share visualizations via URL
    
    ⚠️ **Note**: Only SELECT queries are allowed for security.
    """)
    
    add_vertical_space(2)
    
    # SQL Query Interface
    colored_header(
        label="SQL Query",
        description="Write your custom query below",
        color_name="violet-70"
    )
    
    # Pre-defined query templates
    query_templates = {
        "All VMs": "SELECT * FROM virtual_machines LIMIT 1000",
        "VM Resources": """SELECT 
            vm, 
            cpus, 
            memory / 1024 as memory_gb,
            provisioned_mib / 1024 as storage_gb,
            datacenter, 
            cluster,
            powerstate
        FROM virtual_machines 
        WHERE template = 0
        LIMIT 1000""",
        "VMs by Datacenter": """SELECT 
            datacenter,
            COUNT(*) as vm_count,
            SUM(cpus) as total_cpus,
            SUM(memory) / 1024 as total_memory_gb
        FROM virtual_machines
        WHERE template = 0
        GROUP BY datacenter""",
        "VMs by OS": """SELECT 
            os_config,
            COUNT(*) as count,
            AVG(cpus) as avg_cpus,
            AVG(memory / 1024) as avg_memory_gb
        FROM virtual_machines
        WHERE os_config IS NOT NULL AND template = 0
        GROUP BY os_config
        ORDER BY count DESC
        LIMIT 20""",
        "Storage Analysis": """SELECT 
            datacenter,
            cluster,
            COUNT(*) as vm_count,
            SUM(provisioned_mib / 1024) as provisioned_gb,
            SUM(in_use_mib / 1024) as in_use_gb,
            ROUND((SUM(in_use_mib) * 100.0 / SUM(provisioned_mib)), 2) as efficiency_pct
        FROM virtual_machines
        WHERE provisioned_mib > 0 AND template = 0
        GROUP BY datacenter, cluster
        ORDER BY provisioned_gb DESC"""
    }
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        template = st.selectbox(
            "Query Templates",
            options=["Custom"] + list(query_templates.keys()),
            help="Select a pre-defined query template or write custom SQL"
        )
    
    with col2:
        if template != "Custom":
            query = st.text_area(
                "SQL Query",
                value=query_templates[template],
                height=200,
                help="Modify the template or write your own SELECT query"
            )
        else:
            query = st.text_area(
                "SQL Query",
                value="SELECT * FROM virtual_machines LIMIT 100",
                height=200,
                help="Write your custom SELECT query"
            )
    
    add_vertical_space(1)
    
    # Security check
    if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE')):
        st.error("❌ Only SELECT queries are allowed for security reasons.")
        return
    
    # Execute query button
    if st.button("▶️ Execute Query", type="primary", use_container_width=True):
        execute_and_visualize(db_url, query)
    
    add_vertical_space(2)
    
    # Help section
    with st.expander("📚 Available Tables and Columns"):
        st.markdown("""
        ### Main Tables
        
        **virtual_machines**
        - Basic: `vm`, `powerstate`, `template`, `datacenter`, `cluster`, `host`
        - Resources: `cpus`, `memory` (MB), `nics`, `disks`
        - Storage: `provisioned_mib`, `in_use_mib`, `unshared_mib`
        - Network: `primary_ip_address`, `dns_name`, `network_1` through `network_8`
        - Organization: `folder`, `resource_pool`, `vapp`
        - OS: `os_config`, `os_vmware_tools`
        - Dates: `creation_date`, `poweron`, `suspend_time`, `nb_last_backup`
        - Custom: `env`, `code_ccx`, `vm_nbu`, `vm_orchid`
        
        **labels**
        - `id`, `key`, `value`, `description`, `color`
        
        **vm_labels**
        - `vm_id`, `label_id`, `inherited_from_folder`
        
        **folder_labels**
        - `folder_path`, `label_id`, `inherit_to_vms`, `inherit_to_subfolders`
        
        ### Query Tips
        - Always use `LIMIT` to avoid loading too much data
        - Convert memory from MB to GB: `memory / 1024`
        - Convert storage from MiB to GiB: `provisioned_mib / 1024`
        - Filter out templates: `WHERE template = 0` or `WHERE template = False`
        - Join tables using proper foreign keys
        """)


def execute_and_visualize(db_url: str, query: str):
    """Execute SQL query and visualize results with PyGWalker."""
    
    with st.spinner("Executing query..."):
        try:
            engine = create_engine(db_url, echo=False)
            
            # Execute query
            df = pd.read_sql(text(query), engine)
            
            if df.empty:
                st.warning("Query returned no results.")
                return
            
            # Display results summary
            colored_header(
                label="Query Results",
                description=f"{len(df):,} rows × {len(df.columns)} columns",
                color_name="green-70"
            )
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Rows", f"{len(df):,}")
            with col2:
                st.metric("📋 Columns", len(df.columns))
            with col3:
                numeric_cols = df.select_dtypes(include=['number']).columns
                st.metric("🔢 Numeric", len(numeric_cols))
            with col4:
                text_cols = df.select_dtypes(include=['object']).columns
                st.metric("📝 Text", len(text_cols))
            
            add_vertical_space(1)
            
            # Show data preview
            with st.expander("📄 Data Preview (first 10 rows)"):
                st.dataframe(df.head(10), width='stretch')
            
            add_vertical_space(1)
            
            # Render PyGWalker explorer
            colored_header(
                label="Interactive Visualization",
                description="Drag and drop fields to create charts",
                color_name="blue-70"
            )
            
            try:
                import pygwalker as pyg
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from utils.theme import ThemeManager
                
                # Get current theme
                theme = ThemeManager.get_pygwalker_theme()
                
                pyg.walk(
                    df,
                    env='Streamlit',
                    spec="./configs/advanced_explorer.json",
                    use_kernel_calc=True,
                    dark=theme
                )
            except ImportError:
                st.error("PyGWalker not installed. Install with: `uv pip install pygwalker`")
                st.dataframe(df, width='stretch', height=600)
            except Exception as e:
                st.error(f"Error rendering explorer: {e}")
                st.dataframe(df, width='stretch', height=600)
                
        except Exception as e:
            st.error(f"❌ Query execution failed: {str(e)}")
            with st.expander("🔍 Error Details"):
                import traceback
                st.code(traceback.format_exc())
