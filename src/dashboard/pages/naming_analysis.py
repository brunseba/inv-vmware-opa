"""VM Naming Analysis page - View and analyze VM naming patterns."""

import streamlit as st
import pandas as pd
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from src.services.naming_convention_service import NamingConventionService
from src.models import VMNamingAnalysis, VirtualMachine


def render(db_url: str):
    """Render the VM naming analysis page."""
    colored_header(
        label="📊 VM Naming Analysis",
        description="View and analyze parsed VM names by convention",
        color_name="blue-70",
    )

    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        service = NamingConventionService(session)

        # Get all conventions
        conventions = service.list_conventions(active_only=True)

        if not conventions:
            st.warning("⚠️ No active naming conventions found. Create one in the Convention Manager.")
            if st.button("➕ Go to Convention Manager"):
                st.session_state["current_page"] = "Naming Convention Manager"
                st.rerun()
            return

        add_vertical_space(1)

        # Convention selector with multi-select option
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Toggle between single and multi-convention mode
            analysis_mode = st.radio(
                "Analysis Mode",
                options=["Single Convention", "Multi-Convention"],
                horizontal=True,
                help="Choose single or multi-convention analysis"
            )

        if analysis_mode == "Single Convention":
            with col2:
                convention_names = {f"{c.name} ({c.pattern})": c.id for c in conventions}
                selected_name = st.selectbox(
                    "Select Convention",
                    options=list(convention_names.keys()),
                    help="Choose a convention to view analysis results",
                    label_visibility="collapsed"
                )
                selected_convention_id = convention_names[selected_name]

            with col3:
                if st.button("🔄 Refresh", use_container_width=True):
                    with st.spinner("Re-analyzing VMs..."):
                        stats = service.analyze_vm_inventory(selected_convention_id)
                        st.success(f"✅ Analyzed {stats['total']} VMs")
                        st.rerun()

            # Get selected convention
            convention = service.get_convention(selected_convention_id)
            selected_conventions = [convention]
        else:
            # Multi-convention selection
            with col2:
                st.caption("Select conventions below")
            
            with col3:
                if st.button("🔄 Refresh All", use_container_width=True):
                    selected_conv_ids = st.session_state.get('multi_conv_selected', [])
                    if selected_conv_ids:
                        with st.spinner("Re-analyzing VMs with multiple conventions..."):
                            stats = service.analyze_vm_inventory_multi(
                                convention_ids=selected_conv_ids,
                                stop_on_first_match=False
                            )
                            st.success(f"✅ Analyzed {stats['total']} VMs with {len(selected_conv_ids)} conventions")
                            st.rerun()
            
            add_vertical_space(1)
            
            # Multi-select conventions
            selected_conventions = []
            st.markdown("**Select Conventions:**")
            cols_per_row = 3
            for i in range(0, len(conventions), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(conventions):
                        conv = conventions[idx]
                        with col:
                            if st.checkbox(
                                f"{conv.name}",
                                key=f"analysis_multi_select_{conv.id}",
                                help=f"Pattern: {conv.pattern}"
                            ):
                                selected_conventions.append(conv)
            
            # Store selected IDs in session state for refresh
            st.session_state['multi_conv_selected'] = [c.id for c in selected_conventions]
            
            if not selected_conventions:
                st.warning("⚠️ Please select at least one convention to view statistics")
                return
            
            convention = selected_conventions[0]  # Use first for compatibility

        add_vertical_space(1)

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Analysis Results", "📈 Statistics", "📤 Export"])

        # ========== TAB 1: Analysis Results ==========
        with tab1:
            render_analysis_results(service, session, convention)

        # ========== TAB 2: Statistics ==========
        with tab2:
            if analysis_mode == "Multi-Convention":
                render_multi_convention_statistics(service, session, selected_conventions)
            else:
                render_statistics(service, session, convention)

        # ========== TAB 3: Export ==========
        with tab3:
            render_export(service, session, convention)

        session.close()

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)


