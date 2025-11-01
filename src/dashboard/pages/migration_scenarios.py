"""Migration Scenarios page - Create and compare migration scenarios."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import VirtualMachine, MigrationTarget, MigrationScenario, MigrationStrategy, MigrationWave, Base, Label
from src.services.migration_scenarios import MigrationScenarioService


def render(db_url: str):
    """Render the migration scenarios page."""
    colored_header(
        label="🔄 Migration Scenarios",
        description="Create and compare migration scenarios across multiple targets",
        color_name="green-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        # Ensure migration tables exist
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        service = MigrationScenarioService(session)
        
        # Check for migration targets
        targets = service.get_active_targets()
        if not targets:
            st.warning("⚠️ No migration targets configured. Please add targets first.")
            if st.button("➕ Go to Migration Targets"):
                st.switch_page("pages/migration_targets.py")
            return
        
        # Tab navigation
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Scenarios List", "➕ Create Scenario", "✏️ Edit Scenario", "📊 Compare Scenarios", "🌊 Migration Waves"])
        
        with tab1:
            render_scenarios_list(service, session)
        
        with tab2:
            render_create_scenario(service, session)
        
        with tab3:
            render_edit_scenario(service, session)
        
        with tab4:
            render_compare_scenarios(service)
        
        with tab5:
            render_migration_waves(service, session)
        
        session.close()
        
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())


def render_scenarios_list(service: MigrationScenarioService, session):
    """Render list of existing scenarios."""
    st.subheader("Existing Migration Scenarios")
    
    scenarios = session.query(MigrationScenario).all()
    
    if not scenarios:
        st.info("No migration scenarios created yet. Create your first scenario in the 'Create Scenario' tab.")
        return
    
    # Bulk recalculation section
    with st.expander("🔄 Bulk Recalculate Scenarios", expanded=False):
        st.caption("Recalculate costs and durations for scenarios when target parameters change")
        
        scenario_names_recalc = {s.id: f"{s.name} ({s.target.name})" for s in scenarios}
        selected_recalc_ids = st.multiselect(
            "Select scenarios to recalculate",
            options=list(scenario_names_recalc.keys()),
            format_func=lambda x: scenario_names_recalc[x],
            key="bulk_recalc_select"
        )
        
        if selected_recalc_ids:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔄 Recalculate Selected", type="primary", key="bulk_recalc_btn"):
                    with st.spinner(f"Recalculating {len(selected_recalc_ids)} scenario(s)..."):
                        try:
                            recalc_count = 0
                            for scenario_id in selected_recalc_ids:
                                scenario = session.query(MigrationScenario).get(scenario_id)
                                if scenario:
                                    # Get VMs based on existing criteria
                                    vms = service._get_vms_by_criteria(scenario.vm_selection_criteria)
                                    
                                    if vms:
                                        # Get target
                                        target = session.query(MigrationTarget).get(scenario.target_id)
                                        
                                        # Recalculate estimates
                                        cost_breakdown = service.calculate_migration_cost(
                                            vms, target, scenario.estimated_duration_days or 30, scenario.strategy
                                        )
                                        duration = service.calculate_migration_duration(vms, target, 5, scenario.strategy)
                                        risk_level, risk_factors = service.assess_risk_level(vms, target, scenario.strategy)
                                        recommendation_score = service.calculate_recommendation_score(
                                            cost_breakdown, duration, risk_level, target
                                        )
                                        
                                        # Update scenario with new calculations
                                        scenario.estimated_duration_days = duration["total_days"]
                                        scenario.estimated_cost_total = cost_breakdown["total"]
                                        scenario.estimated_cost_breakdown = cost_breakdown
                                        
                                        # Update separated cost fields
                                        scenario.estimated_migration_cost = cost_breakdown["migration"]["total"]
                                        scenario.estimated_runtime_cost_monthly = cost_breakdown["runtime_monthly"]["total"]
                                        scenario.migration_cost_breakdown = cost_breakdown["migration"]
                                        scenario.runtime_cost_breakdown = cost_breakdown["runtime_monthly"]
                                        
                                        scenario.risk_level = risk_level
                                        scenario.risk_factors = risk_factors
                                        scenario.recommendation_score = recommendation_score
                                        scenario.recommended = (recommendation_score >= 70)
                                        
                                        recalc_count += 1
                            
                            session.commit()
                            st.success(f"✅ Recalculated {recalc_count} scenario(s) successfully")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error recalculating scenarios: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                            session.rollback()
            with col2:
                st.info("💡 Use this when migration target parameters (costs, region, etc.) have changed")
    
    add_vertical_space(1)
    
    # Bulk delete section
    with st.expander("🗑️ Bulk Delete Scenarios", expanded=False):
        st.caption("Select multiple scenarios to delete at once")
        
        scenario_names = {s.id: f"{s.name} ({s.target.name})" for s in scenarios}
        selected_ids = st.multiselect(
            "Select scenarios to delete",
            options=list(scenario_names.keys()),
            format_func=lambda x: scenario_names[x],
            key="bulk_delete_select"
        )
        
        if selected_ids:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🗑️ Delete Selected", type="secondary", key="bulk_delete_btn"):
                    if st.session_state.get("confirm_bulk_delete"):
                        deleted_count = service.delete_scenarios_bulk(selected_ids)
                        st.success(f"✅ Deleted {deleted_count} scenario(s)")
                        st.session_state.confirm_bulk_delete = False
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.session_state.confirm_bulk_delete = True
                        st.warning(f"⚠️ Click again to confirm deletion of {len(selected_ids)} scenario(s)")
            with col2:
                if st.session_state.get("confirm_bulk_delete"):
                    if st.button("❌ Cancel", key="cancel_bulk_delete"):
                        st.session_state.confirm_bulk_delete = False
                        st.rerun()
    
    add_vertical_space(1)
    
    # Column descriptions with tooltips
    st.markdown("**📊 Migration Scenarios Overview**")
    with st.expander("ℹ️ Column Descriptions", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            - **ID**: Unique scenario identifier
            - **Name**: Scenario name for easy reference
            - **Target**: Migration destination platform name
            - **Platform**: Target platform type (AWS, Azure, GCP, etc.)
            - **Strategy**: Migration strategy from 6Rs framework
              - *Rehost*: Lift-and-shift (minimal changes)
              - *Replatform*: Minor optimizations during migration
              - *Refactor*: Re-architect for cloud-native
              - *Repurchase*: Move to SaaS alternative
              - *Retain*: Keep as-is
              - *Retire*: Decommission
            - **VMs**: Total number of virtual machines
            - **vCPUs**: Total virtual CPU cores across all VMs
            - **RAM (GB)**: Total memory in gigabytes
            - **Storage (GB)**: Total provisioned storage in gigabytes
            """)
        
        with col2:
            st.markdown("""
            - **Duration (days)**: Estimated total migration time
              - Formula: (Repl hours / 24) + (Cutover hours / 8)
              - Replication runs 24/7, cutover in 8-hour windows
            - **Total (h)**: Total hours (Replication + Cutover)
              - Sum of all phases for verification
            - **🔄 Repl (h)**: Total replication time (adjusted)
              - Initial full copy + delta syncs
              - Includes strategy-specific efficiency multiplier
              - Accounts for compression, dedup, network overhead
            - **✅ Cutover (h)**: Final cutover and validation
              - VM-by-VM testing and validation (2h per VM)
              - Performed in parallel waves
            - **Cost ($)**: Total estimated cost
              - Includes one-time migration + runtime for duration
            - **Risk**: Risk assessment level
              - Based on VM count, data volume, platform complexity
            - **Score**: Recommendation score (0-100)
              - Higher is better (cost, duration, risk factors)
            - **Recommended**: ✅ if score ≥70, ❌ otherwise
            """)
    
    add_vertical_space(1)
    
    # Create DataFrame with replication breakdown
    scenarios_data = []
    for scenario in scenarios:
        # Calculate detailed duration breakdown
        try:
            vms = service._get_vms_by_criteria(scenario.vm_selection_criteria)
            target = scenario.target
            if vms and target:
                duration_detail = service.calculate_migration_duration(vms, target, 5, scenario.strategy)
                initial_repl_h = duration_detail.get('initial_replication_hours', 0)
                delta_sync_h = duration_detail.get('delta_sync_hours', 0)
                cutover_h = duration_detail.get('cutover_hours', 0)
                total_repl_h = duration_detail.get('total_replication_hours', 0)  # Adjusted with strategy efficiency
                total_h = duration_detail.get('total_hours', 0)
                # Calculate duration from live values to match hour columns
                calculated_days = duration_detail.get('total_days', 0)
            else:
                initial_repl_h = delta_sync_h = cutover_h = total_repl_h = total_h = calculated_days = 0
        except:
            initial_repl_h = delta_sync_h = cutover_h = total_repl_h = total_h = calculated_days = 0
        
        scenarios_data.append({
            "ID": scenario.id,
            "Name": scenario.name,
            "Target": scenario.target.name,
            "Platform": scenario.target.platform_type.value.upper(),
            "Strategy": scenario.strategy.value.capitalize(),
            "VMs": scenario.vm_count or 0,
            "vCPUs": scenario.total_vcpus or 0,
            "RAM (GB)": f"{scenario.total_memory_gb:.1f}" if scenario.total_memory_gb else "0.0",
            "Storage (GB)": f"{scenario.total_storage_gb:.1f}" if scenario.total_storage_gb else "0.0",
            "Duration (days)": f"{calculated_days:.1f}",
            "Total (h)": f"{total_h:.1f}",
            "🔄 Repl (h)": f"{total_repl_h:.1f}",
            "✅ Cutover (h)": f"{cutover_h:.1f}",
            "Cost ($)": f"${scenario.estimated_cost_total:,.0f}",
            "Risk": scenario.risk_level,
            "Score": f"{scenario.recommendation_score:.0f}/100",
            "Recommended": "✅" if scenario.recommended else "❌"
        })
    
    df = pd.DataFrame(scenarios_data)
    st.dataframe(df, width='stretch', hide_index=True)
    
    add_vertical_space(2)
    
    # Scenario details
    st.subheader("Scenario Details")
    
    selected_scenario_id = st.selectbox(
        "Select scenario to view details",
        options=[s.id for s in scenarios],
        format_func=lambda x: next((s.name for s in scenarios if s.id == x), "Unknown")
    )
    
    if selected_scenario_id:
        scenario = session.query(MigrationScenario).get(selected_scenario_id)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Target", scenario.target.name)
            st.metric("Platform", scenario.target.platform_type.value.upper())
        
        with col2:
            st.metric("Strategy", scenario.strategy.value.capitalize())
            st.metric("Risk Level", scenario.risk_level)
        
        with col3:
            st.metric("Duration", f"{scenario.estimated_duration_days:.1f} days")
            st.metric("Total Cost", f"${scenario.estimated_cost_total:,.2f}")
        
        with col4:
            st.metric("Score", f"{scenario.recommendation_score:.0f}/100")
            st.metric("Recommended", "✅ Yes" if scenario.recommended else "❌ No")
        
        add_vertical_space(1)
        
        # Duration breakdown - Calculate live from scenario data
        st.markdown("#### ⏱️ Migration Timeline Breakdown")
        
        # Recalculate duration to get detailed breakdown
        try:
            vms = service._get_vms_by_criteria(scenario.vm_selection_criteria)
            target = scenario.target
            if vms and target:
                duration_detail = service.calculate_migration_duration(
                    vms, target, 5, scenario.strategy
                )
                
                # Display detailed metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "🔄 Initial Replication",
                        f"{duration_detail.get('initial_replication_hours', 0):.1f}h",
                        help="Full data replication time"
                    )
                
                with col2:
                    st.metric(
                        "🔁 Delta Syncs",
                        f"{duration_detail.get('delta_sync_hours', 0):.1f}h",
                        help="Incremental synchronization time"
                    )
                
                with col3:
                    st.metric(
                        "✅ Cutover",
                        f"{duration_detail.get('cutover_hours', 0):.1f}h",
                        help="Validation and cutover time"
                    )
                
                with col4:
                    st.metric(
                        "🎯 Total",
                        f"{duration_detail.get('total_hours', 0):.1f}h",
                        help="Total migration time"
                    )
                
                add_vertical_space(1)
                
                # Data efficiency metrics
                st.markdown("##### 💾 Data Transfer Efficiency")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    original_tb = duration_detail.get('original_data_tb', 0)
                    st.metric(
                        "📊 Original Data",
                        f"{original_tb:.2f} TB",
                        help="Total VM storage before optimization"
                    )
                
                with col2:
                    effective_tb = duration_detail.get('effective_data_tb', 0)
                    st.metric(
                        "💾 Transferred",
                        f"{effective_tb:.2f} TB",
                        help="Actual data transferred"
                    )
                
                with col3:
                    compression_pct = duration_detail.get('compression_savings_percent', 0)
                    st.metric(
                        "📉 Compression",
                        f"{compression_pct:.0f}%",
                        help="Compression savings"
                    )
                
                with col4:
                    dedup_pct = duration_detail.get('dedup_savings_percent', 0)
                    st.metric(
                        "📉 Dedup",
                        f"{dedup_pct:.0f}%",
                        help="Deduplication savings"
                    )
                
                # Timeline visualization
                add_vertical_space(1)
                
                st.markdown("##### 📅 Timeline Distribution")
                
                # Create a simple progress-bar style visualization
                init_hours = duration_detail.get('initial_replication_hours', 0)
                delta_hours = duration_detail.get('delta_sync_hours', 0)
                cutover_hours = duration_detail.get('cutover_hours', 0)
                total = init_hours + delta_hours + cutover_hours
                
                if total > 0:
                    init_pct = (init_hours / total) * 100
                    delta_pct = (delta_hours / total) * 100
                    cutover_pct = (cutover_hours / total) * 100
                    
                    col1, col2, col3 = st.columns([init_pct, delta_pct, cutover_pct])
                    
                    with col1:
                        st.markdown(f"""<div style="background-color: #4CAF50; padding: 10px; border-radius: 5px; text-align: center;">
                            <b>🔄 Initial</b><br>{init_hours:.1f}h ({init_pct:.0f}%)
                        </div>""", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""<div style="background-color: #2196F3; padding: 10px; border-radius: 5px; text-align: center;">
                            <b>🔁 Delta</b><br>{delta_hours:.1f}h ({delta_pct:.0f}%)
                        </div>""", unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""<div style="background-color: #FF9800; padding: 10px; border-radius: 5px; text-align: center;">
                            <b>✅ Cutover</b><br>{cutover_hours:.1f}h ({cutover_pct:.0f}%)
                        </div>""", unsafe_allow_html=True)
                
        except Exception as e:
            st.warning(f"⚠️ Could not calculate detailed duration breakdown: {e}")
        
        add_vertical_space(1)
        
        # Resource metrics
        st.markdown("#### Resource Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💻 VMs", f"{scenario.vm_count or 0:,}")
        
        with col2:
            st.metric("⚡ vCPUs", f"{scenario.total_vcpus or 0:,}")
        
        with col3:
            memory_gb = scenario.total_memory_gb or 0
            st.metric("💾 RAM", f"{memory_gb:,.1f} GB")
        
        with col4:
            storage_gb = scenario.total_storage_gb or 0
            st.metric("💾 Storage", f"{storage_gb:,.1f} GB")
        
        add_vertical_space(1)
        
        # Cost breakdown - Migration vs Runtime
        st.markdown("#### Cost Analysis")
        
        # Cost summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            migration_cost = scenario.estimated_migration_cost or 0
            st.metric(
                "📦 Migration Cost (One-Time)", 
                f"${migration_cost:,.2f}",
                help="One-time costs for migration labor and data transfer"
            )
        
        with col2:
            runtime_cost = scenario.estimated_runtime_cost_monthly or 0
            st.metric(
                "🔄 Runtime Cost (Monthly)", 
                f"${runtime_cost:,.2f}",
                help="Ongoing monthly operational costs"
            )
        
        with col3:
            if scenario.estimated_duration_days:
                months = scenario.estimated_duration_days / 30
                runtime_for_duration = runtime_cost * months
                st.metric(
                    "📅 Runtime for Duration",
                    f"${runtime_for_duration:,.2f}",
                    help=f"Runtime costs for {months:.1f} months"
                )
        
        add_vertical_space(1)
        
        # Detailed cost breakdowns
        if scenario.migration_cost_breakdown or scenario.runtime_cost_breakdown:
            col1, col2 = st.columns(2)
            
            with col1:
                if scenario.migration_cost_breakdown:
                    st.markdown("##### Migration Cost Breakdown")
                    migration_data = []
                    for key, value in scenario.migration_cost_breakdown.items():
                        if key != "total" and value > 0:
                            migration_data.append({"Category": key.replace("_", " ").title(), "Cost": value})
                    
                    if migration_data:
                        mig_df = pd.DataFrame(migration_data)
                        fig1 = px.pie(
                            mig_df,
                            values="Cost",
                            names="Category",
                            title="Migration Costs"
                        )
                        st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                if scenario.runtime_cost_breakdown:
                    st.markdown("##### Runtime Cost Breakdown (Monthly)")
                    runtime_data = []
                    for key, value in scenario.runtime_cost_breakdown.items():
                        if key != "total" and value > 0:
                            runtime_data.append({"Category": key.replace("_", " ").title(), "Cost": value})
                    
                    if runtime_data:
                        run_df = pd.DataFrame(runtime_data)
                        fig2 = px.pie(
                            run_df,
                            values="Cost",
                            names="Category",
                            title="Monthly Runtime Costs"
                        )
                        st.plotly_chart(fig2, use_container_width=True)
        
        # Risk factors
        if scenario.risk_factors:
            st.markdown("#### Risk Factors")
            for factor in scenario.risk_factors:
                st.warning(f"⚠️ {factor.replace('_', ' ').title()}")
        
        add_vertical_space(1)
        
        # Actions
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("🗑️ Delete Scenario", key=f"delete_{scenario.id}", type="secondary"):
                confirm_key = f"confirm_delete_scenario_{scenario.id}"
                if st.session_state.get(confirm_key):
                    if service.delete_scenario(scenario.id):
                        st.success(f"✅ Deleted scenario: {scenario.name}")
                        st.session_state[confirm_key] = False
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete scenario")
                else:
                    st.session_state[confirm_key] = True
                    st.rerun()
        
        with col2:
            confirm_key = f"confirm_delete_scenario_{scenario.id}"
            if st.session_state.get(confirm_key):
                if st.button("❌ Cancel", key=f"cancel_delete_{scenario.id}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
        
        # Show confirmation warning
        if st.session_state.get(f"confirm_delete_scenario_{scenario.id}"):
            st.warning("⚠️ Click 'Delete Scenario' again to confirm, or click 'Cancel' to abort.")


def render_create_scenario(service: MigrationScenarioService, session):
    """Render form to create new migration scenario."""
    st.subheader("Create New Migration Scenario")
    
    with st.form("create_scenario_form"):
        # Basic information
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Scenario Name*", placeholder="e.g., AWS Migration - Phase 1")
            description = st.text_area("Description", placeholder="Optional description")
        
        with col2:
            targets = service.get_active_targets()
            target_id = st.selectbox(
                "Target Platform*",
                options=[t.id for t in targets],
                format_func=lambda x: next((f"{t.name} ({t.platform_type.value.upper()})" for t in targets if t.id == x), "Unknown")
            )
            
            strategy = st.selectbox(
                "Migration Strategy*",
                options=[s.value for s in MigrationStrategy],
                format_func=lambda x: f"{x.capitalize()} - {get_strategy_description(x)}",
                help="Select migration strategy from 6Rs framework"
            )
        
        add_vertical_space(1)
        
        # VM Selection
        st.markdown("#### VM Selection")
        
        selection_type = st.radio(
            "Selection Method",
            options=["By Datacenter/Cluster", "By Folder", "By Label", "By VM IDs"],
            horizontal=True
        )
        
        vm_selection_criteria = {}
        
        if selection_type == "By Datacenter/Cluster":
            # Get unique datacenters and clusters
            datacenters = [r[0] for r in session.query(VirtualMachine.datacenter).distinct().all() if r[0]]
            clusters = [r[0] for r in session.query(VirtualMachine.cluster).distinct().all() if r[0]]
            
            col1, col2 = st.columns(2)
            with col1:
                selected_dcs = st.multiselect("Datacenters", options=datacenters)
                if selected_dcs:
                    vm_selection_criteria["datacenters"] = selected_dcs
            
            with col2:
                selected_clusters = st.multiselect("Clusters", options=clusters)
                if selected_clusters:
                    vm_selection_criteria["clusters"] = selected_clusters
        
        elif selection_type == "By Folder":
            folders = [r[0] for r in session.query(VirtualMachine.folder).distinct().all() if r[0]]
            selected_folders = st.multiselect("Folders", options=folders)
            if selected_folders:
                vm_selection_criteria["folders"] = selected_folders
        
        elif selection_type == "By Label":
            # Get all unique labels (key:value pairs)
            labels = session.query(Label).order_by(Label.key, Label.value).all()
            
            if not labels:
                st.warning("⚠️ No labels found. Please create labels first in the Folder Labelling page.")
            else:
                # Group labels by key for better UX
                label_keys = sorted(set(label.key for label in labels))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_keys = st.multiselect(
                        "Label Keys",
                        options=label_keys,
                        help="Select label keys to filter by"
                    )
                
                with col2:
                    if selected_keys:
                        # Show values for selected keys
                        available_values = [f"{label.key}:{label.value}" 
                                          for label in labels 
                                          if label.key in selected_keys]
                        selected_label_pairs = st.multiselect(
                            "Label Values",
                            options=available_values,
                            help="Select specific key:value pairs"
                        )
                        
                        if selected_label_pairs:
                            # Parse key:value pairs
                            label_criteria = []
                            for pair in selected_label_pairs:
                                key, value = pair.split(":", 1)
                                label_criteria.append({"key": key, "value": value})
                            vm_selection_criteria["labels"] = label_criteria
        
        else:  # By VM IDs
            vm_ids_input = st.text_area(
                "VM IDs (comma-separated)",
                placeholder="1,2,3,4,5",
                help="Enter VM IDs separated by commas"
            )
            if vm_ids_input:
                try:
                    vm_ids = [int(x.strip()) for x in vm_ids_input.split(",")]
                    vm_selection_criteria["vm_ids"] = vm_ids
                except:
                    st.error("Invalid VM IDs format")
        
        add_vertical_space(1)
        
        # Migration parameters
        st.markdown("#### Migration Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            duration_days = st.number_input(
                "Expected Duration (days)",
                min_value=1,
                max_value=365,
                value=30,
                help="Overall migration duration including testing"
            )
        
        with col2:
            parallel_migrations = st.number_input(
                "Parallel Migrations",
                min_value=1,
                max_value=50,
                value=5,
                help="Number of VMs migrating simultaneously"
            )
        
        add_vertical_space(1)
        
        # Submit button
        submitted = st.form_submit_button("✨ Create Scenario", type="primary", width='stretch')
        
        if submitted:
            if not name:
                st.error("Please provide a scenario name")
            elif not vm_selection_criteria:
                st.error("Please select at least one VM selection criterion")
            else:
                try:
                    with st.spinner("Creating scenario and calculating estimates..."):
                        scenario = service.create_scenario(
                            name=name,
                            target_id=target_id,
                            vm_selection_criteria=vm_selection_criteria,
                            strategy=MigrationStrategy(strategy),
                            description=description,
                            duration_days=duration_days,
                            parallel_migrations=parallel_migrations
                        )
                    
                    st.success(f"✅ Created scenario: {scenario.name}")
                    st.balloons()
                    
                    # Show summary
                    st.markdown("#### Scenario Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Estimated Duration", f"{scenario.estimated_duration_days:.1f} days")
                    
                    with col2:
                        st.metric("Estimated Cost", f"${scenario.estimated_cost_total:,.2f}")
                    
                    with col3:
                        st.metric("Risk Level", scenario.risk_level)
                    
                except Exception as e:
                    st.error(f"Error creating scenario: {e}")


def render_edit_scenario(service: MigrationScenarioService, session):
    """Render form to edit existing migration scenario."""
    st.subheader("Edit Migration Scenario")
    
    # Get all scenarios
    all_scenarios = session.query(MigrationScenario).all()
    
    if not all_scenarios:
        st.info("No migration scenarios available. Create your first scenario in the 'Create Scenario' tab.")
        return
    
    # Select scenario to edit
    selected_scenario_id = st.selectbox(
        "Select scenario to edit",
        options=[s.id for s in all_scenarios],
        format_func=lambda x: next((f"{s.name} ({s.target.name})" for s in all_scenarios if s.id == x), "Unknown"),
        key="edit_scenario_select"
    )
    
    if not selected_scenario_id:
        return
    
    scenario = session.query(MigrationScenario).get(selected_scenario_id)
    targets = service.get_active_targets()
    
    with st.form("edit_scenario_form"):
        # Basic information
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Scenario Name*", value=scenario.name)
            description = st.text_area("Description", value=scenario.description or "")
        
        with col2:
            target_id = st.selectbox(
                "Target Platform*",
                options=[t.id for t in targets],
                format_func=lambda x: next((f"{t.name} ({t.platform_type.value.upper()})" for t in targets if t.id == x), "Unknown"),
                index=[t.id for t in targets].index(scenario.target_id) if scenario.target_id in [t.id for t in targets] else 0
            )
            
            strategy = st.selectbox(
                "Migration Strategy*",
                options=[s.value for s in MigrationStrategy],
                format_func=lambda x: f"{x.capitalize()} - {get_strategy_description(x)}",
                index=[s.value for s in MigrationStrategy].index(scenario.strategy.value),
                help="Select migration strategy from 6Rs framework"
            )
        
        add_vertical_space(1)
        
        # Display current VM selection criteria (read-only)
        st.markdown("#### Current VM Selection Criteria")
        st.info("📝 VM selection criteria cannot be edited. Create a new scenario to change VM selection.")
        
        if scenario.vm_selection_criteria:
            criteria_text = []
            if "datacenters" in scenario.vm_selection_criteria:
                criteria_text.append(f"Datacenters: {', '.join(scenario.vm_selection_criteria['datacenters'])}")
            if "clusters" in scenario.vm_selection_criteria:
                criteria_text.append(f"Clusters: {', '.join(scenario.vm_selection_criteria['clusters'])}")
            if "folders" in scenario.vm_selection_criteria:
                criteria_text.append(f"Folders: {', '.join(scenario.vm_selection_criteria['folders'])}")
            if "labels" in scenario.vm_selection_criteria:
                labels = [f"{l['key']}:{l['value']}" for l in scenario.vm_selection_criteria['labels']]
                criteria_text.append(f"Labels: {', '.join(labels)}")
            if "vm_ids" in scenario.vm_selection_criteria:
                criteria_text.append(f"VM IDs: {', '.join(map(str, scenario.vm_selection_criteria['vm_ids']))}")
            
            if criteria_text:
                for text in criteria_text:
                    st.text(text)
        
        add_vertical_space(1)
        
        # Current estimates
        st.markdown("#### Current Estimates")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duration", f"{scenario.estimated_duration_days:.1f} days")
        with col2:
            st.metric("Total Cost", f"${scenario.estimated_cost_total:,.2f}")
        with col3:
            st.metric("Risk Level", scenario.risk_level)
        with col4:
            st.metric("Score", f"{scenario.recommendation_score:.0f}/100")
        
        add_vertical_space(1)
        
        # Recalculate option
        recalculate = st.checkbox(
            "Recalculate estimates after update",
            value=True,
            help="Recalculates duration, cost, and risk based on new target/strategy"
        )
        
        add_vertical_space(1)
        
        # Submit button
        submitted = st.form_submit_button("✏️ Update Scenario", type="primary", width='stretch')
        
        if submitted:
            if not name:
                st.error("Please provide a scenario name")
            else:
                try:
                    # Update basic fields
                    scenario.name = name
                    scenario.description = description
                    scenario.target_id = target_id
                    scenario.strategy = MigrationStrategy(strategy)
                    
                    # Recalculate if requested
                    if recalculate:
                        with st.spinner("Recalculating estimates..."):
                            # Get target
                            target = session.query(MigrationTarget).get(target_id)
                            
                            # Get VMs based on existing criteria
                            vms = service._get_vms_by_criteria(scenario.vm_selection_criteria)
                            
                            if vms:
                                # Recalculate estimates
                                cost_breakdown = service.calculate_migration_cost(vms, target, 30, MigrationStrategy(strategy))
                                duration = service.calculate_migration_duration(vms, target, 5, MigrationStrategy(strategy))
                                risk_level, risk_factors = service.assess_risk_level(vms, target, MigrationStrategy(strategy))
                                recommendation_score = service.calculate_recommendation_score(
                                    cost_breakdown, duration, risk_level, target
                                )
                                
                                # Update scenario with new calculations
                                scenario.estimated_duration_days = duration["total_days"]
                                scenario.estimated_cost_total = cost_breakdown["total"]
                                scenario.estimated_cost_breakdown = cost_breakdown
                                scenario.risk_level = risk_level
                                scenario.risk_factors = risk_factors
                                scenario.recommendation_score = recommendation_score
                                scenario.recommended = (recommendation_score >= 70)
                    
                    session.commit()
                    st.success(f"✅ Updated scenario: {scenario.name}")
                    # Force refresh
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating scenario: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    session.rollback()


def render_compare_scenarios(service: MigrationScenarioService):
    """Render scenario comparison view."""
    st.subheader("Compare Migration Scenarios")
    
    # Get all scenarios
    scenarios = service.session.query(MigrationScenario).all()
    
    if len(scenarios) < 2:
        st.info("Create at least 2 scenarios to compare them.")
        return
    
    # Select scenarios to compare
    selected_ids = st.multiselect(
        "Select scenarios to compare",
        options=[s.id for s in scenarios],
        format_func=lambda x: next((s.name for s in scenarios if s.id == x), "Unknown"),
        default=[s.id for s in scenarios[:min(3, len(scenarios))]]  # Default to first 3
    )
    
    if len(selected_ids) < 2:
        st.warning("Select at least 2 scenarios to compare")
        return
    
    add_vertical_space(1)
    
    # Comparison table
    comparison_df = service.compare_scenarios(selected_ids)
    st.dataframe(comparison_df, width='stretch', hide_index=True)
    
    add_vertical_space(2)
    
    # Visual comparisons
    col1, col2 = st.columns(2)
    
    with col1:
        # Cost comparison
        fig_cost = px.bar(
            comparison_df,
            x="Scenario",
            y="Total Cost ($)",
            color="Platform",
            title="Cost Comparison"
        )
        st.plotly_chart(fig_cost, width='stretch')
    
    with col2:
        # Duration comparison
        fig_duration = px.bar(
            comparison_df,
            x="Scenario",
            y="Duration (days)",
            color="Risk Level",
            title="Duration Comparison"
        )
        st.plotly_chart(fig_duration, width='stretch')
    
    add_vertical_space(2)
    
    # Recommendation score radar chart
    if len(selected_ids) <= 5:  # Only show radar for <=5 scenarios
        fig_radar = go.Figure()
        
        for _, row in comparison_df.iterrows():
            fig_radar.add_trace(go.Scatterpolar(
                r=[row["Score"], 100 - row["Duration (days)"], 100 - (row["Total Cost ($)"] / 1000)],
                theta=["Score", "Speed", "Cost"],
                fill='toself',
                name=row["Scenario"]
            ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Multi-Criteria Comparison"
        )
        st.plotly_chart(fig_radar, width='stretch')


def render_migration_waves(service: MigrationScenarioService, session):
    """Render migration waves view for phased migrations."""
    st.subheader("Migration Waves - Phased Execution")
    
    st.markdown("""
    Migration waves allow you to group VMs into phased migration batches for organized, 
    low-risk migration execution.
    """)
    
    add_vertical_space(1)
    
    # Get all scenarios
    scenarios = session.query(MigrationScenario).all()
    
    if not scenarios:
        st.info("No migration scenarios available. Create a scenario first.")
        return
    
    # Select scenario
    selected_scenario_id = st.selectbox(
        "Select Scenario",
        options=[s.id for s in scenarios],
        format_func=lambda x: next((f"{s.name} ({s.vm_count or 0} VMs)" for s in scenarios if s.id == x), "Unknown")
    )
    
    scenario = session.query(MigrationScenario).get(selected_scenario_id)
    
    if not scenario:
        return
    
    add_vertical_space(1)
    
    # Show scenario info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("VMs", scenario.vm_count or 0)
    with col2:
        st.metric("Target", scenario.target.name)
    with col3:
        st.metric("Strategy", scenario.strategy.value.capitalize())
    with col4:
        st.metric("Duration", f"{scenario.estimated_duration_days:.1f} days")
    
    add_vertical_space(2)
    
    # Check for existing waves
    existing_waves = session.query(MigrationWave).filter(
        MigrationWave.scenario_id == scenario.id
    ).order_by(MigrationWave.wave_number).all()
    
    if existing_waves:
        st.success(f"✅ {len(existing_waves)} wave(s) generated for this scenario")
        
        add_vertical_space(1)
        
        # Display waves
        st.markdown("### Migration Waves")
        
        waves_data = []
        for wave in existing_waves:
            waves_data.append({
                "Wave": f"Wave {wave.wave_number}",
                "Name": wave.wave_name or f"Wave {wave.wave_number}",
                "VMs": len(wave.vm_ids or []),
                "Status": wave.status.upper(),
                "Duration (est)": f"{wave.duration_hours:.1f}h" if wave.duration_hours else "TBD",
                "Start Date": wave.start_date or "Not scheduled",
                "End Date": wave.end_date or "Not scheduled"
            })
        
        df_waves = pd.DataFrame(waves_data)
        st.dataframe(df_waves, width='stretch', hide_index=True)
        
        add_vertical_space(2)
        
        # Wave details
        st.markdown("### Wave Details")
        
        selected_wave_num = st.selectbox(
            "Select wave to view details",
            options=[w.wave_number for w in existing_waves],
            format_func=lambda x: f"Wave {x}"
        )
        
        selected_wave = next((w for w in existing_waves if w.wave_number == selected_wave_num), None)
        
        if selected_wave:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Wave {selected_wave.wave_number}**: {selected_wave.wave_name}")
                st.write(f"**Status**: {selected_wave.status.upper()}")
                st.write(f"**VMs**: {len(selected_wave.vm_ids or [])}")
            
            with col2:
                if selected_wave.start_date:
                    st.write(f"**Start**: {selected_wave.start_date}")
                if selected_wave.end_date:
                    st.write(f"**End**: {selected_wave.end_date}")
                if selected_wave.duration_hours:
                    st.write(f"**Duration**: {selected_wave.duration_hours:.1f} hours")
            
            with col3:
                if selected_wave.depends_on_wave_ids:
                    st.write(f"**Dependencies**: Wave(s) {', '.join(map(str, selected_wave.depends_on_wave_ids))}")
                else:
                    st.write("**Dependencies**: None")
            
            # Show VM IDs if available
            if selected_wave.vm_ids:
                with st.expander(f"📋 VM List ({len(selected_wave.vm_ids)} VMs)"):
                    vm_ids_str = ", ".join(map(str, selected_wave.vm_ids[:50]))
                    if len(selected_wave.vm_ids) > 50:
                        vm_ids_str += f"... and {len(selected_wave.vm_ids) - 50} more"
                    st.text(vm_ids_str)
        
        add_vertical_space(2)
        
        # Delete waves button
        if st.button("🗑️ Delete All Waves", type="secondary"):
            if st.session_state.get(f"confirm_delete_waves_{scenario.id}"):
                for wave in existing_waves:
                    session.delete(wave)
                session.commit()
                st.success("✅ Deleted all waves")
                st.session_state[f"confirm_delete_waves_{scenario.id}"] = False
                st.rerun()
            else:
                st.session_state[f"confirm_delete_waves_{scenario.id}"] = True
                st.warning("⚠️ Click again to confirm deletion of all waves")
    
    else:
        st.info("No migration waves generated yet for this scenario.")
        
        add_vertical_space(2)
        
        # Generate waves form
        st.markdown("### Generate Migration Waves")
        
        with st.form("generate_waves_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                wave_size = st.number_input(
                    "VMs per Wave",
                    min_value=1,
                    max_value=100,
                    value=10,
                    help="Number of VMs to migrate in each wave"
                )
            
            with col2:
                wave_strategy = st.selectbox(
                    "Wave Strategy",
                    options=["size_based", "random"],
                    format_func=lambda x: "Size-based (smallest first)" if x == "size_based" else "Random",
                    help="How to group VMs into waves"
                )
            
            add_vertical_space(1)
            
            submitted = st.form_submit_button("🌊 Generate Waves", type="primary", use_container_width=True)
            
            if submitted:
                try:
                    with st.spinner("Generating migration waves..."):
                        waves = service.generate_migration_waves(
                            scenario_id=scenario.id,
                            wave_size=wave_size,
                            strategy=wave_strategy
                        )
                    
                    st.success(f"✅ Generated {len(waves)} migration wave(s)!")
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating waves: {e}")
                    import traceback
                    st.code(traceback.format_exc())


def get_strategy_description(strategy: str) -> str:
    """Get short description for migration strategy."""
    descriptions = {
        "rehost": "Lift and shift",
        "replatform": "Lift, tinker, and shift",
        "refactor": "Re-architect for cloud",
        "repurchase": "Move to SaaS",
        "retire": "Decommission",
        "retain": "Keep as-is"
    }
    return descriptions.get(strategy, "")
