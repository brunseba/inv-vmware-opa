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

from src.models import MigrationTarget, PlatformType, Base
from src.services.migration_scenarios import MigrationScenarioService


def render(db_url: str):
    """Render the migration targets management page."""
    colored_header(
        label="🎯 Migration Targets",
        description="Configure and manage migration destination platforms",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        # Ensure migration tables exist
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        service = MigrationScenarioService(session)
        
        # Tab navigation
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Targets List", "➕ Add Target", "✏️ Edit Target", "📊 Target Comparison"])
        
        with tab1:
            render_targets_list(service, session)
        
        with tab2:
            render_add_target(service, session)
        
        with tab3:
            render_edit_target(service, session)
        
        with tab4:
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
            "Type": target.platform_type.value.upper(),
            "Region": target.region or "N/A",
            "Bandwidth": f"{target.bandwidth_mbps} Mbps",
            "Max Parallel": target.max_parallel_migrations,
            "Live Migration": "✅" if target.supports_live_migration else "❌",
            "Active": "✅" if target.is_active else "❌"
        })
    
    df = pd.DataFrame(targets_data)
    st.dataframe(df, width='stretch', hide_index=True)
    
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
        
        # Network and cost metrics
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
        
        # Replication efficiency parameters
        st.markdown("##### 🔄 Replication Efficiency Parameters")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            compression = getattr(target, 'compression_ratio', 0.6)
            st.metric(
                "📉 Compression", 
                f"{(1-compression)*100:.0f}% savings",
                help=f"Compression ratio: {compression:.2f}"
            )
        
        with col2:
            dedup = getattr(target, 'dedup_ratio', 0.8)
            st.metric(
                "📉 Deduplication", 
                f"{(1-dedup)*100:.0f}% savings",
                help=f"Dedup ratio: {dedup:.2f}"
            )
        
        with col3:
            change_rate = getattr(target, 'change_rate_percent', 0.10)
            st.metric(
                "🔄 Change Rate", 
                f"{change_rate*100:.0f}%",
                help="Data change during migration"
            )
        
        with col4:
            delta_syncs = getattr(target, 'delta_sync_count', 2)
            st.metric(
                "🔁 Delta Syncs", 
                f"{delta_syncs}x",
                help="Number of synchronizations"
            )
        
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


def render_add_target(service: MigrationScenarioService, session):
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
                "Network Efficiency (%)",
                min_value=50,
                max_value=100,
                value=80,
                step=5,
                help="Typical: 70-80%"
            )
            # Convert percentage to decimal for storage
            network_efficiency = network_efficiency / 100.0
        
        with col3:
            max_parallel = st.number_input(
                "Max Parallel Migrations",
                min_value=1,
                max_value=100,
                value=10
            )
        
        add_vertical_space(1)
        
        # Replication efficiency parameters
        st.markdown("#### Replication Efficiency")
        st.caption("These parameters affect migration duration calculations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            compression_ratio = st.slider(
                "Compression Ratio",
                min_value=0.3,
                max_value=1.0,
                value=0.6,
                step=0.05,
                help="Lower = more compression. 0.6 = 40% size reduction (typical)",
                format="%.2f"
            )
            st.caption(f"📉 {(1-compression_ratio)*100:.0f}% compression savings")
            
            dedup_ratio = st.slider(
                "Deduplication Ratio",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                step=0.05,
                help="Lower = more deduplication. 0.8 = 20% savings (typical)",
                format="%.2f"
            )
            st.caption(f"📉 {(1-dedup_ratio)*100:.0f}% dedup savings")
        
        with col2:
            change_rate_percent = st.slider(
                "Data Change Rate (%)",
                min_value=0.0,
                max_value=50.0,
                value=10.0,
                step=1.0,
                help="Percentage of data that changes during migration",
                format="%.0f"
            )
            # Convert to decimal
            change_rate_percent = change_rate_percent / 100.0
            
            delta_sync_count = st.number_input(
                "Delta Sync Count",
                min_value=1,
                max_value=5,
                value=2,
                help="Number of delta synchronizations before cutover"
            )
        
        with col3:
            network_protocol_overhead = st.slider(
                "Network Overhead",
                min_value=1.0,
                max_value=1.5,
                value=1.2,
                step=0.05,
                help="TCP/IP protocol overhead. 1.2 = 20% overhead (typical)",
                format="%.2f"
            )
            st.caption(f"📊 {(network_protocol_overhead-1)*100:.0f}% overhead")
            
            st.markdown("")
            st.info("""
                💡 **Replication Model:**  
                Total time = Initial sync + Delta syncs + Cutover
            """)
        
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
        submitted = st.form_submit_button("➕ Add Target", type="primary", width='stretch')
        
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
                        compression_ratio=compression_ratio,
                        dedup_ratio=dedup_ratio,
                        change_rate_percent=change_rate_percent,
                        network_protocol_overhead=network_protocol_overhead,
                        delta_sync_count=int(delta_sync_count),
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
                    # Force refresh
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating target: {e}")


