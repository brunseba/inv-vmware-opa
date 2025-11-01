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
    
    # Create tabs: Fixed charts vs Custom explorer
    tab1, tab2 = st.tabs(["📊 Built-in Analytics", "🔬 Custom Explorer"])
    
    with tab1:
        render_builtin_analytics(db_url)
    
    with tab2:
        render_custom_explorer(db_url)


def render_builtin_analytics(db_url: str):
    """Render the built-in fixed analytics charts."""
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


def render_custom_explorer(db_url: str):
    """Render PyGWalker custom explorer for analytics."""
    st.markdown("""
    💡 **Custom Analytics Explorer** - Create your own visualizations!
    
    This tab loads all VM data with detailed metrics for custom analysis.
    Drag and drop fields to create any chart you want.
    """)
    
    st.divider()
    
    # Load options
    col1, col2 = st.columns(2)
    with col1:
        limit = st.selectbox(
            "Maximum Rows",
            options=[1000, 5000, 10000, 25000],
            index=2,
            key="analytics_limit"
        )
    with col2:
        include_templates = st.checkbox(
            "Include Templates",
            value=False,
            key="analytics_templates"
        )
    
    if st.button("🔄 Load Data for Explorer", type="primary", use_container_width=True):
        with st.spinner(f"Loading {limit:,} VMs..."):
            try:
                engine = create_engine(db_url, echo=False)
                SessionLocal = sessionmaker(bind=engine)
                session = SessionLocal()
                
                query = session.query(VirtualMachine)
                if not include_templates:
                    query = query.filter(VirtualMachine.template == False)
                
                vms = query.limit(limit).all()
                
                if not vms:
                    st.warning("No VMs found.")
                    session.close()
                    return
                
                # Prepare comprehensive DataFrame for analytics
                df = pd.DataFrame([{
                    'VM': vm.vm or 'Unknown',
                    'CPUs': vm.cpus or 0,
                    'Memory_GB': round((vm.memory or 0) / 1024, 2),
                    'Storage_Provisioned_GB': round((vm.provisioned_mib or 0) / 1024, 2),
                    'Storage_InUse_GB': round((vm.in_use_mib or 0) / 1024, 2),
                    'Storage_Unshared_GB': round((vm.unshared_mib or 0) / 1024, 2),
                    'Storage_Efficiency_%': round(((vm.in_use_mib or 0) / (vm.provisioned_mib or 1)) * 100, 1) if vm.provisioned_mib and vm.provisioned_mib > 0 else 0,
                    'Datacenter': vm.datacenter or 'Unknown',
                    'Cluster': vm.cluster or 'Unknown',
                    'Host': vm.host or 'Unknown',
                    'Resource_Pool': vm.resource_pool or 'Unknown',
                    'Folder': vm.folder or 'Unknown',
                    'PowerState': vm.powerstate or 'Unknown',
                    'OS': (vm.os_config or 'Unknown')[:50],
                    'Environment': vm.env or 'Unknown',
                    'Is_Template': bool(vm.template),
                    'NICs': vm.nics or 0,
                    'Disks': vm.disks or 0,
                    'HW_Version': vm.hw_version or 'Unknown'
                } for vm in vms])
                
                session.close()
                
                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 VMs", f"{len(df):,}")
                with col2:
                    st.metric("⚡ vCPUs", f"{df['CPUs'].sum():,}")
                with col3:
                    st.metric("💾 RAM", f"{df['Memory_GB'].sum():,.1f} GB")
                with col4:
                    st.metric("💿 Storage", f"{df['Storage_Provisioned_GB'].sum():,.1f} GB")
                
                st.divider()
                
                # Render PyGWalker
                try:
                    import pygwalker as pyg
                    pyg.walk(
                        df,
                        env='Streamlit',
                        spec="./configs/analytics_explorer.json",
                        use_kernel_calc=True,
                        dark='media'
                    )
                except ImportError:
                    st.error("PyGWalker not installed. Install with: `uv pip install pygwalker`")
                    st.dataframe(df, width='stretch', height=600)
                except Exception as e:
                    st.error(f"Error rendering explorer: {e}")
                    st.dataframe(df, width='stretch', height=600)
                    
            except Exception as e:
                st.error(f"Error loading data: {e}")
    else:
        st.info("👆 Click 'Load Data for Explorer' to start custom analytics")
