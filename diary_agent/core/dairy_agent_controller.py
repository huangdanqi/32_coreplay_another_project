"""
Main Dairy Agent Controller - Central orchestrator for the diary generation system.

This module implements the DairyAgentController class that serves as the central
coordinator for the entire diary generation system, managing initialization,
event processing workflow, health monitoring, and error recovery.
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
import random

from diary_agent.core.event_router import EventRouter
from diary_agent.core.condition import ConditionChecker
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.llm_manager import LLMConfigManager, LLMProviderError
from diary_agent.core.diary_entry_generator import DiaryEntryGenerator
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DailyQuota, EmotionalTag, DatabaseConfig
)
from diary_agent.utils.validators import EventValidator
from diary_agent.integration.database_manager import DatabaseManager

# Error handling and monitoring imports
from diary_agent.utils.error_handler import (
    ErrorHandler, ErrorCategory, ErrorContext, with_error_handling, global_error_handler
)
from diary_agent.utils.graceful_degradation import (
    GracefulDegradationManager, ServiceHealth, with_graceful_degradation, 
    register_component_health_check, degradation_manager
)
from diary_agent.utils.monitoring import (
    PerformanceMonitor, performance_monitor, start_monitoring, stop_monitoring
)
from diary_agent.utils.error_recovery import (
    ErrorRecoveryOrchestrator, error_recovery_orchestrator, handle_error_with_recovery
)
from diary_agent.utils.system_health import (
    SystemHealthDashboard, system_health_dashboard, start_all_monitoring, stop_all_monitoring
)
from diary_agent.utils.logger import get_component_logger, diary_logger


class SystemHealthError(Exception):
    """Exception raised when system health checks fail."""
    pass


class DairyAgentController:
    """
    Central orchestrator for the diary generation system.
    
    Manages system initialization, component coordination, event processing workflow,
    health monitoring, and error recovery mechanisms.
    """
    
    def __init__(self, 
                 config_dir: str = "diary_agent/config",
                 data_dir: str = "diary_agent/data",
                 log_level: str = "INFO"):
        """
        Initialize the DairyAgentController.
        
        Args:
            config_dir: Directory containing configuration files
            data_dir: Directory for data storage
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        # Setup enhanced logging
        self.logger = get_component_logger("dairy_agent_controller")
        
        # Configuration paths
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components (initialized in initialize_system)
        self.llm_manager: Optional[LLMConfigManager] = None
        self.sub_agent_manager: Optional[SubAgentManager] = None
        self.event_router: Optional[EventRouter] = None
        self.condition_checker: Optional[ConditionChecker] = None
        self.diary_generator: Optional[DiaryEntryGenerator] = None
        self.database_manager: Optional[DatabaseManager] = None
        
        # Error handling and monitoring components
        self.error_handler = global_error_handler
        self.degradation_manager = degradation_manager
        self.performance_monitor = performance_monitor
        self.error_recovery = error_recovery_orchestrator
        self.health_dashboard = system_health_dashboard
        
        # System state
        self.is_initialized = False
        self.is_running = False
        self.daily_scheduler_task: Optional[asyncio.Task] = None
        self.health_monitor_task: Optional[asyncio.Task] = None
        
        # Event processing
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_tasks: List[asyncio.Task] = []
        self.event_handlers: Dict[str, Callable] = {}
        
        # Enhanced health monitoring
        self.health_status = {
            "system_status": "initializing",
            "components": {},
            "last_health_check": None,
            "error_count": 0,
            "uptime_start": datetime.now(),
            "recovery_attempts": 0,
            "circuit_breaker_states": {}
        }
        
        # Enhanced statistics
        self.system_stats = {
            "events_processed": 0,
            "diaries_generated": 0,
            "errors_encountered": 0,
            "system_restarts": 0,
            "last_event_time": None,
            "recovery_successes": 0,
            "fallback_activations": 0
        }
        
        # Setup health checks for this controller
        self._setup_health_checks()
        
        self.logger.info("DairyAgentController initialized with comprehensive error handling")
    
    def _setup_health_checks(self):
        """Setup health checks for the controller and its components."""
        def check_controller_health():
            try:
                return (self.is_initialized and 
                       self.llm_manager is not None and
                       self.sub_agent_manager is not None and
                       self.event_router is not None)
            except Exception:
                return False
        
        def check_event_processing_health():
            try:
                return (self.is_running and 
                       self.event_queue is not None and
                       len(self.processing_tasks) > 0)
            except Exception:
                return False
        
        def check_database_health():
            try:
                return (self.database_manager is not None and
                       self.database_manager.is_connected())
            except Exception:
                return False
        
        # Register health checks
        register_component_health_check("dairy_agent_controller", check_controller_health, interval=60)
        register_component_health_check("event_processing", check_event_processing_health, interval=120)
        register_component_health_check("database_connection", check_database_health, interval=180)
    
    @with_error_handling(ErrorCategory.CONFIGURATION_ERROR, "dairy_agent_controller")
    async def initialize_system(self) -> bool:
        """
        Initialize all system components and establish connections with comprehensive error handling.
        
        Returns:
            True if initialization successful, False otherwise
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting system initialization with error handling...")
            
            # Start monitoring systems first
            self.logger.info("Starting monitoring systems...")
            monitoring_started = start_all_monitoring()
            if not monitoring_started:
                self.logger.warning("Some monitoring systems failed to start, continuing with initialization")
            
            # Step 1: Initialize LLM Manager with error handling
            self.logger.info("Initializing LLM Manager...")
            try:
                self.llm_manager = LLMConfigManager(
                    str(Path("config") / "llm_configuration.json")
                )
                self.health_status["components"]["llm_manager"] = "healthy"
            except Exception as e:
                error_context = ErrorContext(
                    error_category=ErrorCategory.CONFIGURATION_ERROR,
                    error_message=f"LLM Manager initialization failed: {str(e)}",
                    component_name="llm_manager",
                    timestamp=datetime.now()
                )
                
                recovery_result = await handle_error_with_recovery(e, error_context)
                if not recovery_result.get("success", False):
                    self.logger.error("Failed to recover from LLM Manager initialization error")
                    return False
                
                self.health_status["components"]["llm_manager"] = "degraded"
            
            # Step 2: Initialize Database Manager with error handling
            self.logger.info("Initializing Database Manager...")
            try:
                self.database_manager = DatabaseManager()
                await self.database_manager.initialize()
                self.health_status["components"]["database_manager"] = "healthy"
            except Exception as e:
                error_context = ErrorContext(
                    error_category=ErrorCategory.DATABASE_ERROR,
                    error_message=f"Database Manager initialization failed: {str(e)}",
                    component_name="database_manager",
                    timestamp=datetime.now()
                )
                
                recovery_result = await handle_error_with_recovery(e, error_context)
                if not recovery_result.get("success", False):
                    self.logger.error("Failed to recover from Database Manager initialization error")
                    return False
                
                self.health_status["components"]["database_manager"] = "degraded"
            
            # Step 3: Initialize Sub-Agent Manager with error handling
            self.logger.info("Initializing Sub-Agent Manager...")
            try:
                self.sub_agent_manager = SubAgentManager(
                    llm_manager=self.llm_manager,
                    config_dir=str(self.config_dir)
                )
                
                # Initialize all agents with error handling
                agents_initialized = await self._initialize_agents_with_recovery()
                if not agents_initialized:
                    self.logger.error("Failed to initialize all agents")
                    self.health_status["components"]["sub_agent_manager"] = "degraded"
                else:
                    self.health_status["components"]["sub_agent_manager"] = "healthy"
                    
            except Exception as e:
                error_context = ErrorContext(
                    error_category=ErrorCategory.SUB_AGENT_FAILURE,
                    error_message=f"Sub-Agent Manager initialization failed: {str(e)}",
                    component_name="sub_agent_manager",
                    timestamp=datetime.now()
                )
                
                recovery_result = await handle_error_with_recovery(e, error_context)
                if not recovery_result.get("success", False):
                    self.logger.error("Failed to recover from Sub-Agent Manager initialization error")
                    return False
                
                self.health_status["components"]["sub_agent_manager"] = "degraded"
            
            # Step 4: Initialize Condition Checker
            self.logger.info("Initializing Condition Checker...")
            self.condition_checker = ConditionChecker(
                str(self.config_dir / "condition_rules.json")
            )
            
            # Step 5: Initialize Event Router
            self.logger.info("Initializing Event Router...")
            self.event_router = EventRouter(
                events_json_path="diary_agent/events.json"
            )
            
            # Register agents with event router
            for agent_type in self.sub_agent_manager.list_agents():
                agent = self.sub_agent_manager.get_agent(agent_type)
                if agent:
                    self.event_router.register_agent(agent_type, agent)
            
            # Step 6: Initialize Diary Entry Generator
            self.logger.info("Initializing Diary Entry Generator...")
            self.diary_generator = DiaryEntryGenerator(
                llm_manager=self.llm_manager,
                agent_registry=self.sub_agent_manager.registry,
                storage_path=str(self.data_dir / "diary_entries")
            )
            
            # Step 7: Setup event handlers and connections
            self._setup_event_handlers()
            self._setup_component_connections()
            
            # Step 8: Initialize daily quota for today
            await self._initialize_daily_quota()
            
            # Step 9: Perform initial health check
            health_status = await self._perform_health_check()
            if not health_status["overall_healthy"]:
                self.logger.warning("System health check shows issues, but continuing...")
            
            self.is_initialized = True
            self.health_status["system_status"] = "initialized"
            
            self.logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {str(e)}")
            self.health_status["system_status"] = "initialization_failed"
            return False
    
    def _setup_event_handlers(self):
        """Setup event handlers for different event types."""
        # Register condition checker as event handler
        if self.condition_checker:
            self.condition_checker.register_event_handler(
                "all", self._handle_event_processing
            )
        
        # Register query functions with event router
        if self.event_router and self.sub_agent_manager:
            for agent_type in self.sub_agent_manager.list_agents():
                agent = self.sub_agent_manager.get_agent(agent_type)
                if agent and hasattr(agent, 'get_data_reader'):
                    data_reader = agent.get_data_reader()
                    if data_reader:
                        self.event_router.register_query_function(
                            agent_type, data_reader.read_event_context
                        )
    
    def _setup_component_connections(self):
        """Setup connections between components."""
        # Connect condition checker with daily quota
        if self.condition_checker and self.event_router:
            # Set initial daily quota in condition checker
            current_quota = self.event_router.daily_quota
            if current_quota:
                self.condition_checker.set_daily_quota(current_quota)
    
    async def _initialize_daily_quota(self):
        """Initialize daily quota for today."""
        today = datetime.now()
        
        # Check if we already have a quota for today
        if self.diary_generator:
            existing_quota = self.diary_generator.get_daily_quota(today)
            if existing_quota:
                self.logger.info(f"Using existing daily quota: {existing_quota.total_quota}")
                return
        
        # Generate new daily quota (0-5 entries)
        daily_quota_count = random.randint(2, 5)  # Ensure at least 2 for testing
        
        # Set quota in diary generator
        if self.diary_generator:
            self.diary_generator.set_daily_quota(today, daily_quota_count)
        
        # Set quota in event router
        if self.event_router:
            daily_quota = DailyQuota(
                date=today.date(),
                total_quota=daily_quota_count
            )
            self.event_router.update_daily_quota(daily_quota)
        
        # Set quota in condition checker
        if self.condition_checker:
            daily_quota = DailyQuota(
                date=today.date(),
                total_quota=daily_quota_count
            )
            self.condition_checker.set_daily_quota(daily_quota)
        
        self.logger.info(f"Initialized daily quota for {today.date()}: {daily_quota_count} entries")
    
    async def start_system(self) -> bool:
        """
        Start the diary generation system.
        
        Returns:
            True if system started successfully, False otherwise
        """
        if not self.is_initialized:
            self.logger.error("System not initialized. Call initialize_system() first.")
            return False
        
        try:
            self.logger.info("Starting diary generation system...")
            
            # Start daily scheduler
            self.daily_scheduler_task = asyncio.create_task(
                self._daily_scheduler_loop()
            )
            
            # Start health monitor
            self.health_monitor_task = asyncio.create_task(
                self._health_monitor_loop()
            )
            
            # Start event processing
            for i in range(3):  # 3 concurrent event processors
                task = asyncio.create_task(self._event_processor_loop())
                self.processing_tasks.append(task)
            
            self.is_running = True
            self.health_status["system_status"] = "running"
            
            self.logger.info("Diary generation system started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {str(e)}")
            return False
    
    async def stop_system(self):
        """Stop the diary generation system gracefully."""
        self.logger.info("Stopping diary generation system...")
        
        self.is_running = False
        
        # Cancel daily scheduler
        if self.daily_scheduler_task:
            self.daily_scheduler_task.cancel()
            try:
                await self.daily_scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel health monitor
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel event processing tasks
        for task in self.processing_tasks:
            task.cancel()
        
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        # Shutdown sub-agent manager
        if self.sub_agent_manager:
            await self.sub_agent_manager.shutdown()
        
        # Close database connections
        if self.database_manager:
            self.database_manager.close()
        
        self.health_status["system_status"] = "stopped"
        self.logger.info("Diary generation system stopped")
    
    async def process_event(self, event_data: EventData) -> Optional[DiaryEntry]:
        """
        Process a single event through the complete workflow.
        
        Args:
            event_data: Event data to process
            
        Returns:
            Generated diary entry or None if processing failed/skipped
        """
        try:
            self.logger.debug(f"Processing event: {event_data.event_name}")
            
            # Step 1: Validate event data
            validator = EventValidator()
            if not validator.validate_event_data(event_data):
                self.logger.warning(f"Event validation failed: {event_data.event_id}")
                return None
            
            # Step 2: Check conditions for diary generation
            if not self.condition_checker.evaluate_conditions(event_data):
                self.logger.debug(f"Conditions not met for event: {event_data.event_name}")
                return None
            
            # Step 3: Route event to appropriate agent
            routing_result = self.event_router.route_event(event_data)
            if not routing_result or not routing_result.get("success"):
                self.logger.warning(f"Event routing failed: {routing_result}")
                return None
            
            # Step 4: Generate diary entry if routing was successful
            if routing_result.get("diary_generated"):
                diary_entry = routing_result.get("diary_entry")
                if diary_entry:
                    self.system_stats["diaries_generated"] += 1
                    self.system_stats["last_event_time"] = datetime.now()
                    self.logger.info(f"Successfully generated diary for event: {event_data.event_name}")
                    return diary_entry
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing event {event_data.event_id}: {str(e)}")
            self.system_stats["errors_encountered"] += 1
            return None
        finally:
            self.system_stats["events_processed"] += 1
    
    async def _handle_event_processing(self, event_data: EventData):
        """Handle event processing triggered by condition checker."""
        await self.event_queue.put(event_data)
    
    async def _event_processor_loop(self):
        """Event processor loop for handling queued events."""
        while self.is_running:
            try:
                # Wait for event with timeout
                event_data = await asyncio.wait_for(
                    self.event_queue.get(), timeout=1.0
                )
                
                # Process the event
                await self.process_event(event_data)
                
            except asyncio.TimeoutError:
                # No events to process, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in event processor loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _daily_scheduler_loop(self):
        """Daily scheduler loop for quota management and daily tasks."""
        while self.is_running:
            try:
                now = datetime.now()
                
                # Check if it's time for daily reset (00:00-00:01)
                if now.time() >= time(0, 0) and now.time() <= time(0, 1):
                    await self._perform_daily_reset()
                    
                    # Sleep until next minute to avoid multiple resets
                    await asyncio.sleep(60)
                
                # Sleep for 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in daily scheduler: {str(e)}")
                await asyncio.sleep(60)
    
    async def _perform_daily_reset(self):
        """Perform daily reset tasks at 00:00."""
        self.logger.info("Performing daily reset...")
        
        try:
            # Reset daily quota
            await self._initialize_daily_quota()
            
            # Reset event router quota
            if self.event_router:
                self.event_router.reset_daily_quota()
            
            # Restart unhealthy agents
            if self.sub_agent_manager:
                restart_results = await self.sub_agent_manager.restart_unhealthy_agents()
                if restart_results:
                    self.logger.info(f"Restarted unhealthy agents: {restart_results}")
            
            # Reset generation statistics
            if self.diary_generator:
                self.diary_generator.reset_generation_stats()
            
            self.logger.info("Daily reset completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during daily reset: {str(e)}")
    
    async def _health_monitor_loop(self):
        """Health monitoring loop."""
        while self.is_running:
            try:
                # Perform health check every 5 minutes
                health_status = await self._perform_health_check()
                
                # Log health issues
                if not health_status["overall_healthy"]:
                    self.logger.warning(f"Health issues detected: {health_status}")
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {str(e)}")
                await asyncio.sleep(60)
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check.
        
        Returns:
            Dictionary containing health status information
        """
        health_status = {
            "timestamp": datetime.now(),
            "overall_healthy": True,
            "components": {},
            "issues": []
        }
        
        try:
            # Check LLM Manager
            if self.llm_manager:
                llm_status = self.llm_manager.get_provider_status()
                health_status["components"]["llm_manager"] = {
                    "status": "healthy" if llm_status["total_providers"] > 0 else "unhealthy",
                    "details": llm_status
                }
                if llm_status["total_providers"] == 0:
                    health_status["issues"].append("No LLM providers available")
                    health_status["overall_healthy"] = False
            
            # Check Sub-Agent Manager
            if self.sub_agent_manager:
                agent_status = self.sub_agent_manager.get_system_status()
                health_status["components"]["sub_agent_manager"] = {
                    "status": "healthy" if agent_status["unhealthy_agents"] == 0 else "degraded",
                    "details": agent_status
                }
                if agent_status["unhealthy_agents"] > 0:
                    health_status["issues"].append(f"{agent_status['unhealthy_agents']} unhealthy agents")
            
            # Check Database Manager
            if self.database_manager:
                db_healthy = await self.database_manager.health_check()
                health_status["components"]["database_manager"] = {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "details": {"connection_active": db_healthy}
                }
                if not db_healthy:
                    health_status["issues"].append("Database connection issues")
                    health_status["overall_healthy"] = False
            
            # Check Event Router
            if self.event_router:
                router_stats = self.event_router.get_routing_statistics()
                health_status["components"]["event_router"] = {
                    "status": "healthy",
                    "details": router_stats
                }
            
            # Check Diary Generator
            if self.diary_generator:
                gen_stats = self.diary_generator.get_generation_stats()
                success_rate = (gen_stats["successful_generations"] / 
                              max(1, gen_stats["total_generated"]) * 100)
                health_status["components"]["diary_generator"] = {
                    "status": "healthy" if success_rate >= 80 else "degraded",
                    "details": {**gen_stats, "success_rate": success_rate}
                }
                if success_rate < 80:
                    health_status["issues"].append(f"Low diary generation success rate: {success_rate:.1f}%")
            
            # Update overall health status
            if health_status["issues"]:
                health_status["overall_healthy"] = False
            
            # Update system health status
            self.health_status.update({
                "system_status": "healthy" if health_status["overall_healthy"] else "degraded",
                "components": health_status["components"],
                "last_health_check": health_status["timestamp"],
                "error_count": len(health_status["issues"])
            })
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            health_status["overall_healthy"] = False
            health_status["issues"].append(f"Health check error: {str(e)}")
            return health_status
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status information.
        
        Returns:
            Dictionary containing system status and statistics
        """
        uptime = datetime.now() - self.health_status["uptime_start"]
        
        return {
            "system_info": {
                "is_initialized": self.is_initialized,
                "is_running": self.is_running,
                "uptime_seconds": int(uptime.total_seconds()),
                "uptime_formatted": str(uptime)
            },
            "health_status": self.health_status.copy(),
            "statistics": self.system_stats.copy(),
            "component_status": {
                "llm_manager": self.llm_manager.get_provider_status() if self.llm_manager else None,
                "sub_agent_manager": self.sub_agent_manager.get_system_status() if self.sub_agent_manager else None,
                "event_router": self.event_router.get_routing_statistics() if self.event_router else None,
                "diary_generator": self.diary_generator.get_generation_stats() if self.diary_generator else None
            }
        }
    
    async def restart_system(self) -> bool:
        """
        Restart the entire system.
        
        Returns:
            True if restart successful, False otherwise
        """
        self.logger.info("Restarting system...")
        
        try:
            # Stop system
            await self.stop_system()
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Reinitialize and start
            if await self.initialize_system():
                if await self.start_system():
                    self.system_stats["system_restarts"] += 1
                    self.logger.info("System restart completed successfully")
                    return True
            
            self.logger.error("System restart failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Error during system restart: {str(e)}")
            return False
    
    async def process_manual_event(self, 
                                 event_name: str, 
                                 user_id: int,
                                 context_data: Optional[Dict[str, Any]] = None) -> Optional[DiaryEntry]:
        """
        Process a manually triggered event.
        
        Args:
            event_name: Name of the event to process
            user_id: User ID for the event
            context_data: Optional context data
            
        Returns:
            Generated diary entry or None if processing failed
        """
        # Create event data
        event_data = EventData(
            event_id=f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{event_name}",
            event_type="manual",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data=context_data or {},
            metadata={"source": "manual", "triggered_by": "user"}
        )
        
        # Process the event
        return await self.process_event(event_data)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Register a custom event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Callable to handle the event
        """
        self.event_handlers[event_type] = handler
        self.logger.info(f"Registered custom event handler for: {event_type}")
    
    async def get_diary_entries(self, 
                              user_id: int, 
                              date: Optional[datetime] = None) -> List[DiaryEntry]:
        """
        Get diary entries for a user.
        
        Args:
            user_id: User ID
            date: Specific date (if None, gets all entries)
            
        Returns:
            List of diary entries
        """
        if self.diary_generator:
            return await self.diary_generator.load_diary_entries(user_id, date)
        return []
    
    def get_supported_events(self) -> List[str]:
        """Get list of all supported event names."""
        if self.sub_agent_manager:
            return self.sub_agent_manager.list_supported_events()
        return []
    
    async def force_daily_reset(self):
        """Force a daily reset (for testing or manual intervention)."""
        await self._perform_daily_reset()
    
    async def emergency_shutdown(self):
        """Emergency shutdown of the system."""
        self.logger.warning("Emergency shutdown initiated")
        
        self.is_running = False
        
        # Cancel all tasks immediately
        tasks_to_cancel = []
        if self.daily_scheduler_task:
            tasks_to_cancel.append(self.daily_scheduler_task)
        if self.health_monitor_task:
            tasks_to_cancel.append(self.health_monitor_task)
        tasks_to_cancel.extend(self.processing_tasks)
        
        for task in tasks_to_cancel:
            task.cancel()
        
        # Don't wait for graceful shutdown in emergency
        self.health_status["system_status"] = "emergency_stopped"
        self.logger.warning("Emergency shutdown completed")


