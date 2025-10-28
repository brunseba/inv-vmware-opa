"""Help page - Comprehensive documentation for the dashboard."""

import streamlit as st
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space


def render(db_url: str):
    """Render the help page."""
    colored_header(
        label="📚 Dashboard Help & Documentation",
        description="Complete guide to using the VMware Inventory Dashboard",
        color_name="blue-70"
    )
    
    # Quick start
    with st.expander("🚀 Quick Start Guide", expanded=True):
        st.markdown("""
        ### Getting Started
        
        1. **Load Your Data**: Use the CLI to load VMware inventory data:
           ```bash
           vmware-inv load your_inventory.xlsx
           ```
        
        2. **Navigate**: Use the sidebar menu to explore different sections
        
        3. **Analyze**: Each page provides specific analytics and visualizations
        
        4. **Export**: Use PDF or Excel export options to save your analysis
        
        ### Connection Configuration
        
        The database connection is configured in the sidebar under **⚙️ Configuration**.
        By default, it uses: `sqlite:///data/vmware_inventory.db`
        """)
    
    add_vertical_space(1)
    
    # Dashboard sections
    colored_header(
        label="📊 Dashboard Pages",
        description="",
        color_name="green-70"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📊 Dashboards
        
        **Overview**
        - High-level infrastructure statistics
        - Power state distribution
        - Datacenter and cluster breakdowns
        - OS configuration analysis
        - Key metrics: Total VMs, vCPUs, Memory
        
        **Resources**
        - Detailed CPU and memory allocation
        - Resource utilization analysis
        - Top consumers identification
        - Resource trending
        
        **Infrastructure**
        - Datacenter hierarchies
        - Cluster configurations
        - Host distribution
        - Network and storage details
        
        **Folder Analysis**
        - VM organization by folders
        - Folder-level statistics
        - Resource distribution by folder
        - Folder hierarchy visualization
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 Analysis Tools
        
        **VM Explorer**
        - Search and filter VMs
        - Detailed VM information
        - Custom queries and filters
        - Export VM lists
        
        **Analytics**
        - Advanced data analysis
        - Custom metrics and KPIs
        - Trend analysis
        - Correlation insights
        
        **Comparison**
        - Compare VMs, clusters, or datacenters
        - Side-by-side analysis
        - Resource comparison
        - Configuration differences
        
        **Data Quality**
        - Data completeness checks
        - Missing information identification
        - Data validation reports
        - Quality improvement suggestions
        """)
    
    add_vertical_space(1)
    
    # Migration planning
    with st.expander("🚀 Migration Planning", expanded=False):
        st.markdown("""
        ### Overview
        
        The Migration Planning tool helps you plan and estimate VM migrations with:
        
        - **Batch Planning**: Organize VMs into migration batches
        - **Timeline Estimation**: Calculate realistic migration timelines
        - **Resource Analysis**: Understand bandwidth and storage requirements
        - **Performance Tracking**: Monitor migration metrics
        
        ### Configuration Options
        
        **Migration Method**
        - *Cold Migration*: VMs are powered off during migration
        - *Hot Migration (vMotion)*: VMs remain running during migration
        
        **Selection Strategy**
        - *Smart (Size-based)*: Automatically balances batches by VM size
        - *Folder-based*: Groups VMs by their folder organization
        
        **Key Parameters**
        - **Network Bandwidth**: Available network throughput (Mbps)
        - **Network Efficiency**: Real-world efficiency factor (typically 70-80%)
        - **Parallel VMs**: Number of simultaneous migrations
        - **Maintenance Window**: Hours per day available for migration
        - **Fixed Time**: Setup/teardown time per VM (hours)
        
        ### Understanding the Results
        
        **Timeline Tab**
        - Gantt chart showing migration schedule
        - Batch progression over time
        - Critical path identification
        
        **Storage Tab**
        - Storage requirements per VM
        - Replication time estimates
        - Top storage consumers
        
        **Performance Tab**
        - Bandwidth utilization over time
        - Batch duration analysis
        - Efficiency metrics
        
        **Folder Tab** (if folder-based)
        - Folder-level migration planning
        - Folder migration times
        - Folder-based resource analysis
        
        ### Export Options
        
        - **Excel Export**: Multi-sheet workbook with charts
        - Contains all tabs: Overview, Timeline, Storage, Performance, Folders
        - Professional formatting with native Excel charts
        """)
    
    add_vertical_space(1)
    
    # Export features
    colored_header(
        label="📄 Export & Reporting",
        description="",
        color_name="orange-70"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### PDF Export
        
        Generate comprehensive PDF reports with:
        - Executive summary
        - All dashboard visualizations
        - Detailed tables and metrics
        - Custom branding and styling
        
        **Best Practices**
        - Generate PDFs for stakeholder presentations
        - Archive reports for historical tracking
        - Include data quality notes
        """)
    
    with col2:
        st.markdown("""
        ### Excel Export
        
        Export detailed data to Excel with:
        - Multiple worksheets for different analyses
        - Native Excel charts
        - Formatted tables with headers
        - Ready for further analysis
        
        **Use Cases**
        - Custom calculations and pivots
        - Integration with other tools
        - Detailed audit trails
        - Sharing with teams
        """)
    
    add_vertical_space(1)
    
    # Tips and tricks
    with st.expander("💡 Tips & Best Practices", expanded=False):
        st.markdown("""
        ### Performance Tips
        
        - **Large Datasets**: Use filters to reduce data volume
        - **Charts**: Hover over charts for detailed information
        - **Exports**: Generate exports during off-peak hours for large datasets
        
        ### Data Quality
        
        - Regularly check the **Data Quality** page
        - Address missing DNS names and IP addresses
        - Validate VM power states
        - Review cluster and datacenter assignments
        
        ### Migration Planning
        
        - Start with conservative estimates
        - Test with a small pilot batch
        - Monitor actual vs. estimated times
        - Adjust parameters based on real results
        - Always include buffer time for issues
        
        ### Navigation
        
        - Use **Quick Stats** in sidebar for at-a-glance info
        - Bookmark frequently used views
        - Use browser refresh if data doesn't update
        - Check connection status in Configuration
        """)
    
    add_vertical_space(1)
    
    # Troubleshooting
    with st.expander("🔧 Troubleshooting", expanded=False):
        st.markdown("""
        ### Common Issues
        
        **No Data Displayed**
        - Verify database connection in Configuration
        - Check if data has been loaded using CLI
        - Confirm correct database path
        
        **Connection Failed**
        - Check database file exists
        - Verify file permissions
        - Ensure SQLite is properly installed
        
        **Charts Not Loading**
        - Refresh the page
        - Check browser console for errors
        - Clear browser cache
        
        **Slow Performance**
        - Reduce number of VMs displayed
        - Use filters to limit data
        - Close other browser tabs
        - Check system resources
        
        ### Getting Help
        
        - Check error messages in the UI
        - Review logs in the terminal
        - Verify input data format
        - Contact your administrator
        """)
    
    add_vertical_space(1)
    
    # Keyboard shortcuts
    colored_header(
        label="⌨️ Keyboard Shortcuts & Interface Tips",
        description="",
        color_name="violet-70"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Interface Elements
        
        **ⓘ Help Icons**
        - Hover over ⓘ icons for contextual help
        - Available throughout the interface
        - Provide quick guidance
        
        **📊 Expanders**
        - Click to expand/collapse sections
        - Organize content efficiently
        - Remember state during session
        
        **🔍 Filters**
        - Use filters to narrow data
        - Combine multiple filters
        - Reset to see all data
        """)
    
    with col2:
        st.markdown("""
        ### Browser Tips
        
        **Zoom Controls**
        - `Cmd/Ctrl +` : Zoom in
        - `Cmd/Ctrl -` : Zoom out
        - `Cmd/Ctrl 0` : Reset zoom
        
        **Navigation**
        - Use sidebar buttons to switch pages
        - Browser back/forward not recommended
        - Refresh page to reload data
        
        **Full Screen**
        - Press `F11` for full screen mode
        - Maximize browser for best experience
        """)
    
    add_vertical_space(2)
    
    # Version and info
    st.markdown("---")
    st.caption("VMware vSphere Inventory Dashboard v0.4.0")
    st.caption("For technical support, contact your system administrator")
