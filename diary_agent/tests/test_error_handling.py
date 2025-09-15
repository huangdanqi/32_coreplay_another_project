"""
Unit tests for error handling and recovery mechanisms.
Tests error categorization, circuit breaker patterns, and graceful degradation.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from diary_agent.utils.error_handler import (
    ErrorHandler, ErrorCategory, ErrorContext, CircuitBreaker, 
    CircuitBreakerConfig, CircuitBreakerState, CircuitBreakerOpenError,
    with_error_handling, global_error_handler
)
from diary_agent.utils.graceful_degradation import (
    GracefulDegradationManager, ServiceHealth, HealthCheck, FallbackConfig,
    with_graceful_degradation, register_component_health_check
)
from diary_agent.utils.logger import DiaryAgentLogger, get_component_logger


class TestErrorHandler:
    """Test cases for ErrorHandler class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.error_handler = ErrorHandler()
    
    def test_error_categorization(self):
        """Test error categorization and handling."""
        # Test LLM API failure
        context = ErrorContext(
            error_category=ErrorCategory.LLM_API_FAILURE,
            error_message="API timeout",
            component_name="llm_manager",
            timestamp=datetime.now()
        )
        
        result = self.error_handler.handle_error(Exception("API timeout"), context)
        assert result["retry"] == True
        assert "wait_time" in result
    
    def test_sub_agent_failure_handling(self):
        """Test sub-agent failure recovery."""
        context = ErrorContext(
            error_category=ErrorCategory.SUB_AGENT_FAILURE,
            error_message="Agent crashed",
            component_name="weather_agent",
            timestamp=datetime.now()
        )
        
        result = self.error_handler.handle_error(Exception("Agent crashed"), context)
        assert result["fallback_agent"] == "generic_agent"
        assert result["continue_processing"] == True
    
    def test_data_validation_error_handling(self):
        """Test data validation error recovery."""
        context = ErrorContext(
            error_category=ErrorCategory.DATA_VALIDATION_ERROR,
            error_message="Invalid format",
            component_name="diary_generator",
            timestamp=datetime.now()
        )
        
        result = self.error_handler.handle_error(Exception("Invalid format"), context)
        assert result["sanitize_data"] == True
        assert result["use_default_format"] == True
    
    def test_error_statistics(self):
        """Test error statistics collection."""
        # Generate some errors
        for i in range(3):
            context = ErrorContext(
                error_category=ErrorCategory.LLM_API_FAILURE,
                error_message=f"Error {i}",
                component_name="test",
                timestamp=datetime.now()
            )
            self.error_handler.handle_error(Exception(f"Error {i}"), context)
        
        stats = self.error_handler.get_error_statistics()
        assert stats["error_counts"]["llm_api_failure"] == 3
        assert stats["total_errors"] == 3


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1,
            success_threshold=1
        )
        self.circuit_breaker = CircuitBreaker("test_breaker", self.config)
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        def success_func():
            return "success"
        
        result = self.circuit_breaker.call(success_func)
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        def failing_func():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception):
            self.circuit_breaker.call(failing_func)
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
        
        # Second failure should open the circuit
        with pytest.raises(Exception):
            self.circuit_breaker.call(failing_func)
        assert self.circuit_breaker.state == CircuitBreakerState.OPEN
    
    def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects calls when open."""
        # Force circuit to open
        self.circuit_breaker.state = CircuitBreakerState.OPEN
        self.circuit_breaker.failure_count = self.config.failure_threshold
        self.circuit_breaker.last_failure_time = datetime.now()
        
        def test_func():
            return "should not execute"
        
        with pytest.raises(CircuitBreakerOpenError):
            self.circuit_breaker.call(test_func)
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        # Force circuit to open
        self.circuit_breaker.state = CircuitBreakerState.OPEN
        self.circuit_breaker.failure_count = self.config.failure_threshold
        self.circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=2)
        
        def success_func():
            return "success"
        
        # Should move to half-open and then closed on success
        result = self.circuit_breaker.call(success_func)
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED


class TestGracefulDegradation:
    """Test cases for GracefulDegradationManager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.degradation_manager = GracefulDegradationManager()
    
    def test_health_check_registration(self):
        """Test health check registration."""
        def test_health_check():
            return True
        
        health_check = HealthCheck(
            name="test_component",
            check_function=test_health_check,
            interval=60
        )
        
        self.degradation_manager.register_health_check(health_check)
        assert "test_component" in self.degradation_manager.health_checks
    
    def test_fallback_registration(self):
        """Test fallback configuration registration."""
        def test_fallback():
            return {"fallback": True}
        
        fallback_config = FallbackConfig(
            component_name="test_fallback",
            fallback_function=test_fallback,
            priority=1
        )
        
        self.degradation_manager.register_fallback("test_component", fallback_config)
        assert "test_component" in self.degradation_manager.fallback_configs
    
    def test_execute_with_fallback_success(self):
        """Test successful execution without fallback."""
        def primary_function():
            return "primary_success"
        
        result = self.degradation_manager.execute_with_fallback(
            "test_component", 
            primary_function
        )
        assert result == "primary_success"
    
    def test_execute_with_fallback_failure(self):
        """Test fallback execution on primary failure."""
        def primary_function():
            raise Exception("Primary failed")
        
        def fallback_function():
            return "fallback_success"
        
        fallback_config = FallbackConfig(
            component_name="test_fallback",
            fallback_function=fallback_function,
            priority=1
        )
        
        self.degradation_manager.register_fallback("test_component", fallback_config)
        
        result = self.degradation_manager.execute_with_fallback(
            "test_component",
            primary_function
        )
        assert result == "fallback_success"
    
    def test_system_health_summary(self):
        """Test system health summary generation."""
        # Add some components with different health states
        self.degradation_manager.component_status["healthy_component"] = ServiceHealth.HEALTHY
        self.degradation_manager.component_status["degraded_component"] = ServiceHealth.DEGRADED
        self.degradation_manager.component_status["unhealthy_component"] = ServiceHealth.UNHEALTHY
        
        summary = self.degradation_manager.get_system_health_summary()
        
        assert summary["component_counts"]["healthy"] == 1
        assert summary["component_counts"]["degraded"] == 1
        assert summary["component_counts"]["unhealthy"] == 1
        assert summary["overall_health"] == "unhealthy"  # Due to unhealthy component


