"""Folder Analysis page - Synthesis and metrics by folder."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.models import VirtualMachine


def _aggregate_folder_path(folder_path: str, level: int) -> str:
    """Aggregate folder path to specified hierarchy level.
    
    Args:
        folder_path: Full folder path (e.g., 'vm/datacenter1/cluster1/folder1')
        level: Hierarchy level to aggregate to (1 = first segment, 2 = first two segments, etc.)
    
    Returns:
        Aggregated folder path
    
    Examples:
        >>> _aggregate_folder_path('vm/datacenter1/cluster1/folder1', 1)
        'vm'
        >>> _aggregate_folder_path('vm/datacenter1/cluster1/folder1', 2)
        'vm/datacenter1'
    """
    if not folder_path:
        return "(root)"
    
    parts = folder_path.split('/')
    if level >= len(parts):
        return folder_path
    
    aggregated = '/'.join(parts[:level])
    return aggregated if aggregated else "(root)"


def render(db_url: str):
    """Render the folder analysis page."""
    st.markdown('<h1 class="main-header">📁 Folder Analysis</h1>', unsafe_allow_html=True)
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Check if data exists
        total_vms = session.query(func.count(VirtualMachine.id)).scalar()
        
        if total_vms == 0:
            st.warning("⚠️ No data found in database. Please load data first.")
            return
        
        # Get folder statistics
        folder_stats = session.query(
            VirtualMachine.folder,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory'),
            func.count(func.distinct(VirtualMachine.datacenter)).label('datacenters'),
            func.count(func.distinct(VirtualMachine.cluster)).label('clusters'),
            func.count(func.distinct(VirtualMachine.host)).label('hosts')
        ).filter(
            VirtualMachine.folder.isnot(None)
        ).group_by(VirtualMachine.folder).all()
        
        if not folder_stats:
            st.warning("No folder information found in the inventory.")
            return
        
        # Convert to DataFrame
        df_folders = pd.DataFrame(folder_stats, columns=[
            'Folder', 'VMs', 'Total_CPUs', 'Total_Memory_MB', 'Datacenters', 'Clusters', 'Hosts'
        ])
        df_folders['Total_Memory_GB'] = (df_folders['Total_Memory_MB'] / 1024).round(1)
        df_folders['Avg_CPUs'] = (df_folders['Total_CPUs'] / df_folders['VMs']).round(1)
        df_folders['Avg_Memory_GB'] = (df_folders['Total_Memory_GB'] / df_folders['VMs']).round(1)
        
        # Fill NaN values
        df_folders = df_folders.fillna(0)
        
        # Sort by VM count
        df_folders = df_folders.sort_values('VMs', ascending=False)
        
        # Aggregation options (must be before summary metrics)
        st.subheader("Aggregation Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            aggregate_level = st.selectbox(
                "Folder Hierarchy Level",
                ["Full Path", "Level 1", "Level 2", "Level 3", "Level 4", "Level 5"],
                help="Aggregate folders by hierarchy level (/ is separator)"
            )
        
        with col2:
            min_vms = st.number_input("Min VMs", min_value=0, value=0, help="Show folders with at least this many VMs")
        
        with col3:
            sort_by = st.selectbox("Sort by", ["VMs", "Total_CPUs", "Total_Memory_GB", "Folder"])
        
        # Apply folder aggregation
        if aggregate_level != "Full Path":
            level = int(aggregate_level.split()[1])  # Extract level number
            df_folders['Aggregated_Folder'] = df_folders['Folder'].apply(
                lambda x: _aggregate_folder_path(x, level)
            )
            
            # Re-aggregate by new folder paths
            df_folders = df_folders.groupby('Aggregated_Folder').agg({
                'VMs': 'sum',
                'Total_CPUs': 'sum',
                'Total_Memory_MB': 'sum',
                'Total_Memory_GB': 'sum',
                'Datacenters': 'sum',  # This will over-count but gives an idea
                'Clusters': 'sum',
                'Hosts': 'sum'
            }).reset_index()
            df_folders.rename(columns={'Aggregated_Folder': 'Folder'}, inplace=True)
            
            # Recalculate averages
            df_folders['Avg_CPUs'] = (df_folders['Total_CPUs'] / df_folders['VMs']).round(1)
            df_folders['Avg_Memory_GB'] = (df_folders['Total_Memory_GB'] / df_folders['VMs']).round(1)
            df_folders = df_folders.sort_values('VMs', ascending=False)
            
            st.info(f"📂 Viewing folders aggregated at **{aggregate_level}** (folders grouped by first {aggregate_level.split()[1]} level(s))")
        
        st.divider()
        
        # Summary metrics
        st.subheader("Folder Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Folders", len(df_folders))
        with col2:
            avg_vms_per_folder = df_folders['VMs'].mean()
            st.metric("Avg VMs per Folder", f"{avg_vms_per_folder:.1f}")
        with col3:
            max_vms = df_folders['VMs'].max()
            st.metric("Largest Folder", f"{int(max_vms)} VMs")
        with col4:
            folders_with_null = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.folder.is_(None)
            ).scalar() or 0
            st.metric("VMs w/o Folder", folders_with_null)
        
        st.divider()
        
        # Apply filters
        df_filtered = df_folders[df_folders['VMs'] >= min_vms]
        if sort_by != "VMs":
            df_filtered = df_filtered.sort_values(sort_by, ascending=False)
        
        st.divider()
        
        # Export button
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Export Folder Analysis CSV",
            data=csv_data,
            file_name="folder_analysis.csv",
            mime="text/csv"
        )
        
        # Display detailed table
        st.subheader(f"Folder Details ({len(df_filtered)} folders)")
        
        # Select columns to display
        display_df = df_filtered[[
            'Folder', 'VMs', 'Total_CPUs', 'Total_Memory_GB', 
            'Avg_CPUs', 'Avg_Memory_GB', 'Datacenters', 'Clusters', 'Hosts'
        ]].copy()
        
        st.dataframe(
            display_df.style.format({
                'VMs': '{:,.0f}',
                'Total_CPUs': '{:,.0f}',
                'Total_Memory_GB': '{:,.1f}',
                'Avg_CPUs': '{:.1f}',
                'Avg_Memory_GB': '{:.1f}',
                'Datacenters': '{:.0f}',
                'Clusters': '{:.0f}',
                'Hosts': '{:.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        
        # Visualizations
        st.subheader("Folder Visualizations")
        
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📊 Distribution", "🎯 Resources", "🗂️ Hierarchy"])
        
        with viz_tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top folders by VM count
                top_n = min(15, len(df_filtered))
                df_top = df_filtered.head(top_n)
                
                fig = px.bar(
                    df_top,
                    x='VMs',
                    y='Folder',
                    orientation='h',
                    title=f'Top {top_n} Folders by VM Count',
                    color='VMs',
                    color_continuous_scale='Blues',
                    text='VMs'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    showlegend=False,
                    yaxis={'categoryorder':'total ascending'},
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Folder size distribution
                fig = px.histogram(
                    df_filtered,
                    x='VMs',
                    nbins=20,
                    title='Folder Size Distribution',
                    labels={'VMs': 'Number of VMs', 'count': 'Number of Folders'},
                    color_discrete_sequence=['#1f77b4']
                )
                fig.update_layout(
                    showlegend=False,
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with viz_tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # Resource allocation by folder
                df_top = df_filtered.head(10)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='vCPUs',
                    x=df_top['Folder'],
                    y=df_top['Total_CPUs'],
                    marker_color='lightblue'
                ))
                fig.add_trace(go.Bar(
                    name='Memory (GB)',
                    x=df_top['Folder'],
                    y=df_top['Total_Memory_GB'],
                    marker_color='lightcoral'
                ))
                
                fig.update_layout(
                    title='Top 10 Folders - Resource Allocation',
                    barmode='group',
                    xaxis_tickangle=-45,
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Average resources per VM by folder
                df_top = df_filtered.head(10)
                
                fig = px.scatter(
                    df_top,
                    x='Avg_CPUs',
                    y='Avg_Memory_GB',
                    size='VMs',
                    hover_data=['Folder', 'VMs'],
                    title='Top 10 Folders - Avg Resource Profile per VM',
                    color='VMs',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(
                    xaxis_title='Avg vCPUs per VM',
                    yaxis_title='Avg Memory (GB) per VM',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with viz_tab3:
            # Treemap of folder hierarchy
            fig = px.treemap(
                df_filtered.head(20),
                path=['Folder'],
                values='VMs',
                title='Top 20 Folders - VM Distribution (Treemap)',
                color='VMs',
                color_continuous_scale='Blues',
                hover_data=['Total_CPUs', 'Total_Memory_GB']
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Sunburst alternative view
            fig = px.sunburst(
                df_filtered.head(15),
                path=['Folder'],
                values='VMs',
                title='Top 15 Folders - VM Distribution (Sunburst)',
                color='Total_CPUs',
                color_continuous_scale='Oranges'
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Detailed folder inspection
        st.subheader("🔍 Folder Details")
        
        selected_folder = st.selectbox(
            "Select a folder to inspect:",
            df_filtered['Folder'].tolist()
        )
        
        if selected_folder:
            # Get VMs in this folder
            folder_vms = session.query(VirtualMachine).filter(
                VirtualMachine.folder == selected_folder
            ).all()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total VMs", len(folder_vms))
            with col2:
                powered_on = sum(1 for vm in folder_vms if vm.powerstate == "poweredOn")
                st.metric("Powered On", powered_on)
            with col3:
                total_cpus = sum(vm.cpus or 0 for vm in folder_vms)
                st.metric("Total vCPUs", int(total_cpus))
            with col4:
                total_mem = sum(vm.memory or 0 for vm in folder_vms) / 1024
                st.metric("Total Memory", f"{total_mem:.0f} GB")
            
            # VMs in folder
            with st.expander(f"View VMs in '{selected_folder}' ({len(folder_vms)} VMs)"):
                vm_data = []
                for vm in folder_vms:
                    vm_data.append({
                        'VM': vm.vm,
                        'Power': vm.powerstate or 'N/A',
                        'CPUs': vm.cpus or 0,
                        'Memory (GB)': (vm.memory or 0) / 1024,
                        'Datacenter': vm.datacenter or 'N/A',
                        'Cluster': vm.cluster or 'N/A',
                        'Host': vm.host or 'N/A'
                    })
                
                df_vms = pd.DataFrame(vm_data)
                st.dataframe(df_vms, use_container_width=True, hide_index=True)
                
                # Export VMs in folder
                csv_vms = df_vms.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Export VMs in '{selected_folder}'",
                    data=csv_vms,
                    file_name=f"folder_{selected_folder.replace('/', '_')}_vms.csv",
                    mime="text/csv"
                )
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        session.close()
