"""Unit tests for dashboard data processing functions."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import pandas as pd

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.models import Base, VirtualMachine


@pytest.fixture
def in_memory_db_with_data():
    """Create an in-memory database with sample VM data."""
    from sqlalchemy import event
    
    engine = create_engine("sqlite:///:memory:")
    
    # Enable foreign key constraints
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Add sample VMs
    vms = [
        VirtualMachine(
            vm="vm-prod-01", powerstate="poweredOn", cpus=4, memory=8192,
            datacenter="DC1", cluster="CL1", host="host1.example.com",
            os_config="Microsoft Windows Server 2019",
            creation_date=datetime(2023, 1, 15),
            in_use_mib=51200, provisioned_mib=102400
        ),
        VirtualMachine(
            vm="vm-prod-02", powerstate="poweredOn", cpus=8, memory=16384,
            datacenter="DC1", cluster="CL1", host="host1.example.com",
            os_config="Red Hat Enterprise Linux 8",
            creation_date=datetime(2023, 3, 20),
            in_use_mib=81920, provisioned_mib=163840
        ),
        VirtualMachine(
            vm="vm-dev-01", powerstate="poweredOff", cpus=2, memory=4096,
            datacenter="DC1", cluster="CL2", host="host2.example.com",
            os_config="Ubuntu Linux (64-bit)",
            creation_date=datetime(2023, 6, 10),
            in_use_mib=20480, provisioned_mib=40960
        ),
        VirtualMachine(
            vm="vm-test-01", powerstate="poweredOn", cpus=4, memory=8192,
            datacenter="DC2", cluster="CL3", host="host3.example.com",
            os_config="Microsoft Windows Server 2022",
            creation_date=datetime(2024, 1, 5),
            in_use_mib=40960, provisioned_mib=81920
        ),
        VirtualMachine(
            vm="vm-test-02", powerstate="suspended", cpus=2, memory=4096,
            datacenter="DC2", cluster="CL3", host="host3.example.com",
            os_config="CentOS 7 (64-bit)",
            creation_date=datetime(2024, 2, 15),
            dns_name=None,  # Missing DNS
            primary_ip_address=None  # Missing IP
        ),
    ]
    
    for vm in vms:
        session.add(vm)
    session.commit()
    
    yield session
    session.close()


class TestOverviewPageDataProcessing:
    """Tests for Overview page data calculations."""
    
    def test_get_total_vm_count(self, in_memory_db_with_data):
        """Test getting total VM count."""
        session = in_memory_db_with_data
        
        total = session.query(func.count(VirtualMachine.id)).scalar()
        
        assert total == 5
    
    def test_get_powered_on_count(self, in_memory_db_with_data):
        """Test getting powered on VM count."""
        session = in_memory_db_with_data
        
        powered_on = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.powerstate == "poweredOn"
        ).scalar()
        
        assert powered_on == 3
    
    def test_get_power_state_percentage(self, in_memory_db_with_data):
        """Test calculating power state percentage."""
        session = in_memory_db_with_data
        
        total = session.query(func.count(VirtualMachine.id)).scalar()
        powered_on = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.powerstate == "poweredOn"
        ).scalar()
        
        percentage = (powered_on / total * 100) if total > 0 else 0
        
        assert percentage == 60.0  # 3/5 * 100
    
    def test_get_total_vcpus(self, in_memory_db_with_data):
        """Test calculating total vCPUs."""
        session = in_memory_db_with_data
        
        total_cpus = session.query(func.sum(VirtualMachine.cpus)).scalar() or 0
        
        assert total_cpus == 20  # 4+8+2+4+2
    
    def test_get_total_memory_gb(self, in_memory_db_with_data):
        """Test calculating total memory in GB."""
        session = in_memory_db_with_data
        
        total_memory_mb = session.query(func.sum(VirtualMachine.memory)).scalar() or 0
        total_memory_gb = total_memory_mb / 1024
        
        assert total_memory_gb == 40.0  # (8192+16384+4096+8192+4096)/1024
    
    def test_get_power_state_distribution(self, in_memory_db_with_data):
        """Test getting power state distribution."""
        session = in_memory_db_with_data
        
        power_states = session.query(
            VirtualMachine.powerstate,
            func.count(VirtualMachine.id).label('count')
        ).group_by(VirtualMachine.powerstate).all()
        
        df = pd.DataFrame(power_states, columns=['State', 'Count'])
        
        assert len(df) == 3
        assert df[df['State'] == 'poweredOn']['Count'].values[0] == 3
        assert df[df['State'] == 'poweredOff']['Count'].values[0] == 1
        assert df[df['State'] == 'suspended']['Count'].values[0] == 1
    
    def test_get_datacenter_distribution(self, in_memory_db_with_data):
        """Test getting datacenter distribution."""
        session = in_memory_db_with_data
        
        datacenters = session.query(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('count')
        ).group_by(VirtualMachine.datacenter).order_by(
            func.count(VirtualMachine.id).desc()
        ).all()
        
        df = pd.DataFrame(datacenters, columns=['Datacenter', 'Count'])
        
        assert len(df) == 2
        assert df.iloc[0]['Datacenter'] == 'DC1'
        assert df.iloc[0]['Count'] == 3
    
    def test_get_cluster_distribution(self, in_memory_db_with_data):
        """Test getting cluster distribution."""
        session = in_memory_db_with_data
        
        clusters = session.query(
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('count')
        ).group_by(VirtualMachine.cluster).order_by(
            func.count(VirtualMachine.id).desc()
        ).limit(10).all()
        
        df = pd.DataFrame(clusters, columns=['Cluster', 'Count'])
        
        assert len(df) == 3
        assert df.iloc[0]['Cluster'] == 'CL1'
        assert df.iloc[0]['Count'] == 2
    
    def test_get_os_distribution(self, in_memory_db_with_data):
        """Test getting OS distribution."""
        session = in_memory_db_with_data
        
        os_config = session.query(
            VirtualMachine.os_config,
            func.count(VirtualMachine.id).label('count')
        ).filter(
            VirtualMachine.os_config.isnot(None)
        ).group_by(VirtualMachine.os_config).order_by(
            func.count(VirtualMachine.id).desc()
        ).limit(10).all()
        
        df = pd.DataFrame(os_config, columns=['OS', 'Count'])
        
        assert len(df) == 5
        assert df['Count'].sum() == 5
    
    def test_get_infrastructure_summary_counts(self, in_memory_db_with_data):
        """Test getting infrastructure summary counts."""
        session = in_memory_db_with_data
        
        dc_count = session.query(func.count(func.distinct(VirtualMachine.datacenter))).scalar()
        cluster_count = session.query(func.count(func.distinct(VirtualMachine.cluster))).scalar()
        host_count = session.query(func.count(func.distinct(VirtualMachine.host))).scalar()
        
        assert dc_count == 2
        assert cluster_count == 3
        assert host_count == 3
    
    def test_detect_missing_dns_and_ip(self, in_memory_db_with_data):
        """Test detecting VMs with missing DNS/IP."""
        session = in_memory_db_with_data
        
        null_dns = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.dns_name.is_(None)
        ).scalar() or 0
        
        null_ip = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.primary_ip_address.is_(None)
        ).scalar() or 0
        
        assert null_dns >= 1
        assert null_ip >= 1


class TestAnalyticsPageDataProcessing:
    """Tests for Analytics page data calculations."""
    
    def test_get_resource_allocation_data(self, in_memory_db_with_data):
        """Test getting resource allocation data."""
        session = in_memory_db_with_data
        
        vms = session.query(VirtualMachine).filter(
            VirtualMachine.cpus.isnot(None),
            VirtualMachine.memory.isnot(None)
        ).all()
        
        df = pd.DataFrame([{
            'VM': vm.vm,
            'CPUs': vm.cpus,
            'Memory_GB': vm.memory / 1024,
            'PowerState': vm.powerstate or 'Unknown'
        } for vm in vms if vm.cpus and vm.memory])
        
        assert len(df) == 5
        assert 'CPUs' in df.columns
        assert 'Memory_GB' in df.columns
        assert df['Memory_GB'].min() == 4.0
        assert df['Memory_GB'].max() == 16.0
    
    def test_calculate_resource_configurations(self, in_memory_db_with_data):
        """Test calculating resource configuration patterns."""
        session = in_memory_db_with_data
        
        vms = session.query(VirtualMachine).filter(
            VirtualMachine.cpus.isnot(None),
            VirtualMachine.memory.isnot(None)
        ).all()
        
        df = pd.DataFrame([{
            'CPUs': vm.cpus,
            'Memory_GB': vm.memory / 1024
        } for vm in vms if vm.cpus and vm.memory])
        
        df['Config'] = df['CPUs'].astype(str) + ' CPU / ' + \
                      df['Memory_GB'].round(0).astype(int).astype(str) + ' GB'
        
        config_counts = df['Config'].value_counts()
        
        assert '4 CPU / 8 GB' in config_counts.index
        assert '2 CPU / 4 GB' in config_counts.index
    
    def test_get_vm_creation_timeline(self, in_memory_db_with_data):
        """Test getting VM creation timeline data."""
        session = in_memory_db_with_data
        
        vms = session.query(VirtualMachine).filter(
            VirtualMachine.creation_date.isnot(None)
        ).all()
        
        df = pd.DataFrame([{
            'Date': vm.creation_date.date(),
            'VM': vm.vm
        } for vm in vms])
        
        assert len(df) == 5
        assert 'Date' in df.columns
    
    def test_get_os_resource_allocation(self, in_memory_db_with_data):
        """Test getting OS resource allocation data."""
        session = in_memory_db_with_data
        
        os_data = session.query(
            VirtualMachine.os_config,
            func.count(VirtualMachine.id).label('count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).filter(
            VirtualMachine.os_config.isnot(None)
        ).group_by(VirtualMachine.os_config).all()
        
        df = pd.DataFrame(os_data, columns=['OS', 'Count', 'CPUs', 'Memory_MB'])
        df['Memory_GB'] = df['Memory_MB'] / 1024
        
        assert len(df) == 5
        assert df['CPUs'].sum() == 20
        assert df['Memory_GB'].sum() == 40.0
    
    def test_calculate_cluster_efficiency(self, in_memory_db_with_data):
        """Test calculating cluster efficiency metrics."""
        session = in_memory_db_with_data
        
        cluster_data = session.query(
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('vm_count'),
            func.count(func.distinct(VirtualMachine.host)).label('host_count')
        ).filter(
            VirtualMachine.cluster.isnot(None)
        ).group_by(VirtualMachine.cluster).all()
        
        df = pd.DataFrame(cluster_data, columns=['Cluster', 'VMs', 'Hosts'])
        df['VMs_per_Host'] = df['VMs'] / df['Hosts']
        
        assert len(df) == 3
        assert 'VMs_per_Host' in df.columns
        assert df['VMs_per_Host'].max() == 2.0  # CL1 has 2 VMs on 1 host


class TestInfrastructurePageDataProcessing:
    """Tests for Infrastructure page data calculations."""
    
    def test_get_datacenter_stats(self, in_memory_db_with_data):
        """Test getting datacenter statistics."""
        session = in_memory_db_with_data
        
        dc_stats = session.query(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).group_by(VirtualMachine.datacenter).all()
        
        df = pd.DataFrame(dc_stats, columns=['Datacenter', 'VMs', 'CPUs', 'Memory_MB'])
        df['Memory_GB'] = df['Memory_MB'] / 1024
        
        assert len(df) == 2
        assert df[df['Datacenter'] == 'DC1']['VMs'].values[0] == 3
        assert df[df['Datacenter'] == 'DC1']['CPUs'].values[0] == 14
    
    def test_get_cluster_stats_all_datacenters(self, in_memory_db_with_data):
        """Test getting cluster stats for all datacenters."""
        session = in_memory_db_with_data
        
        cluster_stats = session.query(
            VirtualMachine.cluster,
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('vm_count')
        ).group_by(
            VirtualMachine.cluster,
            VirtualMachine.datacenter
        ).all()
        
        df = pd.DataFrame(cluster_stats, columns=['Cluster', 'Datacenter', 'VMs'])
        
        assert len(df) == 3
        assert df['VMs'].sum() == 5
    
    def test_get_cluster_stats_filtered(self, in_memory_db_with_data):
        """Test getting cluster stats for specific datacenter."""
        session = in_memory_db_with_data
        
        cluster_stats = session.query(
            VirtualMachine.cluster,
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('vm_count')
        ).filter(
            VirtualMachine.datacenter == 'DC1'
        ).group_by(
            VirtualMachine.cluster,
            VirtualMachine.datacenter
        ).all()
        
        df = pd.DataFrame(cluster_stats, columns=['Cluster', 'Datacenter', 'VMs'])
        
        assert len(df) == 2  # Only CL1 and CL2 are in DC1
        assert df['VMs'].sum() == 3
    
    def test_get_host_distribution(self, in_memory_db_with_data):
        """Test getting host distribution."""
        session = in_memory_db_with_data
        
        host_stats = session.query(
            VirtualMachine.host,
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('vm_count')
        ).group_by(
            VirtualMachine.host,
            VirtualMachine.cluster
        ).order_by(func.count(VirtualMachine.id).desc()).all()
        
        df = pd.DataFrame(host_stats, columns=['Host', 'Cluster', 'VMs'])
        
        assert len(df) == 3
        assert df.iloc[0]['VMs'] == 2  # host1 has most VMs
    
    def test_calculate_host_metrics(self, in_memory_db_with_data):
        """Test calculating host distribution metrics."""
        session = in_memory_db_with_data
        
        host_stats = session.query(
            VirtualMachine.host,
            func.count(VirtualMachine.id).label('vm_count')
        ).group_by(VirtualMachine.host).all()
        
        df = pd.DataFrame(host_stats, columns=['Host', 'VMs'])
        
        avg_vms = df['VMs'].mean()
        max_vms = df['VMs'].max()
        min_vms = df['VMs'].min()
        
        assert avg_vms > 0
        assert max_vms >= min_vms
        assert max_vms == 2


class TestDataQualityChecks:
    """Tests for data quality detection."""
    
    def test_detect_null_values(self, in_memory_db_with_data):
        """Test detecting null values in important fields."""
        session = in_memory_db_with_data
        
        total = session.query(func.count(VirtualMachine.id)).scalar()
        null_dns = session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.dns_name.is_(None)
        ).scalar()
        
        data_quality_ratio = (total - null_dns) / total if total > 0 else 0
        
        assert data_quality_ratio < 1.0  # We have at least one null
        assert data_quality_ratio >= 0.0
    
    def test_empty_database_detection(self):
        """Test detecting empty database."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        total_vms = session.query(func.count(VirtualMachine.id)).scalar()
        
        assert total_vms == 0
        
        session.close()
    
    def test_resource_consistency(self, in_memory_db_with_data):
        """Test checking resource allocation consistency."""
        session = in_memory_db_with_data
        
        # VMs should have positive CPU and memory if set
        invalid_resources = session.query(VirtualMachine).filter(
            (VirtualMachine.cpus.isnot(None) & (VirtualMachine.cpus <= 0)) |
            (VirtualMachine.memory.isnot(None) & (VirtualMachine.memory <= 0))
        ).count()
        
        assert invalid_resources == 0


