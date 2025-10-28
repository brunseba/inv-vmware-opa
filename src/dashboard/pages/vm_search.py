"""VM Search page - Advanced regex-based VM search."""

import streamlit as st
import re
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from src.models import VirtualMachine


def render(db_url: str):
    """Render the VM search page."""
    colored_header(
        label="🔍 VM Search",
        description="Advanced regex pattern matching for VM names",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Check if data exists
        total_vms = session.query(VirtualMachine).count()
        
        if total_vms == 0:
            st.warning("⚠️ No data found in database. Please load data first.")
            return
        
        st.info(f"📊 Searching across {total_vms:,} VMs")
        
        add_vertical_space(1)
        
        # Search input
        colored_header(
            label="Search Pattern",
            description="Enter a regex pattern to search VM names",
            color_name="green-70"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pattern = st.text_input(
                "Regex Pattern",
                placeholder="e.g., ^prod-.*, web-.*-[0-9]+, database",
                help="Enter a Python regex pattern to match VM names"
            )
        
        with col2:
            case_sensitive = st.checkbox("Case Sensitive", value=False)
        
        # Pattern examples
        with st.expander("📖 Pattern Examples"):
            st.markdown("""
            **Common Patterns:**
            - `^prod-` - VMs starting with "prod-"
            - `.*test.*` - VMs containing "test"
            - `web-[0-9]+` - VMs like "web-01", "web-123"
            - `(dev|test|staging)` - VMs containing dev, test, or staging
            - `.*\\.local$` - VMs ending with ".local"
            - `^[A-Z]{3}-.*` - VMs starting with 3 uppercase letters
            """)
        
        add_vertical_space(1)
        
        # Filters
        colored_header(
            label="Filters",
            description="Narrow down search results",
            color_name="orange-70"
        )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
            selected_dc = st.selectbox("Datacenter", ["All"] + datacenters)
        
        with col2:
            clusters = [c[0] for c in session.query(VirtualMachine.cluster).distinct().all() if c[0]]
            selected_cluster = st.selectbox("Cluster", ["All"] + clusters)
        
        with col3:
            power_states = ["All", "poweredOn", "poweredOff"]
            selected_power = st.selectbox("Power State", power_states)
        
        with col4:
            limit = st.number_input("Max Results", min_value=10, max_value=1000, value=50, step=10)
        
        add_vertical_space(1)
        
        # Search button
        search_button = st.button("🔎 Search", type="primary", use_container_width=True)
        
        if search_button or (pattern and len(pattern) >= 2):
            if not pattern:
                st.warning("Please enter a search pattern")
                return
            
            # Validate regex
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex = re.compile(pattern, flags)
            except re.error as e:
                st.error(f"❌ Invalid regex pattern: {e}")
                return
            
            # Build query
            query = session.query(VirtualMachine)
            
            # Apply filters
            if selected_dc != "All":
                query = query.filter(VirtualMachine.datacenter == selected_dc)
            if selected_cluster != "All":
                query = query.filter(VirtualMachine.cluster == selected_cluster)
            if selected_power != "All":
                query = query.filter(VirtualMachine.powerstate == selected_power)
            
            # Get all VMs and filter by regex
            all_vms = query.all()
            matching_vms = [vm for vm in all_vms if vm.vm and regex.search(vm.vm)]
            
            # Apply limit
            vms_to_show = matching_vms[:limit]
            
            add_vertical_space(1)
            
            # Results
            if not matching_vms:
                st.warning(f"No VMs found matching pattern: `{pattern}`")
                return
            
            # Results header
            colored_header(
                label=f"Search Results",
                description=f"Found {len(matching_vms):,} matching VMs" + (f" (showing {limit})" if len(matching_vms) > limit else ""),
                color_name="violet-70"
            )
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Matches", len(matching_vms))
            with col2:
                powered_on = sum(1 for vm in matching_vms if vm.powerstate == "poweredOn")
                st.metric("Powered On", powered_on)
            with col3:
                total_cpus = sum(vm.cpus or 0 for vm in matching_vms)
                st.metric("Total vCPUs", int(total_cpus))
            with col4:
                total_mem = sum(vm.memory or 0 for vm in matching_vms) / 1024
                st.metric("Total Memory", f"{total_mem:.0f} GB")
            
            add_vertical_space(1)
            
            # Prepare table data
            vm_data = []
            for vm in vms_to_show:
                # Highlight matching pattern in VM name
                vm_name = vm.vm
                if vm_name:
                    match = regex.search(vm_name)
                    if match:
                        # Mark matched portion (for display purposes)
                        vm_name = vm_name
                
                vm_data.append({
                    'VM Name': vm_name,
                    'Power': vm.powerstate or 'N/A',
                    'Datacenter': vm.datacenter or 'N/A',
                    'Cluster': vm.cluster or 'N/A',
                    'Host': vm.host or 'N/A',
                    'vCPUs': vm.cpus or 0,
                    'Memory (GB)': (vm.memory or 0) / 1024,
                    'IP Address': vm.primary_ip_address or 'N/A',
                    'OS': (vm.os_config or 'N/A')[:30]
                })
            
            df_results = pd.DataFrame(vm_data)
            
            # Export buttons
            col1, col2 = st.columns(2)
            with col1:
                csv_data = df_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Export CSV",
                    data=csv_data,
                    file_name=f"vm_search_{pattern.replace('/', '_')}.csv",
                    mime="text/csv"
                )
            with col2:
                try:
                    import io
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                        df_results.to_excel(writer, index=False, sheet_name='Search Results')
                    st.download_button(
                        label="⬇️ Export Excel",
                        data=buf.getvalue(),
                        file_name=f"vm_search_{pattern.replace('/', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception:
                    st.caption("Install xlsxwriter for Excel export")
            
            # Display results table
            st.dataframe(
                df_results.style.format({
                    'Memory (GB)': '{:.1f}'
                }),
                width="stretch",
                hide_index=True
            )
            
            add_vertical_space(1)
            
            # Detailed view selector
            with st.expander("🔍 View VM Details"):
                vm_names = [vm.vm for vm in vms_to_show]
                selected_vm_name = st.selectbox("Select a VM", vm_names)
                
                if selected_vm_name:
                    selected_vm = next((vm for vm in vms_to_show if vm.vm == selected_vm_name), None)
                    
                    if selected_vm:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**Power State:**", selected_vm.powerstate or "N/A")
                            st.write("**Datacenter:**", selected_vm.datacenter or "N/A")
                            st.write("**Cluster:**", selected_vm.cluster or "N/A")
                            st.write("**Host:**", selected_vm.host or "N/A")
                        
                        with col2:
                            st.write("**vCPUs:**", selected_vm.cpus or 0)
                            st.write("**Memory:**", f"{(selected_vm.memory or 0) / 1024:.1f} GB")
                            st.write("**Disks:**", selected_vm.disks or 0)
                            st.write("**NICs:**", selected_vm.nics or 0)
                        
                        with col3:
                            st.write("**IP Address:**", selected_vm.primary_ip_address or "N/A")
                            st.write("**DNS Name:**", selected_vm.dns_name or "N/A")
                            st.write("**OS:**", selected_vm.os_config or "N/A")
                            st.write("**Folder:**", selected_vm.folder or "N/A")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        session.close()
