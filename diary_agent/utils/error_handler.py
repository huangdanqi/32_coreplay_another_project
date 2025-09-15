"""
Error handling utilities for the diary agent system.
Provides error categorization, recovery mechanisms, and circuit breaker patterns.
"""

import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from functools import wraps
import asyncio
from datetime import datetime, timedelta


class ErrorCategory(Enum):
    """Categories of errors that can occur in the diary agent system."""
    LLM_API_FAILURE = "llm_api_failure"
    SUB_AGENT_FAILURE = "sub_agent_failure"
    CONDITION_EVALUATION_ERROR = "condition_evaluation_error"
    DATA_VALIDATION_ERROR = "data_validation_error"
    DATABASE_ERROR = "database_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorContext:
    """Context information for error handling and recovery."""
    error_category: ErrorCategory
    error_message: str
    component_name: str
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CircuitBreakerState(Enum):
    """States for the circuit breaker pattern."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3  # for half-open state
    timeout: int = 30  # request timeout


class CircuitBreaker:
    """Circuit breaker implementation for LLM API calls."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger = logging.getLogger(f"circuit_breaker.{name}")
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} reset to CLOSED state")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class ErrorHandler:
    """Central error handling and recovery system."""
    
    def __init__(self):
        self.logger = logging.getLogger("error_handler")
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_counts: Dict[ErrorCategory, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default recovery strategies for each error category."""
        self.recovery_strategies = {
            ErrorCategory.LLM_API_FAILURE: self._handle_llm_api_failure,
            ErrorCategory.SUB_AGENT_FAILURE: self._handle_sub_agent_failure,
            ErrorCategory.CONDITION_EVALUATION_ERROR: self._handle_condition_error,
            ErrorCategory.DATA_VALIDATION_ERROR: self._handle_validation_error,
            ErrorCategory.DATABASE_ERROR: self._handle_database_error,
            ErrorCategory.CONFIGURATION_ERROR: self._handle_config_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.UNKNOWN_ERROR: self._handle_unknown_error,
        }
    
    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None):
        """Register a circuit breaker for a component."""
        if config is None:
            config = CircuitBreakerConfig()
        self.circuit_breakers[name] = CircuitBreaker(name, config)
        self.logger.info(f"Registered circuit breaker for {name}")
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get circuit breaker by name."""
        if name not in self.circuit_breakers:
            self.register_circuit_breaker(name)
        return self.circuit_breakers[name]
    
    def handle_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle error with appropriate recovery strategy."""
        self.logger.error(
            f"Error in {context.component_name}: {context.error_message}",
            extra={
                "category": context.error_category.value,
                "component": context.component_name,
                "retry_count": context.retry_count,
                "metadata": context.metadata
            }
        )
        
        # Update error counts
        self.error_counts[context.error_category] = self.error_counts.get(context.error_category, 0) + 1
        
        # Apply recovery strategy
        recovery_func = self.recovery_strategies.get(context.error_category, self._handle_unknown_error)
        return recovery_func(error, context)
    
    def _handle_llm_api_failure(self, error: Exception, context: ErrorContext) -> Any:
        """Handle LLM API failures with failover and retry logic."""
        self.logger.warning(f"LLM API failure in {context.component_name}: {str(error)}")
        
        if context.retry_count < context.max_retries:
            # Exponential backoff
            wait_time = 2 ** context.retry_count
            self.logger.info(f"Retrying LLM API call in {wait_time} seconds (attempt {context.retry_count + 1})")
            time.sleep(wait_time)
            return {"retry": True, "wait_time": wait_time}
        else:
            self.logger.error(f"LLM API failure exceeded max retries for {context.component_name}")
            return {"retry": False, "fallback": "queue_for_later"}
    
    def _handle_sub_agent_failure(self, error: Exception, context: ErrorContext) -> Any:
        """Handle sub-agent failures with fallback mechanisms."""
        self.logger.warning(f"Sub-agent failure in {context.component_name}: {str(error)}")
        
        return {
            "retry": context.retry_count < context.max_retries,
            "fallback_agent": "generic_agent",
            "continue_processing": True
        }
    
    def _handle_condition_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle condition evaluation errors."""
        self.logger.warning(f"Condition evaluation error: {str(error)}")
        
        return {
            "use_default_conditions": True,
            "continue_monitoring": True,
            "alert_admin": True
        }
    
    def _handle_validation_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle data validation errors."""
        self.logger.warning(f"Data validation error in {context.component_name}: {str(error)}")
        
        return {
            "sanitize_data": True,
            "use_default_format": True,
            "log_malformed_data": True
        }
    
    def _handle_database_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle database connection and operation errors."""
        self.logger.error(f"Database error in {context.component_name}: {str(error)}")
        
        return {
            "retry": context.retry_count < context.max_retries,
            "use_cache": True,
            "queue_operation": True
        }
    
    def _handle_config_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle configuration errors."""
        self.logger.error(f"Configuration error in {context.component_name}: {str(error)}")
        
        return {
            "use_default_config": True,
            "reload_config": True,
            "alert_admin": True
        }
    
    def _handle_network_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle network connectivity errors."""
        self.logger.warning(f"Network error in {context.component_name}: {str(error)}")
        
        return {
            "retry": context.retry_count < context.max_retries,
            "use_cache": True,
            "check_connectivity": True
        }
    
    def _handle_unknown_error(self, error: Exception, context: ErrorContext) -> Any:
        """Handle unknown errors with generic recovery."""
        self.logger.error(f"Unknown error in {context.component_name}: {str(error)}")
        
        return {
            "retry": context.retry_count < 1,  # Only retry once for unknown errors
            "continue_processing": True,
            "alert_admin": True
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        circuit_breaker_states = {
            name: breaker.state.value 
            for name, breaker in self.circuit_breakers.items()
        }
        
        return {
            "error_counts": {cat.value: count for cat, count in self.error_counts.items()},
            "circuit_breaker_states": circuit_breaker_states,
            "total_errors": sum(self.error_counts.values())
        }


def with_error_handling(error_category: ErrorCategory, component_name: str, max_retries: int = 3):
    """Decorator for automatic error handling."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    context = ErrorContext(
                        error_category=error_category,
                        error_message=str(e),
                        component_name=component_name,
                        timestamp=datetime.now(),
                        retry_count=retry_count,
                        max_retries=max_retries
                    )
                    
                    recovery_result = error_handler.handle_error(e, context)
                    
                    if not recovery_result.get("retry", False):
                        raise e
                    
                    retry_count += 1
                    if "wait_time" in recovery_result:
                        time.sleep(recovery_result["wait_time"])
            
            raise Exception(f"Max retries exceeded for {component_name}")
        
        return wrapper
    return decorator


# Global error handler instance
global_error_handler = ErrorHandler()