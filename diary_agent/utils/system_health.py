"""
System health dashboard and comprehensive status reporting.
Provides unified view of all error handling, monitoring, and recovery systems.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import asdict
from pathlib import Path

from .error_handler import global_error_handler, ErrorCategory
from .graceful_degradation import degradation_manager, ServiceHealth
from .monitoring import performance_monitor, alert_manager, health_check_registry
from .error_recovery import error_recovery_orchestrator
from .logger import get_component_logger, diary_logger


class SystemHealthDashboard:
    """Comprehensive system health dashboard."""
    
    def __init__(self):
        self.logger = get_component_logger("system_health")
        self.last_health_check = None
        self.health_history: List[Dict[str, Any]] = []
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including all subsystems."""
        timestamp = datetime.now()
        
        status = {
            "timestamp": timestamp.isoformat(),
            "overall_health": self._calculate_overall_health(),
            "subsystems": {
                "error_handling": self._get_error_handling_status(),
                "monitoring": self._get_monitoring_status(),
                "graceful_degradation": self._get_degradation_status(),
                "recovery": self._get_recovery_status(),
                "logging": self._get_logging_status()
            },
            "components": self._get_component_status(),
            "alerts": self._get_alert_status(),
            "performance": self._get_performance_summary(),
            "recommendations": self._generate_recommendations()
        }
        
        # Store in history
        self.health_history.append(status)
        self._cleanup_history()
        
        self.last_health_check = timestamp
        return status
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health status."""
        try:
            # Get health from various subsystems
            degradation_health = degradation_manager.get_system_health_summary()
            error_stats = global_error_handler.get_error_statistics()
            alert_summary = alert_manager.get_alert_summary()
            
            # Check for critical issues
            if degradation_health["component_counts"]["unhealthy"] > 0:
                return "critical"
            
            if alert_summary["active_by_severity"].get("critical", 0) > 0:
                return "critical"
            
            # Check for warnings
            if (degradation_health["component_counts"]["degraded"] > 0 or
                alert_summary["active_by_severity"].get("high", 0) > 0 or
                error_stats["total_errors"] > 10):
                return "warning"
            
            # Check for minor issues
            if (alert_summary["active_alerts"] > 0 or
                error_stats["total_errors"] > 0):
                return "minor_issues"
            
            return "healthy"
            
        except Exception as e:
            self.logger.error(f"Error calculating overall health: {str(e)}")
            return "unknown"
    
    def _get_error_handling_status(self) -> Dict[str, Any]:
        """Get error handling subsystem status."""
        try:
            error_stats = global_error_handler.get_error_statistics()
            
            return {
                "status": "operational",
                "error_counts": error_stats["error_counts"],
                "total_errors": error_stats["total_errors"],
                "circuit_breakers": error_stats["circuit_breaker_states"],
                "active_handlers": len(global_error_handler.recovery_strategies)
            }
        except Exception as e:
            self.logger.error(f"Error getting error handling status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring subsystem status."""
        try:
            system_status = performance_monitor.get_system_status()
            
            return {
                "status": "operational" if performance_monitor.monitoring_active else "inactive",
                "monitoring_active": performance_monitor.monitoring_active,
                "system_metrics": system_status,
                "health_checks": len(health_check_registry.health_checks),
                "collection_interval": performance_monitor.collection_interval
            }
        except Exception as e:
            self.logger.error(f"Error getting monitoring status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_degradation_status(self) -> Dict[str, Any]:
        """Get graceful degradation subsystem status."""
        try:
            health_summary = degradation_manager.get_system_health_summary()
            
            return {
                "status": "operational",
                "overall_health": health_summary["overall_health"],
                "component_counts": health_summary["component_counts"],
                "monitoring_active": health_summary["monitoring_active"],
                "fallback_configs": len(degradation_manager.fallback_configs)
            }
        except Exception as e:
            self.logger.error(f"Error getting degradation status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_recovery_status(self) -> Dict[str, Any]:
        """Get error recovery subsystem status."""
        try:
            recovery_status = error_recovery_orchestrator.get_recovery_status()
            
            return {
                "status": "operational",
                "recovery_plans": recovery_status["recovery_plans"],
                "active_attempts": recovery_status["active_recovery_attempts"],
                "component_health": recovery_status["component_health"]
            }
        except Exception as e:
            self.logger.error(f"Error getting recovery status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_logging_status(self) -> Dict[str, Any]:
        """Get logging subsystem status."""
        try:
            log_stats = diary_logger.get_log_statistics()
            
            return {
                "status": "operational",
                "active_loggers": log_stats["active_loggers"],
                "log_directory": log_stats["log_directory"],
                "log_level": log_stats["log_level"],
                "log_files": log_stats["log_files"]
            }
        except Exception as e:
            self.logger.error(f"Error getting logging status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get individual component status."""
        components = {}
        
        # Get component health from degradation manager
        for component, health in degradation_manager.component_status.items():
            component_info = {
                "health": health.value,
                "performance": None,
                "last_check": None
            }
            
            # Add performance data if available
            try:
                perf_status = performance_monitor.get_component_status(component)
                if perf_status.get("status") != "no_data":
                    component_info["performance"] = {
                        "operation_count": perf_status["operation_count"],
                        "error_rate": perf_status["error_rate"],
                        "avg_response_time": perf_status["average_response_time"],
                        "last_operation": perf_status["last_operation_time"]
                    }
            except Exception:
                pass
            
            components[component] = component_info
        
        return components
    
    def _get_alert_status(self) -> Dict[str, Any]:
        """Get alert system status."""
        try:
            alert_summary = alert_manager.get_alert_summary()
            active_alerts = alert_manager.get_active_alerts()
            
            return {
                "summary": alert_summary,
                "active_alerts": [
                    {
                        "id": alert.alert_id,
                        "severity": alert.severity,
                        "component": alert.component,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "age_minutes": (datetime.now() - alert.timestamp).total_seconds() / 60
                    }
                    for alert in active_alerts
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting alert status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        try:
            return performance_monitor.get_performance_summary()
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate system health recommendations."""
        recommendations = []
        
        try:
            # Check error rates
            error_stats = global_error_handler.get_error_statistics()
            if error_stats["total_errors"] > 50:
                recommendations.append({
                    "priority": "high",
                    "category": "error_handling",
                    "message": "High error rate detected. Consider reviewing error patterns and improving error handling.",
                    "action": "review_error_logs"
                })
            
            # Check component health
            health_summary = degradation_manager.get_system_health_summary()
            if health_summary["component_counts"]["unhealthy"] > 0:
                recommendations.append({
                    "priority": "critical",
                    "category": "component_health",
                    "message": "Unhealthy components detected. Immediate attention required.",
                    "action": "investigate_unhealthy_components"
                })
            
            # Check alerts
            alert_summary = alert_manager.get_alert_summary()
            if alert_summary["active_by_severity"].get("critical", 0) > 0:
                recommendations.append({
                    "priority": "critical",
                    "category": "alerts",
                    "message": "Critical alerts active. Immediate investigation required.",
                    "action": "resolve_critical_alerts"
                })
            
            # Check monitoring
            if not performance_monitor.monitoring_active:
                recommendations.append({
                    "priority": "medium",
                    "category": "monitoring",
                    "message": "Performance monitoring is inactive. Enable monitoring for better system visibility.",
                    "action": "enable_monitoring"
                })
            
            # Check circuit breakers
            circuit_states = error_stats.get("circuit_breaker_states", {})
            open_breakers = [name for name, state in circuit_states.items() if state == "open"]
            if open_breakers:
                recommendations.append({
                    "priority": "high",
                    "category": "circuit_breakers",
                    "message": f"Circuit breakers open: {', '.join(open_breakers)}. Services may be degraded.",
                    "action": "investigate_circuit_breaker_failures"
                })
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            recommendations.append({
                "priority": "medium",
                "category": "system",
                "message": "Error generating recommendations. System health check may be impaired.",
                "action": "check_health_system"
            })
        
        return recommendations
    
    def _cleanup_history(self):
        """Clean up old health history entries."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.health_history = [
            entry for entry in self.health_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_history = [
            entry for entry in self.health_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        if not recent_history:
            return {"message": "No historical data available"}
        
        # Calculate trends
        health_states = [entry["overall_health"] for entry in recent_history]
        error_counts = [
            entry["subsystems"]["error_handling"]["total_errors"]
            for entry in recent_history
            if "error_handling" in entry["subsystems"]
        ]
        
        return {
            "period_hours": hours,
            "data_points": len(recent_history),
            "health_trend": {
                "current": health_states[-1] if health_states else "unknown",
                "previous": health_states[0] if health_states else "unknown",
                "stability": len(set(health_states)) == 1 if health_states else False
            },
            "error_trend": {
                "current": error_counts[-1] if error_counts else 0,
                "average": sum(error_counts) / len(error_counts) if error_counts else 0,
                "peak": max(error_counts) if error_counts else 0
            }
        }
    
    def export_health_report(self, filepath: Optional[str] = None) -> str:
        """Export comprehensive health report to file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"health_report_{timestamp}.json"
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "current_status": self.get_comprehensive_status(),
            "trends": self.get_health_trends(),
            "history_summary": {
                "total_entries": len(self.health_history),
                "oldest_entry": self.health_history[0]["timestamp"] if self.health_history else None,
                "newest_entry": self.health_history[-1]["timestamp"] if self.health_history else None
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Health report exported to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting health report: {str(e)}")
            raise
    
    def get_quick_status(self) -> Dict[str, Any]:
        """Get quick system status for monitoring dashboards."""
        try:
            overall_health = self._calculate_overall_health()
            alert_summary = alert_manager.get_alert_summary()
            error_stats = global_error_handler.get_error_statistics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "health": overall_health,
                "active_alerts": alert_summary["active_alerts"],
                "critical_alerts": alert_summary["active_by_severity"].get("critical", 0),
                "total_errors": error_stats["total_errors"],
                "monitoring_active": performance_monitor.monitoring_active,
                "status": "ok" if overall_health in ["healthy", "minor_issues"] else "attention_required"
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "health": "unknown",
                "status": "error",
                "message": str(e)
            }


# Global system health dashboard
system_health_dashboard = SystemHealthDashboard()


def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health status."""
    return system_health_dashboard.get_comprehensive_status()


def get_quick_health() -> Dict[str, Any]:
    """Get quick system health status."""
    return system_health_dashboard.get_quick_status()


def export_health_report(filepath: Optional[str] = None) -> str:
    """Export system health report."""
    return system_health_dashboard.export_health_report(filepath)


def start_all_monitoring():
    """Start all monitoring and health systems."""
    try:
        performance_monitor.start_monitoring()
        degradation_manager.start_monitoring()
        
        logger = get_component_logger("system_startup")
        logger.info("All monitoring systems started successfully")
        
        return True
    except Exception as e:
        logger = get_component_logger("system_startup")
        logger.error(f"Error starting monitoring systems: {str(e)}")
        return False


def stop_all_monitoring():
    """Stop all monitoring and health systems."""
    try:
        performance_monitor.stop_monitoring()
        degradation_manager.stop_monitoring()
        
        logger = get_component_logger("system_shutdown")
        logger.info("All monitoring systems stopped successfully")
        
        return True
    except Exception as e:
        logger = get_component_logger("system_shutdown")
        logger.error(f"Error stopping monitoring systems: {str(e)}")
        return False