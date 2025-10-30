"""Backup and restore service for labels and assignments."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from src.models import Label, VMLabel, FolderLabel, VirtualMachine


class BackupService:
    """Service for backing up and restoring label data."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def export_labels(self, output_path: Path, include_metadata: bool = True) -> Dict:
        """
        Export all labels and assignments to JSON file.
        
        Args:
            output_path: Path to output JSON file
            include_metadata: Include metadata like timestamps
            
        Returns:
            Dictionary with export statistics
        """
        # Get all labels
        labels = self.session.query(Label).all()
        
        # Get all VM label assignments
        vm_labels = self.session.query(VMLabel, VirtualMachine.vm).join(
            VirtualMachine, VMLabel.vm_id == VirtualMachine.id
        ).all()
        
        # Get all folder label assignments
        folder_labels = self.session.query(FolderLabel).all()
        
        # Build export data structure
        export_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "labels": [],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        # Export label definitions
        for label in labels:
            label_data = {
                "id": label.id,
                "key": label.key,
                "value": label.value,
                "description": label.description,
                "color": label.color
            }
            
            if include_metadata:
                label_data["created_at"] = label.created_at.isoformat() if label.created_at else None
                label_data["updated_at"] = label.updated_at.isoformat() if label.updated_at else None
            
            export_data["labels"].append(label_data)
        
        # Export VM label assignments
        for vm_label, vm_name in vm_labels:
            vm_assignment = {
                "vm_name": vm_name,
                "label_id": vm_label.label_id,
                "inherited_from_folder": vm_label.inherited_from_folder,
                "source_folder_path": vm_label.source_folder_path,
                "assigned_by": vm_label.assigned_by
            }
            
            if include_metadata:
                vm_assignment["assigned_at"] = vm_label.assigned_at.isoformat() if vm_label.assigned_at else None
            
            export_data["vm_assignments"].append(vm_assignment)
        
        # Export folder label assignments
        for folder_label in folder_labels:
            folder_assignment = {
                "folder_path": folder_label.folder_path,
                "label_id": folder_label.label_id,
                "inherit_to_vms": folder_label.inherit_to_vms,
                "inherit_to_subfolders": folder_label.inherit_to_subfolders,
                "assigned_by": folder_label.assigned_by
            }
            
            if include_metadata:
                folder_assignment["assigned_at"] = folder_label.assigned_at.isoformat() if folder_label.assigned_at else None
            
            export_data["folder_assignments"].append(folder_assignment)
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Return statistics
        return {
            "labels": len(labels),
            "vm_assignments": len(vm_labels),
            "folder_assignments": len(folder_labels),
            "file": str(output_path),
            "size_bytes": output_path.stat().st_size
        }
    
    def import_labels(self, input_path: Path, mode: str = 'merge', 
                     clear_existing: bool = False) -> Dict:
        """
        Import labels and assignments from JSON file.
        
        Args:
            input_path: Path to input JSON file
            mode: Import mode - 'merge' (default), 'replace', 'skip_duplicates'
            clear_existing: Clear existing data before import (use with caution!)
            
        Returns:
            Dictionary with import statistics
        """
        # Load backup file
        with open(input_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        stats = {
            "labels_created": 0,
            "labels_updated": 0,
            "labels_skipped": 0,
            "vm_assignments_created": 0,
            "vm_assignments_skipped": 0,
            "folder_assignments_created": 0,
            "folder_assignments_skipped": 0,
            "errors": []
        }
        
        try:
            # Clear existing data if requested (DANGEROUS!)
            if clear_existing:
                self.session.query(VMLabel).delete()
                self.session.query(FolderLabel).delete()
                self.session.query(Label).delete()
                self.session.commit()
            
            # Import label definitions
            label_id_mapping = {}  # old_id -> new_id
            
            for label_data in import_data.get("labels", []):
                old_id = label_data["id"]
                
                # Check if label exists
                existing = self.session.query(Label).filter(
                    Label.key == label_data["key"],
                    Label.value == label_data["value"]
                ).first()
                
                if existing:
                    if mode == 'skip_duplicates':
                        stats["labels_skipped"] += 1
                        label_id_mapping[old_id] = existing.id
                        continue
                    elif mode == 'merge':
                        # Update existing label
                        if label_data.get("description"):
                            existing.description = label_data["description"]
                        if label_data.get("color"):
                            existing.color = label_data["color"]
                        existing.updated_at = datetime.utcnow()
                        stats["labels_updated"] += 1
                        label_id_mapping[old_id] = existing.id
                    elif mode == 'replace':
                        # Delete and recreate
                        self.session.delete(existing)
                        self.session.commit()
                        # Fall through to create new
                
                if not existing or mode == 'replace':
                    # Create new label
                    new_label = Label(
                        key=label_data["key"],
                        value=label_data["value"],
                        description=label_data.get("description"),
                        color=label_data.get("color")
                    )
                    self.session.add(new_label)
                    self.session.flush()  # Get the new ID
                    label_id_mapping[old_id] = new_label.id
                    stats["labels_created"] += 1
            
            self.session.commit()
            
            # Import VM label assignments
            for vm_assignment in import_data.get("vm_assignments", []):
                try:
                    vm_name = vm_assignment["vm_name"]
                    old_label_id = vm_assignment["label_id"]
                    
                    # Get VM
                    vm = self.session.query(VirtualMachine).filter(
                        VirtualMachine.vm == vm_name
                    ).first()
                    
                    if not vm:
                        stats["errors"].append(f"VM not found: {vm_name}")
                        continue
                    
                    # Map old label ID to new label ID
                    new_label_id = label_id_mapping.get(old_label_id)
                    if not new_label_id:
                        stats["errors"].append(f"Label ID {old_label_id} not found in mapping")
                        continue
                    
                    # Check if assignment exists
                    existing = self.session.query(VMLabel).filter(
                        VMLabel.vm_id == vm.id,
                        VMLabel.label_id == new_label_id
                    ).first()
                    
                    if existing:
                        stats["vm_assignments_skipped"] += 1
                        continue
                    
                    # Create assignment
                    vm_label = VMLabel(
                        vm_id=vm.id,
                        label_id=new_label_id,
                        inherited_from_folder=vm_assignment.get("inherited_from_folder", False),
                        source_folder_path=vm_assignment.get("source_folder_path"),
                        assigned_by=vm_assignment.get("assigned_by")
                    )
                    self.session.add(vm_label)
                    stats["vm_assignments_created"] += 1
                    
                except Exception as e:
                    stats["errors"].append(f"VM assignment error: {str(e)}")
            
            self.session.commit()
            
            # Import folder label assignments
            for folder_assignment in import_data.get("folder_assignments", []):
                try:
                    folder_path = folder_assignment["folder_path"]
                    old_label_id = folder_assignment["label_id"]
                    
                    # Map old label ID to new label ID
                    new_label_id = label_id_mapping.get(old_label_id)
                    if not new_label_id:
                        stats["errors"].append(f"Label ID {old_label_id} not found in mapping")
                        continue
                    
                    # Check if assignment exists
                    existing = self.session.query(FolderLabel).filter(
                        FolderLabel.folder_path == folder_path,
                        FolderLabel.label_id == new_label_id
                    ).first()
                    
                    if existing:
                        stats["folder_assignments_skipped"] += 1
                        continue
                    
                    # Create assignment
                    folder_label = FolderLabel(
                        folder_path=folder_path,
                        label_id=new_label_id,
                        inherit_to_vms=folder_assignment.get("inherit_to_vms", True),
                        inherit_to_subfolders=folder_assignment.get("inherit_to_subfolders", False),
                        assigned_by=folder_assignment.get("assigned_by")
                    )
                    self.session.add(folder_label)
                    stats["folder_assignments_created"] += 1
                    
                except Exception as e:
                    stats["errors"].append(f"Folder assignment error: {str(e)}")
            
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            stats["errors"].append(f"Critical error: {str(e)}")
            raise
        
        return stats
    
    def list_backups(self, backup_dir: Path) -> List[Dict]:
        """
        List all backup files in a directory.
        
        Args:
            backup_dir: Directory containing backup files
            
        Returns:
            List of backup file information
        """
        if not backup_dir.exists():
            return []
        
        backups = []
        for backup_file in backup_dir.glob("*.json"):
            try:
                with open(backup_file, 'r') as f:
                    data = json.load(f)
                
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_bytes": backup_file.stat().st_size,
                    "modified": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                    "version": data.get("version"),
                    "exported_at": data.get("exported_at"),
                    "labels_count": len(data.get("labels", [])),
                    "vm_assignments_count": len(data.get("vm_assignments", [])),
                    "folder_assignments_count": len(data.get("folder_assignments", []))
                })
            except Exception:
                # Skip invalid files
                continue
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x["modified"], reverse=True)
        return backups
    
    def backup_database(self, output_path: Path, db_url: str) -> Dict:
        """
        Create a full database backup.
        
        Args:
            output_path: Path to output backup file
            db_url: Database URL to backup
            
        Returns:
            Dictionary with backup statistics
        """
        import shutil
        from sqlalchemy import create_engine, inspect
        
        # For SQLite, we can just copy the file
        if db_url.startswith('sqlite:///') or db_url.startswith('sqlite://'):
            # Extract file path from URL
            db_path = db_url.replace('sqlite:///', '').replace('sqlite://', '')
            db_file = Path(db_path)
            
            if not db_file.exists():
                raise FileNotFoundError(f"Database file not found: {db_file}")
            
            # Create backup directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy database file
            shutil.copy2(db_file, output_path)
            
            # Get database stats
            engine = create_engine(db_url, echo=False)
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            stats = {
                "database_type": "SQLite",
                "source": str(db_file),
                "backup_file": str(output_path),
                "size_bytes": output_path.stat().st_size,
                "tables": len(tables),
                "table_names": tables
            }
            
            engine.dispose()
            return stats
        else:
            # For other databases, export as SQL dump or JSON
            raise NotImplementedError("Database backup only supports SQLite for now")
    
    def restore_database(self, backup_path: Path, db_url: str, 
                        confirm: bool = False) -> Dict:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            db_url: Target database URL
            confirm: Confirmation flag (required for safety)
            
        Returns:
            Dictionary with restore statistics
        """
        import shutil
        
        if not confirm:
            raise ValueError("Restore requires explicit confirmation (confirm=True)")
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # For SQLite, replace the database file
        if db_url.startswith('sqlite:///') or db_url.startswith('sqlite://'):
            # Extract file path from URL
            db_path = db_url.replace('sqlite:///', '').replace('sqlite://', '')
            db_file = Path(db_path)
            
            # Backup current database if it exists
            if db_file.exists():
                backup_current = db_file.with_suffix('.db.backup')
                shutil.copy2(db_file, backup_current)
            
            # Restore from backup
            shutil.copy2(backup_path, db_file)
            
            return {
                "database_type": "SQLite",
                "restored_to": str(db_file),
                "restored_from": str(backup_path),
                "size_bytes": db_file.stat().st_size
            }
        else:
            raise NotImplementedError("Database restore only supports SQLite for now")
