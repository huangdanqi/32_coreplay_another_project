"""
Example usage of the Daily Diary Generation Scheduler.

This example demonstrates how to set up and use the daily scheduler
for automatic diary generation following the diary_agent_specifications_en.md process.
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Dict, Any

from diary_agent.core.daily_scheduler import DailyScheduler, DailyScheduleConfig
from diary_agent.core.event_router import EventRouter
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.diary_entry_generator import DiaryEntryGenerator
from diary_agent.core.data_persistence import DiaryPersistenceManager
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, DiaryContextData


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_daily_scheduler() -> DailyScheduler:
    """
    Set up and configure the daily diary generation scheduler.
    
    Returns:
        Configured DailyScheduler instance
    """
    # 1. Configure scheduler settings
    config = DailyScheduleConfig(
        schedule_time=time(0, 0),  # Reset quota at 00:00
        min_quota=0,
        max_quota=5,
        claimed_events_always_generate=True,
        random_selection_probability=0.6,
        alternative_approach_enabled=True,
        max_retries_per_event=3,
        storage_enabled=True
    )
    
    # 2. Initialize core components
    llm_manager = LLMConfigManager("config/llm_configuration.json")
    
    event_router = EventRouter("diary_agent/events.json")
    
    sub_agent_manager = SubAgentManager(llm_manager)
    await sub_agent_manager.initialize_agents()
    
    diary_generator = DiaryEntryGenerator(llm_manager)
    
    data_persistence = DiaryPersistenceManager("diary_agent/data")
    
    # 3. Create scheduler
    scheduler = DailyScheduler(
        event_router=event_router,
        sub_agent_manager=sub_agent_manager,
        diary_generator=diary_generator,
        data_persistence=data_persistence,
        config=config
    )
    
    # 4. Register query functions for different event types
    await register_query_functions(scheduler)
    
    return scheduler


async def register_query_functions(scheduler: DailyScheduler):
    """
    Register query functions for different event types.
    
    Args:
        scheduler: DailyScheduler instance to register functions with
    """
    
    # Weather events query function
    async def weather_query_function(event_data: EventData) -> DiaryContextData:
        """Query function for weather events."""
        logger.info(f"Querying weather data for event: {event_data.event_name}")
        
        # In real implementation, this would call weather_function.py
        # For example: weather_data = weather_function.process_weather_event(event_data.user_id, user_ip)
        
        return DiaryContextData(
            user_profile={
                "user_id": event_data.user_id,
                "role": "clam",  # or "lively"
                "favorite_weathers": ["Clear", "Sunny"],
                "dislike_weathers": ["Rain", "Storm"]
            },
            event_details={
                "event_name": event_data.event_name,
                "event_type": "weather_events"
            },
            environmental_context={
                "current_weather": "Sunny",
                "temperature": 25,
                "city": "Beijing",
                "next_day_weather": "Cloudy"
            },
            social_context={},
            emotional_context={
                "weather_preference_match": True,
                "emotion_change": {"x": 1, "y": -1}
            },
            temporal_context={
                "timestamp": event_data.timestamp,
                "season": "Spring"
            }
        )
    
    # Friends events query function
    async def friends_query_function(event_data: EventData) -> DiaryContextData:
        """Query function for friends events."""
        logger.info(f"Querying friends data for event: {event_data.event_name}")
        
        # In real implementation, this would call friends_function.py
        # For example: friends_data = friends_function.process_friend_event(event_data)
        
        return DiaryContextData(
            user_profile={
                "user_id": event_data.user_id,
                "nickname": "小明"
            },
            event_details={
                "event_name": event_data.event_name,
                "event_type": "friends_function"
            },
            environmental_context={},
            social_context={
                "friend_nickname": "小红",
                "friend_owner_nickname": "小红的主人",
                "interaction_type": "liked",
                "interaction_count": 3
            },
            emotional_context={
                "social_emotion": "happy",
                "friendship_level": "close"
            },
            temporal_context={
                "timestamp": event_data.timestamp
            }
        )
    
    # Holiday events query function
    async def holiday_query_function(event_data: EventData) -> DiaryContextData:
        """Query function for holiday events."""
        logger.info(f"Querying holiday data for event: {event_data.event_name}")
        
        # In real implementation, this would call holiday_function.py
        # For example: holiday_data = holiday_function.process_holiday_event(event_data)
        
        return DiaryContextData(
            user_profile={
                "user_id": event_data.user_id
            },
            event_details={
                "event_name": event_data.event_name,
                "event_type": "holiday_events"
            },
            environmental_context={},
            social_context={},
            emotional_context={
                "holiday_excitement": True
            },
            temporal_context={
                "timestamp": event_data.timestamp,
                "holiday_name": "春节",
                "holiday_phase": "approaching",  # "approaching", "during", "ends"
                "days_to_holiday": 3
            }
        )
    
    # Register all query functions
    scheduler.register_query_function("weather_events", weather_query_function)
    scheduler.register_query_function("friends_function", friends_query_function)
    scheduler.register_query_function("holiday_events", holiday_query_function)
    
    logger.info("Registered query functions for all event types")


async def simulate_daily_diary_generation():
    """
    Simulate a full day of diary generation with various events.
    """
    logger.info("Starting daily diary generation simulation")
    
    # Set up scheduler
    scheduler = await setup_daily_scheduler()
    
    # Start the scheduler
    await scheduler.start_scheduler()
    
    try:
        # Simulate various events throughout the day
        events = [
            EventData(
                event_id="event_001",
                event_type="weather_events",
                event_name="favorite_weather",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"weather": "sunny"},
                metadata={"source": "weather_system"}
            ),
            EventData(
                event_id="event_002",
                event_type="friends_function",
                event_name="made_new_friend",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"friend_id": 123},
                metadata={"source": "social_system"}
            ),
            EventData(
                event_id="event_003",
                event_type="holiday_events",
                event_name="approaching_holiday",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"holiday": "春节"},
                metadata={"source": "calendar_system"}
            ),
            EventData(
                event_id="event_004",
                event_type="weather_events",
                event_name="dislike_weather",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"weather": "rainy"},
                metadata={"source": "weather_system"}
            )
        ]
        
        # Process each event
        results = []
        for event in events:
            logger.info(f"Processing event: {event.event_name}")
            result = await scheduler.process_event(event)
            results.append(result)
            
            if result.success and result.diary_entry:
                logger.info(f"Generated diary entry: {result.diary_entry.title} - {result.diary_entry.content}")
            else:
                logger.info(f"Event processing result: {result.error_message}")
            
            # Small delay between events
            await asyncio.sleep(0.1)
        
        # Display daily status
        status = scheduler.get_daily_status()
        logger.info(f"Daily Status: {status}")
        
        # Display generation history
        history = scheduler.get_generation_history()
        logger.info(f"Generated {len(history)} diary entries today")
        
        # Test force generation (bypassing quota)
        logger.info("Testing force generation...")
        force_event = EventData(
            event_id="force_event_001",
            event_type="weather_events",
            event_name="favorite_season",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"season": "spring"},
            metadata={"source": "force_test"}
        )
        
        force_result = await scheduler.force_generate_diary(force_event)
        if force_result.success:
            logger.info(f"Force generated diary: {force_result.diary_entry.title}")
        
    finally:
        # Stop the scheduler
        await scheduler.stop_scheduler()
        logger.info("Daily diary generation simulation completed")


async def demonstrate_scheduler_features():
    """
    Demonstrate various scheduler features and capabilities.
    """
    logger.info("Demonstrating scheduler features")
    
    scheduler = await setup_daily_scheduler()
    
    # 1. Show available emotional tags
    emotional_tags = scheduler.get_available_emotional_tags()
    logger.info(f"Available emotional tags: {emotional_tags}")
    
    # 2. Select random emotional tags
    random_tags = scheduler.select_random_emotional_tags(count=3)
    logger.info(f"Random emotional tags: {[tag.value for tag in random_tags]}")
    
    # 3. Show daily status before any events
    status = scheduler.get_daily_status()
    logger.info(f"Initial daily status: {status}")
    
    # 4. Manually reset quota for demonstration
    await scheduler._reset_daily_quota()
    logger.info(f"Reset quota to: {scheduler.current_quota.total_quota}")
    
    # 5. Show daily status after quota reset
    status = scheduler.get_daily_status()
    logger.info(f"Status after quota reset: {status}")


async def main():
    """Main example function."""
    logger.info("Daily Scheduler Example Starting")
    
    try:
        # Demonstrate scheduler features
        await demonstrate_scheduler_features()
        
        # Simulate daily diary generation
        await simulate_daily_diary_generation()
        
    except Exception as e:
        logger.error(f"Example execution failed: {str(e)}")
        raise
    
    logger.info("Daily Scheduler Example Completed")


if __name__ == "__main__":
    asyncio.run(main())