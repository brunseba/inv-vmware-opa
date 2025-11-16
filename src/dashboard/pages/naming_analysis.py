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
        color_name="blue-70"
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
                st.session_state['current_page'] = "Naming Convention Manager"
                st.rerun()
            return
        
        add_vertical_space(1)
        
        # Convention selector
        col1, col2 = st.columns([3, 1])
        
        with col1:
            convention_names = {f"{c.name} ({c.pattern})": c.id for c in conventions}
            selected_name = st.selectbox(
                "Select Naming Convention",
                options=list(convention_names.keys()),
                help="Choose a convention to view analysis results"
            )
            selected_convention_id = convention_names[selected_name]
        
        with col2:
            if st.button("🔄 Refresh Analysis", use_container_width=True):
                with st.spinner("Re-analyzing VMs..."):
                    stats = service.analyze_vm_inventory(selected_convention_id)
                    st.success(f"✅ Analyzed {stats['total']} VMs")
                    st.rerun()
        
        # Get selected convention
        convention = service.get_convention(selected_convention_id)
        
        add_vertical_space(1)
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Analysis Results", "📈 Statistics", "📤 Export"])
        
        # ========== TAB 1: Analysis Results ==========
        with tab1:
            render_analysis_results(service, session, convention)
        
        # ========== TAB 2: Statistics ==========
        with tab2:
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
    query = session.query(VMNamingAnalysis, VirtualMachine).join(
        VirtualMachine, VMNamingAnalysis.vm_id == VirtualMachine.id
    ).filter(VMNamingAnalysis.convention_id == convention.id)
    
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
    colored_header(
        label="Filters",
        description="Filter analysis results",
        color_name="orange-70"
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        validity_filter = st.selectbox(
            "Validity",
            options=["All", "Valid Only", "Invalid Only"]
        )
    
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
                    # Get unique values for this field
                    field_values = session.query(
                        VMNamingAnalysis.field_values[field.field_name].astext
                    ).filter(
                        VMNamingAnalysis.convention_id == convention.id,
                        VMNamingAnalysis.is_valid == True
                    ).distinct().all()
                    
                    unique_values = sorted([v[0] for v in field_values if v[0]])[:20]
                    
                    if unique_values:
                        selected_value = st.selectbox(
                            f"{field.field_name}",
                            options=["All"] + unique_values,
                            key=f"filter_{field.field_name}"
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
    
    # Apply field filters
    if 'field_filters' in locals() and field_filters:
        for field_name, field_value in field_filters.items():
            query = query.filter(
                VMNamingAnalysis.field_values[field_name].astext == field_value
            )
    
    # Get results
    results = query.limit(limit).all()
    
    if not results:
        st.warning("No VMs match the selected filters")
        return
    
    filtered_count = query.count()
    
    colored_header(
        label="Results",
        description=f"Showing {len(results)} of {filtered_count:,} matching VMs",
        color_name="violet-70"
    )
    
    # Prepare table data
    table_data = []
    for analysis, vm in results:
        row = {
            'VM Name': analysis.vm_name,
            'Valid': '✅' if analysis.is_valid else '❌',
            'Datacenter': vm.datacenter or 'N/A',
            'Cluster': vm.cluster or 'N/A',
            'Power': vm.powerstate or 'N/A',
        }
        
        # Add parsed field values
        for field in sorted(convention.fields, key=lambda f: f.position):
            field_value = analysis.field_values.get(field.field_name, '')
            
            # Highlight invalid values
            if analysis.is_valid:
                row[field.field_name] = field_value
            else:
                row[field.field_name] = f"⚠️ {field_value}" if field_value else '❌'
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Display table with styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Show validation errors for invalid VMs
    if validity_filter in ["All", "Invalid Only"]:
        invalid_analyses = [a for a, v in results if not a.is_valid]
        if invalid_analyses:
            with st.expander(f"⚠️ View Validation Errors ({len(invalid_analyses)} invalid VMs)", expanded=False):
                for analysis in invalid_analyses[:10]:  # Show first 10
                    if analysis.validation_errors and 'errors' in analysis.validation_errors:
                        st.markdown(f"**{analysis.vm_name}:**")
                        for error in analysis.validation_errors['errors']:
                            st.caption(f"  • {error}")


def render_statistics(service: NamingConventionService, session, convention):
    """Render the statistics tab."""
    add_vertical_space(1)
    
    colored_header(
        label="Field Value Distribution",
        description="Distribution of values for each field",
        color_name="green-70"
    )
    
    # Get valid analyses
    analyses = session.query(VMNamingAnalysis).filter(
        VMNamingAnalysis.convention_id == convention.id,
        VMNamingAnalysis.is_valid == True
    ).all()
    
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
                value = analysis.field_values.get(field.field_name, '')
                value_counts[value] = value_counts.get(value, 0) + 1
            
            # Sort by count
            sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Create distribution dataframe
                dist_data = []
                for value, count in sorted_values[:20]:  # Top 20
                    percentage = (count / len(analyses)) * 100
                    dist_data.append({
                        'Value': value if value else '(empty)',
                        'Count': count,
                        'Percentage': f"{percentage:.1f}%"
                    })
                
                if dist_data:
                    st.dataframe(
                        pd.DataFrame(dist_data),
                        use_container_width=True,
                        hide_index=True,
                        height=min(len(dist_data) * 35 + 38, 400)
                    )
            
            with col2:
                st.metric("Unique Values", len(value_counts))
                st.metric("Most Common", sorted_values[0][0] if sorted_values else "N/A")
                st.metric("Count", sorted_values[0][1] if sorted_values else 0)
            
            add_vertical_space(1)


def render_export(service: NamingConventionService, session, convention):
    """Render the export tab."""
    add_vertical_space(1)
    
    colored_header(
        label="Export Analysis Results",
        description="Download naming analysis in various formats",
        color_name="blue-70"
    )
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        validity_filter = st.radio(
            "Export Filter",
            options=["All VMs", "Valid Only", "Invalid Only"],
            horizontal=True
        )
    
    with col2:
        export_format = st.radio(
            "Export Format",
            options=["CSV", "Excel"],
            horizontal=True
        )
    
    add_vertical_space(1)
    
    # Build query
    query = session.query(VMNamingAnalysis, VirtualMachine).join(
        VirtualMachine, VMNamingAnalysis.vm_id == VirtualMachine.id
    ).filter(VMNamingAnalysis.convention_id == convention.id)
    
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
            'vm_name': analysis.vm_name,
            'is_valid': analysis.is_valid,
            'datacenter': vm.datacenter or '',
            'cluster': vm.cluster or '',
            'host': vm.host or '',
            'powerstate': vm.powerstate or '',
            'vcpus': vm.cpus or 0,
            'memory_gb': (vm.memory or 0) / 1024,
            'ip_address': vm.primary_ip_address or '',
        }
        
        # Add field values
        for field in sorted(convention.fields, key=lambda f: f.position):
            row[field.field_name] = analysis.field_values.get(field.field_name, '')
        
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
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"naming_analysis_{convention.name.replace(' ', '_')}_{validity_filter.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
    
    with col2:
        if export_format == "Excel":
            try:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Naming Analysis', index=False)
                
                st.download_button(
                    label="⬇️ Download Excel",
                    data=buf.getvalue(),
                    file_name=f"naming_analysis_{convention.name.replace(' ', '_')}_{validity_filter.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"❌ Excel export failed: {e}")
                st.caption("Note: Excel export requires xlsxwriter package")
