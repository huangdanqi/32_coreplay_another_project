# Diary Agent Monitoring System

The monitoring system provides comprehensive health checks, performance monitoring, alerting, and status dashboard capabilities for the Diary Agent system.

## Overview

The monitoring system consists of four main components:

1. **Health Checker** - Monitors component health and system status
2. **Performance Monitor** - Tracks performance metrics and system resources
3. **Alerting System** - Manages alerts, rules, and notifications
4. **Status Dashboard** - Provides system status visualization and reporting

## Components

### Health Checker (`health_checker.py`)

Monitors the health of all system components and provides overall system status.

**Features:**
- Component health checks with configurable intervals
- Async health check execution with timeout protection
- Overall system health calculation
- Built-in health checks for core components
- Extensible health check registration

**Usage:**
```python
from diary_agent.monitoring import health_checker, setup_default_health_checks

# Setup default health checks
setup_default_health_checks()

# Register custom health check
def my_component_health():
    return {"status": "healthy", "message": "Component is working"}

health_checker.register_health_check("my_component", my_component_health, interval=60)

# Check system health
system_health = await health_checker.check_all_components()
print(f"Overall status: {system_health.overall_status.value}")
```

### Performance Monitor (`performance_monitor.py`)

Tracks system and component performance metrics.

**Features:**
- System resource monitoring (CPU, memory, disk)
- Component-specific performance tracking
- Request/response time tracking
- Throughput and error rate monitoring
- Custom metric recording
- Performance trend analysis

**Usage:**
```python
from diary_agent.monitoring import performance_monitor

# Start monitoring
performance_monitor.start_monitoring()

# Register component for tracking
tracker = performance_monitor.register_component("my_service")

# Track requests
with tracker.start_request() as ctx:
    # Do work
    if error_occurred:
        ctx.mark_error()

# Record custom metrics
performance_monitor.record_custom_metric("queue_size", 42, "items")

# Get performance summary
summary = performance_monitor.get_performance_summary(duration_minutes=60)
```

### Alerting System (`alerting_system.py`)

Manages alerts, alert rules, and notification channels.

**Features:**
- Alert creation, acknowledgment, and resolution
- Rule-based alert triggering
- Multiple notification channels (email, webhook, log)
- Alert cooldown and deduplication
- Alert statistics and history
- Custom alert handlers

**Usage:**
```python
from diary_agent.monitoring import alert_manager, AlertSeverity, AlertRule

# Create alert
alert = alert_manager.create_alert(
    title="High CPU Usage",
    message="CPU usage exceeded 80%",
    severity=AlertSeverity.WARNING,
    component="system"
)

# Add alert rule
rule = AlertRule(
    name="cpu_alert",
    condition="cpu_usage > 80",
    severity=AlertSeverity.WARNING,
    message_template="CPU usage is {cpu_usage}%",
    component="system"
)
alert_manager.add_alert_rule(rule)

# Evaluate rules
alert_manager.evaluate_rules({"cpu_usage": 85})

# Acknowledge alert
alert_manager.acknowledge_alert(alert.id, "admin")
```

### Status Dashboard (`status_dashboard.py`)

Provides system status visualization and reporting.

**Features:**
- Comprehensive system status overview
- Component-specific status details
- Performance trend visualization
- Alert status and history
- Status report export
- Enhanced logging interface
- REST-like API interface

**Usage:**
```python
from diary_agent.monitoring import status_dashboard, monitoring_api

# Get system status
status = await status_dashboard.get_system_status()
print(f"Overall status: {status['overall_status']}")

# Get component details
details = status_dashboard.get_component_details("my_component")

# Export status report
status_dashboard.export_status_report("status_report.json")

# Use monitoring API
api_status = await monitoring_api.get_status()
alerts = await monitoring_api.get_alerts()
```

## Configuration

### Health Check Configuration

Health checks are registered with configurable intervals:

```python
# Register health check with 30-second interval
health_checker.register_health_check("component", check_function, interval=30)
```

### Alert Rules Configuration

Alert rules use Python expressions for conditions:

