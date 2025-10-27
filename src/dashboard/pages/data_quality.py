"""Data Quality Report page - Unique values and completeness analysis."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func, inspect
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.models import VirtualMachine


def render(db_url: str):
    """Render the data quality report page."""
    st.markdown('<h1 class="main-header">📋 Data Quality Report</h1>', unsafe_allow_html=True)
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        inspector = inspect(engine)
        
        # Get total VM count
        total_vms = session.query(func.count(VirtualMachine.id)).scalar()
        
        if total_vms == 0:
            st.warning("⚠️ No data found in database. Please load data first.")
            return
        
        st.info(f"Analyzing {total_vms:,} virtual machines")
        
        # Category selection
        categories = {
            "All": None,
            "Basic Info": ["vm", "powerstate", "template", "config_status", "dns_name", "connection_state", "guest_state"],
            "Resources": ["cpus", "memory", "nics", "disks", "provisioned_mib", "in_use_mib"],
            "Network": ["primary_ip_address", "network_1", "network_2", "network_3", "network_4"],
            "Infrastructure": ["datacenter", "cluster", "host", "resource_pool", "folder"],
            "Operating System": ["os_config", "os_vmware_tools"],
            "Hardware": ["firmware", "hw_version", "hw_upgrade_status"],
            "Custom Fields": ["code_ccx", "vm_nbu", "vm_orchid", "env"],
            "Identifiers": ["vm_id", "vm_uuid"],
        }
        
        selected_category = st.selectbox("Select Category", list(categories.keys()))
        
        st.divider()
        
        # Get columns to analyze
        if categories[selected_category]:
            columns_to_analyze = categories[selected_category]
        else:
            # Get all columns except id and imported_at
            all_columns = [col["name"] for col in inspector.get_columns("virtual_machines")]
            columns_to_analyze = [c for c in all_columns if c not in ["id", "imported_at"]]
        
        # Analysis mode
        col1, col2 = st.columns(2)
        with col1:
            analysis_mode = st.radio(
                "Analysis Type",
                ["Summary", "Detailed"],
                horizontal=True
            )
        with col2:
            show_charts = st.checkbox("Show Charts", value=True)
        
        st.divider()
        
        if analysis_mode == "Summary":
            _render_summary_report(session, columns_to_analyze, total_vms, show_charts)
        else:
            _render_detailed_report(session, columns_to_analyze, total_vms)
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
    finally:
        session.close()


def _render_summary_report(session, columns, total_vms, show_charts):
    """Render summary report with completeness metrics."""
    st.subheader("Data Completeness Summary")
    
    report_data = []
    
    for col_name in columns:
        try:
            col_attr = getattr(VirtualMachine, col_name)
            
            # Count non-null values
            non_null_count = session.query(func.count(col_attr)).filter(
                col_attr.isnot(None)
            ).scalar() or 0
            
            # Count distinct values
            distinct_count = session.query(func.count(func.distinct(col_attr))).filter(
                col_attr.isnot(None)
            ).scalar() or 0
            
            # Calculate metrics
            completeness = (non_null_count / total_vms * 100) if total_vms > 0 else 0
            null_count = total_vms - non_null_count
            
            report_data.append({
                'Column': col_name,
                'Non-Null Count': non_null_count,
                'Null Count': null_count,
                'Completeness (%)': round(completeness, 1),
                'Unique Values': distinct_count,
                'Cardinality': round(distinct_count / non_null_count * 100, 1) if non_null_count > 0 else 0
            })
        except Exception as e:
            st.warning(f"Could not analyze column '{col_name}': {e}")
    
    df_report = pd.DataFrame(report_data)
    
    if df_report.empty:
        st.warning("No data to display")
        return
    
    # Sort by completeness
    df_report = df_report.sort_values('Completeness (%)', ascending=False)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_completeness = df_report['Completeness (%)'].mean()
        st.metric("Average Completeness", f"{avg_completeness:.1f}%")
    with col2:
        complete_cols = len(df_report[df_report['Completeness (%)'] == 100])
        st.metric("100% Complete Columns", complete_cols)
    with col3:
        incomplete_cols = len(df_report[df_report['Completeness (%)'] < 50])
        st.metric("< 50% Complete Columns", incomplete_cols)
    
    st.divider()
    
    # Export button
    csv_data = df_report.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Export Report CSV",
        data=csv_data,
        file_name="data_quality_report.csv",
        mime="text/csv"
    )
    
    # Display table with color coding
    def color_completeness(val):
        if val >= 90:
            return 'background-color: #d4edda'
        elif val >= 70:
            return 'background-color: #fff3cd'
        elif val >= 50:
            return 'background-color: #f8d7da'
        else:
            return 'background-color: #f5c6cb'
    
    styled_df = df_report.style.map(
        color_completeness,
        subset=['Completeness (%)']
    )
    
    st.dataframe(styled_df, width="stretch", hide_index=True)
    
    if show_charts:
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Completeness bar chart
            fig = px.bar(
                df_report.head(20),
                x='Completeness (%)',
                y='Column',
                orientation='h',
                title='Data Completeness by Column (Top 20)',
                color='Completeness (%)',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Unique values distribution
            fig = px.scatter(
                df_report,
                x='Unique Values',
                y='Completeness (%)',
                size='Non-Null Count',
                hover_data=['Column'],
                title='Unique Values vs Completeness',
                color='Cardinality',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                xaxis_type='log',
                xaxis_title='Unique Values (log scale)'
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_detailed_report(session, columns, total_vms):
    """Render detailed report with actual unique values."""
    st.subheader("Detailed Unique Values Report")
    
    # Column selector for detailed view
    selected_column = st.selectbox(
        "Select column to analyze:",
        columns
    )
    
    if not selected_column:
        return
    
    st.divider()
    
    try:
        col_attr = getattr(VirtualMachine, selected_column)
        
        # Get statistics
        non_null_count = session.query(func.count(col_attr)).filter(
            col_attr.isnot(None)
        ).scalar() or 0
        
        null_count = total_vms - non_null_count
        completeness = (non_null_count / total_vms * 100) if total_vms > 0 else 0
        
        # Display column stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Non-Null Values", f"{non_null_count:,}")
        with col2:
            st.metric("Null Values", f"{null_count:,}")
        with col3:
            st.metric("Completeness", f"{completeness:.1f}%")
        with col4:
            distinct_count = session.query(func.count(func.distinct(col_attr))).filter(
                col_attr.isnot(None)
            ).scalar() or 0
            st.metric("Unique Values", f"{distinct_count:,}")
        
        st.divider()
        
        # Get unique values with counts
        st.subheader(f"Unique Values in '{selected_column}'")
        
        value_counts = session.query(
            col_attr,
            func.count(VirtualMachine.id).label('count')
        ).filter(
            col_attr.isnot(None)
        ).group_by(col_attr).order_by(func.count(VirtualMachine.id).desc()).all()
        
        if not value_counts:
            st.info("No non-null values found for this column")
            return
        
        # Create dataframe
        df_values = pd.DataFrame(value_counts, columns=['Value', 'Count'])
        df_values['Percentage'] = (df_values['Count'] / total_vms * 100).round(2)
        
        # Show top values
        limit = st.slider("Number of values to display", 10, min(100, len(df_values)), 25)
        df_display = df_values.head(limit)
        
        # Export button
        csv_data = df_values.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"⬇️ Export All {len(df_values)} Values CSV",
            data=csv_data,
            file_name=f"unique_values_{selected_column}.csv",
            mime="text/csv"
        )
        
        # Display table
        st.dataframe(
            df_display.style.format({
                'Count': '{:,}',
                'Percentage': '{:.2f}%'
            }),
            width="stretch",
            hide_index=True
        )
        
        st.divider()
        
        # Visualization
        viz_type = st.radio("Visualization", ["Bar Chart", "Pie Chart", "Treemap"], horizontal=True)
        
        if viz_type == "Bar Chart":
            fig = px.bar(
                df_display,
                x='Count',
                y='Value',
                orientation='h',
                title=f'Top {limit} Values Distribution',
                text='Count',
                color='Count',
                color_continuous_scale='Blues'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Pie Chart":
            fig = px.pie(
                df_display,
                values='Count',
                names='Value',
                title=f'Top {limit} Values Distribution'
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        else:  # Treemap
            fig = px.treemap(
                df_display,
                path=['Value'],
                values='Count',
                title=f'Top {limit} Values Distribution',
                color='Count',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show null values if any
        if null_count > 0:
            with st.expander(f"⚠️ {null_count:,} VMs with NULL values"):
                st.write(f"**{completeness:.1f}%** of VMs have a value for this field")
                st.write(f"**{100-completeness:.1f}%** of VMs are missing this field")
                
    except Exception as e:
        st.error(f"Error analyzing column: {str(e)}")
