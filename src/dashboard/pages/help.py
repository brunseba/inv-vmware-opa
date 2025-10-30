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
    
    # Data Model
    colored_header(
        label="🗄️ Data Model & Schema",
        description="Database structure and relationships",
        color_name="violet-70"
    )
    
    tabs = st.tabs(["📊 ER Diagram", "📋 Tables", "🔄 Relationships", "📈 Schema History"])
    
    with tabs[0]:
        st.markdown("### Entity Relationship Diagram")
        st.caption("Visual representation of the database schema (v1.4.0)")
        
        # Mermaid ER diagram with embedded rendering
        mermaid_code = """
        erDiagram
            VIRTUAL_MACHINES ||--o{ VM_LABELS : has
            LABELS ||--o{ VM_LABELS : used_by
            LABELS ||--o{ FOLDER_LABELS : used_by
            
            MIGRATION_TARGETS ||--o{ MIGRATION_SCENARIOS : target
            MIGRATION_SCENARIOS ||--o{ MIGRATION_WAVES : contains
            MIGRATION_STRATEGY_CONFIGS }o--|| MIGRATION_SCENARIOS : defines
            
            VIRTUAL_MACHINES {
                int id PK
                string vm
                string powerstate
                string datacenter
                string cluster
                string folder
                int cpus
                int memory
                float provisioned_mib
                string os_config
                datetime imported_at
            }
            
            LABELS {
                int id PK
                string key
                string value
                string description
                string color
                datetime created_at
            }
            
            VM_LABELS {
                int id PK
                int vm_id FK
                int label_id FK
                bool inherited_from_folder
                string source_folder_path
                datetime assigned_at
            }
            
            FOLDER_LABELS {
                int id PK
                string folder_path
                int label_id FK
                bool apply_to_children
                datetime created_at
            }
            
            MIGRATION_TARGETS {
                int id PK
                string name
                string platform_type
                string region
                int bandwidth_mbps
                float network_efficiency
                float compression_ratio
                float dedup_ratio
                float change_rate_percent
                float network_protocol_overhead
                int delta_sync_count
                float compute_cost_per_vcpu
                float memory_cost_per_gb
                float storage_cost_per_gb
                bool supports_live_migration
            }
            
            MIGRATION_SCENARIOS {
                int id PK
                string name
                int target_id FK
                string strategy
                json vm_selection_criteria
                float estimated_duration_days
                int vm_count
                int total_vcpus
                float total_memory_gb
                float total_storage_gb
                float estimated_migration_cost
                float estimated_runtime_cost_monthly
                string risk_level
                float recommendation_score
                bool recommended
            }
            
            MIGRATION_WAVES {
                int id PK
                int scenario_id FK
                int wave_number
                string wave_name
                json vm_ids
                string start_date
                string end_date
                float duration_hours
                string status
            }
            
            MIGRATION_STRATEGY_CONFIGS {
                int id PK
                string strategy
                float hours_per_vm
                float labor_rate_per_hour
                float compute_multiplier
                float memory_multiplier
                float storage_multiplier
                float network_multiplier
                float replication_efficiency
                float parallel_replication_factor
            }
            
            SCHEMA_VERSIONS {
                int id PK
                string version
                string description
                datetime applied_at
                bool is_current
            }
        """
        
        # Embed Mermaid with dark theme
        st.components.v1.html(
            f"""
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
            <script>
                mermaid.initialize({{ 
                    startOnLoad: true,
                    theme: 'dark',
                    er: {{
                        useMaxWidth: true
                    }}
                }});
            </script>
            <div class="mermaid" style="background: #0e1117; padding: 20px; border-radius: 10px; overflow: auto; max-height: 800px;">
            {mermaid_code}
            </div>
            """,
            height=850,
            scrolling=True
        )
    
    with tabs[1]:
        st.markdown("### Database Tables")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### Core Tables
            
            **virtual_machines**
            - Stores all VM inventory data from RVTools
            - 130+ columns covering all VM attributes
            - Indexed on: vm, datacenter, cluster, folder
            - Primary data source for all analytics
            
            **labels**
            - Master list of available labels (key:value pairs)
            - Used for categorization and tagging
            - Supports color coding
            - Unique constraint on key+value combination
            
            **vm_labels**
            - Junction table: VMs ↔ Labels (many-to-many)
            - Tracks label assignments to VMs
            - Supports inherited labels from folders
            - Records assignment history and source
            
            **folder_labels**
            - Assigns labels to VM folder paths
            - Supports hierarchical inheritance
            - Enables folder-based labeling strategies
            - Links to labels via label_id
            """)
        
        with col2:
            st.markdown("""
            #### Migration Tables
            
            **migration_targets**
            - Defines migration destination platforms
            - Stores cost parameters (compute, memory, storage)
            - **NEW in v1.4.0**: Replication efficiency parameters
              - compression_ratio, dedup_ratio
              - change_rate_percent, delta_sync_count
              - network_protocol_overhead
            - Platform types: AWS, Azure, GCP, VMware Cloud, On-Prem
            
            **migration_scenarios**
            - Migration planning scenarios
            - Links VMs to targets with strategies
            - Calculates costs, duration, and risk
            - Tracks resource totals (vCPUs, RAM, storage)
            - Separate migration vs runtime costs
            
            **migration_waves**
            - Phased migration execution batches
            - Groups VMs for staged migrations
            - Tracks wave status and dependencies
            - Timeline and duration tracking
            
            **migration_strategy_configs**
            - Configuration for 6Rs strategies:
              - Rehost, Replatform, Refactor
              - Repurchase, Retire, Retain
            - **NEW in v1.4.0**: Replication efficiency multipliers
            - Cost multipliers per strategy
            
            **schema_versions**
            - Tracks database schema evolution
            - Version history and migration log
            - Current version: **1.4.0**
            """)
    
    with tabs[2]:
        st.markdown("### Relationships & Constraints")
        
        st.markdown("""
        #### Primary Relationships
        
        **VM Labeling (Many-to-Many)**
        ```
        virtual_machines ←→ vm_labels ←→ labels
        ```
        - One VM can have multiple labels
        - One label can be assigned to multiple VMs
        - Junction table: `vm_labels`
        
        **Folder Labeling (Many-to-Many)**
        ```
        folder_paths ←→ folder_labels ←→ labels
        ```
        - One folder can have multiple labels
        - One label can be assigned to multiple folders
        - Junction table: `folder_labels`
        
        **Migration Planning (One-to-Many)**
        ```
        migration_targets → migration_scenarios → migration_waves
        ```
        - One target can have multiple scenarios
        - One scenario can have multiple waves
        - Cascade delete: removing target removes scenarios
        
        **Strategy Configuration (One-to-Many)**
        ```
        migration_strategy_configs → migration_scenarios
        ```
        - One strategy config defines parameters for multiple scenarios
        - Strategies: 6 predefined (6Rs framework)
        
        #### Key Constraints
        
        - **Unique Constraints**:
          - `labels.key + labels.value` (prevents duplicate labels)
          - `vm_labels.vm_id + vm_labels.label_id` (prevents duplicate assignments)
          - `migration_targets.name` (unique target names)
          - `schema_versions.version` (unique version numbers)
        
        - **Foreign Key Constraints**:
          - `vm_labels.vm_id → virtual_machines.id` (CASCADE DELETE)
          - `vm_labels.label_id → labels.id` (CASCADE DELETE)
          - `folder_labels.label_id → labels.id` (CASCADE DELETE)
          - `migration_scenarios.target_id → migration_targets.id`
          - `migration_waves.scenario_id → migration_scenarios.id`
        
        - **Check Constraints**:
          - Cost values ≥ 0
          - Efficiency ratios: 0.0 to 1.0
          - Bandwidth > 0
        """)
    
    with tabs[3]:
        st.markdown("### Schema Version History")
        
        st.markdown("""
        #### Version 1.4.0 (Current) - 2025-10-30
        **Replication Duration Enhancement**
        
        Added realistic multi-phase replication modeling:
        
        **migration_targets** - Added columns:
        - `compression_ratio` (REAL, default 0.6) - 40% compression savings
        - `dedup_ratio` (REAL, default 0.8) - 20% deduplication savings
        - `change_rate_percent` (REAL, default 0.10) - 10% data change during migration
        - `network_protocol_overhead` (REAL, default 1.2) - 20% TCP/IP overhead
        - `delta_sync_count` (INTEGER, default 2) - Number of delta synchronizations
        
        **migration_strategy_configs** - Added columns:
        - `replication_efficiency` (REAL, default 1.0) - Strategy-specific multiplier
        - `parallel_replication_factor` (REAL, default 1.0) - Parallelism efficiency
        
        **Impact**: 2-5x more realistic migration duration estimates
        
        ---
        
        #### Version 1.3.0 - 2025-10-30
        **VM Resource Metrics**
        
        Added resource tracking to migration_scenarios:
        - `vm_count` - Number of VMs in scenario
        - `total_vcpus` - Total vCPUs across all VMs
        - `total_memory_gb` - Total RAM in GB
        - `total_storage_gb` - Total storage in GB
        
        ---
        
        #### Version 1.2.0 - 2025-10-30
        **Cost Separation**
        
        Separated migration costs into one-time vs ongoing:
        - `estimated_migration_cost` - One-time migration costs (labor, transfer)
        - `estimated_runtime_cost_monthly` - Monthly operational costs
        - `migration_cost_breakdown` - Detailed migration cost JSON
        - `runtime_cost_breakdown` - Detailed runtime cost JSON
        
        ---
        
        #### Version 1.1.0 - 2025-10-30
        **Initial Schema**
        
        Base database structure:
        - virtual_machines (130+ columns)
        - labels, vm_labels, folder_labels
        - migration_targets, migration_scenarios
        - migration_waves, migration_strategy_configs
        - schema_versions tracking
        """)
        
        st.info("""
        💡 **Migration Management**: Use `python migrate_database.py data/vmware_inventory.db --status` 
        to check your current schema version and available migrations.
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
