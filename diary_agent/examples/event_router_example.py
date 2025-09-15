"""
Example usage of the EventRouter class.

This example demonstrates:
1. Setting up an EventRouter with agents and query functions
2. Processing different types of events
3. Handling claimed vs non-claimed events
4. Managing daily quotas
5. Routing events to appropriate sub-agents
"""

from datetime import datetime, date
from typing import Dict, Any

from diary_agent.core.event_router import EventRouter
from diary_agent.utils.data_models import (
    EventData, DiaryContextData, DailyQuota, DiaryEntry, EmotionalTag
)


class MockWeatherAgent:
    """Mock weather agent for demonstration."""
    
    def process_event(self, event_data: EventData, context_data: DiaryContextData) -> DiaryEntry:
        """Process weather event and generate diary entry."""
        print(f"WeatherAgent processing: {event_data.event_name}")
        
        # Generate diary entry based on weather event
        if "favorite" in event_data.event_name:
            title = "好天气"
            content = "今天天气很棒，心情愉快😊"
            emotion = EmotionalTag.HAPPY_JOYFUL
        else:
            title = "坏天气"
            content = "天气不好，有点郁闷😔"
            emotion = EmotionalTag.SAD_UPSET
        
        return DiaryEntry(
            entry_id=f"diary_{event_data.event_id}",
            user_id=event_data.user_id,
            timestamp=datetime.now(),
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title=title,
            content=content,
            emotion_tags=[emotion],
            agent_type="weather_agent",
            llm_provider="mock"
        )


class MockFriendsAgent:
    """Mock friends agent for demonstration."""
    
    def process_event(self, event_data: EventData, context_data: DiaryContextData) -> DiaryEntry:
        """Process friends event and generate diary entry."""
        print(f"FriendsAgent processing: {event_data.event_name}")
        
        if "new_friend" in event_data.event_name:
            title = "新朋友"
            content = "今天认识了新朋友，很开心🎉"
            emotion = EmotionalTag.EXCITED_THRILLED
        else:
            title = "朋友"
            content = "和朋友的互动很有趣😄"
            emotion = EmotionalTag.HAPPY_JOYFUL
        
        return DiaryEntry(
            entry_id=f"diary_{event_data.event_id}",
            user_id=event_data.user_id,
            timestamp=datetime.now(),
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title=title,
            content=content,
            emotion_tags=[emotion],
            agent_type="friends_agent",
            llm_provider="mock"
        )


class MockAdoptionAgent:
    """Mock adoption agent for demonstration."""
    
    def process_event(self, event_data: EventData, context_data: DiaryContextData) -> DiaryEntry:
        """Process adoption event and generate diary entry."""
        print(f"AdoptionAgent processing: {event_data.event_name}")
        
        return DiaryEntry(
            entry_id=f"diary_{event_data.event_id}",
            user_id=event_data.user_id,
            timestamp=datetime.now(),
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title="被领养",
            content="今天被新主人领养了，好兴奋！🥳",
            emotion_tags=[EmotionalTag.EXCITED_THRILLED],
            agent_type="adoption_agent",
            llm_provider="mock"
        )


def mock_weather_query(event_data: EventData) -> DiaryContextData:
    """Mock query function for weather events."""
    print(f"Querying weather data for: {event_data.event_name}")
    
    return DiaryContextData(
        user_profile={"role": "clam", "name": "test_user"},
        event_details={
            "weather": "sunny" if "favorite" in event_data.event_name else "rainy",
            "temperature": 25
        },
        environmental_context={"city": "Beijing", "season": "spring"},
        social_context={},
        emotional_context={"current_mood": "neutral"},
        temporal_context={"time_of_day": "morning"}
    )


def mock_friends_query(event_data: EventData) -> DiaryContextData:
    """Mock query function for friends events."""
    print(f"Querying friends data for: {event_data.event_name}")
    
    return DiaryContextData(
        user_profile={"role": "lively", "name": "test_user"},
        event_details={
            "friend_count": 5,
            "interaction_type": "positive"
        },
        environmental_context={},
        social_context={"recent_interactions": ["chat", "play"]},
        emotional_context={"social_mood": "happy"},
        temporal_context={"interaction_time": "afternoon"}
    )


def mock_adoption_query(event_data: EventData) -> DiaryContextData:
    """Mock query function for adoption events."""
    print(f"Querying adoption data for: {event_data.event_name}")
    
    return DiaryContextData(
        user_profile={"role": "excited", "name": "new_toy"},
        event_details={
            "adoption_time": datetime.now().isoformat(),
            "owner_info": "caring_owner"
        },
        environmental_context={"location": "home"},
        social_context={"family_members": 3},
        emotional_context={"excitement_level": "high"},
        temporal_context={"adoption_date": date.today().isoformat()}
    )


