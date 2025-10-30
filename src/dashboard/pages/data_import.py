"""Data Import & Database Management Page."""

import streamlit as st
from pathlib import Path
import tempfile
import os
from datetime import datetime
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Import loader and models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.loader import load_excel_to_db, get_sheet_names
from src.models import Base, VirtualMachine


def render(db_url: str):
    """Render the data import page.
    
    Args:
        db_url: Database connection URL
    """
    colored_header(
        label="📥 Data Import & Database Management",
        description="Load VMware inventory data and manage database",
        color_name="blue-70"
    )
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Import Data", "🗄️ Database Info", "🧹 Database Maintenance"])
    
    # =====================================================================
    # Tab 1: Import Data
    # =====================================================================
    with tab1:
        st.write("### Upload and Import VMware Inventory Data")
        
        add_vertical_space(1)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=['xlsx', 'xls'],
            help="Upload VMware vSphere inventory export (RVTools or similar format)"
        )
        
        if uploaded_file is not None:
            # Show file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Name", uploaded_file.name)
            with col2:
                file_size_mb = uploaded_file.size / (1024 * 1024)
                st.metric("File Size", f"{file_size_mb:.2f} MB")
            with col3:
                st.metric("Upload Time", datetime.now().strftime("%H:%M:%S"))
            
            add_vertical_space(1)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = Path(tmp_file.name)
            
            try:
                # Get sheet names
                sheet_names = get_sheet_names(tmp_path)
                
                st.write("**Import Configuration:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Sheet selection
                    selected_sheet = st.selectbox(
                        "Select Sheet",
                        options=sheet_names,
                        help="Choose which sheet to import"
                    )
                
                with col2:
                    # Clear existing data option
                    clear_existing = st.checkbox(
                        "Clear Existing Data",
                        value=True,
                        help="Remove all existing data before import"
                    )
                
                add_vertical_space(1)
                
                # Preview button
                if st.button("👁️ Preview Data", type="secondary", use_container_width=True):
                    try:
                        import pandas as pd
                        df = pd.read_excel(tmp_path, sheet_name=selected_sheet, nrows=10)
                        
                        st.write(f"**Preview (first 10 rows from '{selected_sheet}'):**")
                        st.dataframe(df, use_container_width=True)
                        
                        st.info(f"📊 Total columns: {len(df.columns)} | Preview rows: {len(df)}")
                    except Exception as e:
                        st.error(f"Error previewing data: {e}")
                
                add_vertical_space(1)
                
                # Import button
                if st.button("🚀 Import Data", type="primary", use_container_width=True):
                    with st.spinner("Importing data... This may take a few minutes for large files."):
                        try:
                            # Load data
                            records_loaded = load_excel_to_db(
                                tmp_path,
                                db_url,
                                clear_existing=clear_existing,
                                sheet_name=selected_sheet
                            )
                            
                            st.success(f"✅ Successfully imported {records_loaded:,} records!")
                            
                            # Show import summary
                            st.balloons()
                            
                            with st.expander("📋 Import Summary", expanded=True):
                                summary_col1, summary_col2 = st.columns(2)
                                
                                with summary_col1:
                                    st.metric("Records Imported", f"{records_loaded:,}")
                                    st.metric("Source Sheet", selected_sheet)
                                
                                with summary_col2:
                                    st.metric("Database", "Connected" if db_url else "N/A")
                                    st.metric("Mode", "Replace" if clear_existing else "Append")
                                
                                st.info("💡 **Next Steps:** Navigate to Overview or VM Explorer to analyze your data")
                            
                            # Clear cache after import
                            st.cache_data.clear()
                            
                        except Exception as e:
                            st.error(f"❌ Import failed: {e}")
                            
                            with st.expander("🔍 Error Details"):
                                st.exception(e)
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        else:
            # Show instructions when no file uploaded
            st.info("📂 **No file uploaded yet**")
            
            with st.expander("📖 Import Instructions", expanded=True):
                st.markdown("""
                ### How to Import Data
                
                1. **Export from vSphere**: Use RVTools or similar tool to export your VMware inventory
                2. **Upload File**: Click "Browse files" above to select your Excel file
                3. **Select Sheet**: Choose the sheet containing VM data (usually "vInfo" or "Sheet1")
                4. **Configure Import**: 
                   - ✅ Check "Clear Existing Data" to replace all data (recommended for updates)
                   - ❌ Uncheck to append to existing data
                5. **Preview**: Review data structure before importing
                6. **Import**: Click "Import Data" to load into database
                
                ### Supported Formats
                
                - **RVTools** vInfo exports (recommended)
                - **PowerCLI** VM inventory exports
                - **Custom exports** with standard VMware fields
                
                ### Required Columns
                
                At minimum, your Excel file should include:
                - `VM` (VM name)
                - `Powerstate`
                - `CPUs`
                - `Memory`
                - `Datacenter`
                - `Cluster`
                
                ### Tips
                
                - 💾 **Backup First**: Create a database backup before importing (use Database Backup page)
                - 🔄 **Regular Updates**: Import fresh data weekly or monthly
                - 📊 **Large Files**: Files >50MB may take several minutes to process
                - ⚠️ **Network Timeouts**: Upload from local files rather than network drives
                """)
    
    # =====================================================================
    # Tab 2: Database Info
    # =====================================================================
    with tab2:
        st.write("### Database Information & Statistics")
        
        add_vertical_space(1)
        
        try:
            engine = create_engine(db_url, echo=False)
            inspector = inspect(engine)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            
            # Connection info
            st.write("**Connection Details:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Database URL", db_url.split('://')[0].upper())
                st.metric("Status", "✅ Connected")
            
            with col2:
                # Database file size (for SQLite)
                if db_url.startswith('sqlite'):
                    db_path = db_url.replace('sqlite:///', '')
                    if os.path.exists(db_path):
                        size_mb = os.path.getsize(db_path) / (1024 * 1024)
                        st.metric("Database Size", f"{size_mb:.2f} MB")
                    else:
                        st.metric("Database Size", "N/A")
            
            add_vertical_space(2)
            
            # Table statistics
            st.write("**Tables & Record Counts:**")
            
            tables = inspector.get_table_names()
            
            if tables:
                table_data = []
                for table_name in tables:
                    try:
                        count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                        table_data.append({
                            "Table": table_name,
                            "Records": f"{count:,}"
                        })
                    except Exception as e:
                        table_data.append({
                            "Table": table_name,
                            "Records": "Error"
                        })
                
                import pandas as pd
                df_tables = pd.DataFrame(table_data)
                st.dataframe(df_tables, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ No tables found. Import data to create database structure.")
            
            add_vertical_space(2)
            
            # VM statistics (if data exists)
            vm_count = session.query(VirtualMachine).count()
            
            if vm_count > 0:
                st.write("**VM Inventory Statistics:**")
                
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                
                with stat_col1:
                    total_vms = vm_count
                    st.metric("Total VMs", f"{total_vms:,}")
                
                with stat_col2:
                    powered_on = session.query(VirtualMachine).filter(
                        VirtualMachine.powerstate == 'poweredOn'
                    ).count()
                    st.metric("Powered On", f"{powered_on:,}")
                
                with stat_col3:
                    datacenters = session.query(VirtualMachine.datacenter).distinct().count()
                    st.metric("Datacenters", f"{datacenters:,}")
                
                with stat_col4:
                    clusters = session.query(VirtualMachine.cluster).distinct().count()
                    st.metric("Clusters", f"{clusters:,}")
                
                add_vertical_space(1)
                
                # Additional stats
                with st.expander("📊 Detailed Statistics"):
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.write("**Resource Totals:**")
                        total_cpus = session.query(text("SUM(cpus)")).select_from(VirtualMachine).scalar() or 0
                        total_memory = session.query(text("SUM(memory)")).select_from(VirtualMachine).scalar() or 0
                        st.write(f"- Total vCPUs: {total_cpus:,}")
                        st.write(f"- Total Memory: {total_memory / 1024:.0f} GB")
                    
                    with detail_col2:
                        st.write("**VM States:**")
                        powered_off = session.query(VirtualMachine).filter(
                            VirtualMachine.powerstate == 'poweredOff'
                        ).count()
                        suspended = session.query(VirtualMachine).filter(
                            VirtualMachine.powerstate == 'suspended'
                        ).count()
                        st.write(f"- Powered Off: {powered_off:,}")
                        st.write(f"- Suspended: {suspended:,}")
            
            session.close()
            
        except Exception as e:
            st.error(f"❌ Error connecting to database: {e}")
            
            with st.expander("🔍 Connection Details"):
                st.write(f"**Database URL:** `{db_url}`")
                st.exception(e)
    
    # =====================================================================
    # Tab 3: Database Maintenance
    # =====================================================================
    with tab3:
        st.write("### Database Maintenance Operations")
        
        add_vertical_space(1)
        
        # Dangerous operations warning
        st.warning("⚠️ **Warning:** These operations can permanently modify or delete data. Use with caution!")
        
        add_vertical_space(2)
        
        # Clear all data
        st.write("**🗑️ Clear All Data**")
        st.caption("Remove VM records and optionally clear labels")
        
        # Clear mode selection
        clear_mode = st.radio(
            "Select what to clear:",
            [
                "VM Data Only (Preserve all labels)",
                "VM Data + Label Mappings (Preserve label definitions)",
                "Everything (VM Data + All Labels)"
            ],
            key="clear_mode",
            help="Choose what data to remove from the database"
        )
        
        # Show what will be affected
        with st.expander("ℹ️ What will be deleted?"):
            if clear_mode == "VM Data Only (Preserve all labels)":
                st.write("**Will Delete:**")
                st.write("- ✅ All VM records")
                st.write("\n**Will Preserve:**")
                st.write("- ✅ Label definitions (Label table)")
                st.write("- ✅ VM label assignments (VMLabel table)")
                st.write("- ✅ Folder label assignments (FolderLabel table)")
                st.info("💡 Use this when you want to reload VM data but keep your labelling work intact")
            
            elif clear_mode == "VM Data + Label Mappings (Preserve label definitions)":
                st.write("**Will Delete:**")
                st.write("- ✅ All VM records")
                st.write("- ✅ VM label assignments (VMLabel table)")
                st.write("- ✅ Folder label assignments (FolderLabel table)")
                st.write("\n**Will Preserve:**")
                st.write("- ✅ Label definitions (Label table)")
                st.info("💡 Use this when you want to reload data and reassign labels, but keep label definitions")
            
            else:  # Everything
                st.write("**Will Delete:**")
                st.write("- ✅ All VM records")
                st.write("- ✅ All label definitions (Label table)")
                st.write("- ✅ VM label assignments (VMLabel table)")
                st.write("- ✅ Folder label assignments (FolderLabel table)")
                st.warning("⚠️ This will completely reset your database - all data and labels will be lost!")
        
        add_vertical_space(1)
        
        if st.button("Clear Data", type="secondary"):
            st.warning(f"⚠️ **Confirmation Required**")
            st.write(f"You selected: **{clear_mode}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Yes, Clear Data", type="primary"):
                    try:
                        from src.models import Label, VMLabel, FolderLabel
                        
                        engine = create_engine(db_url, echo=False)
                        SessionLocal = sessionmaker(bind=engine)
                        session = SessionLocal()
                        
                        # Count before deletion
                        vm_count = session.query(VirtualMachine).count()
                        
                        results = []
                        
                        # Delete VM data
                        session.query(VirtualMachine).delete()
                        results.append(f"✅ Deleted {vm_count:,} VM records")
                        
                        # Handle labels based on mode
                        if clear_mode == "VM Data + Label Mappings (Preserve label definitions)":
                            # Delete label mappings only
                            vm_label_count = session.query(VMLabel).count()
                            folder_label_count = session.query(FolderLabel).count()
                            
                            session.query(VMLabel).delete()
                            session.query(FolderLabel).delete()
                            
                            results.append(f"✅ Deleted {vm_label_count:,} VM label mappings")
                            results.append(f"✅ Deleted {folder_label_count:,} folder label mappings")
                            results.append(f"ℹ️ Preserved label definitions")
                        
                        elif clear_mode == "Everything (VM Data + All Labels)":
                            # Delete everything including label definitions
                            label_count = session.query(Label).count()
                            vm_label_count = session.query(VMLabel).count()
                            folder_label_count = session.query(FolderLabel).count()
                            
                            # Delete in correct order (mappings first, then definitions)
                            session.query(VMLabel).delete()
                            session.query(FolderLabel).delete()
                            session.query(Label).delete()
                            
                            results.append(f"✅ Deleted {vm_label_count:,} VM label mappings")
                            results.append(f"✅ Deleted {folder_label_count:,} folder label mappings")
                            results.append(f"✅ Deleted {label_count:,} label definitions")
                        else:
                            # VM Data Only - labels preserved
                            results.append(f"ℹ️ Preserved all labels and mappings")
                        
                        session.commit()
                        session.close()
                        
                        st.success(f"✅ Clear operation completed!")
                        for result in results:
                            st.write(result)
                        
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        session.rollback()
            
            with col2:
                if st.button("❌ Cancel"):
                    st.rerun()
        
        add_vertical_space(2)
        st.divider()
        add_vertical_space(2)
        
        # Rebuild database
        st.write("**🔨 Rebuild Database Schema**")
        st.caption("Recreate all database tables (data will be preserved if possible)")
        
        if st.button("Rebuild Schema", type="secondary"):
            try:
                engine = create_engine(db_url, echo=False)
                Base.metadata.create_all(engine)
                st.success("✅ Database schema rebuilt successfully")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        add_vertical_space(2)
        st.divider()
        add_vertical_space(2)
        
        # Optimize database (SQLite only)
        if db_url.startswith('sqlite'):
            st.write("**⚡ Optimize Database**")
            st.caption("Vacuum and optimize SQLite database (reduces file size)")
            
            if st.button("Optimize Database", type="secondary"):
                try:
                    engine = create_engine(db_url, echo=False)
                    with engine.connect() as conn:
                        # Get size before
                        db_path = db_url.replace('sqlite:///', '')
                        size_before = os.path.getsize(db_path) / (1024 * 1024)
                        
                        # Vacuum
                        conn.execute(text("VACUUM"))
                        conn.commit()
                        
                        # Get size after
                        size_after = os.path.getsize(db_path) / (1024 * 1024)
                        saved = size_before - size_after
                        
                        st.success(f"✅ Database optimized!")
                        st.info(f"📊 Size before: {size_before:.2f} MB → After: {size_after:.2f} MB (Saved: {saved:.2f} MB)")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        add_vertical_space(2)
        st.divider()
        add_vertical_space(2)
        
        # Database health check
        st.write("**🏥 Database Health Check**")
        st.caption("Verify database integrity and connections")
        
        if st.button("Run Health Check", type="secondary"):
            with st.spinner("Running health check..."):
                health_status = []
                
                try:
                    engine = create_engine(db_url, echo=False)
                    
                    # Test 1: Connection
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                        health_status.append(("✅", "Database Connection", "Successful"))
                    except Exception as e:
                        health_status.append(("❌", "Database Connection", f"Failed: {e}"))
                    
                    # Test 2: Tables exist
                    try:
                        inspector = inspect(engine)
                        tables = inspector.get_table_names()
                        health_status.append(("✅", "Tables", f"{len(tables)} tables found"))
                    except Exception as e:
                        health_status.append(("❌", "Tables", f"Error: {e}"))
                    
                    # Test 3: Data accessible
                    try:
                        SessionLocal = sessionmaker(bind=engine)
                        session = SessionLocal()
                        count = session.query(VirtualMachine).count()
                        session.close()
                        health_status.append(("✅", "Data Access", f"{count:,} VM records"))
                    except Exception as e:
                        health_status.append(("❌", "Data Access", f"Error: {e}"))
                    
                    # Test 4: Write test
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                            conn.commit()
                        health_status.append(("✅", "Write Access", "Successful"))
                    except Exception as e:
                        health_status.append(("❌", "Write Access", f"Failed: {e}"))
                    
                except Exception as e:
                    health_status.append(("❌", "Health Check", f"Error: {e}"))
                
                # Display results
                st.write("**Health Check Results:**")
                for icon, check, result in health_status:
                    st.write(f"{icon} **{check}:** {result}")
