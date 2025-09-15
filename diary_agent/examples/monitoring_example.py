"""
Example demonstrating the monitoring system capabilities.
"""

import asyncio
import time
import json
from datetime import datetime

from diary_agent.monitoring import (
    health_checker, performance_monitor, alert_manager, status_dashboard,
    HealthStatus, AlertSeverity, start_monitoring, stop_monitoring
)


async def demonstrate_health_checks():
    """Demonstrate health check functionality"""
    print("=== Health Check Demonstration ===")
    
    # Register custom health checks
    def database_mock_check():
        return {"status": "healthy", "message": "Database connection OK"}
    
    def api_mock_check():
        return {"status": "degraded", "message": "API responding slowly"}
    
    def cache_mock_check():
        raise Exception("Cache server unreachable")
    
    health_checker.register_health_check("database", database_mock_check, 30)
    health_checker.register_health_check("api_service", api_mock_check, 45)
    health_checker.register_health_check("cache", cache_mock_check, 60)
    
    # Run health checks
    system_health = await health_checker.check_all_components()
    
    print(f"Overall Status: {system_health.overall_status.value}")
    print(f"Uptime: {system_health.uptime_seconds:.1f} seconds")
    print("\nComponent Health:")
    
    for component, result in system_health.components.items():
        print(f"  {component}: {result.status.value} - {result.message} ({result.response_time_ms:.1f}ms)")


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring"""
    print("\n=== Performance Monitoring Demonstration ===")
    
    # Register components for tracking
    web_tracker = performance_monitor.register_component("web_server")
    db_tracker = performance_monitor.register_component("database")
    
    # Simulate some requests
    print("Simulating web server requests...")
    for i in range(10):
        with web_tracker.start_request() as ctx:
            time.sleep(0.01 + (i * 0.005))  # Increasing response time
            if i % 4 == 0:  # 25% error rate
                ctx.mark_error()
    
    print("Simulating database queries...")
    for i in range(5):
        with db_tracker.start_request():
            time.sleep(0.02)  # Consistent DB response time
    
    # Get performance metrics
    web_metrics = web_tracker.get_current_metrics()
    db_metrics = db_tracker.get_current_metrics()
    
    print(f"\nWeb Server Metrics:")
    print(f"  Response Time: {web_metrics.response_time_ms:.1f}ms")
    print(f"  Throughput: {web_metrics.throughput_per_second:.1f} req/sec")
    print(f"  Error Rate: {web_metrics.error_rate_percent:.1f}%")
    print(f"  Active Requests: {web_metrics.active_requests}")
    
    print(f"\nDatabase Metrics:")
    print(f"  Response Time: {db_metrics.response_time_ms:.1f}ms")
    print(f"  Throughput: {db_metrics.throughput_per_second:.1f} req/sec")
    print(f"  Error Rate: {db_metrics.error_rate_percent:.1f}%")
    
    # Record custom metrics
    performance_monitor.record_custom_metric("memory_usage", 75.5, "percent")
    performance_monitor.record_custom_metric("disk_io", 1250, "ops/sec")
    
    print("\nCustom metrics recorded: memory_usage, disk_io")


def demonstrate_alerting():
    """Demonstrate alerting system"""
    print("\n=== Alerting System Demonstration ===")
    
    # Create some alerts
    alert1 = alert_manager.create_alert(
        title="High CPU Usage",
        message="CPU usage has exceeded 85% for 5 minutes",
        severity=AlertSeverity.WARNING,
        component="system",
        tags={"metric": "cpu", "threshold": "85%"}
    )
    
    alert2 = alert_manager.create_alert(
        title="Database Connection Failed",
        message="Unable to connect to primary database",
        severity=AlertSeverity.CRITICAL,
        component="database"
    )
    
    alert3 = alert_manager.create_alert(
        title="Disk Space Low",
        message="Disk usage is at 92%",
        severity=AlertSeverity.WARNING,
        component="storage"
    )
    
    print(f"Created {len(alert_manager.get_active_alerts())} alerts")
    
    # Show active alerts
    active_alerts = alert_manager.get_active_alerts()
    print("\nActive Alerts:")
    for alert in active_alerts:
        print(f"  [{alert.severity.value.upper()}] {alert.title}")
        print(f"    Component: {alert.component}")
        print(f"    Message: {alert.message}")
        print(f"    Time: {alert.timestamp.strftime('%H:%M:%S')}")
        print()
    
    # Acknowledge an alert
    alert_manager.acknowledge_alert(alert1.id, "admin_user")
    print(f"Acknowledged alert: {alert1.title}")
    
    # Resolve an alert
    alert_manager.resolve_alert(alert2.id)
    print(f"Resolved alert: {alert2.title}")
    
    # Show alert statistics
    stats = alert_manager.get_alert_statistics()
    print(f"\nAlert Statistics:")
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Active alerts: {stats['active_alerts']}")
    print(f"  By severity: {dict(stats['by_severity'])}")
    print(f"  By status: {dict(stats['by_status'])}")


async def demonstrate_dashboard():
    """Demonstrate status dashboard"""
    print("\n=== Status Dashboard Demonstration ===")
    
    # Get system status
    dashboard = status_dashboard
    system_status = await dashboard.get_system_status()
    
    print("System Status Summary:")
    print(f"  Overall Status: {system_status['overall_status']}")
    print(f"  Uptime: {system_status['uptime_seconds']:.1f} seconds")
    print(f"  Active Alerts: {system_status['alerts']['active_count']}")
    
    # Show component health
    if 'health' in system_status and 'components' in system_status['health']:
        print("\nComponent Health:")
        for component, health in system_status['health']['components'].items():
            print(f"  {component}: {health['status']} - {health['message']}")
    
    # Export status report
    report_path = "monitoring_report.json"
    dashboard.export_status_report(report_path)
    print(f"\nStatus report exported to: {report_path}")


def demonstrate_alert_rules():
    """Demonstrate alert rule evaluation"""
    print("\n=== Alert Rules Demonstration ===")
    
    from diary_agent.monitoring.alerting_system import AlertRule
    
    # Add custom alert rules
    cpu_rule = AlertRule(
        name="cpu_threshold",
        condition="cpu_usage > 80",
        severity=AlertSeverity.WARNING,
        message_template="CPU usage is {cpu_usage}%",
        component="system"
    )
    
    memory_rule = AlertRule(
        name="memory_threshold", 
        condition="memory_usage > 90",
        severity=AlertSeverity.CRITICAL,
        message_template="Memory usage is {memory_usage}%",
        component="system"
    )
    
    alert_manager.add_alert_rule(cpu_rule)
    alert_manager.add_alert_rule(memory_rule)
    
    print("Added alert rules: cpu_threshold, memory_threshold")
    
    # Simulate conditions that trigger alerts
    print("\nEvaluating rules with high CPU...")
    alert_manager.evaluate_rules({"cpu_usage": 85, "memory_usage": 70})
    
    print("Evaluating rules with high memory...")
    alert_manager.evaluate_rules({"cpu_usage": 60, "memory_usage": 95})
    
    # Show triggered alerts
    new_alerts = alert_manager.get_active_alerts()
    rule_alerts = [a for a in new_alerts if a.tags and 'rule' in a.tags]
    
    print(f"\nTriggered {len(rule_alerts)} rule-based alerts:")
    for alert in rule_alerts:
        print(f"  Rule: {alert.tags.get('rule')} - {alert.message}")


async def main():
    """Main demonstration function"""
    print("Diary Agent Monitoring System Demonstration")
    print("=" * 50)
    
    try:
        # Start monitoring services
        print("Starting monitoring services...")
        start_monitoring()
        
        # Wait a moment for services to start
        await asyncio.sleep(1)
        
        # Run demonstrations
        await demonstrate_health_checks()
        demonstrate_performance_monitoring()
        demonstrate_alerting()
        await demonstrate_dashboard()
        demonstrate_alert_rules()
        
        print("\n" + "=" * 50)
        print("Monitoring demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop monitoring services
        print("\nStopping monitoring services...")
        stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())