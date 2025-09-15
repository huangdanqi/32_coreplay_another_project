"""
System monitoring and health check utilities for the diary agent.
Provides real-time monitoring, alerting, and system status reporting.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .logger import get_component_logger


class HealthCheckRegistry:
    """Registry for system health checks."""
    
    def __init__(self):
        self.logger = get_component_logger("health_check_registry")
        self.health_checks: Dict[str, callable] = {}
    
    def register_check(self, component_name: str, check_function: callable):
        """Register a health check function for a component."""
        self.health_checks[component_name] = check_function
        self.logger.info(f"Registered health check for component: {component_name}")
    
    def unregister_check(self, component_name: str):
        """Unregister a health check function."""
        if component_name in self.health_checks:
            del self.health_checks[component_name]
            self.logger.info(f"Unregistered health check for component: {component_name}")
    
    def run_check(self, component_name: str) -> bool:
        """Run health check for a specific component."""
        if component_name not in self.health_checks:
            self.logger.warning(f"No health check registered for component: {component_name}")
            return False
        
        try:
            result = self.health_checks[component_name]()
            return bool(result)
        except Exception as e:
            self.logger.error(f"Health check failed for {component_name}: {str(e)}")
            return False
    
    def run_all_checks(self) -> Dict[str, bool]:
        """Run all registered health checks."""
        results = {}
        for component_name in self.health_checks:
            results[component_name] = self.run_check(component_name)
        return results
    
    def get_registered_components(self) -> List[str]:
        """Get list of components with registered health checks."""
        return list(self.health_checks.keys())


class ServiceHealth(Enum):
    """Health status of system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Alert:
    """System alert definition."""
    alert_id: str
    severity: str
    component: str
    message: str
    timestamp: datetime
    resolved: bool = False


class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self):
        self.logger = get_component_logger("alert_manager")
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
    
    def create_alert(self, alert_id: str, severity: str, component: str, message: str, metadata: Dict[str, Any] = None) -> Alert:
        """Create a new alert."""
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            component=component,
            message=message,
            timestamp=datetime.now()
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.logger.warning(f"Alert created: {message}")
        
        return alert
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        return {
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history)
        }


class PerformanceMonitor:
    """Monitors system and component performance."""
    
    def __init__(self, collection_interval: int = 60):
        self.logger = get_component_logger("performance_monitor")
        self.collection_interval = collection_interval
        self.monitoring_active = False
        self.component_operations: Dict[str, List[Dict[str, Any]]] = {}
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring_active = True
        self.logger.info("Started performance monitoring")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        self.logger.info("Stopped performance monitoring")
    
    def record_component_operation(self, component: str, operation_time: float, success: bool, metadata: Dict[str, Any] = None):
        """Record a component operation for performance tracking."""
        if component not in self.component_operations:
            self.component_operations[component] = []
        
        operation = {
            "timestamp": datetime.now(),
            "operation_time": operation_time,
            "success": success,
            "metadata": metadata or {}
        }
        
        self.component_operations[component].append(operation)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status summary."""
        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self.monitoring_active,
            "components_tracked": len(self.component_operations)
        }
    
    def get_component_status(self, component: str) -> Dict[str, Any]:
        """Get status for a specific component."""
        if component not in self.component_operations:
            return {"status": "no_data"}
        
        operations = self.component_operations[component]
        if not operations:
            return {"status": "no_data"}
        
        total_ops = len(operations)
        successful_ops = sum(1 for op in operations if op["success"])
        
        return {
            "component_name": component,
            "operation_count": total_ops,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
            "last_operation": operations[-1]["timestamp"].isoformat()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        return {
            "system": self.get_system_status(),
            "components": {comp: self.get_component_status(comp) for comp in self.component_operations}
        }


# Global monitoring instances
performance_monitor = PerformanceMonitor()
alert_manager = AlertManager()
health_check_registry = HealthCheckRegistry()


def start_monitoring():
    """Start all monitoring systems."""
    performance_monitor.start_monitoring()


def stop_monitoring():
    """Stop all monitoring systems."""
    performance_monitor.stop_monitoring()