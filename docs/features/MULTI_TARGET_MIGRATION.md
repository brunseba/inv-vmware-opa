# Multi-Target Migration Planning

## Overview

The Multi-Target Migration Planning feature enables comprehensive analysis and comparison of migration scenarios across multiple cloud and on-premises platforms. It supports the complete 6Rs migration framework and provides cost, duration, and risk assessment for each scenario.

## Supported Platforms

- **AWS (Amazon Web Services)**
- **Azure (Microsoft Azure)**
- **GCP (Google Cloud Platform)**
- **VMware Cloud**
- **On-Premises**
- **OpenStack**
- **Kubernetes**
- **Other** (custom platforms)

## Migration Strategies (6Rs Framework)

### 1. Rehost (Lift and Shift)
- **Description**: Move applications without changes
- **Use Case**: Quick migration with minimal disruption
- **Risk Level**: Low to Medium
- **Complexity**: Low

### 2. Replatform (Lift, Tinker, and Shift)
- **Description**: Make minimal cloud optimizations
- **Use Case**: Benefit from cloud features without re-architecting
- **Risk Level**: Medium
- **Complexity**: Medium

### 3. Refactor (Re-architect)
- **Description**: Re-design application for cloud-native
- **Use Case**: Maximize cloud benefits and scalability
- **Risk Level**: High
- **Complexity**: High

### 4. Repurchase (Move to SaaS)
- **Description**: Replace with SaaS solutions
- **Use Case**: Reduce operational overhead
- **Risk Level**: Medium to High
- **Complexity**: Medium

### 5. Retire
- **Description**: Decommission unused applications
- **Use Case**: Reduce costs and complexity
- **Risk Level**: Low
- **Complexity**: Low

### 6. Retain (Keep as-is)
- **Description**: Keep in current environment
- **Use Case**: Not ready or not suitable for migration
- **Risk Level**: Low
- **Complexity**: None

## Features

### Migration Target Configuration

Each migration target can be configured with:

- **Network Settings**
  - Dedicated bandwidth (Mbps)
  - Network efficiency factor
  - Maximum parallel migrations

- **Cost Factors**
  - Compute cost per vCPU ($/hour)
  - Memory cost per GB ($/hour)
  - Storage cost per GB ($/month)
  - Network ingress/egress costs ($/GB)

- **Platform Attributes**
  - Account/subscription IDs
  - Regions and availability zones
  - Instance types and sizes
  - SLA commitments

- **Service Level**
  - Uptime SLA (%)
  - Support level (24/7, business hours)
  - Live migration support

### Scenario Analysis

For each migration scenario, the system calculates:

#### Cost Breakdown
```python
{
    "compute": 5000.00,   # Compute resource costs
    "memory": 2000.00,    # Memory resource costs
    "storage": 1500.00,   # Storage costs
    "network": 800.00,    # Data transfer costs
    "labor": 12000.00,    # Professional services
    "total": 21300.00     # Total estimated cost
}
```

#### Duration Estimation
```python
{
    "replication_hours_per_vm": 2.5,
    "total_hours_per_vm": 4.5,
    "total_migration_hours": 450,
    "total_days": 56.25,
    "migration_waves": 10
}
```

#### Risk Assessment
- **Risk Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Risk Factors**:
  - Large VM count
  - Large data volume
  - Downtime requirements
  - Platform complexity
  - Strategy complexity
  - Data sovereignty
  - Compliance requirements

#### Recommendation Score (0-100)
Calculated based on:
- Total cost (lower is better)
- Migration duration (shorter is better)
- Risk level (lower is better)
- SLA guarantees (higher is better)

Scenarios with score ≥ 70 are marked as "Recommended"

### Scenario Comparison

Compare multiple scenarios side-by-side:

| Scenario | Target | Platform | Strategy | Duration (days) | Cost ($) | Risk | Score | Recommended |
|----------|--------|----------|----------|----------------|----------|------|-------|-------------|
| AWS Quick | AWS US-East-1 | aws | rehost | 45 | 18,500 | MEDIUM | 75 | ✅ |
| Azure Optimized | Azure West Europe | azure | replatform | 60 | 22,000 | HIGH | 65 | ❌ |
| GCP Cloud-Native | GCP US-Central1 | gcp | refactor | 90 | 35,000 | HIGH | 55 | ❌ |

### Migration Waves

Break large migrations into manageable waves:

- **Wave-based Execution**: Group VMs into waves (e.g., 10-20 VMs per wave)
- **Dependencies**: Define wave dependencies (e.g., Wave 2 depends on Wave 1)
- **Strategies**:
  - **Size-based**: Migrate smaller VMs first
  - **Criticality-based**: Migrate less critical workloads first
  - **Custom**: Define your own order

## Usage Examples

### Creating a Migration Target

```python
from src.services.migration_scenarios import MigrationScenarioService
from src.models.migration_target import PlatformType

service = MigrationScenarioService(session)

aws_target = service.create_target(
    name="AWS US-East-1 Production",
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
    supports_live_migration=False,
    platform_attributes={
        "account_id": "123456789012",
        "vpc_id": "vpc-abc123",
        "instance_types": ["t3.medium", "t3.large", "m5.xlarge"]
    }
)
```

### Creating a Migration Scenario