class TestErrorHandlingDecorators:
    """Test cases for error handling decorators."""
    
    def test_with_error_handling_decorator(self):
        """Test with_error_handling decorator."""
        @with_error_handling(ErrorCategory.SUB_AGENT_FAILURE, "test_component")
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_with_error_handling_decorator_retry(self):
        """Test with_error_handling decorator with retry."""
        call_count = 0
        
        @with_error_handling(ErrorCategory.SUB_AGENT_FAILURE, "test_component", max_retries=2)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success_after_retry"
        
        result = test_function()
        assert result == "success_after_retry"
        assert call_count == 2
    
    def test_with_graceful_degradation_decorator(self):
        """Test with_graceful_degradation decorator."""
        @with_graceful_degradation("test_component")
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"


class TestLoggingIntegration:
    """Test cases for logging integration with error handling."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.logger = DiaryAgentLogger(log_dir="test_logs")
    
    def test_component_logger_creation(self):
        """Test component logger creation."""
        logger = get_component_logger("test_component")
        assert logger is not None
    
    def test_error_logging(self):
        """Test error logging functionality."""
        logger = self.logger.get_error_logger()
        
        # Test that logging doesn't raise exceptions
        logger.error("Test error message")
        logger.warning("Test warning message")
        logger.info("Test info message")
    
    def test_performance_logging(self):
        """Test performance metrics logging."""
        logger = self.logger.get_performance_logger()
        
        # Test performance logging
        logger.info(
            "Test operation completed",
            extra={
                "component": "test_component",
                "operation": "test_operation",
                "duration": 1.5
            }
        )
    
    def test_audit_logging(self):
        """Test audit logging functionality."""
        logger = self.logger.get_audit_logger()
        
        # Test audit logging
        logger.info(
            "Test event processed",
            extra={
                "event_type": "test_event",
                "user_id": 123,
                "agent_type": "test_agent"
            }
        )


@pytest.mark.asyncio
class TestAsyncErrorHandling:
    """Test cases for async error handling scenarios."""
    
    async def test_async_circuit_breaker(self):
        """Test circuit breaker with async functions."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        circuit_breaker = CircuitBreaker("async_test", config)
        
        async def async_success():
            await asyncio.sleep(0.1)
            return "async_success"
        
        result = circuit_breaker.call(asyncio.create_task, async_success())
        final_result = await result
        assert final_result == "async_success"
    
    async def test_async_error_recovery(self):
        """Test async error recovery mechanisms."""
        call_count = 0
        
        async def async_function_with_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Async failure")
            return "async_success_after_retry"
        
        # Simulate retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await async_function_with_retry()
                assert result == "async_success_after_retry"
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(0.1)


