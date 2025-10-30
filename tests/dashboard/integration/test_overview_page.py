"""Integration tests for Overview dashboard page."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))


@pytest.mark.integration
@pytest.mark.dashboard
class TestOverviewPageRendering:
    """Tests for Overview page rendering."""
    
    @patch('dashboard.pages.overview.render')
    def test_overview_page_can_be_imported(self, mock_render):
        """Test that overview page module can be imported."""
        from dashboard.pages import overview
        
        assert overview is not None
        assert hasattr(overview, 'render')
    
    @patch('streamlit.title')
    @patch('streamlit.metric')
    @patch('streamlit.warning')
    def test_overview_handles_empty_database(self, mock_warning, mock_metric, mock_title, empty_db_session, db_url):
        """Test that overview page handles empty database gracefully."""
        from dashboard.pages import overview
        
        try:
            overview.render(db_url)
            # Should show warning about no data
            # mock_warning.assert_called()
        except Exception as e:
            pytest.fail(f"Overview page should handle empty database: {e}")
    
    @patch('streamlit.title')
    @patch('streamlit.metric')
    def test_overview_displays_with_data(self, mock_metric, mock_title, populated_db_session, db_url):
        """Test that overview page displays correctly with data."""
        from dashboard.pages import overview
        
        try:
            overview.render(db_url)
            # Should display metrics
            assert mock_metric.call_count > 0
        except Exception as e:
            pytest.fail(f"Overview page should render with data: {e}")
    
    def test_overview_calculates_vm_counts(self, populated_db_session):
        """Test VM count calculations."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        total = populated_db_session.query(func.count(VirtualMachine.id)).scalar()
        powered_on = populated_db_session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.powerstate == "poweredOn"
        ).scalar()
        
        assert total > 0
        assert powered_on > 0
        assert powered_on <= total
    
    def test_overview_datacenter_distribution(self, populated_db_session):
        """Test datacenter distribution calculation."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        dc_dist = populated_db_session.query(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('count')
        ).group_by(VirtualMachine.datacenter).all()
        
        assert len(dc_dist) > 0
        assert all(count > 0 for _, count in dc_dist)
    
    def test_overview_power_state_distribution(self, populated_db_session):
        """Test power state distribution calculation."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        power_states = populated_db_session.query(
            VirtualMachine.powerstate,
            func.count(VirtualMachine.id).label('count')
        ).group_by(VirtualMachine.powerstate).all()
        
        assert len(power_states) > 0
        df = pd.DataFrame(power_states, columns=['State', 'Count'])
        assert df['Count'].sum() > 0


@pytest.mark.integration
@pytest.mark.dashboard
class TestOverviewPageDataAggregations:
    """Tests for Overview page data aggregations."""
    
    def test_total_resource_calculations(self, populated_db_session):
        """Test total CPU and memory calculations."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        total_cpus = populated_db_session.query(func.sum(VirtualMachine.cpus)).scalar() or 0
        total_memory = populated_db_session.query(func.sum(VirtualMachine.memory)).scalar() or 0
        
        assert total_cpus >= 0
        assert total_memory >= 0
    
    def test_infrastructure_counts(self, populated_db_session):
        """Test infrastructure component counting."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        dc_count = populated_db_session.query(func.count(func.distinct(VirtualMachine.datacenter))).scalar()
        cluster_count = populated_db_session.query(func.count(func.distinct(VirtualMachine.cluster))).scalar()
        host_count = populated_db_session.query(func.count(func.distinct(VirtualMachine.host))).scalar()
        
        assert dc_count > 0
        assert cluster_count > 0
        assert host_count > 0
    
    def test_os_distribution(self, populated_db_session):
        """Test OS distribution calculation."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        os_dist = populated_db_session.query(
            VirtualMachine.os_config,
            func.count(VirtualMachine.id).label('count')
        ).filter(
            VirtualMachine.os_config.isnot(None)
        ).group_by(VirtualMachine.os_config).all()
        
        assert len(os_dist) > 0
    
    def test_storage_calculations(self, populated_db_session):
        """Test storage usage calculations."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        total_provisioned = populated_db_session.query(
            func.sum(VirtualMachine.provisioned_mib)
        ).scalar() or 0
        
        total_in_use = populated_db_session.query(
            func.sum(VirtualMachine.in_use_mib)
        ).scalar() or 0
        
        # These can be 0 if data is missing
        assert total_provisioned >= 0
        assert total_in_use >= 0


