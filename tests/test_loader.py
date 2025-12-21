"""Unit tests for loader module."""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.loader import (
    normalize_column_name,
    parse_date,
    parse_bool,
    parse_int,
    parse_float,
    get_sheet_names,
    load_excel_to_db,
)
from src.models import Base, VirtualMachine
import pandas as pd


def test_normalize_column_name():
    """Test column name normalization."""
    assert normalize_column_name("VM Name") == "vm_name"
    assert normalize_column_name("Network #1") == "network_1"
    assert normalize_column_name("CPU(s)") == "cpus"
    assert normalize_column_name("Power State") == "power_state"


def test_parse_date():
    """Test date parsing."""
    # Valid datetime
    dt = datetime(2024, 1, 15)
    assert parse_date(dt) == dt

    # None/NaN
    assert parse_date(None) is None
    assert parse_date(pd.NaT) is None

    # String date
    result = parse_date("2024-01-15")
    assert result is not None
    assert result.year == 2024


def test_parse_bool():
    """Test boolean parsing."""
    # True values
    assert parse_bool(True) is True
    assert parse_bool("yes") is True
    assert parse_bool("Yes") is True
    assert parse_bool("true") is True
    assert parse_bool("1") is True

    # False values
    assert parse_bool(False) is False
    assert parse_bool("no") is False
    assert parse_bool("No") is False
    assert parse_bool("false") is False
    assert parse_bool("0") is False

    # None/invalid
    assert parse_bool(None) is None
    assert parse_bool(pd.NA) is None
    assert parse_bool("invalid") is None


def test_parse_int():
    """Test integer parsing."""
    assert parse_int(42) == 42
    assert parse_int("42") == 42
    assert parse_int(42.0) == 42
    assert parse_int(None) is None
    assert parse_int(pd.NA) is None
    assert parse_int("not a number") is None


def test_parse_float():
    """Test float parsing."""
    assert parse_float(42.5) == 42.5
    assert parse_float("42.5") == 42.5
    assert parse_float(42) == 42.0
    assert parse_float(None) is None
    assert parse_float(pd.NA) is None
    assert parse_float("not a number") is None


class TestParseEdgeCases:
    """Test edge cases for parsing functions."""

    def test_parse_date_invalid_string(self):
        """Test parse_date with invalid string."""
        assert parse_date("not a date") is None
        # Empty string returns NaT which is considered None-like
        result = parse_date("")
        assert result is None or pd.isna(result)

    def test_parse_bool_with_whitespace(self):
        """Test parse_bool handles whitespace."""
        assert parse_bool(" yes ") is True
        assert parse_bool(" no ") is False

    def test_parse_int_with_float(self):
        """Test parse_int converts float to int."""
        assert parse_int(42.9) == 42
        # String "42.9" fails int() conversion, returns None
        assert parse_int("42.9") is None

    def test_parse_float_edge_values(self):
        """Test parse_float with edge values."""
        assert parse_float(0.0) == 0.0
        assert parse_float(-42.5) == -42.5
        assert parse_float("0") == 0.0


