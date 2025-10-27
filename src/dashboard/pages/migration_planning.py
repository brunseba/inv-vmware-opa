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
        fixed_time_hours = st.sidebar.selectbox(
            "Fixed Setup Time",
            options=[1, 2, 4, 8],
            index=1,  # Default 2 hours
            help="Time for VM configuration, validation, and testing"
        )
        
        # Network bandwidth
        st.sidebar.markdown("#### Network Configuration")
        bandwidth_preset = st.sidebar.selectbox(
            "Network Bandwidth",
            options=["100 Mbps", "1 Gbps", "10 Gbps", "25 Gbps", "Custom"],
            index=1,  # Default 1 Gbps
            help="Available network bandwidth for migration"
        )
        
        if bandwidth_preset == "Custom":
            bandwidth_mbps = st.sidebar.number_input(
                "Custom Bandwidth (Mbps)",
                min_value=1,
                max_value=100000,
                value=1000,
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
            "Network Efficiency",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Accounts for network overhead, protocol efficiency, etc."
        )
        
        # Parallel migrations
        st.sidebar.markdown("#### Migration Strategy")
        parallel_vms = st.sidebar.number_input(
            "Parallel VM Migrations",
            min_value=1,
            max_value=50,
            value=5,
            help="Number of VMs that can migrate simultaneously"
        )
        
        # Migration method
        migration_method = st.sidebar.selectbox(
            "Migration Method",
            options=["vMotion (Live)", "Cold Migration", "Replication + Cutover", "Hybrid"],
            index=0,
            help="Migration technique affects downtime and duration"
        )
        
        # Downtime window
        st.sidebar.markdown("#### Scheduling")
        maintenance_window_hours = st.sidebar.number_input(
            "Maintenance Window (hours/day)",
            min_value=1,
            max_value=24,
            value=8,
            help="Available hours per day for migration"
        )
        
        add_vertical_space(1)
        
        # Main content - VM Selection
        colored_header(
            label="VM Selection",
            description="Select VMs to include in migration planning",
            color_name="green-70"
        )
        
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
        
        vms = query.all()
        
        if not vms:
            st.warning("No VMs found matching the selected criteria.")
            return
        
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
        
        # Visualizations
        colored_header(
            label="Migration Analysis",
            description="Visual breakdown of migration plan",
            color_name="violet-70"
        )
        
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
                st.plotly_chart(fig, use_container_width=True)
            
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
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Gantt chart for migration timeline
            st.subheader("Migration Schedule")
            
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
                    title=f'Migration Timeline (First 50 VMs shown)'
                )
                fig.update_yaxes(categoryorder='total ascending')
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                if len(gantt_data) > 50:
                    st.info(f"Showing first 50 of {len(gantt_data)} VMs. Download full migration plan for complete timeline.")
        
        with tab3:
            # Storage analysis
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
                st.plotly_chart(fig, use_container_width=True)
            
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
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            # Network utilization
            st.subheader("Network Bandwidth Utilization")
            
            # Simulate bandwidth usage over time
            timeline_hours = []
            bandwidth_usage = []
            
            cumulative = 0
            for batch in migration_batches:
                # Assume bandwidth ramps up at start of batch
                timeline_hours.append(cumulative)
                bandwidth_usage.append(0)
                
                timeline_hours.append(cumulative + 0.1)
                vms_in_batch = len(batch['vms'])
                bandwidth_usage.append(min(bandwidth_mbps, (bandwidth_mbps / parallel_vms) * vms_in_batch))
                
                timeline_hours.append(cumulative + batch['duration'] - 0.1)
                bandwidth_usage.append(min(bandwidth_mbps, (bandwidth_mbps / parallel_vms) * vms_in_batch))
                
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
            
            fig.add_hline(
                y=bandwidth_mbps,
                line_dash="dash",
                line_color="red",
                annotation_text="Max Bandwidth"
            )
            
            fig.update_layout(
                title='Network Bandwidth Utilization Over Time',
                xaxis_title='Time (hours)',
                yaxis_title='Bandwidth (Mbps)',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                peak_bandwidth = max(bandwidth_usage) if bandwidth_usage else 0
                st.metric("Peak Bandwidth", f"{peak_bandwidth:.0f} Mbps")
            with col2:
                avg_util = (sum(bandwidth_usage) / len(bandwidth_usage) / bandwidth_mbps * 100) if bandwidth_usage else 0
                st.metric("Avg Utilization", f"{avg_util:.1f}%")
            with col3:
                st.metric("Data Transferred", f"{total_storage:,.1f} GiB")
        
        add_vertical_space(2)
        
        # Detailed VM list with export
        colored_header(
            label="Migration Plan Details",
            description="Detailed VM-by-VM migration plan",
            color_name="red-70"
        )
        
        # Add batch information to dataframe
        vm_to_batch = {}
        for batch in migration_batches:
            for vm in batch['vms']:
                vm_to_batch[vm['VM']] = batch['batch']
        
        df['Batch'] = df['VM'].map(vm_to_batch)
        df['Total_Days'] = df['Total_Hours'] / maintenance_window_hours
        
        # Display table
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
            use_container_width=True
        )
        
        # Export options
        col1, col2 = st.columns([1, 3])
        
        with col1:
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Export Migration Plan (CSV)",
                data=csv_data,
                file_name=f"migration_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
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