```python
from src.models.migration_target import MigrationStrategy

scenario = service.create_scenario(
    name="Production Web Servers to AWS",
    target_id=aws_target.id,
    vm_selection_criteria={
        "datacenters": ["DC1"],
        "clusters": ["Prod-Cluster-A"]
    },
    strategy=MigrationStrategy.REHOST,
    duration_days=30,
    parallel_migrations=10
)

print(f"Estimated Duration: {scenario.estimated_duration_days} days")
print(f"Estimated Cost: ${scenario.estimated_cost_total:,.2f}")
print(f"Risk Level: {scenario.risk_level}")
print(f"Recommendation Score: {scenario.recommendation_score}/100")
```

### Comparing Scenarios

```python
# Create multiple scenarios
aws_scenario = service.create_scenario(...)
azure_scenario = service.create_scenario(...)
gcp_scenario = service.create_scenario(...)

# Compare them
comparison = service.compare_scenarios([
    aws_scenario.id,
    azure_scenario.id,
    gcp_scenario.id
])

print(comparison)
```

### Generating Migration Waves

```python
waves = service.generate_migration_waves(
    scenario_id=scenario.id,
    wave_size=15,
    strategy="size_based"
)

for wave in waves:
    print(f"Wave {wave.wave_number}: {len(wave.vm_ids)} VMs")
    if wave.depends_on_wave_ids:
        print(f"  Depends on: Wave {wave.depends_on_wave_ids[0]}")
```

## Decision Matrix

### When to Use Each Strategy

| Strategy | Best For | Avoid If |
|----------|----------|----------|
| **Rehost** | Quick migration, minimal changes, proven applications | Applications need modernization |
| **Replatform** | Optimize for cloud, moderate changes acceptable | Major re-architecture needed |
| **Refactor** | Maximize cloud benefits, greenfield approach | Tight timeline or budget |
| **Repurchase** | Commodity applications, reduce maintenance | Custom or highly specialized apps |
| **Retire** | Unused or redundant applications | Still actively used |
| **Retain** | Not cloud-ready, compliance restrictions | Cloud benefits are clear |

### Platform Selection Criteria

| Criteria | AWS | Azure | GCP | On-Prem |
|----------|-----|-------|-----|---------|
| **Market Leader** | ✅ | ⭕ | ⭕ | - |
| **Enterprise Integration** | ⭕ | ✅ | ⭕ | ✅ |
| **AI/ML Services** | ✅ | ⭕ | ✅ | ❌ |
| **Kubernetes** | ⭕ | ⭕ | ✅ | ⭕ |
| **Cost Control** | ⭕ | ⭕ | ⭕ | ✅ |
| **Data Sovereignty** | ⭕ | ⭕ | ⭕ | ✅ |

✅ = Excellent | ⭕ = Good | ❌ = Limited

## Best Practices

### 1. Start with Assessment
- Inventory all applications and dependencies
- Classify workloads by criticality
- Identify compliance and regulatory requirements

### 2. Create Multiple Scenarios
- Compare at least 2-3 different targets
- Evaluate different migration strategies
- Consider hybrid scenarios

### 3. Pilot Program
- Start with non-critical workloads
- Test migration tools and processes
- Validate cost and performance estimates

### 4. Wave Planning
- Group related applications together
- Consider dependencies between systems
- Schedule waves during maintenance windows

### 5. Monitor and Optimize
- Track actual vs. estimated costs
- Monitor performance after migration
- Optimize resources based on actual usage

## Cost Optimization Tips

1. **Right-size Resources**: Don't over-provision in the cloud
2. **Use Reserved Instances**: Commit to 1-3 year terms for savings
3. **Leverage Spot Instances**: For non-critical workloads
4. **Implement Auto-scaling**: Scale resources based on demand
5. **Use Cost Management Tools**: Monitor and alert on spending
6. **Consider Multi-cloud**: Avoid vendor lock-in and optimize costs

## Risk Mitigation

### High-Risk Scenarios
- **Large-scale migrations** (>100 VMs): Break into smaller waves
- **Complex applications**: Consider replatform or refactor
- **Critical workloads**: Ensure comprehensive testing and rollback plans

### Risk Reduction Strategies
1. **Proof of Concept**: Validate approach with pilot applications
2. **Parallel Running**: Run old and new systems concurrently
3. **Incremental Cutover**: Gradual traffic shifting
4. **Comprehensive Testing**: Functional, performance, and disaster recovery
5. **Communication Plan**: Keep stakeholders informed

## Troubleshooting

### Common Issues

**Issue**: Cost estimates are too high
- **Solution**: Review instance sizing, consider reserved instances, optimize storage tiers

**Issue**: Migration duration is too long
- **Solution**: Increase parallel migrations, use higher bandwidth, compress data

**Issue**: High risk assessment
- **Solution**: Break into smaller waves, choose less complex strategy, add testing time

**Issue**: Low recommendation score
- **Solution**: Review target configuration, consider alternative platforms, optimize VM selection

## API Reference

See `src/services/migration_scenarios.py` for complete API documentation.

### Key Methods

- `create_target()`: Create migration target
- `create_scenario()`: Create migration scenario with estimates
- `compare_scenarios()`: Compare multiple scenarios
- `generate_migration_waves()`: Create wave-based execution plan
- `calculate_migration_cost()`: Estimate migration costs
- `calculate_migration_duration()`: Estimate migration duration
- `assess_risk_level()`: Assess scenario risks

## Support

For questions or issues, please refer to:
- [GitHub Issues](https://github.com/brunseba/inv-vmware-opa/issues)
- [Documentation](https://github.com/brunseba/inv-vmware-opa/docs)
- [CONTRIBUTING.md](https://github.com/brunseba/inv-vmware-opa/blob/main/CONTRIBUTING.md)

## License

This feature is part of the inv-vmware-opa project, licensed under MIT License.
