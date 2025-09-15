"""
Example usage of the ConditionChecker class.

This example demonstrates how to use the ConditionChecker to evaluate
trigger conditions for diary generation.
"""

import logging
from datetime import datetime, time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.condition import ConditionChecker, TriggerCondition, ConditionType
from utils.data_models import EventData, DailyQuota, ClaimedEvent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_event_handler(event_data: EventData):
    """Example event handler for diary generation."""
    logger.info(f"Handling event: {event_data.event_name} of type {event_data.event_type}")
    logger.info(f"Event context: {event_data.context_data}")
    # In a real implementation, this would trigger the appropriate sub-agent


def main():
    """Main example function."""
    logger.info("=== ConditionChecker Example ===")
    
    # 1. Initialize ConditionChecker with configuration
    config_path = "config/condition_rules.json"
    condition_checker = ConditionChecker(config_path)
    
    logger.info(f"Loaded {len(condition_checker.conditions)} conditions")
    logger.info(f"Loaded {len(condition_checker.claimed_events)} claimed events")
    
    # 2. Set up daily quota (normally done at midnight)
    daily_quota = DailyQuota(
        date=datetime.now(),
        total_quota=3,  # Allow 3 diary entries today
        current_count=0
    )
    condition_checker.set_daily_quota(daily_quota)
    
    # 3. Register event handlers
    condition_checker.register_event_handler("weather", example_event_handler)
    condition_checker.register_event_handler("friends", example_event_handler)
    condition_checker.register_event_handler("dialogue", example_event_handler)
    
    # 4. Create sample events
    events = [
        # Claimed event - should always trigger
        EventData(
            event_id="weather_001",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={
                "temperature": 25,
                "condition": "sunny",
                "city": "Beijing"
            },
            metadata={"source": "weather_api"}
        ),
        
        # Non-claimed event - may trigger based on conditions
        EventData(
            event_id="friend_001",
            event_type="friends",
            event_name="made_new_friend",
            timestamp=datetime.now(),
            user_id=1,
            context_data={
                "friend_name": "Alice",
                "interaction_type": "positive"
            },
            metadata={"source": "social_api"}
        ),
        
        # Another non-claimed event
        EventData(
            event_id="dialogue_001",
            event_type="dialogue",
            event_name="positive_emotional_dialogue",
            timestamp=datetime.now(),
            user_id=1,
            context_data={
                "dialogue_content": "I'm so happy today!",
                "emotion": "joy",
                "duration": 30
            },
            metadata={"source": "dialogue_system"}
        ),
        
        # Event that might not trigger due to quota
        EventData(
            event_id="friend_002",
            event_type="friends",
            event_name="liked_single",
            timestamp=datetime.now(),
            user_id=1,
            context_data={
                "interaction_count": 1,
                "sentiment": "positive"
            },
            metadata={"source": "interaction_tracker"}
        )
    ]
    
    # 5. Process events
    logger.info("\n=== Processing Events ===")
    
    for event in events:
        logger.info(f"\nProcessing event: {event.event_name}")
        
        # Check if conditions are met
        conditions_met = condition_checker.evaluate_conditions(event)
        logger.info(f"Conditions met: {conditions_met}")
        
        # Trigger diary generation if conditions are met
        if conditions_met:
            triggered = condition_checker.trigger_diary_generation(event)
            logger.info(f"Diary generation triggered: {triggered}")
        
        # Show current quota status
        if condition_checker.daily_quota:
            logger.info(f"Daily quota: {condition_checker.daily_quota.current_count}/{condition_checker.daily_quota.total_quota}")
            logger.info(f"Completed event types: {condition_checker.daily_quota.completed_event_types}")
    
    # 6. Demonstrate condition management
    logger.info("\n=== Condition Management ===")
    
    # Get active conditions
    active_conditions = condition_checker.get_active_conditions()
    logger.info(f"Active conditions: {[c.condition_id for c in active_conditions]}")
    
    # Disable a condition
    condition_checker.update_condition_status("social_events", False)
    logger.info("Disabled 'social_events' condition")
    
    # Check active conditions again
    active_conditions = condition_checker.get_active_conditions()
    logger.info(f"Active conditions after update: {[c.condition_id for c in active_conditions]}")
    
    # 7. Demonstrate image processing (basic example)
    logger.info("\n=== Image Processing Example ===")
    
    # Create a simple image event
    image_event = EventData(
        event_id="image_001",
        event_type="weather",
        event_name="weather_detection",
        timestamp=datetime.now(),
        user_id=1,
        context_data={
            "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="  # 1x1 red pixel
        },
        metadata={"source": "camera"}
    )
    
    # Process image for events
    image_info = condition_checker.process_image_for_events(image_event.context_data["image_data"])
    if image_info:
        logger.info(f"Image processed: {image_info['image_size']} pixels, mode: {image_info['image_mode']}")
    
    # 8. Demonstrate time-based conditions
    logger.info("\n=== Time-based Condition Example ===")
    
    # Create a time-based condition for midnight
    midnight_condition = TriggerCondition(
        condition_id="midnight_reset",
        condition_type=ConditionType.TIME_BASED,
        event_types=["all"],
        time_range=(time(0, 0), time(0, 1)),  # 00:00-00:01
        probability=1.0
    )
    
    # Create an event at current time
    current_event = EventData(
        event_id="time_test",
        event_type="system",
        event_name="quota_reset",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={}
    )
    
    # Evaluate time condition
    time_result = condition_checker._evaluate_time_condition(midnight_condition, current_event)
    logger.info(f"Midnight condition evaluation (current time): {time_result}")
    
    # Create an event at midnight
    midnight_event = EventData(
        event_id="midnight_test",
        event_type="system",
        event_name="quota_reset",
        timestamp=datetime.now().replace(hour=0, minute=0, second=30),
        user_id=1,
        context_data={},
        metadata={}
    )
    
    time_result = condition_checker._evaluate_time_condition(midnight_condition, midnight_event)
    logger.info(f"Midnight condition evaluation (00:00:30): {time_result}")
    
    logger.info("\n=== Example Complete ===")


if __name__ == "__main__":
    main()