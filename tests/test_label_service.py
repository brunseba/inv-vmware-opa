"""Pure unit tests for LabelService."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from sqlalchemy.orm import Session

from src.services.label_service import LabelService
from src.models import Label, VMLabel, FolderLabel, VirtualMachine


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.delete = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def label_service(mock_session):
    """Create LabelService with mocked session."""
    return LabelService(mock_session)


class TestLabelCRUD:
    """Unit tests for label CRUD operations."""
    
    def test_create_label_new(self, label_service, mock_session):
        """Test creating a new label."""
        # Setup: no existing label
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = label_service.create_label("env", "prod", "Production", "#FF0000")
        
        # Verify
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert isinstance(result, Label)
    
    def test_create_label_existing(self, label_service, mock_session):
        """Test creating a label that already exists returns existing."""
        existing_label = Mock(spec=Label, id=1, key="env", value="prod")
        mock_session.query.return_value.filter.return_value.first.return_value = existing_label
        
        # Execute
        result = label_service.create_label("env", "prod")
        
        # Verify - should not add or commit
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        assert result == existing_label
    
    def test_get_label(self, label_service, mock_session):
        """Test getting a label by ID."""
        mock_label = Mock(spec=Label, id=1)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        
        result = label_service.get_label(1)
        
        assert result == mock_label
    
    def test_get_label_by_key_value(self, label_service, mock_session):
        """Test getting a label by key-value pair."""
        mock_label = Mock(spec=Label, key="env", value="prod")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        
        result = label_service.get_label_by_key_value("env", "prod")
        
        assert result == mock_label
    
    def test_list_labels_all(self, label_service, mock_session):
        """Test listing all labels."""
        mock_labels = [Mock(spec=Label), Mock(spec=Label)]
        mock_session.query.return_value.order_by.return_value.all.return_value = mock_labels
        
        result = label_service.list_labels()
        
        assert result == mock_labels
    
    def test_list_labels_filtered(self, label_service, mock_session):
        """Test listing labels filtered by key."""
        mock_labels = [Mock(spec=Label, key="env")]
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_labels
        
        result = label_service.list_labels(key="env")
        
        assert result == mock_labels
    
    def test_get_label_keys(self, label_service, mock_session):
        """Test getting unique label keys."""
        mock_session.query.return_value.distinct.return_value.order_by.return_value.all.return_value = [
            ("env",), ("team",), ("tier",)
        ]
        
        result = label_service.get_label_keys()
        
        assert result == ["env", "team", "tier"]
    
    def test_get_label_values(self, label_service, mock_session):
        """Test getting values for a specific key."""
        mock_session.query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = [
            ("prod",), ("dev",), ("test",)
        ]
        
        result = label_service.get_label_values("env")
        
        assert result == ["prod", "dev", "test"]
    
    def test_update_label(self, label_service, mock_session):
        """Test updating a label."""
        mock_label = Mock(spec=Label, id=1, description="Old", color="#FF0000")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        
        result = label_service.update_label(1, description="New", color="#00FF00")
        
        assert mock_label.description == "New"
        assert mock_label.color == "#00FF00"
        mock_session.commit.assert_called_once()
    
    def test_update_label_not_found(self, label_service, mock_session):
        """Test updating non-existent label returns None."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.update_label(999, description="New")
        
        assert result is None
        mock_session.commit.assert_not_called()
    
    def test_delete_label(self, label_service, mock_session):
        """Test deleting a label."""
        mock_label = Mock(spec=Label, id=1)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        
        result = label_service.delete_label(1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(mock_label)
        mock_session.commit.assert_called_once()
    
    def test_delete_label_not_found(self, label_service, mock_session):
        """Test deleting non-existent label returns False."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.delete_label(999)
        
        assert result is False
        mock_session.delete.assert_not_called()


class TestVMLabelOperations:
    """Unit tests for VM label operations."""
    
    def test_assign_vm_label_new(self, label_service, mock_session):
        """Test assigning a new label to a VM."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.assign_vm_label(1, 2, "test_user")
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert isinstance(result, VMLabel)
    
    def test_assign_vm_label_existing(self, label_service, mock_session):
        """Test assigning a label that's already assigned."""
        existing = Mock(spec=VMLabel, vm_id=1, label_id=2)
        mock_session.query.return_value.filter.return_value.first.return_value = existing
        
        result = label_service.assign_vm_label(1, 2)
        
        mock_session.add.assert_not_called()
        assert result == existing
    
    def test_assign_vm_label_inherited(self, label_service, mock_session):
        """Test assigning an inherited label."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.assign_vm_label(
            1, 2, "system", inherited=True, source_folder="/prod"
        )
        
        mock_session.add.assert_called_once()
        added_vm_label = mock_session.add.call_args[0][0]
        assert added_vm_label.inherited_from_folder is True
        assert added_vm_label.source_folder_path == "/prod"
    
    def test_remove_vm_label(self, label_service, mock_session):
        """Test removing a label from a VM."""
        mock_vm_label = Mock(spec=VMLabel)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_vm_label
        
        result = label_service.remove_vm_label(1, 2)
        
        assert result is True
        mock_session.delete.assert_called_once_with(mock_vm_label)
        mock_session.commit.assert_called_once()
    
    def test_remove_vm_label_not_found(self, label_service, mock_session):
        """Test removing non-existent VM label."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.remove_vm_label(1, 2)
        
        assert result is False
        mock_session.delete.assert_not_called()
    
    def test_get_vm_labels(self, label_service, mock_session):
        """Test getting all labels for a VM."""
        mock_label = Mock(
            spec=Label, id=1, key="env", value="prod", 
            description="Prod", color="#FF0000"
        )
        mock_vm_label = Mock(
            spec=VMLabel, inherited_from_folder=False, 
            source_folder_path=None, assigned_at=datetime.utcnow(),
            assigned_by="user"
        )
        
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (mock_label, mock_vm_label)
        ]
        
        result = label_service.get_vm_labels(1)
        
        assert len(result) == 1
        assert result[0]["key"] == "env"
        assert result[0]["value"] == "prod"
        assert result[0]["inherited"] is False
    
    def test_get_vm_labels_exclude_inherited(self, label_service, mock_session):
        """Test getting VM labels excluding inherited ones."""
        mock_query = Mock()
        mock_session.query.return_value.join.return_value.filter.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []
        
        result = label_service.get_vm_labels(1, include_inherited=False)
        
        # Verify filter was called with inherited_from_folder == False
        mock_query.filter.assert_called_once()
    
    def test_get_vms_with_label(self, label_service, mock_session):
        """Test getting all VMs with a specific label."""
        mock_label = Mock(spec=Label, id=1)
        mock_vms = [Mock(spec=VirtualMachine), Mock(spec=VirtualMachine)]
        
        # Mock get_label_by_key_value
        with patch.object(label_service, 'get_label_by_key_value', return_value=mock_label):
            mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = mock_vms
            
            result = label_service.get_vms_with_label("env", "prod")
            
            assert result == mock_vms
    
    def test_get_vms_with_label_not_found(self, label_service, mock_session):
        """Test getting VMs with non-existent label."""
        with patch.object(label_service, 'get_label_by_key_value', return_value=None):
            result = label_service.get_vms_with_label("env", "nonexistent")
            
            assert result == []


