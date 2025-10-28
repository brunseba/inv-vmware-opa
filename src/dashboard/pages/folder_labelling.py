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
            folders = label_service.get_all_folders()
            
            if not folders:
                st.warning("No folders found in the inventory.")
                return
            
            # Assign label to folder
            with st.expander("➕ Assign Label to Folder", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_folder = st.selectbox("Select Folder", folders, key="folder_assign")
                    
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
                            st.error(f"❌ Error: {e}")
                    else:
                        st.warning("Please select folder and label")
            
            add_vertical_space(1)
            
            # List folders with labels
            st.write("**Folders with Labels:**")
            
            folder_filter = st.text_input("🔍 Filter folders", placeholder="Type to filter...")
            
            filtered_folders = [f for f in folders if not folder_filter or folder_filter.lower() in f.lower()]
            
            for folder in filtered_folders[:50]:  # Limit display
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
            
            if len(filtered_folders) > 50:
                st.info(f"Showing 50 of {len(filtered_folders)} folders. Use filter to narrow results.")
        
        # =====================================================================
        # Tab 3: VM Labels
        # =====================================================================
        with tab3:
            colored_header(
                label="VM Labels",
                description="Assign labels directly to VMs",
                color_name="violet-70"
            )
            
            # Search for VM
            vm_search = st.text_input("🔍 Search VM by name", placeholder="Enter VM name...")
            
            if vm_search and len(vm_search) >= 2:
                vms = session.query(VirtualMachine).filter(
                    VirtualMachine.vm.ilike(f"%{vm_search}%")
                ).limit(20).all()
                
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
                                            st.error(f"Error: {e}")
                else:
                    st.warning("No VMs found matching your search")
        
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
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        session.close()
