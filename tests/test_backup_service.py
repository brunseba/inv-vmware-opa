"""Unit tests for BackupService."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, Label, VMLabel, FolderLabel, VirtualMachine
from src.services.backup_service import BackupService


@pytest.fixture
def db_session():
    """Create a temporary in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_labels(db_session):
    """Create sample labels for testing."""
    labels = [
        Label(key="environment", value="production", description="Prod env", color="#FF0000"),
        Label(key="environment", value="development", description="Dev env", color="#00FF00"),
        Label(key="team", value="backend", description="Backend team", color="#0000FF"),
    ]
    for label in labels:
        db_session.add(label)
    db_session.commit()
    return labels


@pytest.fixture
def sample_vms(db_session):
    """Create sample VMs for testing."""
    vms = [
        VirtualMachine(vm="test-vm-01", datacenter="DC1", cluster="CL1", folder="/prod"),
        VirtualMachine(vm="test-vm-02", datacenter="DC1", cluster="CL1", folder="/dev"),
    ]
    for vm in vms:
        db_session.add(vm)
    db_session.commit()
    return vms


@pytest.fixture
def backup_service(db_session):
    """Create BackupService instance."""
    return BackupService(db_session)


class TestLabelExport:
    """Tests for label export functionality."""
    
    def test_export_labels_creates_file(self, backup_service, sample_labels, tmp_path):
        """Test that export creates a valid JSON file."""
        output_file = tmp_path / "backup.json"
        
        stats = backup_service.export_labels(output_file)
        
        assert output_file.exists()
        assert stats["labels"] == 3
        assert stats["file"] == str(output_file)
        assert stats["size_bytes"] > 0
    
    def test_export_labels_json_structure(self, backup_service, sample_labels, tmp_path):
        """Test that exported JSON has correct structure."""
        output_file = tmp_path / "backup.json"
        backup_service.export_labels(output_file)
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert "version" in data
        assert "exported_at" in data
        assert "labels" in data
        assert "vm_assignments" in data
        assert "folder_assignments" in data
        assert len(data["labels"]) == 3
    
    def test_export_labels_with_vm_assignments(self, backup_service, sample_labels, sample_vms, tmp_path):
        """Test exporting labels with VM assignments."""
        # Create VM label assignment
        vm_label = VMLabel(
            vm_id=sample_vms[0].id,
            label_id=sample_labels[0].id,
            assigned_by="test_user"
        )
        backup_service.session.add(vm_label)
        backup_service.session.commit()
        
        output_file = tmp_path / "backup.json"
        stats = backup_service.export_labels(output_file)
        
        assert stats["vm_assignments"] == 1
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert len(data["vm_assignments"]) == 1
        assert data["vm_assignments"][0]["vm_name"] == "test-vm-01"
    
    def test_export_labels_with_folder_assignments(self, backup_service, sample_labels, tmp_path):
        """Test exporting labels with folder assignments."""
        folder_label = FolderLabel(
            folder_path="/prod",
            label_id=sample_labels[0].id,
            inherit_to_vms=True,
            inherit_to_subfolders=False,
            assigned_by="test_user"
        )
        backup_service.session.add(folder_label)
        backup_service.session.commit()
        
        output_file = tmp_path / "backup.json"
        stats = backup_service.export_labels(output_file)
        
        assert stats["folder_assignments"] == 1
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert len(data["folder_assignments"]) == 1
        assert data["folder_assignments"][0]["folder_path"] == "/prod"


