"""
Simple example demonstrating the Diary Agent usage.
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


async def main():
    """Demonstrate diary agent usage."""
    
    print("🌟 Diary Agent Demo 🌟")
    print("=" * 50)
    
    # Load prompt configuration
    with open("config/agent_prompts/diary_agent.json", 'r', encoding='utf-8') as f:
        prompt_data = json.load(f)
    
    prompt_config = PromptConfig(
        agent_type=prompt_data["agent_type"],
        system_prompt=prompt_data["system_prompt"],
        user_prompt_template=prompt_data["user_prompt_template"],
        output_format=prompt_data["output_format"],
        validation_rules=prompt_data["validation_rules"]
    )
    
    # Initialize components
    llm_manager = LLMConfigManager()
    data_reader = DiaryDataReader()
    
    # Create test events
    events = [
        {
            "name": "daily_reflection",
            "description": "A peaceful day at home",
            "context": {
                "user_profile": {"personality": "calm", "interests": ["reading", "music"]},
                "environmental_context": {"weather": "sunny", "season": "spring"},
                "emotional_context": {"mood": "content"}
            }
        },
        {
            "name": "personal_milestone",
            "description": "Completed a major project",
            "context": {
                "user_profile": {"personality": "lively", "interests": ["work", "achievement"]},
                "environmental_context": {"weather": "clear", "season": "autumn"},
                "emotional_context": {"mood": "accomplished"}
            }
        },
        {
            "name": "social_interaction",
            "description": "Had dinner with friends",
            "context": {
                "user_profile": {"personality": "lively", "interests": ["socializing", "food"]},
                "environmental_context": {"weather": "pleasant", "season": "summer"},
                "emotional_context": {"mood": "happy"}
            }
        }
    ]
    
    # Test both modes
    for mode, use_llm in [("Default Content Mode", False), ("LLM Mode", True)]:
        print(f"\n📝 {mode}")
        print("-" * 30)
        
        diary_agent = DiaryAgent(
            agent_type="diary_agent",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=data_reader,
            use_llm=use_llm
        )
        
        for i, event_info in enumerate(events, 1):
            event_data = EventData(
                event_id=f"demo_{i}",
                event_type="diary",
                event_name=event_info["name"],
                timestamp=datetime.now(),
                user_id=1,
                context_data=event_info["context"],
                metadata={}
            )
            
            try:
                diary_entry = await diary_agent.process_event(event_data)
                
                print(f"\n📖 Event: {event_info['name']}")
                print(f"   Title: {diary_entry.title}")
                print(f"   Content: {diary_entry.content}")
                print(f"   Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
                print(f"   Source: {diary_entry.llm_provider}")
                
            except Exception as e:
                print(f"\n❌ Error with {event_info['name']}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✨ Demo Complete! ✨")


if __name__ == "__main__":
    asyncio.run(main())
