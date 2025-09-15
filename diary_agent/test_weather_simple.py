#!/usr/bin/env python3
"""
Simple test script for Weather Category Diary (3.1)
Sets up proper Python path and tests weather agent functionality.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add parent directory to path for imports
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

print(f"Added to Python path:")
print(f"  Current dir: {current_dir}")
print(f"  Parent dir: {parent_dir}")

try:
    from diary_agent.agents.weather_agent import WeatherAgent
    from diary_agent.integration.weather_data_reader import WeatherDataReader
    from diary_agent.core.llm_manager import LLMConfigManager
    from diary_agent.utils.data_models import EventData, PromptConfig
    print("✓ Successfully imported diary_agent modules")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Trying alternative import...")
    
    # Try importing directly from subdirectories
    try:
        sys.path.insert(0, str(current_dir / "agents"))
        sys.path.insert(0, str(current_dir / "integration"))
        sys.path.insert(0, str(current_dir / "core"))
        sys.path.insert(0, str(current_dir / "utils"))
        
        from weather_agent import WeatherAgent
        from weather_data_reader import WeatherDataReader
        from llm_manager import LLMConfigManager
        from data_models import EventData, PromptConfig
        print("✓ Successfully imported with alternative path")
    except ImportError as e2:
        print(f"✗ Alternative import also failed: {e2}")
        sys.exit(1)

async def test_weather_agent():
    """Test the weather agent functionality."""
    print("\n=== Testing Weather Category Diary (3.1) ===")
    
    try:
        # Initialize components
        print("Initializing components...")
        llm_manager = LLMConfigManager()
        weather_data_reader = WeatherDataReader()
        
        # Create prompt config
        prompt_config = PromptConfig(
            agent_type="weather_agent",
            system_prompt="Generate weather diary entries",
            user_prompt_template="Event: {event_name}, Time: {timestamp}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
        
        # Create weather agent
        weather_agent = WeatherAgent(
            agent_type="weather_agent",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=weather_data_reader
        )
        
        print("✓ Weather agent initialized successfully")
        
        # Test supported events
        supported_events = weather_agent.get_supported_events()
        print(f"\nSupported weather events: {supported_events}")
        
        # Test weather data reader
        print("\n--- Testing Weather Data Reader ---")
        from datetime import datetime
        
        sample_event = EventData(
            event_id="weather_test_001",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={"user_ip": "8.8.8.8"}
        )
        
        try:
            context_data = weather_data_reader.read_event_context(sample_event)
            print("✓ Successfully read weather context")
            print(f"  City: {context_data.environmental_context.get('city', 'Unknown')}")
            print(f"  Current Weather: {context_data.environmental_context.get('current_weather', 'Unknown')}")
            print(f"  Current Season: {context_data.environmental_context.get('current_season', 'Unknown')}")
            print(f"  User Role: {context_data.user_profile.get('role', 'Unknown')}")
            print(f"  Preference Match: {context_data.event_details.get('preference_match', False)}")
            
        except Exception as e:
            print(f"✗ Error reading weather context: {e}")
        
        # Test diary generation for each event type
        print("\n--- Testing Diary Generation ---")
        
        weather_events = [
            "favorite_weather",
            "dislike_weather", 
            "favorite_season",
            "dislike_season"
        ]
        
        for event_name in weather_events:
            print(f"\nTesting event: {event_name}")
            
            event_data = EventData(
                event_id=f"test_{event_name}",
                event_type="weather",
                event_name=event_name,
                timestamp=datetime.now(),
                user_id=1,
                context_data={},
                metadata={"user_ip": "8.8.8.8"}
            )
            
            try:
                # Generate diary entry
                diary_entry = await weather_agent.process_event(event_data)
                
                print(f"✓ Generated diary entry:")
                print(f"  Title: '{diary_entry.title}' ({len(diary_entry.title)} chars)")
                print(f"  Content: '{diary_entry.content}' ({len(diary_entry.content)} chars)")
                print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
                print(f"  Time: {diary_entry.timestamp}")
                
                # Validate specification requirements
                if len(diary_entry.title) <= 6:
                    print(f"  ✓ Title length OK (≤6 chars)")
                else:
                    print(f"  ✗ Title too long: {len(diary_entry.title)} chars")
                    
                if len(diary_entry.content) <= 35:
                    print(f"  ✓ Content length OK (≤35 chars)")
                else:
                    print(f"  ✗ Content too long: {len(diary_entry.content)} chars")
                    
                if len(diary_entry.emotion_tags) > 0:
                    print(f"  ✓ Emotion tags present")
                else:
                    print(f"  ✗ No emotion tags")
                    
            except Exception as e:
                print(f"✗ Error generating diary for {event_name}: {e}")
        
        print("\n=== Weather Category Diary Test Complete ===")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_weather_agent())
