"""
Integration tests for the monitoring system.
"""

import asyncio
import time
import pytest
from unittest.mock import patch, Mock

from diary_agent.monitoring import (
    health_checker, performance_monitor, alert_manager, status_dashboard,
    HealthStatus, AlertSeverity
)


class TestMonitoringIntegration:
    """Integration tests for the complete monitoring system"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Clear any existing state
        health_checker.health_checks.clear()
        health_checker.last_results.clear()
        alert_manager.active_alerts.clear()
        alert_manager.alert_history.clear()
    
    def teardown_method(self):
        """Cleanup after tests"""
        if performance_monitor.running:
            performance_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self):
        """Test health check system integration"""
        # Register a test health check
        def test_health_check():
            return {"status": "healthy", "message": "Test component is working"}
        
        health_checker.register_health_check("test_component", test_health_check)
        
        # Run health check
        system_health = await health_checker.check_all_components()
        
        assert system_health.overall_status == HealthStatus.HEALTHY
        assert "test_component" in system_health.components
        assert system_health.components["test_component"].status == HealthStatus.HEALTHY
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring integration"""
        # Register a component for tracking
        tracker = performance_monitor.register_component("test_service")
        
        # Simulate some requests
        with tracker.start_request():
            time.sleep(0.01)  # Simulate work
        
        with tracker.start_request() as ctx:
            ctx.mark_error()
            time.sleep(0.01)
        
        # Get metrics
        metrics = tracker.get_current_metrics()
        
        assert metrics.component == "test_service"
        assert metrics.throughput_per_second > 0
        assert metrics.error_rate_percent == 50.0  # 1 error out of 2 requests
    
    def test_alerting_integration(self):
        """Test alerting system integration"""
        # Create an alert
        alert = alert_manager.create_alert(
            title="Integration Test Alert",
            message="This is a test alert for integration testing",
            severity=AlertSeverity.WARNING,
            component="test_component"
        )
        
        # Verify alert was created
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].id == alert.id
        
        # Acknowledge the alert
        ack_alert = alert_manager.acknowledge_alert(alert.id, "test_user")
        assert ack_alert is not None
        assert ack_alert.acknowledged_by == "test_user"
        
        # Resolve the alert
        resolved_alert = alert_manager.resolve_alert(alert.id)
        assert resolved_alert is not None
        assert len(alert_manager.get_active_alerts()) == 0
    
    @pytest.mark.asyncio
    async def test_dashboard_integration(self):
        """Test status dashboard integration"""
        # Mock the monitoring components
        with patch('diary_agent.monitoring.status_dashboard.health_checker') as mock_health, \
             patch('diary_agent.monitoring.status_dashboard.performance_monitor') as mock_perf, \
             patch('diary_agent.monitoring.status_dashboard.alert_manager') as mock_alerts:
            
            # Setup mocks
            mock_health.check_all_components.return_value = Mock(
                overall_status=HealthStatus.HEALTHY,
                components={},
                timestamp=time.time(),
                uptime_seconds=3600
            )
            mock_health.start_time = time.time() - 3600
            
            mock_perf.get_performance_summary.return_value = {
                "system": {"cpu": {"current": 25.0}},
                "components": {}
            }
            
            mock_alerts.get_active_alerts.return_value = []
            mock_alerts.get_alert_statistics.return_value = {"total_alerts": 0}
            
            # Get system status
            dashboard = status_dashboard
            status = await dashboard.get_system_status()
            
            assert "overall_status" in status
            assert "health" in status
            assert "performance" in status
            assert "alerts" in status
    
    def test_end_to_end_monitoring_flow(self):
        """Test complete monitoring flow from health check to alert"""
        # Register a failing health check
        def failing_health_check():
            return {"status": "unhealthy", "message": "Component is down"}
        
        health_checker.register_health_check("failing_component", failing_health_check)
        
        # Add an alert rule for unhealthy components
        from diary_agent.monitoring.alerting_system import AlertRule
        
        rule = AlertRule(
            name="component_failure",
            condition="component_health.get('failing_component') == 'unhealthy'",
            severity=AlertSeverity.CRITICAL,
            message_template="Component {component} is unhealthy",
            component="failing_component"
        )
        
        alert_manager.add_alert_rule(rule)
        
        # Simulate health check results processing
        context = {
            "component_health": {"failing_component": "unhealthy"},
            "component": "failing_component"
        }
        
        alert_manager.evaluate_rules(context)
        
        # Verify alert was created
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) > 0
        
        # Find the alert created by our rule
        rule_alerts = [a for a in active_alerts if a.tags and a.tags.get('rule') == 'component_failure']
        assert len(rule_alerts) > 0
    
    def test_performance_alert_integration(self):
        """Test performance monitoring triggering alerts"""
        # Create a performance-based alert rule
        from diary_agent.monitoring.alerting_system import AlertRule
        
        rule = AlertRule(
            name="high_response_time",
            condition="any(metrics.get('response_time_ms', 0) > 1000 for metrics in component_metrics.values())",
            severity=AlertSeverity.WARNING,
            message_template="High response time detected",
            component="performance"
        )
        
        alert_manager.add_alert_rule(rule)
        
        # Simulate high response time
        context = {
            "component_metrics": {
                "slow_service": {"response_time_ms": 1500, "error_rate_percent": 0}
            }
        }
        
        alert_manager.evaluate_rules(context)
        
        # Verify alert was created
        active_alerts = alert_manager.get_active_alerts()
        performance_alerts = [a for a in active_alerts if a.component == "performance"]
        assert len(performance_alerts) > 0
    
    def test_monitoring_system_startup_shutdown(self):
        """Test monitoring system startup and shutdown"""
        from diary_agent.monitoring import start_monitoring, stop_monitoring
        
        # Test startup
        start_monitoring()
        assert performance_monitor.running
        
        # Test shutdown
        stop_monitoring()
        assert not performance_monitor.running


if __name__ == "__main__":
    pytest.main([__file__, "-v"])