def render_analysis_results(service: NamingConventionService, session, convention):
    """Render the analysis results tab."""
    add_vertical_space(1)

    # Get analysis results
    query = (
        session.query(VMNamingAnalysis, VirtualMachine)
        .join(VirtualMachine, VMNamingAnalysis.vm_id == VirtualMachine.id)
        .filter(VMNamingAnalysis.convention_id == convention.id)
    )

    total_count = query.count()

    if total_count == 0:
        st.info("📝 No analysis data found. Click 'Refresh Analysis' to analyze VMs.")
        return

    # Summary metrics
    valid_count = query.filter(VMNamingAnalysis.is_valid == True).count()
    invalid_count = query.filter(VMNamingAnalysis.is_valid == False).count()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total VMs", f"{total_count:,}")
    with col2:
        st.metric("Valid", f"{valid_count:,}", delta=f"{(valid_count/total_count*100):.1f}%")
    with col3:
        st.metric("Invalid", f"{invalid_count:,}", delta=f"{(invalid_count/total_count*100):.1f}%")
    with col4:
        match_rate = (valid_count / total_count * 100) if total_count > 0 else 0
        st.metric("Match Rate", f"{match_rate:.1f}%")

    add_vertical_space(1)

    # Filters
    colored_header(label="Filters", description="Filter analysis results", color_name="orange-70")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        validity_filter = st.selectbox("Validity", options=["All", "Valid Only", "Invalid Only"])

    with col2:
        datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
        selected_dc = st.selectbox("Datacenter", ["All"] + sorted(datacenters))

    with col3:
        clusters = [c[0] for c in session.query(VirtualMachine.cluster).distinct().all() if c[0]]
        selected_cluster = st.selectbox("Cluster", ["All"] + sorted(clusters))

    with col4:
        limit = st.number_input("Max Results", min_value=10, max_value=1000, value=100, step=10)

    # Field-specific filters
    if convention.fields:
        with st.expander("🔍 Filter by Field Values", expanded=False):
            field_filters = {}
            cols = st.columns(min(len(convention.fields), 4))

            for idx, field in enumerate(sorted(convention.fields, key=lambda f: f.position)):
                with cols[idx % 4]:
                    # Get unique values for this field (SQLite compatible)
                    # Fetch all analyses and extract field values in Python
                    analyses = (
                        session.query(VMNamingAnalysis)
                        .filter(VMNamingAnalysis.convention_id == convention.id, VMNamingAnalysis.is_valid == True)
                        .all()
                    )

                    field_values = set()
                    for analysis in analyses:
                        if field.field_name in analysis.field_values:
                            field_values.add(analysis.field_values[field.field_name])

                    unique_values = sorted([v for v in field_values if v])[:20]

                    if unique_values:
                        selected_value = st.selectbox(
                            f"{field.field_name}", options=["All"] + unique_values, key=f"filter_{field.field_name}"
                        )
                        if selected_value != "All":
                            field_filters[field.field_name] = selected_value

    add_vertical_space(1)

    # Apply filters to query
    if validity_filter == "Valid Only":
        query = query.filter(VMNamingAnalysis.is_valid == True)
    elif validity_filter == "Invalid Only":
        query = query.filter(VMNamingAnalysis.is_valid == False)

    if selected_dc != "All":
        query = query.filter(VirtualMachine.datacenter == selected_dc)

    if selected_cluster != "All":
        query = query.filter(VirtualMachine.cluster == selected_cluster)

    # Apply field filters (done in Python for SQLite compatibility)
    if "field_filters" in locals() and field_filters:
        # Get all results first, then filter in Python
        temp_results = query.all()
        filtered_results = []
        for analysis, vm in temp_results:
            match = True
            for field_name, field_value in field_filters.items():
                if analysis.field_values.get(field_name) != field_value:
                    match = False
                    break
            if match:
                filtered_results.append((analysis, vm))

        # Update query count and results
        filtered_count = len(filtered_results)
        results = filtered_results[:limit]
    else:
        # Get results normally
        results = query.limit(limit).all()
        filtered_count = query.count()

    if not results:
        st.warning("No VMs match the selected filters")
        return

    colored_header(
        label="Results",
        description=f"Showing {len(results)} of {filtered_count:,} matching VMs",
        color_name="violet-70",
    )

    # Prepare table data
    table_data = []
    for analysis, vm in results:
        row = {
            "VM Name": analysis.vm_name,
            "Valid": "✅" if analysis.is_valid else "❌",
            "Datacenter": vm.datacenter or "N/A",
            "Cluster": vm.cluster or "N/A",
            "Power": vm.powerstate or "N/A",
        }

        # Add parsed field values
        for field in sorted(convention.fields, key=lambda f: f.position):
            field_value = analysis.field_values.get(field.field_name, "")

            # Highlight invalid values
            if analysis.is_valid:
                row[field.field_name] = field_value
            else:
                row[field.field_name] = f"⚠️ {field_value}" if field_value else "❌"

        table_data.append(row)

    df = pd.DataFrame(table_data)

    # Display table with styling
    st.dataframe(df, use_container_width=True, hide_index=True, height=600)

    # Show validation errors for invalid VMs
    if validity_filter in ["All", "Invalid Only"]:
        invalid_analyses = [a for a, v in results if not a.is_valid]
        if invalid_analyses:
            with st.expander(f"⚠️ View Validation Errors ({len(invalid_analyses)} invalid VMs)", expanded=False):
                for analysis in invalid_analyses[:10]:  # Show first 10
                    if analysis.validation_errors and "errors" in analysis.validation_errors:
                        st.markdown(f"**{analysis.vm_name}:**")
                        for error in analysis.validation_errors["errors"]:
                            st.caption(f"  • {error}")


