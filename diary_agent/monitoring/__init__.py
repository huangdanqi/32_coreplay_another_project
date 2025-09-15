"""
Monitoring package for the Diary Agent system.

This package provides comprehensive monitoring capabilities including:
- Health checks for all system components
- Performance monitoring and metrics collection
- Alerting system for component failures
- System status dashboard and logging interface
"""

from .health_checker import (
    HealthChecker,
    HealthStatus,
    HealthCheckResult,
    SystemHealth,
    ComponentHealthChecks,
    health_checker,
    setup_default_health_checks
)

from .performance_monitor import (
    PerformanceMonitor,
    MetricsCollector,
    ComponentTracker,
    PerformanceMetric,
    SystemMetrics,
    ComponentMetrics,
    RequestContext,
    performance_monitor
)

from .alerting_system import (
    AlertManager,
    Alert,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    NotificationChannel,
    AlertingIntegration,
    alert_manager,
    alerting_integration
)

from .status_dashboard import (
    StatusDashboard,
    LoggingInterface,
    MonitoringAPI,
    status_dashboard,
    logging_interface,
    monitoring_api
)

__all__ = [
    # Health checking
    'HealthChecker',
    'HealthStatus',
    'HealthCheckResult',
    'SystemHealth',
    'ComponentHealthChecks',
    'health_checker',
    'setup_default_health_checks',
    
    # Performance monitoring
    'PerformanceMonitor',
    'MetricsCollector',
    'ComponentTracker',
    'PerformanceMetric',
    'SystemMetrics',
    'ComponentMetrics',
    'RequestContext',
    'performance_monitor',
    
    # Alerting
    'AlertManager',
    'Alert',
    'AlertRule',
    'AlertSeverity',
    'AlertStatus',
    'NotificationChannel',
    'AlertingIntegration',
    'alert_manager',
    'alerting_integration',
    
    # Dashboard and logging
    'StatusDashboard',
    'LoggingInterface',
    'MonitoringAPI',
    'status_dashboard',
    'logging_interface',
    'monitoring_api'
]


def initialize_monitoring():
    """Initialize the complete monitoring system"""
    # Setup default health checks
    setup_default_health_checks()
    
    # Setup default alert rules and channels
    alerting_integration.setup_default_channels()
    
    # Start performance monitoring
    performance_monitor.start_monitoring()
    
    print("Monitoring system initialized successfully")


def start_monitoring():
    """Start all monitoring services"""
    import asyncio
    import threading
    
    # Start performance monitoring
    performance_monitor.start_monitoring()
    
    # Start health monitoring in background
    def health_monitor_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(health_checker.start_monitoring())
    
    health_thread = threading.Thread(target=health_monitor_thread, daemon=True)
    health_thread.start()
    
    print("All monitoring services started")


def stop_monitoring():
    """Stop all monitoring services"""
    performance_monitor.stop_monitoring()
    health_checker.stop_monitoring()
    print("All monitoring services stopped")


# Initialize monitoring on import
initialize_monitoring()