def render_edit_target(service: MigrationScenarioService, session):
    """Render form to edit existing migration target."""
    st.subheader("Edit Migration Target")
    
    # Get all targets
    all_targets = session.query(MigrationTarget).all()
    
    if not all_targets:
        st.info("No migration targets available. Add your first target in the 'Add Target' tab.")
        return
    
    # Select target to edit
    selected_target_id = st.selectbox(
        "Select target to edit",
        options=[t.id for t in all_targets],
        format_func=lambda x: next((f"{t.name} ({t.platform_type.value.upper()})" for t in all_targets if t.id == x), "Unknown"),
        key="edit_target_select"
    )
    
    if not selected_target_id:
        return
    
    target = session.query(MigrationTarget).get(selected_target_id)
    
    with st.form("edit_target_form"):
        # Basic information
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Target Name*", value=target.name)
            platform_type = st.selectbox(
                "Platform Type*",
                options=[p.value for p in PlatformType],
                format_func=lambda x: x.upper(),
                index=[p.value for p in PlatformType].index(target.platform_type.value)
            )
        
        with col2:
            region = st.text_input("Region", value=target.region or "")
            support_level = st.selectbox(
                "Support Level",
                options=["24/7", "Business Hours", "Best Effort"],
                index=["24/7", "Business Hours", "Best Effort"].index(target.support_level) if target.support_level in ["24/7", "Business Hours", "Best Effort"] else 0
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
                value=target.bandwidth_mbps,
                step=100
            )
        
        with col2:
            network_efficiency = st.slider(
                "Network Efficiency (%)",
                min_value=50,
                max_value=100,
                value=int(target.network_efficiency * 100),
                step=5,
                help="Typical: 70-80%"
            )
            # Convert percentage to decimal for storage
            network_efficiency = network_efficiency / 100.0
        
        with col3:
            max_parallel = st.number_input(
                "Max Parallel Migrations",
                min_value=1,
                max_value=100,
                value=target.max_parallel_migrations
            )
        
        add_vertical_space(1)
        
        # Replication efficiency parameters
        st.markdown("#### Replication Efficiency")
        st.caption("These parameters affect migration duration calculations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            compression_ratio = st.slider(
                "Compression Ratio",
                min_value=0.3,
                max_value=1.0,
                value=float(getattr(target, 'compression_ratio', 0.6)),
                step=0.05,
                help="Lower = more compression. 0.6 = 40% size reduction (typical)",
                format="%.2f",
                key="edit_compression"
            )
            st.caption(f"📉 {(1-compression_ratio)*100:.0f}% compression savings")
            
            dedup_ratio = st.slider(
                "Deduplication Ratio",
                min_value=0.5,
                max_value=1.0,
                value=float(getattr(target, 'dedup_ratio', 0.8)),
                step=0.05,
                help="Lower = more deduplication. 0.8 = 20% savings (typical)",
                format="%.2f",
                key="edit_dedup"
            )
            st.caption(f"📉 {(1-dedup_ratio)*100:.0f}% dedup savings")
        
        with col2:
            change_rate_percent_display = float(getattr(target, 'change_rate_percent', 0.10)) * 100
            change_rate_percent_input = st.slider(
                "Data Change Rate (%)",
                min_value=0.0,
                max_value=50.0,
                value=change_rate_percent_display,
                step=1.0,
                help="Percentage of data that changes during migration",
                format="%.0f",
                key="edit_change_rate"
            )
            # Convert to decimal
            change_rate_percent = change_rate_percent_input / 100.0
            
            delta_sync_count = st.number_input(
                "Delta Sync Count",
                min_value=1,
                max_value=5,
                value=int(getattr(target, 'delta_sync_count', 2)),
                help="Number of delta synchronizations before cutover",
                key="edit_delta_sync"
            )
        
        with col3:
            network_protocol_overhead = st.slider(
                "Network Overhead",
                min_value=1.0,
                max_value=1.5,
                value=float(getattr(target, 'network_protocol_overhead', 1.2)),
                step=0.05,
                help="TCP/IP protocol overhead. 1.2 = 20% overhead (typical)",
                format="%.2f",
                key="edit_overhead"
            )
            st.caption(f"📊 {(network_protocol_overhead-1)*100:.0f}% overhead")
            
            st.markdown("")
            st.info("""
                💡 **Replication Model:**  
                Total time = Initial sync + Delta syncs + Cutover
            """)
        
        add_vertical_space(1)
        
        # Cost configuration
        st.markdown("#### Cost Configuration (USD)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            compute_cost = st.number_input(
                "Compute ($/vCPU/hour)",
                min_value=0.0,
                max_value=10.0,
                value=target.compute_cost_per_vcpu,
                step=0.01,
                format="%.4f"
            )
            memory_cost = st.number_input(
                "Memory ($/GB/hour)",
                min_value=0.0,
                max_value=1.0,
                value=target.memory_cost_per_gb,
                step=0.001,
                format="%.4f"
            )
        
        with col2:
            storage_cost = st.number_input(
                "Storage ($/GB/month)",
                min_value=0.0,
                max_value=1.0,
                value=target.storage_cost_per_gb,
                step=0.0001,
                format="%.4f"
            )
            network_ingress_cost = st.number_input(
                "Ingress ($/GB)",
                min_value=0.0,
                max_value=1.0,
                value=target.network_ingress_cost_per_gb,
                step=0.01,
                format="%.4f"
            )
        
        with col3:
            network_egress_cost = st.number_input(
                "Egress ($/GB)",
                min_value=0.0,
                max_value=1.0,
                value=target.network_egress_cost_per_gb,
                step=0.01,
                format="%.4f"
            )
            sla_uptime = st.number_input(
                "SLA Uptime (%)",
                min_value=90.0,
                max_value=100.0,
                value=target.sla_uptime_percent,
                step=0.1,
                format="%.2f"
            )
        
        add_vertical_space(1)
        
        # Features
        st.markdown("#### Features")
        col1, col2 = st.columns(2)
        
        with col1:
            supports_live = st.checkbox("Supports Live Migration", value=target.supports_live_migration)
        
        with col2:
            is_active = st.checkbox("Active", value=target.is_active)
        
        add_vertical_space(1)
        
        # Submit button
        submitted = st.form_submit_button("✏️ Update Target", type="primary", width='stretch')
        
        if submitted:
            if not name:
                st.error("Please provide a target name")
            else:
                try:
                    # Update target fields
                    target.name = name
                    target.platform_type = PlatformType(platform_type)
                    target.region = region
                    target.bandwidth_mbps = int(bandwidth_mbps)
                    target.network_efficiency = network_efficiency
                    target.compression_ratio = compression_ratio
                    target.dedup_ratio = dedup_ratio
                    target.change_rate_percent = change_rate_percent
                    target.network_protocol_overhead = network_protocol_overhead
                    target.delta_sync_count = int(delta_sync_count)
                    target.compute_cost_per_vcpu = compute_cost
                    target.memory_cost_per_gb = memory_cost
                    target.storage_cost_per_gb = storage_cost
                    target.network_ingress_cost_per_gb = network_ingress_cost
                    target.network_egress_cost_per_gb = network_egress_cost
                    target.max_parallel_migrations = max_parallel
                    target.supports_live_migration = supports_live
                    target.sla_uptime_percent = sla_uptime
                    target.support_level = support_level
                    target.is_active = is_active
                    
                    session.commit()
                    st.success(f"✅ Updated migration target: {target.name}")
                    # Force refresh
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating target: {e}")
                    session.rollback()


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
    st.dataframe(df, width='stretch', hide_index=True)
    
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