def render_statistics(service: NamingConventionService, session, convention):
    """Render the statistics tab."""
    add_vertical_space(1)

    colored_header(
        label="Field Value Distribution", description="Distribution of values for each field", color_name="green-70"
    )

    # Get valid analyses
    analyses = (
        session.query(VMNamingAnalysis)
        .filter(VMNamingAnalysis.convention_id == convention.id, VMNamingAnalysis.is_valid == True)
        .all()
    )

    if not analyses:
        st.info("No valid analyses found to generate statistics")
        return

    st.success(f"📊 Statistics based on {len(analyses):,} valid VMs")

    add_vertical_space(1)

    # Statistics for each field
    for field in sorted(convention.fields, key=lambda f: f.position):
        with st.container(border=True):
            st.markdown(f"### {field.field_name}")
            st.caption(f"Position: {field.position} | Length: {field.length} characters")

            # Count value occurrences
            value_counts = {}
            for analysis in analyses:
                value = analysis.field_values.get(field.field_name, "")
                value_counts[value] = value_counts.get(value, 0) + 1

            # Sort by count
            sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)

            col1, col2 = st.columns([2, 1])

            with col1:
                # Create distribution dataframe
                dist_data = []
                for value, count in sorted_values[:20]:  # Top 20
                    percentage = (count / len(analyses)) * 100
                    dist_data.append(
                        {"Value": value if value else "(empty)", "Count": count, "Percentage": f"{percentage:.1f}%"}
                    )

                if dist_data:
                    st.dataframe(
                        pd.DataFrame(dist_data),
                        use_container_width=True,
                        hide_index=True,
                        height=min(len(dist_data) * 35 + 38, 400),
                    )

            with col2:
                st.metric("Unique Values", len(value_counts))
                st.metric("Most Common", sorted_values[0][0] if sorted_values else "N/A")
                st.metric("Count", sorted_values[0][1] if sorted_values else 0)

            add_vertical_space(1)


def render_multi_convention_statistics(service: NamingConventionService, session, conventions: list):
    """Render multi-convention statistics tab."""
    add_vertical_space(1)

    colored_header(
        label="Multi-Convention Field Value Distribution",
        description=f"Compare field value distributions across {len(conventions)} conventions",
        color_name="green-70"
    )

    # Get all common field names across selected conventions
    all_field_names = set()
    for convention in conventions:
        for field in convention.fields:
            all_field_names.add(field.field_name)

    if not all_field_names:
        st.info("No fields found in selected conventions")
        return

    # Get analyses for all conventions
    all_analyses_by_convention = {}
    total_valid_vms = 0

    for convention in conventions:
        analyses = (
            session.query(VMNamingAnalysis)
            .filter(VMNamingAnalysis.convention_id == convention.id, VMNamingAnalysis.is_valid == True)
            .all()
        )
        all_analyses_by_convention[convention.id] = analyses
        total_valid_vms += len(analyses)

    if total_valid_vms == 0:
        st.info("No valid analyses found to generate statistics")
        return

    st.success(f"📊 Statistics based on {total_valid_vms:,} valid VMs across {len(conventions)} conventions")

    add_vertical_space(1)

    # Summary statistics by convention
    st.markdown("### 📈 Convention Summary")
    summary_data = []
    for convention in conventions:
        analyses = all_analyses_by_convention[convention.id]
        summary_data.append({
            "Convention": convention.name,
            "Pattern": convention.pattern,
            "Valid VMs": len(analyses),
            "Percentage": f"{(len(analyses) / total_valid_vms * 100):.1f}%" if total_valid_vms > 0 else "0%"
        })

    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    add_vertical_space(2)

    # Field-by-field comparison
    st.markdown("### 🔍 Field Value Distribution by Convention")

    for field_name in sorted(all_field_names):
        with st.container(border=True):
            st.markdown(f"### {field_name}")

            # Collect data for this field across all conventions
            field_data_by_convention = {}

            for convention in conventions:
                # Check if this convention has this field
                has_field = any(f.field_name == field_name for f in convention.fields)
                if not has_field:
                    continue

                analyses = all_analyses_by_convention[convention.id]

                # Count value occurrences for this convention
                value_counts = {}
                for analysis in analyses:
                    value = analysis.field_values.get(field_name, "")
                    if value:  # Only count non-empty values
                        value_counts[value] = value_counts.get(value, 0) + 1

                field_data_by_convention[convention.name] = value_counts

            if not field_data_by_convention:
                st.caption(f"No data available for field '{field_name}'")
                continue

            # Create comparison table
            st.markdown(f"**Value distribution across {len(field_data_by_convention)} convention(s)**")

            # Get all unique values across conventions
            all_values = set()
            for value_counts in field_data_by_convention.values():
                all_values.update(value_counts.keys())

            # Build comparison data
            comparison_data = []
            for value in sorted(all_values):
                row = {"Value": value}
                for conv_name, value_counts in field_data_by_convention.items():
                    count = value_counts.get(value, 0)
                    row[conv_name] = count
                comparison_data.append(row)

            # Sort by total count across all conventions
            comparison_data.sort(
                key=lambda x: sum(x[conv_name] for conv_name in field_data_by_convention.keys() if conv_name in x),
                reverse=True
            )

            # Display top 20 values
            df_comparison = pd.DataFrame(comparison_data[:20])
            st.dataframe(df_comparison, use_container_width=True, hide_index=True)

            # Visualization with plotly
            if len(comparison_data) > 0:
                import plotly.express as px
                import plotly.graph_objects as go

                # Prepare data for grouped bar chart
                chart_data = []
                for row in comparison_data[:10]:  # Top 10 for chart
                    for conv_name in field_data_by_convention.keys():
                        if conv_name in row:
                            chart_data.append({
                                "Value": row["Value"],
                                "Convention": conv_name,
                                "Count": row[conv_name]
                            })

                if chart_data:
                    df_chart = pd.DataFrame(chart_data)
                    fig = px.bar(
                        df_chart,
                        x="Value",
                        y="Count",
                        color="Convention",
                        barmode="group",
                        title=f"Top 10 Values for {field_name}",
                        labels={"Count": "Number of VMs", "Value": field_name}
                    )
                    st.plotly_chart(fig, use_container_width=True)

            add_vertical_space(1)


