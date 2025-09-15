"""
Daily Diary Generation Scheduler for the diary agent system.

This module implements the daily scheduling logic following diary_agent_specifications_en.md:
- Daily scheduler that runs at 00:00 to randomly determine diary quota (0-5 entries)
- Claimed events logic (certain events must result in diary entries)
- Event-driven random selection logic
- Query function calling system
- Agent type calling system
- Daily completion tracking
- One-diary-per-type constraint
- Diary entry formatting and storage
"""

import asyncio
import random
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import json

from ..utils.data_models import (
    EventData, DiaryEntry, DailyQuota, EmotionalTag, DiaryContextData
)
from ..core.event_router import EventRouter
from ..core.sub_agent_manager import SubAgentManager
from ..core.diary_entry_generator import DiaryEntryGenerator
from ..core.data_persistence import DiaryPersistenceManager
from ..utils.validators import DiaryEntryValidator
from ..utils.formatters import DiaryEntryFormatter


@dataclass
class DailyScheduleConfig:
    """Configuration for daily diary generation scheduling."""
    schedule_time: time = field(default_factory=lambda: time(0, 0))  # 00:00
    min_quota: int = 0
    max_quota: int = 5
    claimed_events_always_generate: bool = True
    random_selection_probability: float = 0.6
    alternative_approach_enabled: bool = True
    max_retries_per_event: int = 3
    storage_enabled: bool = True


@dataclass
class DiaryGenerationResult:
    """Result of diary generation attempt."""
    success: bool
    diary_entry: Optional[DiaryEntry] = None
    error_message: Optional[str] = None
    agent_type: Optional[str] = None
    event_type: Optional[str] = None
    generation_time: Optional[datetime] = None


