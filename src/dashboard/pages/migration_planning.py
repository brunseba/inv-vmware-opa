"""Migration Planning page - Estimate migration time and plan VM migrations."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime, timedelta
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from src.models import VirtualMachine
from io import BytesIO


def calculate_replication_time(storage_gib: float, bandwidth_mbps: float, efficiency: float = 0.8) -> float:
    """Calculate storage replication time in hours.
    
    Args:
        storage_gib: Storage size in GiB
        bandwidth_mbps: Network bandwidth in Mbps
        efficiency: Network efficiency factor (0-1), default 0.8
        
    Returns:
        Time in hours
    """
    if bandwidth_mbps <= 0:
        return 0
    
    # Convert GiB to Mib (1 GiB = 1024 MiB = 8192 Mib)
    storage_mib = storage_gib * 8192
    
    # Calculate time: (data in Mib) / (bandwidth in Mbps * efficiency)
    # Result in seconds, convert to hours
    effective_bandwidth = bandwidth_mbps * efficiency
    time_seconds = storage_mib / effective_bandwidth
    time_hours = time_seconds / 3600
    
    return time_hours


def render(db_url: str):
    """Render the migration planning page."""
    colored_header(
        label="🚀 Migration Planning",
        description="Estimate migration time and plan VM migrations to new location",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Check if data exists
        total_vms = session.query(func.count(VirtualMachine.id)).scalar()
        
        if total_vms == 0:
            st.warning("⚠️ No data found in database. Please load data first.")
            return
        
        # Sidebar Configuration
        st.sidebar.markdown("### ⚙️ Migration Configuration")
        
        # Fixed time per VM
        st.sidebar.markdown("#### Time per VM")
        
        # Check for quick override
        default_fixed_time = st.session_state.get('quick_fixed_time_override')
        if default_fixed_time is None:
            default_fixed_time = 2
        fixed_time_hours = st.sidebar.selectbox(
            "Fixed Setup Time (hours)",
            options=[1, 2, 4, 8],
            index=[1, 2, 4, 8].index(default_fixed_time) if default_fixed_time in [1, 2, 4, 8] else 1,
            help="Fixed time per VM for setup, configuration, validation, and testing after migration completes",
            key="sidebar_fixed_time"
        )
        # Clear override if sidebar value changed
        if st.session_state.get('quick_fixed_time_override') and fixed_time_hours != st.session_state.get('quick_fixed_time_override'):
            st.session_state.quick_fixed_time_override = None
        
        # Network bandwidth
        st.sidebar.markdown("#### Network Configuration")
        
        # Check for quick bandwidth override
        default_bandwidth_preset = st.session_state.get('quick_bandwidth_override')
        if default_bandwidth_preset is None:
            default_bandwidth_preset = "1 Gbps"
        
        bandwidth_presets = ["100 Mbps", "1 Gbps", "10 Gbps", "25 Gbps", "Custom"]
        bandwidth_preset = st.sidebar.selectbox(
            "Network Bandwidth",
            options=bandwidth_presets,
            index=bandwidth_presets.index(default_bandwidth_preset) if default_bandwidth_preset in bandwidth_presets else 1,
            help="Total available network bandwidth dedicated to migration traffic",
            key="sidebar_bandwidth"
        )
        # Clear override if sidebar value changed
        if st.session_state.get('quick_bandwidth_override') and bandwidth_preset != st.session_state.get('quick_bandwidth_override'):
            st.session_state.quick_bandwidth_override = None
        
        if bandwidth_preset == "Custom":
            default_custom_bandwidth = st.session_state.get('quick_custom_bandwidth_override', 1000)
            bandwidth_mbps = st.sidebar.number_input(
                "Custom Bandwidth (Mbps)",
                min_value=1,
                max_value=100000,
                value=default_custom_bandwidth,
                step=100
            )
        else:
            bandwidth_map = {
                "100 Mbps": 100,
                "1 Gbps": 1000,
                "10 Gbps": 10000,
                "25 Gbps": 25000
            }
            bandwidth_mbps = bandwidth_map[bandwidth_preset]
        
        # Network efficiency
        network_efficiency = st.sidebar.slider(
            "Network Efficiency (%)",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Real-world efficiency factor accounting for network overhead, protocol efficiency, and congestion (typically 70-80%)"
        )
        
        # Parallel migrations
        st.sidebar.markdown("#### Migration Strategy")
        
        # Check for quick override
        default_parallel = st.session_state.get('quick_parallel_override')
        if default_parallel is None:
            default_parallel = 5
        parallel_vms = st.sidebar.number_input(
            "Parallel VM Migrations",
            min_value=1,
            max_value=50,
            value=default_parallel,
            help="Maximum number of VMs that can migrate simultaneously. Limited by network, storage, and compute resources.",
            key="sidebar_parallel"
        )
        # Clear override if sidebar value changed
        if st.session_state.get('quick_parallel_override') and parallel_vms != st.session_state.get('quick_parallel_override'):
            st.session_state.quick_parallel_override = None
        
        # Migration method
        migration_method = st.sidebar.selectbox(
            "Migration Method",
            options=["vMotion (Live)", "Cold Migration", "Replication + Cutover", "Hybrid"],
            index=0,
            help="vMotion: Zero downtime live migration | Cold: VM powered off | Replication: Pre-copy data then cutover | Hybrid: Mix of methods"
        )
        
        # Downtime window
        st.sidebar.markdown("#### Scheduling")
        
        # Check for quick override
        default_window = st.session_state.get('quick_window_override')
        if default_window is None:
            default_window = 8
        maintenance_window_hours = st.sidebar.number_input(
            "Maintenance Window (hours/day)",
            min_value=1,
            max_value=24,
            value=default_window,
            help="Number of hours available per day for migration activities during maintenance windows",
            key="sidebar_window"
        )
        # Clear override if sidebar value changed
        if st.session_state.get('quick_window_override') and maintenance_window_hours != st.session_state.get('quick_window_override'):
            st.session_state.quick_window_override = None
        
        add_vertical_space(1)
        
        # Main content - VM Selection (moved before config summary)
        colored_header(
            label="VM Selection",
            description="Select VMs to include in migration planning",
            color_name="green-70"
        )
        
        # Selection strategy
        selection_strategy = st.radio(
            "Selection Strategy",
            options=["Infrastructure-based", "Folder-based"],
            horizontal=True,
            help="Infrastructure-based: Select by datacenter/cluster/host | Folder-based: Select by VM folder organization"
        )
        
        # Store selection strategy in session state for synthesis table
        st.session_state.current_selection_strategy = selection_strategy
        
        add_vertical_space(1)
        
        # Configuration Summary with Quick Adjustments (moved after selection strategy)
        with st.expander("⚡ Configuration & Quick Adjustments", expanded=True):
            # Current configuration display
            st.markdown("### Current Configuration")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**⚙️ Parameters**")
                st.markdown(f"""
                - Fixed Time: **{fixed_time_hours}h** per VM
                - Parallel VMs: **{parallel_vms}**
                - Window: **{maintenance_window_hours}h/day**
                """)
            
            with col2:
                st.markdown("**🌐 Network**")
                st.markdown(f"""
                - Bandwidth: **{bandwidth_mbps:,} Mbps**
                - Efficiency: **{network_efficiency*100:.0f}%**
                - Effective: **{bandwidth_mbps * network_efficiency:.0f} Mbps**
                """)
            
            with col3:
                st.markdown("**📋 Strategy**")
                st.markdown(f"""
                - Method: **{migration_method}**
                - Selection: **{selection_strategy}**
                """)
            
            # Quick adjustment controls
            st.markdown("---")
            st.markdown("### ⚡ Quick Parameter Adjustments")
            st.caption("💡 Quickly adjust migration parameters without scrolling to the sidebar. Changes apply immediately when you click Apply.")
            st.info("""
            **How to use:**
            - Modify any parameter value below
            - Click the **✔️ Apply** button for that parameter
            - The sidebar and configuration summary will update automatically
            - Use **🔄 Reset All** to revert to sidebar values
            """)
            
            # First row - 4 parameters
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**Fixed Time per VM**")
                st.caption("Setup/validation time per VM")
                quick_fixed_time = st.selectbox(
                    "hours",
                    options=[1, 2, 4, 8],
                    index=[1, 2, 4, 8].index(fixed_time_hours) if fixed_time_hours in [1, 2, 4, 8] else 1,
                    key="quick_fixed_time_select",
                    label_visibility="collapsed",
                    help="Time for post-migration setup and testing"
                )
                if quick_fixed_time != fixed_time_hours:
                    if st.button("✔️ Apply Fixed Time", key="apply_fixed_time", help="Apply this fixed time value"):
                        st.session_state.quick_fixed_time_override = quick_fixed_time
                        st.rerun()
            
            with col2:
                st.markdown("**Parallel Migrations**")
                st.caption("Concurrent VM migrations")
                quick_parallel = st.number_input(
                    "VMs",
                    min_value=1,
                    max_value=50,
                    value=parallel_vms,
                    step=1,
                    key="quick_parallel_input",
                    label_visibility="collapsed",
                    help="Number of VMs migrating at the same time"
                )
                if quick_parallel != parallel_vms:
                    if st.button("✔️ Apply Parallel", key="apply_parallel", help="Apply this parallel VM count"):
                        st.session_state.quick_parallel_override = quick_parallel
                        st.rerun()
            
            with col3:
                st.markdown("**Maintenance Window**")
                st.caption("Available hours per day")
                quick_window = st.number_input(
                    "hours/day",
                    min_value=1,
                    max_value=24,
                    value=maintenance_window_hours,
                    step=1,
                    key="quick_window_input",
                    label_visibility="collapsed",
                    help="Daily time window for migrations"
                )
                if quick_window != maintenance_window_hours:
                    if st.button("✔️ Apply Window", key="apply_window", help="Apply this maintenance window"):
                        st.session_state.quick_window_override = quick_window
                        st.rerun()
            
            with col4:
                st.markdown("**Network Bandwidth**")
                st.caption("Available network speed")
                bandwidth_options = ["100 Mbps", "1 Gbps", "10 Gbps", "25 Gbps"]
                current_bandwidth_str = f"{bandwidth_mbps} Mbps" if bandwidth_mbps not in [100, 1000, 10000, 25000] else bandwidth_preset
                
                # Find current index
                if bandwidth_preset in bandwidth_options:
                    current_idx = bandwidth_options.index(bandwidth_preset)
                else:
                    current_idx = 1  # Default to 1 Gbps
                
                quick_bandwidth = st.selectbox(
                    "bandwidth",
                    options=bandwidth_options,
                    index=current_idx,
                    key="quick_bandwidth_select",
                    label_visibility="collapsed",
                    help="Network bandwidth for migrations"
                )
                if quick_bandwidth != bandwidth_preset:
                    if st.button("✔️ Apply Bandwidth", key="apply_bandwidth", help="Apply this bandwidth setting"):
                        st.session_state.quick_bandwidth_override = quick_bandwidth
                        st.rerun()
            
            # Second row - Reset button
            st.markdown("")
            col1, col2, col3, col4 = st.columns(4)
            with col4:
                if st.button("🔄 Reset All to Sidebar", key="reset_all_overrides"):
                    st.session_state.quick_fixed_time_override = None
                    st.session_state.quick_parallel_override = None
                    st.session_state.quick_window_override = None
                    st.session_state.quick_bandwidth_override = None
                    st.session_state.quick_custom_bandwidth_override = None
                    st.rerun()
            
            # Show impact estimation
            st.markdown("---")
            st.markdown("### 📊 Impact Estimation")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Effective Bandwidth",
                    f"{bandwidth_mbps * network_efficiency:.0f} Mbps",
                    help="Available bandwidth after efficiency factor"
                )
            with col2:
                st.metric(
                    "Per-VM Bandwidth",
                    f"{(bandwidth_mbps * network_efficiency) / parallel_vms:.1f} Mbps",
                    help="Bandwidth allocated per VM when running in parallel"
                )
            with col3:
                st.metric(
                    "Daily Capacity",
                    f"{maintenance_window_hours}h",
                    help="Available migration hours per day"
                )
        
        add_vertical_space(1)
        
        # VM Selection filters section header
        st.markdown("### 🔍 Filter VMs")
        
        if selection_strategy == "Infrastructure-based":
            col1, col2, col3 = st.columns(3)
            
            # Filters
            with col1:
                datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
                selected_dc = st.selectbox(
                    "Datacenter",
                    options=["All"] + datacenters,
                    index=0
                )
            
            with col2:
                clusters = [c[0] for c in session.query(VirtualMachine.cluster).distinct().all() if c[0]]
                selected_cluster = st.selectbox(
                    "Cluster",
                    options=["All"] + clusters,
                    index=0
                )
            
            with col3:
                power_state = st.selectbox(
                    "Power State",
                    options=["All", "poweredOn", "poweredOff"],
                    index=0
                )
            
            # Build query
            query = session.query(VirtualMachine).filter(
                VirtualMachine.in_use_mib.isnot(None)
            )
            
            if selected_dc != "All":
                query = query.filter(VirtualMachine.datacenter == selected_dc)
            if selected_cluster != "All":
                query = query.filter(VirtualMachine.cluster == selected_cluster)
            if power_state != "All":
                query = query.filter(VirtualMachine.powerstate == power_state)
        
        else:  # Folder-based selection
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Get all folders
                all_folders = [f[0] for f in session.query(VirtualMachine.folder).distinct().all() if f[0]]
                
                # Folder hierarchy level
                folder_level = st.selectbox(
                    "Folder Hierarchy Level",
                    options=["Full Path", "Level 1", "Level 2", "Level 3", "Level 4", "Level 5"],
                    help="Select folder aggregation level (Level 1 = root folders)"
                )
                
                # Extract unique folders at selected level
                if folder_level == "Full Path":
                    available_folders = sorted(set(all_folders))
                else:
                    level = int(folder_level.split()[1])
                    available_folders = sorted(set(
                        '/'.join(f.split('/')[:level]) for f in all_folders if f.split('/')[:level]
                    ))
                
                # Folder selection
                selected_folders = st.multiselect(
                    "Select Folders",
                    options=available_folders,
                    default=available_folders[:min(3, len(available_folders))],
                    help="Select one or more folders to migrate"
                )
            
            with col2:
                # Include subfolders option
                include_subfolders = st.checkbox(
                    "Include Subfolders",
                    value=True,
                    help="Include all VMs in subfolders"
                )
                
                power_state = st.selectbox(
                    "Power State",
                    options=["All", "poweredOn", "poweredOff"],
                    index=0
                )
            
            # Build folder-based query
            query = session.query(VirtualMachine).filter(
                VirtualMachine.in_use_mib.isnot(None),
                VirtualMachine.folder.isnot(None)
            )
            
            if selected_folders:
                if include_subfolders:
                    # Match folders that start with any selected folder
                    folder_filters = [VirtualMachine.folder.like(f"{folder}%") for folder in selected_folders]
                    from sqlalchemy import or_
                    query = query.filter(or_(*folder_filters))
                else:
                    # Exact match only
                    query = query.filter(VirtualMachine.folder.in_(selected_folders))
            else:
                # No folders selected, return empty
                query = query.filter(VirtualMachine.id == -1)
            
            if power_state != "All":
                query = query.filter(VirtualMachine.powerstate == power_state)
        
        vms = query.all()
        
        if not vms:
            st.warning("No VMs found matching the selected criteria.")
            return
        
        # Display selection summary
        with st.expander("📋 Selection Summary", expanded=False):
            if selection_strategy == "Infrastructure-based":
                st.markdown(f"""
                **Selection Criteria:**
                - Datacenter: `{selected_dc}`
                - Cluster: `{selected_cluster}`
                - Power State: `{power_state}`
                - Total VMs: **{len(vms):,}**
                """)
            else:
                st.markdown(f"""
                **Selection Criteria:**
                - Folder Level: `{folder_level}`
                - Selected Folders: `{len(selected_folders)}`
                - Include Subfolders: `{include_subfolders}`
                - Power State: `{power_state}`
                - Total VMs: **{len(vms):,}**
                
                **Folders in scope:**
                """)
                for folder in selected_folders[:10]:
                    st.markdown(f"  - `{folder}`")
                if len(selected_folders) > 10:
                    st.markdown(f"  - *... and {len(selected_folders) - 10} more*")
        
        # Calculate migration metrics
        vm_data = []
        for vm in vms:
            storage_gib = (vm.in_use_mib or 0) / 1024
            replication_time = calculate_replication_time(
                storage_gib, 
                bandwidth_mbps / parallel_vms,  # Bandwidth per VM when parallel
                network_efficiency
            )
            total_time = fixed_time_hours + replication_time
            
            vm_data.append({
                'VM': vm.vm,
                'Folder': vm.folder or 'N/A',
                'Datacenter': vm.datacenter or 'Unknown',
                'Cluster': vm.cluster or 'Unknown',
                'PowerState': vm.powerstate or 'Unknown',
                'Storage_GiB': storage_gib,
                'Replication_Hours': replication_time,
                'Fixed_Hours': fixed_time_hours,
                'Total_Hours': total_time,
                'CPUs': vm.cpus or 0,
                'Memory_GB': (vm.memory or 0) / 1024
            })
        
        df = pd.DataFrame(vm_data)
        
        # Summary metrics
        add_vertical_space(1)
        colored_header(
            label="Migration Summary",
            description="Estimated time and resource requirements",
            color_name="orange-70"
        )
        
        total_storage = df['Storage_GiB'].sum()
        total_sequential_time = df['Total_Hours'].sum()
        
        # Calculate parallel migration time (with batching)
        df_sorted = df.sort_values('Total_Hours', ascending=False)
        
        # Simulate parallel migration batches
        migration_batches = []
        current_batch = []
        batch_num = 1
        
        for idx, row in df_sorted.iterrows():
            current_batch.append(row)
            if len(current_batch) >= parallel_vms:
                migration_batches.append({
                    'batch': batch_num,
                    'vms': current_batch.copy(),
                    'duration': max(vm['Total_Hours'] for vm in current_batch)
                })
                current_batch = []
                batch_num += 1
        
        # Add remaining VMs
        if current_batch:
            migration_batches.append({
                'batch': batch_num,
                'vms': current_batch,
                'duration': max(vm['Total_Hours'] for vm in current_batch)
            })
        
        total_parallel_time = sum(batch['duration'] for batch in migration_batches)
        
        # Account for maintenance window
        actual_days = total_parallel_time / maintenance_window_hours
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total VMs", f"{len(vms):,}")
        with col2:
            st.metric("Total Storage", f"{total_storage:,.1f} GiB")
        with col3:
            st.metric("Migration Time", f"{total_parallel_time:.1f}h")
        with col4:
            st.metric("Calendar Days", f"{actual_days:.1f} days")
        
        style_metric_cards(
            background_color="#1f1f1f",
            border_left_color="#ff8c00",
            border_color="#2e2e2e",
            box_shadow="#1f1f1f"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Parallel Batches", f"{len(migration_batches)}")
        with col2:
            time_saved = total_sequential_time - total_parallel_time
            st.metric("Time Saved", f"{time_saved:.1f}h", delta=f"{(time_saved/total_sequential_time*100):.1f}%")
        with col3:
            avg_bandwidth = (total_storage * 8192) / (total_parallel_time * 3600) if total_parallel_time > 0 else 0
            st.metric("Avg Bandwidth Used", f"{avg_bandwidth:.0f} Mbps")
        
        add_vertical_space(2)
        
        # Add batch information to dataframe (needed for visualizations)
        vm_to_batch = {}
        for batch in migration_batches:
            for vm in batch['vms']:
                vm_to_batch[vm['VM']] = batch['batch']
        
        df['Batch'] = df['VM'].map(vm_to_batch)
        df['Total_Days'] = df['Total_Hours'] / maintenance_window_hours
        
        # Visualizations
        colored_header(
            label="Migration Analysis",
            description="Visual breakdown of migration plan",
            color_name="violet-70"
        )
        
        if selection_strategy == "Folder-based":
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📅 Timeline", "💾 Storage", "⚡ Performance", "📁 Folders"])
        else:
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📅 Timeline", "💾 Storage", "⚡ Performance"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Time breakdown
                fig = go.Figure(data=[
                    go.Bar(
                        name='Replication Time',
                        x=['Sequential', 'Parallel'],
                        y=[df['Replication_Hours'].sum(), 
                           sum(batch['duration'] - fixed_time_hours for batch in migration_batches)],
                        marker_color='lightblue'
                    ),
                    go.Bar(
                        name='Fixed Setup Time',
                        x=['Sequential', 'Parallel'],
                        y=[df['Fixed_Hours'].sum(), len(migration_batches) * fixed_time_hours],
                        marker_color='lightcoral'
                    )
                ])
                fig.update_layout(
                    title='Migration Time Comparison',
                    barmode='stack',
                    yaxis_title='Hours',
                    height=400
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # VM distribution by migration batch
                batch_sizes = [len(batch['vms']) for batch in migration_batches]
                batch_labels = [f"Batch {i+1}" for i in range(len(migration_batches))]
                
                fig = px.bar(
                    x=batch_labels,
                    y=batch_sizes,
                    title=f'VMs per Migration Batch (Max {parallel_vms} parallel)',
                    labels={'x': 'Batch', 'y': 'Number of VMs'},
                    color=batch_sizes,
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, width='stretch')
        
        with tab2:
            # Batch Overview Timeline
            st.subheader("Batch Overview Timeline")
            
            # Build batch timeline data
            batch_timeline_data = []
            start_time = datetime.now()
            cumulative_time = 0
            
            for batch in migration_batches:
                batch_start = start_time + timedelta(hours=cumulative_time)
                batch_end = batch_start + timedelta(hours=batch['duration'])
                
                batch_timeline_data.append({
                    'Batch': f"Batch {batch['batch']}",
                    'BatchNumber': batch['batch'],  # Add numeric field for sorting
                    'Start': batch_start,
                    'Finish': batch_end,
                    'VMs': len(batch['vms']),
                    'Storage': f"{sum(vm['Storage_GiB'] for vm in batch['vms']):.1f} GiB",
                    'Duration': f"{batch['duration']:.1f}h"
                })
                
                cumulative_time += batch['duration']
            
            df_batch_timeline = pd.DataFrame(batch_timeline_data)
            
            # Sort by batch number for correct display order
            df_batch_timeline = df_batch_timeline.sort_values('BatchNumber')
            
            if not df_batch_timeline.empty:
                fig = px.timeline(
                    df_batch_timeline,
                    x_start='Start',
                    x_end='Finish',
                    y='Batch',
                    color='VMs',
                    hover_data=['VMs', 'Storage', 'Duration'],
                    title=f'All {len(migration_batches)} Migration Batches',
                    color_continuous_scale='Blues'
                )
                # Use array order for y-axis (already sorted by BatchNumber)
                fig.update_yaxes(categoryorder='array', categoryarray=df_batch_timeline['Batch'].tolist())
                fig.update_layout(height=max(300, len(migration_batches) * 40))
                st.plotly_chart(fig, width='stretch')
            
            add_vertical_space(1)
            
            # Detailed VM Gantt chart
            st.subheader("Detailed VM Migration Schedule")
            
            gantt_data = []
            start_time = datetime.now()
            cumulative_time = 0
            
            for batch in migration_batches:
                batch_start = start_time + timedelta(hours=cumulative_time)
                batch_end = batch_start + timedelta(hours=batch['duration'])
                
                for vm in batch['vms']:
                    gantt_data.append({
                        'Task': vm['VM'][:30],
                        'Start': batch_start,
                        'Finish': batch_end,
                        'Batch': f"Batch {batch['batch']}",
                        'Storage': f"{vm['Storage_GiB']:.1f} GiB"
                    })
                
                cumulative_time += batch['duration']
            
            df_gantt = pd.DataFrame(gantt_data[:50])  # Show first 50 VMs
            
            if not df_gantt.empty:
                fig = px.timeline(
                    df_gantt,
                    x_start='Start',
                    x_end='Finish',
                    y='Task',
                    color='Batch',
                    hover_data=['Storage'],
                    title=f'VM Migration Timeline (First 50 VMs shown)'
                )
                fig.update_yaxes(categoryorder='total ascending')
                fig.update_layout(height=600)
                st.plotly_chart(fig, width='stretch')
                
                if len(gantt_data) > 50:
                    st.info(f"Showing first 50 of {len(gantt_data)} VMs. Download full migration plan for complete timeline.")
        
        with tab3:
            # Storage analysis
            st.subheader("Storage Resource Analysis")
            
            # First row - Storage distribution by batch
            col1, col2 = st.columns(2)
            
            with col1:
                # Storage distribution by batch (pie chart)
                batch_storage_data = []
                for batch in migration_batches:
                    batch_storage = sum(vm['Storage_GiB'] for vm in batch['vms'])
                    batch_storage_data.append({
                        'Batch': f"Batch {batch['batch']}",
                        'Storage_GiB': batch_storage
                    })
                
                df_batch_storage = pd.DataFrame(batch_storage_data)
                
                fig = px.pie(
                    df_batch_storage,
                    values='Storage_GiB',
                    names='Batch',
                    title='Storage Distribution by Batch',
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Storage: %{value:.1f} GiB<br>Percent: %{percent}<extra></extra>'
                )
                fig.update_layout(height=450)
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Storage distribution by batch (bar chart)
                fig = px.bar(
                    df_batch_storage,
                    x='Batch',
                    y='Storage_GiB',
                    title='Storage per Batch',
                    color='Storage_GiB',
                    color_continuous_scale='Teal',
                    labels={'Storage_GiB': 'Storage (GiB)'}
                )
                fig.update_layout(showlegend=False, height=450)
                st.plotly_chart(fig, width='stretch')
            
            add_vertical_space(1)
            
            # Second row - VM storage distribution histogram
            st.markdown("#### VM Storage Distribution")
            st.caption("Distribution of storage sizes across all VMs - helps identify VM sizing patterns")
            
            fig = px.histogram(
                df,
                x='Storage_GiB',
                nbins=30,
                title='VM Count by Storage Size',
                labels={'Storage_GiB': 'Storage (GiB)', 'count': 'Number of VMs'},
                color_discrete_sequence=['#636EFA']
            )
            fig.update_layout(
                xaxis_title='Storage Size (GiB)',
                yaxis_title='Number of VMs',
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig, width='stretch')
            
            # Show storage statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Median VM Size",
                    f"{df['Storage_GiB'].median():.1f} GiB",
                    help="50% of VMs are smaller than this size"
                )
            with col2:
                st.metric(
                    "Average VM Size",
                    f"{df['Storage_GiB'].mean():.1f} GiB",
                    help="Mean storage size across all VMs"
                )
            with col3:
                st.metric(
                    "Smallest VM",
                    f"{df['Storage_GiB'].min():.1f} GiB",
                    help="Smallest VM by storage size"
                )
            with col4:
                st.metric(
                    "Largest VM",
                    f"{df['Storage_GiB'].max():.1f} GiB",
                    help="Largest VM by storage size"
                )
            
            add_vertical_space(1)
            
            # Third row - VM-level analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Top VMs by storage
                df_top = df.nlargest(15, 'Storage_GiB')
                
                fig = px.bar(
                    df_top,
                    x='Storage_GiB',
                    y='VM',
                    orientation='h',
                    title='Top 15 VMs by Storage Size',
                    color='Storage_GiB',
                    color_continuous_scale='Oranges',
                    labels={'Storage_GiB': 'Storage (GiB)'}
                )
                fig.update_layout(showlegend=False, height=500)
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Storage vs Replication Time
                fig = px.scatter(
                    df,
                    x='Storage_GiB',
                    y='Replication_Hours',
                    size='CPUs',
                    color='PowerState',
                    hover_data=['VM', 'Cluster'],
                    title='Storage vs Replication Time',
                    labels={
                        'Storage_GiB': 'Storage (GiB)',
                        'Replication_Hours': 'Replication Time (hours)'
                    }
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, width='stretch')
        
        with tab4:
            # Network utilization
            st.subheader("Network Bandwidth Utilization")
            
            # Simulate bandwidth usage over time
            timeline_hours = []
            bandwidth_usage = []
            
            # Calculate effective bandwidth (max available considering efficiency)
            effective_bandwidth_mbps = bandwidth_mbps * network_efficiency
            
            cumulative = 0
            for batch in migration_batches:
                # Assume bandwidth ramps up at start of batch
                timeline_hours.append(cumulative)
                bandwidth_usage.append(0)
                
                timeline_hours.append(cumulative + 0.1)
                vms_in_batch = len(batch['vms'])
                # Cap at effective bandwidth, considering parallel VMs
                batch_bandwidth = min(effective_bandwidth_mbps, (bandwidth_mbps / parallel_vms) * vms_in_batch)
                bandwidth_usage.append(batch_bandwidth)
                
                timeline_hours.append(cumulative + batch['duration'] - 0.1)
                bandwidth_usage.append(batch_bandwidth)
                
                timeline_hours.append(cumulative + batch['duration'])
                bandwidth_usage.append(0)
                
                cumulative += batch['duration']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timeline_hours,
                y=bandwidth_usage,
                mode='lines',
                fill='tozeroy',
                name='Bandwidth Usage',
                line=dict(color='lightblue', width=2)
            ))
            
            # Add line for effective bandwidth
            fig.add_hline(
                y=effective_bandwidth_mbps,
                line_dash="dash",
                line_color="orange",
                annotation_text="Effective Bandwidth"
            )
            
            # Add line for total bandwidth
            fig.add_hline(
                y=bandwidth_mbps,
                line_dash="dot",
                line_color="red",
                annotation_text="Total Bandwidth"
            )
            
            fig.update_layout(
                title='Network Bandwidth Utilization Over Time',
                xaxis_title='Time (hours)',
                yaxis_title='Bandwidth (Mbps)',
                height=400
            )
            st.plotly_chart(fig, width='stretch')
            
            # Performance metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                peak_bandwidth = max(bandwidth_usage) if bandwidth_usage else 0
                st.metric(
                    "Peak Bandwidth", 
                    f"{peak_bandwidth:.0f} Mbps",
                    help=f"Maximum bandwidth used (capped at effective: {effective_bandwidth_mbps:.0f} Mbps)"
                )
            with col2:
                avg_util = (sum(bandwidth_usage) / len(bandwidth_usage) / effective_bandwidth_mbps * 100) if bandwidth_usage and effective_bandwidth_mbps > 0 else 0
                st.metric(
                    "Avg Utilization", 
                    f"{avg_util:.1f}%",
                    help="Average utilization of effective bandwidth"
                )
            with col3:
                st.metric(
                    "Data Transferred", 
                    f"{total_storage:,.1f} GiB",
                    help="Total storage to be migrated"
                )
        
        # Folder analysis tab (only for folder-based selection)
        if selection_strategy == "Folder-based":
            with tab5:
                st.subheader("Migration by Folder")
                
                # Aggregate by folder
                folder_summary = df.groupby('Folder').agg({
                    'VM': 'count',
                    'Storage_GiB': 'sum',
                    'Total_Hours': 'sum',
                    'Batch': lambda x: x.nunique()
                }).reset_index()
                folder_summary.columns = ['Folder', 'VM_Count', 'Total_Storage', 'Total_Time', 'Batches']
                folder_summary = folder_summary.sort_values('VM_Count', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # VMs per folder
                    fig = px.bar(
                        folder_summary.head(15),
                        x='VM_Count',
                        y='Folder',
                        orientation='h',
                        title='Top 15 Folders - VM Count',
                        color='VM_Count',
                        color_continuous_scale='Blues',
                        text='VM_Count'
                    )
                    fig.update_traces(textposition='outside')
                    fig.update_layout(
                        showlegend=False,
                        yaxis={'categoryorder':'total ascending'},
                        height=500
                    )
                    st.plotly_chart(fig, width='stretch')
                
                with col2:
                    # Migration time per folder
                    fig = px.bar(
                        folder_summary.head(15),
                        x='Total_Time',
                        y='Folder',
                        orientation='h',
                        title='Top 15 Folders - Migration Time (hours)',
                        color='Total_Time',
                        color_continuous_scale='Oranges',
                        text='Total_Time'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}h', textposition='outside')
                    fig.update_layout(
                        showlegend=False,
                        yaxis={'categoryorder':'total ascending'},
                        height=500
                    )
                    st.plotly_chart(fig, width='stretch')
                
                # Folder metrics table
                st.subheader("Folder Migration Metrics")
                st.dataframe(
                    folder_summary.style.format({
                        'VM_Count': '{:,.0f}',
                        'Total_Storage': '{:,.1f}',
                        'Total_Time': '{:.2f}',
                        'Batches': '{:.0f}'
                    }),
                    height=300,
                    width='stretch'
                )
                
                # Export folder summary
                csv_folder = folder_summary.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Export Folder Summary (CSV)",
                    data=csv_folder,
                    file_name=f"migration_folder_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=False
                )
        
        add_vertical_space(2)
        
        # Detailed VM list with export
        colored_header(
            label="Migration Plan Details",
            description="Detailed VM-by-VM migration plan",
            color_name="red-70"
        )
        
        # Display table (include Folder column if folder-based selection)
        if selection_strategy == "Folder-based":
            display_df = df[[
                'Batch', 'VM', 'Folder', 'Datacenter', 'Cluster', 'Storage_GiB',
                'Replication_Hours', 'Fixed_Hours', 'Total_Hours', 'Total_Days'
            ]].copy()
        else:
            display_df = df[[
                'Batch', 'VM', 'Datacenter', 'Cluster', 'Storage_GiB',
                'Replication_Hours', 'Fixed_Hours', 'Total_Hours', 'Total_Days'
            ]].copy()
        
        display_df = display_df.sort_values(['Batch', 'Total_Hours'], ascending=[True, False])
        
        st.dataframe(
            display_df.style.format({
                'Storage_GiB': '{:,.1f}',
                'Replication_Hours': '{:.2f}',
                'Fixed_Hours': '{:.1f}',
                'Total_Hours': '{:.2f}',
                'Total_Days': '{:.2f}',
                'Batch': '{:.0f}'
            }),
            height=400,
            width='stretch'
        )
        
        # Export options
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Export CSV",
                data=csv_data,
                file_name=f"migration_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )
        
        with col2:
            # Generate Excel with multiple sheets
            excel_buffer = BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Sheet 1: Overview Summary
                overview_data = {
                    'Metric': [
                        'Total VMs',
                        'Total Storage (GiB)',
                        'Migration Time (hours)',
                        'Calendar Days',
                        'Parallel Batches',
                        'Time Saved (hours)',
                        'Time Saved (%)',
                        'Avg Bandwidth Used (Mbps)',
                        'Configuration',
                        'Fixed Time per VM (h)',
                        'Parallel VMs',
                        'Maintenance Window (h/day)',
                        'Network Bandwidth (Mbps)',
                        'Network Efficiency (%)',
                        'Effective Bandwidth (Mbps)',
                        'Migration Method',
                        'Selection Strategy'
                    ],
                    'Value': [
                        len(vms),
                        f"{total_storage:.1f}",
                        f"{total_parallel_time:.1f}",
                        f"{actual_days:.1f}",
                        len(migration_batches),
                        f"{time_saved:.1f}",
                        f"{(time_saved/total_sequential_time*100):.1f}",
                        f"{avg_bandwidth:.0f}",
                        '',
                        fixed_time_hours,
                        parallel_vms,
                        maintenance_window_hours,
                        bandwidth_mbps,
                        f"{network_efficiency*100:.0f}",
                        f"{bandwidth_mbps * network_efficiency:.0f}",
                        migration_method,
                        selection_strategy
                    ]
                }
                df_overview = pd.DataFrame(overview_data)
                df_overview.to_excel(writer, sheet_name='Overview', index=False)
                
                # Sheet 2: VM Details - Rename columns for better readability
                vm_details_export = display_df.copy()
                
                # Build column names based on whether Folder is present
                if 'Folder' in display_df.columns:
                    # Folder-based selection (9 columns)
                    vm_details_export.columns = [
                        'Batch #',
                        'VM Name',
                        'Folder',
                        'Datacenter',
                        'Cluster',
                        'Storage (GiB)',
                        'Replication Time (hours)',
                        'Setup Time (hours)',
                        'Total Time (hours)',
                        'Calendar Days'
                    ]
                else:
                    # Infrastructure-based selection (8 columns)
                    vm_details_export.columns = [
                        'Batch #',
                        'VM Name',
                        'Datacenter',
                        'Cluster',
                        'Storage (GiB)',
                        'Replication Time (hours)',
                        'Setup Time (hours)',
                        'Total Time (hours)',
                        'Calendar Days'
                    ]
                
                vm_details_export.to_excel(writer, sheet_name='VM Details', index=False)
                
                # Sheet 3: Batch Summary
                batch_summary = []
                for batch in migration_batches:
                    batch_summary.append({
                        'Batch #': batch['batch'],
                        'VM Count': len(batch['vms']),
                        'Duration (hours)': f"{batch['duration']:.2f}",
                        'Total Storage (GiB)': f"{sum(vm['Storage_GiB'] for vm in batch['vms']):.1f}",
                        'Avg Time per VM (hours)': f"{sum(vm['Total_Hours'] for vm in batch['vms'])/len(batch['vms']):.2f}"
                    })
                df_batches = pd.DataFrame(batch_summary)
                df_batches.to_excel(writer, sheet_name='Batches', index=False)
                
                # Sheet 4: Storage Analysis (Top VMs)
                df_top_storage = df.nlargest(50, 'Storage_GiB')[[
                    'VM', 'Storage_GiB', 'Replication_Hours', 'Datacenter', 'Cluster'
                ]].copy()
                df_top_storage.columns = [
                    'VM Name',
                    'Storage (GiB)',
                    'Replication Time (hours)',
                    'Datacenter',
                    'Cluster'
                ]
                df_top_storage.to_excel(writer, sheet_name='Storage Analysis', index=False)
                
                # Sheet 5: Timeline (first 100 VMs)
                timeline_data = []
                cumulative_time = 0
                for batch in migration_batches:
                    for vm in batch['vms'][:100]:  # Limit to avoid huge files
                        timeline_data.append({
                            'Batch #': batch['batch'],
                            'VM Name': vm['VM'],
                            'Start (hour)': f"{cumulative_time:.2f}",
                            'End (hour)': f"{cumulative_time + batch['duration']:.2f}",
                            'Duration (hours)': f"{batch['duration']:.2f}",
                            'Storage (GiB)': f"{vm['Storage_GiB']:.1f}"
                        })
                    cumulative_time += batch['duration']
                    if len(timeline_data) >= 100:
                        break
                
                df_timeline = pd.DataFrame(timeline_data)
                df_timeline.to_excel(writer, sheet_name='Timeline', index=False)
                
                # Sheet 6: Folder Analysis (if folder-based)
                if selection_strategy == "Folder-based":
                    folder_summary.to_excel(writer, sheet_name='Folder Analysis', index=False)
                
                # Sheet 7: Charts
                df_charts_placeholder = pd.DataFrame({'Info': ['Charts are displayed below']})
                df_charts_placeholder.to_excel(writer, sheet_name='Charts', index=False)
                
                # Format the workbook
                workbook = writer.book
                
                # Add formats
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                cell_format = workbook.add_format({
                    'border': 1
                })
                
                # Apply formatting to each sheet
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    
                    # Set column widths based on content
                    worksheet.set_column('A:A', 25)  # First column wider
                    worksheet.set_column('B:Z', 18)  # Other columns
                    
                    # Get the dataframe for this sheet to format headers
                    if sheet_name == 'Overview':
                        df_to_format = df_overview
                    elif sheet_name == 'VM Details':
                        df_to_format = vm_details_export
                    elif sheet_name == 'Batches':
                        df_to_format = df_batches
                    elif sheet_name == 'Storage Analysis':
                        df_to_format = df_top_storage
                    elif sheet_name == 'Timeline':
                        df_to_format = df_timeline
                    elif sheet_name == 'Folder Analysis' and selection_strategy == "Folder-based":
                        df_to_format = folder_summary
                    else:
                        continue
                    
                    # Write headers with formatting
                    for col_num, value in enumerate(df_to_format.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Freeze the header row
                    worksheet.freeze_panes(1, 0)
                
                # Add charts to the Charts sheet
                chart_sheet = writer.sheets['Charts']
                title_format = workbook.add_format({'bold': True, 'size': 14, 'color': '#4472C4'})
                section_format = workbook.add_format({'bold': True, 'size': 12, 'color': '#70AD47'})
                
                # Title
                chart_sheet.write('A1', 'Migration Analysis - Visual Dashboard', title_format)
                note_format = workbook.add_format({'italic': True, 'size': 10, 'color': '#666666'})
                chart_sheet.write('A2', 'Charts from web interface tabs | Timeline data available in Timeline sheet', note_format)
                
                # === OVERVIEW SECTION (matching Overview tab - 2 charts) ===
                chart_sheet.write('A4', '📊 Overview (2 charts)', section_format)
                
                # Chart 1: VMs per Batch (matching Overview tab)
                chart1 = workbook.add_chart({'type': 'column'})
                num_batches = len(df_batches)
                chart1.add_series({
                    'name': 'VMs per Batch',
                    'categories': f"=Batches!$A$2:$A${num_batches+1}",
                    'values': f"=Batches!$B$2:$B${num_batches+1}",
                    'fill': {'color': '#4472C4'}
                })
                chart1.set_title({'name': f'VMs per Migration Batch (Max {parallel_vms} parallel)'})
                chart1.set_x_axis({'name': 'Batch'})
                chart1.set_y_axis({'name': 'Number of VMs'})
                chart1.set_size({'width': 560, 'height': 350})
                chart_sheet.insert_chart('A6', chart1)
                
                # Chart 2: Migration Time Comparison Sequential vs Parallel
                chart2 = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
                # Create temporary data for this comparison
                comparison_sheet = workbook.add_worksheet('_temp_comparison')
                comparison_sheet.write_row('A1', ['Type', 'Replication', 'Setup'])
                comparison_sheet.write_row('A2', ['Sequential', df['Replication_Hours'].sum(), df['Fixed_Hours'].sum()])
                replication_parallel = sum(batch['duration'] - fixed_time_hours for batch in migration_batches)
                comparison_sheet.write_row('A3', ['Parallel', replication_parallel, len(migration_batches) * fixed_time_hours])
                comparison_sheet.hide()
                
                chart2.add_series({
                    'name': 'Replication Time',
                    'categories': "='_temp_comparison'!$A$2:$A$3",
                    'values': "='_temp_comparison'!$B$2:$B$3",
                    'fill': {'color': '#ADD8E6'}
                })
                chart2.add_series({
                    'name': 'Fixed Setup Time',
                    'categories': "='_temp_comparison'!$A$2:$A$3",
                    'values': "='_temp_comparison'!$C$2:$C$3",
                    'fill': {'color': '#F08080'}
                })
                chart2.set_title({'name': 'Migration Time Comparison'})
                chart2.set_x_axis({'name': ''})
                chart2.set_y_axis({'name': 'Hours'})
                chart2.set_size({'width': 560, 'height': 350})
                chart_sheet.insert_chart('K6', chart2)
                
                # === TIMELINE SECTION ===
                chart_sheet.write('A25', '📅 Timeline', section_format)
                chart_sheet.write('A26', 'Timeline data with Start/End times available in Timeline sheet tab', note_format)
                chart_sheet.write('A27', '(Gantt charts are not supported in native Excel format)', note_format)
                
                # === STORAGE SECTION (matching Storage tab - 2 charts) ===
                chart_sheet.write('A29', '💾 Storage Analysis (2 charts)', section_format)
                
                # Chart 3: Top 15 VMs by Storage (matching Storage tab)
                chart3 = workbook.add_chart({'type': 'bar'})
                top_rows = min(15, len(df_top_storage))
                chart3.add_series({
                    'name': 'Storage (GiB)',
                    'categories': f"='Storage Analysis'!$A$2:$A${top_rows+1}",
                    'values': f"='Storage Analysis'!$B$2:$B${top_rows+1}",
                    'fill': {'color': '#FFA500'},
                    'data_labels': {'value': True, 'num_format': '#,##0.0'}
                })
                chart3.set_title({'name': 'Top 15 VMs by Storage Size'})
                chart3.set_x_axis({'name': 'Storage (GiB)'})
                chart3.set_y_axis({'name': 'VM Name', 'reverse': True})
                chart3.set_size({'width': 560, 'height': 400})
                chart_sheet.insert_chart('A31', chart3)
                
                # Chart 4: Storage Distribution by Batch
                chart4 = workbook.add_chart({'type': 'pie'})
                chart4.add_series({
                    'name': 'Storage per Batch',
                    'categories': f"=Batches!$A$2:$A${num_batches+1}",
                    'values': f"=Batches!$D$2:$D${num_batches+1}",
                    'data_labels': {'percentage': True, 'category': True}
                })
                chart4.set_title({'name': 'Storage Distribution by Batch'})
                chart4.set_size({'width': 560, 'height': 400})
                chart_sheet.insert_chart('K31', chart4)
                
                chart_sheet.write('A52', 'Note: Storage vs Replication Time scatter plot data available in Storage Analysis sheet', note_format)
                
                # === PERFORMANCE SECTION (matching Performance tab - 1 chart) ===
                chart_sheet.write('A54', '⚡ Performance (1 chart)', section_format)
                
                # Chart 5: Duration per Batch
                chart5 = workbook.add_chart({'type': 'column'})
                chart5.add_series({
                    'name': 'Duration (hours)',
                    'categories': f"=Batches!$A$2:$A${num_batches+1}",
                    'values': f"=Batches!$C$2:$C${num_batches+1}",
                    'fill': {'color': '#70AD47'}
                })
                chart5.set_title({'name': 'Migration Duration per Batch'})
                chart5.set_x_axis({'name': 'Batch Number'})
                chart5.set_y_axis({'name': 'Hours'})
                chart5.set_size({'width': 1120, 'height': 350})
                chart5.set_legend({'position': 'none'})
                chart_sheet.insert_chart('A56', chart5)
                
                # Chart 6: Average Time per VM by Batch
                chart6 = workbook.add_chart({'type': 'line'})
                chart6.add_series({
                    'name': 'Avg Time per VM',
                    'categories': f"=Batches!$A$2:$A${num_batches+1}",
                    'values': f"=Batches!$E$2:$E${num_batches+1}",
                    'line': {'color': '#C55A11', 'width': 2.5},
                    'marker': {'type': 'circle', 'size': 7, 'fill': {'color': '#C55A11'}}
                })
                chart6.set_title({'name': 'Average Time per VM by Batch'})
                chart6.set_x_axis({'name': 'Batch Number'})
                chart6.set_y_axis({'name': 'Hours'})
                chart6.set_size({'width': 560, 'height': 350})
                chart_sheet.insert_chart('K56', chart6)
                
                chart_sheet.write('A76', 'Note: Bandwidth utilization line chart represents network usage over time', note_format)
                
                # === FOLDER SECTION (if folder-based - 2 charts) ===
                if selection_strategy == "Folder-based":
                    chart_sheet.write('A78', '📁 Folder Analysis (2 charts)', section_format)
                    
                    # Chart 7: Top Folders by VM Count
                    chart7 = workbook.add_chart({'type': 'bar'})
                    top_folders = min(15, len(folder_summary))
                    chart7.add_series({
                        'name': 'VM Count',
                        'categories': f"='Folder Analysis'!$A$2:$A${top_folders+1}",
                        'values': f"='Folder Analysis'!$B$2:$B${top_folders+1}",
                        'fill': {'color': '#4472C4'}
                    })
                    chart7.set_title({'name': 'Top 15 Folders - VM Count'})
                    chart7.set_x_axis({'name': 'VM Count'})
                    chart7.set_y_axis({'name': 'Folder', 'reverse': True})
                    chart7.set_size({'width': 560, 'height': 400})
                    chart_sheet.insert_chart('A80', chart7)
                    
                    # Chart 8: Top Folders by Migration Time
                    chart8 = workbook.add_chart({'type': 'bar'})
                    chart8.add_series({
                        'name': 'Migration Time (hours)',
                        'categories': f"='Folder Analysis'!$A$2:$A${top_folders+1}",
                        'values': f"='Folder Analysis'!$D$2:$D${top_folders+1}",
                        'fill': {'color': '#FFA500'}
                    })
                    chart8.set_title({'name': 'Top 15 Folders - Migration Time'})
                    chart8.set_x_axis({'name': 'Hours'})
                    chart8.set_y_axis({'name': 'Folder', 'reverse': True})
                    chart8.set_size({'width': 560, 'height': 400})
                    chart_sheet.insert_chart('K80', chart8)
            
            excel_buffer.seek(0)
            
            st.download_button(
                label="📄 Export Excel",
                data=excel_buffer,
                file_name=f"migration_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )
        
        # Migration recommendations
        add_vertical_space(1)
        with st.expander("📋 Migration Recommendations"):
            st.markdown(f"""
            ### Based on your configuration:
            
            **Migration Strategy**: {migration_method}
            - **Total VMs**: {len(vms):,}
            - **Estimated Duration**: {total_parallel_time:.1f} hours ({actual_days:.1f} calendar days)
            - **Network Bandwidth**: {bandwidth_mbps:,} Mbps ({network_efficiency*100:.0f}% efficiency)
            - **Parallel Migrations**: {parallel_vms} VMs at once
            
            ### Recommendations:
            
            1. **Network Preparation**
               - Ensure dedicated network link of at least {bandwidth_mbps} Mbps
               - Test bandwidth and latency before starting
               - Consider network compression for WAN migrations
            
            2. **Migration Phases**
               - Start with non-critical VMs for testing
               - Migrate largest VMs during off-peak hours
               - Plan {len(migration_batches)} migration batches
            
            3. **Risk Mitigation**
               - Have rollback plan for each batch
               - Test application functionality after each batch
               - Monitor network performance during migration
               - Keep source environment available for fallback
            
            4. **Resource Planning**
               - Schedule {actual_days:.0f}-{actual_days+2:.0f} days for complete migration
               - Allocate {maintenance_window_hours} hours/day maintenance window
               - Plan for {parallel_vms} concurrent migration streams
            
            5. **Critical Path Items**
               - Top 10 largest VMs will take longest to replicate
               - Consider pre-staging large VMs before cutover
               - Validate network path supports required bandwidth
            """)
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        session.close()
