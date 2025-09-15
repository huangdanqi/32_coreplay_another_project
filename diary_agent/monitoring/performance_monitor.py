"""
Performance monitoring system for tracking metrics and system performance.
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None


@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    timestamp: datetime


@dataclass
class ComponentMetrics:
    """Component-specific performance metrics"""
    component: str
    response_time_ms: float
    throughput_per_second: float
    error_rate_percent: float
    active_requests: int
    timestamp: datetime


class MetricsCollector:
    """Collects and stores performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.system_metrics: deque = deque(maxlen=max_history)
        self.lock = threading.Lock()
        
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        with self.lock:
            self.metrics_history[metric.name].append(metric)
            
    def record_system_metrics(self, metrics: SystemMetrics):
        """Record system-level metrics"""
        with self.lock:
            self.system_metrics.append(metrics)
            
    def record_component_metrics(self, metrics: ComponentMetrics):
        """Record component-specific metrics"""
        with self.lock:
            self.component_metrics[metrics.component].append(metrics)
    
    def get_metric_history(self, metric_name: str, duration_minutes: int = 60) -> List[PerformanceMetric]:
        """Get metric history for the specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        with self.lock:
            history = self.metrics_history.get(metric_name, deque())
            return [m for m in history if m.timestamp >= cutoff_time]
    
    def get_system_metrics_history(self, duration_minutes: int = 60) -> List[SystemMetrics]:
        """Get system metrics history"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        with self.lock:
            return [m for m in self.system_metrics if m.timestamp >= cutoff_time]
    
    def get_component_metrics_history(self, component: str, duration_minutes: int = 60) -> List[ComponentMetrics]:
        """Get component metrics history"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        with self.lock:
            history = self.component_metrics.get(component, deque())
            return [m for m in history if m.timestamp >= cutoff_time]
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics for all components"""
        with self.lock:
            result = {
                'system': self.system_metrics[-1] if self.system_metrics else None,
                'components': {},
                'custom_metrics': {}
            }
            
            # Latest component metrics
            for component, history in self.component_metrics.items():
                if history:
                    result['components'][component] = history[-1]
            
            # Latest custom metrics
            for metric_name, history in self.metrics_history.items():
                if history:
                    result['custom_metrics'][metric_name] = history[-1]
            
            return result


