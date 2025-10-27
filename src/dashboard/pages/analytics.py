"""Analytics page - Advanced analytics and trends."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.models import VirtualMachine


def render(db_url: str):
    """Render the analytics page."""
    st.markdown('<h1 class="main-header">📈 Advanced Analytics</h1>', unsafe_allow_html=True)
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Resource allocation analysis
        st.subheader("Resource Allocation Patterns")
        
        vms = session.query(VirtualMachine).filter(
            VirtualMachine.cpus.isnot(None),
            VirtualMachine.memory.isnot(None)
        ).all()
        
        if vms:
            df_vms = pd.DataFrame([{
                'VM': vm.vm,
                'CPUs': vm.cpus,
                'Memory_GB': vm.memory / 1024,
                'Datacenter': vm.datacenter or 'Unknown',
                'Cluster': vm.cluster or 'Unknown',
                'PowerState': vm.powerstate or 'Unknown',
                'OS': (vm.os_config or 'Unknown')[:20]
            } for vm in vms if vm.cpus and vm.memory])
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CPU vs Memory scatter
                fig = px.scatter(
                    df_vms,
                    x='CPUs',
                    y='Memory_GB',
                    color='PowerState',
                    size='Memory_GB',
                    hover_data=['VM', 'Datacenter', 'Cluster'],
                    title='CPU vs Memory Allocation',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_layout(
                    xaxis_title='vCPUs',
                    yaxis_title='Memory (GB)'
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Resource configuration distribution
                df_vms['Config'] = df_vms['CPUs'].astype(str) + ' CPU / ' + df_vms['Memory_GB'].round(0).astype(int).astype(str) + ' GB'
                config_counts = df_vms['Config'].value_counts().head(10)
                
                fig = px.bar(
                    x=config_counts.values,
                    y=config_counts.index,
                    orientation='h',
                    title='Top 10 Resource Configurations',
                    labels={'x': 'Count', 'y': 'Configuration'},
                    color=config_counts.values,
                    color_continuous_scale='Teal'
                )
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, width='stretch')
        
        st.divider()
        
        # Power state timeline (if creation dates available)
        st.subheader("VM Creation Timeline")
        
        vms_with_dates = session.query(VirtualMachine).filter(
            VirtualMachine.creation_date.isnot(None)
        ).all()
        
        if vms_with_dates:
            df_dates = pd.DataFrame([{
                'Date': vm.creation_date.date(),
                'VM': vm.vm,
                'Datacenter': vm.datacenter or 'Unknown'
            } for vm in vms_with_dates])
            
            # Group by month
            df_dates['Month'] = pd.to_datetime(df_dates['Date']).dt.to_period('M')
            monthly_counts = df_dates.groupby('Month').size().reset_index(name='Count')
            monthly_counts['Month'] = monthly_counts['Month'].astype(str)
            
            fig = px.line(
                monthly_counts,
                x='Month',
                y='Count',
                title='VMs Created Over Time',
                markers=True
            )
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='VMs Created'
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No creation date information available")
        
        st.divider()
        
        # OS distribution analysis
        st.subheader("Operating System Analysis")
        
        os_data = session.query(
            VirtualMachine.os_config,
            func.count(VirtualMachine.id).label('count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).filter(
            VirtualMachine.os_config.isnot(None)
        ).group_by(VirtualMachine.os_config).order_by(func.count(VirtualMachine.id).desc()).limit(15).all()
        
        if os_data:
            df_os = pd.DataFrame(os_data, columns=['OS', 'Count', 'CPUs', 'Memory_MB'])
            df_os['Memory_GB'] = df_os['Memory_MB'] / 1024
            df_os = df_os.fillna(0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.treemap(
                    df_os,
                    path=['OS'],
                    values='Count',
                    title='OS Distribution (Top 15)',
                    color='Count',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                fig = px.sunburst(
                    df_os.head(10),
                    path=['OS'],
                    values='CPUs',
                    title='CPU Allocation by OS (Top 10)',
                    color='CPUs',
                    color_continuous_scale='Plasma'
                )
                st.plotly_chart(fig, width='stretch')
        
        st.divider()
        
        # Cluster efficiency analysis
        st.subheader("Cluster Efficiency Metrics")
        
        cluster_data = session.query(
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('vm_count'),
            func.count(func.distinct(VirtualMachine.host)).label('host_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).filter(
            VirtualMachine.cluster.isnot(None)
        ).group_by(VirtualMachine.cluster).all()
        
        if cluster_data:
            df_clusters = pd.DataFrame(
                cluster_data,
                columns=['Cluster', 'VMs', 'Hosts', 'CPUs', 'Memory_MB']
            )
            df_clusters['VMs_per_Host'] = df_clusters['VMs'] / df_clusters['Hosts']
            df_clusters['Memory_GB'] = df_clusters['Memory_MB'] / 1024
            df_clusters = df_clusters.fillna(0)
            df_clusters = df_clusters.sort_values('VMs', ascending=False).head(15)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    df_clusters,
                    x='Cluster',
                    y='VMs_per_Host',
                    title='Average VMs per Host by Cluster',
                    color='VMs_per_Host',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(
                    showlegend=False,
                    xaxis_tickangle=-45,
                    yaxis_title='VMs per Host'
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Bubble chart
                fig = px.scatter(
                    df_clusters,
                    x='CPUs',
                    y='Memory_GB',
                    size='VMs',
                    color='Hosts',
                    hover_data=['Cluster'],
                    title='Cluster Resource Distribution',
                    color_continuous_scale='Rainbow'
                )
                fig.update_layout(
                    xaxis_title='Total vCPUs',
                    yaxis_title='Total Memory (GB)'
                )
                st.plotly_chart(fig, width='stretch')
        
        st.divider()
        
        # Custom field analysis (if available)
        st.subheader("Environment Distribution")
        
        env_data = session.query(
            VirtualMachine.env,
            func.count(VirtualMachine.id).label('count')
        ).filter(
            VirtualMachine.env.isnot(None)
        ).group_by(VirtualMachine.env).all()
        
        if env_data:
            df_env = pd.DataFrame(env_data, columns=['Environment', 'Count'])
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                fig = px.pie(
                    df_env,
                    values='Count',
                    names='Environment',
                    title='VMs by Environment',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Environment metrics
                st.write("**Environment Breakdown**")
                for _, row in df_env.iterrows():
                    st.metric(row['Environment'], f"{row['Count']:,}")
        else:
            st.info("No environment classification data available")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
    finally:
        session.close()
