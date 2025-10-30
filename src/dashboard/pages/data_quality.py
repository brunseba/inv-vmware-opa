"""Data Quality Report page - Unique values and completeness analysis."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, func, inspect
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.models import VirtualMachine
from src.dashboard.utils.pagination import PaginationHelper
from src.dashboard.utils.errors import DataValidator


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
            "Labels": "labels",  # Special handling for labels
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
        
        # Check if Labels category is selected
        if selected_category == "Labels":
            _render_label_quality_report(session, total_vms)
        elif analysis_mode == "Summary":
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
            st.plotly_chart(fig, width='stretch')
        
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
            st.plotly_chart(fig, width='stretch')


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
        
        # Count total distinct values
        total_distinct = session.query(func.count(func.distinct(col_attr))).filter(
            col_attr.isnot(None)
        ).scalar() or 0
        
        if total_distinct == 0:
            st.info("No non-null values found for this column")
            return
        
        # Initialize pagination
        pagination = PaginationHelper(
            key_prefix=f"data_quality_detail_{selected_column}",
            default_page_size=25
        )
        
        # Build base query
        base_query = session.query(
            col_attr,
            func.count(VirtualMachine.id).label('count')
        ).filter(
            col_attr.isnot(None)
        ).group_by(col_attr).order_by(func.count(VirtualMachine.id).desc())
        
        # Apply pagination
        paginated_query = pagination.paginate_query(
            base_query,
            total_count=total_distinct
        )
        
        value_counts = paginated_query.all()
        
        # Create dataframe for current page
        df_values = pd.DataFrame(value_counts, columns=['Value', 'Count'])
        df_values['Percentage'] = (df_values['Count'] / total_vms * 100).round(2)
        
        # Show pagination info
        st.info(f"Showing {len(df_values)} of {total_distinct:,} unique values")
        
        limit = len(df_values)
        df_display = df_values
        
        # Export button (exports current page only)
        csv_data = df_values.to_csv(index=False).encode('utf-8')
        col1, col2 = st.columns([3, 1])
        with col1:
            st.download_button(
                label=f"⬇️ Export Current Page ({len(df_values)} values)",
                data=csv_data,
                file_name=f"unique_values_{selected_column}_page_{pagination.current_page}.csv",
                mime="text/csv"
            )
        with col2:
            # Pagination controls
            pagination.show_pagination_controls()
        
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
            st.plotly_chart(fig, width='stretch')
            
        elif viz_type == "Pie Chart":
            fig = px.pie(
                df_display,
                values='Count',
                names='Value',
                title=f'Top {limit} Values Distribution'
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, width='stretch')
            
        else:  # Treemap
            fig = px.treemap(
                df_display,
                path=['Value'],
                values='Count',
                title=f'Top {limit} Values Distribution',
                color='Count',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, width='stretch')
        
        # Show null values if any
        if null_count > 0:
            with st.expander(f"⚠️ {null_count:,} VMs with NULL values"):
                st.write(f"**{completeness:.1f}%** of VMs have a value for this field")
                st.write(f"**{100-completeness:.1f}%** of VMs are missing this field")
                
    except Exception as e:
        st.error(f"Error analyzing column: {str(e)}")


def _render_label_quality_report(session, total_vms):
    """Render label quality and coverage report."""
    from src.models import Label, VMLabel, FolderLabel
    
    st.subheader("🏷️ Label Coverage & Quality")
    
    # Get label statistics
    total_labels = session.query(func.count(Label.id)).scalar() or 0
    total_label_keys = session.query(func.count(func.distinct(Label.key))).scalar() or 0
    
    # Get VM label assignments (direct only, not inherited)
    vms_with_labels = session.query(
        func.count(func.distinct(VMLabel.vm_id))
    ).filter(VMLabel.inherited_from_folder == False).scalar() or 0
    
    # Get folder label assignments
    folders_with_labels = session.query(
        func.count(func.distinct(FolderLabel.folder_path))
    ).scalar() or 0
    
    # Display overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Label Definitions", f"{total_labels:,}")
    with col2:
        st.metric("Unique Label Keys", f"{total_label_keys:,}")
    with col3:
        vm_coverage = (vms_with_labels / total_vms * 100) if total_vms > 0 else 0
        st.metric("VMs with Direct Labels", f"{vms_with_labels:,}", delta=f"{vm_coverage:.1f}%")
    with col4:
        st.metric("Folders with Labels", f"{folders_with_labels:,}")
    
    st.divider()
    
    # Tab view for different analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Label Coverage",
        "🔑 Label Keys Analysis",
        "⚠️ Quality Issues",
        "📈 Coverage by Folder"
    ])
    
    with tab1:
        st.write("**VM Label Coverage:**")
        
        # VMs with no labels at all (direct or inherited)
        vms_no_labels = session.query(
            func.count(VirtualMachine.id)
        ).outerjoin(VMLabel).filter(VMLabel.id.is_(None)).scalar() or 0
        
        # VMs with inherited labels only
        vms_inherited_only = session.query(
            func.count(func.distinct(VMLabel.vm_id))
        ).filter(
            VMLabel.inherited_from_folder == True
        ).scalar() or 0
        
        vms_with_any_labels = total_vms - vms_no_labels
        
        coverage_data = pd.DataFrame({
            'Category': ['With Direct Labels', 'Inherited Only', 'No Labels'],
            'Count': [vms_with_labels, vms_inherited_only - vms_with_labels, vms_no_labels],
            'Percentage': [
                (vms_with_labels / total_vms * 100) if total_vms > 0 else 0,
                ((vms_inherited_only - vms_with_labels) / total_vms * 100) if total_vms > 0 else 0,
                (vms_no_labels / total_vms * 100) if total_vms > 0 else 0
            ]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(
                coverage_data.style.format({
                    'Count': '{:,}',
                    'Percentage': '{:.1f}%'
                }),
                hide_index=True
            )
        
        with col2:
            fig = px.pie(
                coverage_data,
                values='Count',
                names='Category',
                title='VM Label Coverage Distribution',
                color='Category',
                color_discrete_map={
                    'With Direct Labels': '#28a745',
                    'Inherited Only': '#ffc107',
                    'No Labels': '#dc3545'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        if vms_no_labels > 0:
            st.warning(f"⚠️ {vms_no_labels:,} VMs ({vms_no_labels/total_vms*100:.1f}%) have no labels assigned")
    
    with tab2:
        st.write("**Label Key Usage Analysis:**")
        
        # Count total label keys
        total_label_keys_count = session.query(
            func.count(func.distinct(Label.key))
        ).scalar() or 0
        
        if total_label_keys_count == 0:
            st.info("No label keys found")
            return
        
        # Initialize pagination for label keys
        label_key_pagination = PaginationHelper(
            key_prefix="data_quality_label_keys",
            default_page_size=25
        )
        
        # Build base query for label key statistics
        # Note: We need to use a subquery approach for proper pagination with GROUP BY
        from sqlalchemy import select
        
        # Get label key usage statistics with pagination
        base_key_query = session.query(
            Label.key,
            func.count(func.distinct(Label.id)).label('value_count'),
            func.count(func.distinct(VMLabel.vm_id)).label('vm_count')
        ).outerjoin(
            VMLabel, Label.id == VMLabel.label_id
        ).group_by(Label.key).order_by(
            func.count(func.distinct(VMLabel.vm_id)).desc()
        )
        
        # Apply pagination
        paginated_key_query = label_key_pagination.paginate_query(
            base_key_query,
            total_count=total_label_keys_count
        )
        
        key_stats = paginated_key_query.all()
        
        if key_stats:
            df_keys = pd.DataFrame(key_stats, columns=['Label Key', 'Value Count', 'VM Count'])
            df_keys['VM Coverage %'] = (df_keys['VM Count'] / total_vms * 100).round(1)
            
            # Show pagination info
            st.info(f"Showing {len(df_keys)} of {total_label_keys_count:,} label keys")
            
            # Pagination controls
            label_key_pagination.show_pagination_controls()
            
            st.divider()
            
            # Show table
            st.dataframe(
                df_keys.style.format({
                    'Value Count': '{:,}',
                    'VM Count': '{:,}',
                    'VM Coverage %': '{:.1f}%'
                }),
                hide_index=True,
                use_container_width=True
            )
            
            # Export (current page)
            csv_data = df_keys.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"⬇️ Export Current Page ({len(df_keys)} keys)",
                data=csv_data,
                file_name=f"label_keys_analysis_page_{label_key_pagination.current_page}.csv",
                mime="text/csv"
            )
            
            # Visualization
            fig = px.bar(
                df_keys,
                x='VM Count',
                y='Label Key',
                orientation='h',
                title='VM Count by Label Key',
                text='VM Count',
                color='VM Coverage %',
                color_continuous_scale='RdYlGn'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No label keys found")
    
    with tab3:
        st.write("**Data Quality Issues:**")
        
        issues = []
        
        # Check for VMs without required labels (customize based on your requirements)
        if vms_no_labels > 0:
            issues.append({
                'Issue': 'VMs without labels',
                'Count': vms_no_labels,
                'Severity': 'High',
                'Description': f'{vms_no_labels:,} VMs have no labels assigned (direct or inherited)'
            })
        
        # Check for label keys with only one value (might be misconfigured)
        single_value_keys = session.query(
            Label.key
        ).group_by(Label.key).having(
            func.count(func.distinct(Label.value)) == 1
        ).all()
        
        if single_value_keys:
            issues.append({
                'Issue': 'Label keys with single value',
                'Count': len(single_value_keys),
                'Severity': 'Low',
                'Description': f'{len(single_value_keys)} label keys have only one value: {", ".join([k[0] for k in single_value_keys[:5]])}{"..." if len(single_value_keys) > 5 else ""}'
            })
        
        # Check for unused labels
        unused_labels = session.query(
            func.count(Label.id)
        ).outerjoin(
            VMLabel, Label.id == VMLabel.label_id
        ).outerjoin(
            FolderLabel, Label.id == FolderLabel.label_id
        ).filter(
            VMLabel.id.is_(None),
            FolderLabel.id.is_(None)
        ).scalar() or 0
        
        if unused_labels > 0:
            issues.append({
                'Issue': 'Unused label definitions',
                'Count': unused_labels,
                'Severity': 'Medium',
                'Description': f'{unused_labels} label definitions are not assigned to any VM or folder'
            })
        
        # Check for low coverage labels
        low_coverage_keys = session.query(
            Label.key
        ).join(
            VMLabel, Label.id == VMLabel.label_id
        ).group_by(Label.key).having(
            func.count(func.distinct(VMLabel.vm_id)) < total_vms * 0.1  # Less than 10% coverage
        ).all()
        
        if low_coverage_keys and total_vms > 10:
            issues.append({
                'Issue': 'Label keys with low coverage',
                'Count': len(low_coverage_keys),
                'Severity': 'Low',
                'Description': f'{len(low_coverage_keys)} label keys are used by less than 10% of VMs'
            })
        
        if issues:
            df_issues = pd.DataFrame(issues)
            
            # Color code by severity
            def color_severity(val):
                if val == 'High':
                    return 'background-color: #f8d7da'
                elif val == 'Medium':
                    return 'background-color: #fff3cd'
                else:
                    return 'background-color: #d1ecf1'
            
            styled_issues = df_issues.style.map(
                color_severity,
                subset=['Severity']
            )
            
            st.dataframe(styled_issues, hide_index=True, use_container_width=True)
            
            # Summary
            high_issues = len(df_issues[df_issues['Severity'] == 'High'])
            if high_issues > 0:
                st.error(f"⚠️ {high_issues} high-severity issues found")
            else:
                st.success("✅ No high-severity issues found")
        else:
            st.success("✅ No quality issues detected")
    
    with tab4:
        st.write("**Label Coverage by Folder:**")
        
        # Count total folders
        total_folders = session.query(
            func.count(func.distinct(VirtualMachine.folder))
        ).filter(
            VirtualMachine.folder.isnot(None)
        ).scalar() or 0
        
        if total_folders == 0:
            st.info("No folder data available")
            return
        
        # Initialize pagination for folders
        folder_pagination = PaginationHelper(
            key_prefix="data_quality_folder_coverage",
            default_page_size=50
        )
        
        # Build base query for folders
        base_folder_query = session.query(
            VirtualMachine.folder,
            func.count(func.distinct(VirtualMachine.id)).label('total_vms'),
            func.count(func.distinct(VMLabel.vm_id)).label('labeled_vms')
        ).outerjoin(
            VMLabel, VirtualMachine.id == VMLabel.vm_id
        ).filter(
            VirtualMachine.folder.isnot(None)
        ).group_by(
            VirtualMachine.folder
        ).order_by(
            func.count(func.distinct(VirtualMachine.id)).desc()
        )
        
        # Apply pagination
        paginated_folder_query = folder_pagination.paginate_query(
            base_folder_query,
            total_count=total_folders
        )
        
        folder_coverage = paginated_folder_query.all()
        
        if folder_coverage:
            df_folders = pd.DataFrame(
                folder_coverage,
                columns=['Folder', 'Total VMs', 'Labeled VMs']
            )
            df_folders['Coverage %'] = (df_folders['Labeled VMs'] / df_folders['Total VMs'] * 100).round(1)
            df_folders['Unlabeled VMs'] = df_folders['Total VMs'] - df_folders['Labeled VMs']
            
            # Show pagination info
            st.info(f"Showing {len(df_folders)} of {total_folders:,} folders")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                min_vms = st.slider('Minimum VMs in folder', 1, int(df_folders['Total VMs'].max()), 1)
            with col2:
                sort_by = st.selectbox('Sort by', ['Total VMs', 'Coverage %', 'Unlabeled VMs'])
            with col3:
                folder_pagination.show_pagination_controls()
            
            df_filtered = df_folders[df_folders['Total VMs'] >= min_vms].sort_values(
                sort_by,
                ascending=(sort_by != 'Coverage %')
            )
            
            # Display table
            st.dataframe(
                df_filtered.style.format({
                    'Total VMs': '{:,}',
                    'Labeled VMs': '{:,}',
                    'Unlabeled VMs': '{:,}',
                    'Coverage %': '{:.1f}%'
                }),
                hide_index=True,
                use_container_width=True
            )
            
            # Export (current page)
            csv_data = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"⬇️ Export Current Page ({len(df_filtered)} folders)",
                data=csv_data,
                file_name=f"folder_label_coverage_page_{folder_pagination.current_page}.csv",
                mime="text/csv"
            )
            
            # Show folders with 0% coverage
            zero_coverage = df_filtered[df_filtered['Coverage %'] == 0]
            if len(zero_coverage) > 0:
                with st.expander(f"⚠️ {len(zero_coverage)} folders with 0% label coverage"):
                    st.dataframe(zero_coverage[['Folder', 'Total VMs']], hide_index=True)
        else:
            st.info("No folder data available")
