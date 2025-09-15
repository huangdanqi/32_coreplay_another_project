"""
Unit tests for the monitoring system components.
"""

import asyncio
import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from diary_agent.monitoring.health_checker import (
    HealthChecker, HealthStatus, HealthCheckResult, SystemHealth,
    ComponentHealthChecks, setup_default_health_checks
)
from diary_agent.monitoring.performance_monitor import (
    PerformanceMonitor, MetricsCollector, ComponentTracker,
    PerformanceMetric, SystemMetrics, ComponentMetrics
)
from diary_agent.monitoring.alerting_system import (
    AlertManager, Alert, AlertRule, AlertSeverity, AlertStatus,
    NotificationChannel, AlertingIntegration
)
from diary_agent.monitoring.status_dashboard import (
    StatusDashboard, LoggingInterface, MonitoringAPI
)


class TestHealthChecker:
    """Test cases for HealthChecker"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.health_checker = HealthChecker()
    
    def test_register_health_check(self):
        """Test registering health check functions"""
        def dummy_check():
            return True
        
        self.health_checker.register_health_check("test_component", dummy_check, 60)
        
        assert "test_component" in self.health_checker.health_checks
        assert self.health_checker.check_intervals["test_component"] == 60
    
    @pytest.mark.asyncio
    async def test_check_component_health_success(self):
        """Test successful component health check"""
        def healthy_check():
            return True
        
        self.health_checker.register_health_check("test_component", healthy_check)
        
        result = await self.health_checker.check_component_health("test_component")
        
        assert result.component == "test_component"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Component is healthy"
        assert result.response_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_check_component_health_failure(self):
        """Test failed component health check"""
        def failing_check():
            raise Exception("Component failed")
        
        self.health_checker.register_health_check("test_component", failing_check)
        
        result = await self.health_checker.check_component_health("test_component")
        
        assert result.component == "test_component"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Component failed" in result.message
    
    @pytest.mark.asyncio
    async def test_check_component_health_timeout(self):
        """Test health check timeout"""
        async def slow_check():
            await asyncio.sleep(15)  # Longer than 10s timeout
            return True
        
        self.health_checker.register_health_check("test_component", slow_check)
        
        result = await self.health_checker.check_component_health("test_component")
        
        assert result.component == "test_component"
        assert result.status == HealthStatus.UNHEALTHY
        assert "timed out" in result.message
    
    @pytest.mark.asyncio
    async def test_check_all_components(self):
        """Test checking all registered components"""
        def healthy_check():
            return True
        
        def degraded_check():
            return {"status": "degraded", "message": "Partially working"}
        
        self.health_checker.register_health_check("healthy_component", healthy_check)
        self.health_checker.register_health_check("degraded_component", degraded_check)
        
        system_health = await self.health_checker.check_all_components()
        
        assert isinstance(system_health, SystemHealth)
        assert system_health.overall_status == HealthStatus.DEGRADED
        assert len(system_health.components) == 2
        assert "healthy_component" in system_health.components
        assert "degraded_component" in system_health.components
    
    def test_calculate_overall_status(self):
        """Test overall status calculation"""
        # All healthy
        results = {
            "comp1": HealthCheckResult("comp1", HealthStatus.HEALTHY, "OK", datetime.now(), 10.0),
            "comp2": HealthCheckResult("comp2", HealthStatus.HEALTHY, "OK", datetime.now(), 15.0)
        }
        status = self.health_checker._calculate_overall_status(results)
        assert status == HealthStatus.HEALTHY
        
        # One degraded
        results["comp2"].status = HealthStatus.DEGRADED
        status = self.health_checker._calculate_overall_status(results)
        assert status == HealthStatus.DEGRADED
        
        # One unhealthy
        results["comp2"].status = HealthStatus.UNHEALTHY
        status = self.health_checker._calculate_overall_status(results)
        assert status == HealthStatus.UNHEALTHY


class TestComponentHealthChecks:
    """Test cases for ComponentHealthChecks"""
    
    @patch('diary_agent.monitoring.health_checker.LLMConfigManager')
    def test_llm_manager_health_success(self, mock_llm_manager):
        """Test LLM manager health check success"""
        mock_manager = Mock()
        mock_manager.providers = {"qwen": Mock(), "deepseek": Mock()}
        mock_llm_manager.return_value = mock_manager
        
        result = ComponentHealthChecks.llm_manager_health()
        
        assert result['status'] == 'healthy'
        assert 'providers available' in result['message']
    
    @patch('diary_agent.monitoring.health_checker.LLMConfigManager')
    def test_llm_manager_health_no_providers(self, mock_llm_manager):
        """Test LLM manager health check with no providers"""
        mock_manager = Mock()
        mock_manager.providers = {}
        mock_llm_manager.return_value = mock_manager
        
        result = ComponentHealthChecks.llm_manager_health()
        
        assert result['status'] == 'unhealthy'
        assert 'No LLM providers configured' in result['message']
    
    @patch('diary_agent.monitoring.health_checker.DatabaseManager')
    def test_database_health_success(self, mock_db_manager):
        """Test database health check success"""
        mock_manager = Mock()
        mock_manager.test_connection.return_value = True
        mock_db_manager.return_value = mock_manager
        
        result = ComponentHealthChecks.database_health()
        
        assert result['status'] == 'healthy'
        assert 'connection successful' in result['message']
    
    @patch('diary_agent.monitoring.health_checker.DatabaseManager')
    def test_database_health_failure(self, mock_db_manager):
        """Test database health check failure"""
        mock_manager = Mock()
        mock_manager.test_connection.return_value = False
        mock_db_manager.return_value = mock_manager
        
        result = ComponentHealthChecks.database_health()
        
        assert result['status'] == 'unhealthy'
        assert 'connection failed' in result['message']


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.monitor = PerformanceMonitor(collection_interval=1)
    
    def teardown_method(self):
        """Cleanup after tests"""
        if self.monitor.running:
            self.monitor.stop_monitoring()
    
    def test_register_component(self):
        """Test component registration"""
        tracker = self.monitor.register_component("test_component")
        
        assert isinstance(tracker, ComponentTracker)
        assert "test_component" in self.monitor.component_trackers
        assert tracker.component_name == "test_component"
    
    def test_record_custom_metric(self):
        """Test recording custom metrics"""
        self.monitor.record_custom_metric("test_metric", 42.5, "ms")
        
        metrics = self.monitor.metrics_collector.get_metric_history("test_metric")
        assert len(metrics) == 1
        assert metrics[0].name == "test_metric"
        assert metrics[0].value == 42.5
        assert metrics[0].unit == "ms"
    
    @patch('diary_agent.monitoring.performance_monitor.psutil')
    def test_collect_system_metrics(self, mock_psutil):
        """Test system metrics collection"""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 45.2
        mock_memory = Mock()
        mock_memory.percent = 67.8
        mock_memory.used = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_disk = Mock()
        mock_disk.used = 500 * 1024 * 1024 * 1024  # 500GB
        mock_disk.total = 1000 * 1024 * 1024 * 1024  # 1TB
        mock_disk.free = 500 * 1024 * 1024 * 1024  # 500GB
        mock_psutil.disk_usage.return_value = mock_disk
        
        metrics = self.monitor._collect_system_metrics()
        
        assert metrics.cpu_percent == 45.2
        assert metrics.memory_percent == 67.8
        assert metrics.memory_used_mb == 8192.0
        assert metrics.memory_available_mb == 4096.0
        assert metrics.disk_usage_percent == 50.0
        assert abs(metrics.disk_free_gb - 465.66) < 1  # Allow for rounding
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        assert not self.monitor.running
        
        self.monitor.start_monitoring()
        assert self.monitor.running
        assert self.monitor.monitor_thread is not None
        
        self.monitor.stop_monitoring()
        assert not self.monitor.running


class TestComponentTracker:
    """Test cases for ComponentTracker"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tracker = ComponentTracker("test_component")
    
    def test_request_tracking(self):
        """Test request tracking"""
        # Start a request
        with self.tracker.start_request() as ctx:
            time.sleep(0.01)  # Simulate work
        
        metrics = self.tracker.get_current_metrics()
        
        assert metrics.component == "test_component"
        assert metrics.throughput_per_second > 0
        assert metrics.response_time_ms > 0
        assert metrics.error_rate_percent == 0
        assert metrics.active_requests == 0
    
    def test_error_tracking(self):
        """Test error tracking"""
        # Successful request
        with self.tracker.start_request():
            time.sleep(0.01)
        
        # Failed request
        with self.tracker.start_request() as ctx:
            ctx.mark_error()
            time.sleep(0.01)
        
        metrics = self.tracker.get_current_metrics()
        
        assert metrics.error_rate_percent == 50.0  # 1 error out of 2 requests
    
    def test_reset_metrics(self):
        """Test metrics reset"""
        # Generate some metrics
        with self.tracker.start_request():
            time.sleep(0.01)
        
        initial_metrics = self.tracker.get_current_metrics()
        assert initial_metrics.throughput_per_second > 0
        
        # Reset and check
        self.tracker.reset_metrics()
        time.sleep(0.01)  # Small delay for time window
        
        reset_metrics = self.tracker.get_current_metrics()
        assert reset_metrics.request_count == 0