class TestIntegrationScenarios:
    """Integration test scenarios for error handling system."""
    
    def test_end_to_end_error_recovery(self):
        """Test complete error recovery workflow."""
        error_handler = ErrorHandler()
        degradation_manager = GracefulDegradationManager()
        
        # Register circuit breaker
        error_handler.register_circuit_breaker("integration_test")
        
        # Register fallback
        def fallback_function():
            return {"fallback": True}
        
        fallback_config = FallbackConfig(
            component_name="integration_fallback",
            fallback_function=fallback_function
        )
        degradation_manager.register_fallback("integration_test", fallback_config)
        
        # Test primary function failure with fallback
        def failing_primary():
            raise Exception("Primary function failed")
        
        result = degradation_manager.execute_with_fallback(
            "integration_test",
            failing_primary
        )
        
        assert result["fallback"] == True
    
    def test_multiple_component_failure_scenario(self):
        """Test scenario with multiple component failures."""
        degradation_manager = GracefulDegradationManager()
        
        # Simulate multiple component failures
        degradation_manager.component_status["llm_api"] = ServiceHealth.UNHEALTHY
        degradation_manager.component_status["database"] = ServiceHealth.DEGRADED
        degradation_manager.component_status["sub_agent"] = ServiceHealth.HEALTHY
        
        summary = degradation_manager.get_system_health_summary()
        
        # System should be unhealthy due to critical component failure
        assert summary["overall_health"] == "unhealthy"
        assert summary["component_counts"]["unhealthy"] == 1
        assert summary["component_counts"]["degraded"] == 1
        assert summary["component_counts"]["healthy"] == 1


