"""
System status dashboard and logging interface for monitoring.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import logging
from pathlib import Path

from .health_checker import health_checker, HealthStatus
from .performance_monitor import performance_monitor
from .alerting_system import alert_manager

logger = logging.getLogger(__name__)


class StatusDashboard:
    """System status dashboard for monitoring and visualization"""
    
    def __init__(self):
        self.dashboard_data = {}
        self.last_update = None
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Get health check results
            health_results = await health_checker.check_all_components()
            
            # Get performance metrics
            performance_summary = performance_monitor.get_performance_summary(duration_minutes=60)
            
            # Get alert information
            active_alerts = alert_manager.get_active_alerts()
            alert_stats = alert_manager.get_alert_statistics(hours=24)
            
            # Compile dashboard data
            dashboard_data = {
                'timestamp': datetime.now(),
                'uptime_seconds': time.time() - health_checker.start_time,
                'overall_status': health_results.overall_status.value,
                'health': {
                    'overall_status': health_results.overall_status.value,
                    'components': {
                        name: {
                            'status': result.status.value,
                            'message': result.message,
                            'response_time_ms': result.response_time_ms,
                            'last_check': result.timestamp
                        }
                        for name, result in health_results.components.items()
                    }
                },
                'performance': performance_summary,
                'alerts': {
                    'active_count': len(active_alerts),
                    'active_alerts': [
                        {
                            'id': alert.id,
                            'title': alert.title,
                            'severity': alert.severity.value,
                            'component': alert.component,
                            'timestamp': alert.timestamp,
                            'status': alert.status.value
                        }
                        for alert in active_alerts[:10]  # Limit to 10 most recent
                    ],
                    'statistics': alert_stats
                },
                'system_info': self._get_system_info()
            }
            
            self.dashboard_data = dashboard_data
            self.last_update = datetime.now()
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating system status: {e}")
            return {
                'timestamp': datetime.now(),
                'error': str(e),
                'overall_status': 'error'
            }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        try:
            import platform
            import psutil
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'total_memory_gb': psutil.virtual_memory().total / (1024**3),
                'boot_time': datetime.fromtimestamp(psutil.boot_time())
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def get_component_details(self, component_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific component"""
        try:
            # Health check details
            health_result = health_checker.get_component_status(component_name)
            
            # Performance metrics
            performance_history = performance_monitor.metrics_collector.get_component_metrics_history(
                component_name, duration_minutes=60
            )
            
            # Recent alerts
            component_alerts = [
                alert for alert in alert_manager.get_alert_history(hours=24)
                if alert.component == component_name
            ]
            
            return {
                'component': component_name,
                'timestamp': datetime.now(),
                'health': asdict(health_result) if health_result else None,
                'performance': {
                    'history_count': len(performance_history),
                    'recent_metrics': [asdict(m) for m in performance_history[-10:]] if performance_history else []
                },
                'alerts': {
                    'recent_count': len(component_alerts),
                    'recent_alerts': [asdict(alert) for alert in component_alerts[:5]]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting component details for {component_name}: {e}")
            return {
                'component': component_name,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def get_performance_trends(self, duration_hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            # System metrics trends
            system_history = performance_monitor.metrics_collector.get_system_metrics_history(
                duration_minutes=duration_hours * 60
            )
            
            trends = {
                'duration_hours': duration_hours,
                'timestamp': datetime.now(),
                'system_trends': {
                    'cpu_usage': [
                        {'timestamp': m.timestamp, 'value': m.cpu_percent}
                        for m in system_history
                    ],
                    'memory_usage': [
                        {'timestamp': m.timestamp, 'value': m.memory_percent}
                        for m in system_history
                    ],
                    'disk_usage': [
                        {'timestamp': m.timestamp, 'value': m.disk_usage_percent}
                        for m in system_history
                    ]
                },
                'component_trends': {}
            }
            
            # Component trends
            for component in performance_monitor.component_trackers.keys():
                component_history = performance_monitor.metrics_collector.get_component_metrics_history(
                    component, duration_minutes=duration_hours * 60
                )
                
                trends['component_trends'][component] = {
                    'response_time': [
                        {'timestamp': m.timestamp, 'value': m.response_time_ms}
                        for m in component_history
                    ],
                    'throughput': [
                        {'timestamp': m.timestamp, 'value': m.throughput_per_second}
                        for m in component_history
                    ],
                    'error_rate': [
                        {'timestamp': m.timestamp, 'value': m.error_rate_percent}
                        for m in component_history
                    ]
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def export_status_report(self, output_path: Optional[str] = None) -> str:
        """Export comprehensive status report"""
        try:
            report_data = {
                'report_timestamp': datetime.now(),
                'system_status': self.dashboard_data or {},
                'performance_trends': self.get_performance_trends(duration_hours=24),
                'component_details': {}
            }
            
            # Add component details
            if self.dashboard_data and 'health' in self.dashboard_data:
                for component_name in self.dashboard_data['health']['components'].keys():
                    report_data['component_details'][component_name] = self.get_component_details(component_name)
            
            # Generate report
            report_json = json.dumps(report_data, indent=2, default=str)
            
            # Save to file if path provided
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(report_json)
                logger.info(f"Status report exported to {output_path}")
            
            return report_json
            
        except Exception as e:
            logger.error(f"Error exporting status report: {e}")
            return json.dumps({'error': str(e), 'timestamp': datetime.now()}, default=str)


class LoggingInterface:
    """Enhanced logging interface for monitoring"""
    
    def __init__(self, log_dir: str = "logs/monitoring"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup specialized loggers
        self.setup_monitoring_loggers()
    
    def setup_monitoring_loggers(self):
        """Setup specialized loggers for monitoring"""
        # Health check logger
        health_logger = logging.getLogger('diary_agent.monitoring.health')
        health_handler = logging.FileHandler(self.log_dir / 'health_checks.log')
        health_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        health_logger.addHandler(health_handler)
        health_logger.setLevel(logging.INFO)
        
        # Performance logger
        perf_logger = logging.getLogger('diary_agent.monitoring.performance')
        perf_handler = logging.FileHandler(self.log_dir / 'performance.log')
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        
        # Alert logger
        alert_logger = logging.getLogger('diary_agent.monitoring.alerts')
        alert_handler = logging.FileHandler(self.log_dir / 'alerts.log')
        alert_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        alert_logger.addHandler(alert_handler)
        alert_logger.setLevel(logging.WARNING)
        
        logger.info("Monitoring loggers configured")
    
    def log_health_check(self, component: str, status: str, message: str, response_time: float):
        """Log health check result"""
        health_logger = logging.getLogger('diary_agent.monitoring.health')
        health_logger.info(f"Component: {component}, Status: {status}, "
                          f"Response: {response_time:.2f}ms, Message: {message}")
    
    def log_performance_metric(self, component: str, metric_name: str, value: float, unit: str = ""):
        """Log performance metric"""
        perf_logger = logging.getLogger('diary_agent.monitoring.performance')
        perf_logger.info(f"Component: {component}, Metric: {metric_name}, "
                        f"Value: {value}{unit}")
    
    def log_alert(self, alert_id: str, title: str, severity: str, component: str, message: str):
        """Log alert"""
        alert_logger = logging.getLogger('diary_agent.monitoring.alerts')
        alert_logger.warning(f"Alert: {alert_id}, Title: {title}, "
                           f"Severity: {severity}, Component: {component}, Message: {message}")
    
    def get_log_summary(self, log_type: str = "all", hours: int = 24) -> Dict[str, Any]:
        """Get summary of log entries"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            summary = {
                'log_type': log_type,
                'duration_hours': hours,
                'timestamp': datetime.now(),
                'entries': []
            }
            
            log_files = []
            if log_type == "all":
                log_files = list(self.log_dir.glob("*.log"))
            else:
                log_files = [self.log_dir / f"{log_type}.log"]
            
            for log_file in log_files:
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Parse recent entries
                    recent_entries = []
                    for line in lines[-100:]:  # Last 100 lines
                        try:
                            # Simple timestamp parsing
                            if line.strip() and ' - ' in line:
                                timestamp_str = line.split(' - ')[0]
                                entry_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                
                                if entry_time >= cutoff_time:
                                    recent_entries.append({
                                        'timestamp': entry_time,
                                        'content': line.strip(),
                                        'file': log_file.name
                                    })
                        except:
                            continue
                    
                    summary['entries'].extend(recent_entries)
            
            # Sort by timestamp
            summary['entries'].sort(key=lambda x: x['timestamp'], reverse=True)
            summary['total_entries'] = len(summary['entries'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting log summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }


class MonitoringAPI:
    """Simple API interface for monitoring data"""
    
    def __init__(self):
        self.dashboard = StatusDashboard()
        self.logging_interface = LoggingInterface()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return await self.dashboard.get_system_status()
    
    async def get_component_status(self, component: str) -> Dict[str, Any]:
        """Get status for specific component"""
        return self.dashboard.get_component_details(component)
    
    async def get_alerts(self, active_only: bool = True) -> Dict[str, Any]:
        """Get alert information"""
        if active_only:
            alerts = alert_manager.get_active_alerts()
        else:
            alerts = alert_manager.get_alert_history(hours=24)
        
        return {
            'timestamp': datetime.now(),
            'active_only': active_only,
            'count': len(alerts),
            'alerts': [asdict(alert) for alert in alerts]
        }
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        alert = alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        
        if alert:
            return {
                'success': True,
                'alert_id': alert_id,
                'acknowledged_by': acknowledged_by,
                'timestamp': datetime.now()
            }
        else:
            return {
                'success': False,
                'error': 'Alert not found or already resolved',
                'alert_id': alert_id,
                'timestamp': datetime.now()
            }
    
    async def get_performance_data(self, duration_hours: int = 1) -> Dict[str, Any]:
        """Get performance data"""
        return self.dashboard.get_performance_trends(duration_hours)
    
    async def get_logs(self, log_type: str = "all", hours: int = 24) -> Dict[str, Any]:
        """Get log data"""
        return self.logging_interface.get_log_summary(log_type, hours)
    
    async def export_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export status report"""
        try:
            report_content = self.dashboard.export_status_report(output_path)
            return {
                'success': True,
                'output_path': output_path,
                'report_size': len(report_content),
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }


# Global instances
status_dashboard = StatusDashboard()
logging_interface = LoggingInterface()
monitoring_api = MonitoringAPI()


if __name__ == "__main__":
    # Example usage
    async def main():
        api = MonitoringAPI()
        
        # Get system status
        status = await api.get_status()
        print("System Status:")
        print(json.dumps(status, indent=2, default=str))
        
        # Get alerts
        alerts = await api.get_alerts()
        print(f"\nActive Alerts: {alerts['count']}")
        
        # Export report
        report_result = await api.export_report("monitoring_report.json")
        print(f"\nReport Export: {report_result['success']}")
    
    asyncio.run(main())