# Convenience functions for system management
async def create_and_start_system(config_dir: str = "diary_agent/config",
                                data_dir: str = "diary_agent/data",
                                log_level: str = "INFO") -> DairyAgentController:
    """
    Create, initialize, and start a complete diary agent system.
    
    Args:
        config_dir: Configuration directory
        data_dir: Data directory
        log_level: Logging level
        
    Returns:
        Initialized and started DairyAgentController
        
    Raises:
        SystemHealthError: If system fails to initialize or start
    """
    controller = DairyAgentController(config_dir, data_dir, log_level)
    
    if not await controller.initialize_system():
        raise SystemHealthError("Failed to initialize diary agent system")
    
    if not await controller.start_system():
        raise SystemHealthError("Failed to start diary agent system")
    
    return controller


async def run_system_with_monitoring(controller: DairyAgentController,
                                   monitor_interval: int = 300):
    """
    Run system with continuous monitoring and automatic recovery.
    
    Args:
        controller: Initialized DairyAgentController
        monitor_interval: Health check interval in seconds
    """
    while controller.is_running:
        try:
            # Wait for monitor interval
            await asyncio.sleep(monitor_interval)
            
            # Check system health
            health_status = await controller._perform_health_check()
            
            # Attempt recovery if system is unhealthy
            if not health_status["overall_healthy"]:
                controller.logger.warning("System health issues detected, attempting recovery...")
                
                # Try restarting unhealthy agents first
                if controller.sub_agent_manager:
                    await controller.sub_agent_manager.restart_unhealthy_agents()
                
                # If still unhealthy, try full system restart
                await asyncio.sleep(30)
                health_status = await controller._perform_health_check()
                if not health_status["overall_healthy"]:
                    controller.logger.warning("Attempting full system restart...")
                    await controller.restart_system()
            
        except Exception as e:
            controller.logger.error(f"Error in system monitoring: {str(e)}")
            await asyncio.sleep(60)     
       
            # Step 4: Initialize Event Router with error handling
            self.logger.info("Initializing Event Router...")
            try:
                self.event_router = EventRouter(
                    sub_agent_manager=self.sub_agent_manager,
                    events_config_path=str(self.config_dir.parent / "events.json")
                )
                self.health_status["components"]["event_router"] = "healthy"
            except Exception as e:
                error_context = ErrorContext(
                    error_category=ErrorCategory.CONFIGURATION_ERROR,
                    error_message=f"Event Router initialization failed: {str(e)}",
                    component_name="event_router",
                    timestamp=datetime.now()
                )
                
                recovery_result = await handle_error_with_recovery(e, error_context)
                if not recovery_result.get("success", False):
                    self.logger.error("Failed to recover from Event Router initialization error")
                    return False
                
                self.health_status["components"]["event_router"] = "degraded"
            
            # Step 5: Initialize Condition Checker with error handling
            self.logger.info("Initializing Condition Checker...")
            try:
                self.condition_checker = ConditionChecker(
                    config_path=str(self.config_dir / "condition_rules.json")
                )
                self.health_status["components"]["condition_checker"] = "healthy"
            except Exception as e:
                error_context = ErrorContext(
                    error_category=ErrorCategory.CONDITION_EVALUATION_ERROR,
                    error_message=f"Condition Checker initialization failed: {str(e)}",
                    component_name="condition_checker",
                    timestamp=datetime.now()
                )
                
                recovery_result = await handle_error_with_recovery(e, error_context)
                if not recovery_result.get("success", False):
                    self.logger.error("Failed to recover from Condition Checker initialization error")
                    return False
                
                self.health_status["components"]["condition_checker"] = "degraded"
            
            # Step 6: Initialize Diary Entry Generator with error handling
            self.logger.info("Initializing Diary Entry Generator...")
            try:
                self.diary_generator = DiaryEntryGenerator(
                    llm_manager=self.llm_manager,
                    database_manager=self.database_manager
                )
                self.health_status["components"]["diary_generator"] = "healthy"
            except Exception as e:
                error_context = ErrorContext(
                    error_category=ErrorCategory.CONFIGURATION_ERROR,
                    error_message=f"Diary Generator initialization failed: {str(e)}",
                    component_name="diary_generator",
                    timestamp=datetime.now()
                )
                
                recovery_result = await handle_error_with_recovery(e, error_context)
                if not recovery_result.get("success", False):
                    self.logger.error("Failed to recover from Diary Generator initialization error")
                    return False
                
                self.health_status["components"]["diary_generator"] = "degraded"
            
            # Update system status
            self.is_initialized = True
            self.health_status["system_status"] = "initialized"
            self.health_status["last_health_check"] = datetime.now()
            
            # Log initialization completion
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"System initialization completed in {duration:.2f} seconds")
            
            # Record performance metrics
            self.performance_monitor.record_component_operation(
                component="dairy_agent_controller",
                operation_time=duration,
                success=True,
                metadata={"operation": "system_initialization"}
            )
            
            # Log system health status
            diary_logger.log_component_start(
                "dairy_agent_controller",
                metadata=self.health_status
            )
            
            return True
            
        except Exception as e:
            # Handle unexpected initialization errors
            self.logger.error(f"Unexpected error during system initialization: {str(e)}")
            self.system_stats["errors_encountered"] += 1
            self.health_status["system_status"] = "initialization_failed"
            
            # Record failed initialization
            duration = (datetime.now() - start_time).total_seconds()
            self.performance_monitor.record_component_operation(
                component="dairy_agent_controller",
                operation_time=duration,
                success=False,
                metadata={"operation": "system_initialization", "error": str(e)}
            )
            
            return False
    
    async def _initialize_agents_with_recovery(self) -> bool:
        """Initialize agents with individual error recovery."""
        try:
            agents_initialized = await self.sub_agent_manager.initialize_agents()
            
            if not agents_initialized:
                # Try to initialize agents individually with recovery
                self.logger.warning("Bulk agent initialization failed, trying individual initialization with recovery")
                
                agent_types = [
                    "weather_agent", "trending_agent", "holiday_agent", "friends_agent",
                    "same_frequency_agent", "adoption_agent", "interactive_agent",
                    "dialogue_agent", "neglect_agent"
                ]
                
                successful_agents = 0
                for agent_type in agent_types:
                    try:
                        success = await self.sub_agent_manager.initialize_single_agent(agent_type)
                        if success:
                            successful_agents += 1
                            self.logger.info(f"Successfully initialized {agent_type}")
                        else:
                            self.logger.warning(f"Failed to initialize {agent_type}, will use fallback")
                    except Exception as e:
                        self.logger.error(f"Error initializing {agent_type}: {str(e)}")
                        
                        # Register fallback for failed agent
                        self._register_agent_fallback(agent_type)
                
                # Consider initialization successful if at least half the agents are working
                return successful_agents >= len(agent_types) // 2
            
            return True
            
        except Exception as e:
            self.logger.error(f"Agent initialization with recovery failed: {str(e)}")
            return False
    
    def _register_agent_fallback(self, agent_type: str):
        """Register fallback for a failed agent."""
        from diary_agent.utils.graceful_degradation import FallbackConfig
        
        def agent_fallback(*args, **kwargs):
            return {
                "title": "记录",
                "content": f"今天有关于{agent_type}的事情发生了。",
                "emotion_tags": ["平静"],
                "source": f"{agent_type}_fallback"
            }
        
        fallback_config = FallbackConfig(
            component_name=f"{agent_type}_fallback",
            fallback_function=agent_fallback,
            priority=1
        )
        
        self.degradation_manager.register_fallback(agent_type, fallback_config)
        self.logger.info(f"Registered fallback for {agent_type}")
    
    @with_graceful_degradation("dairy_agent_controller")
    async def start_system(self) -> bool:
        """
        Start the diary agent system with comprehensive error handling.
        
        Returns:
            True if system started successfully, False otherwise
        """
        try:
            if not self.is_initialized:
                self.logger.error("System not initialized. Call initialize_system() first.")
                return False
            
            if self.is_running:
                self.logger.warning("System is already running")
                return True
            
            self.logger.info("Starting diary agent system...")
            
            # Start daily scheduler
            self.daily_scheduler_task = asyncio.create_task(self._daily_scheduler_loop())
            
            # Start health monitoring
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            
            # Start event processing
            for i in range(3):  # Start 3 event processing workers
                task = asyncio.create_task(self._event_processing_worker(f"worker_{i}"))
                self.processing_tasks.append(task)
            
            self.is_running = True
            self.health_status["system_status"] = "running"
            
            self.logger.info("Diary agent system started successfully")
            
            # Log system start
            diary_logger.log_component_start(
                "dairy_agent_system",
                metadata={"workers": len(self.processing_tasks)}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {str(e)}")
            self.system_stats["errors_encountered"] += 1
            
            # Handle startup error
            error_context = ErrorContext(
                error_category=ErrorCategory.UNKNOWN_ERROR,
                error_message=f"System startup failed: {str(e)}",
                component_name="dairy_agent_controller",
                timestamp=datetime.now()
            )
            
            await handle_error_with_recovery(e, error_context)
            return False
    
    async def _health_monitor_loop(self):
        """Continuous health monitoring loop with error recovery."""
        while self.is_running:
            try:
                # Perform health checks
                health_status = self.health_dashboard.get_comprehensive_status()
                
                # Update local health status
                self.health_status.update({
                    "last_health_check": datetime.now(),
                    "overall_health": health_status["overall_health"]
                })
                
                # Check for critical issues
                if health_status["overall_health"] == "critical":
                    self.logger.critical("Critical system health issues detected")
                    await self._handle_critical_health_issues(health_status)
                
                # Log health status periodically
                if datetime.now().minute % 10 == 0:  # Every 10 minutes
                    self.logger.info(f"System health: {health_status['overall_health']}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _handle_critical_health_issues(self, health_status: Dict[str, Any]):
        """Handle critical health issues with recovery actions."""
        try:
            recommendations = health_status.get("recommendations", [])
            critical_recommendations = [
                rec for rec in recommendations 
                if rec.get("priority") == "critical"
            ]
            
            for recommendation in critical_recommendations:
                action = recommendation.get("action")
                
                if action == "investigate_unhealthy_components":
                    await self._recover_unhealthy_components()
                elif action == "resolve_critical_alerts":
                    await self._resolve_critical_alerts()
                elif action == "investigate_circuit_breaker_failures":
                    await self._recover_circuit_breakers()
                
        except Exception as e:
            self.logger.error(f"Error handling critical health issues: {str(e)}")
    
    async def _recover_unhealthy_components(self):
        """Attempt to recover unhealthy components."""
        unhealthy_components = [
            name for name, health in self.degradation_manager.component_status.items()
            if health == ServiceHealth.UNHEALTHY
        ]
        
        for component in unhealthy_components:
            try:
                self.logger.info(f"Attempting to recover unhealthy component: {component}")
                
                # Try to restart component if it's a core component
                if component in ["llm_manager", "sub_agent_manager", "event_router"]:
                    await self._restart_component(component)
                
            except Exception as e:
                self.logger.error(f"Failed to recover component {component}: {str(e)}")
    
    async def _restart_component(self, component_name: str):
        """Restart a specific component."""
        try:
            if component_name == "llm_manager" and self.llm_manager:
                self.llm_manager.reload_configuration()
                self.logger.info(f"Reloaded {component_name} configuration")
            
            elif component_name == "sub_agent_manager" and self.sub_agent_manager:
                await self.sub_agent_manager.reload_agents()
                self.logger.info(f"Reloaded {component_name} agents")
            
            # Mark component as recovered
            self.degradation_manager.component_status[component_name] = ServiceHealth.HEALTHY
            self.system_stats["recovery_successes"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to restart component {component_name}: {str(e)}")
    
    async def _resolve_critical_alerts(self):
        """Attempt to resolve critical alerts."""
        from diary_agent.utils.monitoring import alert_manager
        
        active_alerts = alert_manager.get_active_alerts()
        critical_alerts = [alert for alert in active_alerts if alert.severity == "critical"]
        
        for alert in critical_alerts:
            try:
                # Auto-resolve alerts older than 1 hour if component is now healthy
                if (datetime.now() - alert.timestamp).total_seconds() > 3600:
                    component_health = self.degradation_manager.get_component_health(alert.component)
                    if component_health == ServiceHealth.HEALTHY:
                        alert_manager.resolve_alert(alert.alert_id)
                        self.logger.info(f"Auto-resolved old alert: {alert.alert_id}")
                
            except Exception as e:
                self.logger.error(f"Error resolving alert {alert.alert_id}: {str(e)}")
    
    async def _recover_circuit_breakers(self):
        """Attempt to recover open circuit breakers."""
        circuit_states = self.error_handler.get_error_statistics().get("circuit_breaker_states", {})
        open_breakers = [name for name, state in circuit_states.items() if state == "open"]
        
        for breaker_name in open_breakers:
            try:
                breaker = self.error_handler.get_circuit_breaker(breaker_name)
                
                # Force circuit breaker to half-open for testing
                if breaker.state.value == "open":
                    # Reset failure count to allow testing
                    breaker.failure_count = 0
                    self.logger.info(f"Reset circuit breaker {breaker_name} for recovery testing")
                
            except Exception as e:
                self.logger.error(f"Error recovering circuit breaker {breaker_name}: {str(e)}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including error handling metrics."""
        try:
            base_status = {
                "is_initialized": self.is_initialized,
                "is_running": self.is_running,
                "uptime": (datetime.now() - self.health_status["uptime_start"]).total_seconds(),
                "health_status": self.health_status,
                "system_stats": self.system_stats
            }
            
            # Add comprehensive health information
            comprehensive_health = self.health_dashboard.get_comprehensive_status()
            base_status.update({
                "comprehensive_health": comprehensive_health,
                "error_handling": self.error_handler.get_error_statistics(),
                "performance": self.performance_monitor.get_performance_summary()
            })
            
            return base_status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {str(e)}")
            return {
                "error": str(e),
                "is_initialized": self.is_initialized,
                "is_running": self.is_running
            }
    
    async def shutdown_system(self) -> bool:
        """
        Gracefully shutdown the system with proper cleanup.
        
        Returns:
            True if shutdown successful, False otherwise
        """
        try:
            self.logger.info("Starting system shutdown...")
            
            # Stop accepting new events
            self.is_running = False
            
            # Cancel running tasks
            if self.daily_scheduler_task:
                self.daily_scheduler_task.cancel()
            
            if self.health_monitor_task:
                self.health_monitor_task.cancel()
            
            for task in self.processing_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(
                *[task for task in [self.daily_scheduler_task, self.health_monitor_task] + self.processing_tasks if task],
                return_exceptions=True
            )
            
            # Shutdown components
            if self.database_manager:
                await self.database_manager.close()
            
            # Stop monitoring systems
            stop_all_monitoring()
            
            # Log shutdown
            diary_logger.log_component_stop(
                "dairy_agent_system",
                metadata=self.system_stats
            )
            
            self.logger.info("System shutdown completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during system shutdown: {str(e)}")
            return False    

    async def _initialize_agents_with_recovery(self) -> bool:
        """Initialize all agents with error recovery."""
        try:
            if not self.sub_agent_manager:
                return False
            
            # Initialize all agents
            await self.sub_agent_manager.initialize_all_agents()
            
            # Check if at least some agents were initialized
            agent_count = len(self.sub_agent_manager.list_agents())
            self.logger.info(f"Initialized {agent_count} agents")
            
            return agent_count > 0
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
            return False