class TestErrorRecoveryOrchestrator:
    """Test cases for ErrorRecoveryOrchestrator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        from diary_agent.utils.error_recovery import ErrorRecoveryOrchestrator, RecoveryStrategy, RecoveryPlan
        self.orchestrator = ErrorRecoveryOrchestrator()
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_strategy(self):
        """Test retry with backoff recovery strategy."""
        from diary_agent.utils.error_recovery import RecoveryStrategy, RecoveryPlan
        
        context = ErrorContext(
            error_category=ErrorCategory.LLM_API_FAILURE,
            error_message="API timeout",
            component_name="llm_manager",
            timestamp=datetime.now(),
            retry_count=0
        )
        
        plan = RecoveryPlan(
            error_category=ErrorCategory.LLM_API_FAILURE,
            component="llm_manager",
            strategies=[RecoveryStrategy.RETRY_WITH_BACKOFF],
            max_attempts=3
        )
        
        result = await self.orchestrator._execute_recovery_strategy(
            RecoveryStrategy.RETRY_WITH_BACKOFF,
            Exception("Test error"),
            context,
            plan
        )
        
        assert result["success"] == True
        assert result["action"] == "retry"
        assert "delay" in result
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_strategy(self):
        """Test graceful degradation recovery strategy."""
        from diary_agent.utils.error_recovery import RecoveryStrategy, RecoveryPlan
        
        context = ErrorContext(
            error_category=ErrorCategory.SUB_AGENT_FAILURE,
            error_message="Agent crashed",
            component_name="weather_agent",
            timestamp=datetime.now()
        )
        
        plan = RecoveryPlan(
            error_category=ErrorCategory.SUB_AGENT_FAILURE,
            component="weather_agent",
            strategies=[RecoveryStrategy.GRACEFUL_DEGRADATION]
        )
        
        result = await self.orchestrator._execute_recovery_strategy(
            RecoveryStrategy.GRACEFUL_DEGRADATION,
            Exception("Test error"),
            context,
            plan
        )
        
        # Should succeed even without registered fallback (uses default)
        assert "action" in result
    
    @pytest.mark.asyncio
    async def test_cached_response_strategy(self):
        """Test cached response recovery strategy."""
        from diary_agent.utils.error_recovery import RecoveryStrategy, RecoveryPlan
        
        context = ErrorContext(
            error_category=ErrorCategory.LLM_API_FAILURE,
            error_message="API unavailable",
            component_name="llm_manager",
            timestamp=datetime.now()
        )
        
        plan = RecoveryPlan(
            error_category=ErrorCategory.LLM_API_FAILURE,
            component="llm_manager",
            strategies=[RecoveryStrategy.USE_CACHED_RESPONSE]
        )
        
        result = await self.orchestrator._execute_recovery_strategy(
            RecoveryStrategy.USE_CACHED_RESPONSE,
            Exception("Test error"),
            context,
            plan
        )
        
        assert result["success"] == True
        assert result["action"] == "cached_response"
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_alert_and_continue_strategy(self):
        """Test alert and continue recovery strategy."""
        from diary_agent.utils.error_recovery import RecoveryStrategy, RecoveryPlan
        
        context = ErrorContext(
            error_category=ErrorCategory.DATA_VALIDATION_ERROR,
            error_message="Invalid data format",
            component_name="diary_generator",
            timestamp=datetime.now()
        )
        
        plan = RecoveryPlan(
            error_category=ErrorCategory.DATA_VALIDATION_ERROR,
            component="diary_generator",
            strategies=[RecoveryStrategy.ALERT_AND_CONTINUE]
        )
        
        result = await self.orchestrator._execute_recovery_strategy(
            RecoveryStrategy.ALERT_AND_CONTINUE,
            Exception("Test error"),
            context,
            plan
        )
        
        assert result["success"] == True
        assert result["action"] == "alert_created"
        assert "alert_id" in result
    
    def test_escalation_logic(self):
        """Test error escalation based on frequency."""
        recovery_key = "test_component_error"
        
        # Simulate multiple recovery attempts
        for i in range(6):  # Exceed default threshold
            self.orchestrator._track_recovery_attempt(recovery_key)
        
        should_escalate = self.orchestrator._should_escalate(recovery_key)
        assert should_escalate == True
    
    def test_recovery_plan_selection(self):
        """Test recovery plan selection logic."""
        context = ErrorContext(
            error_category=ErrorCategory.LLM_API_FAILURE,
            error_message="API error",
            component_name="llm_manager",
            timestamp=datetime.now()
        )
        
        plan = self.orchestrator._get_recovery_plan(context)
        assert plan is not None
        assert plan.error_category == ErrorCategory.LLM_API_FAILURE
    
    @pytest.mark.asyncio
    async def test_end_to_end_recovery_workflow(self):
        """Test complete error recovery workflow."""
        context = ErrorContext(
            error_category=ErrorCategory.LLM_API_FAILURE,
            error_message="API timeout",
            component_name="llm_manager",
            timestamp=datetime.now(),
            retry_count=0
        )
        
        result = await self.orchestrator.handle_error_with_recovery(
            Exception("API timeout"),
            context
        )
        
        # Should return some recovery result
        assert result is not None
        assert isinstance(result, dict)


class TestMonitoringIntegration:
    """Test cases for monitoring system integration."""
    
    def setup_method(self):
        """Setup test fixtures."""
        from diary_agent.utils.monitoring import PerformanceMonitor, AlertManager, HealthCheckRegistry
        self.performance_monitor = PerformanceMonitor(collection_interval=1)
        self.alert_manager = AlertManager()
        self.health_registry = HealthCheckRegistry()
    
    def test_performance_monitoring_setup(self):
        """Test performance monitoring initialization."""
        assert self.performance_monitor.collection_interval == 1
        assert self.performance_monitor.monitoring_active == False
        assert len(self.performance_monitor.thresholds) > 0
    
    def test_alert_creation_and_management(self):
        """Test alert creation and management."""
        alert = self.alert_manager.create_alert(
            alert_id="test_alert",
            severity="medium",
            component="test_component",
            message="Test alert message"
        )
        
        assert alert.alert_id == "test_alert"
        assert alert.severity == "medium"
        assert alert.resolved == False
        
        # Test alert resolution
        self.alert_manager.resolve_alert("test_alert")
        assert alert.resolved == True
        assert alert.resolution_time is not None
    
    def test_health_check_registration(self):
        """Test health check registration and execution."""
        def test_health_check():
            return True
        
        self.health_registry.register_check("test_check", test_health_check)
        
        result = self.health_registry.run_check("test_check")
        assert result == True
        
        all_results = self.health_registry.run_all_checks()
        assert "test_check" in all_results
        assert all_results["test_check"] == True
    
    def test_component_operation_recording(self):
        """Test component operation recording."""
        self.performance_monitor.record_component_operation(
            component="test_component",
            operation_time=1.5,
            success=True,
            metadata={"operation": "test"}
        )
        
        status = self.performance_monitor.get_component_status("test_component")
        assert status["operation_count"] == 1
        assert status["error_count"] == 0
        assert status["average_response_time"] == 1.5
    
    def test_alert_severity_handling(self):
        """Test different alert severity levels."""
        severities = ["low", "medium", "high", "critical"]
        
        for severity in severities:
            alert = self.alert_manager.create_alert(
                alert_id=f"test_{severity}",
                severity=severity,
                component="test_component",
                message=f"Test {severity} alert"
            )
            assert alert.severity == severity
        
        summary = self.alert_manager.get_alert_summary()
        assert summary["active_alerts"] == len(severities)


class TestCircuitBreakerIntegration:
    """Test cases for circuit breaker integration with LLM manager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1,
            success_threshold=1
        )
        self.circuit_breaker = CircuitBreaker("integration_test", self.config)
    
    def test_circuit_breaker_with_llm_simulation(self):
        """Test circuit breaker with simulated LLM calls."""
        call_count = 0
        
        def simulated_llm_call():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("LLM API failure")
            return "Success"
        
        # First two calls should fail and open circuit
        with pytest.raises(Exception):
            self.circuit_breaker.call(simulated_llm_call)
        
        with pytest.raises(Exception):
            self.circuit_breaker.call(simulated_llm_call)
        
        assert self.circuit_breaker.state == CircuitBreakerState.OPEN
        
        # Circuit should reject further calls
        with pytest.raises(CircuitBreakerOpenError):
            self.circuit_breaker.call(simulated_llm_call)
    
    def test_circuit_breaker_recovery_simulation(self):
        """Test circuit breaker recovery after timeout."""
        # Force circuit to open
        self.circuit_breaker.state = CircuitBreakerState.OPEN
        self.circuit_breaker.failure_count = self.config.failure_threshold
        self.circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=2)
        
        def successful_call():
            return "Recovery success"
        
        # Should recover and succeed
        result = self.circuit_breaker.call(successful_call)
        assert result == "Recovery success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED


