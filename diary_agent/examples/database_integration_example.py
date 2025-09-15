"""
Example usage of database integration and compatibility layer.
Demonstrates how to use the database reader for diary generation context.
"""

import sys
import os
from datetime import datetime
import uuid

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.append(root_dir)

from diary_agent.integration.database_reader import DatabaseReader
from diary_agent.integration.database_manager import DataValidator
from diary_agent.utils.data_models import (
    DatabaseConfig, EventData, DiaryEntry, EmotionalTag
)


def main():
    """Demonstrate database integration functionality."""
    print("=== Diary Agent Database Integration Example ===\n")
    
    # Initialize database reader with default configuration
    print("1. Initializing database reader...")
    config = DatabaseConfig()
    db_reader = DatabaseReader(config)
    
    # Test database connection
    print("2. Testing database connection...")
    if db_reader.test_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
        print("Note: This is expected if the database is not set up")
        return
    
    # Example 1: Get user profile
    print("\n3. Getting user profile...")
    user_id = 1
    user_profile = db_reader.get_user_profile(user_id)
    
    if user_profile:
        print(f"✓ User profile retrieved for user {user_id}")
        print(f"  Name: {user_profile['basic_info']['name']}")
        print(f"  Role: {user_profile['basic_info']['role']}")
        print(f"  Emotional state: X={user_profile['emotional_state']['x_value']}, "
              f"Y={user_profile['emotional_state']['y_value']}")
        print(f"  Friend count: {user_profile['social_context']['friend_count']}")
        print(f"  Favorite weathers: {user_profile['preferences']['favorite_weathers']}")
    else:
        print(f"✗ User {user_id} not found")
    
    # Example 2: Get interaction context
    print("\n4. Getting interaction context...")
    interaction_context = db_reader.get_interaction_context(user_id, days=7)
    print(f"✓ Interaction context retrieved")
    print(f"  Total interactions (7 days): {interaction_context['statistics']['total_interactions']}")
    print(f"  Daily average: {interaction_context['statistics']['daily_average']:.2f}")
    print(f"  Neglect indicators: {interaction_context['neglect_indicators']['days_since_last_interaction']} days since last interaction")
    
    # Example 3: Get social context
    print("\n5. Getting social context...")
    social_context = db_reader.get_social_context(user_id)
    print(f"✓ Social context retrieved")
    print(f"  Total friends: {social_context['statistics']['total_friends']}")
    print(f"  Social activity level: {social_context['statistics']['social_activity_level']}")
    print(f"  Recent friendships (30 days): {social_context['statistics']['recent_friendships']}")
    
    # Example 4: Create and validate diary entry
    print("\n6. Creating and validating diary entry...")
    diary_entry = DiaryEntry(
        entry_id=str(uuid.uuid4()),
        user_id=user_id,
        timestamp=datetime.now(),
        event_type="weather",
        event_name="favorite_weather",
        title="晴天",
        content="今天天气很好，心情愉快😊",
        emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
        agent_type="weather_agent",
        llm_provider="qwen"
    )
    
    # Validate diary entry
    validation_errors = DataValidator.validate_diary_entry(diary_entry)
    if validation_errors:
        print(f"✗ Diary entry validation failed: {validation_errors}")
    else:
        print("✓ Diary entry validation passed")
        
        # Store diary entry
        if db_reader.store_diary_entry(diary_entry):
            print("✓ Diary entry stored successfully")
        else:
            print("✗ Failed to store diary entry")
    
    # Example 5: Get complete diary context
    print("\n7. Getting complete diary context...")
    event_data = EventData(
        event_id="weather_event_123",
        event_type="weather",
        event_name="favorite_weather",
        timestamp=datetime.now(),
        user_id=user_id,
        context_data={
            'weather': 'Sunny',
            'temperature': 25,
            'city': 'Beijing',
            'season': 'Spring'
        },
        metadata={'source': 'weather_function.py'}
    )
    
    try:
        diary_context = db_reader.get_diary_context(event_data)
        print("✓ Complete diary context retrieved")
        print(f"  User: {diary_context.user_profile['basic_info']['name']}")
        print(f"  Event: {diary_context.event_details}")
        print(f"  Time context: {diary_context.temporal_context['time_of_day']} on {diary_context.temporal_context['day_of_week']}")
        print(f"  Season: {diary_context.temporal_context['season']}")
    except ValueError as e:
        print(f"✗ Failed to get diary context: {e}")
    
    # Example 6: Get user's diary entries
    print("\n8. Getting user's diary entries...")
    diary_entries = db_reader.get_user_diary_entries(user_id, limit=5)
    print(f"✓ Retrieved {len(diary_entries)} diary entries")
    
    for i, entry in enumerate(diary_entries[:3], 1):  # Show first 3
        print(f"  Entry {i}: '{entry['title']}' - {entry['content']}")
        print(f"    Emotions: {entry.get('emotion_tags', [])}")
        print(f"    Time: {entry['timestamp']}")
    
    print("\n=== Database Integration Example Complete ===")


def demonstrate_data_validation():
    """Demonstrate data validation functionality."""
    print("\n=== Data Validation Examples ===\n")
    
    # Test JSON field validation
    print("1. JSON Field Validation:")
    
    valid_json = '["Sunny", "Clear"]'
    invalid_json = 'invalid_json_string'
    list_data = ["Sunny", "Clear"]
    
    print(f"  Valid JSON string: {DataValidator.validate_json_field(valid_json, 'test')}")
    print(f"  Invalid JSON string: {DataValidator.validate_json_field(invalid_json, 'test')}")
    print(f"  List data: {DataValidator.validate_json_field(list_data, 'test')}")
    print(f"  None value: {DataValidator.validate_json_field(None, 'test')}")
    
    # Test user data validation
    print("\n2. User Data Validation:")
    
    valid_user = {
        'id': 1,
        'name': 'test_user',
        'role': 'clam',
        'favorite_weathers': ["Sunny"]
    }
    
    invalid_user = {
        'id': 1,
        # Missing required fields
        'favorite_weathers': 'invalid_json'
    }
    
    print(f"  Valid user data errors: {DataValidator.validate_user_data(valid_user)}")
    print(f"  Invalid user data errors: {DataValidator.validate_user_data(invalid_user)}")
    
    # Test diary entry validation
    print("\n3. Diary Entry Validation:")
    
    valid_entry = DiaryEntry(
        entry_id="test_123",
        user_id=1,
        timestamp=datetime.now(),
        event_type="weather",
        event_name="favorite_weather",
        title="晴天",
        content="今天天气很好😊",
        emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
        agent_type="weather_agent",
        llm_provider="qwen"
    )
    
    invalid_entry = DiaryEntry(
        entry_id="test_456",
        user_id=1,
        timestamp=datetime.now(),
        event_type="weather",
        event_name="favorite_weather",
        title="这个标题太长了超过限制",  # Too long
        content="这是一个非常非常非常非常非常非常非常非常非常非常长的内容，超过了35个字符的限制",  # Too long
        emotion_tags=[],  # Empty
        agent_type="weather_agent",
        llm_provider="qwen"
    )
    
    print(f"  Valid entry errors: {DataValidator.validate_diary_entry(valid_entry)}")
    print(f"  Invalid entry errors: {DataValidator.validate_diary_entry(invalid_entry)}")


if __name__ == "__main__":
    try:
        main()
        demonstrate_data_validation()
    except Exception as e:
        print(f"Error running example: {e}")
        print("This is expected if the database is not set up or configured differently.")