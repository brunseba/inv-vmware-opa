"""Unit tests for migration scenario service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.models.base import Base
from src.models import VirtualMachine
from src.models.migration_target import (
    MigrationTarget,
    MigrationScenario,
    MigrationWave,
    PlatformType,
    MigrationStrategy
)
from src.services.migration_scenarios import MigrationScenarioService


@pytest.fixture
def session():
    """Create in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def service(session):
    """Create migration scenario service instance."""
    return MigrationScenarioService(session)


@pytest.fixture
def sample_vms(session):
    """Create sample VMs for testing."""
    vms = [
        VirtualMachine(
            VM="test-vm-1",
            Powerstate="poweredOn",
            CPUs=4,
            Memory=8192,  # MB
            Provisioned_MiB=102400,  # 100 GB
            Datacenter="DC1",
            Cluster="Cluster-A"
        ),
        VirtualMachine(
            VM="test-vm-2",
            Powerstate="poweredOn",
            CPUs=2,
            Memory=4096,
            Provisioned_MiB=51200,  # 50 GB
            Datacenter="DC1",
            Cluster="Cluster-A"
        ),
        VirtualMachine(
            VM="test-vm-3",
            Powerstate="poweredOn",
            CPUs=8,
            Memory=16384,
            Provisioned_MiB=204800,  # 200 GB
            Datacenter="DC1",
            Cluster="Cluster-B"
        )
    ]
    for vm in vms:
        session.add(vm)
    session.commit()
    return vms


@pytest.fixture
def aws_target(service):
    """Create AWS migration target."""
    return service.create_target(
        name="AWS US-East-1",
        platform_type=PlatformType.AWS,
        region="us-east-1",
        bandwidth_mbps=10000,
        network_efficiency=0.8,
        compute_cost_per_vcpu=0.05,
        memory_cost_per_gb=0.01,
        storage_cost_per_gb=0.001,
        network_ingress_cost_per_gb=0.0,
        network_egress_cost_per_gb=0.09,
        max_parallel_migrations=20,
        supports_live_migration=False
    )


@pytest.fixture
def azure_target(service):
    """Create Azure migration target."""
    return service.create_target(
        name="Azure West Europe",
        platform_type=PlatformType.AZURE,
        region="westeurope",
        bandwidth_mbps=10000,
        network_efficiency=0.8,
        compute_cost_per_vcpu=0.06,
        memory_cost_per_gb=0.012,
        storage_cost_per_gb=0.0015,
        network_ingress_cost_per_gb=0.0,
        network_egress_cost_per_gb=0.087,
        max_parallel_migrations=15,
        supports_live_migration=True
    )