class TestFolderLabelOperations:
    """Unit tests for folder label operations."""
    
    def test_assign_folder_label_new(self, label_service, mock_session):
        """Test assigning a new label to a folder."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch.object(label_service, '_apply_folder_label_to_vms'):
            result = label_service.assign_folder_label("/prod", 1, "user", inherit_to_vms=True)
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called()
            assert isinstance(result, FolderLabel)
    
    def test_assign_folder_label_existing(self, label_service, mock_session):
        """Test assigning an already assigned folder label updates inheritance."""
        existing = Mock(spec=FolderLabel, inherit_to_vms=False, inherit_to_subfolders=False)
        mock_session.query.return_value.filter.return_value.first.return_value = existing
        
        with patch.object(label_service, '_apply_folder_label_to_vms'):
            result = label_service.assign_folder_label(
                "/prod", 1, inherit_to_vms=True, inherit_to_subfolders=True
            )
            
            assert existing.inherit_to_vms is True
            assert existing.inherit_to_subfolders is True
            mock_session.commit.assert_called()
    
    def test_assign_folder_label_no_inheritance(self, label_service, mock_session):
        """Test assigning folder label without VM inheritance."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.assign_folder_label("/prod", 1, inherit_to_vms=False)
        
        mock_session.add.assert_called_once()
        # Should not call _apply_folder_label_to_vms
    
    def test_remove_folder_label(self, label_service, mock_session):
        """Test removing a label from a folder."""
        mock_folder_label = Mock(spec=FolderLabel, inherit_to_subfolders=False)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_folder_label
        
        with patch.object(label_service, '_remove_inherited_labels_from_vms'):
            result = label_service.remove_folder_label("/prod", 1, remove_inherited=True)
            
            assert result is True
            mock_session.delete.assert_called_once_with(mock_folder_label)
            mock_session.commit.assert_called_once()
    
    def test_remove_folder_label_not_found(self, label_service, mock_session):
        """Test removing non-existent folder label."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.remove_folder_label("/prod", 1)
        
        assert result is False
        mock_session.delete.assert_not_called()
    
    def test_get_folder_labels(self, label_service, mock_session):
        """Test getting all labels for a folder."""
        mock_label = Mock(
            spec=Label, id=1, key="env", value="prod",
            description="Prod", color="#FF0000"
        )
        mock_folder_label = Mock(
            spec=FolderLabel, inherit_to_vms=True, inherit_to_subfolders=False,
            assigned_at=datetime.utcnow(), assigned_by="user"
        )
        
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (mock_label, mock_folder_label)
        ]
        
        result = label_service.get_folder_labels("/prod")
        
        assert len(result) == 1
        assert result[0]["key"] == "env"
        assert result[0]["inherit_to_vms"] is True
    
    def test_get_folders_with_label(self, label_service, mock_session):
        """Test getting all folders with a specific label."""
        mock_label = Mock(spec=Label, id=1)
        
        with patch.object(label_service, 'get_label_by_key_value', return_value=mock_label):
            mock_session.query.return_value.filter.return_value.all.return_value = [
                ("/prod",), ("/dev",)
            ]
            
            result = label_service.get_folders_with_label("env", "prod")
            
            assert result == ["/prod", "/dev"]
    
    def test_get_folders_with_label_not_found(self, label_service, mock_session):
        """Test getting folders with non-existent label."""
        with patch.object(label_service, 'get_label_by_key_value', return_value=None):
            result = label_service.get_folders_with_label("env", "nonexistent")
            
            assert result == []


class TestFolderOperations:
    """Unit tests for folder operations."""
    
    def test_get_all_folders(self, label_service, mock_session):
        """Test getting all unique folder paths."""
        mock_session.query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = [
            ("/prod",), ("/dev",), ("/test",)
        ]
        
        result = label_service.get_all_folders()
        
        assert result == ["/prod", "/dev", "/test"]
    
    def test_get_folder_stats(self, label_service, mock_session):
        """Test getting statistics for a folder."""
        # Mock VM count
        mock_session.query.return_value.filter.return_value.scalar.return_value = 10
        
        # Mock storage sum - need to handle two calls
        storage_query = Mock()
        storage_query.filter.return_value.scalar.return_value = 10240  # MiB
        mock_session.query.side_effect = [
            Mock(filter=lambda x: Mock(scalar=lambda: 10)),  # VM count
            storage_query  # Storage sum
        ]
        
        with patch.object(label_service, 'get_folder_labels', return_value=[]):
            result = label_service.get_folder_stats("/prod")
            
            assert result["folder_path"] == "/prod"
            assert result["vm_count"] == 10
            assert result["storage_gib"] == 10
            assert result["label_count"] == 0


class TestLabelInheritance:
    """Unit tests for label inheritance logic."""
    
    def test_apply_folder_label_to_vms_no_subfolders(self, label_service, mock_session):
        """Test applying folder label to VMs without subfolder inheritance."""
        mock_vms = [Mock(spec=VirtualMachine, id=1), Mock(spec=VirtualMachine, id=2)]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_vms
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        label_service._apply_folder_label_to_vms("/prod", 1, include_subfolders=False)
        
        # Should add label twice (once per VM)
        assert mock_session.add.call_count == 2
    
    def test_apply_folder_label_to_vms_with_subfolders(self, label_service, mock_session):
        """Test applying folder label with subfolder inheritance."""
        mock_vms = [
            Mock(spec=VirtualMachine, id=1, folder="/prod"),
            Mock(spec=VirtualMachine, id=2, folder="/prod/sub")
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_vms
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        label_service._apply_folder_label_to_vms("/prod", 1, include_subfolders=True)
        
        assert mock_session.add.call_count == 2
    
    def test_remove_inherited_labels_from_vms(self, label_service, mock_session):
        """Test removing inherited labels from VMs."""
        mock_query = Mock()
        mock_query.filter.return_value.delete.return_value = 5
        mock_session.query.return_value.join.return_value.filter.return_value = mock_query
        
        label_service._remove_inherited_labels_from_vms("/prod", 1, include_subfolders=False)
        
        mock_query.filter.return_value.delete.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_sync_inherited_labels_all(self, label_service, mock_session):
        """Test syncing all inherited labels."""
        mock_folder_labels = [
            Mock(spec=FolderLabel, folder_path="/prod", label_id=1, inherit_to_subfolders=False),
            Mock(spec=FolderLabel, folder_path="/dev", label_id=2, inherit_to_subfolders=True)
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_folder_labels
        
        with patch.object(label_service, '_apply_folder_label_to_vms') as mock_apply:
            label_service.sync_inherited_labels()
            
            assert mock_apply.call_count == 2
            mock_session.commit.assert_called_once()
    
    def test_sync_inherited_labels_single_folder(self, label_service, mock_session):
        """Test syncing inherited labels for a specific folder."""
        mock_folder_labels = [
            Mock(spec=FolderLabel, folder_path="/prod", label_id=1, inherit_to_subfolders=False)
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_folder_labels
        
        with patch.object(label_service, '_apply_folder_label_to_vms') as mock_apply:
            label_service.sync_inherited_labels(folder_path="/prod")
            
            assert mock_apply.call_count == 1


class TestHelperMethods:
    """Unit tests for helper methods."""
    
    def test_get_folder_hierarchy(self, label_service, mock_session):
        """Test building folder hierarchy."""
        result = label_service.get_folder_hierarchy("/prod/app/frontend")
        
        assert result == ["/prod", "/prod/app", "/prod/app/frontend"]
    
    def test_get_folder_hierarchy_empty(self, label_service, mock_session):
        """Test hierarchy for empty path."""
        result = label_service.get_folder_hierarchy("")
        
        assert result == []
    
    def test_get_folder_hierarchy_root(self, label_service, mock_session):
        """Test hierarchy for root folder."""
        result = label_service.get_folder_hierarchy("/prod")
        
        assert result == ["/prod"]
    
    def test_get_vm_effective_labels(self, label_service, mock_session):
        """Test getting effective labels for a VM."""
        mock_vm = Mock(spec=VirtualMachine, id=1, folder="/prod/app")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_vm
        
        # Mock direct labels
        direct_labels = [
            {"key": "tier", "value": "frontend", "label_id": 1, "color": "#FF0000"}
        ]
        
        # Mock folder labels
        folder_labels = [
            {"key": "env", "value": "prod", "label_id": 2, "color": "#00FF00", "inherit_to_vms": True}
        ]
        
        with patch.object(label_service, 'get_vm_labels', return_value=direct_labels):
            with patch.object(label_service, 'get_folder_labels', return_value=folder_labels):
                result = label_service.get_vm_effective_labels(1)
                
                # Direct label should be present
                assert "tier" in result
                assert result["tier"]["type"] == "direct"
                
                # Folder label should be inherited
                assert "env" in result
                assert result["env"]["type"] == "inherited"
    
    def test_get_vm_effective_labels_direct_overrides_inherited(self, label_service, mock_session):
        """Test that direct labels override inherited ones."""
        mock_vm = Mock(spec=VirtualMachine, id=1, folder="/prod")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_vm
        
        # Both direct and folder have same key
        direct_labels = [
            {"key": "env", "value": "dev", "label_id": 1, "color": "#FF0000"}
        ]
        
        folder_labels = [
            {"key": "env", "value": "prod", "label_id": 2, "color": "#00FF00", "inherit_to_vms": True}
        ]
        
        with patch.object(label_service, 'get_vm_labels', return_value=direct_labels):
            with patch.object(label_service, 'get_folder_labels', return_value=folder_labels):
                result = label_service.get_vm_effective_labels(1)
                
                # Direct label should win
                assert result["env"]["value"] == "dev"
                assert result["env"]["type"] == "direct"
    
    def test_get_vm_effective_labels_vm_not_found(self, label_service, mock_session):
        """Test getting effective labels for non-existent VM."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_service.get_vm_effective_labels(999)
        
        assert result == {}
