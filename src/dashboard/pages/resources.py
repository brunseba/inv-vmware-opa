"""Resources page - CPU and Memory analysis."""

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
    """Render the resources page."""
    colored_header(
        label="💾 Resource Analysis",
        description="CPU, Memory, and Storage consumption metrics",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
            selected_dc = st.selectbox("Filter by Datacenter", ["All"] + datacenters)
        
        with col2:
            clusters = [c[0] for c in session.query(VirtualMachine.cluster).distinct().all() if c[0]]
            selected_cluster = st.selectbox("Filter by Cluster", ["All"] + clusters)
        
        with col3:
            power_states = [p[0] for p in session.query(VirtualMachine.powerstate).distinct().all() if p[0]]
            selected_power = st.selectbox("Power State", ["All"] + power_states)
        
        # Build query with filters
        query = session.query(VirtualMachine)
        if selected_dc != "All":
            query = query.filter(VirtualMachine.datacenter == selected_dc)
        if selected_cluster != "All":
            query = query.filter(VirtualMachine.cluster == selected_cluster)
        if selected_power != "All":
            query = query.filter(VirtualMachine.powerstate == selected_power)
        
        vms = query.all()
        
        if not vms:
            st.warning("No VMs found with selected filters")
            return
        
        add_vertical_space(2)
        
        # Summary metrics
        colored_header(
            label="Resource Summary",
            description=f"Analyzing {len(vms):,} virtual machines",
            color_name="green-70"
        )
        col1, col2, col3, col4 = st.columns(4)
        
        total_cpus = sum(vm.cpus or 0 for vm in vms)
        total_memory_gb = sum(vm.memory or 0 for vm in vms) / 1024
        avg_cpus = total_cpus / len(vms) if vms else 0
        avg_memory_gb = total_memory_gb / len(vms) if vms else 0
        
        with col1:
            st.metric("Total vCPUs", f"{int(total_cpus):,}")
        with col2:
            st.metric("Total Memory", f"{total_memory_gb:,.0f} GB")
        with col3:
            st.metric("Avg vCPUs per VM", f"{avg_cpus:.1f}")
        with col4:
            st.metric("Avg Memory per VM", f"{avg_memory_gb:.1f} GB")
        
        # Style metric cards
        style_metric_cards(
            background_color="#1f1f1f",
            border_left_color="#2e8b57",
            border_color="#2e2e2e",
            box_shadow="#1f1f1f"
        )
        
        add_vertical_space(2)
        
        # CPU Distribution
        colored_header(
            label="Resource Distribution",
            description="CPU and memory allocation across VMs",
            color_name="orange-70"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📦 vCPU Distribution")
            cpu_data = [vm.cpus for vm in vms if vm.cpus]
            if cpu_data:
                df_cpu = pd.DataFrame({'vCPUs': cpu_data})
                fig = px.histogram(
                    df_cpu,
                    x='vCPUs',
                    nbins=20,
                    color_discrete_sequence=['#1f77b4']
                )
                fig.update_layout(
                    xaxis_title="Number of vCPUs",
                    yaxis_title="VM Count",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 💾 Memory Distribution (GB)")
            memory_data = [vm.memory / 1024 for vm in vms if vm.memory]
            if memory_data:
                df_mem = pd.DataFrame({'Memory_GB': memory_data})
                fig = px.histogram(
                    df_mem,
                    x='Memory_GB',
                    nbins=20,
                    color_discrete_sequence=['#ff7f0e']
                )
                fig.update_layout(
                    xaxis_title="Memory (GB)",
                    yaxis_title="VM Count",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        add_vertical_space(2)
        
        # Top resource consumers
        colored_header(
            label="Top Resource Consumers",
            description="Virtual machines with highest resource allocation",
            color_name="red-70"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔺 Top 10 VMs by vCPU")
            top_cpu_vms = sorted(vms, key=lambda x: x.cpus or 0, reverse=True)[:10]
            df_top_cpu = pd.DataFrame([
                {'VM': vm.vm[:30], 'vCPUs': vm.cpus} 
                for vm in top_cpu_vms if vm.cpus
            ])
            if not df_top_cpu.empty:
                fig = px.bar(
                    df_top_cpu,
                    x='vCPUs',
                    y='VM',
                    orientation='h',
                    color='vCPUs',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 🔺 Top 10 VMs by Memory")
            top_mem_vms = sorted(vms, key=lambda x: x.memory or 0, reverse=True)[:10]
            df_top_mem = pd.DataFrame([
                {'VM': vm.vm[:30], 'Memory_GB': vm.memory / 1024} 
                for vm in top_mem_vms if vm.memory
            ])
            if not df_top_mem.empty:
                fig = px.bar(
                    df_top_mem,
                    x='Memory_GB',
                    y='VM',
                    orientation='h',
                    color='Memory_GB',
                    color_continuous_scale='Reds'
                )
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        add_vertical_space(2)
        
        # Storage Analysis
        colored_header(
            label="Storage Analysis",
            description="Storage provisioning and utilization metrics",
            color_name="violet-70"
        )
        col1, col2, col3 = st.columns(3)
        
        total_provisioned = sum(vm.provisioned_mib or 0 for vm in vms) / 1024  # Convert to GB
        total_in_use = sum(vm.in_use_mib or 0 for vm in vms) / 1024
        total_unshared = sum(vm.unshared_mib or 0 for vm in vms) / 1024
        
        with col1:
            st.metric("Provisioned Storage", f"{total_provisioned:,.0f} GB")
        with col2:
            st.metric("In Use Storage", f"{total_in_use:,.0f} GB")
        with col3:
            if total_provisioned > 0:
                utilization = (total_in_use / total_provisioned) * 100
                st.metric("Storage Utilization", f"{utilization:.1f}%")
        
        # Style storage metrics
        style_metric_cards(
            background_color="#1f1f1f",
            border_left_color="#9370db",
            border_color="#2e2e2e",
            box_shadow="#1f1f1f"
        )
        
        add_vertical_space(1)
        
        # Storage chart
        storage_df = pd.DataFrame({
            'Type': ['Provisioned', 'In Use', 'Unshared'],
            'Size_GB': [total_provisioned, total_in_use, total_unshared]
        })
        fig = px.bar(
            storage_df,
            x='Type',
            y='Size_GB',
            color='Type',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(showlegend=False, yaxis_title="Storage (GB)")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
    finally:
        session.close()
