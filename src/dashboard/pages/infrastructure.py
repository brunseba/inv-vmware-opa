"""Infrastructure page - Datacenter, Cluster, and Host analysis."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.models import VirtualMachine
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import ThemeManager



def render(db_url: str):
    """Render the infrastructure page."""
    st.markdown('<h1 class="main-header">🏗️ Infrastructure View</h1>', unsafe_allow_html=True)
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Hierarchy metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            dc_count = session.query(func.count(func.distinct(VirtualMachine.datacenter))).scalar()
            st.metric("Datacenters", dc_count)
        
        with col2:
            cluster_count = session.query(func.count(func.distinct(VirtualMachine.cluster))).scalar()
            st.metric("Clusters", cluster_count)
        
        with col3:
            host_count = session.query(func.count(func.distinct(VirtualMachine.host))).scalar()
            st.metric("Hosts", host_count)
        
        with col4:
            total_vms = session.query(func.count(VirtualMachine.id)).scalar()
            st.metric("Total VMs", f"{total_vms:,}")
        
        st.divider()
        
        # Datacenter view
        st.subheader("Datacenters Overview")
        
        dc_stats = session.query(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).group_by(VirtualMachine.datacenter).all()
        
        if dc_stats:
            df_dc = pd.DataFrame(dc_stats, columns=['Datacenter', 'VMs', 'CPUs', 'Memory_MB'])
            df_dc['Memory_GB'] = df_dc['Memory_MB'] / 1024
            df_dc = df_dc.drop('Memory_MB', axis=1)
            df_dc = df_dc.fillna(0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    df_dc,
                    x='Datacenter',
                    y='VMs',
                    title='VMs per Datacenter',
                    color='VMs',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False)
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
            with col2:
                fig = px.bar(
                    df_dc,
                    x='Datacenter',
                    y='CPUs',
                    title='vCPUs per Datacenter',
                    color='CPUs',
                    color_continuous_scale='Greens'
                )
                fig.update_layout(showlegend=False)
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
            # Detailed table
            st.dataframe(
                df_dc.style.format({
                    'VMs': '{:,.0f}',
                    'CPUs': '{:,.0f}',
                    'Memory_GB': '{:,.1f}'
                }),
                width="stretch",
                hide_index=True
            )
        
        st.divider()
        
        # Cluster analysis
        st.subheader("Cluster Distribution")
        
        # Select datacenter for cluster view
        datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
        selected_dc = st.selectbox("Select Datacenter", ["All"] + datacenters)
        
        query = session.query(
            VirtualMachine.cluster,
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        )
        
        if selected_dc != "All":
            query = query.filter(VirtualMachine.datacenter == selected_dc)
        
        cluster_stats = query.group_by(VirtualMachine.cluster, VirtualMachine.datacenter).all()
        
        if cluster_stats:
            df_cluster = pd.DataFrame(
                cluster_stats,
                columns=['Cluster', 'Datacenter', 'VMs', 'CPUs', 'Memory_MB']
            )
            df_cluster['Memory_GB'] = df_cluster['Memory_MB'] / 1024
            df_cluster = df_cluster.drop('Memory_MB', axis=1)
            df_cluster = df_cluster.fillna(0)
            df_cluster = df_cluster.sort_values('VMs', ascending=False).head(20)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    df_cluster,
                    x='VMs',
                    y='Cluster',
                    orientation='h',
                    title='Top 20 Clusters by VM Count',
                    color='VMs',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
            
            with col2:
                fig = px.scatter(
                    df_cluster,
                    x='CPUs',
                    y='Memory_GB',
                    size='VMs',
                    hover_data=['Cluster', 'Datacenter'],
                    title='Cluster Resource Distribution',
                    color='VMs',
                    color_continuous_scale='Plasma'
                )
                fig.update_layout(
                    xaxis_title='Total vCPUs',
                    yaxis_title='Total Memory (GB)'
                )
                fig = ThemeManager.apply_chart_theme(fig)

                st.plotly_chart(fig, width='stretch')
        
        st.divider()
        
        # Host analysis
        st.subheader("Host Distribution")
        
        host_stats = session.query(
            VirtualMachine.host,
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('vm_count')
        ).group_by(
            VirtualMachine.host,
            VirtualMachine.cluster
        ).order_by(func.count(VirtualMachine.id).desc()).limit(20).all()
        
        if host_stats:
            df_host = pd.DataFrame(host_stats, columns=['Host', 'Cluster', 'VMs'])
            
            fig = px.bar(
                df_host,
                x='VMs',
                y='Host',
                orientation='h',
                title='Top 20 Hosts by VM Count',
                color='Cluster',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            fig = ThemeManager.apply_chart_theme(fig)

            st.plotly_chart(fig, width='stretch')
            
            # Host distribution stats
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_vms_per_host = df_host['VMs'].mean()
                st.metric("Avg VMs per Host", f"{avg_vms_per_host:.1f}")
            with col2:
                max_vms_per_host = df_host['VMs'].max()
                st.metric("Max VMs per Host", f"{int(max_vms_per_host)}")
            with col3:
                min_vms_per_host = df_host['VMs'].min()
                st.metric("Min VMs per Host", f"{int(min_vms_per_host)}")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
    finally:
        session.close()
