"""Folder Labelling page - Manage VM and folder labels."""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from src.services.label_service import LabelService
from src.models import VirtualMachine


def _render_label_badge(key: str, value: str, color: str = None):
    """Render a label as a colored badge."""
    bg_color = color if color else "#607078"
    return f'<span style="background-color: {bg_color}; color: white; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 12px;">{key}={value}</span>'


def render(db_url: str):
    """Render the folder labelling page."""
    colored_header(
        label="🏷️ Folder & VM Labelling",
        description="Manage labels for folders and VMs with inheritance",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        label_service = LabelService(session)
        
        # Create tabs for different operations
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Label Definitions", 
            "📁 Folder Labels", 
            "🖥️ VM Labels",
            "🔍 Search by Label",
            "⚙️ Management"
        ])
        
        # =====================================================================
        # Tab 1: Label Definitions
        # =====================================================================
        with tab1:
            colored_header(
                label="Label Definitions",
                description="Create and manage label definitions",
                color_name="green-70"
            )
            
            # Create new label
            with st.expander("➕ Create New Label", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_key = st.text_input("Key", placeholder="e.g., environment, project, owner")
                    new_value = st.text_input("Value", placeholder="e.g., production, web-app, john")
                
                with col2:
                    new_description = st.text_area("Description (optional)", placeholder="Label description")
                    new_color = st.color_picker("Color", value="#607078")
                
                if st.button("Create Label", type="primary"):
                    if new_key and new_value:
                        try:
                            label = label_service.create_label(new_key, new_value, new_description, new_color)
                            st.success(f"✅ Label created: {label.key}={label.value}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                    else:
                        st.warning("Please provide both key and value")
            
            add_vertical_space(1)
            
            # List existing labels
            labels = label_service.list_labels()
            
            if labels:
                st.write(f"**{len(labels)} label(s) defined:**")
                
                # Group by key
                labels_by_key = {}
                for label in labels:
                    if label.key not in labels_by_key:
                        labels_by_key[label.key] = []
                    labels_by_key[label.key].append(label)
                
                # Display grouped labels
                for key in sorted(labels_by_key.keys()):
                    with st.expander(f"🏷️ {key} ({len(labels_by_key[key])} values)"):
                        for label in labels_by_key[key]:
                            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
                            
                            with col1:
                                st.markdown(_render_label_badge(label.key, label.value, label.color), unsafe_allow_html=True)
                            
                            with col2:
                                st.caption(label.description if label.description else "No description")
                            
                            with col3:
                                st.caption(f"ID: {label.id} | Created: {label.created_at.strftime('%Y-%m-%d')}")
                            
                            with col4:
                                if st.button("🗑️", key=f"del_label_{label.id}", help="Delete label"):
                                    if st.session_state.get(f"confirm_del_{label.id}"):
                                        try:
                                            label_service.delete_label(label.id)
                                            st.success(f"Deleted {label.key}={label.value}")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                    else:
                                        st.session_state[f"confirm_del_{label.id}"] = True
                                        st.warning("Click again to confirm deletion")
            else:
                st.info("No labels defined yet. Create your first label above!")
        
        # =====================================================================
        # Tab 2: Folder Labels
        # =====================================================================
        with tab2:
            colored_header(
                label="Folder Labels",
                description="Assign labels to folders with inheritance options",
                color_name="orange-70"
            )
            
            # Get all folders
            all_folders = label_service.get_all_folders()
            
            if not all_folders:
                st.warning("No folders found in the inventory.")
                return
            
            # Add cluster filter
            st.write("**Filter Options:**")
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                # Get unique clusters
                clusters = session.query(VirtualMachine.cluster).filter(
                    VirtualMachine.cluster.isnot(None)
                ).distinct().order_by(VirtualMachine.cluster).all()
                cluster_list = [c[0] for c in clusters]
                selected_cluster_filter = st.selectbox(
                    "Filter by Cluster",
                    ["All Clusters"] + cluster_list,
                    key="cluster_filter"
                )
            
            with filter_col2:
                # Get unique datacenters
                datacenters = session.query(VirtualMachine.datacenter).filter(
                    VirtualMachine.datacenter.isnot(None)
                ).distinct().order_by(VirtualMachine.datacenter).all()
                datacenter_list = [d[0] for d in datacenters]
                selected_dc_filter = st.selectbox(
                    "Filter by Datacenter",
                    ["All Datacenters"] + datacenter_list,
                    key="dc_filter"
                )
            
            # Filter folders based on cluster/datacenter
            if selected_cluster_filter != "All Clusters" or selected_dc_filter != "All Datacenters":
                # Get VMs that match the filter
                vm_query = session.query(VirtualMachine.folder).filter(
                    VirtualMachine.folder.isnot(None)
                )
                
                if selected_cluster_filter != "All Clusters":
                    vm_query = vm_query.filter(VirtualMachine.cluster == selected_cluster_filter)
                
                if selected_dc_filter != "All Datacenters":
                    vm_query = vm_query.filter(VirtualMachine.datacenter == selected_dc_filter)
                
                filtered_folder_results = vm_query.distinct().all()
                folders = [f[0] for f in filtered_folder_results]
                
                st.info(f"📊 Showing {len(folders)} folder(s) matching filter")
            else:
                folders = all_folders
            
            add_vertical_space(1)
            
            # Bulk assign label to all folders
            with st.expander("📦 Bulk Assign Label to All Folders", expanded=False):
                st.markdown("**Assign a label to all folders (or filtered subset):**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Get available labels
                    label_keys = label_service.get_label_keys()
                    if label_keys:
                        bulk_key = st.selectbox("Label Key", label_keys, key="bulk_folder_label_key")
                        bulk_label_values = label_service.get_label_values(bulk_key)
                        bulk_value = st.selectbox("Label Value", bulk_label_values, key="bulk_folder_label_value")
                    else:
                        st.warning("No labels defined. Create labels in the 'Label Definitions' tab first.")
                        bulk_key = None
                        bulk_value = None
                
                with col2:
                    bulk_pattern = st.text_input(
                        "Filter Pattern (optional)",
                        placeholder="e.g., */prod/*, */backend/*",
                        help="Use glob-style pattern to filter folders",
                        key="bulk_pattern"
                    )
                    st.caption(f"Will apply to: {len(folders) if not bulk_pattern else 'filtered'} folder(s)")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    bulk_inherit_vms = st.checkbox("Apply to VMs in folders", value=True, key="bulk_inherit_vms")
                with col2:
                    bulk_inherit_subfolders = st.checkbox("Apply to subfolders", value=False, key="bulk_inherit_subfolders")
                with col3:
                    bulk_assigned_by = st.text_input("Assigned by", placeholder="Optional", key="bulk_assigned_by")
                
                # Preview button
                if st.button("🔍 Preview Folders", key="bulk_preview"):
                    import fnmatch
                    
                    # Filter folders by pattern if provided
                    if bulk_pattern:
                        preview_folders = [f for f in folders if fnmatch.fnmatch(f, bulk_pattern)]
                    else:
                        preview_folders = folders
                    
                    st.write(f"**Preview: {len(preview_folders)} folder(s) will be labeled:**")
                    
                    # Show first 20
                    for folder in preview_folders[:20]:
                        stats = label_service.get_folder_stats(folder)
                        st.caption(f"📁 {folder} ({stats['vm_count']} VMs)")
                    
                    if len(preview_folders) > 20:
                        st.caption(f"... and {len(preview_folders) - 20} more")
                
                # Apply button
                if st.button("✅ Apply to All Folders", type="primary", key="bulk_apply"):
                    if bulk_key and bulk_value:
                        import fnmatch
                        
                        # Filter folders by pattern if provided
                        if bulk_pattern:
                            target_folders = [f for f in folders if fnmatch.fnmatch(f, bulk_pattern)]
                            st.info(f"📊 Filtered to {len(target_folders)} folders matching pattern")
                        else:
                            target_folders = folders
                        
                        if not target_folders:
                            st.warning("No folders match the criteria")
                        else:
                            # Confirm
                            confirm_key = f"confirm_bulk_{bulk_key}_{bulk_value}"
                            if st.session_state.get(confirm_key):
                                try:
                                    label = label_service.get_label_by_key_value(bulk_key, bulk_value)
                                    if not label:
                                        label = label_service.create_label(bulk_key, bulk_value)
                                        st.info(f"ℹ️ Created new label: {bulk_key}={bulk_value}")
                                    
                                    # Progress bar
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    success_count = 0
                                    error_count = 0
                                    
                                    for idx, folder in enumerate(target_folders):
                                        try:
                                            label_service.assign_folder_label(
                                                folder,
                                                label.id,
                                                assigned_by=bulk_assigned_by or None,
                                                inherit_to_vms=bulk_inherit_vms,
                                                inherit_to_subfolders=bulk_inherit_subfolders
                                            )
                                            success_count += 1
                                        except Exception as e:
                                            session.rollback()
                                            error_count += 1
                                            if idx < 5:  # Show first few errors
                                                st.warning(f"⚠️ {folder}: {str(e)[:50]}")
                                        
                                        # Update progress
                                        progress = (idx + 1) / len(target_folders)
                                        progress_bar.progress(progress)
                                        status_text.text(f"Processing: {idx + 1}/{len(target_folders)}")
                                    
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    st.success(f"✅ Complete: {success_count} folders labeled")
                                    if error_count > 0:
                                        st.warning(f"⚠️ {error_count} errors (check above for details)")
                                    
                                    # Clear confirmation
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                            else:
                                st.session_state[confirm_key] = True
                                st.warning(f"⚠️ Click again to confirm: Will label {len(target_folders)} folders")
                    else:
                        st.warning("Please select label key and value")
            
            add_vertical_space(1)
            
            # Assign label to folder
            with st.expander("➕ Assign Label to Single Folder", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_folder = st.selectbox("Select Folder", folders if folders else ["No folders match filter"], key="folder_assign")
                    
                    # Show folder stats
                    if selected_folder:
                        stats = label_service.get_folder_stats(selected_folder)
                        st.info(f"📊 {stats['vm_count']} VMs | {stats['storage_gib']:.1f} GiB")
                
                with col2:
                    # Get available labels
                    label_keys = label_service.get_label_keys()
                    if label_keys:
                        selected_key = st.selectbox("Label Key", label_keys, key="folder_label_key")
                        label_values = label_service.get_label_values(selected_key)
                        selected_value = st.selectbox("Label Value", label_values, key="folder_label_value")
                    else:
                        st.warning("No labels defined. Create labels in the 'Label Definitions' tab first.")
                        selected_key = None
                        selected_value = None
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    inherit_vms = st.checkbox("Apply to VMs in folder", value=True)
                with col2:
                    inherit_subfolders = st.checkbox("Apply to subfolders", value=False)
                with col3:
                    assigned_by = st.text_input("Assigned by", placeholder="Optional")
                
                if st.button("Assign to Folder", type="primary"):
                    if selected_folder and selected_key and selected_value:
                        try:
                            label = label_service.get_label_by_key_value(selected_key, selected_value)
                            if label:
                                label_service.assign_folder_label(
                                    selected_folder, 
                                    label.id,
                                    assigned_by=assigned_by or None,
                                    inherit_to_vms=inherit_vms,
                                    inherit_to_subfolders=inherit_subfolders
                                )
                                st.success(f"✅ Label assigned to {selected_folder}")
                                st.rerun()
                        except Exception as e:
                            session.rollback()
                            error_msg = str(e)
                            if "UNIQUE constraint failed" in error_msg:
                                st.warning("⚠️ Some VMs already have this label assigned (skipped duplicates)")
                            else:
                                st.error(f"❌ Error: {e}")
                    else:
                        st.warning("Please select folder and label")
            
            add_vertical_space(1)
            
            # List folders with labels
            st.write("**Folders with Labels:**")
            
            folder_search = st.text_input("🔍 Search folders by name", placeholder="Type to search...", key="folder_search")
            
            # Apply search filter
            display_folders = folders
            if folder_search:
                display_folders = [f for f in folders if folder_search.lower() in f.lower()]
            
            # Show folder count
            if len(display_folders) != len(folders):
                st.caption(f"Showing {len(display_folders)} of {len(folders)} folders")
            
            for folder in display_folders[:50]:  # Limit display
                folder_labels = label_service.get_folder_labels(folder)
                
                if folder_labels:
                    with st.expander(f"📁 {folder} ({len(folder_labels)} label(s))"):
                        stats = label_service.get_folder_stats(folder)
                        st.caption(f"📊 {stats['vm_count']} VMs | {stats['storage_gib']:.1f} GiB")
                        
                        for lbl in folder_labels:
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                st.markdown(_render_label_badge(lbl['key'], lbl['value'], lbl['color']), unsafe_allow_html=True)
                            
                            with col2:
                                inheritance = []
                                if lbl['inherit_to_vms']:
                                    inheritance.append("VMs")
                                if lbl['inherit_to_subfolders']:
                                    inheritance.append("Subfolders")
                                st.caption(f"Inherits to: {', '.join(inheritance) if inheritance else 'None'}")
                            
                            with col3:
                                if st.button("Remove", key=f"rm_folder_{folder}_{lbl['label_id']}"):
                                    try:
                                        label_service.remove_folder_label(folder, lbl['label_id'])
                                        st.success("Label removed")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
            
            if len(display_folders) > 50:
                st.info(f"Showing first 50 of {len(display_folders)} folders. Use search to narrow results.")
        
        # =====================================================================
        # Tab 3: VM Labels
        # =====================================================================
        with tab3:
            colored_header(
                label="VM Labels",
                description="Assign labels directly to VMs",
                color_name="violet-70"
            )
            
            # Sub-tabs for individual and batch operations
            vm_tab1, vm_tab2 = st.tabs(["Individual VMs", "Batch Operations"])
            
            # ===== Individual VM Labelling =====
            with vm_tab1:
                # Search for VM
                vm_search = st.text_input("🔍 Search VM by name", placeholder="Enter VM name...")
                
                if vm_search and len(vm_search) >= 2:
                    try:
                        vms = session.query(VirtualMachine).filter(
                            VirtualMachine.vm.ilike(f"%{vm_search}%")
                        ).limit(20).all()
                    except Exception as e:
                        # Rollback session if there was a previous error
                        session.rollback()
                        st.error(f"Database error: {str(e)}")
                        vms = []
                    
                    if vms:
                        st.write(f"Found {len(vms)} VM(s):")
                        
                        for vm in vms:
                            with st.expander(f"🖥️ {vm.vm}"):
                                # Show VM info
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Datacenter:** {vm.datacenter or 'N/A'}")
                                    st.write(f"**Cluster:** {vm.cluster or 'N/A'}")
                                    st.write(f"**Folder:** {vm.folder or 'N/A'}")
                                
                                with col2:
                                    st.write(f"**Power:** {vm.powerstate or 'N/A'}")
                                    st.write(f"**vCPUs:** {vm.cpus or 0}")
                                    st.write(f"**Memory:** {(vm.memory or 0) / 1024:.1f} GB")
                                
                                st.divider()
                                
                                # Current labels
                                vm_labels = label_service.get_vm_labels(vm.id, include_inherited=True)
                                
                                if vm_labels:
                                    st.write("**Current Labels:**")
                                    for lbl in vm_labels:
                                        col1, col2 = st.columns([4, 1])
                                        
                                        with col1:
                                            st.markdown(_render_label_badge(lbl['key'], lbl['value'], lbl['color']), unsafe_allow_html=True)
                                            if lbl['inherited']:
                                                st.caption(f"↳ Inherited from: {lbl['source_folder']}")
                                        
                                        with col2:
                                            if not lbl['inherited']:
                                                if st.button("Remove", key=f"rm_vm_{vm.id}_{lbl['label_id']}"):
                                                    try:
                                                        label_service.remove_vm_label(vm.id, lbl['label_id'])
                                                        st.success("Label removed")
                                                        st.rerun()
                                                    except Exception as e:
                                                        st.error(f"Error: {e}")
                                else:
                                    st.info("No labels assigned")
                                
                                # Assign new label
                                st.divider()
                                st.write("**Assign New Label:**")
                                
                                col1, col2, col3 = st.columns([2, 2, 1])
                                
                                with col1:
                                    label_keys = label_service.get_label_keys()
                                    if label_keys:
                                        vm_label_key = st.selectbox("Key", label_keys, key=f"vm_key_{vm.id}")
                                    else:
                                        st.warning("No labels defined")
                                        vm_label_key = None
                                
                                with col2:
                                    if vm_label_key:
                                        vm_label_values = label_service.get_label_values(vm_label_key)
                                        vm_label_value = st.selectbox("Value", vm_label_values, key=f"vm_val_{vm.id}")
                                    else:
                                        vm_label_value = None
                                
                                with col3:
                                    if st.button("Assign", key=f"assign_vm_{vm.id}", type="primary"):
                                        if vm_label_key and vm_label_value:
                                            try:
                                                label = label_service.get_label_by_key_value(vm_label_key, vm_label_value)
                                                if label:
                                                    label_service.assign_vm_label(vm.id, label.id)
                                                    st.success("Label assigned")
                                                    st.rerun()
                                            except Exception as e:
                                                session.rollback()
                                                error_msg = str(e)
                                                if "UNIQUE constraint failed" in error_msg or "already assigned" in error_msg.lower():
                                                    st.info("ℹ️ This label is already assigned to this VM")
                                                else:
                                                    st.error(f"Error: {e}")
                    else:
                        st.warning("No VMs found matching your search")
            
            # ===== Batch VM Labelling =====
            with vm_tab2:
                st.write("**Batch assign labels to VMs matching specific criteria**")
                
                add_vertical_space(1)
                
                # Filter selection
                filter_type = st.selectbox(
                    "Select Filter Type",
                    ["OS Family", "Resource Size", "Network Complexity", "Storage Complexity"],
                    key="batch_filter_type"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if filter_type == "OS Family":
                        category = st.selectbox(
                            "OS Family",
                            ["windows", "linux", "unix", "other"],
                            key="os_family_select"
                        )
                        st.caption("📊 Preview VMs matching this OS family")
                    
                    elif filter_type == "Resource Size":
                        category = st.selectbox(
                            "Resource Category",
                            ["small", "medium", "large", "xlarge"],
                            key="resource_category_select"
                        )
                        size_descriptions = {
                            "small": "1-2 vCPUs, ≤ 4 GB RAM",
                            "medium": "3-4 vCPUs, 4-16 GB RAM",
                            "large": "5-8 vCPUs, 16-32 GB RAM",
                            "xlarge": "9+ vCPUs, 32+ GB RAM"
                        }
                        st.caption(f"📈 {size_descriptions[category]}")
                    
                    elif filter_type == "Network Complexity":
                        category = st.selectbox(
                            "Network Complexity",
                            ["simple", "standard", "complex"],
                            key="network_complexity_select"
                        )
                        net_descriptions = {
                            "simple": "1 NIC (single network)",
                            "standard": "2 NICs (dual-homed)",
                            "complex": "3+ NICs (multi-network)"
                        }
                        st.caption(f"🌐 {net_descriptions[category]}")
                    
                    elif filter_type == "Storage Complexity":
                        category = st.selectbox(
                            "Storage Complexity",
                            ["simple", "standard", "complex"],
                            key="storage_complexity_select"
                        )
                        storage_descriptions = {
                            "simple": "1 disk (single volume)",
                            "standard": "2-3 disks (OS + data)",
                            "complex": "4+ disks (multi-volume)"
                        }
                        st.caption(f"💾 {storage_descriptions[category]}")
                
                with col2:
                    # Label selection
                    label_keys = label_service.get_label_keys()
                    if label_keys:
                        batch_label_key = st.selectbox("Label Key", label_keys, key="batch_label_key")
                        batch_label_values = label_service.get_label_values(batch_label_key)
                        batch_label_value = st.selectbox("Label Value", batch_label_values, key="batch_label_value")
                    else:
                        st.warning("⚠️ No labels defined. Create labels first.")
                        batch_label_key = None
                        batch_label_value = None
                
                add_vertical_space(1)
                
                # Preview button
                if st.button("🔍 Preview VMs", key="preview_batch"):
                    try:
                        # Get matching VMs based on filter type
                        if filter_type == "OS Family":
                            matching_vms = label_service.get_vms_by_os_category(os_family=category)
                        elif filter_type == "Resource Size":
                            matching_vms = label_service.get_vms_by_resource_category(category)
                        elif filter_type == "Network Complexity":
                            matching_vms = label_service.get_vms_by_network_complexity(category)
                        elif filter_type == "Storage Complexity":
                            matching_vms = label_service.get_vms_by_storage_complexity(category)
                        else:
                            matching_vms = []
                        
                        if matching_vms:
                            st.success(f"✅ Found {len(matching_vms)} VMs matching criteria")
                            
                            # Display preview
                            preview_data = []
                            for vm in matching_vms[:50]:  # Show first 50
                                preview_data.append({
                                    'VM': vm.vm,
                                    'OS': vm.os_config or 'N/A',
                                    'vCPUs': vm.cpus or 0,
                                    'Memory (GB)': f"{(vm.memory or 0) / 1024:.1f}",
                                    'NICs': vm.nics or 0,
                                    'Disks': vm.disks or 0,
                                    'Folder': vm.folder or 'N/A'
                                })
                            
                            df_preview = pd.DataFrame(preview_data)
                            st.dataframe(df_preview, width="stretch", hide_index=True)
                            
                            if len(matching_vms) > 50:
                                st.info(f"ℹ️ Showing first 50 of {len(matching_vms)} VMs")
                            
                            # Store in session state for batch assign
                            st.session_state['batch_vm_ids'] = [vm.id for vm in matching_vms]
                        else:
                            st.warning("⚠️ No VMs found matching criteria")
                            st.session_state['batch_vm_ids'] = []
                    
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        st.session_state['batch_vm_ids'] = []
                
                add_vertical_space(1)
                
                # Batch assign button
                if batch_label_key and batch_label_value:
                    if st.button("✅ Assign Label to All Matching VMs", type="primary", key="batch_assign"):
                        if 'batch_vm_ids' in st.session_state and st.session_state['batch_vm_ids']:
                            try:
                                label = label_service.get_label_by_key_value(batch_label_key, batch_label_value)
                                if label:
                                    vm_ids = st.session_state['batch_vm_ids']
                                    
                                    with st.spinner(f"Assigning {batch_label_key}={batch_label_value} to {len(vm_ids)} VMs..."):
                                        successful, failed = label_service.batch_assign_label_to_vms(
                                            vm_ids, label.id, assigned_by='dashboard'
                                        )
                                    
                                    st.success(f"✅ Batch assignment complete!")
                                    st.info(f"📋 **Results:** {successful} assigned, {failed} skipped (already assigned or error)")
                                    
                                    # Clear session state
                                    del st.session_state['batch_vm_ids']
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                        else:
                            st.warning("⚠️ Please preview VMs first before batch assignment")
        
        # =====================================================================
        # Tab 4: Search by Label
        # =====================================================================
        with tab4:
            colored_header(
                label="Search by Label",
                description="Find VMs and folders by labels",
                color_name="red-70"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                label_keys = label_service.get_label_keys()
                if label_keys:
                    search_key = st.selectbox("Label Key", label_keys, key="search_key")
                    search_values = label_service.get_label_values(search_key)
                    search_value = st.selectbox("Label Value", search_values, key="search_value")
                else:
                    st.warning("No labels defined")
                    search_key = None
                    search_value = None
            
            with col2:
                search_type = st.radio("Search for:", ["VMs", "Folders", "Both"], horizontal=True)
            
            if st.button("🔍 Search", type="primary"):
                if search_key and search_value:
                    add_vertical_space(1)
                    
                    # Search VMs
                    if search_type in ["VMs", "Both"]:
                        vms = label_service.get_vms_with_label(search_key, search_value)
                        
                        st.write(f"**VMs with {search_key}={search_value}:** {len(vms)}")
                        
                        if vms:
                            vm_data = []
                            for vm in vms:
                                vm_data.append({
                                    'VM': vm.vm,
                                    'Datacenter': vm.datacenter or 'N/A',
                                    'Cluster': vm.cluster or 'N/A',
                                    'Folder': vm.folder or 'N/A',
                                    'Power': vm.powerstate or 'N/A'
                                })
                            
                            df_vms = pd.DataFrame(vm_data)
                            st.dataframe(df_vms, width="stretch", hide_index=True)
                            
                            # Export button
                            csv_data = df_vms.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="⬇️ Export CSV",
                                data=csv_data,
                                file_name=f"vms_{search_key}_{search_value}.csv",
                                mime="text/csv"
                            )
                    
                    # Search Folders
                    if search_type in ["Folders", "Both"]:
                        add_vertical_space(1)
                        folders = label_service.get_folders_with_label(search_key, search_value)
                        
                        st.write(f"**Folders with {search_key}={search_value}:** {len(folders)}")
                        
                        if folders:
                            for folder in folders:
                                stats = label_service.get_folder_stats(folder)
                                st.write(f"📁 {folder} ({stats['vm_count']} VMs)")
        
        # =====================================================================
        # Tab 5: Management
        # =====================================================================
        with tab5:
            colored_header(
                label="Label Management",
                description="Maintenance and synchronization operations",
                color_name="gray-70"
            )
            
            st.write("**System Operations:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Sync Inherited Labels**")
                st.caption("Re-apply folder labels to VMs based on inheritance settings")
                
                sync_folder = st.selectbox("Folder (or All)", ["All Folders"] + folders, key="sync_folder")
                
                if st.button("🔄 Sync Labels", type="secondary"):
                    try:
                        folder_to_sync = None if sync_folder == "All Folders" else sync_folder
                        label_service.sync_inherited_labels(folder_to_sync)
                        st.success("✅ Labels synchronized")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            with col2:
                st.write("**Statistics**")
                labels_count = len(label_service.list_labels())
                label_keys_count = len(label_service.get_label_keys())
                
                st.metric("Total Label Definitions", labels_count)
                st.metric("Unique Label Keys", label_keys_count)
                
                # Count assignments
                vm_label_count = session.query(VirtualMachine).join(
                    'virtual_machines'
                ).count() if hasattr(VirtualMachine, 'labels') else 0
                
                st.caption(f"📊 Active in system")
            
            add_vertical_space(2)
            st.divider()
            
            # Backup and Restore
            st.write("**💾 Backup & Restore:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Create Backup**")
                st.caption("Export all labels and assignments to JSON file")
                
                from datetime import datetime
                from pathlib import Path
                
                default_filename = f"labels_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_filename = st.text_input("Backup Filename", value=default_filename, key="backup_filename")
                
                if st.button("💾 Create Backup", type="primary", key="create_backup"):
                    try:
                        from src.services.backup_service import BackupService
                        backup_service = BackupService(session)
                        
                        backup_path = Path("data/backups") / backup_filename
                        
                        with st.spinner("Creating backup..."):
                            stats = backup_service.export_labels(backup_path)
                        
                        st.success(f"✅ Backup created successfully!")
                        st.info(f"📊 Labels: {stats['labels']}, VM Assignments: {stats['vm_assignments']}, Folder Assignments: {stats['folder_assignments']}")
                        st.caption(f"📁 File: {stats['file']} ({stats['size_bytes']:,} bytes)")
                        
                        # Offer download
                        with open(backup_path, 'r') as f:
                            backup_data = f.read()
                        
                        st.download_button(
                            label="⬇️ Download Backup",
                            data=backup_data,
                            file_name=backup_filename,
                            mime="application/json"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error creating backup: {e}")
            
            with col2:
                st.write("**Restore from Backup**")
                st.caption("Import labels and assignments from backup file")
                
                # File uploader
                uploaded_file = st.file_uploader(
                    "Choose backup file",
                    type=['json'],
                    key="restore_file"
                )
                
                if uploaded_file:
                    import json
                    import tempfile
                    
                    try:
                        # Show backup info
                        backup_content = json.loads(uploaded_file.read())
                        uploaded_file.seek(0)  # Reset file pointer
                        
                        st.info(f"📊 Backup contains:")
                        st.caption(f"Labels: {len(backup_content.get('labels', []))}")
                        st.caption(f"VM Assignments: {len(backup_content.get('vm_assignments', []))}")
                        st.caption(f"Folder Assignments: {len(backup_content.get('folder_assignments', []))}")
                        st.caption(f"Exported: {backup_content.get('exported_at', 'Unknown')}")
                        
                        restore_mode = st.selectbox(
                            "Import Mode",
                            ["merge", "skip_duplicates", "replace"],
                            help="merge: Update existing, skip_duplicates: Keep existing, replace: Delete and recreate",
                            key="restore_mode"
                        )
                        
                        if st.button("🔄 Restore from Backup", type="primary", key="restore_backup"):
                            # Confirmation
                            confirm_key = "confirm_restore"
                            if st.session_state.get(confirm_key):
                                try:
                                    from src.services.backup_service import BackupService
                                    backup_service = BackupService(session)
                                    
                                    # Save uploaded file temporarily
                                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                                        json.dump(backup_content, tmp)
                                        tmp_path = Path(tmp.name)
                                    
                                    with st.spinner("Restoring backup..."):
                                        stats = backup_service.import_labels(tmp_path, mode=restore_mode)
                                    
                                    # Clean up
                                    tmp_path.unlink()
                                    
                                    st.success("✅ Restore complete!")
                                    st.info(f"""
                                    **Results:**
                                    - Labels Created: {stats['labels_created']}
                                    - Labels Updated: {stats['labels_updated']}
                                    - Labels Skipped: {stats['labels_skipped']}
                                    - VM Assignments Created: {stats['vm_assignments_created']}
                                    - VM Assignments Skipped: {stats['vm_assignments_skipped']}
                                    - Folder Assignments Created: {stats['folder_assignments_created']}
                                    - Folder Assignments Skipped: {stats['folder_assignments_skipped']}
                                    """)
                                    
                                    if stats['errors']:
                                        st.warning(f"⚠️ {len(stats['errors'])} errors occurred")
                                        with st.expander("View Errors"):
                                            for error in stats['errors'][:20]:
                                                st.caption(f"- {error}")
                                    
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error restoring backup: {e}")
                                    if tmp_path.exists():
                                        tmp_path.unlink()
                            else:
                                st.session_state[confirm_key] = True
                                st.warning("⚠️ Click again to confirm restore operation")
                        
                    except json.JSONDecodeError:
                        st.error("❌ Invalid backup file format")
                    except Exception as e:
                        st.error(f"❌ Error reading backup file: {e}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        session.close()