@pytest.fixture
def sample_excel_file():
    """Create a sample Excel file for testing."""
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)

    # Create sample data matching expected Excel format
    data = {
        "VM": ["test-vm-1", "test-vm-2"],
        "Powerstate": ["poweredOn", "poweredOff"],
        "Template": ["No", "No"],
        "SRM Placeholder": ["", ""],
        "Config status": ["green", "green"],
        "DNS Name": ["vm1.test.com", "vm2.test.com"],
        "Connection state": ["connected", "connected"],
        "Guest state": ["running", "notRunning"],
        "Heartbeat": ["green", "gray"],
        "Consolidation Needed": ["No", "No"],
        "PowerOn": ["2024-01-15", ""],
        "Suspend time": ["", ""],
        "Creation date": ["2023-01-01", "2023-06-01"],
        "Change Version": ["1", "2"],
        "CPUs": [4, 2],
        "Memory": [8192, 4096],
        "NICs": [1, 1],
        "Disks": [1, 1],
        "min Required EVC Mode Key": ["", ""],
        "Latency Sensitivity": ["normal", "normal"],
        "EnableUUID": ["Yes", "Yes"],
        "CBT": ["enabled", "enabled"],
        "Primary IP Address": ["192.168.1.10", "192.168.1.11"],
        "Network #1": ["VM Network", "VM Network"],
        "Network #2": ["", ""],
        "Network #3": ["", ""],
        "Network #4": ["", ""],
        "Network #5": ["", ""],
        "Network #6": ["", ""],
        "Network #7": ["", ""],
        "Network #8": ["", ""],
        "Num Monitors": [1, 1],
        "Video Ram KiB": [4096, 4096],
        "Resource pool": ["Resources", "Resources"],
        "Folder": ["/Datacenter/vm", "/Datacenter/vm"],
        "vApp": ["", ""],
        "DAS protection": ["protected", "protected"],
        "FT State": ["notConfigured", "notConfigured"],
        "FT Latency": [0.0, 0.0],
        "FT Bandwidth": [0.0, 0.0],
        "FT Sec. Latency": [0.0, 0.0],
        "Provisioned MiB": [102400.0, 51200.0],
        "In Use MiB": [51200.0, 25600.0],
        "Unshared MiB": [51200.0, 25600.0],
        "HA Restart Priority": ["medium", "medium"],
        "HA Isolation Response": ["none", "none"],
        "HA VM Monitoring": ["vmMonitoringDisabled", "vmMonitoringDisabled"],
        "Cluster rule(s)": ["", ""],
        "Cluster rule name(s)": ["", ""],
        "Boot Required": ["No", "No"],
        "Boot delay": [0, 0],
        "Boot retry delay": [10000, 10000],
        "Boot retry enabled": ["Yes", "Yes"],
        "Boot BIOS setup": ["No", "No"],
        "Firmware": ["bios", "bios"],
        "HW version": ["vmx-19", "vmx-19"],
        "HW upgrade status": ["none", "none"],
        "HW upgrade policy": ["never", "never"],
        "HW target": ["", ""],
        "Path": ["/vmfs/volumes/datastore1/vm1", "/vmfs/volumes/datastore1/vm2"],
        "Log directory": ["", ""],
        "Snapshot directory": ["", ""],
        "Suspend directory": ["", ""],
        "Annotation": ["Test VM 1", "Test VM 2"],
        "NB_LAST_BACKUP": ["", ""],
        "Datacenter": ["DC1", "DC1"],
        "Cluster": ["Cluster-A", "Cluster-A"],
        "Host": ["host1.test.com", "host2.test.com"],
        "OS according to the configuration file": ["Ubuntu Linux (64-bit)", "CentOS 7 (64-bit)"],
        "OS according to the VMware Tools": ["Ubuntu Linux (64-bit)", "CentOS 7 (64-bit)"],
        "VM ID": ["vm-1001", "vm-1002"],
        "VM UUID": ["52345678-1234-1234-1234-123456789012", "52345678-1234-1234-1234-123456789013"],
        "VI SDK Server type": ["VirtualCenter", "VirtualCenter"],
        "VI SDK API Version": ["7.0", "7.0"],
        "CODE_CCX": ["", ""],
        "VM_NBU": ["", ""],
        "VM_ORCHID": ["", ""],
        "Licence Enforcement": ["", ""],
        "Env": ["prod", "dev"],
    }

    df = pd.DataFrame(data)
    df.to_excel(path, index=False, sheet_name="Sheet1")

    yield Path(path)

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite:///{path}"

    # Create schema
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    engine.dispose()

    yield db_url

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


class TestGetSheetNames:
    """Test get_sheet_names function."""

    def test_get_sheet_names(self, sample_excel_file):
        """Test getting sheet names from Excel file."""
        sheet_names = get_sheet_names(sample_excel_file)
        assert isinstance(sheet_names, list)
        assert "Sheet1" in sheet_names
        assert len(sheet_names) > 0


