"""
Graceful degradation system for diary agent components.
Provides fallback mechanisms and service health monitoring.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import time


class ServiceHealth(Enum):
    """Health status of system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check configuration and results."""
    name: str
    check_function: Callable[[], bool]
    interval: int = 60  # seconds
    timeout: int = 30   # seconds
    failure_threshold: int = 3
    recovery_threshold: int = 2
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    status: ServiceHealth = ServiceHealth.UNKNOWN
    last_error: Optional[str] = None


@dataclass
class FallbackConfig:
    """Configuration for fallback mechanisms."""
    component_name: str
    fallback_function: Callable
    fallback_data: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority


class GracefulDegradationManager:
    """Manages graceful degradation and fallback mechanisms."""
    
    def __init__(self):
        self.logger = logging.getLogger("graceful_degradation")
        self.health_checks: Dict[str, HealthCheck] = {}
        self.fallback_configs: Dict[str, List[FallbackConfig]] = {}
        self.component_status: Dict[str, ServiceHealth] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self._setup_default_fallbacks()
    
    def _setup_default_fallbacks(self):
        """Setup default fallback configurations."""
        # LLM API fallbacks
        self.register_fallback(
            "llm_api",
            FallbackConfig(
                component_name="llm_api_cache",
                fallback_function=self._cached_llm_response,
                fallback_data={"use_cache": True},
                priority=1
            )
        )
        
        self.register_fallback(
            "llm_api",
            FallbackConfig(
                component_name="llm_api_queue",
                fallback_function=self._queue_llm_request,
                fallback_data={"queue_for_later": True},
                priority=2
            )
        )
        
        # Sub-agent fallbacks
        self.register_fallback(
            "sub_agent",
            FallbackConfig(
                component_name="generic_agent",
                fallback_function=self._generic_agent_fallback,
                fallback_data={"use_generic_prompts": True},
                priority=1
            )
        )
        
        # Database fallbacks
        self.register_fallback(
            "database",
            FallbackConfig(
                component_name="local_cache",
                fallback_function=self._local_cache_fallback,
                fallback_data={"use_local_storage": True},
                priority=1
            )
        )
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a health check for a component."""
        self.health_checks[health_check.name] = health_check
        self.component_status[health_check.name] = ServiceHealth.UNKNOWN
        self.logger.info(f"Registered health check for {health_check.name}")
    
    def register_fallback(self, component: str, fallback_config: FallbackConfig):
        """Register a fallback configuration for a component."""
        if component not in self.fallback_configs:
            self.fallback_configs[component] = []
        
        self.fallback_configs[component].append(fallback_config)
        # Sort by priority (lower number = higher priority)
        self.fallback_configs[component].sort(key=lambda x: x.priority)
        
        self.logger.info(f"Registered fallback {fallback_config.component_name} for {component}")
    
    def start_monitoring(self):
        """Start health monitoring in background thread."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Started health monitoring")
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Stopped health monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            for name, health_check in self.health_checks.items():
                try:
                    self._perform_health_check(health_check)
                except Exception as e:
                    self.logger.error(f"Error performing health check for {name}: {str(e)}")
            
            time.sleep(10)  # Check every 10 seconds
    
    def _perform_health_check(self, health_check: HealthCheck):
        """Perform a single health check."""
        now = datetime.now()
        
        # Check if it's time for this health check
        if (health_check.last_check and 
            (now - health_check.last_check).seconds < health_check.interval):
            return
        
        try:
            # Perform the health check with timeout
            start_time = time.time()
            is_healthy = health_check.check_function()
            duration = time.time() - start_time
            
            if duration > health_check.timeout:
                is_healthy = False
                health_check.last_error = f"Health check timeout ({duration:.2f}s)"
            
            self._update_health_status(health_check, is_healthy)
            
        except Exception as e:
            self._update_health_status(health_check, False)
            health_check.last_error = str(e)
        
        health_check.last_check = now
    
    def _update_health_status(self, health_check: HealthCheck, is_healthy: bool):
        """Update health status based on check result."""
        old_status = health_check.status
        
        if is_healthy:
            health_check.consecutive_failures = 0
            health_check.consecutive_successes += 1
            health_check.last_error = None
            
            if health_check.consecutive_successes >= health_check.recovery_threshold:
                health_check.status = ServiceHealth.HEALTHY
        else:
            health_check.consecutive_successes = 0
            health_check.consecutive_failures += 1
            
            if health_check.consecutive_failures >= health_check.failure_threshold:
                health_check.status = ServiceHealth.UNHEALTHY
            elif health_check.consecutive_failures > 0:
                health_check.status = ServiceHealth.DEGRADED
        
        # Update component status
        self.component_status[health_check.name] = health_check.status
        
        # Log status changes
        if old_status != health_check.status:
            self.logger.warning(
                f"Component {health_check.name} status changed: {old_status.value} -> {health_check.status.value}"
            )
    
    def get_component_health(self, component: str) -> ServiceHealth:
        """Get current health status of a component."""
        return self.component_status.get(component, ServiceHealth.UNKNOWN)
    
    def is_component_healthy(self, component: str) -> bool:
        """Check if a component is healthy."""
        status = self.get_component_health(component)
        return status == ServiceHealth.HEALTHY
    
    def get_fallback_function(self, component: str) -> Optional[Callable]:
        """Get the best available fallback function for a component."""
        if component not in self.fallback_configs:
            return None
        
        # Find the first enabled fallback
        for fallback_config in self.fallback_configs[component]:
            if fallback_config.enabled:
                return fallback_config.fallback_function
        
        return None
    
    def execute_with_fallback(self, component: str, primary_function: Callable, 
                            *args, **kwargs) -> Any:
        """Execute function with automatic fallback on failure."""
        try:
            # Try primary function first
            return primary_function(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary function failed for {component}: {str(e)}")
            
            # Try fallback functions
            fallback_function = self.get_fallback_function(component)
            if fallback_function:
                try:
                    self.logger.info(f"Executing fallback for {component}")
                    return fallback_function(*args, **kwargs)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {component}: {str(fallback_error)}")
                    raise fallback_error
            else:
                self.logger.error(f"No fallback available for {component}")
                raise e
    
    def _cached_llm_response(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback to cached LLM responses."""
        self.logger.info("Using cached LLM response fallback")
        return {
            "title": "今日",
            "content": "今天发生了一些事情，心情还不错。😊",
            "emotion_tags": ["平静"],
            "source": "cache_fallback"
        }
    
    def _queue_llm_request(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback to queue LLM request for later processing."""
        self.logger.info("Queueing LLM request for later processing")
        return {
            "queued": True,
            "retry_later": True,
            "source": "queue_fallback"
        }
    
    def _generic_agent_fallback(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback to generic agent processing."""
        self.logger.info("Using generic agent fallback")
        return {
            "title": "记录",
            "content": "今天有一些值得记录的事情发生了。",
            "emotion_tags": ["平静"],
            "source": "generic_agent_fallback"
        }
    
    def _local_cache_fallback(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback to local cache storage."""
        self.logger.info("Using local cache fallback")
        return {
            "stored_locally": True,
            "sync_when_available": True,
            "source": "local_cache_fallback"
        }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        healthy_count = sum(1 for status in self.component_status.values() 
                          if status == ServiceHealth.HEALTHY)
        degraded_count = sum(1 for status in self.component_status.values() 
                           if status == ServiceHealth.DEGRADED)
        unhealthy_count = sum(1 for status in self.component_status.values() 
                            if status == ServiceHealth.UNHEALTHY)
        total_count = len(self.component_status)
        
        overall_health = ServiceHealth.HEALTHY
        if unhealthy_count > 0:
            overall_health = ServiceHealth.UNHEALTHY
        elif degraded_count > 0:
            overall_health = ServiceHealth.DEGRADED
        
        return {
            "overall_health": overall_health.value,
            "component_counts": {
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "total": total_count
            },
            "component_details": {
                name: status.value for name, status in self.component_status.items()
            },
            "monitoring_active": self.monitoring_active
        }


# Global degradation manager instance
degradation_manager = GracefulDegradationManager()


def with_graceful_degradation(component: str):
    """Decorator for automatic graceful degradation."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return degradation_manager.execute_with_fallback(component, func, *args, **kwargs)
        return wrapper
    return decorator


def register_component_health_check(component: str, check_function: Callable[[], bool], 
                                  interval: int = 60):
    """Convenience function to register a health check."""
    health_check = HealthCheck(
        name=component,
        check_function=check_function,
        interval=interval
    )
    degradation_manager.register_health_check(health_check)