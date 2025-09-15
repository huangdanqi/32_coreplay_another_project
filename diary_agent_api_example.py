"""
Diary Agent API Example - Complete Usage Guide

This file shows exactly how to use the diary agent system as an API
with clear input/output examples and all necessary code.

Run this file to see the diary agent in action:
    python diary_agent_api_example.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Import diary agent components
from diary_agent.core.dairy_agent_controller import DairyAgentController
from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag


class DiaryAgentAPI:
    """
    Simple API wrapper for the diary agent system.
    Use this class to integrate diary generation into your applications.
    """
    
    def __init__(self):
        self.controller = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the diary agent system."""
        print("🚀 Initializing Diary Agent System...")
        
        self.controller = DairyAgentController(
            config_dir="diary_agent/config",
            data_dir="diary_agent/data",
            log_level="INFO"
        )
        
        # Initialize and start the system
        init_success = await self.controller.initialize_system()
        if not init_success:
            raise Exception("Failed to initialize diary agent system")
        
        start_success = await self.controller.start_system()
        if not start_success:
            raise Exception("Failed to start diary agent system")
        
        self.is_initialized = True
        print("✅ Diary Agent System initialized successfully!")
    
    async def generate_diary_entry(self, 
                                 event_type: str, 
                                 event_name: str, 
                                 user_id: int, 
                                 context_data: Dict[str, Any]) -> Optional[DiaryEntry]:
        """
        Generate a diary entry from an event.
        
        Args:
            event_type: Type of event ("weather", "friends", "holiday", etc.)
            event_name: Specific event name (from events.json)
            user_id: User identifier
            context_data: Event-specific context data
            
        Returns:
            DiaryEntry object if generated, None if conditions not met
        """
        if not self.is_initialized:
            raise Exception("System not initialized. Call initialize() first.")
        
        # Create event data
        event_data = EventData(
            event_id=f"{event_type}_{user_id}_{datetime.now().timestamp()}",
            event_type=event_type,
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data=context_data,
            metadata={"source": "api_example"}
        )
        
        print(f"📝 Processing event: {event_name}")
        print(f"   Type: {event_type}")
        print(f"   User: {user_id}")
        print(f"   Context: {context_data}")
        
        # Process the event
        diary_entry = await self.controller.process_event(event_data)
        
        if diary_entry:
            print(f"✅ Generated diary entry!")
            print(f"   Title: {diary_entry.title}")
            print(f"   Content: {diary_entry.content}")
            print(f"   Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
        else:
            print("❌ No diary entry generated (conditions not met or quota exceeded)")
        
        return diary_entry
    
    async def shutdown(self):
        """Shutdown the diary agent system."""
        if self.controller:
            await self.controller.stop_system()
            print("🛑 Diary Agent System stopped")


async def example_weather_events():
    """Example: Weather-related events (100% trigger rate)"""
    print("\n" + "="*60)
    print("🌤️  WEATHER EVENTS EXAMPLE")
    print("="*60)
    
    api = DiaryAgentAPI()
    await api.initialize()
    
    try:
        # Example 1: Sunny weather (favorite)
        diary1 = await api.generate_diary_entry(
            event_type="weather",
            event_name="favorite_weather",
            user_id=1,
            context_data={
                "weather": "sunny",
                "temperature": 25,
                "city": "Beijing",
                "mood": "happy"
            }
        )
        
        print("\n" + "-"*40)
        
        # Example 2: Rainy weather (dislike)
        diary2 = await api.generate_diary_entry(
            event_type="weather",
            event_name="dislike_weather",
            user_id=1,
            context_data={
                "weather": "rainy",
                "temperature": 15,
                "city": "Shanghai",
                "mood": "gloomy"
            }
        )
        
    finally:
        await api.shutdown()


async def example_social_events():
    """Example: Social/Friends events (70% trigger rate)"""
    print("\n" + "="*60)
    print("👥 SOCIAL EVENTS EXAMPLE")
    print("="*60)
    
    api = DiaryAgentAPI()
    await api.initialize()
    
    try:
        # Example 1: Made new friend
        diary1 = await api.generate_diary_entry(
            event_type="friends",
            event_name="made_new_friend",
            user_id=2,
            context_data={
                "friend_name": "Alice",
                "interaction_type": "positive",
                "meeting_place": "school",
                "activity": "playing games"
            }
        )
        
        print("\n" + "-"*40)
        
        # Example 2: Liked multiple people
        diary2 = await api.generate_diary_entry(
            event_type="friends",
            event_name="liked_3_to_5",
            user_id=2,
            context_data={
                "people_count": 4,
                "interaction_context": "group activity",
                "activity_type": "sports"
            }
        )
        
    finally:
        await api.shutdown()


async def example_holiday_events():
    """Example: Holiday events (80% trigger rate)"""
    print("\n" + "="*60)
    print("🎉 HOLIDAY EVENTS EXAMPLE")
    print("="*60)
    
    api = DiaryAgentAPI()
    await api.initialize()
    
    try:
        # Example 1: Approaching holiday
        diary1 = await api.generate_diary_entry(
            event_type="holiday",
            event_name="approaching_holiday",
            user_id=3,
            context_data={
                "holiday": "Spring Festival",
                "days_until": 7,
                "preparation_activities": ["shopping", "cleaning"],
                "excitement_level": "high"
            }
        )
        
        print("\n" + "-"*40)
        
        # Example 2: During holiday
        diary2 = await api.generate_diary_entry(
            event_type="holiday",
            event_name="during_holiday",
            user_id=3,
            context_data={
                "holiday": "Christmas",
                "activities": ["gift_exchange", "family_dinner"],
                "mood": "joyful",
                "special_moments": "opened presents"
            }
        )
        
    finally:
        await api.shutdown()


async def example_interactive_events():
    """Example: Interactive/Toy events"""
    print("\n" + "="*60)
    print("🧸 INTERACTIVE EVENTS EXAMPLE")
    print("="*60)
    
    api = DiaryAgentAPI()
    await api.initialize()
    
    try:
        # Example 1: Toy claimed/adopted
        diary1 = await api.generate_diary_entry(
            event_type="adoption",
            event_name="toy_claimed",
            user_id=4,
            context_data={
                "toy_type": "robot",
                "toy_name": "Buddy",
                "claim_reason": "looks cute",
                "first_interaction": "played together"
            }
        )
        
        print("\n" + "-"*40)
        
        # Example 2: Positive dialogue
        diary2 = await api.generate_diary_entry(
            event_type="dialogue",
            event_name="positive_emotional_dialogue",
            user_id=4,
            context_data={
                "conversation_topic": "dreams and goals",
                "emotional_tone": "encouraging",
                "duration_minutes": 15,
                "key_phrases": ["you can do it", "believe in yourself"]
            }
        )
        
    finally:
        await api.shutdown()


async def example_neglect_events():
    """Example: Neglect events (100% trigger rate)"""
    print("\n" + "="*60)
    print("😔 NEGLECT EVENTS EXAMPLE")
    print("="*60)
    
    api = DiaryAgentAPI()
    await api.initialize()
    
    try:
        # Example 1: No dialogue for 1 day
        diary1 = await api.generate_diary_entry(
            event_type="neglect",
            event_name="neglect_1_day_no_dialogue",
            user_id=5,
            context_data={
                "days_since_last_interaction": 1,
                "last_interaction_type": "conversation",
                "current_mood": "lonely",
                "waiting_status": "hoping for attention"
            }
        )
        
        print("\n" + "-"*40)
        
        # Example 2: No interaction for 3 days
        diary2 = await api.generate_diary_entry(
            event_type="neglect",
            event_name="neglect_3_days_no_interaction",
            user_id=5,
            context_data={
                "days_since_last_interaction": 3,
                "last_interaction_type": "playing",
                "current_mood": "sad",
                "thoughts": "wondering if forgotten"
            }
        )
        
    finally:
        await api.shutdown()


async def show_input_output_format():
    """Show the exact input/output data structures"""
    print("\n" + "="*60)
    print("📋 INPUT/OUTPUT FORMAT REFERENCE")
    print("="*60)
    
    print("\n🔹 INPUT FORMAT (EventData):")
    print("""
    {
        "event_id": "weather_1_1735689600.123",     # Unique identifier
        "event_type": "weather",                     # Event category
        "event_name": "favorite_weather",            # Specific event
        "timestamp": "2024-01-01T12:00:00",         # When it happened
        "user_id": 1,                               # User identifier
        "context_data": {                           # Event-specific data
            "weather": "sunny",
            "temperature": 25,
            "city": "Beijing"
        },
        "metadata": {                               # Additional context
            "source": "your_app",
            "priority": "normal"
        }
    }
    """)
    
    print("\n🔹 OUTPUT FORMAT (DiaryEntry or None):")
    print("""
    {
        "entry_id": "diary_123456",                 # Generated entry ID
        "user_id": 1,                              # User ID
        "timestamp": "2024-01-01T12:05:00",        # Generation time
        "event_type": "weather",                   # Event category
        "event_name": "favorite_weather",          # Specific event
        "title": "晴天好心情",                      # Max 6 characters
        "content": "今天阳光明媚，心情特别好！😊",    # Max 35 characters
        "emotion_tags": ["开心快乐"],               # Emotional tags
        "agent_type": "weather_agent",             # Which agent generated
        "llm_provider": "qwen"                     # Which LLM was used
    }
    """)
    
    print("\n🔹 VALID EVENT TYPES & NAMES:")
    print("""
    Weather Events (100% trigger):
    - event_type="weather", event_name="favorite_weather"
    - event_type="weather", event_name="dislike_weather"
    
    Social Events (70% trigger):
    - event_type="friends", event_name="made_new_friend"
    - event_type="friends", event_name="liked_single"
    
    Holiday Events (80% trigger):
    - event_type="holiday", event_name="approaching_holiday"
    - event_type="holiday", event_name="during_holiday"
    
    Interactive Events:
    - event_type="adoption", event_name="toy_claimed"
    - event_type="dialogue", event_name="positive_emotional_dialogue"
    
    Neglect Events (100% trigger):
    - event_type="neglect", event_name="neglect_1_day_no_dialogue"
    - event_type="neglect", event_name="neglect_3_days_no_interaction"
    """)


async def main():
    """Run all examples"""
    print("🎯 DIARY AGENT API EXAMPLES")
    print("This demonstrates how to use the diary agent in your applications")
    
    # Setup logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Show input/output format first
        await show_input_output_format()
        
        # Run examples for different event types
        await example_weather_events()
        await example_social_events()
        await example_holiday_events()
        await example_interactive_events()
        await example_neglect_events()
        
        print("\n" + "="*60)
        print("✅ ALL EXAMPLES COMPLETED!")
        print("="*60)
        print("\n📖 How to use in your application:")
        print("1. Create DiaryAgentAPI instance")
        print("2. Call await api.initialize()")
        print("3. Call await api.generate_diary_entry() with your event data")
        print("4. Call await api.shutdown() when done")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())