"""Pure unit tests for BackupService using mocks."""

import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open, call

from src.services.backup_service import BackupService
from src.models import Label, VMLabel, FolderLabel, VirtualMachine


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.flush = Mock()
    session.delete = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def backup_service(mock_session):
    """Create BackupService with mocked session."""
    return BackupService(mock_session)


class TestExportLabelsLogic:
    """Unit tests for export_labels logic without file I/O."""
    
    @patch('src.services.backup_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_builds_correct_data_structure(
        self, mock_json_dump, mock_file, mock_path_class, backup_service, mock_session
    ):
        """Test that export builds correct data structure."""
        # Setup mocks
        mock_label = Mock(
            id=1, key="env", value="prod", 
            description="Production", color="#FF0000",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2)
        )
        
        mock_session.query.return_value.all.return_value = [mock_label]
        mock_session.query.return_value.join.return_value.all.return_value = []
        
        mock_output_path = Mock()
        mock_output_path.parent = Mock()
        mock_output_path.stat.return_value.st_size = 1024
        
        # Execute
        result = backup_service.export_labels(mock_output_path)
        
        # Verify structure passed to json.dump
        call_args = mock_json_dump.call_args[0][0]
        assert "version" in call_args
        assert "exported_at" in call_args
        assert "labels" in call_args
        assert "vm_assignments" in call_args
        assert "folder_assignments" in call_args
        assert len(call_args["labels"]) == 1
        assert call_args["labels"][0]["key"] == "env"
    
    @patch('src.services.backup_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_includes_metadata_when_requested(
        self, mock_json_dump, mock_file, mock_path_class, backup_service, mock_session
    ):
        """Test that export includes metadata fields when requested."""
        mock_label = Mock(
            id=1, key="env", value="prod",
            description="Production", color="#FF0000",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2)
        )
        
        mock_session.query.return_value.all.return_value = [mock_label]
        mock_session.query.return_value.join.return_value.all.return_value = []
        
        mock_output_path = Mock()
        mock_output_path.parent = Mock()
        mock_output_path.stat.return_value.st_size = 1024
        
        # Execute with metadata
        backup_service.export_labels(mock_output_path, include_metadata=True)
        
        call_args = mock_json_dump.call_args[0][0]
        label_data = call_args["labels"][0]
        assert "created_at" in label_data
        assert "updated_at" in label_data
    
    @patch('src.services.backup_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_excludes_metadata_when_not_requested(
        self, mock_json_dump, mock_file, mock_path_class, backup_service, mock_session
    ):
        """Test that export excludes metadata fields when not requested."""
        mock_label = Mock(
            id=1, key="env", value="prod",
            description="Production", color="#FF0000",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2)
        )
        
        mock_session.query.return_value.all.return_value = [mock_label]
        mock_session.query.return_value.join.return_value.all.return_value = []
        
        mock_output_path = Mock()
        mock_output_path.parent = Mock()
        mock_output_path.stat.return_value.st_size = 1024
        
        # Execute without metadata
        backup_service.export_labels(mock_output_path, include_metadata=False)
        
        call_args = mock_json_dump.call_args[0][0]
        label_data = call_args["labels"][0]
        assert "created_at" not in label_data
        assert "updated_at" not in label_data
    
    @patch('src.services.backup_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_handles_vm_assignments(
        self, mock_json_dump, mock_file, mock_path_class, backup_service, mock_session
    ):
        """Test that export correctly processes VM assignments."""
        mock_vm_label = Mock(
            label_id=1,
            inherited_from_folder=False,
            source_folder_path=None,
            assigned_by="test_user",
            assigned_at=datetime(2024, 1, 1)
        )
        
        # Setup query chain
        query_mock = Mock()
        query_mock.all.return_value = []
        query_mock.join.return_value.all.return_value = [(mock_vm_label, "test-vm-01")]
        mock_session.query.return_value = query_mock
        
        mock_output_path = Mock()
        mock_output_path.parent = Mock()
        mock_output_path.stat.return_value.st_size = 1024
        
        # Execute
        backup_service.export_labels(mock_output_path)
        
        call_args = mock_json_dump.call_args[0][0]
        assert len(call_args["vm_assignments"]) == 1
        assert call_args["vm_assignments"][0]["vm_name"] == "test-vm-01"
        assert call_args["vm_assignments"][0]["label_id"] == 1
    
    @patch('src.services.backup_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_returns_correct_statistics(
        self, mock_json_dump, mock_file, mock_path_class, backup_service, mock_session
    ):
        """Test that export returns correct statistics."""
        mock_label = Mock(id=1, key="env", value="prod", description="", color="#FF0000")
        
        query_mock = Mock()
        query_mock.all.side_effect = [
            [mock_label],  # labels query
            []  # folder_labels query
        ]
        query_mock.join.return_value.all.return_value = []  # vm_labels query
        mock_session.query.return_value = query_mock
        
        mock_output_path = Mock()
        mock_output_path.parent = Mock()
        mock_output_path.stat.return_value.st_size = 2048
        
        # Execute
        result = backup_service.export_labels(mock_output_path)
        
        # Verify statistics
        assert result["labels"] == 1
        assert result["vm_assignments"] == 0
        assert result["folder_assignments"] == 0
        assert result["size_bytes"] == 2048
    
    @patch('src.services.backup_service.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_creates_parent_directories(
        self, mock_json_dump, mock_file, mock_path_class, backup_service, mock_session
    ):
        """Test that export creates parent directories."""
        mock_session.query.return_value.all.return_value = []
        mock_session.query.return_value.join.return_value.all.return_value = []
        
        mock_output_path = Mock()
        mock_parent = Mock()
        mock_output_path.parent = mock_parent
        mock_output_path.stat.return_value.st_size = 100
        
        # Execute
        backup_service.export_labels(mock_output_path)
        
        # Verify parent.mkdir was called
        mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestImportLabelsLogic:
    """Unit tests for import_labels logic without file I/O."""
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"version": "1.0", "exported_at": "2024-01-01", "labels": [], "vm_assignments": [], "folder_assignments": []}')
    @patch('json.load')
    def test_import_merge_mode_creates_new_label(
        self, mock_json_load, mock_file, backup_service, mock_session
    ):
        """Test that import in merge mode creates new labels."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [
                {"id": 1, "key": "env", "value": "prod", "description": "Production", "color": "#FF0000"}
            ],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        # No existing label
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        mock_path = Mock(spec=Path)
        
        # Execute
        result = backup_service.import_labels(mock_path, mode='merge')
        
        # Verify
        assert result["labels_created"] == 1
        assert result["labels_skipped"] == 0
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_import_skip_duplicates_mode_skips_existing(
        self, mock_json_load, mock_file, backup_service, mock_session
    ):
        """Test that import in skip_duplicates mode skips existing labels."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [
                {"id": 1, "key": "env", "value": "prod", "description": "Production", "color": "#FF0000"}
            ],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        # Existing label
        existing_label = Mock(id=100)
        mock_session.query.return_value.filter.return_value.first.return_value = existing_label
        
        mock_path = Mock(spec=Path)
        
        # Execute
        result = backup_service.import_labels(mock_path, mode='skip_duplicates')
        
        # Verify
        assert result["labels_created"] == 0
        assert result["labels_skipped"] == 1
        mock_session.add.assert_not_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_import_merge_mode_updates_existing(
        self, mock_json_load, mock_file, backup_service, mock_session
    ):
        """Test that import in merge mode updates existing labels."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [
                {"id": 1, "key": "env", "value": "prod", "description": "Updated", "color": "#00FF00"}
            ],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        # Existing label
        existing_label = Mock(id=100, description="Old", color="#FF0000")
        mock_session.query.return_value.filter.return_value.first.return_value = existing_label
        
        mock_path = Mock(spec=Path)
        
        # Execute
        result = backup_service.import_labels(mock_path, mode='merge')
        
        # Verify
        assert result["labels_updated"] == 1
        assert result["labels_created"] == 0
        assert existing_label.description == "Updated"
        assert existing_label.color == "#00FF00"
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_import_clear_existing_deletes_all_data(
        self, mock_json_load, mock_file, backup_service, mock_session
    ):
        """Test that import with clear_existing deletes all existing data."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        mock_path = Mock(spec=Path)
        
        # Execute
        backup_service.import_labels(mock_path, clear_existing=True)
        
        # Verify delete queries were called
        assert mock_session.query.call_count >= 3
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_import_vm_assignment_error_handling(
        self, mock_json_load, mock_file, backup_service, mock_session
    ):
        """Test that import handles VM not found errors."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [
                {"id": 1, "key": "env", "value": "prod", "description": "Prod", "color": "#FF0000"}
            ],
            "vm_assignments": [
                {"vm_name": "nonexistent-vm", "label_id": 1, "assigned_by": "user"}
            ],
            "folder_assignments": []
        }
        
        # Setup: label exists, but VM doesn't
        existing_label = Mock(id=100)
        mock_query_chain = Mock()
        mock_query_chain.filter.return_value.first.side_effect = [
            None,  # First call: no existing label
            None   # Second call: VM not found
        ]
        mock_session.query.return_value = mock_query_chain
        
        # Mock the new label creation
        new_label = Mock(id=101)
        
        mock_path = Mock(spec=Path)
        
        # Execute
        result = backup_service.import_labels(mock_path, mode='merge')
        
        # Verify error was captured
        assert result["vm_assignments_created"] == 0
        assert len(result["errors"]) > 0
        assert any("VM not found" in error for error in result["errors"])
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_import_label_id_mapping(
        self, mock_json_load, mock_file, backup_service, mock_session
    ):
        """Test that import correctly maps old label IDs to new IDs."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [
                {"id": 999, "key": "env", "value": "prod", "description": "Prod", "color": "#FF0000"}
            ],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        # No existing label
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock new label with different ID
        new_label = Mock(id=1)
        mock_session.add.side_effect = lambda obj: setattr(obj, 'id', 1)
        
        mock_path = Mock(spec=Path)
        
        # Execute
        result = backup_service.import_labels(mock_path, mode='merge')
        
        # Verify label was created
        assert result["labels_created"] == 1
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_import_rollback_on_critical_error(
        self, mock_json_load, mock_file, backup_service, mock_session
    ):
        """Test that import rolls back on critical errors."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [
                {"id": 1, "key": "env", "value": "prod"}
            ],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        # Simulate error during commit
        mock_session.commit.side_effect = Exception("Database error")
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        mock_path = Mock(spec=Path)
        
        # Execute and expect exception
        with pytest.raises(Exception):
            backup_service.import_labels(mock_path, mode='merge')
        
        # Verify rollback was called
        mock_session.rollback.assert_called()


class TestListBackupsLogic:
    """Unit tests for list_backups logic without file I/O."""
    
    @patch('src.services.backup_service.Path')
    def test_list_backups_returns_empty_for_nonexistent_dir(
        self, mock_path_class, backup_service
    ):
        """Test that list_backups returns empty list for nonexistent directory."""
        mock_dir = Mock()
        mock_dir.exists.return_value = False
        
        result = backup_service.list_backups(mock_dir)
        
        assert result == []
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_list_backups_parses_backup_files(
        self, mock_json_load, mock_file, backup_service
    ):
        """Test that list_backups correctly parses backup files."""
        mock_json_load.return_value = {
            "version": "1.0",
            "exported_at": "2024-01-01T00:00:00",
            "labels": [{"id": 1}],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        mock_file1 = Mock()
        mock_file1.name = "backup1.json"
        mock_file1.stat.return_value.st_size = 1024
        mock_file1.stat.return_value.st_mtime = 1704067200
        
        mock_dir = Mock()
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [mock_file1]
        
        result = backup_service.list_backups(mock_dir)
        
        assert len(result) == 1
        assert result[0]["filename"] == "backup1.json"
        assert result[0]["labels_count"] == 1
        assert result[0]["version"] == "1.0"
    
    @patch('builtins.open', side_effect=Exception("Read error"))
    def test_list_backups_skips_invalid_files(
        self, mock_file, backup_service
    ):
        """Test that list_backups skips invalid JSON files."""
        mock_file1 = Mock()
        mock_file1.name = "invalid.json"
        
        mock_dir = Mock()
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [mock_file1]
        
        result = backup_service.list_backups(mock_dir)
        
        # Should skip the invalid file
        assert result == []
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_list_backups_sorts_by_modification_time(
        self, mock_json_load, mock_file, backup_service
    ):
        """Test that list_backups sorts results by modification time (newest first)."""
        mock_json_load.return_value = {
            "version": "1.0",
            "labels": [],
            "vm_assignments": [],
            "folder_assignments": []
        }
        
        mock_file1 = Mock()
        mock_file1.name = "old_backup.json"
        mock_file1.stat.return_value.st_size = 1024
        mock_file1.stat.return_value.st_mtime = 1704067200  # Older
        
        mock_file2 = Mock()
        mock_file2.name = "new_backup.json"
        mock_file2.stat.return_value.st_size = 2048
        mock_file2.stat.return_value.st_mtime = 1704153600  # Newer
        
        mock_dir = Mock()
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [mock_file1, mock_file2]
        
        result = backup_service.list_backups(mock_dir)
        
        # Newer file should be first
        assert result[0]["filename"] == "new_backup.json"
        assert result[1]["filename"] == "old_backup.json"


class TestDatabaseBackupLogic:
    """Unit tests for database backup logic."""
    
    @patch('shutil.copy2')
    @patch('src.services.backup_service.Path')
    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.inspect')
    def test_backup_database_sqlite_logic(
        self, mock_inspect, mock_create_engine, mock_path_class, 
        mock_copy, backup_service
    ):
        """Test SQLite database backup logic."""
        # Setup mocks
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = ["labels", "vm_labels", "virtual_machines"]
        mock_inspect.return_value = mock_inspector
        
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_db_file = Mock()
        mock_db_file.exists.return_value = True
        
        mock_output_path = Mock()
        mock_output_path.parent = Mock()
        mock_output_path.stat.return_value.st_size = 10240
        
        # Mock Path constructor to return our mock
        mock_path_class.return_value = mock_db_file
        
        # Execute
        result = backup_service.backup_database(
            mock_output_path, 
            "sqlite:///data/test.db"
        )
        
        # Verify
        assert result["database_type"] == "SQLite"
        assert result["tables"] == 3
        assert "labels" in result["table_names"]
        mock_copy.assert_called_once()
        mock_engine.dispose.assert_called_once()
    
    def test_backup_database_unsupported_type(self, backup_service):
        """Test that non-SQLite databases raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            backup_service.backup_database(
                Path("/tmp/backup.db"),
                "postgresql://user:pass@localhost/db"
            )
    
    @patch('src.services.backup_service.Path')
    def test_backup_database_missing_source_file(
        self, mock_path_class, backup_service
    ):
        """Test that backup raises error for missing database file."""
        mock_db_file = Mock()
        mock_db_file.exists.return_value = False
        mock_path_class.return_value = mock_db_file
        
        with pytest.raises(FileNotFoundError):
            backup_service.backup_database(
                Path("/tmp/backup.db"),
                "sqlite:///data/nonexistent.db"
            )


