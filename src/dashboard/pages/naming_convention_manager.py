"""Naming Convention Manager page - Create and manage VM naming conventions."""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from src.services.naming_convention_service import (
    NamingConventionService,
    NamingConventionError,
    PatternValidationError,
)
from src.models import NamingConvention


def render(db_url: str):
    """Render the naming convention manager page."""
    colored_header(
        label="🏷️ Naming Convention Manager",
        description="Create and manage VM naming conventions for pattern analysis",
        color_name="blue-70",
    )

    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        service = NamingConventionService(session)

        # Check if we're in edit mode
        if "edit_convention_id" in st.session_state and st.session_state.edit_convention_id:
            # Show edit interface
            render_edit_convention(service, st.session_state.edit_convention_id)
        else:
            # Tabs for different operations
            tab1, tab2, tab3 = st.tabs(["📋 Conventions List", "➕ Create Convention", "📖 Documentation"])

            # ========== TAB 1: List Conventions ==========
            with tab1:
                render_conventions_list(service, session)

            # ========== TAB 2: Create Convention ==========
            with tab2:
                render_create_convention(service)

            # ========== TAB 3: Documentation ==========
            with tab3:
                render_documentation()

        session.close()

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)


def render_conventions_list(service: NamingConventionService, session):
    """Render the conventions list tab."""
    add_vertical_space(1)

    # Refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Get all conventions
    conventions = service.list_conventions(active_only=False)

    if not conventions:
        st.info("📝 No naming conventions found. Create one in the 'Create Convention' tab.")
        return

    st.success(f"✅ Found {len(conventions)} naming convention(s)")

    add_vertical_space(1)

    # Multi-convention analysis section
    if len(conventions) > 1:
        with st.expander("🔀 Multi-Convention Analysis", expanded=False):
            st.caption("Analyze VMs against multiple conventions simultaneously")

            # Convention selection
            selected_conventions = []
            cols_per_row = 3
            for i in range(0, len(conventions), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(conventions):
                        conv = conventions[idx]
                        with col:
                            if st.checkbox(
                                f"{conv.name}", key=f"multi_select_{conv.id}", help=f"Pattern: {conv.pattern}"
                            ):
                                selected_conventions.append(conv.id)

            add_vertical_space(1)

            # Analysis options
            col1, col2 = st.columns(2)
            with col1:
                test_all = st.checkbox(
                    "Test all conventions",
                    value=False,
                    key="multi_test_all",
                    help="Test all conventions even if VM matches earlier one",
                )
            with col2:
                batch_size = st.number_input(
                    "Batch size",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    key="multi_batch_size",
                    help="Number of VMs to process per batch",
                )

            add_vertical_space(1)

            # Analyze button
            if st.button(
                "🔍 Analyze with Selected Conventions",
                disabled=len(selected_conventions) < 2,
                type="primary",
                use_container_width=True,
            ):
                if len(selected_conventions) < 2:
                    st.warning("⚠️ Please select at least 2 conventions")
                else:
                    analyze_multi_conventions(service, selected_conventions, conventions, test_all, batch_size)

    add_vertical_space(1)

    # Display conventions as cards
    for convention in conventions:
        with st.expander(
            f"{'✅' if convention.is_active else '❌'} **{convention.name}** - {convention.pattern}", expanded=False
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Length", f"{convention.total_length} chars")
            with col2:
                st.metric("Fields", len(convention.fields))
            with col3:
                st.metric("Status", "Active" if convention.is_active else "Inactive")

            st.caption(f"**Pattern:** `{convention.pattern}`")
            if convention.description:
                st.caption(f"**Description:** {convention.description}")
            st.caption(f"**Created:** {convention.created_at.strftime('%Y-%m-%d %H:%M')}")

            add_vertical_space(1)

            # Fields table
            st.markdown("**Fields:**")
            field_data = []
            for field in sorted(convention.fields, key=lambda f: f.position):
                possible_vals = ""
                if field.possible_values and isinstance(field.possible_values, list):
                    possible_vals = ", ".join(field.possible_values[:3])
                    if len(field.possible_values) > 3:
                        possible_vals += "..."

                field_data.append(
                    {
                        "Position": field.position,
                        "Field Name": field.field_name,
                        "Length": field.length,
                        "Required": "✓" if field.is_required else "✗",
                        "Possible Values": possible_vals or "-",
                    }
                )

            st.dataframe(pd.DataFrame(field_data), use_container_width=True, hide_index=True)

            add_vertical_space(1)

            # Action buttons
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("✏️ Edit", key=f"edit_{convention.id}", use_container_width=True):
                    st.session_state.edit_convention_id = convention.id
                    st.rerun()

            with col2:
                if st.button(
                    "🔍 Analyze VMs", key=f"analyze_{convention.id}", use_container_width=True, type="primary"
                ):
                    analyze_convention(service, convention)

            with col3:
                if st.button("🏷️ Apply Labels", key=f"labels_{convention.id}", use_container_width=True):
                    st.session_state[f"show_label_config_{convention.id}"] = True
                    st.rerun()

            with col4:
                if st.button("📊 View Results", key=f"view_{convention.id}", use_container_width=True):
                    st.session_state["nav_to_analysis"] = convention.id
                    st.info("Navigate to 'Naming Analysis' page to view results")

            with col5:
                if st.button("🗑️ Delete", key=f"delete_{convention.id}", use_container_width=True):
                    if st.session_state.get(f"confirm_delete_{convention.id}"):
                        try:
                            service.delete_convention(convention.id)
                            st.success(f"✅ Deleted convention '{convention.name}'")
                            add_vertical_space(1)
                            if st.button("↩️ Back to List"):
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting convention: {e}")
                    else:
                        st.session_state[f"confirm_delete_{convention.id}"] = True
                        st.warning("⚠️ Click again to confirm deletion")

            # Label configuration dialog
            if st.session_state.get(f"show_label_config_{convention.id}"):
                show_label_configuration(service, convention)


def show_label_configuration(service: NamingConventionService, convention: NamingConvention):
    """Show label configuration dialog."""
    add_vertical_space(1)
    st.markdown("---")
    st.markdown(f"### 🏷️ Apply Labels from Convention: {convention.name}")

    # Field selection
    field_names = [f.field_name for f in sorted(convention.fields, key=lambda f: f.position)]
    selected_fields = st.multiselect(
        "Select fields to create labels for:",
        options=field_names,
        default=field_names,
        key=f"label_fields_{convention.id}",
        help="Labels will be created for selected fields only",
    )

    add_vertical_space(1)

    # Filter options
    st.markdown("**Filter VMs (optional):**")
    col1, col2 = st.columns(2)
    with col1:
        datacenter = st.text_input(
            "Datacenter", key=f"label_dc_{convention.id}", help="Apply labels only to VMs in this datacenter"
        )
    with col2:
        cluster = st.text_input(
            "Cluster", key=f"label_cluster_{convention.id}", help="Apply labels only to VMs in this cluster"
        )

    add_vertical_space(1)

    # Options
    col1, col2 = st.columns(2)
    with col1:
        overwrite = st.checkbox(
            "Overwrite existing labels",
            value=False,
            key=f"label_overwrite_{convention.id}",
            help="Replace existing label values for VMs",
        )
    with col2:
        dry_run = st.checkbox(
            "Dry run (preview only)",
            value=True,
            key=f"label_dry_run_{convention.id}",
            help="Preview changes without applying them",
        )

    add_vertical_space(1)

    # Build filter
    vm_filter = {}
    if datacenter:
        vm_filter["datacenter"] = datacenter
    if cluster:
        vm_filter["cluster"] = cluster

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button(
            "🚀 Apply Labels",
            key=f"apply_labels_btn_{convention.id}",
            type="primary",
            disabled=len(selected_fields) == 0,
            use_container_width=True,
        ):
            apply_labels_from_convention(service, convention, selected_fields, vm_filter, overwrite, dry_run)

    with col2:
        if st.button("❌ Cancel", key=f"cancel_labels_{convention.id}", use_container_width=True):
            st.session_state[f"show_label_config_{convention.id}"] = False
            st.rerun()

    st.markdown("---")


def apply_labels_from_convention(
    service: NamingConventionService,
    convention: NamingConvention,
    fields: list,
    vm_filter: dict,
    overwrite: bool,
    dry_run: bool,
):
    """Apply labels from naming convention fields."""
    mode_text = "Preview" if dry_run else "Applying"
    with st.spinner(f"{mode_text} labels for convention '{convention.name}'..."):
        try:
            stats = service.apply_labels_from_analysis(
                convention_id=convention.id,
                vm_filter=vm_filter if vm_filter else None,
                overwrite_existing=overwrite,
                field_filter=fields if fields != [f.field_name for f in convention.fields] else None,
                dry_run=dry_run,
                assigned_by="streamlit_ui",
            )

            if dry_run:
                st.info("🔍 **Dry Run Results (No changes made)**")
            else:
                st.success("✅ **Labels Applied Successfully!**")

            # Display statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏷️ Labels Created", stats["labels_created"])
            with col2:
                st.metric("🔗 Assignments", stats["labels_assigned"])
            with col3:
                st.metric("🖥️ VMs Labeled", stats["vms_labeled"])
            with col4:
                if stats["labels_removed"] > 0:
                    st.metric("🗑️ Labels Removed", stats["labels_removed"])
                elif stats["labels_skipped"] > 0:
                    st.metric("⏭️ Labels Skipped", stats["labels_skipped"])

            add_vertical_space(1)

            # Show label examples if created
            if stats["labels_created"] > 0 and dry_run:
                st.markdown("**Label Preview:**")
                st.caption(f"Labels will follow format: `nc:{convention.name}:<field> = <value>`")
                st.caption(f"Example: `nc:{convention.name}:{fields[0]} = <extracted_value>`")

        except Exception as e:
            st.error(f"❌ Error applying labels: {e}")


def analyze_convention(service: NamingConventionService, convention: NamingConvention):
    """Analyze VMs with the selected convention."""
    with st.spinner(f"Analyzing VMs with convention '{convention.name}'..."):
        try:
            stats = service.analyze_vm_inventory(convention.id)

            st.success("✅ Analysis Complete!")

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total VMs", stats["total"])
            with col2:
                st.metric("Valid", stats["valid"])
            with col3:
                st.metric("Invalid", stats["invalid"])
            with col4:
                st.metric("Created", stats["created"])
            with col5:
                st.metric("Updated", stats["updated"])

            if stats["total"] > 0:
                valid_pct = (stats["valid"] / stats["total"]) * 100
                st.progress(valid_pct / 100, text=f"Match Rate: {valid_pct:.1f}%")

        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")


def analyze_multi_conventions(
    service: NamingConventionService, selected_ids: list, all_conventions: list, test_all: bool, batch_size: int
):
    """Analyze VMs with multiple conventions."""
    with st.spinner(f"Analyzing VMs with {len(selected_ids)} conventions..."):
        try:
            stats = service.analyze_vm_inventory_multi(
                convention_ids=selected_ids, vm_filter=None, batch_size=batch_size, stop_on_first_match=not test_all
            )

            st.success("✅ Multi-Convention Analysis Complete!")

            # Overall statistics
            st.markdown("### 📊 Overall Results")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total VMs", stats["total"])
            with col2:
                matched_pct = (stats["matched"] / stats["total"] * 100) if stats["total"] > 0 else 0
                st.metric("Matched", f"{stats['matched']} ({matched_pct:.1f}%)")
            with col3:
                unmatched_pct = (stats["unmatched"] / stats["total"] * 100) if stats["total"] > 0 else 0
                st.metric("Unmatched", f"{stats['unmatched']} ({unmatched_pct:.1f}%)")
            with col4:
                if stats["multiple_matches"] > 0:
                    st.metric("Multiple Matches", stats["multiple_matches"])
                else:
                    st.metric("Records Created", stats["records_created"])

            add_vertical_space(1)

            # Records statistics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🆕 Records Created", stats["records_created"])
            with col2:
                st.metric("🔄 Records Updated", stats["records_updated"])

            add_vertical_space(1)

            # Per-convention results
            st.markdown("### 📊 Results by Convention")

            # Prepare data for chart
            conv_data = []
            for conv_id in selected_ids:
                conv = next((c for c in all_conventions if c.id == conv_id), None)
                if conv:
                    match_count = stats["by_convention"][conv_id]
                    match_pct = (match_count / stats["total"] * 100) if stats["total"] > 0 else 0
                    conv_data.append({"Convention": conv.name, "Matches": match_count, "Percentage": match_pct})

            # Display as table
            conv_df = pd.DataFrame(conv_data)
            st.dataframe(conv_df, use_container_width=True, hide_index=True)

            # Display as bar chart
            if conv_data:
                import plotly.express as px

                fig = px.bar(
                    conv_df,
                    x="Convention",
                    y="Matches",
                    text="Percentage",
                    title="Matches by Convention",
                    labels={"Matches": "Number of Matches", "Convention": "Naming Convention"},
                )
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Multi-convention analysis failed: {e}")
            st.exception(e)


def render_create_convention(service: NamingConventionService):
    """Render the create convention tab."""
    add_vertical_space(1)

    st.markdown("### Create New Naming Convention")

    # Convention details
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Convention Name *", placeholder="e.g., Simple VM Naming", help="Unique name for this convention"
        )

    with col2:
        pattern = st.text_input(
            "Pattern *", placeholder="e.g., <prefix><sep><number>", help="Visual representation of the pattern"
        )

    description = st.text_area(
        "Description", placeholder="Describe the naming convention...", help="Optional description"
    )

    add_vertical_space(1)

    st.markdown("### Field Definitions")
    st.caption("Define fields in order from left to right (position 0, 1, 2, ...)")

    # Initialize fields in session state
    if "convention_fields" not in st.session_state:
        st.session_state.convention_fields = []

    # Add field button
    if st.button("➕ Add Field", use_container_width=False):
        st.session_state.convention_fields.append(
            {
                "position": len(st.session_state.convention_fields),
                "field_name": "",
                "length": 1,
                "description": "",
                "is_required": True,
                "possible_values": "",
            }
        )

    # Display existing fields
    if st.session_state.convention_fields:
        for idx, field in enumerate(st.session_state.convention_fields):
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                with col1:
                    field["field_name"] = st.text_input(
                        "Field Name",
                        value=field.get("field_name", ""),
                        key=f"field_name_{idx}",
                        placeholder="e.g., prefix, environment, number",
                    )

                with col2:
                    field["length"] = st.number_input(
                        "Length", value=field.get("length", 1), min_value=1, max_value=50, key=f"length_{idx}"
                    )

                with col3:
                    field["is_required"] = st.checkbox(
                        "Required", value=field.get("is_required", True), key=f"required_{idx}"
                    )

                with col4:
                    if st.button("🗑️", key=f"del_{idx}", help="Delete field"):
                        st.session_state.convention_fields.pop(idx)
                        st.rerun()

                col1, col2 = st.columns(2)

                with col1:
                    field["description"] = st.text_input(
                        "Description (optional)",
                        value=field.get("description", ""),
                        key=f"desc_{idx}",
                        placeholder="What does this field represent?",
                    )

                with col2:
                    field["possible_values"] = st.text_input(
                        "Possible Values (comma-separated, optional)",
                        value=field.get("possible_values", ""),
                        key=f"values_{idx}",
                        placeholder="e.g., vm, VM, test",
                    )

                st.caption(
                    f"Position: {idx} | "
                    f"Total chars so far: "
                    f"{sum(f['length'] for f in st.session_state.convention_fields[:idx+1])}"
                )
    else:
        st.info("👆 Click 'Add Field' to start defining fields")

    add_vertical_space(2)

    # Create button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        create_button = st.button(
            "✨ Create Convention",
            use_container_width=True,
            type="primary",
            disabled=not name or not pattern or not st.session_state.convention_fields,
        )

    if create_button:
        # Validate and create
        if not name or not pattern:
            st.error("❌ Please provide name and pattern")
            return

        if not st.session_state.convention_fields:
            st.error("❌ Please add at least one field")
            return

        # Prepare fields data
        fields_data = []
        for field in st.session_state.convention_fields:
            if not field["field_name"]:
                st.error(f"❌ Field at position {field['position']} has no name")
                return

            field_dict = {
                "field_name": field["field_name"],
                "position": field["position"],
                "length": field["length"],
                "is_required": field["is_required"],
                "description": field["description"] if field["description"] else None,
            }

            # Parse possible values
            if field["possible_values"]:
                values = [v.strip() for v in field["possible_values"].split(",") if v.strip()]
                if values:
                    field_dict["possible_values"] = values

            fields_data.append(field_dict)

        # Create convention
        try:
            with st.spinner("Creating convention..."):
                convention = service.create_convention(
                    name=name, pattern=pattern, fields=fields_data, description=description if description else None
                )

            st.success(f"✅ Created convention '{convention.name}' (ID: {convention.id})")
            st.balloons()

            # Clear form
            st.session_state.convention_fields = []

            add_vertical_space(1)
            if st.button("↩️ Back to List"):
                st.rerun()

        except PatternValidationError as e:
            st.error(f"❌ Validation Error: {e}")
        except NamingConventionError as e:
            st.error(f"❌ Error: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            st.exception(e)


def render_edit_convention(service: NamingConventionService, convention_id: int):
    """Render the edit convention interface."""
    add_vertical_space(1)

    # Get the convention to edit
    try:
        convention = service.get_convention(convention_id)
        if not convention:
            st.error(f"❌ Convention with ID {convention_id} not found")
            if st.button("↩️ Back to List"):
                st.session_state.edit_convention_id = None
                st.rerun()
            return
    except Exception as e:
        st.error(f"❌ Error loading convention: {e}")
        if st.button("↩️ Back to List"):
            st.session_state.edit_convention_id = None
            st.rerun()
        return

    # Header with back button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### ✏️ Edit Convention: {convention.name}")
    with col2:
        if st.button("↩️ Back", use_container_width=True):
            st.session_state.edit_convention_id = None
            st.rerun()

    add_vertical_space(1)

    # Convention details
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Convention Name *", value=convention.name, help="Unique name for this convention")

    with col2:
        pattern = st.text_input("Pattern *", value=convention.pattern, help="Visual representation of the pattern")

    description = st.text_area("Description", value=convention.description or "", help="Optional description")

    is_active = st.checkbox("Active", value=convention.is_active)

    add_vertical_space(1)

    st.markdown("### Field Definitions")
    st.caption("Fields are listed in order. You can modify existing fields below.")

    # Display and edit fields
    if convention.fields:
        for i, field in enumerate(sorted(convention.fields, key=lambda f: f.position)):
            with st.expander(f"📍 Position {field.position}: {field.field_name}", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.text_input("Field Name", value=field.field_name, key=f"edit_fname_{i}")

                with col2:
                    st.number_input("Length", min_value=1, value=field.length, key=f"edit_len_{i}")

                with col3:
                    st.checkbox("Required", value=field.is_required, key=f"edit_req_{i}")

                st.text_input("Description", value=field.description or "", key=f"edit_desc_{i}")

                # Possible values
                possible_vals = ""
                if field.possible_values and isinstance(field.possible_values, list):
                    possible_vals = ", ".join(field.possible_values)

                st.text_input("Possible Values (comma-separated)", value=possible_vals, key=f"edit_vals_{i}")

                st.text_input("Validation Regex", value=field.validation_regex or "", key=f"edit_regex_{i}")

    add_vertical_space(2)

    # Save button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Save Changes", use_container_width=True, type="primary"):
            # Validate inputs
            if not name or not pattern:
                st.error("❌ Name and Pattern are required")
                return

            # Prepare fields data
            fields_data = []
            for i, field in enumerate(sorted(convention.fields, key=lambda f: f.position)):
                field_name_val = st.session_state.get(f"edit_fname_{i}", field.field_name)

                if not field_name_val:
                    st.error(f"❌ Field at position {field.position} has no name")
                    return

                field_dict = {
                    "field_name": field_name_val,
                    "position": field.position,
                    "length": st.session_state.get(f"edit_len_{i}", field.length),
                    "is_required": st.session_state.get(f"edit_req_{i}", field.is_required),
                    "description": st.session_state.get(f"edit_desc_{i}", field.description),
                }

                # Parse possible values
                possible_values_val = st.session_state.get(f"edit_vals_{i}", "")
                if possible_values_val:
                    values = [v.strip() for v in possible_values_val.split(",") if v.strip()]
                    if values:
                        field_dict["possible_values"] = values

                # Validation regex
                regex_val = st.session_state.get(f"edit_regex_{i}", "")
                if regex_val:
                    field_dict["validation_regex"] = regex_val

                fields_data.append(field_dict)

            # Update convention
            try:
                with st.spinner("Updating convention..."):
                    # Delete existing convention and create new one
                    # (This is a simple approach - ideally would have an update method)
                    service.delete_convention(convention_id)
                    new_convention = service.create_convention(
                        name=name,
                        pattern=pattern,
                        fields=fields_data,
                        description=description if description else None,
                        is_active=is_active,
                    )

                st.success(f"✅ Updated convention '{new_convention.name}'!")
                st.balloons()

                add_vertical_space(1)
                if st.button("↩️ Back to List", key="back_after_save"):
                    st.session_state.edit_convention_id = None
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error updating convention: {e}")
                st.exception(e)


def render_documentation():
    """Render the documentation tab."""
    add_vertical_space(1)

    st.markdown(
        """
    ## 📖 Naming Convention Documentation

    ### What are Naming Conventions?

    Naming conventions allow you to define structured patterns for VM names, making it easier to:
    - **Categorize** VMs by environment, application, or location
    - **Filter** VMs based on naming segments
    - **Plan migrations** by grouping VMs with similar naming patterns
    - **Analyze** your VM inventory structure

    ### Pattern Structure

    A naming convention consists of **fields** that define segments of a VM name:
    - Each field has a **position** (0, 1, 2, ...)
    - Each field has a fixed **length** (number of characters)
    - Fields are extracted in order from the VM name

    ### Example Conventions

    #### 1. Simple Pattern: `vm-###`
    ```
    Pattern: <prefix><sep><number>

    Fields:
    - prefix: position 0, length 2 (values: "vm", "VM")
    - separator: position 1, length 1 (value: "-")
    - number: position 2, length 3 (validates: 000-999)

    Matches: vm-001, vm-123, VM-999
    ```

    #### 2. Environment Pattern: `ENV-TYPE-####`
    ```
    Pattern: <env><sep1><type><sep2><number>

    Fields:
    - environment: position 0, length 3 (values: "DEV", "PRD", "TST")
    - separator1: position 1, length 1 (value: "-")
    - type: position 2, length 2 (values: "VM", "AP", "DB")
    - separator2: position 3, length 1 (value: "-")
    - number: position 4, length 4 (validates: 0000-9999)

    Matches: DEV-VM-0001, PRD-AP-1234, TST-DB-9999
    ```

    ### Field Configuration

    - **Field Name**: Semantic name (e.g., "environment", "datacenter")
    - **Position**: Order in the name (starts at 0)
    - **Length**: Fixed number of characters
    - **Required**: Whether field must have a value
    - **Possible Values**: Optional list of valid values
    - **Validation Regex**: Optional regex pattern for validation

    ### Using Conventions

    1. **Create** a convention with the pattern and fields
    2. **Analyze** your VM inventory to parse names
    3. **View results** in the Naming Analysis page
    4. **Filter** VMs by field values
    5. **Export** analysis results for reporting
    6. **Plan migrations** by grouping VMs with similar patterns

    ### Tips

    - Start with simple patterns and test them
    - Use JSON files to define complex conventions
    - Review analysis results to refine patterns
    - Use possible values to validate extracted fields
    - Consider using regex validation for numeric fields

    ### CLI Alternative

    You can also manage conventions via CLI:
    ```bash
    # List conventions
    uv run python -m src.cli naming-convention list

    # Create from JSON file
    uv run python -m src.cli naming-convention create --from-file pattern.json

    # Analyze VMs
    uv run python -m src.cli naming-convention analyze 1

    # Export results
    uv run python -m src.cli naming-convention export 1 output.csv
    ```
    """
    )
