"""Service layer for multi-target migration scenario planning and analysis."""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import pandas as pd

from src.models import VirtualMachine
from src.models.migration_target import (
    MigrationTarget,
    MigrationScenario,
    MigrationWave,
    PlatformType,
    MigrationStrategy
)


class MigrationScenarioService:
    """Service for creating and analyzing migration scenarios."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_target(
        self,
        name: str,
        platform_type: PlatformType,
        region: str,
        **kwargs
    ) -> MigrationTarget:
        """Create a new migration target."""
        target = MigrationTarget(
            name=name,
            platform_type=platform_type,
            region=region,
            **kwargs
        )
        self.session.add(target)
        self.session.commit()
        return target
    
    def get_active_targets(self) -> List[MigrationTarget]:
        """Get all active migration targets."""
        return self.session.query(MigrationTarget).filter(
            MigrationTarget.is_active == True
        ).all()
    
    def calculate_migration_cost(
        self,
        vms: List[VirtualMachine],
        target: MigrationTarget,
        duration_days: float
    ) -> Dict[str, float]:
        """Calculate estimated migration cost for a target."""
        # Calculate total resources
        total_vcpus = sum(vm.CPUs or 0 for vm in vms)
        total_memory_gb = sum((vm.Memory or 0) / 1024 for vm in vms)  # Convert MB to GB
        total_storage_gb = sum((vm.Provisioned_MiB or 0) / 1024 for vm in vms)  # Convert MiB to GB
        
        # Calculate costs
        compute_cost = total_vcpus * target.compute_cost_per_vcpu * 24 * duration_days
        memory_cost = total_memory_gb * target.memory_cost_per_gb * 24 * duration_days
        storage_cost = total_storage_gb * target.storage_cost_per_gb * 24 * duration_days
        
        # Network transfer cost (ingress + egress)
        network_transfer_gb = total_storage_gb  # Assuming full replication
        network_cost = (
            network_transfer_gb * target.network_ingress_cost_per_gb +
            network_transfer_gb * target.network_egress_cost_per_gb
        )
        
        # Labor cost estimate (placeholder - should be configured)
        hours_per_vm = 4  # Average hours per VM for migration
        labor_rate_per_hour = 150  # USD
        labor_cost = len(vms) * hours_per_vm * labor_rate_per_hour
        
        total_cost = compute_cost + memory_cost + storage_cost + network_cost + labor_cost
        
        return {
            "compute": round(compute_cost, 2),
            "memory": round(memory_cost, 2),
            "storage": round(storage_cost, 2),
            "network": round(network_cost, 2),
            "labor": round(labor_cost, 2),
            "total": round(total_cost, 2)
        }
    
    def calculate_migration_duration(
        self,
        vms: List[VirtualMachine],
        target: MigrationTarget,
        parallel_migrations: int = 5
    ) -> Dict[str, float]:
        """Calculate estimated migration duration."""
        # Calculate total data to transfer
        total_storage_gib = sum((vm.Provisioned_MiB or 0) / 1024 for vm in vms)
        
        # Calculate replication time per VM
        avg_storage_per_vm = total_storage_gib / len(vms) if vms else 0
        
        # Convert GiB to Mib (1 GiB = 1024 MiB = 8192 Mib)
        storage_mib = avg_storage_per_vm * 8192
        
        # Calculate time: (data in Mib) / (bandwidth in Mbps * efficiency)
        effective_bandwidth = target.bandwidth_mbps * target.network_efficiency
        time_seconds_per_vm = storage_mib / effective_bandwidth if effective_bandwidth > 0 else 0
        replication_hours_per_vm = time_seconds_per_vm / 3600
        
        # Add fixed overhead per VM (setup, testing, validation)
        fixed_hours_per_vm = 2
        total_hours_per_vm = replication_hours_per_vm + fixed_hours_per_vm
        
        # Calculate total duration with parallel migrations
        total_vms = len(vms)
        migration_waves = (total_vms + parallel_migrations - 1) // parallel_migrations
        total_migration_hours = migration_waves * total_hours_per_vm
        
        # Convert to days (assuming 8-hour maintenance windows)
        hours_per_day = 8
        total_days = total_migration_hours / hours_per_day
        
        return {
            "replication_hours_per_vm": round(replication_hours_per_vm, 2),
            "total_hours_per_vm": round(total_hours_per_vm, 2),
            "total_migration_hours": round(total_migration_hours, 2),
            "total_days": round(total_days, 2),
            "migration_waves": migration_waves
        }
    
    def assess_risk_level(
        self,
        vms: List[VirtualMachine],
        target: MigrationTarget,
        strategy: MigrationStrategy
    ) -> Tuple[str, List[str]]:
        """Assess risk level and identify risk factors."""
        risk_factors = []
        risk_score = 0
        
        # VM count risk
        vm_count = len(vms)
        if vm_count > 100:
            risk_factors.append("large_vm_count")
            risk_score += 2
        elif vm_count > 50:
            risk_factors.append("moderate_vm_count")
            risk_score += 1
        
        # Data volume risk
        total_storage_tb = sum((vm.Provisioned_MiB or 0) / 1024 / 1024 for vm in vms)
        if total_storage_tb > 50:
            risk_factors.append("large_data_volume")
            risk_score += 2
        elif total_storage_tb > 20:
            risk_factors.append("moderate_data_volume")
            risk_score += 1
        
        # Live migration support
        if not target.supports_live_migration and strategy == MigrationStrategy.REHOST:
            risk_factors.append("downtime_required")
            risk_score += 1
        
        # Platform complexity
        if target.platform_type in [PlatformType.KUBERNETES, PlatformType.OPENSTACK]:
            risk_factors.append("complex_target_platform")
            risk_score += 1
        
        # Strategy complexity
        if strategy in [MigrationStrategy.REFACTOR, MigrationStrategy.REPURCHASE]:
            risk_factors.append("complex_migration_strategy")
            risk_score += 2
        
        # Determine risk level
        if risk_score >= 5:
            risk_level = "CRITICAL"
        elif risk_score >= 3:
            risk_level = "HIGH"
        elif risk_score >= 1:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return risk_level, risk_factors
    
    def calculate_recommendation_score(
        self,
        cost_breakdown: Dict[str, float],
        duration: Dict[str, float],
        risk_level: str,
        target: MigrationTarget
    ) -> float:
        """Calculate recommendation score (0-100)."""
        score = 100.0
        
        # Cost factor (lower is better)
        total_cost = cost_breakdown.get("total", 0)
        if total_cost > 100000:
            score -= 30
        elif total_cost > 50000:
            score -= 20
        elif total_cost > 10000:
            score -= 10
        
        # Duration factor (shorter is better)
        total_days = duration.get("total_days", 0)
        if total_days > 30:
            score -= 20
        elif total_days > 14:
            score -= 10
        elif total_days > 7:
            score -= 5
        
        # Risk factor
        risk_penalties = {
            "CRITICAL": 30,
            "HIGH": 20,
            "MEDIUM": 10,
            "LOW": 0
        }
        score -= risk_penalties.get(risk_level, 0)
        
        # SLA bonus
        if target.sla_uptime_percent >= 99.99:
            score += 10
        elif target.sla_uptime_percent >= 99.9:
            score += 5
        
        return max(0, min(100, score))
    
    def create_scenario(
        self,
        name: str,
        target_id: int,
        vm_selection_criteria: Dict,
        strategy: MigrationStrategy = MigrationStrategy.REHOST,
        **kwargs
    ) -> MigrationScenario:
        """Create a complete migration scenario with estimates."""
        target = self.session.query(MigrationTarget).get(target_id)
        if not target:
            raise ValueError(f"Target {target_id} not found")
        
        # Get VMs based on selection criteria
        vms = self._get_vms_by_criteria(vm_selection_criteria)
        
        if not vms:
            raise ValueError("No VMs match the selection criteria")
        
        # Calculate estimates
        cost_breakdown = self.calculate_migration_cost(
            vms, target, kwargs.get("duration_days", 30)
        )
        duration = self.calculate_migration_duration(
            vms, target, kwargs.get("parallel_migrations", 5)
        )
        risk_level, risk_factors = self.assess_risk_level(vms, target, strategy)
        
        # Calculate recommendation score
        recommendation_score = self.calculate_recommendation_score(
            cost_breakdown, duration, risk_level, target
        )
        
        # Create scenario
        scenario = MigrationScenario(
            name=name,
            target_id=target_id,
            strategy=strategy,
            vm_selection_criteria=vm_selection_criteria,
            estimated_duration_days=duration["total_days"],
            estimated_cost_total=cost_breakdown["total"],
            estimated_cost_breakdown=cost_breakdown,
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendation_score=recommendation_score,
            recommended=(recommendation_score >= 70),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            **kwargs
        )
        
        self.session.add(scenario)
        self.session.commit()
        
        return scenario
    
    def compare_scenarios(
        self,
        scenario_ids: List[int]
    ) -> pd.DataFrame:
        """Compare multiple scenarios side-by-side."""
        scenarios = self.session.query(MigrationScenario).filter(
            MigrationScenario.id.in_(scenario_ids)
        ).all()
        
        if not scenarios:
            return pd.DataFrame()
        
        # Build comparison data
        comparison_data = []
        for scenario in scenarios:
            comparison_data.append({
                "Scenario": scenario.name,
                "Target": scenario.target.name,
                "Platform": scenario.target.platform_type.value,
                "Strategy": scenario.strategy.value,
                "Duration (days)": scenario.estimated_duration_days,
                "Total Cost ($)": scenario.estimated_cost_total,
                "Risk Level": scenario.risk_level,
                "Score": scenario.recommendation_score,
                "Recommended": "✅" if scenario.recommended else "❌"
            })
        
        return pd.DataFrame(comparison_data)
    
    def _get_vms_by_criteria(self, criteria: Dict) -> List[VirtualMachine]:
        """Get VMs matching selection criteria."""
        query = self.session.query(VirtualMachine)
        
        # Apply filters based on criteria
        if "vm_ids" in criteria:
            query = query.filter(VirtualMachine.id.in_(criteria["vm_ids"]))
        
        if "datacenters" in criteria:
            query = query.filter(VirtualMachine.Datacenter.in_(criteria["datacenters"]))
        
        if "clusters" in criteria:
            query = query.filter(VirtualMachine.Cluster.in_(criteria["clusters"]))
        
        if "folders" in criteria:
            # Folder filtering (assuming folder path is stored)
            folder_conditions = []
            for folder in criteria["folders"]:
                folder_conditions.append(VirtualMachine.Folder.like(f"{folder}%"))
            if folder_conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*folder_conditions))
        
        return query.all()
    
    def generate_migration_waves(
        self,
        scenario_id: int,
        wave_size: int = 10,
        strategy: str = "size_based"
    ) -> List[MigrationWave]:
        """Generate migration waves for phased execution."""
        scenario = self.session.query(MigrationScenario).get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Get VMs for scenario
        vms = self._get_vms_by_criteria(scenario.vm_selection_criteria)
        
        # Sort VMs based on strategy
        if strategy == "size_based":
            # Migrate smaller VMs first (less data to transfer)
            vms = sorted(vms, key=lambda x: x.Provisioned_MiB or 0)
        elif strategy == "criticality_based":
            # Migrate less critical VMs first (would need criticality field)
            pass  # Placeholder
        
        # Create waves
        waves = []
        wave_number = 1
        
        for i in range(0, len(vms), wave_size):
            wave_vms = vms[i:i+wave_size]
            vm_ids = [vm.id for vm in wave_vms]
            
            wave = MigrationWave(
                scenario_id=scenario_id,
                wave_number=wave_number,
                wave_name=f"Wave {wave_number}",
                vm_ids=vm_ids,
                status="planned",
                depends_on_wave_ids=[wave_number - 1] if wave_number > 1 else []
            )
            
            waves.append(wave)
            self.session.add(wave)
            wave_number += 1
        
        self.session.commit()
        return waves
