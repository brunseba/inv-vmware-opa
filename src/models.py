"""Database models for VMware inventory."""

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class VirtualMachine(Base):
    """Model representing a VMware virtual machine."""
    
    __tablename__ = "virtual_machines"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Basic VM information
    vm: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    powerstate: Mapped[str | None] = mapped_column(String(50), index=True)  # Frequently filtered
    template: Mapped[bool | None] = mapped_column(Boolean, index=True)  # Frequently filtered
    srm_placeholder: Mapped[str | None] = mapped_column(String(50))
    config_status: Mapped[str | None] = mapped_column(String(50))
    dns_name: Mapped[str | None] = mapped_column(String(255))
    connection_state: Mapped[str | None] = mapped_column(String(50))
    guest_state: Mapped[str | None] = mapped_column(String(50))
    heartbeat: Mapped[str | None] = mapped_column(String(50))
    consolidation_needed: Mapped[bool | None] = mapped_column(Boolean)
    
    # Power and timing
    poweron: Mapped[datetime | None] = mapped_column(DateTime)
    suspend_time: Mapped[datetime | None] = mapped_column(DateTime)
    creation_date: Mapped[datetime | None] = mapped_column(DateTime, index=True)  # Used in filters and trends
    change_version: Mapped[str | None] = mapped_column(String(50))
    
    # Resources
    cpus: Mapped[int | None] = mapped_column(Integer)
    memory: Mapped[int | None] = mapped_column(Integer)
    nics: Mapped[int | None] = mapped_column(Integer)
    disks: Mapped[int | None] = mapped_column(Integer)
    
    # Configuration
    min_required_evc_mode_key: Mapped[str | None] = mapped_column(String(100))
    latency_sensitivity: Mapped[str | None] = mapped_column(String(50))
    enable_uuid: Mapped[bool | None] = mapped_column(Boolean)
    cbt: Mapped[str | None] = mapped_column(String(50))
    
    # Network
    primary_ip_address: Mapped[str | None] = mapped_column(String(50))
    network_1: Mapped[str | None] = mapped_column(String(255))
    network_2: Mapped[str | None] = mapped_column(String(255))
    network_3: Mapped[str | None] = mapped_column(String(255))
    network_4: Mapped[str | None] = mapped_column(String(255))
    network_5: Mapped[str | None] = mapped_column(String(255))
    network_6: Mapped[str | None] = mapped_column(String(255))
    network_7: Mapped[str | None] = mapped_column(String(255))
    network_8: Mapped[str | None] = mapped_column(String(255))
    
    # Display
    num_monitors: Mapped[int | None] = mapped_column(Integer)
    video_ram_kib: Mapped[int | None] = mapped_column(Integer)
    
    # Organization
    resource_pool: Mapped[str | None] = mapped_column(String(255), index=True)  # Frequently grouped
    folder: Mapped[str | None] = mapped_column(String(500), index=True)  # Frequently grouped/filtered
    vapp: Mapped[str | None] = mapped_column(String(255))
    
    # HA/FT
    das_protection: Mapped[str | None] = mapped_column(String(50))
    ft_state: Mapped[str | None] = mapped_column(String(50))
    ft_latency: Mapped[float | None] = mapped_column(Float)
    ft_bandwidth: Mapped[float | None] = mapped_column(Float)
    ft_sec_latency: Mapped[float | None] = mapped_column(Float)
    
    # Storage
    provisioned_mib: Mapped[float | None] = mapped_column(Float)
    in_use_mib: Mapped[float | None] = mapped_column(Float)
    unshared_mib: Mapped[float | None] = mapped_column(Float)
    
    # HA Configuration
    ha_restart_priority: Mapped[str | None] = mapped_column(String(50))
    ha_isolation_response: Mapped[str | None] = mapped_column(String(50))
    ha_vm_monitoring: Mapped[str | None] = mapped_column(String(50))
    cluster_rules: Mapped[str | None] = mapped_column(Text)
    cluster_rule_names: Mapped[str | None] = mapped_column(Text)
    
    # Boot configuration
    boot_required: Mapped[bool | None] = mapped_column(Boolean)
    boot_delay: Mapped[int | None] = mapped_column(Integer)
    boot_retry_delay: Mapped[int | None] = mapped_column(Integer)
    boot_retry_enabled: Mapped[bool | None] = mapped_column(Boolean)
    boot_bios_setup: Mapped[bool | None] = mapped_column(Boolean)
    
    # Hardware
    firmware: Mapped[str | None] = mapped_column(String(50))
    hw_version: Mapped[str | None] = mapped_column(String(50))
    hw_upgrade_status: Mapped[str | None] = mapped_column(String(50))
    hw_upgrade_policy: Mapped[str | None] = mapped_column(String(50))
    hw_target: Mapped[str | None] = mapped_column(String(50))
    
    # Paths
    path: Mapped[str | None] = mapped_column(String(1000))
    log_directory: Mapped[str | None] = mapped_column(String(1000))
    snapshot_directory: Mapped[str | None] = mapped_column(String(1000))
    suspend_directory: Mapped[str | None] = mapped_column(String(1000))
    
    # Additional info
    annotation: Mapped[str | None] = mapped_column(Text)
    nb_last_backup: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Infrastructure
    datacenter: Mapped[str | None] = mapped_column(String(255), index=True)
    cluster: Mapped[str | None] = mapped_column(String(255), index=True)
    host: Mapped[str | None] = mapped_column(String(255), index=True)
    
    # OS
    os_config: Mapped[str | None] = mapped_column(String(255), index=True)  # Frequently grouped
    os_vmware_tools: Mapped[str | None] = mapped_column(String(255))
    
    # Identifiers
    vm_id: Mapped[str | None] = mapped_column(String(50), index=True)
    vm_uuid: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    
    # SDK Info
    vi_sdk_server_type: Mapped[str | None] = mapped_column(String(50))
    vi_sdk_api_version: Mapped[str | None] = mapped_column(String(50))
    
    # Custom fields
    code_ccx: Mapped[str | None] = mapped_column(String(100))
    vm_nbu: Mapped[str | None] = mapped_column(String(100))
    vm_orchid: Mapped[str | None] = mapped_column(String(100))
    licence_enforcement: Mapped[str | None] = mapped_column(String(50))
    env: Mapped[str | None] = mapped_column(String(50), index=True)
    
    # Metadata
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<VirtualMachine(vm='{self.vm}', datacenter='{self.datacenter}', cluster='{self.cluster}')>"