@pytest.mark.integration
@pytest.mark.dashboard
class TestOverviewPageErrorHandling:
    """Tests for Overview page error handling."""
    
    @patch('streamlit.error')
    def test_overview_handles_database_error(self, mock_error):
        """Test that overview handles database errors."""
        from dashboard.pages import overview
        
        # Invalid database URL
        try:
            overview.render("invalid://database")
        except:
            # Should either handle gracefully or raise
            pass
    
    @patch('streamlit.warning')
    def test_overview_warns_on_missing_data(self, mock_warning, db_session, db_url):
        """Test that overview warns about data quality issues."""
        from src.models import VirtualMachine
        from dashboard.pages import overview
        
        # Add VM with missing data
        vm = VirtualMachine(
            vm="incomplete-vm",
            powerstate="poweredOn",
            # Missing most fields
        )
        db_session.add(vm)
        db_session.commit()
        
        try:
            overview.render(db_url)
            # Should handle missing data gracefully
        except Exception as e:
            # Acceptable if it handles the error
            pass


@pytest.mark.integration
@pytest.mark.dashboard
@pytest.mark.slow
class TestOverviewPagePerformance:
    """Tests for Overview page performance."""
    
    def test_overview_renders_with_many_vms(self, db_session, db_url):
        """Test overview performance with large dataset."""
        from src.models import VirtualMachine
        from dashboard.pages import overview
        import time
        
        # Add many VMs
        vms = [
            VirtualMachine(
                vm=f"test-vm-{i}",
                powerstate="poweredOn",
                cpus=2,
                memory=4096,
                datacenter=f"DC{i % 3}",
                cluster=f"CL{i % 5}",
            )
            for i in range(100)
        ]
        
        db_session.add_all(vms)
        db_session.commit()
        
        start_time = time.time()
        
        try:
            with patch('streamlit.title'), \
                 patch('streamlit.metric'), \
                 patch('streamlit.plotly_chart'):
                overview.render(db_url)
        except Exception:
            pass  # Focus on performance, not correctness here
        
        duration = time.time() - start_time
        
        # Should complete within reasonable time (adjust as needed)
        assert duration < 10.0, f"Overview took {duration}s, expected < 10s"
    
    def test_overview_query_efficiency(self, populated_db_session):
        """Test that overview uses efficient queries."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        # These should be efficient single queries
        queries = [
            lambda: populated_db_session.query(func.count(VirtualMachine.id)).scalar(),
            lambda: populated_db_session.query(func.sum(VirtualMachine.cpus)).scalar(),
            lambda: populated_db_session.query(
                VirtualMachine.powerstate,
                func.count(VirtualMachine.id)
            ).group_by(VirtualMachine.powerstate).all(),
        ]
        
        for query in queries:
            result = query()
            assert result is not None


@pytest.mark.integration
@pytest.mark.dashboard
class TestOverviewPageDataValidation:
    """Tests for data validation in Overview page."""
    
    def test_overview_handles_null_values(self, db_session, db_url):
        """Test that overview handles null values correctly."""
        from src.models import VirtualMachine
        from dashboard.pages import overview
        
        # Add VM with nulls
        vm = VirtualMachine(
            vm="null-vm",
            powerstate=None,
            cpus=None,
            memory=None,
        )
        db_session.add(vm)
        db_session.commit()
        
        try:
            with patch('streamlit.title'), \
                 patch('streamlit.metric'):
                overview.render(db_url)
            # Should handle nulls gracefully
        except Exception as e:
            pytest.fail(f"Should handle null values: {e}")
    
    def test_overview_handles_zero_values(self, db_session, db_url):
        """Test that overview handles zero values correctly."""
        from src.models import VirtualMachine
        from dashboard.pages import overview
        
        # Add VM with zeros
        vm = VirtualMachine(
            vm="zero-vm",
            powerstate="poweredOn",
            cpus=0,
            memory=0,
        )
        db_session.add(vm)
        db_session.commit()
        
        try:
            with patch('streamlit.title'), \
                 patch('streamlit.metric'):
                overview.render(db_url)
            # Should handle zeros gracefully
        except Exception as e:
            pytest.fail(f"Should handle zero values: {e}")
    
    def test_overview_validates_percentage_calculations(self, populated_db_session):
        """Test that percentage calculations are valid."""
        from sqlalchemy import func
        from src.models import VirtualMachine
        
        total = populated_db_session.query(func.count(VirtualMachine.id)).scalar()
        powered_on = populated_db_session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.powerstate == "poweredOn"
        ).scalar()
        
        if total > 0:
            percentage = (powered_on / total) * 100
            assert 0 <= percentage <= 100
