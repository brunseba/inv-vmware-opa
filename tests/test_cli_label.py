"""Unit tests for CLI label commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.commands.label import (
    label,
    create_label,
    list_labels,
    delete_label,
    list_keys,
    assign_vm_label,
    remove_vm_label,
    get_label_service
)
from src.models import Label, VirtualMachine


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_label_service():
    """Create a mock LabelService."""
    service = Mock()
    service.session = Mock()
    return service


class TestGetLabelService:
    """Tests for get_label_service helper function."""
    
    @patch('src.commands.label.create_engine')
    @patch('src.commands.label.sessionmaker')
    @patch('src.commands.label.LabelService')
    def test_get_label_service(self, mock_service_class, mock_sessionmaker, mock_create_engine):
        """Test creating a label service instance."""
        mock_session = Mock()
        mock_sessionmaker.return_value.return_value = mock_session
        
        service = get_label_service('sqlite:///test.db')
        
        mock_create_engine.assert_called_once_with('sqlite:///test.db', echo=False)
        mock_service_class.assert_called_once_with(mock_session)


class TestCreateLabelCommand:
    """Tests for create label command."""
    
    @patch('src.commands.label.get_label_service')
    def test_create_label_success(self, mock_get_service, cli_runner, mock_label_service):
        """Test successful label creation."""
        mock_label = Mock(key="env", value="prod", id=1)
        mock_label_service.create_label.return_value = mock_label
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(create_label, ['env', 'prod', '--description', 'Production'])
        
        assert result.exit_code == 0
        assert "Label created" in result.output
        assert "env=prod" in result.output
        mock_label_service.create_label.assert_called_once_with('env', 'prod', 'Production', None)
    
    @patch('src.commands.label.get_label_service')
    def test_create_label_with_color(self, mock_get_service, cli_runner, mock_label_service):
        """Test creating label with color."""
        mock_label = Mock(key="tier", value="1", id=2)
        mock_label_service.create_label.return_value = mock_label
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(create_label, [
            'tier', '1', '--color', '#FF0000'
        ])
        
        assert result.exit_code == 0
        mock_label_service.create_label.assert_called_with('tier', '1', None, '#FF0000')
    
    @patch('src.commands.label.get_label_service')
    def test_create_label_error(self, mock_get_service, cli_runner, mock_label_service):
        """Test label creation with error."""
        mock_label_service.create_label.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(create_label, ['env', 'test'])
        
        assert result.exit_code != 0
        assert "Error" in result.output


class TestListLabelsCommand:
    """Tests for list labels command."""
    
    @patch('src.commands.label.get_label_service')
    def test_list_labels_success(self, mock_get_service, cli_runner, mock_label_service):
        """Test listing all labels."""
        mock_labels = [
            Mock(id=1, key="env", value="prod", description="Production", color="#FF0000"),
            Mock(id=2, key="env", value="dev", description="Development", color="#00FF00")
        ]
        mock_label_service.list_labels.return_value = mock_labels
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(list_labels, [])
        
        assert result.exit_code == 0
        assert "env" in result.output
        assert "prod" in result.output
        assert "2 total" in result.output
    
    @patch('src.commands.label.get_label_service')
    def test_list_labels_with_filter(self, mock_get_service, cli_runner, mock_label_service):
        """Test listing labels with key filter."""
        mock_labels = [Mock(id=1, key="tier", value="1", description="", color="")]
        mock_label_service.list_labels.return_value = mock_labels
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(list_labels, ['--key', 'tier'])
        
        assert result.exit_code == 0
        mock_label_service.list_labels.assert_called_once_with('tier')
    
    @patch('src.commands.label.get_label_service')
    def test_list_labels_empty(self, mock_get_service, cli_runner, mock_label_service):
        """Test listing labels when none exist."""
        mock_label_service.list_labels.return_value = []
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(list_labels, [])
        
        assert result.exit_code == 0
        assert "No labels found" in result.output


class TestDeleteLabelCommand:
    """Tests for delete label command."""
    
    @patch('src.commands.label.get_label_service')
    def test_delete_label_success(self, mock_get_service, cli_runner, mock_label_service):
        """Test successful label deletion."""
        mock_label_service.delete_label.return_value = True
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(delete_label, ['1', '--yes'])
        
        assert result.exit_code == 0
        assert "deleted" in result.output
        mock_label_service.delete_label.assert_called_once_with(1)
    
    @patch('src.commands.label.get_label_service')
    def test_delete_label_not_found(self, mock_get_service, cli_runner, mock_label_service):
        """Test deleting non-existent label."""
        mock_label_service.delete_label.return_value = False
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(delete_label, ['999', '--yes'])
        
        assert result.exit_code == 0
        assert "not found" in result.output


class TestListKeysCommand:
    """Tests for list keys command."""
    
    @patch('src.commands.label.get_label_service')
    def test_list_keys_success(self, mock_get_service, cli_runner, mock_label_service):
        """Test listing label keys."""
        mock_label_service.get_label_keys.return_value = ["env", "tier", "team"]
        mock_label_service.get_label_values.side_effect = [
            ["prod", "dev"],
            ["1", "2", "3"],
            ["backend", "frontend"]
        ]
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(list_keys, [])
        
        assert result.exit_code == 0
        assert "env" in result.output
        assert "2 values" in result.output
        assert "tier" in result.output
    
    @patch('src.commands.label.get_label_service')
    def test_list_keys_empty(self, mock_get_service, cli_runner, mock_label_service):
        """Test listing keys when none exist."""
        mock_label_service.get_label_keys.return_value = []
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(list_keys, [])
        
        assert result.exit_code == 0
        assert "No label keys found" in result.output


class TestAssignVMLabelCommand:
    """Tests for assign VM label command."""
    
    @patch('src.commands.label.get_label_service')
    def test_assign_vm_label_existing_label(self, mock_get_service, cli_runner, mock_label_service):
        """Test assigning existing label to VM."""
        mock_vm = Mock(id=1, vm="test-vm-01")
        mock_label = Mock(id=2, key="env", value="prod")
        
        mock_label_service.session.query.return_value.filter.return_value.first.return_value = mock_vm
        mock_label_service.get_label_by_key_value.return_value = mock_label
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(assign_vm_label, ['test-vm-01', 'env', 'prod'])
        
        assert result.exit_code == 0
        assert "Label assigned" in result.output
        mock_label_service.assign_vm_label.assert_called_once_with(1, 2, assigned_by=None)
    
    @patch('src.commands.label.get_label_service')
    def test_assign_vm_label_create_new_label(self, mock_get_service, cli_runner, mock_label_service):
        """Test assigning label that doesn't exist (creates it)."""
        mock_vm = Mock(id=1, vm="test-vm-01")
        mock_new_label = Mock(id=3, key="tier", value="1")
        
        mock_label_service.session.query.return_value.filter.return_value.first.return_value = mock_vm
        mock_label_service.get_label_by_key_value.return_value = None
        mock_label_service.create_label.return_value = mock_new_label
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(assign_vm_label, ['test-vm-01', 'tier', '1'])
        
        assert result.exit_code == 0
        assert "Created new label" in result.output
        mock_label_service.create_label.assert_called_once_with('tier', '1')
    
    @patch('src.commands.label.get_label_service')
    def test_assign_vm_label_vm_not_found(self, mock_get_service, cli_runner, mock_label_service):
        """Test assigning label to non-existent VM."""
        mock_label_service.session.query.return_value.filter.return_value.first.return_value = None
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(assign_vm_label, ['nonexistent-vm', 'env', 'prod'])
        
        assert result.exit_code != 0
        assert "VM not found" in result.output
    
    @patch('src.commands.label.get_label_service')
    def test_assign_vm_label_with_user(self, mock_get_service, cli_runner, mock_label_service):
        """Test assigning label with assigned_by user."""
        mock_vm = Mock(id=1, vm="test-vm-01")
        mock_label = Mock(id=2, key="env", value="prod")
        
        mock_label_service.session.query.return_value.filter.return_value.first.return_value = mock_vm
        mock_label_service.get_label_by_key_value.return_value = mock_label
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(assign_vm_label, [
            'test-vm-01', 'env', 'prod', '--by', 'admin'
        ])
        
        assert result.exit_code == 0
        mock_label_service.assign_vm_label.assert_called_with(1, 2, assigned_by='admin')


