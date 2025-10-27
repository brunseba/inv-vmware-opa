"""Overview page - High-level dashboard statistics."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from src.models import VirtualMachine


def render(db_url: str):
    """Render the overview page."""
    colored_header(
        label="📊 VMware Inventory Overview",
        description="Comprehensive view of your virtual infrastructure",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Check if data exists
        total_vms = session.query(func.count(VirtualMachine.id)).scalar()
        
        if total_vms == 0:
            st.warning("⚠️ No data found in database. Please load data first using: `vmware-inv load <excel_file>`")
            return
        
        # Data quality indicators
        null_dns = session.query(func.count(VirtualMachine.id)).filter(VirtualMachine.dns_name.is_(None)).scalar() or 0
        null_ip = session.query(func.count(VirtualMachine.id)).filter(VirtualMachine.primary_ip_address.is_(None)).scalar() or 0
        if null_dns or null_ip:
            st.info(f"Data quality: {null_dns} VMs missing DNS name, {null_ip} VMs missing IP address")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total VMs",
                value=f"{total_vms:,}",
                delta=None
            )
        
        with col2:
            powered_on = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.powerstate == "poweredOn"
            ).scalar()
            st.metric(
                label="Powered On",
                value=f"{powered_on:,}",
                delta=f"{(powered_on/total_vms*100):.1f}%" if total_vms > 0 else "0%"
            )
        
        with col3:
            total_cpus = session.query(func.sum(VirtualMachine.cpus)).scalar() or 0
            st.metric(
                label="Total vCPUs",
                value=f"{int(total_cpus):,}"
            )
        
        with col4:
            total_memory_mb = session.query(func.sum(VirtualMachine.memory)).scalar() or 0
            total_memory_gb = total_memory_mb / 1024
            st.metric(
                label="Total Memory",
                value=f"{total_memory_gb:,.0f} GB"
            )
        
        # Charts row 1
        colored_header(
            label="Power and Distribution Analysis",
            description="VM power states and datacenter distribution",
            color_name="green-70"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔋 Power State Distribution")
            power_states = session.query(
                VirtualMachine.powerstate,
                func.count(VirtualMachine.id).label('count')
            ).group_by(VirtualMachine.powerstate).all()
            
            if power_states:
                df_power = pd.DataFrame(power_states, columns=['State', 'Count'])
                fig = px.pie(
                    df_power,
                    values='Count',
                    names='State',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 🏢 VMs by Datacenter")
            datacenters = session.query(
                VirtualMachine.datacenter,
                func.count(VirtualMachine.id).label('count')
            ).group_by(VirtualMachine.datacenter).order_by(func.count(VirtualMachine.id).desc()).limit(10).all()
            
            if datacenters:
                df_dc = pd.DataFrame(datacenters, columns=['Datacenter', 'Count'])
                fig = px.bar(
                    df_dc,
                    x='Count',
                    y='Datacenter',
                    orientation='h',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        add_vertical_space(2)
        
        # Charts row 2
        colored_header(
            label="Cluster and Operating System Insights",
            description="Top clusters and OS distribution",
            color_name="orange-70"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📦 Top 10 Clusters by VM Count")
            clusters = session.query(
                VirtualMachine.cluster,
                func.count(VirtualMachine.id).label('count')
            ).group_by(VirtualMachine.cluster).order_by(func.count(VirtualMachine.id).desc()).limit(10).all()
            
            if clusters:
                df_clusters = pd.DataFrame(clusters, columns=['Cluster', 'Count'])
                fig = px.bar(
                    df_clusters,
                    x='Cluster',
                    y='Count',
                    color='Count',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 💻 OS Configuration Distribution")
            os_config = session.query(
                VirtualMachine.os_config,
                func.count(VirtualMachine.id).label('count')
            ).filter(VirtualMachine.os_config.isnot(None)).group_by(
                VirtualMachine.os_config
            ).order_by(func.count(VirtualMachine.id).desc()).limit(10).all()
            
            if os_config:
                df_os = pd.DataFrame(os_config, columns=['OS', 'Count'])
                fig = px.bar(
                    df_os,
                    x='Count',
                    y='OS',
                    orientation='h',
                    color='Count',
                    color_continuous_scale='Oranges'
                )
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        add_vertical_space(2)
        
        # Infrastructure summary
        colored_header(
            label="Infrastructure Summary",
            description="Overall infrastructure resource distribution",
            color_name="violet-70"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dc_count = session.query(func.count(func.distinct(VirtualMachine.datacenter))).scalar()
            st.metric("Datacenters", dc_count)
        
        with col2:
            cluster_count = session.query(func.count(func.distinct(VirtualMachine.cluster))).scalar()
            st.metric("Clusters", cluster_count)
        
        with col3:
            host_count = session.query(func.count(func.distinct(VirtualMachine.host))).scalar()
            st.metric("Hosts", host_count)
        
        # Apply styling to infrastructure metrics
        style_metric_cards(
            background_color="#1f1f1f",
            border_left_color="#9370db",
            border_color="#2e2e2e",
            box_shadow="#1f1f1f"
        )
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
    finally:
        session.close()