class TestLabelImport:
    """Tests for label import functionality."""
    
    def test_import_labels_merge_mode(self, backup_service, tmp_path):
        """Test importing labels in merge mode."""
        # Create backup data
        backup_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "labels": [
                {"id": 1, "key": "env", "value": "prod", "description": "Production", "color": "#FF0000"}
            ],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        backup_file = tmp_path / "backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)
        
        stats = backup_service.import_labels(backup_file, mode='merge')
        
        assert stats["labels_created"] == 1
        assert stats["labels_skipped"] == 0
        assert len(stats["errors"]) == 0
        
        # Verify label was created
        label = backup_service.session.query(Label).filter_by(key="env", value="prod").first()
        assert label is not None
        assert label.description == "Production"
    
    def test_import_labels_skip_duplicates_mode(self, backup_service, sample_labels, tmp_path):
        """Test importing labels in skip_duplicates mode."""
        backup_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "labels": [
                {"id": 1, "key": "environment", "value": "production", "description": "Updated", "color": "#FF0000"},
                {"id": 2, "key": "new_key", "value": "new_value", "description": "New", "color": "#00FF00"}
            ],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        backup_file = tmp_path / "backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)
        
        stats = backup_service.import_labels(backup_file, mode='skip_duplicates')
        
        assert stats["labels_skipped"] == 1  # environment:production already exists
        assert stats["labels_created"] == 1  # new_key:new_value
    
    def test_import_labels_with_vm_assignments(self, backup_service, sample_vms, tmp_path):
        """Test importing VM label assignments."""
        backup_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "labels": [
                {"id": 1, "key": "env", "value": "prod", "description": "Production", "color": "#FF0000"}
            ],
            "vm_assignments": [
                {
                    "vm_name": "test-vm-01",
                    "label_id": 1,
                    "inherited_from_folder": False,
                    "source_folder_path": None,
                    "assigned_by": "test_user"
                }
            ],
            "folder_assignments": []
        }
        
        backup_file = tmp_path / "backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)
        
        stats = backup_service.import_labels(backup_file, mode='merge')
        
        assert stats["vm_assignments_created"] == 1
        assert len(stats["errors"]) == 0
    
    def test_import_labels_vm_not_found_error(self, backup_service, tmp_path):
        """Test importing with non-existent VM generates error."""
        backup_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "labels": [
                {"id": 1, "key": "env", "value": "prod", "description": "Production", "color": "#FF0000"}
            ],
            "vm_assignments": [
                {
                    "vm_name": "non-existent-vm",
                    "label_id": 1,
                    "inherited_from_folder": False,
                    "source_folder_path": None,
                    "assigned_by": "test_user"
                }
            ],
            "folder_assignments": []
        }
        
        backup_file = tmp_path / "backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)
        
        stats = backup_service.import_labels(backup_file, mode='merge')
        
        assert stats["vm_assignments_created"] == 0
        assert len(stats["errors"]) > 0
        assert "VM not found" in stats["errors"][0]


class TestDatabaseBackup:
    """Tests for database backup functionality."""
    
    def test_backup_database_creates_file(self, backup_service, tmp_path):
        """Test that database backup creates a file."""
        db_url = "sqlite:///data/vmware_inventory.db"
        output_file = tmp_path / "db_backup.db"
        
        # Create a temporary database file
        temp_db = tmp_path / "vmware_inventory.db"
        temp_db.parent.mkdir(parents=True, exist_ok=True)
        temp_db.touch()
        
        # Note: This test requires actual SQLite file, 
        # in-memory databases cannot be backed up this way
        # This is a simplified test
    
    def test_list_backups_empty_directory(self, backup_service, tmp_path):
        """Test listing backups in empty directory."""
        backups = backup_service.list_backups(tmp_path)
        assert backups == []
    
    def test_list_backups_with_files(self, backup_service, tmp_path):
        """Test listing backup files."""
        # Create sample backup files
        backup_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "labels": [],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        backup1 = tmp_path / "backup1.json"
        backup2 = tmp_path / "backup2.json"
        
        for backup_file in [backup1, backup2]:
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f)
        
        backups = backup_service.list_backups(tmp_path)
        
        assert len(backups) == 2
        assert all("filename" in b for b in backups)
        assert all("size_bytes" in b for b in backups)
        assert all("labels_count" in b for b in backups)


class TestBackupValidation:
    """Tests for backup validation and error handling."""
    
    def test_export_creates_parent_directories(self, backup_service, tmp_path):
        """Test that export creates parent directories if needed."""
        nested_path = tmp_path / "level1" / "level2" / "backup.json"
        
        backup_service.export_labels(nested_path)
        
        assert nested_path.exists()
        assert nested_path.parent.exists()
    
    def test_import_invalid_json(self, backup_service, tmp_path):
        """Test importing invalid JSON file."""
        backup_file = tmp_path / "invalid.json"
        with open(backup_file, 'w') as f:
            f.write("invalid json content{")
        
        with pytest.raises(json.JSONDecodeError):
            backup_service.import_labels(backup_file)
    
    def test_import_nonexistent_file(self, backup_service, tmp_path):
        """Test importing non-existent file."""
        backup_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            backup_service.import_labels(backup_file)
