"""VM Explorer page - Detailed VM search and information."""

import streamlit as st
import re
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.models import VirtualMachine


def render(db_url: str):
    """Render the VM explorer page."""
    st.markdown('<h1 class="main-header">🔍 VM Explorer</h1>', unsafe_allow_html=True)
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Search and filters
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            search_term = st.text_input("🔎 Search VMs", placeholder="Enter VM name, IP, or hostname...")
        
        with col4:
            use_regex = st.checkbox("Use Regex", value=False, help="Enable regex pattern matching")
        
        with col2:
            datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
            selected_dc = st.selectbox("Datacenter", ["All"] + datacenters)
        
        with col3:
            power_states = [p[0] for p in session.query(VirtualMachine.powerstate).distinct().all() if p[0]]
            selected_power = st.selectbox("Power State", ["All"] + power_states)
        
        # Additional filters
        colf1, colf2 = st.columns(2)
        with colf1:
            template_filter = st.selectbox("Template", ["All", "Only Templates", "Exclude Templates"], index=2)
        with colf2:
            date_range = st.date_input("Creation Date Range", value=[])
        
        # Build query
        query = session.query(VirtualMachine)
        
        # Handle regex vs normal search
        if search_term and use_regex:
            # For regex, get all VMs and filter in Python
            pass  # We'll filter after fetching
        elif search_term:
            query = query.filter(
                or_(
                    VirtualMachine.vm.ilike(f"%{search_term}%"),
                    VirtualMachine.dns_name.ilike(f"%{search_term}%"),
                    VirtualMachine.primary_ip_address.ilike(f"%{search_term}%"),
                    VirtualMachine.host.ilike(f"%{search_term}%")
                )
            )
        
        if selected_dc != "All":
            query = query.filter(VirtualMachine.datacenter == selected_dc)
        
        if selected_power != "All":
            query = query.filter(VirtualMachine.powerstate == selected_power)

        # Template filter
        if template_filter == "Only Templates":
            query = query.filter(VirtualMachine.template.is_(True))
        elif template_filter == "Exclude Templates":
            query = query.filter(VirtualMachine.template.is_(False))

        # Date range filter
        if date_range:
            if isinstance(date_range, (list, tuple)):
                if len(date_range) == 1:
                    start_date = date_range[0]
                    query = query.filter(VirtualMachine.creation_date >= start_date)
                elif len(date_range) >= 2:
                    start_date, end_date = date_range[0], date_range[1]
                    if start_date:
                        query = query.filter(VirtualMachine.creation_date >= start_date)
                    if end_date:
                        # Include end date fully
                        import datetime
                        query = query.filter(VirtualMachine.creation_date < (datetime.datetime.combine(end_date, datetime.time.max)))
        
        # Apply regex filter if needed
        all_vms = query.all()
        
        if search_term and use_regex:
            try:
                regex = re.compile(search_term, re.IGNORECASE)
                all_vms = [
                    vm for vm in all_vms 
                    if any([
                        vm.vm and regex.search(vm.vm),
                        vm.dns_name and regex.search(vm.dns_name),
                        vm.primary_ip_address and regex.search(vm.primary_ip_address)
                    ])
                ]
            except re.error as e:
                st.error(f"❌ Invalid regex pattern: {e}")
                return
        
        # Pagination
        total_results = len(all_vms)
        st.info(f"Found {total_results:,} VMs" + (" (regex filter applied)" if use_regex and search_term else ""))
        
        page_size = st.selectbox("Results per page", [10, 25, 50, 100], index=1)
        page = st.number_input("Page", min_value=1, max_value=max(1, (total_results // page_size) + 1), value=1)
        
        offset = (page - 1) * page_size
        vms = all_vms[offset:offset + page_size]
        
        if not vms:
            st.warning("No VMs found matching your criteria")
            return
        
        st.divider()
        
        # Results table
        vm_data = []
        for vm in vms:
            vm_data.append({
                'VM': vm.vm,
                'Power': vm.powerstate or 'N/A',
                'CPUs': vm.cpus or 0,
                'Memory_GB': (vm.memory or 0) / 1024,
                'IP': vm.primary_ip_address or 'N/A',
                'OS': (vm.os_config or 'N/A')[:30],
                'Datacenter': vm.datacenter or 'N/A',
                'Cluster': vm.cluster or 'N/A',
                'Host': vm.host or 'N/A',
            })
        
        df_vms = pd.DataFrame(vm_data)

        # Export buttons
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            st.download_button(
                label="⬇️ Export CSV",
                data=df_vms.to_csv(index=False).encode('utf-8'),
                file_name="vms_export.csv",
                mime="text/csv"
            )
        with exp_col2:
            try:
                import io
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    df_vms.to_excel(writer, index=False, sheet_name='VMs')
                st.download_button(
                    label="⬇️ Export Excel",
                    data=buf.getvalue(),
                    file_name="vms_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception:
                st.caption("Install xlsxwriter for Excel export: uv add xlsxwriter")
        
        # Display with formatting
        st.dataframe(
            df_vms.style.format({
                'Memory_GB': '{:.1f}'
            }),
            width="stretch",
            hide_index=True
        )
        
        st.divider()
        
        # VM Details section
        st.subheader("VM Details")
        vm_names = [vm.vm for vm in vms]
        selected_vm_name = st.selectbox("Select a VM to view details", vm_names)
        
        if selected_vm_name:
            selected_vm = next((vm for vm in vms if vm.vm == selected_vm_name), None)
            
            if selected_vm:
                # Basic info
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Power State", selected_vm.powerstate or "N/A")
                with col2:
                    st.metric("vCPUs", selected_vm.cpus or 0)
                with col3:
                    memory_gb = (selected_vm.memory or 0) / 1024
                    st.metric("Memory", f"{memory_gb:.1f} GB")
                with col4:
                    st.metric("NICs", selected_vm.nics or 0)
                
                # Detailed information tabs
                tab1, tab2, tab3, tab4 = st.tabs(["📋 General", "💾 Resources", "🌐 Network", "🏗️ Infrastructure"])
                
                with tab1:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**VM Name:**", selected_vm.vm)
                        st.write("**DNS Name:**", selected_vm.dns_name or "N/A")
                        st.write("**OS:**", selected_vm.os_config or "N/A")
                        st.write("**Template:**", "Yes" if selected_vm.template else "No")
                        st.write("**Guest State:**", selected_vm.guest_state or "N/A")
                        st.write("**VM Tools:**", selected_vm.os_vmware_tools or "N/A")
                    with col2:
                        st.write("**VM ID:**", selected_vm.vm_id or "N/A")
                        st.write("**UUID:**", selected_vm.vm_uuid or "N/A")
                        st.write("**HW Version:**", selected_vm.hw_version or "N/A")
                        st.write("**Firmware:**", selected_vm.firmware or "N/A")
                        if selected_vm.creation_date:
                            st.write("**Created:**", selected_vm.creation_date.strftime("%Y-%m-%d %H:%M"))
                
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**vCPUs:**", selected_vm.cpus or 0)
                        st.write("**Memory:**", f"{memory_gb:.1f} GB")
                        st.write("**Disks:**", selected_vm.disks or 0)
                        st.write("**NICs:**", selected_vm.nics or 0)
                    with col2:
                        if selected_vm.provisioned_mib:
                            st.write("**Provisioned:**", f"{selected_vm.provisioned_mib / 1024:.1f} GB")
                        if selected_vm.in_use_mib:
                            st.write("**In Use:**", f"{selected_vm.in_use_mib / 1024:.1f} GB")
                        if selected_vm.unshared_mib:
                            st.write("**Unshared:**", f"{selected_vm.unshared_mib / 1024:.1f} GB")
                
                with tab3:
                    st.write("**Primary IP:**", selected_vm.primary_ip_address or "N/A")
                    networks = []
                    for i in range(1, 9):
                        net = getattr(selected_vm, f"network_{i}", None)
                        if net:
                            networks.append(f"Network {i}: {net}")
                    if networks:
                        for net in networks:
                            st.write(f"**{net.split(':')[0]}:**", net.split(': ')[1] if ': ' in net else "N/A")
                    else:
                        st.info("No network information available")
                
                with tab4:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Datacenter:**", selected_vm.datacenter or "N/A")
                        st.write("**Cluster:**", selected_vm.cluster or "N/A")
                        st.write("**Host:**", selected_vm.host or "N/A")
                        st.write("**Resource Pool:**", selected_vm.resource_pool or "N/A")
                    with col2:
                        st.write("**Folder:**", selected_vm.folder or "N/A")
                        st.write("**vApp:**", selected_vm.vapp or "N/A")
                        st.write("**HA Protection:**", selected_vm.das_protection or "N/A")
                        st.write("**Environment:**", selected_vm.env or "N/A")
                
                # Annotation if available
                if selected_vm.annotation:
                    with st.expander("📝 Annotation"):
                        st.text(selected_vm.annotation)
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
    finally:
        session.close()
