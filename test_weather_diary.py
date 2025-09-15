"""
Test Weather Category Diary Generation with Local Ollama Model

This script tests the weather diary functionality as specified:
- Trigger Condition: After hitting (matching) liked/disliked weather
- Data to Query: Today's complete weather changes and tomorrow's weather changes
- Content to Include: City, weather changes, IP's liked weather, IP's disliked weather, IP's personality type
"""

import asyncio
import logging
from datetime import datetime
from diary_agent_api_example import DiaryAgentAPI

async def test_weather_diary_comprehensive():
    """Test comprehensive weather diary generation with all required data elements."""
    
    print("🌤️  TESTING WEATHER CATEGORY DIARY")
    print("=" * 60)
    print("Testing requirements:")
    print("- Trigger: After hitting liked/disliked weather")
    print("- Data: Today's and tomorrow's weather changes")
    print("- Content: City, weather changes, preferences, personality")
    print("=" * 60)
    
    # Initialize the diary agent API
    api = DiaryAgentAPI()
    await api.initialize()
    
    try:
        # Test 1: Favorite Weather Event (Sunny Day)
        print("\n🔹 TEST 1: FAVORITE WEATHER (Sunny)")
        print("-" * 40)
        
        diary1 = await api.generate_diary_entry(
            event_type="weather",
            event_name="favorite_weather",
            user_id=1,
            context_data={
                # Current weather data
                "weather": "sunny",
                "temperature": 25,
                "humidity": 60,
                "wind_speed": 5,
                "city": "Beijing",
                
                # Weather changes (today)
                "today_weather_changes": {
                    "morning": {"weather": "cloudy", "temp": 18},
                    "afternoon": {"weather": "sunny", "temp": 25},
                    "evening": {"weather": "clear", "temp": 22}
                },
                
                # Tomorrow's weather forecast
                "tomorrow_weather": {
                    "morning": {"weather": "sunny", "temp": 20},
                    "afternoon": {"weather": "sunny", "temp": 28},
                    "evening": {"weather": "partly_cloudy", "temp": 24}
                },
                
                # User preferences (IP data)
                "user_preferences": {
                    "liked_weather": ["sunny", "clear", "warm"],
                    "disliked_weather": ["rainy", "stormy", "cold"],
                    "personality_type": "lively",  # or "calm"
                    "role": "lively"
                },
                
                # Additional context
                "weather_match": "favorite",
                "emotional_impact": "positive",
                "season": "spring"
            }
        )
        
        if diary1:
            print(f"✅ Generated diary entry!")
            print(f"   Title: {diary1.title}")
            print(f"   Content: {diary1.content}")
            print(f"   Emotions: {[tag.value if hasattr(tag, 'value') else str(tag) for tag in diary1.emotion_tags]}")
            print(f"   Agent: {diary1.agent_type}")
            print(f"   LLM Provider: {diary1.llm_provider}")
        else:
            print("❌ No diary entry generated")
        
        print("\n" + "-" * 40)
        
        # Test 2: Disliked Weather Event (Rainy Day)
        print("\n🔹 TEST 2: DISLIKED WEATHER (Rainy)")
        print("-" * 40)
        
        diary2 = await api.generate_diary_entry(
            event_type="weather",
            event_name="dislike_weather",
            user_id=1,
            context_data={
                # Current weather data
                "weather": "rainy",
                "temperature": 15,
                "humidity": 85,
                "wind_speed": 12,
                "city": "Shanghai",
                
                # Weather changes (today)
                "today_weather_changes": {
                    "morning": {"weather": "cloudy", "temp": 18},
                    "afternoon": {"weather": "light_rain", "temp": 16},
                    "evening": {"weather": "heavy_rain", "temp": 15}
                },
                
                # Tomorrow's weather forecast
                "tomorrow_weather": {
                    "morning": {"weather": "rainy", "temp": 14},
                    "afternoon": {"weather": "cloudy", "temp": 17},
                    "evening": {"weather": "partly_cloudy", "temp": 19}
                },
                
                # User preferences (IP data)
                "user_preferences": {
                    "liked_weather": ["sunny", "clear", "warm"],
                    "disliked_weather": ["rainy", "stormy", "cold"],
                    "personality_type": "calm",  # Different personality
                    "role": "calm"
                },
                
                # Additional context
                "weather_match": "dislike",
                "emotional_impact": "negative",
                "season": "autumn"
            }
        )
        
        if diary2:
            print(f"✅ Generated diary entry!")
            print(f"   Title: {diary2.title}")
            print(f"   Content: {diary2.content}")
            print(f"   Emotions: {[tag.value if hasattr(tag, 'value') else str(tag) for tag in diary2.emotion_tags]}")
            print(f"   Agent: {diary2.agent_type}")
            print(f"   LLM Provider: {diary2.llm_provider}")
        else:
            print("❌ No diary entry generated")
        
        print("\n" + "-" * 40)
        
        # Test 3: Complex Weather Scenario (Mixed conditions)
        print("\n🔹 TEST 3: COMPLEX WEATHER SCENARIO")
        print("-" * 40)
        
        diary3 = await api.generate_diary_entry(
            event_type="weather",
            event_name="favorite_weather",
            user_id=2,
            context_data={
                # Current weather data
                "weather": "partly_cloudy",
                "temperature": 22,
                "humidity": 70,
                "wind_speed": 8,
                "city": "Guangzhou",
                
                # Complex weather changes (today)
                "today_weather_changes": {
                    "early_morning": {"weather": "foggy", "temp": 16},
                    "morning": {"weather": "cloudy", "temp": 19},
                    "noon": {"weather": "sunny", "temp": 24},
                    "afternoon": {"weather": "partly_cloudy", "temp": 22},
                    "evening": {"weather": "clear", "temp": 20},
                    "night": {"weather": "clear", "temp": 18}
                },
                
                # Tomorrow's detailed forecast
                "tomorrow_weather": {
                    "morning": {"weather": "sunny", "temp": 21, "humidity": 65},
                    "afternoon": {"weather": "hot", "temp": 30, "humidity": 55},
                    "evening": {"weather": "warm", "temp": 26, "humidity": 60}
                },
                
                # Detailed user preferences
                "user_preferences": {
                    "liked_weather": ["sunny", "clear", "warm", "partly_cloudy"],
                    "disliked_weather": ["rainy", "stormy", "cold", "foggy"],
                    "personality_type": "lively",
                    "role": "lively",
                    "weather_sensitivity": "high",
                    "preferred_temperature_range": [20, 28]
                },
                
                # Rich context
                "weather_match": "partial_favorite",
                "emotional_impact": "positive",
                "season": "summer",
                "location_context": {
                    "region": "South China",
                    "climate_type": "subtropical",
                    "typical_weather": "humid and warm"
                }
            }
        )
        
        if diary3:
            print(f"✅ Generated diary entry!")
            print(f"   Title: {diary3.title}")
            print(f"   Content: {diary3.content}")
            print(f"   Emotions: {[tag.value if hasattr(tag, 'value') else str(tag) for tag in diary3.emotion_tags]}")
            print(f"   Agent: {diary3.agent_type}")
            print(f"   LLM Provider: {diary3.llm_provider}")
        else:
            print("❌ No diary entry generated")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        generated_count = sum([1 for diary in [diary1, diary2, diary3] if diary is not None])
        print(f"✅ Generated {generated_count}/3 diary entries")
        print(f"🤖 Using local Ollama model: {diary1.llm_provider if diary1 else 'N/A'}")
        
        if generated_count > 0:
            print("\n📋 Content Analysis:")
            for i, diary in enumerate([diary1, diary2, diary3], 1):
                if diary:
                    print(f"   Test {i}: Title='{diary.title}' ({len(diary.title)} chars), Content='{diary.content}' ({len(diary.content)} chars)")
        
        print("\n✅ Weather diary testing completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await api.shutdown()


async def main():
    """Main test function."""
    
    # Setup logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    
    print("🎯 WEATHER CATEGORY DIARY TEST")
    print("Testing with local Ollama Qwen3 model")
    print("Following HOW_TO_RUN_DIARY_AGENT.md template")
    print()
    
    try:
        await test_weather_diary_comprehensive()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Check Qwen3 model: ollama list")
        print("3. Test connection: python test_ollama_connection.py")
        print("4. Verify diary agent setup: python diary_agent_api_example.py")


if __name__ == "__main__":
    # Run the weather diary test
    asyncio.run(main())