def render_export(service: NamingConventionService, session, convention):
    """Render the export tab."""
    add_vertical_space(1)

    colored_header(
        label="Export Analysis Results", description="Download naming analysis in various formats", color_name="blue-70"
    )

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        validity_filter = st.radio("Export Filter", options=["All VMs", "Valid Only", "Invalid Only"], horizontal=True)

    with col2:
        export_format = st.radio("Export Format", options=["CSV", "Excel"], horizontal=True)

    add_vertical_space(1)

    # Build query
    query = (
        session.query(VMNamingAnalysis, VirtualMachine)
        .join(VirtualMachine, VMNamingAnalysis.vm_id == VirtualMachine.id)
        .filter(VMNamingAnalysis.convention_id == convention.id)
    )

    if validity_filter == "Valid Only":
        query = query.filter(VMNamingAnalysis.is_valid == True)
    elif validity_filter == "Invalid Only":
        query = query.filter(VMNamingAnalysis.is_valid == False)

    results = query.all()

    if not results:
        st.warning("No data to export")
        return

    st.info(f"📊 Ready to export {len(results):,} VM(s)")

    # Prepare export data
    export_data = []
    for analysis, vm in results:
        row = {
            "vm_name": analysis.vm_name,
            "is_valid": analysis.is_valid,
            "datacenter": vm.datacenter or "",
            "cluster": vm.cluster or "",
            "host": vm.host or "",
            "powerstate": vm.powerstate or "",
            "vcpus": vm.cpus or 0,
            "memory_gb": (vm.memory or 0) / 1024,
            "ip_address": vm.primary_ip_address or "",
        }

        # Add field values
        for field in sorted(convention.fields, key=lambda f: f.position):
            row[field.field_name] = analysis.field_values.get(field.field_name, "")

        export_data.append(row)

    df = pd.DataFrame(export_data)

    add_vertical_space(1)

    # Preview
    with st.expander("👁️ Preview Data", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

    add_vertical_space(1)

    # Export buttons
    col1, col2 = st.columns(2)

    with col1:
        if export_format == "CSV":
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"naming_analysis_{convention.name.replace(' ', '_')}_{validity_filter.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary",
            )

    with col2:
        if export_format == "Excel":
            try:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                    df.to_excel(writer, sheet_name="Naming Analysis", index=False)

                st.download_button(
                    label="⬇️ Download Excel",
                    data=buf.getvalue(),
                    file_name=f"naming_analysis_{convention.name.replace(' ', '_')}_{validity_filter.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as e:
                st.error(f"❌ Excel export failed: {e}")
                st.caption("Note: Excel export requires xlsxwriter package")
