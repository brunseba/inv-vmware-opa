"""Migration Targets Management page - Configure migration destination platforms."""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.migration_target import MigrationTarget, PlatformType
from services.migration_scenarios import MigrationScenarioService


def render(db_url: str):
    """Render the migration targets management page."""
    colored_header(
        label="🎯 Migration Targets",
        description="Configure and manage migration destination platforms",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        service = MigrationScenarioService(session)
        
        # Tab navigation
        tab1, tab2, tab3 = st.tabs(["📋 Targets List", "➕ Add Target", "📊 Target Comparison"])
        
        with tab1:
            render_targets_list(service, session)
        
        with tab2:
            render_add_target(service)
        
        with tab3:
            render_target_comparison(service)
        
        session.close()
        
    except Exception as e:
        st.error(f"Error: {e}")


def render_targets_list(service: MigrationScenarioService, session):
    """Render list of existing migration targets."""
    st.subheader("Configured Migration Targets")
    
    targets = service.get_active_targets()
    
    if not targets:
        st.info("No migration targets configured. Add your first target in the 'Add Target' tab.")
        return
    
    # Create DataFrame
    targets_data = []
    for target in targets:
        targets_data.append({
            "ID": target.id,
            "Name": target.name,
            "Platform": target.platform_type.value.upper(),
            "Region": target.region or "N/A",
            "Bandwidth": f"{target.bandwidth_mbps} Mbps",
            "Max Parallel": target.max_parallel_migrations,
            "Live Migration": "✅" if target.supports_live_migration else "❌",
            "Active": "✅" if target.is_active else "❌"
        })
    
    df = pd.DataFrame(targets_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    add_vertical_space(2)
    
    # Target details
    st.subheader("Target Details")
    
    selected_target_id = st.selectbox(
        "Select target to view details",
        options=[t.id for t in targets],
        format_func=lambda x: next((t.name for t in targets if t.id == x), "Unknown")
    )
    
    if selected_target_id:
        target = session.query(MigrationTarget).get(selected_target_id)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Bandwidth", f"{target.bandwidth_mbps} Mbps")
            st.metric("Network Efficiency", f"{target.network_efficiency * 100:.0f}%")
            st.metric("Max Parallel", target.max_parallel_migrations)
        
        with col2:
            st.metric("Compute Cost", f"${target.compute_cost_per_vcpu:.4f}/vCPU/hr")
            st.metric("Memory Cost", f"${target.memory_cost_per_gb:.4f}/GB/hr")
            st.metric("Storage Cost", f"${target.storage_cost_per_gb:.4f}/GB/mo")
        
        with col3:
            st.metric("Ingress Cost", f"${target.network_ingress_cost_per_gb:.4f}/GB")
            st.metric("Egress Cost", f"${target.network_egress_cost_per_gb:.4f}/GB")
            st.metric("SLA Uptime", f"{target.sla_uptime_percent}%")
        
        add_vertical_space(1)
        
        # Actions
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("🔄 Toggle Active", key=f"toggle_{target.id}"):
                target.is_active = not target.is_active
                session.commit()
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{target.id}", type="secondary"):
                if st.session_state.get(f"confirm_delete_{target.id}"):
                    session.delete(target)
                    session.commit()
                    st.success(f"Deleted target: {target.name}")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{target.id}"] = True
                    st.warning("Click again to confirm deletion")


def render_add_target(service: MigrationScenarioService):
    """Render form to add new migration target."""
    st.subheader("Add New Migration Target")
    
    with st.form("add_target_form"):
        # Basic information
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Target Name*", placeholder="e.g., AWS US-East-1 Production")
            platform_type = st.selectbox(
                "Platform Type*",
                options=[p.value for p in PlatformType],
                format_func=lambda x: x.upper()
            )
        
        with col2:
            region = st.text_input("Region", placeholder="e.g., us-east-1, westeurope")
            support_level = st.selectbox(
                "Support Level",
                options=["24/7", "Business Hours", "Best Effort"]
            )
        
        add_vertical_space(1)
        
        # Network configuration
        st.markdown("#### Network Configuration")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bandwidth_mbps = st.number_input(
                "Bandwidth (Mbps)*",
                min_value=10,
                max_value=100000,
                value=1000,
                step=100
            )
        
        with col2:
            network_efficiency = st.slider(
                "Network Efficiency",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                step=0.05,
                format="%.0f%%",
                help="Typical: 70-80%"
            )
        
        with col3:
            max_parallel = st.number_input(
                "Max Parallel Migrations",
                min_value=1,
                max_value=100,
                value=10
            )
        
        add_vertical_space(1)
        
        # Cost configuration
        st.markdown("#### Cost Configuration (USD)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            compute_cost = st.number_input(
                "Compute ($/vCPU/hour)",
                min_value=0.0,
                max_value=10.0,
                value=0.05,
                step=0.01,
                format="%.4f"
            )
            memory_cost = st.number_input(
                "Memory ($/GB/hour)",
                min_value=0.0,
                max_value=1.0,
                value=0.01,
                step=0.001,
                format="%.4f"
            )
        
        with col2:
            storage_cost = st.number_input(
                "Storage ($/GB/month)",
                min_value=0.0,
                max_value=1.0,
                value=0.001,
                step=0.0001,
                format="%.4f"
            )
            network_ingress_cost = st.number_input(
                "Ingress ($/GB)",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.01,
                format="%.4f"
            )
        
        with col3:
            network_egress_cost = st.number_input(
                "Egress ($/GB)",
                min_value=0.0,
                max_value=1.0,
                value=0.09,
                step=0.01,
                format="%.4f"
            )
            sla_uptime = st.number_input(
                "SLA Uptime (%)",
                min_value=90.0,
                max_value=100.0,
                value=99.9,
                step=0.1,
                format="%.2f"
            )
        
        add_vertical_space(1)
        
        # Features
        st.markdown("#### Features")
        col1, col2 = st.columns(2)
        
        with col1:
            supports_live = st.checkbox("Supports Live Migration")
        
        with col2:
            is_active = st.checkbox("Active", value=True)
        
        add_vertical_space(1)
        
        # Submit button
        submitted = st.form_submit_button("➕ Add Target", type="primary", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("Please provide a target name")
            else:
                try:
                    target = service.create_target(
                        name=name,
                        platform_type=PlatformType(platform_type),
                        region=region,
                        bandwidth_mbps=int(bandwidth_mbps),
                        network_efficiency=network_efficiency,
                        compute_cost_per_vcpu=compute_cost,
                        memory_cost_per_gb=memory_cost,
                        storage_cost_per_gb=storage_cost,
                        network_ingress_cost_per_gb=network_ingress_cost,
                        network_egress_cost_per_gb=network_egress_cost,
                        max_parallel_migrations=max_parallel,
                        supports_live_migration=supports_live,
                        sla_uptime_percent=sla_uptime,
                        support_level=support_level,
                        is_active=is_active
                    )
                    st.success(f"✅ Created migration target: {target.name}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error creating target: {e}")


def render_target_comparison(service: MigrationScenarioService):
    """Render comparison of migration targets."""
    st.subheader("Target Platform Comparison")
    
    targets = service.get_active_targets()
    
    if len(targets) < 2:
        st.info("Add at least 2 targets to compare them.")
        return
    
    # Comparison table
    comparison_data = []
    for target in targets:
        comparison_data.append({
            "Target": target.name,
            "Platform": target.platform_type.value.upper(),
            "Region": target.region or "N/A",
            "Bandwidth (Mbps)": target.bandwidth_mbps,
            "Max Parallel": target.max_parallel_migrations,
            "Compute ($/vCPU/hr)": f"${target.compute_cost_per_vcpu:.4f}",
            "Memory ($/GB/hr)": f"${target.memory_cost_per_gb:.4f}",
            "Storage ($/GB/mo)": f"${target.storage_cost_per_gb:.4f}",
            "Egress ($/GB)": f"${target.network_egress_cost_per_gb:.4f}",
            "SLA %": target.sla_uptime_percent,
            "Live Migration": "✅" if target.supports_live_migration else "❌"
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    add_vertical_space(2)
    
    # Cost comparison chart
    st.subheader("Cost Comparison")
    
    cost_data = []
    for target in targets:
        cost_data.append({
            "Target": target.name,
            "Compute": target.compute_cost_per_vcpu,
            "Memory": target.memory_cost_per_gb,
            "Storage": target.storage_cost_per_gb,
            "Egress": target.network_egress_cost_per_gb
        })
    
    cost_df = pd.DataFrame(cost_data).set_index("Target")
    st.bar_chart(cost_df)