class TestLoadExcelToDB:
    """Test load_excel_to_db function."""

    def test_load_basic(self, sample_excel_file, test_db):
        """Test basic Excel file loading."""
        records = load_excel_to_db(sample_excel_file, test_db, clear_existing=False)

        assert records == 2  # 2 VMs in sample data

        # Verify data was loaded
        engine = create_engine(test_db, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        vms = session.query(VirtualMachine).all()
        assert len(vms) == 2
        assert vms[0].vm == "test-vm-1"
        assert vms[0].powerstate == "poweredOn"
        assert vms[0].cpus == 4
        assert vms[0].memory == 8192

        session.close()
        engine.dispose()

    def test_load_with_clear_existing(self, sample_excel_file, test_db):
        """Test loading with clear_existing=True."""
        # Load first time
        records1 = load_excel_to_db(sample_excel_file, test_db, clear_existing=False)
        assert records1 == 2

        # Load again with clear
        records2 = load_excel_to_db(sample_excel_file, test_db, clear_existing=True)
        assert records2 == 2

        # Verify only 2 VMs (not 4)
        engine = create_engine(test_db, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        vms = session.query(VirtualMachine).all()
        assert len(vms) == 2

        session.close()
        engine.dispose()

    def test_load_handles_empty_vm_names(self, test_db):
        """Test that rows with empty VM names are skipped."""
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)

        # Create data with empty VM name
        data = {
            "VM": ["", "test-vm-1"],  # First row has empty VM name
            "Powerstate": ["poweredOn", "poweredOn"],
            "Datacenter": ["DC1", "DC1"],
        }
        # Add all required columns with empty values
        required_cols = [
            "Template",
            "SRM Placeholder",
            "Config status",
            "DNS Name",
            "Connection state",
            "Guest state",
            "Heartbeat",
            "Consolidation Needed",
            "PowerOn",
            "Suspend time",
            "Creation date",
            "Change Version",
            "CPUs",
            "Memory",
            "NICs",
            "Disks",
            "min Required EVC Mode Key",
            "Latency Sensitivity",
            "EnableUUID",
            "CBT",
            "Primary IP Address",
            "Network #1",
            "Network #2",
            "Network #3",
            "Network #4",
            "Network #5",
            "Network #6",
            "Network #7",
            "Network #8",
            "Num Monitors",
            "Video Ram KiB",
            "Resource pool",
            "Folder",
            "vApp",
            "DAS protection",
            "FT State",
            "FT Latency",
            "FT Bandwidth",
            "FT Sec. Latency",
            "Provisioned MiB",
            "In Use MiB",
            "Unshared MiB",
            "HA Restart Priority",
            "HA Isolation Response",
            "HA VM Monitoring",
            "Cluster rule(s)",
            "Cluster rule name(s)",
            "Boot Required",
            "Boot delay",
            "Boot retry delay",
            "Boot retry enabled",
            "Boot BIOS setup",
            "Firmware",
            "HW version",
            "HW upgrade status",
            "HW upgrade policy",
            "HW target",
            "Path",
            "Log directory",
            "Snapshot directory",
            "Suspend directory",
            "Annotation",
            "NB_LAST_BACKUP",
            "Cluster",
            "Host",
            "OS according to the configuration file",
            "OS according to the VMware Tools",
            "VM ID",
            "VM UUID",
            "VI SDK Server type",
            "VI SDK API Version",
            "CODE_CCX",
            "VM_NBU",
            "VM_ORCHID",
            "Licence Enforcement",
            "Env",
        ]
        for col in required_cols:
            data[col] = ["", ""]

        df = pd.DataFrame(data)
        df.to_excel(path, index=False)

        records = load_excel_to_db(Path(path), test_db, clear_existing=True)
        assert records == 1  # Only 1 VM should be loaded (empty VM name skipped)

        os.unlink(path)
