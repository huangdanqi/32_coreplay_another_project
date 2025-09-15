"""
Health check system for monitoring component status and system health.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time_ms: float
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_status: HealthStatus
    components: Dict[str, HealthCheckResult]
    timestamp: datetime
    uptime_seconds: float


class HealthChecker:
    """Central health checking system for all components"""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_checks: Dict[str, callable] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self.check_intervals: Dict[str, int] = {}  # seconds
        self.running = False
        
    def register_health_check(self, component: str, check_func: callable, interval: int = 30):
        """Register a health check function for a component"""
        self.health_checks[component] = check_func
        self.check_intervals[component] = interval
        logger.info(f"Registered health check for {component} with {interval}s interval")
        
    async def check_component_health(self, component: str) -> HealthCheckResult:
        """Check health of a specific component"""
        if component not in self.health_checks:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNKNOWN,
                message="No health check registered",
                timestamp=datetime.now(),
                response_time_ms=0.0
            )
            
        start_time = time.time()
        try:
            check_func = self.health_checks[component]
            
            # Run health check with timeout
            result = await asyncio.wait_for(
                self._run_check(check_func),
                timeout=10.0
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if result is True:
                status = HealthStatus.HEALTHY
                message = "Component is healthy"
            elif isinstance(result, dict):
                status = HealthStatus(result.get('status', 'healthy'))
                message = result.get('message', 'Component check completed')
            else:
                status = HealthStatus.DEGRADED
                message = str(result) if result else "Check returned unexpected result"
                
            return HealthCheckResult(
                component=component,
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=result if isinstance(result, dict) else None
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message="Health check timed out",
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Health check failed for {component}: {e}")
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _run_check(self, check_func):
        """Run a health check function (sync or async)"""
        if asyncio.iscoroutinefunction(check_func):
            return await check_func()
        else:
            return check_func()
    
    async def check_all_components(self) -> SystemHealth:
        """Check health of all registered components"""
        results = {}
        
        # Run all health checks concurrently
        tasks = []
        for component in self.health_checks.keys():
            task = asyncio.create_task(self.check_component_health(component))
            tasks.append((component, task))
        
        # Collect results
        for component, task in tasks:
            try:
                result = await task
                results[component] = result
                self.last_results[component] = result
            except Exception as e:
                logger.error(f"Failed to check {component}: {e}")
                results[component] = HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check execution failed: {str(e)}",
                    timestamp=datetime.now(),
                    response_time_ms=0.0
                )
        
        # Determine overall status
        overall_status = self._calculate_overall_status(results)
        
        return SystemHealth(
            overall_status=overall_status,
            components=results,
            timestamp=datetime.now(),
            uptime_seconds=time.time() - self.start_time
        )
    
    def _calculate_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Calculate overall system health from component results"""
        if not results:
            return HealthStatus.UNKNOWN
            
        statuses = [result.status for result in results.values()]
        
        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN
    
    def get_last_results(self) -> Dict[str, HealthCheckResult]:
        """Get the last health check results"""
        return self.last_results.copy()
    
    def get_component_status(self, component: str) -> Optional[HealthCheckResult]:
        """Get the last health check result for a specific component"""
        return self.last_results.get(component)
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        self.running = True
        logger.info("Started health monitoring")
        
        while self.running:
            try:
                # Check all components
                system_health = await self.check_all_components()
                
                # Log overall status
                logger.info(f"System health: {system_health.overall_status.value}")
                
                # Log unhealthy components
                for component, result in system_health.components.items():
                    if result.status != HealthStatus.HEALTHY:
                        logger.warning(f"{component}: {result.status.value} - {result.message}")
                
                # Wait before next check (use minimum interval)
                min_interval = min(self.check_intervals.values()) if self.check_intervals else 30
                await asyncio.sleep(min_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)
    
    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.running = False
        logger.info("Stopped health monitoring")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health checker state to dictionary"""
        return {
            'registered_components': list(self.health_checks.keys()),
            'check_intervals': self.check_intervals,
            'uptime_seconds': time.time() - self.start_time,
            'running': self.running,
            'last_results': {
                component: asdict(result) 
                for component, result in self.last_results.items()
            }
        }


# Component-specific health check functions
class ComponentHealthChecks:
    """Collection of health check functions for system components"""
    
    @staticmethod
    def llm_manager_health():
        """Health check for LLM Manager"""
        try:
            # Import here to avoid circular imports
            from diary_agent.core.llm_manager import LLMConfigManager
            
            # Check if LLM manager can be initialized
            manager = LLMConfigManager()
            
            # Check if at least one provider is configured
            if not manager.providers:
                return {
                    'status': 'unhealthy',
                    'message': 'No LLM providers configured'
                }
            
            # Check provider availability
            available_providers = 0
            for provider_name, provider in manager.providers.items():
                try:
                    # Simple connectivity check
                    if hasattr(provider, 'is_available') and provider.is_available():
                        available_providers += 1
                except:
                    pass
            
            if available_providers == 0:
                return {
                    'status': 'unhealthy',
                    'message': 'No LLM providers available'
                }
            elif available_providers < len(manager.providers):
                return {
                    'status': 'degraded',
                    'message': f'{available_providers}/{len(manager.providers)} providers available'
                }
            else:
                return {
                    'status': 'healthy',
                    'message': f'All {len(manager.providers)} providers available'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'LLM Manager check failed: {str(e)}'
            }
    
    @staticmethod
    def database_health():
        """Health check for database connectivity"""
        try:
            from diary_agent.integration.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Test database connection
            if db_manager.test_connection():
                return {
                    'status': 'healthy',
                    'message': 'Database connection successful'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Database connection failed'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database check failed: {str(e)}'
            }
    
    @staticmethod
    def sub_agent_manager_health():
        """Health check for Sub-Agent Manager"""
        try:
            from diary_agent.core.sub_agent_manager import SubAgentManager
            
            manager = SubAgentManager()
            
            # Check if agents are loaded
            if not manager.agents:
                return {
                    'status': 'degraded',
                    'message': 'No agents loaded'
                }
            
            # Check agent health
            healthy_agents = 0
            for agent_name, agent in manager.agents.items():
                try:
                    if hasattr(agent, 'is_healthy') and agent.is_healthy():
                        healthy_agents += 1
                except:
                    pass
            
            if healthy_agents == len(manager.agents):
                return {
                    'status': 'healthy',
                    'message': f'All {len(manager.agents)} agents healthy'
                }
            elif healthy_agents > 0:
                return {
                    'status': 'degraded',
                    'message': f'{healthy_agents}/{len(manager.agents)} agents healthy'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'No agents are healthy'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Sub-Agent Manager check failed: {str(e)}'
            }
    
    @staticmethod
    def config_manager_health():
        """Health check for Configuration Manager"""
        try:
            from diary_agent.core.config_manager import ConfigManager
            
            config_manager = ConfigManager()
            
            # Check if configurations are loaded
            if not config_manager.llm_config:
                return {
                    'status': 'unhealthy',
                    'message': 'LLM configuration not loaded'
                }
            
            if not config_manager.agent_prompts:
                return {
                    'status': 'degraded',
                    'message': 'Agent prompts not loaded'
                }
            
            return {
                'status': 'healthy',
                'message': 'All configurations loaded successfully'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Config Manager check failed: {str(e)}'
            }
    
    @staticmethod
    def event_router_health():
        """Health check for Event Router"""
        try:
            from diary_agent.core.event_router import EventRouter
            
            router = EventRouter()
            
            # Check if event mappings are loaded
            if not router.event_mappings:
                return {
                    'status': 'unhealthy',
                    'message': 'Event mappings not loaded'
                }
            
            return {
                'status': 'healthy',
                'message': f'Event router loaded with {len(router.event_mappings)} mappings'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Event Router check failed: {str(e)}'
            }    
    
    @staticmethod
    def daily_scheduler_health():
        """Health check for Daily Scheduler"""
        try:
            from diary_agent.core.daily_scheduler import DailyScheduler
            
            scheduler = DailyScheduler()
            
            # Check if scheduler is properly initialized
            if not hasattr(scheduler, 'diary_quota'):
                return {
                    'status': 'unhealthy',
                    'message': 'Daily scheduler not properly initialized'
                }
            
            return {
                'status': 'healthy',
                'message': 'Daily scheduler is operational'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Daily Scheduler check failed: {str(e)}'
            }


# Global health checker instance
health_checker = HealthChecker()


def setup_default_health_checks():
    """Setup default health checks for all system components"""
    health_checker.register_health_check(
        'llm_manager', 
        ComponentHealthChecks.llm_manager_health, 
        interval=60
    )
    
    health_checker.register_health_check(
        'database', 
        ComponentHealthChecks.database_health, 
        interval=30
    )
    
    health_checker.register_health_check(
        'sub_agent_manager', 
        ComponentHealthChecks.sub_agent_manager_health, 
        interval=45
    )
    
    health_checker.register_health_check(
        'config_manager', 
        ComponentHealthChecks.config_manager_health, 
        interval=120
    )
    
    health_checker.register_health_check(
        'event_router', 
        ComponentHealthChecks.event_router_health, 
        interval=60
    )
    
    health_checker.register_health_check(
        'daily_scheduler', 
        ComponentHealthChecks.daily_scheduler_health, 
        interval=90
    )
    
    logger.info("Default health checks configured")


if __name__ == "__main__":
    # Example usage
    async def main():
        setup_default_health_checks()
        
        # Run a single health check
        system_health = await health_checker.check_all_components()
        print(f"System Status: {system_health.overall_status.value}")
        
        for component, result in system_health.components.items():
            print(f"{component}: {result.status.value} - {result.message}")
    
    asyncio.run(main())