class TestAlertManager:
    """Test cases for AlertManager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.alert_manager = AlertManager()
    
    def test_create_alert(self):
        """Test alert creation"""
        alert = self.alert_manager.create_alert(
            title="Test Alert",
            message="This is a test",
            severity=AlertSeverity.WARNING,
            component="test_component"
        )
        
        assert alert.title == "Test Alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.ACTIVE
        assert alert.id in self.alert_manager.active_alerts
    
    def test_resolve_alert(self):
        """Test alert resolution"""
        alert = self.alert_manager.create_alert(
            title="Test Alert",
            message="This is a test",
            severity=AlertSeverity.WARNING,
            component="test_component"
        )
        
        resolved_alert = self.alert_manager.resolve_alert(alert.id)
        
        assert resolved_alert is not None
        assert resolved_alert.status == AlertStatus.RESOLVED
        assert resolved_alert.resolved_at is not None
        assert alert.id not in self.alert_manager.active_alerts
    
    def test_acknowledge_alert(self):
        """Test alert acknowledgment"""
        alert = self.alert_manager.create_alert(
            title="Test Alert",
            message="This is a test",
            severity=AlertSeverity.WARNING,
            component="test_component"
        )
        
        ack_alert = self.alert_manager.acknowledge_alert(alert.id, "test_user")
        
        assert ack_alert is not None
        assert ack_alert.status == AlertStatus.ACKNOWLEDGED
        assert ack_alert.acknowledged_by == "test_user"
        assert ack_alert.acknowledged_at is not None
    
    def test_add_alert_rule(self):
        """Test adding alert rules"""
        rule = AlertRule(
            name="test_rule",
            condition="cpu_usage > 80",
            severity=AlertSeverity.WARNING,
            message_template="High CPU: {cpu_usage}%",
            component="system"
        )
        
        self.alert_manager.add_alert_rule(rule)
        
        assert "test_rule" in self.alert_manager.alert_rules
        assert self.alert_manager.alert_rules["test_rule"] == rule
    
    def test_evaluate_rules(self):
        """Test rule evaluation"""
        rule = AlertRule(
            name="cpu_rule",
            condition="cpu_usage > 80",
            severity=AlertSeverity.WARNING,
            message_template="High CPU: {cpu_usage}%",
            component="system"
        )
        
        self.alert_manager.add_alert_rule(rule)
        
        # Test with high CPU
        context = {"cpu_usage": 85}
        self.alert_manager.evaluate_rules(context)
        
        active_alerts = self.alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert "High CPU: 85%" in active_alerts[0].message
    
    def test_alert_cooldown(self):
        """Test alert cooldown mechanism"""
        rule = AlertRule(
            name="cpu_rule",
            condition="cpu_usage > 80",
            severity=AlertSeverity.WARNING,
            message_template="High CPU: {cpu_usage}%",
            component="system",
            cooldown_minutes=1
        )
        
        self.alert_manager.add_alert_rule(rule)
        
        # First evaluation should create alert
        context = {"cpu_usage": 85}
        self.alert_manager.evaluate_rules(context)
        assert len(self.alert_manager.get_active_alerts()) == 1
        
        # Second evaluation should be blocked by cooldown
        self.alert_manager.evaluate_rules(context)
        assert len(self.alert_manager.get_active_alerts()) == 1  # Still only one
    
    def test_get_alert_statistics(self):
        """Test alert statistics"""
        # Create some alerts
        alert1 = self.alert_manager.create_alert(
            "Alert 1", "Message 1", AlertSeverity.WARNING, "comp1"
        )
        alert2 = self.alert_manager.create_alert(
            "Alert 2", "Message 2", AlertSeverity.CRITICAL, "comp2"
        )
        
        # Resolve one
        self.alert_manager.resolve_alert(alert1.id)
        
        stats = self.alert_manager.get_alert_statistics()
        
        assert stats['total_alerts'] == 2
        assert stats['active_alerts'] == 1
        assert stats['by_severity']['warning'] == 1
        assert stats['by_severity']['critical'] == 1
        assert stats['by_status']['resolved'] == 1
        assert stats['by_status']['active'] == 1


class TestStatusDashboard:
    """Test cases for StatusDashboard"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.dashboard = StatusDashboard()
    
    @pytest.mark.asyncio
    @patch('diary_agent.monitoring.status_dashboard.health_checker')
    @patch('diary_agent.monitoring.status_dashboard.performance_monitor')
    @patch('diary_agent.monitoring.status_dashboard.alert_manager')
    async def test_get_system_status(self, mock_alert_manager, mock_perf_monitor, mock_health_checker):
        """Test getting system status"""
        # Mock health checker
        mock_health_result = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            components={
                "test_comp": HealthCheckResult(
                    "test_comp", HealthStatus.HEALTHY, "OK", datetime.now(), 10.0
                )
            },
            timestamp=datetime.now(),
            uptime_seconds=3600
        )
        mock_health_checker.check_all_components.return_value = mock_health_result
        mock_health_checker.start_time = time.time() - 3600
        
        # Mock performance monitor
        mock_perf_monitor.get_performance_summary.return_value = {
            "system": {"cpu": {"current": 45.2}},
            "components": {}
        }
        
        # Mock alert manager
        mock_alert_manager.get_active_alerts.return_value = []
        mock_alert_manager.get_alert_statistics.return_value = {"total_alerts": 0}
        
        status = await self.dashboard.get_system_status()
        
        assert status['overall_status'] == 'healthy'
        assert 'health' in status
        assert 'performance' in status
        assert 'alerts' in status
        assert 'system_info' in status
    
    def test_get_component_details(self):
        """Test getting component details"""
        with patch('diary_agent.monitoring.status_dashboard.health_checker') as mock_health_checker, \
             patch('diary_agent.monitoring.status_dashboard.performance_monitor') as mock_perf_monitor, \
             patch('diary_agent.monitoring.status_dashboard.alert_manager') as mock_alert_manager:
            
            # Mock health checker
            mock_health_result = HealthCheckResult(
                "test_comp", HealthStatus.HEALTHY, "OK", datetime.now(), 10.0
            )
            mock_health_checker.get_component_status.return_value = mock_health_result
            
            # Mock performance monitor
            mock_perf_monitor.metrics_collector.get_component_metrics_history.return_value = []
            
            # Mock alert manager
            mock_alert_manager.get_alert_history.return_value = []
            
            details = self.dashboard.get_component_details("test_comp")
            
            assert details['component'] == "test_comp"
            assert 'health' in details
            assert 'performance' in details
            assert 'alerts' in details