class TestDataAggregations:
    """Tests for various data aggregation functions."""
    
    def test_group_by_multiple_fields(self, in_memory_db_with_data):
        """Test grouping by multiple fields."""
        session = in_memory_db_with_data
        
        results = session.query(
            VirtualMachine.datacenter,
            VirtualMachine.cluster,
            VirtualMachine.powerstate,
            func.count(VirtualMachine.id).label('count')
        ).group_by(
            VirtualMachine.datacenter,
            VirtualMachine.cluster,
            VirtualMachine.powerstate
        ).all()
        
        assert len(results) > 0
        assert all(r[3] > 0 for r in results)  # All counts should be positive
    
    def test_calculate_percentages(self, in_memory_db_with_data):
        """Test calculating percentage distributions."""
        session = in_memory_db_with_data
        
        total = session.query(func.count(VirtualMachine.id)).scalar()
        
        power_states = session.query(
            VirtualMachine.powerstate,
            func.count(VirtualMachine.id).label('count')
        ).group_by(VirtualMachine.powerstate).all()
        
        percentages = {state: (count / total * 100) for state, count in power_states}
        
        assert sum(percentages.values()) == pytest.approx(100.0, rel=1e-9)
    
    def test_top_n_filtering(self, in_memory_db_with_data):
        """Test getting top N results."""
        session = in_memory_db_with_data
        
        top_3_clusters = session.query(
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('count')
        ).group_by(VirtualMachine.cluster).order_by(
            func.count(VirtualMachine.id).desc()
        ).limit(3).all()
        
        assert len(top_3_clusters) <= 3
        # Results should be in descending order
        counts = [c[1] for c in top_3_clusters]
        assert counts == sorted(counts, reverse=True)