```python
AlertRule(
    name="high_memory",
    condition="memory_percent > 85",  # Python expression
    severity=AlertSeverity.WARNING,
    message_template="Memory usage: {memory_percent}%",
    component="system",
    cooldown_minutes=5
)
```

### Notification Channels

Configure notification channels for alerts:

```python
# Email notification
email_channel = NotificationChannel(
    name="email",
    type="email",
    config={
        "from_email": "alerts@example.com",
        "to_email": "admin@example.com",
        "smtp_server": "smtp.example.com",
        "smtp_port": 587
    }
)

# Webhook notification
webhook_channel = NotificationChannel(
    name="webhook",
    type="webhook",
    config={
        "url": "https://hooks.slack.com/services/...",
        "headers": {"Content-Type": "application/json"}
    }
)

alert_manager.add_notification_channel(email_channel)
alert_manager.add_notification_channel(webhook_channel)
```

## Default Health Checks

The system includes built-in health checks for:

- **LLM Manager** - Checks LLM provider availability
- **Database** - Tests database connectivity
- **Sub-Agent Manager** - Verifies agent health
- **Config Manager** - Validates configuration loading
- **Event Router** - Checks event mapping availability
- **Daily Scheduler** - Verifies scheduler initialization

## Default Alert Rules

Pre-configured alert rules include:

- **High CPU Usage** - CPU > 80% (Warning), CPU > 95% (Critical)
- **High Memory Usage** - Memory > 85% (Warning)
- **Component Failures** - Any component unhealthy (Critical)
- **High Error Rate** - Component error rate > 10% (Warning)

## Monitoring Startup

Initialize and start all monitoring services:

```python
from diary_agent.monitoring import start_monitoring, stop_monitoring

# Start all monitoring services
start_monitoring()

# Stop all monitoring services (cleanup)
stop_monitoring()
```

## Performance Considerations

- Health checks run asynchronously with configurable intervals
- Performance monitoring uses background threads
- Alert rule evaluation is optimized with cooldown periods
- Metrics history is limited to prevent memory growth
- Database operations are read-only for monitoring

## Logging

The monitoring system uses structured logging:

- **Health checks** → `logs/monitoring/health_checks.log`
- **Performance metrics** → `logs/monitoring/performance.log`
- **Alerts** → `logs/monitoring/alerts.log`

## Testing

Run monitoring system tests:

```bash
# Unit tests
python -m pytest diary_agent/tests/test_monitoring.py -v

# Integration tests
python -m pytest diary_agent/tests/test_monitoring_integration.py -v

# Run monitoring example
python diary_agent/examples/monitoring_example.py
```

## API Reference

### Health Status Enum
- `HEALTHY` - Component is functioning normally
- `DEGRADED` - Component has issues but is operational
- `UNHEALTHY` - Component is not functioning
- `UNKNOWN` - Component status cannot be determined

### Alert Severity Enum
- `INFO` - Informational alert
- `WARNING` - Warning condition
- `CRITICAL` - Critical condition requiring immediate attention

### Alert Status Enum
- `ACTIVE` - Alert is currently active
- `ACKNOWLEDGED` - Alert has been acknowledged by user
- `RESOLVED` - Alert condition has been resolved

## Integration with Diary Agent

The monitoring system integrates with the main Diary Agent components:

1. **Health checks** monitor all core components
2. **Performance tracking** measures component response times
3. **Alerts** notify of component failures or performance issues
4. **Dashboard** provides real-time system status

## Troubleshooting

### Common Issues

1. **Import Errors** - Ensure PYTHONPATH includes project root
2. **Permission Errors** - Check log directory write permissions
3. **Health Check Failures** - Verify component dependencies
4. **Alert Rule Errors** - Validate rule condition syntax

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('diary_agent.monitoring').setLevel(logging.DEBUG)
```

## Requirements

The monitoring system requires:

- Python 3.8+
- `psutil` for system metrics
- `asyncio` for async operations
- `pytest` for testing
- `requests` for webhook notifications (optional)

## Future Enhancements

Planned improvements:

- Web-based dashboard UI
- Metrics visualization charts
- Advanced alert correlation
- Machine learning anomaly detection
- Distributed monitoring support
- Custom metric aggregation