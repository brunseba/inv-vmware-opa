"""Excel to database loader for VMware inventory."""

from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

from .models import Base, VirtualMachine


def normalize_column_name(name: str) -> str:
    """Convert Excel column name to database field name."""
    return name.lower().replace(" ", "_").replace("#", "").replace("(", "").replace(")", "")


def parse_date(value) -> Optional[datetime]:
    """Parse date from various formats."""
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return pd.to_datetime(value)
        except:
            return None
    return None


def parse_bool(value) -> Optional[bool]:
    """Parse boolean from various formats."""
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ["yes", "true", "1"]:
            return True
        if value_lower in ["no", "false", "0"]:
            return False
    return None


def parse_int(value) -> Optional[int]:
    """Parse integer safely."""
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_float(value) -> Optional[float]:
    """Parse float safely."""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def load_excel_to_db(excel_path: Path, db_url: str, clear_existing: bool = False) -> int:
    """
    Load VMware inventory from Excel file into database.
    
    Args:
        excel_path: Path to Excel file
        db_url: SQLAlchemy database URL
        clear_existing: If True, clear existing data before loading
        
    Returns:
        Number of records loaded
    """
    # Create engine and session
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session: Session = SessionLocal()
    
    try:
        # Clear existing data if requested
        if clear_existing:
            session.query(VirtualMachine).delete()
            session.commit()
        
        # Read Excel file
        df = pd.read_excel(excel_path, sheet_name="Sheet1")
        
        # Normalize column names for easier mapping
        column_mapping = {col: normalize_column_name(col) for col in df.columns}
        
        records_loaded = 0
        
        # Process each row
        for _, row in df.iterrows():
            # Map Excel columns to model fields
            vm_data = {
                "vm": str(row["VM"]) if not pd.isna(row["VM"]) else None,
                "powerstate": str(row["Powerstate"]) if not pd.isna(row["Powerstate"]) else None,
                "template": parse_bool(row["Template"]),
                "srm_placeholder": str(row["SRM Placeholder"]) if not pd.isna(row["SRM Placeholder"]) else None,
                "config_status": str(row["Config status"]) if not pd.isna(row["Config status"]) else None,
                "dns_name": str(row["DNS Name"]) if not pd.isna(row["DNS Name"]) else None,
                "connection_state": str(row["Connection state"]) if not pd.isna(row["Connection state"]) else None,
                "guest_state": str(row["Guest state"]) if not pd.isna(row["Guest state"]) else None,
                "heartbeat": str(row["Heartbeat"]) if not pd.isna(row["Heartbeat"]) else None,
                "consolidation_needed": parse_bool(row["Consolidation Needed"]),
                "poweron": parse_date(row["PowerOn"]),
                "suspend_time": parse_date(row["Suspend time"]),
                "creation_date": parse_date(row["Creation date"]),
                "change_version": str(row["Change Version"]) if not pd.isna(row["Change Version"]) else None,
                "cpus": parse_int(row["CPUs"]),
                "memory": parse_int(row["Memory"]),
                "nics": parse_int(row["NICs"]),
                "disks": parse_int(row["Disks"]),
                "min_required_evc_mode_key": str(row["min Required EVC Mode Key"]) if not pd.isna(row["min Required EVC Mode Key"]) else None,
                "latency_sensitivity": str(row["Latency Sensitivity"]) if not pd.isna(row["Latency Sensitivity"]) else None,
                "enable_uuid": parse_bool(row["EnableUUID"]),
                "cbt": str(row["CBT"]) if not pd.isna(row["CBT"]) else None,
                "primary_ip_address": str(row["Primary IP Address"]) if not pd.isna(row["Primary IP Address"]) else None,
                "network_1": str(row["Network #1"]) if not pd.isna(row["Network #1"]) else None,
                "network_2": str(row["Network #2"]) if not pd.isna(row["Network #2"]) else None,
                "network_3": str(row["Network #3"]) if not pd.isna(row["Network #3"]) else None,
                "network_4": str(row["Network #4"]) if not pd.isna(row["Network #4"]) else None,
                "network_5": str(row["Network #5"]) if not pd.isna(row["Network #5"]) else None,
                "network_6": str(row["Network #6"]) if not pd.isna(row["Network #6"]) else None,
                "network_7": str(row["Network #7"]) if not pd.isna(row["Network #7"]) else None,
                "network_8": str(row["Network #8"]) if not pd.isna(row["Network #8"]) else None,
                "num_monitors": parse_int(row["Num Monitors"]),
                "video_ram_kib": parse_int(row["Video Ram KiB"]),
                "resource_pool": str(row["Resource pool"]) if not pd.isna(row["Resource pool"]) else None,
                "folder": str(row["Folder"]) if not pd.isna(row["Folder"]) else None,
                "vapp": str(row["vApp"]) if not pd.isna(row["vApp"]) else None,
                "das_protection": str(row["DAS protection"]) if not pd.isna(row["DAS protection"]) else None,
                "ft_state": str(row["FT State"]) if not pd.isna(row["FT State"]) else None,
                "ft_latency": parse_float(row["FT Latency"]),
                "ft_bandwidth": parse_float(row["FT Bandwidth"]),
                "ft_sec_latency": parse_float(row["FT Sec. Latency"]),
                "provisioned_mib": parse_float(row["Provisioned MiB"]),
                "in_use_mib": parse_float(row["In Use MiB"]),
                "unshared_mib": parse_float(row["Unshared MiB"]),
                "ha_restart_priority": str(row["HA Restart Priority"]) if not pd.isna(row["HA Restart Priority"]) else None,
                "ha_isolation_response": str(row["HA Isolation Response"]) if not pd.isna(row["HA Isolation Response"]) else None,
                "ha_vm_monitoring": str(row["HA VM Monitoring"]) if not pd.isna(row["HA VM Monitoring"]) else None,
                "cluster_rules": str(row["Cluster rule(s)"]) if not pd.isna(row["Cluster rule(s)"]) else None,
                "cluster_rule_names": str(row["Cluster rule name(s)"]) if not pd.isna(row["Cluster rule name(s)"]) else None,
                "boot_required": parse_bool(row["Boot Required"]),
                "boot_delay": parse_int(row["Boot delay"]),
                "boot_retry_delay": parse_int(row["Boot retry delay"]),
                "boot_retry_enabled": parse_bool(row["Boot retry enabled"]),
                "boot_bios_setup": parse_bool(row["Boot BIOS setup"]),
                "firmware": str(row["Firmware"]) if not pd.isna(row["Firmware"]) else None,
                "hw_version": str(row["HW version"]) if not pd.isna(row["HW version"]) else None,
                "hw_upgrade_status": str(row["HW upgrade status"]) if not pd.isna(row["HW upgrade status"]) else None,
                "hw_upgrade_policy": str(row["HW upgrade policy"]) if not pd.isna(row["HW upgrade policy"]) else None,
                "hw_target": str(row["HW target"]) if not pd.isna(row["HW target"]) else None,
                "path": str(row["Path"]) if not pd.isna(row["Path"]) else None,
                "log_directory": str(row["Log directory"]) if not pd.isna(row["Log directory"]) else None,
                "snapshot_directory": str(row["Snapshot directory"]) if not pd.isna(row["Snapshot directory"]) else None,
                "suspend_directory": str(row["Suspend directory"]) if not pd.isna(row["Suspend directory"]) else None,
                "annotation": str(row["Annotation"]) if not pd.isna(row["Annotation"]) else None,
                "nb_last_backup": parse_date(row["NB_LAST_BACKUP"]),
                "datacenter": str(row["Datacenter"]) if not pd.isna(row["Datacenter"]) else None,
                "cluster": str(row["Cluster"]) if not pd.isna(row["Cluster"]) else None,
                "host": str(row["Host"]) if not pd.isna(row["Host"]) else None,
                "os_config": str(row["OS according to the configuration file"]) if not pd.isna(row["OS according to the configuration file"]) else None,
                "os_vmware_tools": str(row["OS according to the VMware Tools"]) if not pd.isna(row["OS according to the VMware Tools"]) else None,
                "vm_id": str(row["VM ID"]) if not pd.isna(row["VM ID"]) else None,
                "vm_uuid": str(row["VM UUID"]) if not pd.isna(row["VM UUID"]) else None,
                "vi_sdk_server_type": str(row["VI SDK Server type"]) if not pd.isna(row["VI SDK Server type"]) else None,
                "vi_sdk_api_version": str(row["VI SDK API Version"]) if not pd.isna(row["VI SDK API Version"]) else None,
                "code_ccx": str(row["CODE_CCX"]) if not pd.isna(row["CODE_CCX"]) else None,
                "vm_nbu": str(row["VM_NBU"]) if not pd.isna(row["VM_NBU"]) else None,
                "vm_orchid": str(row["VM_ORCHID"]) if not pd.isna(row["VM_ORCHID"]) else None,
                "licence_enforcement": str(row["Licence Enforcement"]) if not pd.isna(row["Licence Enforcement"]) else None,
                "env": str(row["Env"]) if not pd.isna(row["Env"]) else None,
            }
            
            # Skip if VM name is missing
            if not vm_data["vm"]:
                continue
            
            vm = VirtualMachine(**vm_data)
            session.add(vm)
            records_loaded += 1
        
        # Commit all records
        session.commit()
        return records_loaded
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
