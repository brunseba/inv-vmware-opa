"""Database Backup & Restore page."""

import streamlit as st
from pathlib import Path
from datetime import datetime
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def render(db_url: str):
    """Render the backup & restore page."""
    colored_header(
        label="💾 Database Backup & Restore",
        description="Complete database backup and restore operations",
        color_name="blue-70"
    )
    
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Create tabs
        tab1, tab2 = st.tabs(["📦 Full Database Backup", "🔄 Restore Database"])
        
        # =====================================================================
        # Tab 1: Database Backup
        # =====================================================================
        with tab1:
            colored_header(
                label="Full Database Backup",
                description="Create a complete backup of all data",
                color_name="green-70"
            )
            
            st.info("💡 This creates a complete backup of the entire database including all VMs, labels, and assignments.")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                default_db_backup = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                db_backup_filename = st.text_input(
                    "Backup Filename",
                    value=default_db_backup,
                    help="Name for the backup file",
                    key="db_backup_filename"
                )
            
            with col2:
                st.write("")
                st.write("")
                if st.button("💾 Create Backup", type="primary", key="create_db_backup", width="stretch"):
                    try:
                        from src.services.backup_service import BackupService
                        backup_service = BackupService(session)
                        
                        backup_path = Path("data/backups") / db_backup_filename
                        
                        with st.spinner("Creating database backup..."):
                            stats = backup_service.backup_database(backup_path, db_url)
                        
                        st.success(f"✅ Database backup created successfully!")
                        
                        # Show stats in columns
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("Tables", stats['tables'])
                        with metric_col2:
                            st.metric("Size", f"{stats['size_bytes'] / 1024 / 1024:.2f} MB")
                        with metric_col3:
                            st.metric("Type", stats['database_type'])
                        
                        st.caption(f"📁 Saved to: {stats['backup_file']}")
                        
                        add_vertical_space(1)
                        
                        # Offer download
                        with open(backup_path, 'rb') as f:
                            db_backup_data = f.read()
                        
                        st.download_button(
                            label="⬇️ Download Backup File",
                            data=db_backup_data,
                            file_name=db_backup_filename,
                            mime="application/octet-stream",
                            type="primary",
                            width="stretch"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error creating database backup: {e}")
            
            add_vertical_space(2)
            st.divider()
            
            # List existing backups
            st.write("**📋 Recent Backups:**")
            
            backup_dir = Path("data/backups")
            if backup_dir.exists():
                db_backups = list(backup_dir.glob("database_backup_*.db"))
                db_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                if db_backups:
                    for backup_file in db_backups[:10]:  # Show last 10
                        with st.expander(f"📄 {backup_file.name}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.caption(f"**Size:** {backup_file.stat().st_size / 1024 / 1024:.2f} MB")
                            
                            with col2:
                                mod_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                                st.caption(f"**Modified:** {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            with col3:
                                with open(backup_file, 'rb') as f:
                                    st.download_button(
                                        label="⬇️ Download",
                                        data=f.read(),
                                        file_name=backup_file.name,
                                        mime="application/octet-stream",
                                        key=f"download_{backup_file.name}"
                                    )
                else:
                    st.info("No backup files found")
            else:
                st.info("Backup directory not found. Create a backup to get started.")
        
        # =====================================================================
        # Tab 2: Restore Database
        # =====================================================================
        with tab2:
            colored_header(
                label="Restore Database",
                description="Restore from a backup file",
                color_name="red-70"
            )
            
            st.error("⚠️ **WARNING:** This will replace the entire database with the backup. All current data will be overwritten!")
            st.caption("The current database will be automatically backed up before restore.")
            
            add_vertical_space(1)
            
            # File uploader
            uploaded_db_file = st.file_uploader(
                "Choose database backup file",
                type=['db', 'sqlite', 'sqlite3'],
                help="Select a database backup file to restore",
                key="restore_db_file"
            )
            
            if uploaded_db_file:
                st.write("**📊 Backup File Information:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Filename", uploaded_db_file.name)
                with col2:
                    st.metric("Size", f"{uploaded_db_file.size / 1024 / 1024:.2f} MB")
                
                add_vertical_space(1)
                
                # Restore button with confirmation
                if st.button("🔄 Restore Database", type="primary", key="restore_db_backup", width="stretch"):
                    import tempfile
                    
                    # Double confirmation
                    confirm_db_key = "confirm_db_restore"
                    
                    if st.session_state.get(confirm_db_key):
                        try:
                            from src.services.backup_service import BackupService
                            backup_service = BackupService(session)
                            
                            # Save uploaded file temporarily
                            with tempfile.NamedTemporaryFile(mode='wb', suffix='.db', delete=False) as tmp:
                                tmp.write(uploaded_db_file.read())
                                tmp_path = Path(tmp.name)
                            
                            with st.spinner("Restoring database... Please wait."):
                                stats = backup_service.restore_database(tmp_path, db_url, confirm=True)
                            
                            # Clean up
                            tmp_path.unlink()
                            
                            st.success("✅ Database restore complete!")
                            
                            # Show results
                            result_col1, result_col2 = st.columns(2)
                            with result_col1:
                                st.info(f"**Restored from:**\n{stats['restored_from']}")
                            with result_col2:
                                st.info(f"**Restored to:**\n{stats['restored_to']}")
                            
                            st.metric("Database Size", f"{stats['size_bytes'] / 1024 / 1024:.2f} MB")
                            
                            add_vertical_space(1)
                            st.warning("🔄 **Please refresh the page** to see the restored data")
                            
                            # Clear confirmation
                            st.session_state[confirm_db_key] = False
                            
                            # Offer refresh button
                            if st.button("🔄 Refresh Page Now", type="primary"):
                                st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error restoring database: {e}")
                            if 'tmp_path' in locals() and tmp_path.exists():
                                tmp_path.unlink()
                    else:
                        # First click - show warning
                        st.session_state[confirm_db_key] = True
                        st.error("⚠️ ⚠️ **DANGER:** Click the button again to CONFIRM. This will REPLACE ALL DATA!")
                        st.caption("This is a safety measure to prevent accidental data loss.")
            else:
                st.info("👆 Upload a database backup file to begin the restore process")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        with st.expander("Show error details"):
            st.code(traceback.format_exc())
    finally:
        session.close()
