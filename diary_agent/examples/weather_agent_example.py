"""
Example usage of WeatherAgent and SeasonalAgent.
Demonstrates integration with existing weather_function.py module.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from diary_agent.agents.weather_agent import WeatherAgent, SeasonalAgent
from diary_agent.integration.weather_data_reader import WeatherDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, PromptConfig


async def main():
    """Demonstrate weather agent functionality."""
    print("Weather Agent Example")
    print("====================")
    
    # Initialize components
    llm_manager = LLMConfigManager()
    weather_data_reader = WeatherDataReader()
    
    # Load prompt configuration
    prompt_config_path = Path("diary_agent/config/agent_prompts/weather_agent.json")
    if prompt_config_path.exists():
        with open(prompt_config_path, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        prompt_config = PromptConfig(**prompt_data)
    else:
        # Fallback prompt config
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
    
    # Example weather events
    weather_events = [
        {
            "event_name": "favorite_weather",
            "description": "User's favorite weather condition occurs"
        },
        {
            "event_name": "dislike_weather", 
            "description": "User's disliked weather condition occurs"
        },
        {
            "event_name": "favorite_season",
            "description": "User's favorite season arrives"
        },
        {
            "event_name": "dislike_season",
            "description": "User's disliked season arrives"
        }
    ]
    
    print("\nSupported Events:")
    for event in weather_events:
        print(f"- {event['event_name']}: {event['description']}")
    
    # Test weather data reader
    print("\n" + "="*50)
    print("Testing Weather Data Reader")
    print("="*50)
    
    sample_event = EventData(
        event_id="weather_001",
        event_type="weather",
        event_name="favorite_weather",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={"user_ip": "8.8.8.8"}
    )
    
    try:
        context_data = weather_data_reader.read_event_context(sample_event)
        print(f"✓ Successfully read weather context")
        print(f"  User Profile: {context_data.user_profile.get('name', 'Unknown')} (role: {context_data.user_profile.get('role', 'Unknown')})")
        print(f"  Current Weather: {context_data.environmental_context.get('current_weather', 'Unknown')}")
        print(f"  Current Season: {context_data.environmental_context.get('current_season', 'Unknown')}")
        print(f"  City: {context_data.environmental_context.get('city', 'Unknown')}")
        print(f"  Preference Match: {context_data.event_details.get('preference_match', False)}")
        
    except Exception as e:
        print(f"✗ Error reading weather context: {e}")
    
    # Test emotion tag selection
    print("\n" + "="*50)
    print("Testing Emotion Tag Selection")
    print("="*50)
    
    from diary_agent.utils.data_models import DiaryContextData
    
    test_contexts = [
        {
            "event_name": "favorite_weather",
            "context": DiaryContextData(
                user_profile={},
                event_details={"preference_match": True},
                environmental_context={},
                social_context={},
                emotional_context={"emotional_intensity": 1.5},
                temporal_context={}
            ),
            "expected": "兴奋激动"
        },
        {
            "event_name": "dislike_weather",
            "context": DiaryContextData(
                user_profile={},
                event_details={"preference_match": True},
                environmental_context={},
                social_context={},
                emotional_context={"emotional_intensity": 1.0},
                temporal_context={}
            ),
            "expected": "生气愤怒"
        }
    ]
    
    for test in test_contexts:
        tags = weather_agent._select_weather_emotion_tags(test["event_name"], test["context"])
        print(f"Event: {test['event_name']}")
        print(f"  Selected Tags: {tags}")
        print(f"  Expected: {test['expected']}")
        print(f"  Match: {'✓' if test['expected'] in tags else '✗'}")
    
    # Test fallback content generation
    print("\n" + "="*50)
    print("Testing Fallback Content Generation")
    print("="*50)
    
    fallback_context = DiaryContextData(
        user_profile={},
        event_details={"preference_match": True},
        environmental_context={"current_weather": "Clear", "current_season": "Spring"},
        social_context={},
        emotional_context={},
        temporal_context={}
    )
    
    fallback_content = weather_agent._generate_weather_fallback_content(sample_event, fallback_context)
    print(f"Generated Fallback Content:")
    print(f"  Title: '{fallback_content['title']}' (length: {len(fallback_content['title'])})")
    print(f"  Content: '{fallback_content['content']}' (length: {len(fallback_content['content'])})")
    print(f"  Emotion Tags: {fallback_content['emotion_tags']}")
    
    # Validate format constraints
    title_valid = len(fallback_content['title']) <= 6
    content_valid = len(fallback_content['content']) <= 35
    print(f"  Format Valid: Title {'✓' if title_valid else '✗'}, Content {'✓' if content_valid else '✗'}")
    
    # Test seasonal agent
    print("\n" + "="*50)
    print("Testing Seasonal Agent")
    print("="*50)
    
    seasonal_prompt_config = PromptConfig(
        agent_type="seasonal_agent",
        system_prompt="Generate seasonal diary entries",
        user_prompt_template="Event: {event_name}, Time: {timestamp}",
        output_format={"title": "string", "content": "string", "emotion_tags": "list"},
        validation_rules={"title_max_length": 6, "content_max_length": 35}
    )
    
    seasonal_agent = SeasonalAgent(
        agent_type="seasonal_agent",
        prompt_config=seasonal_prompt_config,
        llm_manager=llm_manager,
        data_reader=weather_data_reader
    )
    
    seasonal_events = seasonal_agent.get_supported_events()
    print(f"Seasonal Agent Events: {seasonal_events}")
    
    # Test weather descriptions
    print("\n" + "="*50)
    print("Testing Weather Descriptions")
    print("="*50)
    
    weather_conditions = ["Clear", "Cloudy", "Rain", "Snow", "Storm"]
    for weather in weather_conditions:
        description = weather_data_reader._get_weather_description(weather)
        print(f"  {weather}: {description}")
    
    seasons = ["Spring", "Summer", "Autumn", "Winter"]
    for season in seasons:
        description = weather_data_reader._get_season_description(season)
        print(f"  {season}: {description}")
    
    print("\n" + "="*50)
    print("Weather Agent Example Complete")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())