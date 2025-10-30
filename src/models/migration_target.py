"""Migration target models for multi-platform migration planning."""

from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base


class PlatformType(enum.Enum):
    """Supported migration target platforms."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    VMWARE_CLOUD = "vmware_cloud"
    ON_PREM = "on_prem"
    OPENSTACK = "openstack"
    KUBERNETES = "kubernetes"
    OTHER = "other"


class MigrationStrategy(enum.Enum):
    """Migration strategies (6Rs framework)."""
    REHOST = "rehost"  # Lift and shift
    REPLATFORM = "replatform"  # Lift, tinker, and shift
    REFACTOR = "refactor"  # Re-architect
    REPURCHASE = "repurchase"  # Move to SaaS
    RETIRE = "retire"  # Decommission
    RETAIN = "retain"  # Keep as-is


class MigrationTarget(Base):
    """Migration target configuration."""
    
    __tablename__ = "migration_targets"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    platform_type = Column(Enum(PlatformType), nullable=False)
    region = Column(String(100))  # e.g., us-east-1, westeurope
    
    # Network configuration
    bandwidth_mbps = Column(Integer, default=1000)  # Dedicated migration bandwidth
    network_efficiency = Column(Float, default=0.8)  # 80% efficiency
    
    # Cost factors (per hour)
    compute_cost_per_vcpu = Column(Float, default=0.0)
    memory_cost_per_gb = Column(Float, default=0.0)
    storage_cost_per_gb = Column(Float, default=0.0)
    network_ingress_cost_per_gb = Column(Float, default=0.0)
    network_egress_cost_per_gb = Column(Float, default=0.0)
    
    # Platform-specific attributes (JSON)
    platform_attributes = Column(JSON, default=dict)
    # Examples:
    # AWS: {"account_id": "...", "vpc_id": "...", "instance_types": [...]}
    # Azure: {"subscription_id": "...", "resource_group": "...", "vm_sizes": [...]}
    # GCP: {"project_id": "...", "zone": "...", "machine_types": [...]}
    
    # Constraints
    max_parallel_migrations = Column(Integer, default=10)
    min_required_bandwidth_mbps = Column(Integer, default=100)
    supports_live_migration = Column(Boolean, default=False)
    
    # Service level
    sla_uptime_percent = Column(Float, default=99.9)
    support_level = Column(String(50))  # e.g., "24/7", "business hours"
    
    # Active/enabled
    is_active = Column(Boolean, default=True)
    
    # Relationships
    scenarios = relationship("MigrationScenario", back_populates="target", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MigrationTarget(name={self.name}, platform={self.platform_type.value})>"


class MigrationScenario(Base):
    """Migration scenario combining VMs, targets, and strategies."""
    
    __tablename__ = "migration_scenarios"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    
    # Target
    target_id = Column(Integer, ForeignKey("migration_targets.id"), nullable=False)
    target = relationship("MigrationTarget", back_populates="scenarios")
    
    # Strategy
    strategy = Column(Enum(MigrationStrategy), nullable=False, default=MigrationStrategy.REHOST)
    
    # VM selection criteria (JSON)
    vm_selection_criteria = Column(JSON, default=dict)
    # Examples:
    # {"datacenters": ["DC1"], "clusters": ["Cluster-A"]}
    # {"folders": ["/Production/WebServers"]}
    # {"vm_ids": [1, 2, 3, 4, 5]}
    
    # Timeline
    estimated_duration_days = Column(Float)
    estimated_cost_total = Column(Float)
    estimated_cost_breakdown = Column(JSON, default=dict)
    # {"compute": 1000, "storage": 500, "network": 200, "labor": 5000}
    
    # Risk assessment
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors = Column(JSON, default=list)
    # ["downtime_required", "data_sovereignty", "compliance"]
    
    # Recommendations
    recommended = Column(Boolean, default=False)
    recommendation_score = Column(Float)  # 0-100
    recommendation_reasons = Column(JSON, default=list)
    
    # Metadata
    created_at = Column(String(50))
    updated_at = Column(String(50))
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<MigrationScenario(name={self.name}, target={self.target.name if self.target else 'None'}, strategy={self.strategy.value})>"


class MigrationWave(Base):
    """Migration wave for phased migration execution."""
    
    __tablename__ = "migration_waves"
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("migration_scenarios.id"), nullable=False)
    
    wave_number = Column(Integer, nullable=False)
    wave_name = Column(String(255))
    
    # VM list (JSON array of VM IDs)
    vm_ids = Column(JSON, default=list)
    
    # Timeline
    start_date = Column(String(50))
    end_date = Column(String(50))
    duration_hours = Column(Float)
    
    # Status
    status = Column(String(50), default="planned")  # planned, in_progress, completed, failed
    
    # Dependencies
    depends_on_wave_ids = Column(JSON, default=list)  # Previous waves that must complete first
    
    def __repr__(self):
        return f"<MigrationWave(scenario_id={self.scenario_id}, wave={self.wave_number}, vms={len(self.vm_ids or [])})>"