class TestSystemIntegration:
    """Integration tests for the complete error handling system."""
    
    def setup_method(self):
        """Setup test fixtures."""
        from diary_agent.utils.error_recovery import ErrorRecoveryOrchestrator
        self.orchestrator = ErrorRecoveryOrchestrator()
    
    @pytest.mark.asyncio
    async def test_complete_system_failure_recovery(self):
        """Test recovery from complete system failure scenario."""
        # Simulate multiple component failures
        components = ["llm_manager", "database", "sub_agent"]
        
        for component in components:
            context = ErrorContext(
                error_category=ErrorCategory.UNKNOWN_ERROR,
                error_message=f"{component} failure",
                component_name=component,
                timestamp=datetime.now()
            )
            
            result = await self.orchestrator.handle_error_with_recovery(
                Exception(f"{component} failure"),
                context
            )
            
            # Should handle each failure gracefully
            assert result is not None
    
    def test_monitoring_and_alerting_integration(self):
        """Test integration between monitoring and alerting systems."""
        from diary_agent.utils.monitoring import performance_monitor, alert_manager
        
        # Record high error rate
        for i in range(10):
            performance_monitor.record_component_operation(
                component="test_component",
                operation_time=0.5,
                success=False  # All failures
            )
        
        # Check if alerts were created (in real implementation)
        # For now, just verify the monitoring recorded the operations
        status = performance_monitor.get_component_status("test_component")
        assert status["error_count"] == 10
        assert status["error_rate"] == 1.0  # 100% error rate
    
    def test_graceful_degradation_with_monitoring(self):
        """Test graceful degradation with health monitoring."""
        from diary_agent.utils.graceful_degradation import degradation_manager
        from diary_agent.utils.monitoring import health_check_registry
        
        # Register a failing health check
        def failing_health_check():
            return False
        
        health_check_registry.register_check("failing_component", failing_health_check)
        
        # Run health checks
        results = health_check_registry.run_all_checks()
        assert results["failing_component"] == False
        
        # Test graceful degradation response
        def fallback_function():
            return {"fallback": True, "message": "Using fallback"}
        
        from diary_agent.utils.graceful_degradation import FallbackConfig
        fallback_config = FallbackConfig(
            component_name="failing_component_fallback",
            fallback_function=fallback_function
        )
        
        degradation_manager.register_fallback("failing_component", fallback_config)
        
        result = degradation_manager.execute_with_fallback(
            "failing_component",
            lambda: (_ for _ in ()).throw(Exception("Component failed"))
        )
        
        assert result["fallback"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])