class TestRemoveVMLabelCommand:
    """Tests for remove VM label command."""
    
    @patch('src.commands.label.get_label_service')
    def test_remove_vm_label_success(self, mock_get_service, cli_runner, mock_label_service):
        """Test successfully removing label from VM."""
        mock_vm = Mock(id=1, vm="test-vm-01")
        mock_label = Mock(id=2, key="env", value="prod")
        
        mock_label_service.session.query.return_value.filter.return_value.first.return_value = mock_vm
        mock_label_service.get_label_by_key_value.return_value = mock_label
        mock_label_service.remove_vm_label.return_value = True
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(remove_vm_label, ['test-vm-01', 'env', 'prod'])
        
        assert result.exit_code == 0
        # Note: This command may need more output assertions based on actual implementation
    
    @patch('src.commands.label.get_label_service')
    def test_remove_vm_label_vm_not_found(self, mock_get_service, cli_runner, mock_label_service):
        """Test removing label from non-existent VM."""
        mock_label_service.session.query.return_value.filter.return_value.first.return_value = None
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(remove_vm_label, ['nonexistent-vm', 'env', 'prod'])
        
        assert result.exit_code != 0
        assert "VM not found" in result.output
    
    @patch('src.commands.label.get_label_service')
    def test_remove_vm_label_label_not_found(self, mock_get_service, cli_runner, mock_label_service):
        """Test removing non-existent label from VM."""
        mock_vm = Mock(id=1, vm="test-vm-01")
        
        mock_label_service.session.query.return_value.filter.return_value.first.return_value = mock_vm
        mock_label_service.get_label_by_key_value.return_value = None
        mock_get_service.return_value = mock_label_service
        
        result = cli_runner.invoke(remove_vm_label, ['test-vm-01', 'env', 'nonexistent'])
        
        assert result.exit_code != 0
        assert "Label not found" in result.output


class TestCLIIntegration:
    """Integration tests for CLI command group."""
    
    def test_label_group_exists(self, cli_runner):
        """Test that label command group exists."""
        result = cli_runner.invoke(label, ['--help'])
        
        assert result.exit_code == 0
        assert "Manage VM and folder labels" in result.output
    
    def test_label_group_has_commands(self, cli_runner):
        """Test that label group has expected commands."""
        result = cli_runner.invoke(label, ['--help'])
        
        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output
        assert "delete" in result.output
        assert "keys" in result.output
        assert "assign-vm" in result.output
        assert "remove-vm" in result.output
