"""Service layer for multi-target migration scenario planning and analysis."""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import pandas as pd

from src.models import VirtualMachine, VMLabel, Label
from src.models.migration_target import (
    MigrationTarget,
    MigrationScenario,
    MigrationWave,
    MigrationStrategyConfig,
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
    
    def delete_scenario(self, scenario_id: int) -> bool:
        """Delete a migration scenario by ID.
        
        Args:
            scenario_id: ID of the scenario to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        scenario = self.session.query(MigrationScenario).get(scenario_id)
        if scenario:
            self.session.delete(scenario)
            self.session.commit()
            return True
        return False
    
    def delete_scenarios_bulk(self, scenario_ids: List[int]) -> int:
        """Delete multiple migration scenarios.
        
        Args:
            scenario_ids: List of scenario IDs to delete
            
        Returns:
            Number of scenarios deleted
        """
        deleted_count = self.session.query(MigrationScenario).filter(
            MigrationScenario.id.in_(scenario_ids)
        ).delete(synchronize_session=False)
        self.session.commit()
        return deleted_count
    
    def calculate_migration_cost(
        self,
        vms: List[VirtualMachine],
        target: MigrationTarget,
        duration_days: float,
        strategy: MigrationStrategy = MigrationStrategy.REHOST
    ) -> Dict[str, any]:
        """Calculate estimated costs separating migration (one-time) and runtime (ongoing).
        
        Returns both migration costs and monthly runtime costs.
        Uses strategy-specific parameters from MigrationStrategyConfig table.
        
        Returns:
            Dict with 'migration', 'runtime_monthly', and 'total' cost breakdowns
        """
        # Get strategy configuration from database
        strategy_config = self.session.query(MigrationStrategyConfig).filter(
            MigrationStrategyConfig.strategy == strategy
        ).first()
        
        # If no config found, initialize defaults
        if not strategy_config:
            from src.dashboard.pages.strategy_config import initialize_default_configs
            initialize_default_configs(self.session)
            strategy_config = self.session.query(MigrationStrategyConfig).filter(
                MigrationStrategyConfig.strategy == strategy
            ).first()
        
        # Calculate total resources
        total_vcpus = sum(vm.cpus or 0 for vm in vms)
        total_memory_gb = sum((vm.memory or 0) / 1024 for vm in vms)  # Convert MB to GB
        total_storage_gb = sum((vm.provisioned_mib or 0) / 1024 for vm in vms)  # Convert MiB to GB
        
        # === MIGRATION COSTS (One-time) ===
        migration_labor = (
            len(vms) * 
            strategy_config.hours_per_vm * 
            strategy_config.labor_rate_per_hour
        )
        
        # Network transfer cost (one-time)
        migration_network_transfer = 0.0
        if strategy_config.network_multiplier > 0:
            network_transfer_gb = total_storage_gb
            migration_network_transfer = (
                network_transfer_gb * target.network_ingress_cost_per_gb +
                network_transfer_gb * target.network_egress_cost_per_gb
            ) * strategy_config.network_multiplier
        
        migration_total = migration_labor + migration_network_transfer
        
        # === RUNTIME COSTS (Monthly ongoing) ===
        # Calculate monthly infrastructure costs with strategy-specific multipliers
        runtime_compute_monthly = 0.0
        if strategy_config.compute_multiplier > 0:
            runtime_compute_monthly = (
                total_vcpus * 
                target.compute_cost_per_vcpu * 
                24 * 
                30 *  # 30 days per month
                strategy_config.compute_multiplier
            )
        
        runtime_memory_monthly = 0.0
        if strategy_config.memory_multiplier > 0:
            runtime_memory_monthly = (
                total_memory_gb * 
                target.memory_cost_per_gb * 
                24 * 
                30 * 
                strategy_config.memory_multiplier
            )
        
        runtime_storage_monthly = 0.0
        if strategy_config.storage_multiplier > 0:
            runtime_storage_monthly = (
                total_storage_gb * 
                target.storage_cost_per_gb * 
                strategy_config.storage_multiplier
            )
        
        # SaaS costs (for REPURCHASE strategy) - monthly
        runtime_saas_monthly = 0.0
        if strategy == MigrationStrategy.REPURCHASE and strategy_config.saas_cost_per_vm_per_month > 0:
            runtime_saas_monthly = len(vms) * strategy_config.saas_cost_per_vm_per_month
        
        runtime_total_monthly = (
            runtime_compute_monthly + 
            runtime_memory_monthly + 
            runtime_storage_monthly + 
            runtime_saas_monthly
        )
        
        # === TOTAL COST (Migration + Runtime for duration) ===
        runtime_cost_for_duration = runtime_total_monthly * (duration_days / 30)
        grand_total = migration_total + runtime_cost_for_duration
        
        return {
            "migration": {
                "labor": round(migration_labor, 2),
                "network_transfer": round(migration_network_transfer, 2),
                "total": round(migration_total, 2)
            },
            "runtime_monthly": {
                "compute": round(runtime_compute_monthly, 2),
                "memory": round(runtime_memory_monthly, 2),
                "storage": round(runtime_storage_monthly, 2),
                "saas": round(runtime_saas_monthly, 2),
                "total": round(runtime_total_monthly, 2)
            },
            "total": round(grand_total, 2),
            "duration_months": round(duration_days / 30, 2)
        }
    
    def calculate_migration_duration(
        self,
        vms: List[VirtualMachine],
        target: MigrationTarget,
        parallel_migrations: int = 5,
        strategy: MigrationStrategy = MigrationStrategy.REHOST
    ) -> Dict[str, float]:
        """Calculate realistic migration duration with multi-phase replication.
        
        Implements a realistic model considering:
        - Initial full replication
        - Delta synchronizations
        - Compression and deduplication
        - Network protocol overhead
        - Strategy-specific multipliers
        
        Args:
            vms: List of VMs to migrate
            target: Migration target platform
            parallel_migrations: Number of concurrent migrations
            strategy: Migration strategy (affects replication complexity)
            
        Returns:
            Dictionary with detailed duration breakdown
        """
        import math
        
        if not vms:
            return {
                "initial_replication_hours": 0.0,
                "delta_sync_hours": 0.0,
                "cutover_hours": 0.0,
                "total_replication_hours": 0.0,
                "total_hours": 0.0,
                "total_days": 0.0,
                "replication_days": 0.0,
                "cutover_days": 0.0,
                "migration_waves": 0,
                "effective_data_tb": 0.0,
                "compression_savings_percent": 0.0,
                "dedup_savings_percent": 0.0
            }
        
        # Get strategy configuration
        strategy_config = self.session.query(MigrationStrategyConfig).filter(
            MigrationStrategyConfig.strategy == strategy
        ).first()
        
        if not strategy_config:
            from src.dashboard.pages.strategy_config import initialize_default_configs
            initialize_default_configs(self.session)
            strategy_config = self.session.query(MigrationStrategyConfig).filter(
                MigrationStrategyConfig.strategy == strategy
            ).first()
        
        # Total data calculation (convert MiB to GB)
        total_storage_gb = sum((vm.provisioned_mib or 0) / 1024 for vm in vms)
        
        # Apply replication efficiency factors
        compression_ratio = getattr(target, 'compression_ratio', None) or 0.6
        dedup_ratio = getattr(target, 'dedup_ratio', None) or 0.8
        network_overhead = getattr(target, 'network_protocol_overhead', None) or 1.2
        
        # Calculate effective data to transfer
        # Start with raw data, apply compression and dedup (reduce size),
        # then add network overhead (increase size)
        effective_storage_gb = (
            total_storage_gb * 
            compression_ratio * 
            dedup_ratio * 
            network_overhead
        )
        
        # Convert to Gigabits for bandwidth calculation (1 GB = 8 Gb)
        effective_storage_gigabits = effective_storage_gb * 8
        
        # Network bandwidth (convert Mbps to Gbps)
        effective_bandwidth_mbps = target.bandwidth_mbps * target.network_efficiency
        effective_bandwidth_gbps = effective_bandwidth_mbps / 1000
        
        # === PHASE 1: Initial Full Replication ===
        # Calculate time to transfer all data: data (Gb) / bandwidth (Gbps) = seconds
        # Then convert seconds to hours
        if effective_bandwidth_gbps > 0:
            initial_replication_seconds = effective_storage_gigabits / effective_bandwidth_gbps
            initial_replication_hours = initial_replication_seconds / 3600
        else:
            initial_replication_hours = 0
        
        # === PHASE 2: Delta Synchronizations ===
        # During migration, data changes. We need to sync these changes.
        # Typical: 2-3 delta syncs, each transferring 5-15% of data
        change_rate = getattr(target, 'change_rate_percent', None) or 0.10
        delta_sync_count = getattr(target, 'delta_sync_count', None) or 2
        delta_sync_hours = initial_replication_hours * change_rate * delta_sync_count
        
        # === PHASE 3: Strategy-Specific Adjustment ===
        # Different strategies have different replication complexities
        replication_efficiency = getattr(strategy_config, 'replication_efficiency', None) or 1.0
        
        # Total replication time (initial + deltas) with strategy adjustment
        total_replication_hours = (
            (initial_replication_hours + delta_sync_hours) * 
            replication_efficiency
        )
        
        # === PHASE 4: Cutover & Validation ===
        # Fixed per-VM overhead for testing, validation, rollback preparation
        fixed_hours_per_vm = 2.0
        
        # Calculate waves with parallelism
        total_vms = len(vms)
        migration_waves = math.ceil(total_vms / parallel_migrations)
        cutover_hours = migration_waves * fixed_hours_per_vm
        
        # === TOTAL DURATION ===
        total_hours = total_replication_hours + cutover_hours
        
        # Convert to days
        # Replication runs 24/7, cutover happens in 8-hour windows
        replication_days = total_replication_hours / 24
        cutover_days = cutover_hours / 8
        total_days = replication_days + cutover_days
        
        return {
            "initial_replication_hours": round(initial_replication_hours, 2),
            "delta_sync_hours": round(delta_sync_hours, 2),
            "cutover_hours": round(cutover_hours, 2),
            "total_replication_hours": round(total_replication_hours, 2),
            "total_hours": round(total_hours, 2),
            "total_days": round(total_days, 2),
            "replication_days": round(replication_days, 2),
            "cutover_days": round(cutover_days, 2),
            "migration_waves": migration_waves,
            "effective_data_tb": round(effective_storage_gb / 1024, 2),
            "original_data_tb": round(total_storage_gb / 1024, 2),
            "compression_savings_percent": round((1 - compression_ratio) * 100, 1),
            "dedup_savings_percent": round((1 - dedup_ratio) * 100, 1)
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
        total_storage_tb = sum((vm.provisioned_mib or 0) / 1024 / 1024 for vm in vms)
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
        
        # Calculate VM resource metrics
        vm_count = len(vms)
        total_vcpus = sum(vm.cpus or 0 for vm in vms)
        total_memory_gb = sum((vm.memory or 0) / 1024 for vm in vms)  # Convert MB to GB
        total_storage_gb = sum((vm.provisioned_mib or 0) / 1024 for vm in vms)  # Convert MiB to GB
        
        # Calculate estimates
        cost_breakdown = self.calculate_migration_cost(
            vms, target, kwargs.get("duration_days", 30), strategy
        )
        duration = self.calculate_migration_duration(
            vms, target, kwargs.get("parallel_migrations", 5), strategy
        )
        risk_level, risk_factors = self.assess_risk_level(vms, target, strategy)
        
        # Calculate recommendation score
        recommendation_score = self.calculate_recommendation_score(
            cost_breakdown, duration, risk_level, target
        )
        
        # Create scenario with separated costs and resource metrics
        scenario = MigrationScenario(
            name=name,
            target_id=target_id,
            strategy=strategy,
            vm_selection_criteria=vm_selection_criteria,
            estimated_duration_days=duration["total_days"],
            vm_count=vm_count,
            total_vcpus=total_vcpus,
            total_memory_gb=total_memory_gb,
            total_storage_gb=total_storage_gb,
            estimated_migration_cost=cost_breakdown["migration"]["total"],
            estimated_runtime_cost_monthly=cost_breakdown["runtime_monthly"]["total"],
            estimated_cost_total=cost_breakdown["total"],
            migration_cost_breakdown=cost_breakdown["migration"],
            runtime_cost_breakdown=cost_breakdown["runtime_monthly"],
            estimated_cost_breakdown=cost_breakdown,  # Legacy field
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendation_score=recommendation_score,
            recommended=(recommendation_score >= 70),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description=kwargs.get("description"),
            created_by=kwargs.get("created_by")
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
                "VMs": scenario.vm_count or 0,
                "vCPUs": scenario.total_vcpus or 0,
                "RAM (GB)": round(scenario.total_memory_gb or 0, 1),
                "Storage (GB)": round(scenario.total_storage_gb or 0, 1),
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
            query = query.filter(VirtualMachine.datacenter.in_(criteria["datacenters"]))
        
        if "clusters" in criteria:
            query = query.filter(VirtualMachine.cluster.in_(criteria["clusters"]))
        
        if "folders" in criteria:
            # Folder filtering (assuming folder path is stored)
            folder_conditions = []
            for folder in criteria["folders"]:
                folder_conditions.append(VirtualMachine.folder.like(f"{folder}%"))
            if folder_conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*folder_conditions))
        
        if "labels" in criteria:
            # Label filtering - VMs that have ALL specified labels
            from sqlalchemy import select
            for label_spec in criteria["labels"]:
                # Subquery to find VMs with this specific label
                label_subquery = select(VMLabel.vm_id).join(
                    Label, VMLabel.label_id == Label.id
                ).filter(
                    Label.key == label_spec["key"],
                    Label.value == label_spec["value"]
                ).scalar_subquery()
                
                query = query.filter(VirtualMachine.id.in_(label_subquery))
        
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
            vms = sorted(vms, key=lambda x: x.provisioned_mib or 0)
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
