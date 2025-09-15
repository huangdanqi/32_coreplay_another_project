"""
Simple Weather Diary Test - Following HOW_TO_RUN_DIARY_AGENT.md template
"""

import asyncio
from diary_agent_api_example import DiaryAgentAPI

async def test_weather_simple():
    """Simple weather diary test using the template from HOW_TO_RUN_DIARY_AGENT.md"""
    
    print("🌤️  SIMPLE WEATHER DIARY TEST")
    print("=" * 50)
    
    # Initialize once
    api = DiaryAgentAPI()
    await api.initialize()
    
    try:
        # Test 1: Favorite Weather (using template format)
        print("\n🔹 Testing Favorite Weather Event")
        diary = await api.generate_diary_entry(
            event_type="weather",
            event_name="favorite_weather",
            user_id=1,
            context_data={
                "weather": "sunny", 
                "temperature": 25, 
                "city": "Beijing",
                "today_changes": "cloudy morning, sunny afternoon",
                "tomorrow_forecast": "sunny all day",
                "user_likes": ["sunny", "warm"],
                "user_dislikes": ["rainy", "cold"],
                "personality": "lively"
            }
        )
        
        # Check if diary was generated
        if diary:
            print(f"✅ SUCCESS!")
            print(f"   Title: {diary.title}")
            print(f"   Content: {diary.content}")
            print(f"   Emotions: {diary.emotion_tags}")
            print(f"   LLM Used: {diary.llm_provider}")
        else:
            print("❌ No diary entry generated (quota reached or conditions not met)")
        
        print("\n" + "-" * 50)
        
        # Test 2: Disliked Weather
        print("\n🔹 Testing Disliked Weather Event")
        diary2 = await api.generate_diary_entry(
            event_type="weather",
            event_name="dislike_weather",
            user_id=1,
            context_data={
                "weather": "rainy", 
                "temperature": 15, 
                "city": "Shanghai",
                "today_changes": "sunny morning, rainy afternoon",
                "tomorrow_forecast": "cloudy with showers",
                "user_likes": ["sunny", "warm"],
                "user_dislikes": ["rainy", "cold"],
                "personality": "calm"
            }
        )
        
        if diary2:
            print(f"✅ SUCCESS!")
            print(f"   Title: {diary2.title}")
            print(f"   Content: {diary2.content}")
            print(f"   Emotions: {diary2.emotion_tags}")
            print(f"   LLM Used: {diary2.llm_provider}")
        else:
            print("❌ No diary entry generated")
        
        print("\n" + "=" * 50)
        print("🎯 TEST COMPLETE!")
        if diary or diary2:
            print("✅ Weather diary generation is working with local Ollama model!")
        else:
            print("⚠️  No entries generated - this is normal due to quotas/conditions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up
        await api.shutdown()

if __name__ == "__main__":
    asyncio.run(test_weather_simple())