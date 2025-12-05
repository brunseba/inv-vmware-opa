"""VM Label Analysis page - Analyze VMs by labels with advanced filtering."""

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from src.models import VirtualMachine, Label, VMLabel


def render(db_url: str):
    """Render the VM label analysis page."""
    colored_header(
        label="🏷️ VM Label Analysis",
        description="Analyze and filter VMs based on labels",
        color_name="blue-70",
    )

    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # Get all labels
        labels = session.query(Label).order_by(Label.name).all()

        if not labels:
            st.warning("⚠️ No labels found in the database. Import data or create labels first.")
            return

        add_vertical_space(1)

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(
            ["🔍 Label Filter & Search", "📊 Label Statistics", "🎯 Label Coverage", "📈 Label Analysis"]
        )

        # ========== TAB 1: Label Filter & Search ==========
        with tab1:
            render_label_filter(session, labels)

        # ========== TAB 2: Label Statistics ==========
        with tab2:
            render_label_statistics(session, labels)

        # ========== TAB 3: Label Coverage ==========
        with tab3:
            render_label_coverage(session, labels)

        # ========== TAB 4: Label Analysis ==========
        with tab4:
            render_label_analysis(session, labels)

        session.close()

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)


def render_label_filter(session, labels):
    """Render label filtering and VM search."""
    add_vertical_space(1)

    st.markdown("### 🔍 Filter VMs by Labels")

    # Label selection
    label_names = [label.name for label in labels]

    # Filter mode
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_mode = st.radio(
            "Filter Mode",
            options=[
                "Include (VMs with ANY selected labels)",
                "Include (VMs with ALL selected labels)",
                "Exclude (VMs without selected labels)",
            ],
            horizontal=True,
        )

    with col2:
        naming_convention_filter = st.checkbox(
            "🏷️ Naming Convention Labels Only",
            value=False,
            help="Show only labels created from naming conventions (nc:*)",
        )

    add_vertical_space(1)

    # Filter labels based on naming convention checkbox
    if naming_convention_filter:
        filtered_labels = [lbl for lbl in labels if lbl.name.startswith("nc:")]
        if not filtered_labels:
            st.info("📝 No naming convention labels found. " "Create them using the Naming Analysis page.")
            return
        label_names = [label.name for label in filtered_labels]

    # Multi-select for labels
    selected_labels = st.multiselect(
        "Select Labels to Filter", options=label_names, help="Choose one or more labels to filter VMs"
    )

    add_vertical_space(1)

    # Additional filters
    st.markdown("**Additional Filters:**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]
        selected_dc = st.selectbox("Datacenter", ["All"] + sorted(datacenters))

    with col2:
        clusters = [c[0] for c in session.query(VirtualMachine.cluster).distinct().all() if c[0]]
        selected_cluster = st.selectbox("Cluster", ["All"] + sorted(clusters))

    with col3:
        power_states = ["All", "poweredOn", "poweredOff", "suspended"]
        selected_power = st.selectbox("Power State", power_states)

    with col4:
        max_results = st.number_input("Max Results", min_value=10, max_value=10000, value=1000, step=100)

    add_vertical_space(1)

    # Apply filters button
    if st.button("🔍 Apply Filters", type="primary", use_container_width=True):
        # Build base query
        query = session.query(VirtualMachine)

        # Apply label filters
        if selected_labels:
            if "ANY" in filter_mode:
                # VMs with ANY of the selected labels
                query = query.join(VMLabel).join(Label).filter(Label.name.in_(selected_labels))
            elif "ALL" in filter_mode:
                # VMs with ALL of the selected labels - use HAVING COUNT approach
                from sqlalchemy import func

                # Get label IDs for the selected label names
                label_ids = [lbl.id for lbl in labels if lbl.name in selected_labels]

                # Subquery: VMs that have all the selected labels
                subquery = (
                    session.query(VMLabel.vm_id)
                    .filter(VMLabel.label_id.in_(label_ids))
                    .group_by(VMLabel.vm_id)
                    .having(func.count(func.distinct(VMLabel.label_id)) == len(label_ids))
                )

                query = query.filter(VirtualMachine.id.in_(subquery))
            else:  # Exclude
                # VMs without any of the selected labels
                subquery = session.query(VMLabel.vm_id).join(Label).filter(Label.name.in_(selected_labels)).distinct()
                query = query.filter(~VirtualMachine.id.in_(subquery))

        # Apply additional filters
        if selected_dc != "All":
            query = query.filter(VirtualMachine.datacenter == selected_dc)
        if selected_cluster != "All":
            query = query.filter(VirtualMachine.cluster == selected_cluster)
        if selected_power != "All":
            query = query.filter(VirtualMachine.powerstate == selected_power)

        # Get results
        results = query.distinct().limit(max_results).all()

        add_vertical_space(1)

        # Display results
        if not results:
            st.warning("⚠️ No VMs found matching the filters")
        else:
            st.success(f"✅ Found {len(results)} VM(s)")

            # Prepare data for display
            vm_data = []
            for vm in results:
                # Get labels for this VM
                vm_labels = session.query(Label.name).join(VMLabel).filter(VMLabel.vm_id == vm.id).all()
                vm_labels_str = ", ".join([label[0] for label in vm_labels])

                vm_data.append(
                    {
                        "Name": vm.vm,
                        "Datacenter": vm.datacenter or "",
                        "Cluster": vm.cluster or "",
                        "Power State": vm.powerstate or "",
                        "CPUs": vm.cpus or 0,
                        "Memory (GB)": round(vm.memory / 1024, 2) if vm.memory else 0,
                        "Labels": vm_labels_str,
                    }
                )

            df = pd.DataFrame(vm_data)

            # Display table
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Export option
            add_vertical_space(1)
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name="vm_label_filter_results.csv",
                mime="text/csv",
                use_container_width=True,
            )