class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.metrics_collector = MetricsCollector()
        self.running = False
        self.monitor_thread = None
        
        # Component performance trackers
        self.component_trackers: Dict[str, ComponentTracker] = {}
        
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.metrics_collector.record_system_metrics(system_metrics)
                
                # Collect component metrics
                for component, tracker in self.component_trackers.items():
                    component_metrics = tracker.get_current_metrics()
                    self.metrics_collector.record_component_metrics(component_metrics)
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0,
                timestamp=datetime.now()
            )
    
    def register_component(self, component_name: str) -> 'ComponentTracker':
        """Register a component for performance tracking"""
        tracker = ComponentTracker(component_name)
        self.component_trackers[component_name] = tracker
        logger.info(f"Registered performance tracking for {component_name}")
        return tracker
    
    def record_custom_metric(self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None):
        """Record a custom performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags
        )
        self.metrics_collector.record_metric(metric)
    
    def get_performance_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for the specified duration"""
        summary = {
            'duration_minutes': duration_minutes,
            'timestamp': datetime.now(),
            'system': self._get_system_summary(duration_minutes),
            'components': self._get_components_summary(duration_minutes),
            'alerts': self._check_performance_alerts()
        }
        return summary
    
    def _get_system_summary(self, duration_minutes: int) -> Dict[str, Any]:
        """Get system performance summary"""
        metrics = self.metrics_collector.get_system_metrics_history(duration_minutes)
        
        if not metrics:
            return {'status': 'no_data'}
        
        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_percent for m in metrics]
        
        return {
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values),
                'current': cpu_values[-1] if cpu_values else 0
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values),
                'current': memory_values[-1] if memory_values else 0
            },
            'samples': len(metrics)
        }
    
    def _get_components_summary(self, duration_minutes: int) -> Dict[str, Any]:
        """Get components performance summary"""
        summary = {}
        
        for component in self.component_trackers.keys():
            metrics = self.metrics_collector.get_component_metrics_history(component, duration_minutes)
            
            if not metrics:
                summary[component] = {'status': 'no_data'}
                continue
            
            response_times = [m.response_time_ms for m in metrics]
            throughputs = [m.throughput_per_second for m in metrics]
            error_rates = [m.error_rate_percent for m in metrics]
            
            summary[component] = {
                'response_time_ms': {
                    'avg': sum(response_times) / len(response_times),
                    'max': max(response_times),
                    'min': min(response_times),
                    'p95': self._calculate_percentile(response_times, 95)
                },
                'throughput': {
                    'avg': sum(throughputs) / len(throughputs),
                    'max': max(throughputs),
                    'current': throughputs[-1] if throughputs else 0
                },
                'error_rate': {
                    'avg': sum(error_rates) / len(error_rates),
                    'max': max(error_rates),
                    'current': error_rates[-1] if error_rates else 0
                },
                'samples': len(metrics)
            }
        
        return summary
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _check_performance_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance alerts"""
        alerts = []
        
        # Get latest system metrics
        latest_metrics = self.metrics_collector.get_latest_metrics()
        
        if latest_metrics['system']:
            system = latest_metrics['system']
            
            # CPU alert
            if system.cpu_percent > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'warning' if system.cpu_percent < 90 else 'critical',
                    'message': f'High CPU usage: {system.cpu_percent:.1f}%',
                    'timestamp': datetime.now()
                })
            
            # Memory alert
            if system.memory_percent > 85:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'warning' if system.memory_percent < 95 else 'critical',
                    'message': f'High memory usage: {system.memory_percent:.1f}%',
                    'timestamp': datetime.now()
                })
            
            # Disk alert
            if system.disk_usage_percent > 90:
                alerts.append({
                    'type': 'high_disk',
                    'severity': 'warning' if system.disk_usage_percent < 95 else 'critical',
                    'message': f'High disk usage: {system.disk_usage_percent:.1f}%',
                    'timestamp': datetime.now()
                })
        
        # Component alerts
        for component, metrics in latest_metrics['components'].items():
            if metrics.error_rate_percent > 5:
                alerts.append({
                    'type': 'high_error_rate',
                    'component': component,
                    'severity': 'warning' if metrics.error_rate_percent < 10 else 'critical',
                    'message': f'{component} high error rate: {metrics.error_rate_percent:.1f}%',
                    'timestamp': datetime.now()
                })
            
            if metrics.response_time_ms > 5000:
                alerts.append({
                    'type': 'slow_response',
                    'component': component,
                    'severity': 'warning' if metrics.response_time_ms < 10000 else 'critical',
                    'message': f'{component} slow response: {metrics.response_time_ms:.0f}ms',
                    'timestamp': datetime.now()
                })
        
        return alerts


class ComponentTracker:
    """Tracks performance metrics for a specific component"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.active_requests = 0
        self.last_reset = time.time()
        self.lock = threading.Lock()
    
    def start_request(self) -> 'RequestContext':
        """Start tracking a request"""
        with self.lock:
            self.active_requests += 1
        return RequestContext(self)
    
    def record_request(self, response_time_ms: float, success: bool = True):
        """Record a completed request"""
        with self.lock:
            self.request_count += 1
            self.total_response_time += response_time_ms
            if not success:
                self.error_count += 1
            if self.active_requests > 0:
                self.active_requests -= 1
    
    def get_current_metrics(self) -> ComponentMetrics:
        """Get current performance metrics"""
        with self.lock:
            current_time = time.time()
            time_window = current_time - self.last_reset
            
            # Calculate rates
            throughput = self.request_count / max(time_window, 1)
            avg_response_time = (self.total_response_time / max(self.request_count, 1))
            error_rate = (self.error_count / max(self.request_count, 1)) * 100
            
            return ComponentMetrics(
                component=self.component_name,
                response_time_ms=avg_response_time,
                throughput_per_second=throughput,
                error_rate_percent=error_rate,
                active_requests=self.active_requests,
                timestamp=datetime.now()
            )
    
    def reset_metrics(self):
        """Reset accumulated metrics"""
        with self.lock:
            self.request_count = 0
            self.error_count = 0
            self.total_response_time = 0.0
            self.last_reset = time.time()


class RequestContext:
    """Context manager for tracking individual requests"""
    
    def __init__(self, tracker: ComponentTracker):
        self.tracker = tracker
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            response_time_ms = (time.time() - self.start_time) * 1000
            self.success = exc_type is None
            self.tracker.record_request(response_time_ms, self.success)
    
    def mark_error(self):
        """Mark the request as failed"""
        self.success = False


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


if __name__ == "__main__":
    # Example usage
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Register a component
    tracker = monitor.register_component("test_component")
    
    # Simulate some requests
    for i in range(10):
        with tracker.start_request() as ctx:
            time.sleep(0.1)  # Simulate work
            if i % 5 == 0:
                ctx.mark_error()
    
    # Get performance summary
    summary = monitor.get_performance_summary(duration_minutes=1)
    print(json.dumps(summary, indent=2, default=str))
    
    monitor.stop_monitoring()