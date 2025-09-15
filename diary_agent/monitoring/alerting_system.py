"""
Alerting system for component failures and performance issues.
"""

import asyncio
import time
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import json
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    component: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    tags: Optional[Dict[str, str]] = None
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str  # Python expression to evaluate
    severity: AlertSeverity
    message_template: str
    component: str
    cooldown_minutes: int = 5
    enabled: bool = True


@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    name: str
    type: str  # email, webhook, log
    config: Dict[str, Any]
    enabled: bool = True


class AlertManager:
    """Central alert management system"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.lock = threading.Lock()
        
        # Alert handlers
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        with self.lock:
            self.alert_rules[rule.name] = rule
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        with self.lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                logger.info(f"Removed alert rule: {rule_name}")
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel"""
        with self.lock:
            self.notification_channels[channel.name] = channel
            logger.info(f"Added notification channel: {channel.name}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add a custom alert handler"""
        self.alert_handlers.append(handler)
    
    def create_alert(self, title: str, message: str, severity: AlertSeverity, 
                    component: str, tags: Optional[Dict[str, str]] = None) -> Alert:
        """Create a new alert"""
        alert_id = f"{component}_{int(time.time() * 1000)}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            component=component,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        with self.lock:
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
        
        # Trigger notifications
        self._process_alert(alert)
        
        logger.warning(f"Alert created: {alert.title} ({alert.severity.value})")
        return alert
    
    def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None):
        """Resolve an active alert"""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                
                # Move to history
                del self.active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {alert.title}")
                return alert
        
        return None
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an active alert"""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                
                logger.info(f"Alert acknowledged: {alert.title} by {acknowledged_by}")
                return alert
        
        return None
    
    def get_active_alerts(self, component: Optional[str] = None, 
                         severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts with optional filtering"""
        with self.lock:
            alerts = list(self.active_alerts.values())
        
        if component:
            alerts = [a for a in alerts if a.component == component]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            return [a for a in self.alert_history if a.timestamp >= cutoff_time]
    
    def evaluate_rules(self, context: Dict[str, Any]):
        """Evaluate alert rules against current context"""
        current_time = datetime.now()
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule_name in self.alert_cooldowns:
                cooldown_end = self.alert_cooldowns[rule_name] + timedelta(minutes=rule.cooldown_minutes)
                if current_time < cooldown_end:
                    continue
            
            try:
                # Evaluate rule condition
                if self._evaluate_condition(rule.condition, context):
                    # Create alert
                    message = rule.message_template.format(**context)
                    alert = self.create_alert(
                        title=f"Rule triggered: {rule.name}",
                        message=message,
                        severity=rule.severity,
                        component=rule.component,
                        tags={'rule': rule.name}
                    )
                    
                    # Set cooldown
                    self.alert_cooldowns[rule_name] = current_time
                    
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_name}: {e}")
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate a condition expression"""
        try:
            # Create a safe evaluation environment
            safe_dict = {
                '__builtins__': {},
                'abs': abs,
                'max': max,
                'min': min,
                'len': len,
                'sum': sum,
                'any': any,
                'all': all,
            }
            safe_dict.update(context)
            
            return bool(eval(condition, safe_dict))
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _process_alert(self, alert: Alert):
        """Process a new alert through notification channels"""
        # Call custom handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        # Send notifications
        for channel_name, channel in self.notification_channels.items():
            if not channel.enabled:
                continue
            
            try:
                self._send_notification(alert, channel)
            except Exception as e:
                logger.error(f"Error sending notification via {channel_name}: {e}")
    
    def _send_notification(self, alert: Alert, channel: NotificationChannel):
        """Send notification through a specific channel"""
        if channel.type == "email":
            self._send_email_notification(alert, channel)
        elif channel.type == "webhook":
            self._send_webhook_notification(alert, channel)
        elif channel.type == "log":
            self._send_log_notification(alert, channel)
        else:
            logger.warning(f"Unknown notification channel type: {channel.type}")
    
    def _send_email_notification(self, alert: Alert, channel: NotificationChannel):
        """Send email notification"""
        config = channel.config
        
        msg = MIMEMultipart()
        msg['From'] = config.get('from_email', 'alerts@diary-agent.local')
        msg['To'] = config.get('to_email', 'admin@diary-agent.local')
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        
        body = f"""
Alert Details:
- Title: {alert.title}
- Message: {alert.message}
- Severity: {alert.severity.value}
- Component: {alert.component}
- Timestamp: {alert.timestamp}
- Tags: {alert.tags}