def render_label_statistics(session, labels):
    """Render label statistics."""
    add_vertical_space(1)

    st.markdown("### 📊 Label Usage Statistics")

    # Get label usage stats
    label_stats = []
    for label in labels:
        count = session.query(VMLabel).filter(VMLabel.label_id == label.id).count()
        label_stats.append(
            {
                "Label": label.name,
                "Value": label.value or "",
                "VM Count": count,
                "Category": label.category or "Uncategorized",
            }
        )

    df_stats = pd.DataFrame(label_stats)
    df_stats = df_stats.sort_values("VM Count", ascending=False)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Labels", len(labels))
    with col2:
        used_labels = len([ls for ls in label_stats if ls["VM Count"] > 0])
        st.metric("Labels in Use", used_labels)
    with col3:
        unused_labels = len([ls for ls in label_stats if ls["VM Count"] == 0])
        st.metric("Unused Labels", unused_labels)
    with col4:
        total_assignments = sum([ls["VM Count"] for ls in label_stats])
        st.metric("Total Assignments", total_assignments)

    add_vertical_space(1)

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_unused = st.checkbox("Show unused labels", value=False)
    with col2:
        category_filter = st.selectbox("Category Filter", ["All"] + sorted(df_stats["Category"].unique().tolist()))

    # Apply filters
    filtered_df = df_stats.copy()
    if not show_unused:
        filtered_df = filtered_df[filtered_df["VM Count"] > 0]
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]

    add_vertical_space(1)

    # Display table
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    add_vertical_space(1)

    # Top labels chart
    if len(filtered_df) > 0:
        st.markdown("#### 🏆 Top 20 Most Used Labels")
        top_labels = filtered_df.head(20)
        fig = px.bar(
            top_labels,
            x="VM Count",
            y="Label",
            orientation="h",
            title="Label Usage",
            color="VM Count",
            color_continuous_scale="Blues",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)