class TestRestoreDatabaseLogic:
    """Unit tests for database restore logic."""
    
    def test_restore_database_requires_confirmation(self, backup_service):
        """Test that restore requires explicit confirmation."""
        with pytest.raises(ValueError, match="explicit confirmation"):
            backup_service.restore_database(
                Path("/tmp/backup.db"),
                "sqlite:///data/test.db",
                confirm=False
            )
    
    @patch('src.services.backup_service.Path')
    def test_restore_database_missing_backup_file(
        self, mock_path_class, backup_service
    ):
        """Test that restore raises error for missing backup file."""
        mock_backup = Mock()
        mock_backup.exists.return_value = False
        mock_path_class.return_value = mock_backup
        
        with pytest.raises(FileNotFoundError):
            backup_service.restore_database(
                mock_backup,
                "sqlite:///data/test.db",
                confirm=True
            )
    
    @patch('shutil.copy2')
    @patch('src.services.backup_service.Path')
    def test_restore_database_sqlite_logic(
        self, mock_path_class, mock_copy, backup_service
    ):
        """Test SQLite database restore logic."""
        mock_backup = Mock()
        mock_backup.exists.return_value = True
        mock_backup.with_suffix.return_value = Mock()
        
        mock_db_file = Mock()
        mock_db_file.exists.return_value = True
        mock_db_file.stat.return_value.st_size = 10240
        mock_db_file.with_suffix.return_value = Mock()
        
        # First call returns backup path, second returns db path
        mock_path_class.side_effect = [mock_db_file, mock_backup]
        
        # Execute
        result = backup_service.restore_database(
            mock_backup,
            "sqlite:///data/test.db",
            confirm=True
        )
        
        # Verify
        assert result["database_type"] == "SQLite"
        assert "restored_to" in result
        assert "restored_from" in result
    
    def test_restore_database_unsupported_type(self, backup_service):
        """Test that non-SQLite restore raises NotImplementedError."""
        mock_backup = Mock()
        mock_backup.exists.return_value = True
        
        with pytest.raises(NotImplementedError):
            backup_service.restore_database(
                mock_backup,
                "postgresql://user:pass@localhost/db",
                confirm=True
            )
