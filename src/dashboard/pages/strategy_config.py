"""Strategy Configuration page - Configure parameters for each migration strategy."""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import MigrationStrategyConfig, MigrationStrategy, Base


def render(db_url: str):
    """Render the strategy configuration page."""
    colored_header(
        label="⚙️ Strategy Configuration",
        description="Configure cost and labor parameters for each migration strategy",
        color_name="orange-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        # Ensure tables exist
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Initialize default configurations if they don't exist
        initialize_default_configs(session)
        
        # Get all strategy configs
        configs = session.query(MigrationStrategyConfig).all()
        
        # Overview table
        st.subheader("Current Strategy Configurations")
        
        config_data = []
        for config in configs:
            config_data.append({
                "Strategy": config.strategy.value.upper(),
                "Hours/VM": config.hours_per_vm,
                "Labor Rate ($/hr)": f"${config.labor_rate_per_hour:.2f}",
                "Compute": f"{config.compute_multiplier * 100:.0f}%",
                "Memory": f"{config.memory_multiplier * 100:.0f}%",
                "Storage": f"{config.storage_multiplier * 100:.0f}%"
            })
        
        df = pd.DataFrame(config_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        add_vertical_space(2)
        
        # Edit configuration
        st.subheader("Edit Strategy Configuration")
        
        # Select strategy to edit
        selected_strategy = st.selectbox(
            "Select strategy to configure",
            options=[s.value for s in MigrationStrategy],
            format_func=lambda x: f"{x.upper()} - {get_strategy_description(x)}"
        )
        
        config = session.query(MigrationStrategyConfig).filter(
            MigrationStrategyConfig.strategy == MigrationStrategy(selected_strategy)
        ).first()
        
        if config:
            with st.form(f"edit_strategy_{selected_strategy}"):
                st.markdown(f"#### {selected_strategy.upper()} Configuration")
                
                # Description
                description = st.text_area(
                    "Description",
                    value=config.description or "",
                    help="Brief description of this migration strategy"
                )
                
                add_vertical_space(1)
                
                # Labor configuration
                st.markdown("**Labor Configuration**")
                col1, col2 = st.columns(2)
                
                with col1:
                    hours_per_vm = st.number_input(
                        "Hours per VM",
                        min_value=0.0,
                        max_value=200.0,
                        value=float(config.hours_per_vm),
                        step=0.5,
                        help="Labor hours required per VM for this strategy"
                    )
                
                with col2:
                    labor_rate = st.number_input(
                        "Labor Rate ($/hour)",
                        min_value=0.0,
                        max_value=500.0,
                        value=float(config.labor_rate_per_hour),
                        step=10.0,
                        help="Hourly rate for migration labor"
                    )
                
                add_vertical_space(1)
                
                # Infrastructure multipliers
                st.markdown("**Infrastructure Cost Multipliers**")
                st.caption("Multipliers adjust base infrastructure costs. 1.0 = 100%, 0.9 = 90% (10% reduction)")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    compute_mult = st.slider(
                        "Compute Multiplier",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(config.compute_multiplier),
                        step=0.1,
                        format="%.1f",
                        help="Multiplier for compute costs (vCPU)"
                    )
                    
                    memory_mult = st.slider(
                        "Memory Multiplier",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(config.memory_multiplier),
                        step=0.1,
                        format="%.1f",
                        help="Multiplier for memory costs"
                    )
                
                with col2:
                    storage_mult = st.slider(
                        "Storage Multiplier",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(config.storage_multiplier),
                        step=0.1,
                        format="%.1f",
                        help="Multiplier for storage costs"
                    )
                    
                    network_mult = st.slider(
                        "Network Multiplier",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(config.network_multiplier),
                        step=0.1,
                        format="%.1f",
                        help="Multiplier for network transfer costs"
                    )
                
                add_vertical_space(1)
                
                # Additional costs (for REPURCHASE)
                if selected_strategy == "repurchase":
                    st.markdown("**SaaS Costs**")
                    saas_cost = st.number_input(
                        "SaaS Cost per VM per Month ($)",
                        min_value=0.0,
                        max_value=10000.0,
                        value=float(config.saas_cost_per_vm_per_month),
                        step=10.0,
                        help="Monthly subscription cost per VM for SaaS solution"
                    )
                else:
                    saas_cost = config.saas_cost_per_vm_per_month
                
                add_vertical_space(1)
                
                # Notes
                notes = st.text_area(
                    "Notes",
                    value=config.notes or "",
                    help="Additional notes or considerations for this strategy"
                )
                
                add_vertical_space(1)
                
                # Submit button
                submitted = st.form_submit_button("💾 Save Configuration", type="primary", width='stretch')
                
                if submitted:
                    try:
                        # Update configuration
                        config.description = description
                        config.hours_per_vm = hours_per_vm
                        config.labor_rate_per_hour = labor_rate
                        config.compute_multiplier = compute_mult
                        config.memory_multiplier = memory_mult
                        config.storage_multiplier = storage_mult
                        config.network_multiplier = network_mult
                        config.saas_cost_per_vm_per_month = saas_cost
                        config.notes = notes
                        
                        session.commit()
                        st.success(f"✅ Updated configuration for {selected_strategy.upper()}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating configuration: {e}")
                        session.rollback()
        
        session.close()
        
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())


def initialize_default_configs(session):
    """Initialize default strategy configurations if they don't exist."""
    defaults = {
        MigrationStrategy.RETAIN: {
            "hours_per_vm": 0.5,
            "labor_rate_per_hour": 150,
            "compute_multiplier": 0.0,
            "memory_multiplier": 0.0,
            "storage_multiplier": 0.0,
            "network_multiplier": 0.0,
            "description": "Keep as-is - minimal assessment only"
        },
        MigrationStrategy.RETIRE: {
            "hours_per_vm": 1.0,
            "labor_rate_per_hour": 150,
            "compute_multiplier": 0.0,
            "memory_multiplier": 0.0,
            "storage_multiplier": 0.0,
            "network_multiplier": 0.0,
            "description": "Decommission - backup and shutdown"
        },
        MigrationStrategy.REHOST: {
            "hours_per_vm": 4.0,
            "labor_rate_per_hour": 150,
            "compute_multiplier": 1.0,
            "memory_multiplier": 1.0,
            "storage_multiplier": 1.0,
            "network_multiplier": 1.0,
            "description": "Lift and shift - direct migration"
        },
        MigrationStrategy.REPLATFORM: {
            "hours_per_vm": 8.0,
            "labor_rate_per_hour": 150,
            "compute_multiplier": 0.9,
            "memory_multiplier": 0.9,
            "storage_multiplier": 0.85,
            "network_multiplier": 1.0,
            "description": "Lift, tinker, shift - with optimization"
        },
        MigrationStrategy.REFACTOR: {
            "hours_per_vm": 40.0,
            "labor_rate_per_hour": 200,
            "compute_multiplier": 0.6,
            "memory_multiplier": 0.7,
            "storage_multiplier": 0.5,
            "network_multiplier": 0.1,
            "description": "Re-architect - cloud-native development"
        },
        MigrationStrategy.REPURCHASE: {
            "hours_per_vm": 6.0,
            "labor_rate_per_hour": 150,
            "compute_multiplier": 0.0,
            "memory_multiplier": 0.0,
            "storage_multiplier": 0.0,
            "network_multiplier": 0.0,
            "saas_cost_per_vm_per_month": 100.0,
            "description": "Move to SaaS - subscription model"
        }
    }
    
    for strategy, config_values in defaults.items():
        existing = session.query(MigrationStrategyConfig).filter(
            MigrationStrategyConfig.strategy == strategy
        ).first()
        
        if not existing:
            config = MigrationStrategyConfig(
                strategy=strategy,
                **config_values
            )
            session.add(config)
    
    session.commit()


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
