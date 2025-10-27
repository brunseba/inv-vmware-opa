"""PDF Export page - Generate comprehensive PDF reports."""

import streamlit as st
from datetime import datetime
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.metric_cards import style_metric_cards
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
        
        # Report preview information
        colored_header(
            label="Report Contents",
            description="This report includes the following sections",
            color_name="green-70"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 Included Sections:
            - **Executive Summary** - Key metrics and overview
            - **Infrastructure Overview** - Datacenters, clusters, hosts
            - **Resource Analysis** - CPU and memory distribution
            - **Storage Analysis** - Provisioning and utilization
            - **Folder Analysis** - Top folders by VM count
            - **Data Quality Report** - Completeness metrics
            """)
        
        with col2:
            st.markdown("""
            ### 📈 Report Statistics:
            """)
            
            # Quick stats
            powered_on = session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.powerstate == "poweredOn"
            ).scalar() or 0
            
            total_cpus = session.query(func.sum(VirtualMachine.cpus)).scalar() or 0
            total_memory_gb = (session.query(func.sum(VirtualMachine.memory)).scalar() or 0) / 1024
            
            st.metric("Total VMs", f"{total_vms:,}")
            st.metric("Powered On", f"{powered_on:,}")
            st.metric("Total vCPUs", f"{int(total_cpus):,}")
            st.metric("Total Memory", f"{total_memory_gb:,.0f} GB")
            
            style_metric_cards(
                background_color="#1f1f1f",
                border_left_color="#2e8b57",
                border_color="#2e2e2e",
                box_shadow="#1f1f1f"
            )
        
        add_vertical_space(2)
        
        # Export section
        colored_header(
            label="Generate Report",
            description="Click the button below to generate and download your PDF report",
            color_name="orange-70"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎯 Generate PDF Report", use_container_width=True, type="primary"):
                with st.spinner("Generating PDF report... This may take a moment."):
                    try:
                        # Generate report
                        report = VMwareInventoryReport(db_url)
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
                            use_container_width=True
                        )
                        
                        # Show file info
                        pdf_size_kb = len(pdf_buffer.getvalue()) / 1024
                        st.info(f"📊 Report size: {pdf_size_kb:.1f} KB")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating report: {str(e)}")
                        import traceback
                        with st.expander("Show error details"):
                            st.code(traceback.format_exc())
        
        add_vertical_space(2)
        
        # Usage tips
        with st.expander("💡 Report Usage Tips"):
            st.markdown("""
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
            
            ### Report Format:
            - **Format**: PDF (portable, printable, archivable)
            - **Page Size**: Letter (8.5" x 11")
            - **Sections**: 7 main sections with tables and summaries
            - **File Size**: Typically 50-200 KB depending on VM count
            """)
        
        session.close()
        
    except Exception as e:
        st.error(f"❌ Error loading page: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
