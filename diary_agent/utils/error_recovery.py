"""
Comprehensive error recovery system for the diary agent.
Integrates error handling, circuit breakers, graceful degradation, and monitoring.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .error_handler import (
    ErrorHandler, ErrorCategory, ErrorContext, CircuitBreakerConfig,
    global_error_handler
)
from .graceful_degradation import (
    GracefulDegradationManager, ServiceHealth, HealthCheck, FallbackConfig,
    degradation_manager
)
from .monitoring import (
    PerformanceMonitor, AlertManager, performance_monitor, alert_manager
)
from .logger import get_component_logger, diary_logger


class RecoveryStrategy(Enum):
    """Recovery strategies for different error scenarios."""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FAILOVER_TO_BACKUP = "failover_to_backup"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"
    QUEUE_FOR_LATER = "queue_for_later"
    USE_CACHED_RESPONSE = "use_cached_response"
    ALERT_AND_CONTINUE = "alert_and_continue"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


@dataclass
class RecoveryPlan:
    """Recovery plan for a specific error scenario."""
    error_category: ErrorCategory
    component: str
    strategies: List[RecoveryStrategy]
    max_attempts: int = 3
    escalation_threshold: int = 5
    cooldown_period: int = 300  # seconds
    metadata: Dict[str, Any] = None


class ErrorRecoveryOrchestrator:
    """Orchestrates error recovery across all system components."""
    
    def __init__(self):
        self.logger = get_component_logger("error_recovery")
        self.error_handler = global_error_handler
        self.degradation_manager = degradation_manager
        self.performance_monitor = performance_monitor
        self.alert_manager = alert_manager
        
        # Recovery plans for different scenarios
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self._setup_default_recovery_plans()
        
        # Track recovery attempts
        self.recovery_attempts: Dict[str, List[datetime]] = {}
        self.component_health_cache: Dict[str, ServiceHealth] = {}
        
    def _setup_default_recovery_plans(self):
        """Setup default recovery plans for common error scenarios."""
        
        # LLM API failure recovery
        self.recovery_plans["llm_api_failure"] = RecoveryPlan(
            error_category=ErrorCategory.LLM_API_FAILURE,
            component="llm_manager",
            strategies=[
                RecoveryStrategy.CIRCUIT_BREAKER,
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                RecoveryStrategy.FAILOVER_TO_BACKUP,
                RecoveryStrategy.USE_CACHED_RESPONSE,
                RecoveryStrategy.QUEUE_FOR_LATER
            ],
            max_attempts=3,
            escalation_threshold=5
        )
        
        # Sub-agent failure recovery
        self.recovery_plans["sub_agent_failure"] = RecoveryPlan(
            error_category=ErrorCategory.SUB_AGENT_FAILURE,
            component="sub_agent",
            strategies=[
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                RecoveryStrategy.FAILOVER_TO_BACKUP,
                RecoveryStrategy.ALERT_AND_CONTINUE
            ],
            max_attempts=2,
            escalation_threshold=3
        )
        
        # Database error recovery
        self.recovery_plans["database_error"] = RecoveryPlan(
            error_category=ErrorCategory.DATABASE_ERROR,
            component="database",
            strategies=[
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                RecoveryStrategy.USE_CACHED_RESPONSE,
                RecoveryStrategy.QUEUE_FOR_LATER,
                RecoveryStrategy.ALERT_AND_CONTINUE
            ],
            max_attempts=3,
            escalation_threshold=5
        )
        
        # Configuration error recovery
        self.recovery_plans["config_error"] = RecoveryPlan(
            error_category=ErrorCategory.CONFIGURATION_ERROR,
            component="config_manager",
            strategies=[
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                RecoveryStrategy.USE_CACHED_RESPONSE,
                RecoveryStrategy.ALERT_AND_CONTINUE
            ],
            max_attempts=1,
            escalation_threshold=2
        )
        
        # Network error recovery
        self.recovery_plans["network_error"] = RecoveryPlan(
            error_category=ErrorCategory.NETWORK_ERROR,
            component="network",
            strategies=[
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                RecoveryStrategy.USE_CACHED_RESPONSE,
                RecoveryStrategy.QUEUE_FOR_LATER,
                RecoveryStrategy.ALERT_AND_CONTINUE
            ],
            max_attempts=3,
            escalation_threshold=5
        )
    
    async def handle_error_with_recovery(self, error: Exception, context: ErrorContext) -> Any:
        """Handle error with comprehensive recovery strategy."""
        recovery_key = f"{context.error_category.value}_{context.component_name}"
        
        # Log the error
        self.logger.error(
            f"Error in {context.component_name}: {context.error_message}",
            extra={
                "error_category": context.error_category.value,
                "component": context.component_name,
                "retry_count": context.retry_count
            }
        )
        
        # Track recovery attempts
        self._track_recovery_attempt(recovery_key)
        
        # Check if we should escalate
        if self._should_escalate(recovery_key):
            return await self._escalate_error(error, context)
        
        # Get recovery plan
        recovery_plan = self._get_recovery_plan(context)
        if not recovery_plan:
            return await self._default_error_handling(error, context)
        
        # Execute recovery strategies
        for strategy in recovery_plan.strategies:
            try:
                result = await self._execute_recovery_strategy(strategy, error, context, recovery_plan)
                if result and result.get("success", False):
                    self.logger.info(f"Recovery successful using strategy: {strategy.value}")
                    return result
            except Exception as recovery_error:
                self.logger.warning(f"Recovery strategy {strategy.value} failed: {str(recovery_error)}")
                continue
        
        # If all strategies failed, escalate
        return await self._escalate_error(error, context)
    
    def _get_recovery_plan(self, context: ErrorContext) -> Optional[RecoveryPlan]:
        """Get appropriate recovery plan for the error context."""
        # Try exact match first
        exact_key = f"{context.error_category.value}_{context.component_name}"
        if exact_key in self.recovery_plans:
            return self.recovery_plans[exact_key]
        
        # Try category match
        category_key = context.error_category.value
        if category_key in self.recovery_plans:
            return self.recovery_plans[category_key]
        
        # Try component-specific plans
        for plan_key, plan in self.recovery_plans.items():
            if plan.component == context.component_name:
                return plan
        
        return None
    
    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy, error: Exception,
                                       context: ErrorContext, plan: RecoveryPlan) -> Dict[str, Any]:
        """Execute a specific recovery strategy."""
        
        if strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return await self._retry_with_backoff(error, context, plan)
        
        elif strategy == RecoveryStrategy.FAILOVER_TO_BACKUP:
            return await self._failover_to_backup(error, context, plan)
        
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._graceful_degradation(error, context, plan)
        
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            return await self._circuit_breaker_recovery(error, context, plan)
        
        elif strategy == RecoveryStrategy.QUEUE_FOR_LATER:
            return await self._queue_for_later(error, context, plan)
        
        elif strategy == RecoveryStrategy.USE_CACHED_RESPONSE:
            return await self._use_cached_response(error, context, plan)
        
        elif strategy == RecoveryStrategy.ALERT_AND_CONTINUE:
            return await self._alert_and_continue(error, context, plan)
        
        elif strategy == RecoveryStrategy.EMERGENCY_SHUTDOWN:
            return await self._emergency_shutdown(error, context, plan)
        
        else:
            self.logger.warning(f"Unknown recovery strategy: {strategy.value}")
            return {"success": False, "reason": "unknown_strategy"}
    
    async def _retry_with_backoff(self, error: Exception, context: ErrorContext, 
                                plan: RecoveryPlan) -> Dict[str, Any]:
        """Implement retry with exponential backoff."""
        if context.retry_count >= plan.max_attempts:
            return {"success": False, "reason": "max_retries_exceeded"}
        
        # Calculate backoff delay
        delay = min(2 ** context.retry_count, 60)  # Max 60 seconds
        
        self.logger.info(f"Retrying {context.component_name} in {delay} seconds (attempt {context.retry_count + 1})")
        
        await asyncio.sleep(delay)
        
        return {
            "success": True,
            "action": "retry",
            "delay": delay,
            "attempt": context.retry_count + 1
        }
    
    async def _failover_to_backup(self, error: Exception, context: ErrorContext,
                                plan: RecoveryPlan) -> Dict[str, Any]:
        """Implement failover to backup systems."""
        self.logger.info(f"Attempting failover for {context.component_name}")
        
        # Use graceful degradation manager to find fallback
        fallback_function = self.degradation_manager.get_fallback_function(context.component_name)
        
        if fallback_function:
            try:
                result = await self._execute_fallback(fallback_function, context)
                return {
                    "success": True,
                    "action": "failover",
                    "result": result
                }
            except Exception as fallback_error:
                self.logger.error(f"Failover failed: {str(fallback_error)}")
                return {"success": False, "reason": "failover_failed"}
        
        return {"success": False, "reason": "no_fallback_available"}
    
    async def _graceful_degradation(self, error: Exception, context: ErrorContext,
                                  plan: RecoveryPlan) -> Dict[str, Any]:
        """Implement graceful degradation."""
        self.logger.info(f"Applying graceful degradation for {context.component_name}")
        
        # Mark component as degraded
        self.degradation_manager.component_status[context.component_name] = ServiceHealth.DEGRADED
        
        # Use fallback functionality
        fallback_function = self.degradation_manager.get_fallback_function(context.component_name)
        if fallback_function:
            try:
                result = await self._execute_fallback(fallback_function, context)
                return {
                    "success": True,
                    "action": "graceful_degradation",
                    "result": result
                }
            except Exception as fallback_error:
                self.logger.error(f"Graceful degradation failed: {str(fallback_error)}")
        
        return {"success": False, "reason": "degradation_failed"}
    
    async def _circuit_breaker_recovery(self, error: Exception, context: ErrorContext,
                                      plan: RecoveryPlan) -> Dict[str, Any]:
        """Implement circuit breaker recovery."""
        circuit_breaker = self.error_handler.get_circuit_breaker(context.component_name)
        
        # Circuit breaker logic is handled in the error handler
        # This strategy focuses on recovery actions when circuit is open
        
        if circuit_breaker.state.value == "open":
            self.logger.info(f"Circuit breaker open for {context.component_name}, using fallback")
            
            fallback_function = self.degradation_manager.get_fallback_function(context.component_name)
            if fallback_function:
                try:
                    result = await self._execute_fallback(fallback_function, context)
                    return {
                        "success": True,
                        "action": "circuit_breaker_fallback",
                        "result": result
                    }
                except Exception as fallback_error:
                    self.logger.error(f"Circuit breaker fallback failed: {str(fallback_error)}")
        
        return {"success": False, "reason": "circuit_breaker_open"}
    
    async def _queue_for_later(self, error: Exception, context: ErrorContext,
                             plan: RecoveryPlan) -> Dict[str, Any]:
        """Queue operation for later processing."""
        self.logger.info(f"Queueing operation for later: {context.component_name}")
        
        # In a real implementation, this would add to a persistent queue
        # For now, we'll simulate by logging the action
        
        return {
            "success": True,
            "action": "queued",
            "retry_after": datetime.now() + timedelta(minutes=5)
        }
    
    async def _use_cached_response(self, error: Exception, context: ErrorContext,
                                 plan: RecoveryPlan) -> Dict[str, Any]:
        """Use cached response as fallback."""
        self.logger.info(f"Using cached response for {context.component_name}")
        
        # Simulate cached response based on component type
        cached_responses = {
            "llm_manager": {
                "title": "今日",
                "content": "今天发生了一些事情，心情还不错。😊",
                "emotion_tags": ["平静"],
                "source": "cache"
            },
            "sub_agent": {
                "title": "记录",
                "content": "今天有值得记录的事情发生了。",
                "emotion_tags": ["平静"],
                "source": "cache"
            }
        }
        
        cached_response = cached_responses.get(context.component_name, {
            "message": "Cached response not available",
            "source": "cache"
        })
        
        return {
            "success": True,
            "action": "cached_response",
            "result": cached_response
        }
    
    async def _alert_and_continue(self, error: Exception, context: ErrorContext,
                                plan: RecoveryPlan) -> Dict[str, Any]:
        """Create alert and continue processing."""
        self.logger.info(f"Creating alert and continuing for {context.component_name}")
        
        # Create alert
        alert_id = f"{context.component_name}_{context.error_category.value}_{int(datetime.now().timestamp())}"
        self.alert_manager.create_alert(
            alert_id=alert_id,
            severity="medium",
            component=context.component_name,
            message=f"Error in {context.component_name}: {context.error_message}",
            metadata=context.metadata or {}
        )
        
        return {
            "success": True,
            "action": "alert_created",
            "alert_id": alert_id,
            "continue_processing": True
        }
    
    async def _emergency_shutdown(self, error: Exception, context: ErrorContext,
                                plan: RecoveryPlan) -> Dict[str, Any]:
        """Perform emergency shutdown of component."""
        self.logger.critical(f"Emergency shutdown initiated for {context.component_name}")
        
        # Create critical alert
        alert_id = f"emergency_{context.component_name}_{int(datetime.now().timestamp())}"
        self.alert_manager.create_alert(
            alert_id=alert_id,
            severity="critical",
            component=context.component_name,
            message=f"Emergency shutdown: {context.error_message}",
            metadata=context.metadata or {}
        )
        
        # Mark component as unhealthy
        self.degradation_manager.component_status[context.component_name] = ServiceHealth.UNHEALTHY
        
        return {
            "success": True,
            "action": "emergency_shutdown",
            "alert_id": alert_id,
            "component_shutdown": True
        }
    
    async def _execute_fallback(self, fallback_function: Callable, context: ErrorContext) -> Any:
        """Execute fallback function safely."""
        try:
            if asyncio.iscoroutinefunction(fallback_function):
                return await fallback_function()
            else:
                return fallback_function()
        except Exception as e:
            self.logger.error(f"Fallback function failed: {str(e)}")
            raise
    
    def _track_recovery_attempt(self, recovery_key: str):
        """Track recovery attempts for escalation logic."""
        now = datetime.now()
        
        if recovery_key not in self.recovery_attempts:
            self.recovery_attempts[recovery_key] = []
        
        # Add current attempt
        self.recovery_attempts[recovery_key].append(now)
        
        # Clean up old attempts (older than 1 hour)
        cutoff_time = now - timedelta(hours=1)
        self.recovery_attempts[recovery_key] = [
            attempt for attempt in self.recovery_attempts[recovery_key]
            if attempt > cutoff_time
        ]
    
    def _should_escalate(self, recovery_key: str) -> bool:
        """Check if error should be escalated based on frequency."""
        if recovery_key not in self.recovery_attempts:
            return False
        
        # Get recovery plan to check escalation threshold
        plan = None
        for plan_key, recovery_plan in self.recovery_plans.items():
            if plan_key in recovery_key:
                plan = recovery_plan
                break
        
        if not plan:
            return len(self.recovery_attempts[recovery_key]) >= 5  # Default threshold
        
        return len(self.recovery_attempts[recovery_key]) >= plan.escalation_threshold
    
    async def _escalate_error(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Escalate error to higher level handling."""
        self.logger.critical(f"Escalating error for {context.component_name}: {context.error_message}")
        
        # Create critical alert
        alert_id = f"escalated_{context.component_name}_{int(datetime.now().timestamp())}"
        self.alert_manager.create_alert(
            alert_id=alert_id,
            severity="critical",
            component=context.component_name,
            message=f"Escalated error: {context.error_message}",
            metadata={
                "error_category": context.error_category.value,
                "retry_count": context.retry_count,
                "escalation_reason": "max_recovery_attempts_exceeded"
            }
        )
        
        return {
            "success": False,
            "action": "escalated",
            "alert_id": alert_id,
            "requires_manual_intervention": True
        }
    
    async def _default_error_handling(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Default error handling when no specific plan exists."""
        self.logger.warning(f"No recovery plan found for {context.component_name}, using default handling")
        
        # Use basic error handler
        result = self.error_handler.handle_error(error, context)
        
        return {
            "success": result.get("retry", False),
            "action": "default_handling",
            "result": result
        }
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status."""
        return {
            "recovery_plans": len(self.recovery_plans),
            "active_recovery_attempts": {
                key: len(attempts) for key, attempts in self.recovery_attempts.items()
            },
            "component_health": {
                component: health.value 
                for component, health in self.component_health_cache.items()
            }
        }


# Global error recovery orchestrator
error_recovery_orchestrator = ErrorRecoveryOrchestrator()


async def handle_error_with_recovery(error: Exception, context: ErrorContext) -> Any:
    """Convenience function for error recovery."""
    return await error_recovery_orchestrator.handle_error_with_recovery(error, context)


def register_recovery_plan(plan_key: str, recovery_plan: RecoveryPlan):
    """Register a custom recovery plan."""
    error_recovery_orchestrator.recovery_plans[plan_key] = recovery_plan