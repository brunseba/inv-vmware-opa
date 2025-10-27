"""PDF Export page - Generate comprehensive PDF reports."""

import streamlit as st
from datetime import datetime
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.stoggle import stoggle
import plotly.graph_objects as go
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from src.models import VirtualMachine
from src.report_generator import VMwareInventoryReport


def render(db_url: str):
    """Render the PDF export page."""
    colored_header(
        label="📄 PDF Report Export",
        description="Generate comprehensive PDF reports from your inventory data",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Check if data exists
        total_vms = session.query(func.count(VirtualMachine.id)).scalar() or 0
        
        if total_vms == 0:
            st.warning("⚠️ No data found in database. Please load data first.")
            return
        
        add_vertical_space(1)
        
        # Report configuration options
        colored_header(
            label="Report Configuration",
            description="Customize your report settings",
            color_name="violet-70"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            report_type = st.selectbox(
                "Report Type",
                ["Standard", "Extended (All Charts)", "Summary Only"],
                help="Choose report comprehensiveness"
            )
        with col2:
            page_size = st.selectbox("Page Size", ["Letter", "A4"], help="Choose paper size")
        with col3:
            detailed_tables = st.checkbox("Detailed Tables", value=True, help="Include comprehensive data tables")
        
        # Set include_charts based on report type
        include_charts = report_type != "Summary Only"
        is_extended = report_type == "Extended (All Charts)"
        
        # Advanced options in expander
        with st.expander("⚙️ Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Chart Settings:**")
                chart_dpi = st.slider("Chart Quality (DPI)", 100, 300, 150, 25, help="Higher = better quality but larger file")
                color_scheme = st.selectbox("Color Scheme", ["Professional", "Grayscale", "High Contrast"])
            
            with col2:
                st.markdown("**Data Filters:**")
                max_items = st.slider("Max items per table", 5, 20, 10, help="Limit rows in tables")
                include_nulls = st.checkbox("Include items with missing data", value=True)
        
        add_vertical_space(1)
        
        # Report preview information
        colored_header(
            label="Report Contents",
            description="This report includes the following sections",
            color_name="green-70"
        )
        
        # Create tabs for better organization
        tab1, tab2, tab3 = st.tabs(["📋 Sections", "📊 Preview", "📈 Statistics"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### Included Sections:
                - ✅ **Executive Summary** - Key metrics and overview
                - ✅ **Infrastructure Overview** - Datacenters, clusters, hosts
                - ✅ **Resource Analysis** - CPU and memory distribution
                """)
            
            with col2:
                st.markdown("""
                ### Additional Sections:
                - ✅ **Storage Analysis** - Provisioning and utilization
                - ✅ **Folder Analysis** - Top folders by VM count
                - ✅ **Data Quality Report** - Completeness metrics
                """)
            
            if is_extended:
                st.success("🔥 Extended Report: ALL charts from web interface included!")
                st.info("⚡ This includes 15+ visualizations across all sections")
            elif include_charts:
                st.success("📊 Standard Report: Key charts included (8+ charts)")
            else:
                st.info("📋 Summary Only: Tables only (smallest file size)")
        
        with tab2:
            # Visual preview using metrics
            st.markdown("### Report Structure Preview")
            
            sections = [
                ("Title Page", "Professional cover with metadata"),
                ("Executive Summary", "High-level overview with key metrics"),
                ("Infrastructure", "Datacenter and cluster breakdown"),
                ("Resources", "CPU and memory analysis"),
                ("Storage", "Storage consumption and efficiency"),
                ("Folders", "VM organization analysis"),
                ("Data Quality", "Completeness assessment")
            ]
            
            for idx, (section, desc) in enumerate(sections, 1):
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"**{idx}**")
                    with col2:
                        st.markdown(f"**{section}**  \n{desc}")
                    if idx < len(sections):
                        st.divider()
        
        with tab3:
            st.markdown("""
            ### Report Metrics:
            """)
            
            # Quick stats
            powered_on = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.powerstate == "poweredOn"
            ).scalar() or 0
            
            total_cpus = session.query(func.sum(VirtualMachine.cpus)).scalar() or 0
            total_memory_gb = (session.query(func.sum(VirtualMachine.memory)).scalar() or 0) / 1024
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total VMs", f"{total_vms:,}")
            with col2:
                st.metric("Powered On", f"{powered_on:,}")
            with col3:
                st.metric("Total vCPUs", f"{int(total_cpus):,}")
            with col4:
                st.metric("Total Memory", f"{total_memory_gb:,.0f} GB")
            
            style_metric_cards(
                background_color="#1f1f1f",
                border_left_color="#2e8b57",
                border_color="#2e2e2e",
                box_shadow="#1f1f1f"
            )
            
            # Add a mini visualization
            add_vertical_space(1)
            st.markdown("**Power State Distribution:**")
            
            fig = go.Figure(data=[
                go.Bar(
                    x=['Powered On', 'Powered Off'],
                    y=[powered_on, total_vms - powered_on],
                    marker_color=['#2ecc71', '#e74c3c'],
                    text=[f'{powered_on:,}', f'{total_vms - powered_on:,}'],
                    textposition='auto',
                )
            ])
            fig.update_layout(
                height=200,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis_title="",
                yaxis_title="VM Count"
            )
            st.plotly_chart(fig, width='stretch')
        
        add_vertical_space(2)
        
        # Export section
        colored_header(
            label="Generate Report",
            description="Ready to generate your customized PDF report",
            color_name="orange-70"
        )
        
        # Show estimated file size
        if not include_charts:
            estimated_size = 50
            estimated_time = 2 + (total_vms // 1000) * 2
        elif is_extended:
            estimated_size = 200 + (chart_dpi - 100) * 4  # More charts
            estimated_time = 2 + (total_vms // 1000) * 2 + 20  # 15+ charts
        else:
            estimated_size = 100 + (chart_dpi - 100) * 2
            estimated_time = 2 + (total_vms // 1000) * 2 + 8
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Estimated Size", f"{estimated_size}-{estimated_size*2} KB")
        with col2:
            st.metric("Estimated Time", f"{estimated_time}-{estimated_time*2}s")
        with col3:
            st.metric("Sections", "7")
        
        style_metric_cards(
            background_color="#1f1f1f",
            border_left_color="#ff8c00",
            border_color="#2e2e2e",
            box_shadow="#1f1f1f"
        )
        
        add_vertical_space(1)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Store config in session state
            if 'pdf_config' not in st.session_state:
                st.session_state.pdf_config = {}
            
            st.session_state.pdf_config = {
                'include_charts': include_charts,
                'is_extended': is_extended,
                'report_type': report_type,
                'page_size': page_size,
                'detailed_tables': detailed_tables,
                'chart_dpi': chart_dpi,
                'color_scheme': color_scheme,
                'max_items': max_items,
                'include_nulls': include_nulls
            }
            
            if st.button("🎯 Generate PDF Report", width='stretch', type="primary"):
                with st.spinner("Generating PDF report... This may take a moment."):
                    try:
                        # Generate report with configuration
                        report = VMwareInventoryReport(
                            db_url, 
                            include_charts=include_charts,
                            extended=is_extended,
                            chart_dpi=chart_dpi
                        )
                        pdf_buffer = report.generate_report()
                        report.close()
                        
                        # Create filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"vmware_inventory_report_{timestamp}.pdf"
                        
                        # Success message
                        st.success("✅ Report generated successfully!")
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=pdf_buffer,
                            file_name=filename,
                            mime="application/pdf",
                            width='stretch'
                        )
                        
                        # Show file info with nice formatting
                        pdf_size_kb = len(pdf_buffer.getvalue()) / 1024
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("File Size", f"{pdf_size_kb:.1f} KB")
                        with col2:
                            st.metric("Format", page_size)
                        with col3:
                            st.metric("Quality", f"{chart_dpi} DPI" if include_charts else "Tables")
                        
                        # Add to history
                        st.session_state.report_history.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'size': pdf_size_kb,
                            'vms': total_vms,
                            'config': st.session_state.pdf_config
                        })
                        
                        # Show success badge
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Error generating report: {str(e)}")
                        import traceback
                        with st.expander("Show error details"):
                            st.code(traceback.format_exc())
        
        add_vertical_space(2)
        
        # Report history (if available)
        if 'report_history' not in st.session_state:
            st.session_state.report_history = []
        
        if st.session_state.report_history:
            colored_header(
                label="Recent Reports",
                description="Previously generated reports in this session",
                color_name="blue-70"
            )
            
            for idx, report in enumerate(reversed(st.session_state.report_history[-5:])):
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    with col1:
                        st.text(report.get('timestamp', 'N/A'))
                    with col2:
                        st.text(f"{report.get('size', 0):.1f} KB")
                    with col3:
                        st.text(f"{report.get('vms', 0):,} VMs")
                    with col4:
                        st.text(report.get('config', {}).get('page_size', 'Letter'))
            
            if st.button("🗑️ Clear History"):
                st.session_state.report_history = []
                st.rerun()
            
            add_vertical_space(1)
        
        # Usage tips with toggle
        stoggle(
            "💡 Report Usage Tips",
            """
            ### How to use this report:
            
            1. **Executive Summary** - Perfect for management presentations
            2. **Infrastructure Overview** - Share with your VMware team for planning
            3. **Resource Analysis** - Use for capacity planning and resource optimization
            4. **Storage Analysis** - Identify thin provisioning opportunities
            5. **Data Quality** - Track and improve data completeness
            
            ### Best Practices:
            - Generate reports regularly (weekly/monthly) to track trends
            - Archive reports for compliance and audit purposes
            - Share with stakeholders who don't have dashboard access
            - Use for capacity planning meetings
            - Include in documentation and runbooks
            
            ### Configuration Tips:
            - **High DPI (200-300)**: For printing or presentations
            - **Low DPI (100-150)**: For email or archival
            - **No Charts**: Smallest file size, fastest generation
            - **A4 vs Letter**: Choose based on your region
            """
        )
        
        add_vertical_space(1)
        
        # Quick actions
        with st.expander("⚡ Quick Actions"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📧 Email Report Settings", width='stretch'):
                    st.info("Configure email settings in the main configuration")
            
            with col2:
                if st.button("📅 Schedule Reports", width='stretch'):
                    st.info("Report scheduling feature coming soon!")
            
            st.markdown("---")
            
            # Quick presets
            st.markdown("**Quick Presets:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔥 Extended Report\n(ALL Charts)", width='stretch'):
                    st.session_state.pdf_config = {
                        'report_type': 'Extended (All Charts)',
                        'include_charts': True,
                        'is_extended': True,
                        'detailed_tables': True,
                        'chart_dpi': 150
                    }
                    st.success("Extended report preset loaded!")
                    st.rerun()
            
            with col2:
                if st.button("📋 Quick Summary\n(Tables Only)", width='stretch'):
                    st.session_state.pdf_config = {
                        'include_charts': False,
                        'detailed_tables': False,
                        'max_items': 5
                    }
                    st.success("Quick summary preset loaded!")
            
            with col3:
                if st.button("🖨️ Print Quality\n(High DPI)", width='stretch'):
                    st.session_state.pdf_config = {
                        'include_charts': True,
                        'detailed_tables': True,
                        'chart_dpi': 300
                    }
                    st.success("Print quality preset loaded!")
        
        session.close()
        
    except Exception as e:
        st.error(f"❌ Error loading page: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