class TestMigrationScenarioService:
    """Test suite for MigrationScenarioService."""
    
    def test_create_target(self, service):
        """Test creating a migration target."""
        target = service.create_target(
            name="Test Target",
            platform_type=PlatformType.GCP,
            region="us-central1"
        )
        
        assert target.id is not None
        assert target.name == "Test Target"
        assert target.platform_type == PlatformType.GCP
        assert target.region == "us-central1"
        assert target.is_active is True
    
    def test_get_active_targets(self, service, aws_target, azure_target):
        """Test retrieving active targets."""
        targets = service.get_active_targets()
        
        assert len(targets) == 2
        assert aws_target in targets
        assert azure_target in targets
    
    def test_calculate_migration_cost(self, service, sample_vms, aws_target):
        """Test migration cost calculation."""
        cost_breakdown = service.calculate_migration_cost(
            vms=sample_vms,
            target=aws_target,
            duration_days=30
        )
        
        assert "compute" in cost_breakdown
        assert "memory" in cost_breakdown
        assert "storage" in cost_breakdown
        assert "network" in cost_breakdown
        assert "labor" in cost_breakdown
        assert "total" in cost_breakdown
        
        assert cost_breakdown["total"] > 0
        assert cost_breakdown["total"] == sum([
            cost_breakdown["compute"],
            cost_breakdown["memory"],
            cost_breakdown["storage"],
            cost_breakdown["network"],
            cost_breakdown["labor"]
        ])
    
    def test_calculate_migration_duration(self, service, sample_vms, aws_target):
        """Test migration duration calculation."""
        duration = service.calculate_migration_duration(
            vms=sample_vms,
            target=aws_target,
            parallel_migrations=2
        )
        
        assert "replication_hours_per_vm" in duration
        assert "total_hours_per_vm" in duration
        assert "total_migration_hours" in duration
        assert "total_days" in duration
        assert "migration_waves" in duration
        
        # 3 VMs with parallelism of 2 should create 2 waves
        assert duration["migration_waves"] == 2
        assert duration["total_days"] > 0
    
    def test_assess_risk_level_low(self, service, aws_target):
        """Test risk assessment for low-risk scenario."""
        # Small number of VMs with small data volume
        small_vms = [
            VirtualMachine(
                VM=f"vm-{i}",
                CPUs=2,
                Memory=4096,
                Provisioned_MiB=10240  # 10 GB
            ) for i in range(5)
        ]
        
        risk_level, risk_factors = service.assess_risk_level(
            vms=small_vms,
            target=aws_target,
            strategy=MigrationStrategy.REHOST
        )
        
        assert risk_level == "LOW"
        assert len(risk_factors) >= 0
    
    def test_assess_risk_level_high(self, service, aws_target):
        """Test risk assessment for high-risk scenario."""
        # Large number of VMs with large data volume
        large_vms = [
            VirtualMachine(
                VM=f"vm-{i}",
                CPUs=8,
                Memory=16384,
                Provisioned_MiB=1048576  # 1 TB
            ) for i in range(150)
        ]
        
        risk_level, risk_factors = service.assess_risk_level(
            vms=large_vms,
            target=aws_target,
            strategy=MigrationStrategy.REFACTOR
        )
        
        assert risk_level in ["HIGH", "CRITICAL"]
        assert "large_vm_count" in risk_factors
        assert "large_data_volume" in risk_factors
        assert "complex_migration_strategy" in risk_factors
    
    def test_calculate_recommendation_score(self, service, aws_target):
        """Test recommendation score calculation."""
        cost_breakdown = {
            "compute": 1000,
            "memory": 500,
            "storage": 200,
            "network": 100,
            "labor": 1500,
            "total": 3300
        }
        duration = {
            "total_days": 5
        }
        
        score = service.calculate_recommendation_score(
            cost_breakdown=cost_breakdown,
            duration=duration,
            risk_level="LOW",
            target=aws_target
        )
        
        assert 0 <= score <= 100
        # Low cost, short duration, low risk should yield high score
        assert score > 70
    
    def test_create_scenario(self, service, sample_vms, aws_target):
        """Test creating a migration scenario."""
        scenario = service.create_scenario(
            name="Test Scenario",
            target_id=aws_target.id,
            vm_selection_criteria={"datacenters": ["DC1"]},
            strategy=MigrationStrategy.REHOST
        )
        
        assert scenario.id is not None
        assert scenario.name == "Test Scenario"
        assert scenario.target_id == aws_target.id
        assert scenario.strategy == MigrationStrategy.REHOST
        assert scenario.estimated_duration_days is not None
        assert scenario.estimated_cost_total is not None
        assert scenario.risk_level is not None
        assert scenario.recommendation_score is not None
    
    def test_compare_scenarios(self, service, sample_vms, aws_target, azure_target):
        """Test comparing multiple scenarios."""
        # Create two scenarios
        scenario1 = service.create_scenario(
            name="AWS Scenario",
            target_id=aws_target.id,
            vm_selection_criteria={"datacenters": ["DC1"]},
            strategy=MigrationStrategy.REHOST
        )
        
        scenario2 = service.create_scenario(
            name="Azure Scenario",
            target_id=azure_target.id,
            vm_selection_criteria={"datacenters": ["DC1"]},
            strategy=MigrationStrategy.REPLATFORM
        )
        
        # Compare scenarios
        comparison_df = service.compare_scenarios([scenario1.id, scenario2.id])
        
        assert len(comparison_df) == 2
        assert "Scenario" in comparison_df.columns
        assert "Target" in comparison_df.columns
        assert "Platform" in comparison_df.columns
        assert "Strategy" in comparison_df.columns
        assert "Duration (days)" in comparison_df.columns
        assert "Total Cost ($)" in comparison_df.columns
        assert "Risk Level" in comparison_df.columns
        assert "Score" in comparison_df.columns
    
    def test_generate_migration_waves(self, service, sample_vms, aws_target):
        """Test generating migration waves."""
        scenario = service.create_scenario(
            name="Wave Test Scenario",
            target_id=aws_target.id,
            vm_selection_criteria={"datacenters": ["DC1"]},
            strategy=MigrationStrategy.REHOST
        )
        
        waves = service.generate_migration_waves(
            scenario_id=scenario.id,
            wave_size=2,
            strategy="size_based"
        )
        
        # 3 VMs with wave size of 2 should create 2 waves
        assert len(waves) == 2
        assert waves[0].wave_number == 1
        assert waves[1].wave_number == 2
        assert len(waves[0].vm_ids) == 2
        assert len(waves[1].vm_ids) == 1
        
        # Second wave should depend on first
        assert 1 in waves[1].depends_on_wave_ids
    
    def test_vm_selection_by_cluster(self, service, sample_vms, aws_target):
        """Test VM selection by cluster."""
        scenario = service.create_scenario(
            name="Cluster A Only",
            target_id=aws_target.id,
            vm_selection_criteria={"clusters": ["Cluster-A"]},
            strategy=MigrationStrategy.REHOST
        )
        
        # Should only select VMs from Cluster-A (2 VMs)
        vms = service._get_vms_by_criteria(scenario.vm_selection_criteria)
        assert len(vms) == 2
        assert all(vm.Cluster == "Cluster-A" for vm in vms)
    
    def test_empty_vm_selection_raises_error(self, service, aws_target):
        """Test that empty VM selection raises an error."""
        with pytest.raises(ValueError, match="No VMs match the selection criteria"):
            service.create_scenario(
                name="Empty Scenario",
                target_id=aws_target.id,
                vm_selection_criteria={"datacenters": ["NonExistent"]},
                strategy=MigrationStrategy.REHOST
            )
    
    def test_invalid_target_raises_error(self, service):
        """Test that invalid target ID raises an error."""
        with pytest.raises(ValueError, match="Target .* not found"):
            service.create_scenario(
                name="Invalid Target",
                target_id=99999,
                vm_selection_criteria={"datacenters": ["DC1"]},
                strategy=MigrationStrategy.REHOST
            )


class TestMigrationStrategy:
    """Test migration strategy enum."""
    
    def test_strategy_values(self):
        """Test migration strategy enum values."""
        assert MigrationStrategy.REHOST.value == "rehost"
        assert MigrationStrategy.REPLATFORM.value == "replatform"
        assert MigrationStrategy.REFACTOR.value == "refactor"
        assert MigrationStrategy.REPURCHASE.value == "repurchase"
        assert MigrationStrategy.RETIRE.value == "retire"
        assert MigrationStrategy.RETAIN.value == "retain"


class TestPlatformType:
    """Test platform type enum."""
    
    def test_platform_values(self):
        """Test platform type enum values."""
        assert PlatformType.AWS.value == "aws"
        assert PlatformType.AZURE.value == "azure"
        assert PlatformType.GCP.value == "gcp"
        assert PlatformType.VMWARE_CLOUD.value == "vmware_cloud"
        assert PlatformType.ON_PREM.value == "on_prem"
        assert PlatformType.OPENSTACK.value == "openstack"
        assert PlatformType.KUBERNETES.value == "kubernetes"