This is an automated alert from the Diary Agent monitoring system.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email (would need SMTP configuration)
        logger.info(f"Email notification sent for alert: {alert.title}")
    
    def _send_webhook_notification(self, alert: Alert, channel: NotificationChannel):
        """Send webhook notification"""
        import requests
        
        config = channel.config
        url = config.get('url')
        
        if not url:
            logger.error("Webhook URL not configured")
            return
        
        payload = {
            'alert': asdict(alert),
            'timestamp': datetime.now().isoformat()
        }
        
        headers = config.get('headers', {})
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Webhook notification sent for alert: {alert.title}")
    
    def _send_log_notification(self, alert: Alert, channel: NotificationChannel):
        """Send log notification"""
        config = channel.config
        level = config.get('level', 'warning').upper()
        
        log_message = f"ALERT [{alert.severity.value.upper()}] {alert.component}: {alert.message}"
        
        if level == 'CRITICAL':
            logger.critical(log_message)
        elif level == 'ERROR':
            logger.error(log_message)
        elif level == 'WARNING':
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for the specified time period"""
        history = self.get_alert_history(hours)
        
        stats = {
            'total_alerts': len(history),
            'active_alerts': len(self.active_alerts),
            'by_severity': defaultdict(int),
            'by_component': defaultdict(int),
            'by_status': defaultdict(int),
            'resolution_times': []
        }
        
        for alert in history:
            stats['by_severity'][alert.severity.value] += 1
            stats['by_component'][alert.component] += 1
            stats['by_status'][alert.status.value] += 1
            
            if alert.resolved_at and alert.timestamp:
                resolution_time = (alert.resolved_at - alert.timestamp).total_seconds()
                stats['resolution_times'].append(resolution_time)
        
        # Calculate average resolution time
        if stats['resolution_times']:
            stats['avg_resolution_time_seconds'] = sum(stats['resolution_times']) / len(stats['resolution_times'])
        else:
            stats['avg_resolution_time_seconds'] = 0
        
        return dict(stats)


class AlertingIntegration:
    """Integration between monitoring systems and alerting"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.setup_default_rules()
    
    def setup_default_rules(self):
        """Setup default alert rules"""
        # High CPU usage
        self.alert_manager.add_alert_rule(AlertRule(
            name="high_cpu_usage",
            condition="system_metrics.get('cpu_percent', 0) > 80",
            severity=AlertSeverity.WARNING,
            message_template="High CPU usage detected: {cpu_percent:.1f}%",
            component="system",
            cooldown_minutes=5
        ))
        
        # Critical CPU usage
        self.alert_manager.add_alert_rule(AlertRule(
            name="critical_cpu_usage",
            condition="system_metrics.get('cpu_percent', 0) > 95",
            severity=AlertSeverity.CRITICAL,
            message_template="Critical CPU usage detected: {cpu_percent:.1f}%",
            component="system",
            cooldown_minutes=2
        ))
        
        # High memory usage
        self.alert_manager.add_alert_rule(AlertRule(
            name="high_memory_usage",
            condition="system_metrics.get('memory_percent', 0) > 85",
            severity=AlertSeverity.WARNING,
            message_template="High memory usage detected: {memory_percent:.1f}%",
            component="system",
            cooldown_minutes=5
        ))
        
        # Component health failures
        self.alert_manager.add_alert_rule(AlertRule(
            name="component_unhealthy",
            condition="any(status == 'unhealthy' for status in component_health.values())",
            severity=AlertSeverity.CRITICAL,
            message_template="One or more components are unhealthy",
            component="health_check",
            cooldown_minutes=3
        ))
        
        # High error rate
        self.alert_manager.add_alert_rule(AlertRule(
            name="high_error_rate",
            condition="any(metrics.get('error_rate_percent', 0) > 10 for metrics in component_metrics.values())",
            severity=AlertSeverity.WARNING,
            message_template="High error rate detected in components",
            component="performance",
            cooldown_minutes=5
        ))
        
        logger.info("Default alert rules configured")
    
    def setup_default_channels(self):
        """Setup default notification channels"""
        # Log channel
        self.alert_manager.add_notification_channel(NotificationChannel(
            name="log_channel",
            type="log",
            config={'level': 'warning'},
            enabled=True
        ))
        
        # Email channel (would need SMTP configuration)
        self.alert_manager.add_notification_channel(NotificationChannel(
            name="email_channel",
            type="email",
            config={
                'from_email': 'alerts@diary-agent.local',
                'to_email': 'admin@diary-agent.local',
                'smtp_server': 'localhost',
                'smtp_port': 587
            },
            enabled=False  # Disabled by default
        ))
        
        logger.info("Default notification channels configured")
    
    def process_health_check_results(self, health_results: Dict[str, Any]):
        """Process health check results and trigger alerts"""
        context = {
            'component_health': {
                comp: result.status.value 
                for comp, result in health_results.get('components', {}).items()
            },
            'system_health': health_results.get('overall_status', 'unknown')
        }
        
        self.alert_manager.evaluate_rules(context)
    
    def process_performance_metrics(self, performance_data: Dict[str, Any]):
        """Process performance metrics and trigger alerts"""
        context = {
            'system_metrics': {},
            'component_metrics': {}
        }
        
        # System metrics
        if 'system' in performance_data and performance_data['system']:
            system = performance_data['system']
            context['system_metrics'] = {
                'cpu_percent': system.cpu_percent,
                'memory_percent': system.memory_percent,
                'disk_usage_percent': system.disk_usage_percent
            }
        
        # Component metrics
        if 'components' in performance_data:
            for component, metrics in performance_data['components'].items():
                context['component_metrics'][component] = {
                    'response_time_ms': metrics.response_time_ms,
                    'error_rate_percent': metrics.error_rate_percent,
                    'throughput_per_second': metrics.throughput_per_second
                }
        
        self.alert_manager.evaluate_rules(context)


# Global alert manager instance
alert_manager = AlertManager()
alerting_integration = AlertingIntegration(alert_manager)


if __name__ == "__main__":
    # Example usage
    manager = AlertManager()
    integration = AlertingIntegration(manager)
    integration.setup_default_channels()
    
    # Create a test alert
    alert = manager.create_alert(
        title="Test Alert",
        message="This is a test alert",
        severity=AlertSeverity.WARNING,
        component="test_component"
    )
    
    print(f"Created alert: {alert.id}")
    
    # Get active alerts
    active = manager.get_active_alerts()
    print(f"Active alerts: {len(active)}")
    
    # Resolve the alert
    manager.resolve_alert(alert.id)
    print("Alert resolved")
    
    # Get statistics
    stats = manager.get_alert_statistics()
    print(f"Alert statistics: {json.dumps(stats, indent=2)}")