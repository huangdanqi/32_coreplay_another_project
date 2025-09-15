"""
Example usage of the diary entry generation and formatting system.
Demonstrates how to use DiaryEntryGenerator for creating, validating, and formatting diary entries.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from diary_agent.core.diary_entry_generator import (
    DiaryEntryGenerator, EmotionalContextProcessor, ChineseTextProcessor
)
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, EmotionalTag, DailyQuota
)
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.agents.base_agent import AgentRegistry
from diary_agent.agents.weather_agent import WeatherAgent
from diary_agent.integration.weather_data_reader import WeatherDataReader


async def main():
    """Main example function demonstrating diary entry generation."""
    
    print("=== Diary Entry Generation System Example ===\n")
    
    # 1. Setup components
    print("1. Setting up components...")
    
    # Initialize LLM manager (mock for example)
    llm_config_path = "config/llm_configuration.json"
    llm_manager = LLMConfigManager(llm_config_path)
    
    # Initialize agent registry
    agent_registry = AgentRegistry()
    
    # Create and register weather agent (example)
    weather_data_reader = WeatherDataReader()
    # Note: In real usage, you would properly initialize the weather agent
    # weather_agent = WeatherAgent("weather_agent", prompt_config, llm_manager, weather_data_reader)
    # agent_registry.register_agent(weather_agent)
    
    # Initialize diary entry generator
    storage_path = "diary_agent/examples/temp_diary_storage"
    diary_generator = DiaryEntryGenerator(
        llm_manager=llm_manager,
        agent_registry=agent_registry,
        storage_path=storage_path
    )
    
    print("✓ Components initialized\n")
    
    # 2. Set daily quota
    print("2. Setting daily diary quota...")
    today = datetime.now()
    diary_generator.set_daily_quota(today, 3)  # Allow 3 diary entries today
    
    quota = diary_generator.get_daily_quota(today)
    print(f"✓ Daily quota set: {quota.total_quota} entries allowed")
    print(f"  Current count: {quota.current_count}")
    print(f"  Completed event types: {quota.completed_event_types}\n")
    
    # 3. Create sample event data
    print("3. Creating sample event data...")
    
    sample_events = [
        EventData(
            event_id="weather_001",
            event_type="weather_events",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={
                "weather": "sunny",
                "temperature": 25,
                "city": "Beijing"
            },
            metadata={"source": "weather_api"}
        ),
        EventData(
            event_id="social_001",
            event_type="friends_function",
            event_name="made_new_friend",
            timestamp=datetime.now() + timedelta(hours=1),
            user_id=1,
            context_data={
                "friend_name": "小明",
                "interaction_type": "positive"
            },
            metadata={"source": "social_interaction"}
        ),
        EventData(
            event_id="holiday_001",
            event_type="holiday_events",
            event_name="approaching_holiday",
            timestamp=datetime.now() + timedelta(hours=2),
            user_id=1,
            context_data={
                "holiday_name": "春节",
                "days_until": 7
            },
            metadata={"source": "calendar"}
        )
    ]
    
    print(f"✓ Created {len(sample_events)} sample events\n")
    
    # 4. Demonstrate diary entry generation (mock since we don't have real agents)
    print("4. Demonstrating diary entry generation...")
    
    # Create mock diary entries to demonstrate formatting
    mock_entries = []
    
    for i, event in enumerate(sample_events):
        # Create a mock diary entry with potential formatting issues
        mock_entry = DiaryEntry(
            entry_id="",  # Empty ID to test ID generation
            user_id=event.user_id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            event_name=event.event_name,
            title="今天是一个非常美好的天气，阳光明媚" if i == 0 else f"事件{i+1}",  # Too long title for first entry
            content="今天天气非常好，阳光明媚，微风徐徐，让人心情愉快，想要出去散步，享受这美好的时光" if i == 0 else f"今天发生了{event.event_name}事件",  # Too long content for first entry
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED],
            agent_type=f"{event.event_type}_agent",
            llm_provider="qwen"
        )
        mock_entries.append(mock_entry)
    
    # 5. Demonstrate formatting and validation
    print("5. Demonstrating formatting and validation...")
    
    for i, entry in enumerate(mock_entries):
        print(f"\n--- Processing Entry {i+1} ---")
        print(f"Original title: '{entry.title}' (length: {len(entry.title)})")
        print(f"Original content: '{entry.content}' (length: {len(entry.content)})")
        
        # Apply formatting corrections
        formatted_entry = diary_generator._apply_formatting_corrections(entry)
        
        print(f"Formatted title: '{formatted_entry.title}' (length: {len(formatted_entry.title)})")
        print(f"Formatted content: '{formatted_entry.content}' (length: {len(formatted_entry.content)})")
        print(f"Entry ID: {formatted_entry.entry_id}")
        print(f"Emotion tags: {[tag.value for tag in formatted_entry.emotion_tags]}")
        
        # Validate the formatted entry
        validation_errors = diary_generator.entry_validator.get_validation_errors(formatted_entry)
        if validation_errors:
            print(f"❌ Validation errors: {validation_errors}")
        else:
            print("✅ Entry validation passed")
        
        # Store the formatted entry
        await diary_generator._store_diary_entry(formatted_entry)
        print("✓ Entry stored successfully")
    
    # 6. Demonstrate emotional context processing
    print("\n6. Demonstrating emotional context processing...")
    
    emotion_processor = EmotionalContextProcessor()
    
    for event in sample_events:
        context_data = DiaryContextData(
            user_profile={"role": "clam", "name": "test_user"},
            event_details=event.context_data,
            environmental_context={"location": "Beijing"},
            social_context={"friends_count": 5},
            emotional_context={"mood": "neutral"},
            temporal_context={"season": "spring"}
        )
        
        suggested_emotions = emotion_processor.process_emotional_context(context_data, event)
        print(f"Event: {event.event_name}")
        print(f"Suggested emotions: {[emotion.value for emotion in suggested_emotions]}")
        
        # Validate emotional consistency
        is_consistent = emotion_processor.validate_emotional_consistency(
            suggested_emotions, event.event_name
        )
        print(f"Emotional consistency: {'✅ Valid' if is_consistent else '❌ Invalid'}\n")
    
    # 7. Demonstrate Chinese text processing
    print("7. Demonstrating Chinese text processing...")
    
    chinese_texts = [
        "今天天气很好",
        "今天天气非常好，阳光明媚，微风徐徐，让人心情愉快",
        "Hello World 123",
        "今天temperature是25度",
        "今天天气很好！！！心情愉快？？？"
    ]
    
    for text in chinese_texts:
        chinese_count = ChineseTextProcessor.count_chinese_characters(text)
        is_valid = ChineseTextProcessor.is_valid_chinese_diary_content(text)
        formatted = ChineseTextProcessor.format_chinese_diary_text(text, 10)
        
        print(f"Text: '{text}'")
        print(f"  Chinese characters: {chinese_count}")
        print(f"  Valid diary content: {'✅' if is_valid else '❌'}")
        print(f"  Formatted (max 10): '{formatted}'\n")
    
    # 8. Demonstrate diary loading
    print("8. Demonstrating diary loading...")
    
    loaded_entries = await diary_generator.load_diary_entries(user_id=1, date=today)
    print(f"✓ Loaded {len(loaded_entries)} diary entries for user 1")
    
    for entry in loaded_entries:
        formatted_display = diary_generator.formatter.format_diary_entry_for_display(entry)
        print(f"\n{formatted_display}")
    
    # 9. Show generation statistics
    print("\n9. Generation statistics:")
    stats = diary_generator.get_generation_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 10. Demonstrate daily quota management
    print("\n10. Daily quota management:")
    
    # Simulate quota updates
    test_event = sample_events[0]
    print(f"Before update - Current count: {diary_generator.get_daily_quota(today).current_count}")
    
    diary_generator._update_daily_quota(test_event)
    updated_quota = diary_generator.get_daily_quota(today)
    print(f"After update - Current count: {updated_quota.current_count}")
    print(f"Completed event types: {updated_quota.completed_event_types}")
    
    # Check if we can still generate for the same event type
    can_generate = diary_generator._can_generate_diary(test_event)
    print(f"Can generate for same event type again: {'✅' if can_generate else '❌'}")
    
    # Check if we can generate for a different event type
    different_event = EventData(
        event_id="test_002",
        event_type="trending_events",
        event_name="celebration",
        timestamp=today,
        user_id=1,
        context_data={},
        metadata={}
    )
    can_generate_different = diary_generator._can_generate_diary(different_event)
    print(f"Can generate for different event type: {'✅' if can_generate_different else '❌'}")
    
    print("\n=== Example completed successfully! ===")
    
    # Cleanup
    import shutil
    if Path(storage_path).exists():
        shutil.rmtree(storage_path)
        print("✓ Cleaned up temporary storage")


def demonstrate_formatting_edge_cases():
    """Demonstrate edge cases in diary entry formatting."""
    
    print("\n=== Formatting Edge Cases ===\n")
    
    # Test cases for title formatting
    title_test_cases = [
        "",  # Empty title
        "好",  # Single character
        "今天天气",  # Exactly 4 characters
        "今天天气很好",  # Exactly 6 characters
        "今天天气很好心情愉快",  # Too long
        "Today天气很好",  # Mixed language
        "😊今天很开心😄",  # With emojis
    ]
    
    print("Title formatting test cases:")
    generator = DiaryEntryGenerator(None, None, "temp")
    
    for i, title in enumerate(title_test_cases):
        formatted = generator._format_title(title)
        print(f"  {i+1}. '{title}' -> '{formatted}' (len: {len(formatted)})")
    
    # Test cases for content formatting
    content_test_cases = [
        "",  # Empty content
        "今天天气很好",  # Short content
        "今天天气很好，心情愉快，想要出去散步",  # Medium content
        "今天天气非常好，阳光明媚，微风徐徐，让人心情愉快，想要出去散步，享受这美好的时光，感受大自然的魅力",  # Too long
        "今天天气很好😊🌞心情愉快😄",  # With emojis
        "Today is a beautiful day 今天天气很好",  # Mixed language
    ]
    
    print("\nContent formatting test cases:")
    
    for i, content in enumerate(content_test_cases):
        formatted = generator._format_content(content)
        print(f"  {i+1}. '{content}' -> '{formatted}' (len: {len(formatted)})")
    
    print("\n=== Edge Cases Demo Completed ===")


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Run edge cases demonstration
    demonstrate_formatting_edge_cases()