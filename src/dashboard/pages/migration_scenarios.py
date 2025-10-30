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

from models import VirtualMachine
from models.migration_target import MigrationTarget, MigrationScenario, MigrationStrategy
from services.migration_scenarios import MigrationScenarioService


def render(db_url: str):
    """Render the migration scenarios page."""
    colored_header(
        label="🔄 Migration Scenarios",
        description="Create and compare migration scenarios across multiple targets",
        color_name="green-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
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
        tab1, tab2, tab3 = st.tabs(["\ud83d\udccb Scenarios List", "➕ Create Scenario", "📊 Compare Scenarios"])
        
        with tab1:
            render_scenarios_list(service, session)
        
        with tab2:
            render_create_scenario(service, session)
        
        with tab3:
            render_compare_scenarios(service)
        
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
    
    # Create DataFrame
    scenarios_data = []
    for scenario in scenarios:
        scenarios_data.append({
            "ID": scenario.id,
            "Name": scenario.name,
            "Target": scenario.target.name,
            "Platform": scenario.target.platform_type.value.upper(),
            "Strategy": scenario.strategy.value.capitalize(),
            "Duration (days)": f"{scenario.estimated_duration_days:.1f}",
            "Cost ($)": f"${scenario.estimated_cost_total:,.0f}",
            "Risk": scenario.risk_level,
            "Score": f"{scenario.recommendation_score:.0f}/100",
            "Recommended": "✅" if scenario.recommended else "❌"
        })
    
    df = pd.DataFrame(scenarios_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
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
        
        # Cost breakdown
        if scenario.estimated_cost_breakdown:
            st.markdown("#### Cost Breakdown")
            cost_df = pd.DataFrame([scenario.estimated_cost_breakdown]).T
            cost_df.columns = ["Amount ($)"]
            cost_df.index.name = "Category"
            
            fig = px.pie(
                values=cost_df["Amount ($)"],
                names=cost_df.index,
                title="Cost Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk factors
        if scenario.risk_factors:
            st.markdown("#### Risk Factors")
            for factor in scenario.risk_factors:
                st.warning(f"⚠️ {factor.replace('_', ' ').title()}")
        
        add_vertical_space(1)
        
        # Actions
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("🗑️ Delete", key=f"delete_{scenario.id}", type="secondary"):
                if st.session_state.get(f"confirm_delete_scenario_{scenario.id}"):
                    session.delete(scenario)
                    session.commit()
                    st.success(f"Deleted scenario: {scenario.name}")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_scenario_{scenario.id}"] = True
                    st.warning("Click again to confirm deletion")


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
            options=["By Datacenter/Cluster", "By Folder", "By VM IDs"],
            horizontal=True
        )
        
        vm_selection_criteria = {}
        
        if selection_type == "By Datacenter/Cluster":
            # Get unique datacenters and clusters
            datacenters = [r[0] for r in session.query(VirtualMachine.Datacenter).distinct().all() if r[0]]
            clusters = [r[0] for r in session.query(VirtualMachine.Cluster).distinct().all() if r[0]]
            
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
            folders = [r[0] for r in session.query(VirtualMachine.Folder).distinct().all() if r[0]]
            selected_folders = st.multiselect("Folders", options=folders)
            if selected_folders:
                vm_selection_criteria["folders"] = selected_folders
        
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
        submitted = st.form_submit_button("✨ Create Scenario", type="primary", use_container_width=True)
        
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
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
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
        st.plotly_chart(fig_cost, use_container_width=True)
    
    with col2:
        # Duration comparison
        fig_duration = px.bar(
            comparison_df,
            x="Scenario",
            y="Duration (days)",
            color="Risk Level",
            title="Duration Comparison"
        )
        st.plotly_chart(fig_duration, use_container_width=True)
    
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
        st.plotly_chart(fig_radar, use_container_width=True)


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