def render_label_coverage(session, labels):
    """Render label coverage analysis."""
    add_vertical_space(1)

    st.markdown("### 🎯 Label Coverage Analysis")

    # Get total VMs
    total_vms = session.query(VirtualMachine).count()

    if total_vms == 0:
        st.warning("⚠️ No VMs found in the database")
        return

    # Get VMs with/without labels
    vms_with_labels = session.query(VirtualMachine.id).join(VMLabel).distinct().count()
    vms_without_labels = total_vms - vms_with_labels

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total VMs", f"{total_vms:,}")
    with col2:
        coverage_pct = (vms_with_labels / total_vms * 100) if total_vms > 0 else 0
        st.metric("VMs with Labels", f"{vms_with_labels:,}", delta=f"{coverage_pct:.1f}%")
    with col3:
        st.metric("VMs without Labels", f"{vms_without_labels:,}")
    with col4:
        avg_labels = session.query(func.count(VMLabel.label_id)).join(VirtualMachine).group_by(VirtualMachine.id).all()
        avg_labels_per_vm = sum([count[0] for count in avg_labels]) / len(avg_labels) if avg_labels else 0
        st.metric("Avg Labels/VM", f"{avg_labels_per_vm:.1f}")

    add_vertical_space(1)

    # Coverage by datacenter
    st.markdown("#### 📍 Coverage by Datacenter")

    datacenter_coverage = []
    datacenters = [dc[0] for dc in session.query(VirtualMachine.datacenter).distinct().all() if dc[0]]

    for dc in datacenters:
        dc_vms = session.query(VirtualMachine).filter(VirtualMachine.datacenter == dc).count()
        dc_labeled = (
            session.query(VirtualMachine.id).filter(VirtualMachine.datacenter == dc).join(VMLabel).distinct().count()
        )
        dc_coverage = (dc_labeled / dc_vms * 100) if dc_vms > 0 else 0

        datacenter_coverage.append(
            {"Datacenter": dc, "Total VMs": dc_vms, "Labeled VMs": dc_labeled, "Coverage %": dc_coverage}
        )

    if datacenter_coverage:
        df_dc = pd.DataFrame(datacenter_coverage)
        st.dataframe(df_dc, use_container_width=True, hide_index=True)

        add_vertical_space(1)

        # Chart
        fig = px.bar(
            df_dc, x="Datacenter", y=["Labeled VMs", "Total VMs"], barmode="group", title="Label Coverage by Datacenter"
        )
        st.plotly_chart(fig, use_container_width=True)

    add_vertical_space(1)

    # Naming convention label coverage
    st.markdown("#### 🏷️ Naming Convention Label Coverage")

    nc_labels = [lbl for lbl in labels if lbl.name.startswith("nc:")]
    if nc_labels:
        vms_with_nc_labels = (
            session.query(VirtualMachine.id)
            .join(VMLabel)
            .join(Label)
            .filter(Label.name.like("nc:%"))
            .distinct()
            .count()
        )

        nc_coverage = (vms_with_nc_labels / total_vms * 100) if total_vms > 0 else 0

        col1, col2 = st.columns(2)
        with col1:
            st.metric("NC Labels", len(nc_labels))
        with col2:
            st.metric("VMs with NC Labels", f"{vms_with_nc_labels:,}", delta=f"{nc_coverage:.1f}%")
    else:
        st.info("📝 No naming convention labels found. Create them using the Naming Analysis page.")


def render_label_analysis(session, labels):
    """Render advanced label analysis."""
    add_vertical_space(1)

    st.markdown("### 📈 Advanced Label Analysis")

    # Label co-occurrence analysis
    st.markdown("#### 🔗 Label Co-occurrence")
    st.caption("Find which labels frequently appear together on VMs")

    # Select a label to analyze
    label_names = [label.name for label in labels]
    selected_label = st.selectbox("Select a label to analyze", options=label_names)

    if selected_label:
        # Find VMs with this label
        label = session.query(Label).filter(Label.name == selected_label).first()
        vms_with_label = session.query(VirtualMachine.id).join(VMLabel).filter(VMLabel.label_id == label.id).all()
        vm_ids = [vm[0] for vm in vms_with_label]

        if not vm_ids:
            st.info(f"📝 No VMs have the label '{selected_label}'")
        else:
            st.info(f"📊 Found {len(vm_ids)} VMs with label '{selected_label}'")

            # Find co-occurring labels
            co_occurring = (
                session.query(Label.name, func.count(VMLabel.vm_id).label("count"))
                .join(VMLabel)
                .filter(VMLabel.vm_id.in_(vm_ids))
                .filter(Label.name != selected_label)
                .group_by(Label.name)
                .order_by(func.count(VMLabel.vm_id).desc())
                .limit(20)
                .all()
            )

            if co_occurring:
                df_cooccur = pd.DataFrame(co_occurring, columns=["Co-occurring Label", "Count"])
                df_cooccur["Percentage"] = (df_cooccur["Count"] / len(vm_ids) * 100).round(1)

                add_vertical_space(1)

                col1, col2 = st.columns([2, 1])

                with col1:
                    fig = px.bar(
                        df_cooccur.head(15),
                        x="Count",
                        y="Co-occurring Label",
                        orientation="h",
                        title=f"Labels Co-occurring with '{selected_label}'",
                        color="Percentage",
                        color_continuous_scale="Viridis",
                    )
                    fig.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.dataframe(df_cooccur, use_container_width=True, hide_index=True)

    add_vertical_space(2)

    # Label distribution by category
    st.markdown("#### 📊 Label Distribution by Category")

    category_dist = []
    categories = session.query(Label.category).distinct().all()

    for cat in categories:
        cat_name = cat[0] if cat[0] else "Uncategorized"
        count = session.query(Label).filter(Label.category == cat[0]).count()
        category_dist.append({"Category": cat_name, "Count": count})

    if category_dist:
        df_cat = pd.DataFrame(category_dist)

        fig = px.pie(df_cat, values="Count", names="Category", title="Label Distribution by Category")
        st.plotly_chart(fig, use_container_width=True)