class DailyScheduler:
    """
    Daily diary generation scheduler that manages the complete diary generation workflow.
    
    Implements the process specified in diary_agent_specifications_en.md:
    1. Daily quota determination at 00:00 (0-5 entries)
    2. Event-driven diary generation with random selection
    3. Claimed events processing (always generate)
    4. Query function calling and agent routing
    5. Daily completion tracking with one-diary-per-type constraint
    6. Alternative approach for insufficient events
    """
    
    def __init__(self,
                 event_router: EventRouter,
                 sub_agent_manager: SubAgentManager,
                 diary_generator: DiaryEntryGenerator,
                 data_persistence: DiaryPersistenceManager,
                 config: Optional[DailyScheduleConfig] = None):
        """
        Initialize the DailyScheduler.
        
        Args:
            event_router: Event routing system
            sub_agent_manager: Sub-agent management system
            diary_generator: Diary entry generation system
            data_persistence: Data storage system
            config: Scheduler configuration
        """
        self.event_router = event_router
        self.sub_agent_manager = sub_agent_manager
        self.diary_generator = diary_generator
        self.data_persistence = data_persistence
        self.config = config or DailyScheduleConfig()
        
        # Current daily state
        self.current_quota: Optional[DailyQuota] = None
        self.daily_generation_results: List[DiaryGenerationResult] = []
        
        # Query function registry
        self.query_functions: Dict[str, Callable] = {}
        
        # Validation and formatting
        self.validator = DiaryEntryValidator()
        self.formatter = DiaryEntryFormatter()
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Scheduler state
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.daily_stats = {
            "total_events_processed": 0,
            "diaries_generated": 0,
            "claimed_events_processed": 0,
            "random_events_processed": 0,
            "failed_generations": 0
        }
    
    async def start_scheduler(self):
        """Start the daily scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Daily scheduler started")
    
    async def stop_scheduler(self):
        """Stop the daily scheduler."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Daily scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop that runs continuously."""
        try:
            while self.is_running:
                now = datetime.now()
                
                # Check if it's time for daily quota reset (00:00)
                if self._should_reset_daily_quota(now):
                    await self._reset_daily_quota()
                
                # Process any pending events
                await self._process_pending_events()
                
                # Sleep until next check (every minute)
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            self.logger.info("Scheduler loop cancelled")
        except Exception as e:
            self.logger.error(f"Scheduler loop error: {str(e)}")
    
    def _should_reset_daily_quota(self, current_time: datetime) -> bool:
        """Check if daily quota should be reset."""
        if not self.current_quota:
            return True
        
        # Check if it's a new day and past the schedule time
        current_date = current_time.date()
        quota_date = self.current_quota.date
        
        if current_date > quota_date:
            current_time_only = current_time.time()
            return current_time_only >= self.config.schedule_time
        
        return False
    
    async def _reset_daily_quota(self):
        """Reset daily quota at 00:00 and determine new quota."""
        # Generate random quota (0-5)
        new_quota = random.randint(self.config.min_quota, self.config.max_quota)
        
        # Create new daily quota
        self.current_quota = DailyQuota(
            date=datetime.now().date(),
            total_quota=new_quota
        )
        
        # Update event router with new quota
        self.event_router.update_daily_quota(self.current_quota)
        
        # Reset daily statistics
        self.daily_stats = {
            "total_events_processed": 0,
            "diaries_generated": 0,
            "claimed_events_processed": 0,
            "random_events_processed": 0,
            "failed_generations": 0
        }
        
        # Clear previous day's results
        self.daily_generation_results.clear()
        
        self.logger.info(f"Daily quota reset: {new_quota} diaries for {self.current_quota.date}")
        
        # If quota is 0, log and return
        if new_quota == 0:
            self.logger.info("No diaries scheduled for today (quota = 0)")
            return
        
        # Alternative approach: Pre-select event types for today if enabled
        if self.config.alternative_approach_enabled and new_quota > 0:
            await self._select_event_types_for_today()
    
    async def _select_event_types_for_today(self):
        """Alternative approach: Randomly select event types for today's diary generation."""
        if not self.current_quota or self.current_quota.total_quota == 0:
            return
        
        # Get available event types
        available_types = self.event_router.get_available_event_types_for_today()
        
        if not available_types:
            self.logger.warning("No available event types for today")
            return
        
        # Randomly select event types up to quota
        selected_count = min(self.current_quota.total_quota, len(available_types))
        selected_types = random.sample(available_types, selected_count)
        
        self.logger.info(f"Pre-selected event types for today: {selected_types}")
        
        # Store selected types for reference
        self.current_quota.metadata = {"pre_selected_types": selected_types}
    
    async def _process_pending_events(self):
        """Process any pending events that need diary generation."""
        # This would typically be called by external event system
        # For now, it's a placeholder for integration with event detection
        pass
    
    async def process_event(self, event_data: EventData) -> DiaryGenerationResult:
        """
        Process an event and potentially generate a diary entry.
        
        Args:
            event_data: Event data to process
            
        Returns:
            DiaryGenerationResult with processing outcome
        """
        try:
            self.daily_stats["total_events_processed"] += 1
            
            # Ensure we have a current quota
            if not self.current_quota:
                await self._reset_daily_quota()
            
            # Step 1: Determine if diary should be generated for this event
            should_generate = await self._should_generate_diary_for_event(event_data)
            
            if not should_generate:
                return DiaryGenerationResult(
                    success=True,
                    error_message="Event skipped - quota reached or random selection declined"
                )
            
            # Step 2: Route event and get context
            routing_result = self.event_router.route_event(event_data)
            
            if not routing_result or not routing_result.get("success"):
                error_msg = routing_result.get("error", "Event routing failed") if routing_result else "Event routing failed"
                return DiaryGenerationResult(
                    success=False,
                    error_message=error_msg
                )
            
            # Step 3: Generate diary entry
            diary_result = await self._generate_diary_entry(event_data, routing_result)
            
            # Step 4: Update statistics and quota
            if diary_result.success and diary_result.diary_entry:
                await self._record_successful_generation(event_data, diary_result)
            else:
                self.daily_stats["failed_generations"] += 1
            
            return diary_result
            
        except Exception as e:
            self.logger.error(f"Error processing event {event_data.event_id}: {str(e)}")
            self.daily_stats["failed_generations"] += 1
            
            return DiaryGenerationResult(
                success=False,
                error_message=f"Processing error: {str(e)}"
            )
    
    async def _should_generate_diary_for_event(self, event_data: EventData) -> bool:
        """
        Determine if a diary should be generated for this event.
        
        Args:
            event_data: Event data to evaluate
            
        Returns:
            True if diary should be generated, False otherwise
        """
        # Check if we have quota remaining
        if not self.current_quota or self.current_quota.current_count >= self.current_quota.total_quota:
            return False
        
        # Get event type for quota tracking
        event_type = self.event_router.event_mapper.get_event_type_for_event(event_data.event_name)
        if not event_type:
            return False
        
        # Check one-diary-per-type constraint
        if event_type in self.current_quota.completed_event_types:
            return False
        
        # Always generate for claimed events
        if self.event_router.is_claimed_event(event_data.event_name):
            self.logger.info(f"Generating diary for claimed event: {event_data.event_name}")
            return True
        
        # Random selection for non-claimed events
        if random.random() < self.config.random_selection_probability:
            self.logger.info(f"Random selection chose to generate diary for: {event_data.event_name}")
            return True
        
        return False
    
    async def _generate_diary_entry(self, event_data: EventData, routing_result: Dict[str, Any]) -> DiaryGenerationResult:
        """
        Generate diary entry using the appropriate agent.
        
        Args:
            event_data: Event data
            routing_result: Result from event routing
            
        Returns:
            DiaryGenerationResult with generation outcome
        """
        try:
            agent_type = routing_result.get("agent_type")
            if not agent_type:
                return DiaryGenerationResult(
                    success=False,
                    error_message="No agent type in routing result"
                )
            
            # Get agent from sub-agent manager
            agent = self.sub_agent_manager.get_agent(agent_type)
            if not agent:
                return DiaryGenerationResult(
                    success=False,
                    error_message=f"Agent not found: {agent_type}",
                    agent_type=agent_type
                )
            
            # Call query function to get context data
            context_data = await self._call_query_function(event_data)
            
            # Generate diary entry using agent
            diary_entry = await agent.process_event(event_data, context_data)
            
            if not diary_entry:
                return DiaryGenerationResult(
                    success=False,
                    error_message="Agent returned no diary entry",
                    agent_type=agent_type
                )
            
            # Validate and format diary entry
            if not self.validator.validate_diary_entry(diary_entry):
                return DiaryGenerationResult(
                    success=False,
                    error_message="Diary entry validation failed",
                    agent_type=agent_type
                )
            
            # Format diary entry (ensure 6-char title, 35-char content)
            formatted_entry = self.formatter.format_diary_entry(diary_entry)
            
            # Store diary entry if storage enabled
            if self.config.storage_enabled:
                await self._store_diary_entry(formatted_entry)
            
            return DiaryGenerationResult(
                success=True,
                diary_entry=formatted_entry,
                agent_type=agent_type,
                event_type=self.event_router.event_mapper.get_event_type_for_event(event_data.event_name),
                generation_time=datetime.now()
            )
            
        except Exception as e:
            return DiaryGenerationResult(
                success=False,
                error_message=f"Generation error: {str(e)}",
                agent_type=routing_result.get("agent_type")
            )
    
    async def _call_query_function(self, event_data: EventData) -> DiaryContextData:
        """
        Call corresponding query function as input parameters.
        
        Args:
            event_data: Event data for context
            
        Returns:
            DiaryContextData with event context
        """
        event_type = self.event_router.event_mapper.get_event_type_for_event(event_data.event_name)
        
        # Check if we have a registered query function for this event type
        query_func = self.query_functions.get(event_type)
        
        if query_func:
            try:
                # Call query function with event data as input parameters
                context_result = await query_func(event_data)
                
                if isinstance(context_result, DiaryContextData):
                    return context_result
                elif isinstance(context_result, dict):
                    # Convert dict to DiaryContextData
                    return DiaryContextData(
                        user_profile=context_result.get("user_profile", {}),
                        event_details=context_result.get("event_details", {}),
                        environmental_context=context_result.get("environmental_context", {}),
                        social_context=context_result.get("social_context", {}),
                        emotional_context=context_result.get("emotional_context", {}),
                        temporal_context=context_result.get("temporal_context", {})
                    )
                
            except Exception as e:
                self.logger.error(f"Error calling query function for {event_type}: {str(e)}")
        
        # Return basic context if no query function or error
        return DiaryContextData(
            user_profile={"user_id": event_data.user_id},
            event_details={"event_name": event_data.event_name, "event_type": event_type},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": event_data.timestamp}
        )
    
    async def _store_diary_entry(self, diary_entry: DiaryEntry):
        """
        Store diary entry using data persistence system.
        
        Args:
            diary_entry: Diary entry to store
        """
        try:
            # Run synchronous save_diary_entry in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None, 
                self.data_persistence.save_diary_entry, 
                diary_entry
            )
            if success:
                self.logger.info(f"Stored diary entry: {diary_entry.entry_id}")
            else:
                self.logger.error(f"Failed to store diary entry {diary_entry.entry_id}")
        except Exception as e:
            self.logger.error(f"Failed to store diary entry {diary_entry.entry_id}: {str(e)}")
    
    async def _record_successful_generation(self, event_data: EventData, diary_result: DiaryGenerationResult):
        """
        Record successful diary generation and update quota.
        
        Args:
            event_data: Original event data
            diary_result: Successful diary generation result
        """
        # Update daily quota
        event_type = diary_result.event_type
        if event_type and self.current_quota:
            self.current_quota.add_diary_entry(event_type)
        
        # Update statistics
        self.daily_stats["diaries_generated"] += 1
        
        if self.event_router.is_claimed_event(event_data.event_name):
            self.daily_stats["claimed_events_processed"] += 1
        else:
            self.daily_stats["random_events_processed"] += 1
        
        # Store result for tracking
        self.daily_generation_results.append(diary_result)
        
        self.logger.info(f"Successfully generated diary for {event_data.event_name} "
                        f"({self.current_quota.current_count}/{self.current_quota.total_quota})")
    
    def register_query_function(self, event_type: str, query_func: Callable):
        """
        Register a query function for a specific event type.
        
        Args:
            event_type: Event type (e.g., "weather_events", "friends_function")
            query_func: Async function to call for querying event context
        """
        self.query_functions[event_type] = query_func
        self.logger.info(f"Registered query function for event type: {event_type}")
    
    def get_daily_status(self) -> Dict[str, Any]:
        """
        Get current daily diary generation status.
        
        Returns:
            Dictionary containing daily status information
        """
        if not self.current_quota:
            return {
                "status": "no_quota_set",
                "message": "Daily quota not yet determined"
            }
        
        return {
            "date": self.current_quota.date.isoformat(),
            "quota": {
                "total": self.current_quota.total_quota,
                "current": self.current_quota.current_count,
                "remaining": self.current_quota.total_quota - self.current_quota.current_count
            },
            "completed_event_types": self.current_quota.completed_event_types,
            "statistics": self.daily_stats.copy(),
            "generation_results": len(self.daily_generation_results),
            "is_complete": self.current_quota.current_count >= self.current_quota.total_quota
        }
    
    def get_generation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get history of diary generation results.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of generation result dictionaries
        """
        results = self.daily_generation_results
        if limit:
            results = results[-limit:]
        
        return [
            {
                "success": result.success,
                "agent_type": result.agent_type,
                "event_type": result.event_type,
                "generation_time": result.generation_time.isoformat() if result.generation_time else None,
                "error_message": result.error_message,
                "has_diary_entry": result.diary_entry is not None
            }
            for result in results
        ]
    
    async def force_generate_diary(self, event_data: EventData) -> DiaryGenerationResult:
        """
        Force generate a diary entry regardless of quota constraints.
        
        Args:
            event_data: Event data to process
            
        Returns:
            DiaryGenerationResult with generation outcome
        """
        self.logger.info(f"Force generating diary for event: {event_data.event_name}")
        
        # Temporarily bypass quota checks
        original_quota = self.current_quota
        temp_quota = DailyQuota(date=datetime.now().date(), total_quota=999)
        self.current_quota = temp_quota
        
        try:
            result = await self.process_event(event_data)
            return result
        finally:
            # Restore original quota
            self.current_quota = original_quota
    
    def get_available_emotional_tags(self) -> List[str]:
        """
        Get list of available emotional tags for diary entries.
        
        Returns:
            List of emotional tag values
        """
        return [tag.value for tag in EmotionalTag]
    
    def select_random_emotional_tags(self, count: int = 1) -> List[EmotionalTag]:
        """
        Select random emotional tags for diary entries.
        
        Args:
            count: Number of tags to select
            
        Returns:
            List of randomly selected emotional tags
        """
        all_tags = list(EmotionalTag)
        selected_count = min(count, len(all_tags))
        return random.sample(all_tags, selected_count)