#!/usr/bin/env python3
"""
Simple test to verify original topics are being used in diary generation.
Shows which of the 50 trending topics gets selected for diary content.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'diary_agent'))

from diary_agent.agents.trending_agent import TrendingAgent
from diary_agent.integration.trending_data_reader import TrendingDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData


async def test_original_topics():
    """Test that shows which original topics are being used."""
    print("=== Testing Original Topic Usage ===")
    
    # Setup
    trending_data_reader = TrendingDataReader()
    llm_config_manager = LLMConfigManager('config/llm_configuration.json')
    
    # Load trending agent prompt
    with open('diary_agent/config/agent_prompts/trending_agent.json', 'r', encoding='utf-8') as f:
        prompt_config = json.load(f)
    
    trending_agent = TrendingAgent(
        agent_type="trending_agent",
        prompt_config=prompt_config,
        llm_manager=llm_config_manager,
        data_reader=trending_data_reader
    )
    
    # Create test event
    event_data = EventData(
        event_id=f"test_celebration_{int(datetime.now().timestamp())}",
        event_type="trending_events",
        event_name="celebration",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={
            "douyin_file_path": "hewan_emotion_cursor_python/douyin_words_20250826_212805.json",
            "page_size": 50
        }
    )
    
    # Load the original 50 topics first
    print("\n=== Original 50 Trending Topics ===")
    with open('hewan_emotion_cursor_python/douyin_words_20250826_212805.json', 'r', encoding='utf-8') as f:
        douyin_data = json.load(f)
    
    original_topics = [word["word"] for word in douyin_data["words"]]
    for i, topic in enumerate(original_topics, 1):
        print(f"{i:2d}. {topic}")
    
    print(f"\nTotal original topics: {len(original_topics)}")
    
    # Test multiple diary generations to see variety
    print("\n=== Generated Diary Entries ===")
    for i in range(5):
        print(f"\n--- Generation {i+1} ---")
        
        # Read context
        context_data = trending_data_reader.read_event_context(event_data)
        
        # Generate diary entry
        diary_entry = await trending_agent.process_event(event_data)
        
        # Find which original topic was used
        used_topic = None
        for topic in original_topics:
            if topic in diary_entry.content:
                used_topic = topic
                break
        
        # Show results
        print(f"Title: '{diary_entry.title}'")
        print(f"Content: '{diary_entry.content}'")
        print(f"Emotion: {[tag.value for tag in diary_entry.emotion_tags]}")
        
        if used_topic:
            topic_index = original_topics.index(used_topic) + 1
            print(f"Original Topic Used: #{topic_index} - '{used_topic}'")
        else:
            print("Original Topic Used: Not directly found (may be partial match)")
            # Try to find partial matches
            for j, topic in enumerate(original_topics, 1):
                if any(word in diary_entry.content for word in topic.split()):
                    print(f"Possible Match: #{j} - '{topic}'")
                    break


if __name__ == "__main__":
    asyncio.run(test_original_topics())