def demonstrate_event_routing():
    """Demonstrate EventRouter functionality."""
    print("=== EventRouter Demonstration ===\n")
    
    # 1. Initialize EventRouter with daily quota
    print("1. Initializing EventRouter...")
    daily_quota = DailyQuota(
        date=date.today(),
        total_quota=3,  # Allow 3 diary entries today
        current_count=0
    )
    
    router = EventRouter(
        events_json_path="diary_agent/events.json",
        daily_quota=daily_quota
    )
    
    # 2. Register agents
    print("2. Registering agents...")
    router.register_agent("weather_agent", MockWeatherAgent())
    router.register_agent("friends_agent", MockFriendsAgent())
    router.register_agent("adoption_agent", MockAdoptionAgent())
    
    # 3. Register query functions
    print("3. Registering query functions...")
    router.register_query_function("weather_events", mock_weather_query)
    router.register_query_function("friends_function", mock_friends_query)
    router.register_query_function("adopted_function", mock_adoption_query)
    
    print(f"Initial routing statistics:")
    stats = router.get_routing_statistics()
    print(f"  Daily quota: {stats['daily_quota']['current_count']}/{stats['daily_quota']['total_quota']}")
    print(f"  Registered agents: {stats['registered_agents']}")
    print(f"  Claimed events: {stats['claimed_events']}")
    print()
    
    # 4. Create test events
    test_events = [
        EventData(
            event_id="event_001",
            event_type="weather_events",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"weather_type": "sunny"},
            metadata={"source": "weather_sensor"}
        ),
        EventData(
            event_id="event_002",
            event_type="friends_function",
            event_name="made_new_friend",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"friend_name": "Alice"},
            metadata={"source": "social_interaction"}
        ),
        EventData(
            event_id="event_003",
            event_type="adopted_function",
            event_name="toy_claimed",  # This is a claimed event
            timestamp=datetime.now(),
            user_id=1,
            context_data={"owner_id": "user_123"},
            metadata={"source": "adoption_system"}
        ),
        EventData(
            event_id="event_004",
            event_type="weather_events",
            event_name="dislike_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"weather_type": "rainy"},
            metadata={"source": "weather_sensor"}
        )
    ]
    
    # 5. Process events
    print("4. Processing events...\n")
    
    for i, event in enumerate(test_events, 1):
        print(f"--- Processing Event {i}: {event.event_name} ---")
        
        # Route the event
        result = router.route_event(event)
        
        if result["success"]:
            if result.get("action") == "skipped":
                print(f"✓ Event skipped: {result['reason']}")
            else:
                diary_entry = result.get("diary_entry")
                if diary_entry:
                    print(f"✓ Diary generated by {result['agent_type']}:")
                    print(f"  Title: {diary_entry.title}")
                    print(f"  Content: {diary_entry.content}")
                    print(f"  Emotion: {[tag.value for tag in diary_entry.emotion_tags]}")
                else:
                    print(f"✓ Event processed but no diary generated")
        else:
            print(f"✗ Error: {result['error']}")
        
        # Show updated statistics
        current_stats = router.get_routing_statistics()
        quota_info = current_stats['daily_quota']
        print(f"  Quota: {quota_info['current_count']}/{quota_info['total_quota']}")
        print(f"  Completed types: {quota_info['completed_event_types']}")
        print()
    
    # 6. Demonstrate quota management
    print("5. Demonstrating quota management...")
    
    # Try to process another weather event (should be skipped due to type already processed)
    duplicate_event = EventData(
        event_id="event_005",
        event_type="weather_events",
        event_name="favorite_season",
        timestamp=datetime.now(),
        user_id=1,
        context_data={"season": "spring"},
        metadata={"source": "calendar"}
    )
    
    print("--- Processing duplicate weather event type ---")
    result = router.route_event(duplicate_event)
    if result["success"] and result.get("action") == "skipped":
        print(f"✓ Event correctly skipped: {result['reason']}")
    
    # 7. Demonstrate daily quota reset
    print("\n6. Demonstrating daily quota reset...")
    print(f"Before reset: {router.daily_quota.current_count}/{router.daily_quota.total_quota}")
    
    router.reset_daily_quota(5)  # Reset with new quota of 5
    print(f"After reset: {router.daily_quota.current_count}/{router.daily_quota.total_quota}")
    
    # 8. Demonstrate random event type selection
    print("\n7. Demonstrating random event type selection...")
    selected_types = router.select_random_event_types_for_today()
    print(f"Randomly selected event types for today: {selected_types}")
    
    print("\n=== Demonstration Complete ===")


def demonstrate_claimed_events():
    """Demonstrate claimed event handling."""
    print("\n=== Claimed Events Demonstration ===\n")
    
    router = EventRouter("diary_agent/events.json")
    
    # Set quota to 0 to test claimed event behavior
    router.daily_quota.total_quota = 0
    router.daily_quota.current_count = 0
    
    print("Daily quota set to 0 - normal events should be skipped")
    
    # Register adoption agent for claimed events
    router.register_agent("adoption_agent", MockAdoptionAgent())
    router.register_query_function("adopted_function", mock_adoption_query)
    
    # Test claimed event (should still be processed despite quota = 0)
    claimed_event = EventData(
        event_id="claimed_001",
        event_type="adopted_function",
        event_name="toy_claimed",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={}
    )
    
    print("Processing claimed event (toy_claimed)...")
    result = router.route_event(claimed_event)
    
    if result["success"] and result.get("diary_generated"):
        print("✓ Claimed event processed successfully despite quota = 0")
        diary = result["diary_entry"]
        print(f"  Generated diary: {diary.title} - {diary.content}")
    else:
        print("✗ Claimed event was not processed correctly")
    
    print("\n=== Claimed Events Demonstration Complete ===")


if __name__ == "__main__":
    # Run demonstrations
    demonstrate_event_routing()
    demonstrate_claimed_events()