class Label(Base):
    """Label definitions - master list of available labels."""
    
    __tablename__ = "labels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    color: Mapped[str | None] = mapped_column(String(7))  # Hex color: #RRGGBB
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('key', 'value', name='_label_key_value_uc'),
    )
    
    def __repr__(self) -> str:
        return f"<Label(key='{self.key}', value='{self.value}')>"


class VMLabel(Base):
    """VM to Label assignment (many-to-many relationship)."""
    
    __tablename__ = "vm_labels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vm_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('virtual_machines.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    label_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('labels.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[str | None] = mapped_column(String(100))
    inherited_from_folder: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    source_folder_path: Mapped[str | None] = mapped_column(String(500))
    
    __table_args__ = (
        UniqueConstraint('vm_id', 'label_id', name='_vm_label_uc'),
    )
    
    def __repr__(self) -> str:
        return f"<VMLabel(vm_id={self.vm_id}, label_id={self.label_id}, inherited={self.inherited_from_folder})>"


class FolderLabel(Base):
    """Folder path to Label assignment."""
    
    __tablename__ = "folder_labels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folder_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    label_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('labels.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[str | None] = mapped_column(String(100))
    inherit_to_vms: Mapped[bool] = mapped_column(Boolean, default=True)
    inherit_to_subfolders: Mapped[bool] = mapped_column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('folder_path', 'label_id', name='_folder_label_uc'),
    )
    
    def __repr__(self) -> str:
        return f"<FolderLabel(folder_path='{self.folder_path}', label_id={self.label_id})>"
