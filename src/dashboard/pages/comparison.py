"""Comparison page - Compare datacenters and clusters side by side."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.models import VirtualMachine


def render(db_url: str):
    """Render the comparison page."""
    st.markdown('<h1 class="main-header">⚖️ Comparison View</h1>', unsafe_allow_html=True)
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Comparison mode
        comparison_mode = st.radio(
            "Compare by:",
            ["Datacenters", "Clusters", "Hosts"],
            horizontal=True
        )
        
        st.divider()
        
        if comparison_mode == "Datacenters":
            _compare_datacenters(session)
        elif comparison_mode == "Clusters":
            _compare_clusters(session)
        else:
            _compare_hosts(session)
            
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
    finally:
        session.close()


def _compare_datacenters(session):
    """Compare datacenters side by side."""
    st.subheader("📍 Datacenter Comparison")
    
    # Get all datacenters
    datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
    
    if not datacenters:
        st.warning("No datacenter data available")
        return
    
    # Selection
    selected_dcs = st.multiselect(
        "Select datacenters to compare (select 2-5):",
        datacenters,
        default=datacenters[:min(3, len(datacenters))]
    )
    
    if len(selected_dcs) < 2:
        st.info("Please select at least 2 datacenters to compare")
        return
    
    # Gather metrics for each datacenter
    dc_data = []
    for dc in selected_dcs:
        dc_vms = session.query(VirtualMachine).filter(VirtualMachine.datacenter == dc)
        total = dc_vms.count()
        powered_on = dc_vms.filter(VirtualMachine.powerstate == "poweredOn").count()
        total_cpus = dc_vms.with_entities(func.sum(VirtualMachine.cpus)).scalar() or 0
        total_mem = dc_vms.with_entities(func.sum(VirtualMachine.memory)).scalar() or 0
        clusters = dc_vms.with_entities(func.count(func.distinct(VirtualMachine.cluster))).scalar()
        hosts = dc_vms.with_entities(func.count(func.distinct(VirtualMachine.host))).scalar()
        
        dc_data.append({
            'Datacenter': dc,
            'Total VMs': total,
            'Powered On': powered_on,
            'Power On %': f"{(powered_on/total*100):.1f}%" if total > 0 else "0%",
            'vCPUs': int(total_cpus),
            'Memory (GB)': int(total_mem / 1024) if total_mem else 0,
            'Clusters': clusters,
            'Hosts': hosts,
            'VMs/Host': f"{total/hosts:.1f}" if hosts > 0 else "0"
        })
    
    df_comparison = pd.DataFrame(dc_data)
    
    # Display comparison table
    st.dataframe(df_comparison, width="stretch", hide_index=True)
    
    st.divider()
    
    # Visual comparisons
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            df_comparison,
            x='Datacenter',
            y='Total VMs',
            title='VM Count Comparison',
            color='Datacenter',
            text='Total VMs'
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            df_comparison,
            x='Datacenter',
            y=['vCPUs', 'Memory (GB)'],
            title='Resource Comparison',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Radar chart for overall comparison
    st.subheader("Overall Comparison (Normalized)")
    
    # Normalize metrics for radar chart
    metrics = ['Total VMs', 'vCPUs', 'Memory (GB)', 'Clusters', 'Hosts']
    normalized_data = []
    
    for metric in metrics:
        max_val = df_comparison[metric].max()
        if max_val > 0:
            for dc in selected_dcs:
                val = df_comparison[df_comparison['Datacenter'] == dc][metric].values[0]
                normalized_data.append({
                    'Datacenter': dc,
                    'Metric': metric,
                    'Normalized Value': (val / max_val) * 100
                })
    
    df_radar = pd.DataFrame(normalized_data)
    
    fig = px.line_polar(
        df_radar,
        r='Normalized Value',
        theta='Metric',
        color='Datacenter',
        line_close=True,
        title='Datacenter Profile Comparison (% of max)'
    )
    fig.update_traces(fill='toself')
    st.plotly_chart(fig, use_container_width=True)


def _compare_clusters(session):
    """Compare clusters side by side."""
    st.subheader("🔷 Cluster Comparison")
    
    # Get all clusters
    clusters = [c[0] for c in session.query(VirtualMachine.cluster).distinct().all() if c[0]]
    
    if not clusters:
        st.warning("No cluster data available")
        return
    
    # Selection
    selected_clusters = st.multiselect(
        "Select clusters to compare (select 2-5):",
        clusters,
        default=clusters[:min(3, len(clusters))]
    )
    
    if len(selected_clusters) < 2:
        st.info("Please select at least 2 clusters to compare")
        return
    
    # Gather metrics
    cluster_data = []
    for cluster in selected_clusters:
        c_vms = session.query(VirtualMachine).filter(VirtualMachine.cluster == cluster)
        total = c_vms.count()
        powered_on = c_vms.filter(VirtualMachine.powerstate == "poweredOn").count()
        total_cpus = c_vms.with_entities(func.sum(VirtualMachine.cpus)).scalar() or 0
        total_mem = c_vms.with_entities(func.sum(VirtualMachine.memory)).scalar() or 0
        hosts = c_vms.with_entities(func.count(func.distinct(VirtualMachine.host))).scalar()
        datacenter = c_vms.with_entities(VirtualMachine.datacenter).first()
        
        cluster_data.append({
            'Cluster': cluster,
            'Datacenter': datacenter[0] if datacenter else 'Unknown',
            'Total VMs': total,
            'Powered On': powered_on,
            'vCPUs': int(total_cpus),
            'Memory (GB)': int(total_mem / 1024) if total_mem else 0,
            'Hosts': hosts,
            'VMs/Host': f"{total/hosts:.1f}" if hosts > 0 else "0",
            'Avg vCPU/VM': f"{total_cpus/total:.1f}" if total > 0 else "0"
        })
    
    df_comparison = pd.DataFrame(cluster_data)
    st.dataframe(df_comparison, width="stretch", hide_index=True)
    
    st.divider()
    
    # Visual comparisons
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            df_comparison,
            x='Cluster',
            y=['Total VMs', 'Powered On'],
            title='VM Distribution',
            barmode='group',
            color_discrete_sequence=['#1f77b4', '#2ca02c']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(
            df_comparison,
            x='vCPUs',
            y='Memory (GB)',
            size='Total VMs',
            color='Cluster',
            hover_data=['Hosts'],
            title='Resource Allocation Profile'
        )
        st.plotly_chart(fig, use_container_width=True)


def _compare_hosts(session):
    """Compare hosts side by side."""
    st.subheader("🖥️ Host Comparison")
    
    # Get all hosts
    hosts = [h[0] for h in session.query(VirtualMachine.host).distinct().all() if h[0]]
    
    if not hosts:
        st.warning("No host data available")
        return
    
    # Selection
    selected_hosts = st.multiselect(
        "Select hosts to compare (select 2-10):",
        hosts,
        default=hosts[:min(5, len(hosts))]
    )
    
    if len(selected_hosts) < 2:
        st.info("Please select at least 2 hosts to compare")
        return
    
    # Gather metrics
    host_data = []
    for host in selected_hosts:
        h_vms = session.query(VirtualMachine).filter(VirtualMachine.host == host)
        total = h_vms.count()
        powered_on = h_vms.filter(VirtualMachine.powerstate == "poweredOn").count()
        total_cpus = h_vms.with_entities(func.sum(VirtualMachine.cpus)).scalar() or 0
        total_mem = h_vms.with_entities(func.sum(VirtualMachine.memory)).scalar() or 0
        cluster_dc = h_vms.with_entities(VirtualMachine.cluster, VirtualMachine.datacenter).first()
        
        host_data.append({
            'Host': host[:30],
            'Cluster': cluster_dc[0] if cluster_dc and cluster_dc[0] else 'Unknown',
            'Datacenter': cluster_dc[1] if cluster_dc and cluster_dc[1] else 'Unknown',
            'Total VMs': total,
            'Powered On': powered_on,
            'vCPUs': int(total_cpus),
            'Memory (GB)': int(total_mem / 1024) if total_mem else 0,
        })
    
    df_comparison = pd.DataFrame(host_data)
    st.dataframe(df_comparison, width="stretch", hide_index=True)
    
    st.divider()
    
    # Visual comparison
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Total VMs',
        x=df_comparison['Host'],
        y=df_comparison['Total VMs'],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Powered On',
        x=df_comparison['Host'],
        y=df_comparison['Powered On'],
        marker_color='green'
    ))
    
    fig.update_layout(
        title='Host VM Distribution',
        barmode='group',
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)
