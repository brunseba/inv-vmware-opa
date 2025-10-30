"""Unit tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, VirtualMachine, Label, VMLabel, FolderLabel


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    from sqlalchemy import event
    
    engine = create_engine("sqlite:///:memory:")
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestVirtualMachineModel:
    """Tests for VirtualMachine model."""
    
    def test_create_vm(self, in_memory_db):
        """Test creating a virtual machine."""
        vm = VirtualMachine(
            vm="test-vm-01",
            datacenter="DC1",
            cluster="CL1",
            folder="/prod"
        )
        in_memory_db.add(vm)
        in_memory_db.commit()
        
        assert vm.id is not None
        assert vm.vm == "test-vm-01"
        assert vm.imported_at is not None
    
    def test_vm_with_full_attributes(self, in_memory_db):
        """Test VM with all common attributes."""
        vm = VirtualMachine(
            vm="test-vm-02",
            powerstate="poweredOn",
            template=False,
            cpus=4,
            memory=8192,
            datacenter="DC1",
            cluster="CL1",
            host="host01.example.com",
            folder="/prod/app",
            os_config="Microsoft Windows Server 2019",
            provisioned_mib=102400,
            in_use_mib=51200
        )
        in_memory_db.add(vm)
        in_memory_db.commit()
        
        assert vm.cpus == 4
        assert vm.memory == 8192
        assert vm.powerstate == "poweredOn"
        assert vm.template is False
    
    def test_vm_repr(self, in_memory_db):
        """Test VM string representation."""
        vm = VirtualMachine(
            vm="test-vm-03",
            datacenter="DC1",
            cluster="CL1"
        )
        
        repr_str = repr(vm)
        assert "test-vm-03" in repr_str
        assert "DC1" in repr_str
    
    def test_vm_unique_uuid_constraint(self, in_memory_db):
        """Test that VM UUID must be unique."""
        vm1 = VirtualMachine(vm="vm-01", vm_uuid="unique-uuid-123")
        vm2 = VirtualMachine(vm="vm-02", vm_uuid="unique-uuid-123")
        
        in_memory_db.add(vm1)
        in_memory_db.commit()
        
        in_memory_db.add(vm2)
        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()


class TestLabelModel:
    """Tests for Label model."""
    
    def test_create_label(self, in_memory_db):
        """Test creating a label."""
        label = Label(
            key="env",
            value="prod",
            description="Production environment",
            color="#FF0000"
        )
        in_memory_db.add(label)
        in_memory_db.commit()
        
        assert label.id is not None
        assert label.key == "env"
        assert label.value == "prod"
        assert label.created_at is not None
        assert label.updated_at is not None
    
    def test_label_unique_key_value_constraint(self, in_memory_db):
        """Test that key-value pairs must be unique."""
        label1 = Label(key="env", value="prod")
        label2 = Label(key="env", value="prod")
        
        in_memory_db.add(label1)
        in_memory_db.commit()
        
        in_memory_db.add(label2)
        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()
    
    def test_label_repr(self, in_memory_db):
        """Test label string representation."""
        label = Label(key="team", value="backend")
        
        repr_str = repr(label)
        assert "team" in repr_str
        assert "backend" in repr_str
    
    def test_label_without_optional_fields(self, in_memory_db):
        """Test creating label without description and color."""
        label = Label(key="tier", value="1")
        in_memory_db.add(label)
        in_memory_db.commit()
        
        assert label.description is None
        assert label.color is None


class TestVMLabelModel:
    """Tests for VMLabel model."""
    
    def test_create_vm_label_assignment(self, in_memory_db):
        """Test creating a VM label assignment."""
        # Create VM and Label
        vm = VirtualMachine(vm="test-vm", datacenter="DC1", cluster="CL1")
        label = Label(key="env", value="dev")
        
        in_memory_db.add(vm)
        in_memory_db.add(label)
        in_memory_db.commit()
        
        # Create assignment
        vm_label = VMLabel(
            vm_id=vm.id,
            label_id=label.id,
            assigned_by="admin"
        )
        in_memory_db.add(vm_label)
        in_memory_db.commit()
        
        assert vm_label.id is not None
        assert vm_label.vm_id == vm.id
        assert vm_label.label_id == label.id
        assert vm_label.inherited_from_folder is False
        assert vm_label.assigned_at is not None
    
    def test_vm_label_with_inheritance(self, in_memory_db):
        """Test VM label with folder inheritance."""
        vm = VirtualMachine(vm="test-vm", datacenter="DC1", cluster="CL1")
        label = Label(key="env", value="prod")
        
        in_memory_db.add(vm)
        in_memory_db.add(label)
        in_memory_db.commit()
        
        vm_label = VMLabel(
            vm_id=vm.id,
            label_id=label.id,
            inherited_from_folder=True,
            source_folder_path="/prod"
        )
        in_memory_db.add(vm_label)
        in_memory_db.commit()
        
        assert vm_label.inherited_from_folder is True
        assert vm_label.source_folder_path == "/prod"
    
    def test_vm_label_unique_constraint(self, in_memory_db):
        """Test that VM+Label combination must be unique."""
        vm = VirtualMachine(vm="test-vm", datacenter="DC1", cluster="CL1")
        label = Label(key="env", value="test")
        
        in_memory_db.add(vm)
        in_memory_db.add(label)
        in_memory_db.commit()
        
        vm_label1 = VMLabel(vm_id=vm.id, label_id=label.id)
        vm_label2 = VMLabel(vm_id=vm.id, label_id=label.id)
        
        in_memory_db.add(vm_label1)
        in_memory_db.commit()
        
        in_memory_db.add(vm_label2)
        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()
    
    def test_vm_label_cascade_delete_vm(self, in_memory_db):
        """Test that deleting VM cascades to VMLabel."""
        vm = VirtualMachine(vm="test-vm", datacenter="DC1", cluster="CL1")
        label = Label(key="env", value="dev")
        
        in_memory_db.add(vm)
        in_memory_db.add(label)
        in_memory_db.commit()
        
        vm_label = VMLabel(vm_id=vm.id, label_id=label.id)
        in_memory_db.add(vm_label)
        in_memory_db.commit()
        
        # Delete VM
        in_memory_db.delete(vm)
        in_memory_db.commit()
        
        # VMLabel should be deleted
        remaining = in_memory_db.query(VMLabel).filter_by(vm_id=vm.id).first()
        assert remaining is None
    
    def test_vm_label_cascade_delete_label(self, in_memory_db):
        """Test that deleting Label cascades to VMLabel."""
        vm = VirtualMachine(vm="test-vm", datacenter="DC1", cluster="CL1")
        label = Label(key="env", value="dev")
        
        in_memory_db.add(vm)
        in_memory_db.add(label)
        in_memory_db.commit()
        
        vm_label = VMLabel(vm_id=vm.id, label_id=label.id)
        in_memory_db.add(vm_label)
        in_memory_db.commit()
        
        # Delete Label
        in_memory_db.delete(label)
        in_memory_db.commit()
        
        # VMLabel should be deleted
        remaining = in_memory_db.query(VMLabel).filter_by(label_id=label.id).first()
        assert remaining is None


class TestFolderLabelModel:
    """Tests for FolderLabel model."""
    
    def test_create_folder_label(self, in_memory_db):
        """Test creating a folder label assignment."""
        label = Label(key="env", value="prod")
        in_memory_db.add(label)
        in_memory_db.commit()
        
        folder_label = FolderLabel(
            folder_path="/prod",
            label_id=label.id,
            assigned_by="admin",
            inherit_to_vms=True,
            inherit_to_subfolders=False
        )
        in_memory_db.add(folder_label)
        in_memory_db.commit()
        
        assert folder_label.id is not None
        assert folder_label.folder_path == "/prod"
        assert folder_label.inherit_to_vms is True
        assert folder_label.inherit_to_subfolders is False
        assert folder_label.assigned_at is not None
    
    def test_folder_label_default_values(self, in_memory_db):
        """Test folder label default values."""
        label = Label(key="tier", value="1")
        in_memory_db.add(label)
        in_memory_db.commit()
        
        folder_label = FolderLabel(
            folder_path="/test",
            label_id=label.id
        )
        in_memory_db.add(folder_label)
        in_memory_db.commit()
        
        # Check defaults
        assert folder_label.inherit_to_vms is True
        assert folder_label.inherit_to_subfolders is False
    
    def test_folder_label_unique_constraint(self, in_memory_db):
        """Test that folder_path+label_id combination must be unique."""
        label = Label(key="env", value="dev")
        in_memory_db.add(label)
        in_memory_db.commit()
        
        folder_label1 = FolderLabel(folder_path="/dev", label_id=label.id)
        folder_label2 = FolderLabel(folder_path="/dev", label_id=label.id)
        
        in_memory_db.add(folder_label1)
        in_memory_db.commit()
        
        in_memory_db.add(folder_label2)
        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()
    
    def test_folder_label_cascade_delete(self, in_memory_db):
        """Test that deleting Label cascades to FolderLabel."""
        label = Label(key="env", value="prod")
        in_memory_db.add(label)
        in_memory_db.commit()
        
        folder_label = FolderLabel(folder_path="/prod", label_id=label.id)
        in_memory_db.add(folder_label)
        in_memory_db.commit()
        
        # Delete Label
        in_memory_db.delete(label)
        in_memory_db.commit()
        
        # FolderLabel should be deleted
        remaining = in_memory_db.query(FolderLabel).filter_by(label_id=label.id).first()
        assert remaining is None


class TestModelRelationships:
    """Tests for model relationships and queries."""
    
    def test_query_vms_with_labels(self, in_memory_db):
        """Test querying VMs with their labels."""
        # Create VM and labels
        vm = VirtualMachine(vm="app-server-01", datacenter="DC1", cluster="CL1")
        label1 = Label(key="env", value="prod")
        label2 = Label(key="tier", value="app")
        
        in_memory_db.add_all([vm, label1, label2])
        in_memory_db.commit()
        
        # Assign labels
        vm_label1 = VMLabel(vm_id=vm.id, label_id=label1.id)
        vm_label2 = VMLabel(vm_id=vm.id, label_id=label2.id)
        
        in_memory_db.add_all([vm_label1, vm_label2])
        in_memory_db.commit()
        
        # Query
        labels_count = in_memory_db.query(VMLabel).filter_by(vm_id=vm.id).count()
        assert labels_count == 2
    
    def test_query_folders_with_labels(self, in_memory_db):
        """Test querying folders with their labels."""
        label = Label(key="env", value="prod")
        in_memory_db.add(label)
        in_memory_db.commit()
        
        folder_label1 = FolderLabel(folder_path="/prod", label_id=label.id)
        folder_label2 = FolderLabel(folder_path="/prod/app", label_id=label.id)
        
        in_memory_db.add_all([folder_label1, folder_label2])
        in_memory_db.commit()
        
        # Query all folders with this label
        folders = in_memory_db.query(FolderLabel).filter_by(label_id=label.id).all()
        assert len(folders) == 2
        folder_paths = [f.folder_path for f in folders]
        assert "/prod" in folder_paths
        assert "/prod/app" in folder_paths
