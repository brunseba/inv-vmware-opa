"""Folder Analysis page - Synthesis and metrics by folder."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.dataframe_explorer import dataframe_explorer
from src.models import VirtualMachine
from src.services.label_service import LabelService
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import ThemeManager



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
    colored_header(
        label="📁 Folder Analysis",
        description="Comprehensive folder-level resource and storage analysis",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        label_service = LabelService(session)
        
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
            func.sum(VirtualMachine.provisioned_mib).label('total_provisioned'),
            func.sum(VirtualMachine.in_use_mib).label('total_in_use'),
            func.sum(VirtualMachine.unshared_mib).label('total_unshared'),
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
            'Folder', 'VMs', 'Total_CPUs', 'Total_Memory_MB', 
            'Total_Provisioned_MiB', 'Total_In_Use_MiB', 'Total_Unshared_MiB',
            'Datacenters', 'Clusters', 'Hosts'
        ])
        df_folders['Total_Memory_GB'] = (df_folders['Total_Memory_MB'] / 1024).round(1)
        df_folders['Total_Provisioned_GB'] = (df_folders['Total_Provisioned_MiB'] / 1024).round(1)
        df_folders['Total_In_Use_GB'] = (df_folders['Total_In_Use_MiB'] / 1024).round(1)
        df_folders['Total_Unshared_GB'] = (df_folders['Total_Unshared_MiB'] / 1024).round(1)
        df_folders['Avg_CPUs'] = (df_folders['Total_CPUs'] / df_folders['VMs']).round(1)
        df_folders['Avg_Memory_GB'] = (df_folders['Total_Memory_GB'] / df_folders['VMs']).round(1)
        df_folders['Avg_Provisioned_GB'] = (df_folders['Total_Provisioned_GB'] / df_folders['VMs']).round(1)
        df_folders['Avg_In_Use_GB'] = (df_folders['Total_In_Use_GB'] / df_folders['VMs']).round(1)
        
        # Fill NaN values
        df_folders = df_folders.fillna(0)
        
        # Sort by VM count
        df_folders = df_folders.sort_values('VMs', ascending=False)
        
        # Aggregation options (must be before summary metrics)
        add_vertical_space(1)
        colored_header(
            label="Aggregation Settings",
            description="Configure folder hierarchy and filtering options",
            color_name="green-70"
        )
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
            sort_by = st.selectbox("Sort by", ["VMs", "Total_CPUs", "Total_Memory_GB", "Total_Provisioned_GB", "Total_In_Use_GB", "Folder"])
        
        # Label filters
        col_label1, col_label2 = st.columns(2)
        with col_label1:
            from src.models import Label
            label_keys = [k[0] for k in session.query(Label.key).distinct().all() if k[0]]
            selected_label_key = st.selectbox("Filter by Label Key", ["All"] + label_keys, help="Filter folders by label key")
        
        with col_label2:
            selected_label_value = None
            if selected_label_key != "All":
                label_values = [v[0] for v in session.query(Label.value).filter(
                    Label.key == selected_label_key
                ).distinct().all() if v[0]]
                selected_label_value = st.selectbox("Filter by Label Value", ["All"] + label_values)
        
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
                'Total_Provisioned_MiB': 'sum',
                'Total_In_Use_MiB': 'sum',
                'Total_Unshared_MiB': 'sum',
                'Total_Provisioned_GB': 'sum',
                'Total_In_Use_GB': 'sum',
                'Total_Unshared_GB': 'sum',
                'Datacenters': 'sum',  # This will over-count but gives an idea
                'Clusters': 'sum',
                'Hosts': 'sum'
            }).reset_index()
            df_folders.rename(columns={'Aggregated_Folder': 'Folder'}, inplace=True)
            
            # Recalculate averages
            df_folders['Avg_CPUs'] = (df_folders['Total_CPUs'] / df_folders['VMs']).round(1)
            df_folders['Avg_Memory_GB'] = (df_folders['Total_Memory_GB'] / df_folders['VMs']).round(1)
            df_folders['Avg_Provisioned_GB'] = (df_folders['Total_Provisioned_GB'] / df_folders['VMs']).round(1)
            df_folders['Avg_In_Use_GB'] = (df_folders['Total_In_Use_GB'] / df_folders['VMs']).round(1)
            df_folders = df_folders.sort_values('VMs', ascending=False)
            
            st.info(f"📂 Viewing folders aggregated at **{aggregate_level}** (folders grouped by first {aggregate_level.split()[1]} level(s))")
        
        # Add label coverage info to dataframe (before summary metrics)
        folder_label_counts = {}
        for folder in df_folders['Folder']:
            try:
                labels = label_service.get_folder_labels(folder)
                folder_label_counts[folder] = len(labels)
            except:
                folder_label_counts[folder] = 0
        
        df_folders['Label_Count'] = df_folders['Folder'].map(folder_label_counts)
        df_folders['Label_Count'] = df_folders['Label_Count'].fillna(0).astype(int)
        
        add_vertical_space(2)
        
        # Summary metrics
        colored_header(
            label="Folder Summary",
            description="Key folder metrics and statistics",
            color_name="orange-70"
        )
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Folders", len(df_folders))
        with col2:
            avg_vms_per_folder = df_folders['VMs'].mean()
            st.metric("Avg VMs per Folder", f"{avg_vms_per_folder:.1f}")
        with col3:
            max_vms = df_folders['VMs'].max()
            st.metric("Largest Folder", f"{int(max_vms)} VMs")
        with col4:
            folders_with_labels = len(df_folders[df_folders['Label_Count'] > 0])
            label_coverage_pct = (folders_with_labels / len(df_folders) * 100) if len(df_folders) > 0 else 0
            st.metric("🏷️ Labeled Folders", folders_with_labels, delta=f"{label_coverage_pct:.0f}%")
        with col5:
            folders_with_null = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.folder.is_(None)
            ).scalar() or 0
            st.metric("VMs w/o Folder", folders_with_null)
        
        # Style metric cards
        style_metric_cards(
            background_color="#1f1f1f",
            border_left_color="#ff8c00",
            border_color="#2e2e2e",
            box_shadow="#1f1f1f"
        )
        
        add_vertical_space(2)
        
        # Apply label filter if selected
        if selected_label_key != "All":
            from src.models import FolderLabel
            
            # Get folders with the selected label
            if selected_label_value and selected_label_value != "All":
                # Specific key=value
                label = session.query(Label).filter(
                    Label.key == selected_label_key,
                    Label.value == selected_label_value
                ).first()
                if label:
                    labeled_folders = session.query(FolderLabel.folder_path).filter(
                        FolderLabel.label_id == label.id
                    ).all()
                    labeled_folders = [f[0] for f in labeled_folders]
            else:
                # Any value for this key
                label_ids = session.query(Label.id).filter(
                    Label.key == selected_label_key
                ).all()
                label_ids = [lid[0] for lid in label_ids]
                if label_ids:
                    labeled_folders = session.query(FolderLabel.folder_path).filter(
                        FolderLabel.label_id.in_(label_ids)
                    ).distinct().all()
                    labeled_folders = [f[0] for f in labeled_folders]
                else:
                    labeled_folders = []
            
            # Filter dataframe to only labeled folders
            df_folders = df_folders[df_folders['Folder'].isin(labeled_folders)]
            
            if len(df_folders) > 0:
                st.info(f"🏷️ Showing {len(df_folders)} folders with label: {selected_label_key}" + 
                       (f"={selected_label_value}" if selected_label_value and selected_label_value != "All" else ""))
            else:
                st.warning(f"No folders found with label: {selected_label_key}" + 
                          (f"={selected_label_value}" if selected_label_value and selected_label_value != "All" else ""))
            
            # Recalculate label counts for filtered folders
            folder_label_counts = {}
            for folder in df_folders['Folder']:
                try:
                    labels = label_service.get_folder_labels(folder)
                    folder_label_counts[folder] = len(labels)
                except:
                    folder_label_counts[folder] = 0
            
            df_folders['Label_Count'] = df_folders['Folder'].map(folder_label_counts)
            df_folders['Label_Count'] = df_folders['Label_Count'].fillna(0).astype(int)
        
        # Apply filters
        df_filtered = df_folders[df_folders['VMs'] >= min_vms]
        if sort_by != "VMs":
            df_filtered = df_filtered.sort_values(sort_by, ascending=False)
        
        # Export button
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Export Folder Analysis CSV",
            data=csv_data,
            file_name="folder_analysis.csv",
            mime="text/csv"
        )
        
        # Display detailed table
        colored_header(
            label=f"Folder Details ({len(df_filtered)} folders)",
            description="Detailed folder metrics with sorting and filtering",
            color_name="violet-70"
        )
        
        # Select columns to display
        display_df = df_filtered[[
            'Folder', 'Label_Count', 'VMs', 'Total_CPUs', 'Total_Memory_GB', 
            'Total_Provisioned_GB', 'Total_In_Use_GB', 'Total_Unshared_GB',
            'Avg_CPUs', 'Avg_Memory_GB', 'Avg_Provisioned_GB', 'Avg_In_Use_GB',
            'Datacenters', 'Clusters', 'Hosts'
        ]].copy()
        
        st.dataframe(
            display_df.style.format({
                'Label_Count': '{:,.0f}',
                'VMs': '{:,.0f}',
                'Total_CPUs': '{:,.0f}',
                'Total_Memory_GB': '{:,.1f}',
                'Total_Provisioned_GB': '{:,.1f}',
                'Total_In_Use_GB': '{:,.1f}',
                'Total_Unshared_GB': '{:,.1f}',
                'Avg_CPUs': '{:.1f}',
                'Avg_Memory_GB': '{:.1f}',
                'Avg_Provisioned_GB': '{:.1f}',
                'Avg_In_Use_GB': '{:.1f}',
                'Datacenters': '{:.0f}',
                'Clusters': '{:.0f}',
                'Hosts': '{:.0f}'
            }),
            width="stretch",
            hide_index=True
        )
        
        add_vertical_space(2)
        
        # Visualizations
        colored_header(
            label="Folder Visualizations",
            description="Interactive charts and analytics",
            color_name="blue-70"
        )
        
        viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs(["📊 Distribution", "🎯 Resources", "💾 Storage", "🗂️ Hierarchy"])
        
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
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
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
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
        
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
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
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
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
        
        with viz_tab3:
            st.subheader("Storage Consumption by Folder")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top folders by provisioned storage
                df_top = df_filtered.head(15)
                
                fig = px.bar(
                    df_top,
                    x='Total_Provisioned_GB',
                    y='Folder',
                    orientation='h',
                    title='Top 15 Folders by Provisioned Storage',
                    color='Total_Provisioned_GB',
                    color_continuous_scale='Oranges',
                    text='Total_Provisioned_GB'
                )
                fig.update_traces(texttemplate='%{text:.0f} GB', textposition='outside')
                fig.update_layout(
                    showlegend=False,
                    yaxis={'categoryorder':'total ascending'},
                    height=500
                )
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Storage utilization (In Use vs Provisioned)
                df_top = df_filtered.head(15)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Provisioned',
                    x=df_top['Folder'],
                    y=df_top['Total_Provisioned_GB'],
                    marker_color='lightsalmon'
                ))
                fig.add_trace(go.Bar(
                    name='In Use',
                    x=df_top['Folder'],
                    y=df_top['Total_In_Use_GB'],
                    marker_color='lightseagreen'
                ))
                
                fig.update_layout(
                    title='Top 15 Folders - Storage Utilization',
                    barmode='group',
                    xaxis_tickangle=-45,
                    height=500,
                    yaxis_title='Storage (GB)'
                )
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
            # Storage efficiency metrics
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                # Storage efficiency scatter
                df_top = df_filtered.head(20).copy()
                df_top['Storage_Efficiency_%'] = (df_top['Total_In_Use_GB'] / df_top['Total_Provisioned_GB'] * 100).round(1)
                
                fig = px.scatter(
                    df_top,
                    x='Total_Provisioned_GB',
                    y='Storage_Efficiency_%',
                    size='VMs',
                    hover_data=['Folder', 'Total_In_Use_GB'],
                    title='Storage Efficiency by Folder',
                    color='VMs',
                    color_continuous_scale='Viridis',
                    labels={'Storage_Efficiency_%': 'Efficiency (%)', 'Total_Provisioned_GB': 'Provisioned Storage (GB)'}
                )
                fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="100% Efficiency")
                fig.update_layout(height=450)
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Avg storage per VM
                df_top = df_filtered.head(15)
                
                fig = px.bar(
                    df_top,
                    x='Avg_Provisioned_GB',
                    y='Folder',
                    orientation='h',
                    title='Top 15 Folders - Avg Provisioned Storage per VM',
                    color='Avg_Provisioned_GB',
                    color_continuous_scale='Purples',
                    text='Avg_Provisioned_GB'
                )
                fig.update_traces(texttemplate='%{text:.1f} GB', textposition='outside')
                fig.update_layout(
                    showlegend=False,
                    yaxis={'categoryorder':'total ascending'},
                    height=450
                )
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
        
        with viz_tab4:
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
            fig = ThemeManager.apply_chart_theme(fig)

            st.plotly_chart(fig, width='stretch')
            
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
            fig = ThemeManager.apply_chart_theme(fig)

            st.plotly_chart(fig, width='stretch')
        
        add_vertical_space(2)
        
        # Detailed folder inspection
        colored_header(
            label="🔍 Folder Details",
            description="Drill down into specific folder contents",
            color_name="red-70"
        )
        
        selected_folder = st.selectbox(
            "Select a folder to inspect:",
            df_filtered['Folder'].tolist()
        )
        
        if selected_folder:
            # Show folder labels if any
            try:
                folder_labels = label_service.get_folder_labels(selected_folder)
                if folder_labels:
                    st.write("**🏷️ Folder Labels:**")
                    label_badges = []
                    for lbl in folder_labels:
                        color = lbl.get('color', '#607078') or '#607078'
                        badge = f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 12px;">{lbl["key"]}={lbl["value"]}</span>'
                        label_badges.append(badge)
                    st.markdown(' '.join(label_badges), unsafe_allow_html=True)
                    add_vertical_space(1)
            except Exception:
                pass  # Labels feature may not be available
            
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
            
            # Style metrics
            style_metric_cards(
                background_color="#1f1f1f",
                border_left_color="#dc143c",
                border_color="#2e2e2e",
                box_shadow="#1f1f1f"
            )
            
            add_vertical_space(1)
            
            # Storage metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_prov = sum(vm.provisioned_mib or 0 for vm in folder_vms) / 1024
                st.metric("Provisioned Storage", f"{total_prov:.0f} GB")
            with col2:
                total_used = sum(vm.in_use_mib or 0 for vm in folder_vms) / 1024
                st.metric("In Use Storage", f"{total_used:.0f} GB")
            with col3:
                efficiency = (total_used / total_prov * 100) if total_prov > 0 else 0
                st.metric("Storage Efficiency", f"{efficiency:.1f}%")
            
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
                st.dataframe(df_vms, width="stretch", hide_index=True)
                
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