class TestLoggingInterface:
    """Test cases for LoggingInterface"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.logging_interface = LoggingInterface(log_dir="test_logs")
    
    def test_log_health_check(self):
        """Test logging health check results"""
        # This test verifies the method doesn't crash
        self.logging_interface.log_health_check(
            "test_component", "healthy", "All good", 15.5
        )
    
    def test_log_performance_metric(self):
        """Test logging performance metrics"""
        # This test verifies the method doesn't crash
        self.logging_interface.log_performance_metric(
            "test_component", "response_time", 123.4, "ms"
        )
    
    def test_log_alert(self):
        """Test logging alerts"""
        # This test verifies the method doesn't crash
        self.logging_interface.log_alert(
            "alert_123", "Test Alert", "warning", "test_component", "Test message"
        )


class TestMonitoringAPI:
    """Test cases for MonitoringAPI"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.api = MonitoringAPI()
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting status via API"""
        with patch.object(self.api.dashboard, 'get_system_status') as mock_get_status:
            mock_get_status.return_value = {"status": "healthy"}
            
            result = await self.api.get_status()
            
            assert result == {"status": "healthy"}
            mock_get_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_alerts(self):
        """Test getting alerts via API"""
        with patch('diary_agent.monitoring.status_dashboard.alert_manager') as mock_alert_manager:
            mock_alert = Alert(
                id="test_alert",
                title="Test Alert",
                message="Test message",
                severity=AlertSeverity.WARNING,
                component="test_comp",
                timestamp=datetime.now()
            )
            mock_alert_manager.get_active_alerts.return_value = [mock_alert]
            
            result = await self.api.get_alerts(active_only=True)
            
            assert result['active_only'] is True
            assert result['count'] == 1
            assert len(result['alerts']) == 1
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self):
        """Test acknowledging alert via API"""
        with patch('diary_agent.monitoring.status_dashboard.alert_manager') as mock_alert_manager:
            mock_alert = Alert(
                id="test_alert",
                title="Test Alert",
                message="Test message",
                severity=AlertSeverity.WARNING,
                component="test_comp",
                timestamp=datetime.now()
            )
            mock_alert_manager.acknowledge_alert.return_value = mock_alert
            
            result = await self.api.acknowledge_alert("test_alert", "test_user")
            
            assert result['success'] is True
            assert result['alert_id'] == "test_alert"
            assert result['acknowledged_by'] == "test_user"


class TestAlertingIntegration:
    """Test cases for AlertingIntegration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.alert_manager = AlertManager()
        self.integration = AlertingIntegration(self.alert_manager)
    
    def test_setup_default_rules(self):
        """Test default rules setup"""
        # Rules should be added during initialization
        assert len(self.alert_manager.alert_rules) > 0
        assert "high_cpu_usage" in self.alert_manager.alert_rules
        assert "high_memory_usage" in self.alert_manager.alert_rules
    
    def test_process_health_check_results(self):
        """Test processing health check results"""
        health_results = {
            'overall_status': 'healthy',
            'components': {
                'test_comp': Mock(status=Mock(value='unhealthy'))
            }
        }
        
        # This should trigger the component_unhealthy rule
        self.integration.process_health_check_results(health_results)
        
        # Check if alert was created (would need more specific mocking for full test)
    
    def test_process_performance_metrics(self):
        """Test processing performance metrics"""
        performance_data = {
            'system': Mock(
                cpu_percent=85.0,
                memory_percent=90.0,
                disk_usage_percent=95.0
            ),
            'components': {
                'test_comp': Mock(
                    response_time_ms=5000.0,
                    error_rate_percent=15.0,
                    throughput_per_second=10.0
                )
            }
        }
        
        # This should trigger multiple rules
        self.integration.process_performance_metrics(performance_data)
        
        # Check if alerts were created (would need more specific mocking for full test)


if __name__ == "__main__":
    pytest.main([__file__])