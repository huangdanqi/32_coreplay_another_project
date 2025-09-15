"""
Test script for Diary Agent demonstrating both LLM and default content modes.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path
sys.path.append('..')

from agents.diary_agent import DiaryAgent
from integration.diary_data_reader import DiaryDataReader
from utils.data_models import EventData, PromptConfig
from core.llm_manager import LLMConfigManager


async def test_diary_agent():
    """Test the diary agent with both LLM and default content modes."""
    
    # Load prompt configuration
    prompt_config_path = Path("config/agent_prompts/diary_agent.json")
    with open(prompt_config_path, 'r', encoding='utf-8') as f:
        prompt_data = json.load(f)
    
    prompt_config = PromptConfig(
        agent_type=prompt_data["agent_type"],
        system_prompt=prompt_data["system_prompt"],
        user_prompt_template=prompt_data["user_prompt_template"],
        output_format=prompt_data["output_format"],
        validation_rules=prompt_data["validation_rules"]
    )
    
    # Initialize components
    llm_manager = LLMConfigManager()  # You may need to configure this based on your LLM setup
    data_reader = DiaryDataReader()
    
    # Create test event data
    test_event = EventData(
        event_id="test_001",
        event_type="diary",
        event_name="daily_reflection",
        timestamp=datetime.now(),
        user_id=1,
        context_data={
            "user_profile": {"personality": "calm", "interests": ["reading", "music"]},
            "event_details": {"description": "A peaceful day at home"},
            "environmental_context": {"weather": "sunny", "season": "spring"},
            "social_context": {"interactions": "minimal"},
            "emotional_context": {"mood": "content"},
            "temporal_context": {"time_of_day": "afternoon"}
        },
        metadata={}
    )
    
    print("=== Testing Diary Agent ===\n")
    
    # Test 1: Default content mode (no LLM)
    print("1. Testing Default Content Mode:")
    print("-" * 40)
    
    diary_agent_default = DiaryAgent(
        agent_type="diary_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader,
        use_llm=False  # Use default content
    )
    
    try:
        diary_entry = await diary_agent_default.process_event(test_event)
        print(f"Title: {diary_entry.title}")
        print(f"Content: {diary_entry.content}")
        print(f"Emotion Tags: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"LLM Provider: {diary_entry.llm_provider}")
        print()
    except Exception as e:
        print(f"Error in default mode: {e}")
        print()
    
    # Test 2: LLM mode
    print("2. Testing LLM Mode:")
    print("-" * 40)
    
    diary_agent_llm = DiaryAgent(
        agent_type="diary_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader,
        use_llm=True  # Use LLM
    )
    
    try:
        diary_entry = await diary_agent_llm.process_event(test_event)
        print(f"Title: {diary_entry.title}")
        print(f"Content: {diary_entry.content}")
        print(f"Emotion Tags: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"LLM Provider: {diary_entry.llm_provider}")
        print()
    except Exception as e:
        print(f"Error in LLM mode: {e}")
        print("(This is expected if LLM is not configured)")
        print()
    
    # Test 3: Different event types with default mode
    print("3. Testing Different Event Types (Default Mode):")
    print("-" * 40)
    
    event_types = [
        "personal_milestone",
        "learning_experience", 
        "social_interaction",
        "work_achievement",
        "hobby_activity"
    ]
    
    for event_type in event_types:
        test_event.event_name = event_type
        test_event.event_id = f"test_{event_type}"
        
        try:
            diary_entry = await diary_agent_default.process_event(test_event)
            print(f"{event_type}:")
            print(f"  Title: {diary_entry.title}")
            print(f"  Content: {diary_entry.content}")
            print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
            print()
        except Exception as e:
            print(f"{event_type}: Error - {e}")
            print()
    
    # Test 4: Mode switching
    print("4. Testing Mode Switching:")
    print("-" * 40)
    
    diary_agent = DiaryAgent(
        agent_type="diary_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader,
        use_llm=False
    )
    
    print(f"Initial mode: {'LLM' if diary_agent.get_llm_mode() else 'Default'}")
    
    # Switch to LLM mode
    diary_agent.set_llm_mode(True)
    print(f"After switching to LLM: {'LLM' if diary_agent.get_llm_mode() else 'Default'}")
    
    # Switch back to default mode
    diary_agent.set_llm_mode(False)
    print(f"After switching to Default: {'LLM' if diary_agent.get_llm_mode() else 'Default'}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_diary_agent())
