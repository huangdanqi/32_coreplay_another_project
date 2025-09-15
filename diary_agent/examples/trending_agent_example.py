"""
Example usage of TrendingAgent for generating diary entries about trending news and social events.
Demonstrates integration with douyin_news.py module.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from diary_agent.agents.trending_agent import TrendingAgent
from diary_agent.integration.trending_data_reader import TrendingDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, PromptConfig


async def create_trending_agent():
    """Create and configure a TrendingAgent instance."""
    
    # Create LLM manager (mock for example)
    llm_manager = LLMConfigManager()
    
    # Create trending data reader
    data_reader = TrendingDataReader()
    
    # Create prompt configuration
    prompt_config = PromptConfig(
        agent_type="trending_agent",
        system_prompt="你是一个专门写关于热门话题和社会事件日记的助手。你需要根据当前的热门话题生成真实、有情感的日记条目。",
        user_prompt_template="""请为以下事件写一篇日记：

事件类型：{event_name}
时间：{timestamp}
用户信息：{user_profile}
社交背景：{social_context}
情感背景：{emotional_context}

要求：
1. 标题最多6个字符
2. 内容最多35个字符，可以包含表情符号
3. 选择合适的情感标签
4. 体现用户对热门话题的真实感受

请以JSON格式输出：
{{"title": "标题", "content": "内容", "emotion_tags": ["情感标签"]}}""",
        output_format={"title": "string", "content": "string", "emotion_tags": "list"},
        validation_rules={"title_max_length": 6, "content_max_length": 35}
    )
    
    # Create trending agent
    agent = TrendingAgent(
        agent_type="trending_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )
    
    return agent


async def example_celebration_event():
    """Example of processing a celebration trending event."""
    print("=== Celebration Event Example ===")
    
    # Create trending agent
    agent = await create_trending_agent()
    
    # Create sample celebration event data
    event_data = EventData(
        event_id="celebration_001",
        event_type="trending",
        event_name="celebration",
        timestamp=datetime(2024, 1, 15, 14, 30),
        user_id=1,
        context_data={},
        metadata={
            "douyin_file_path": "hewan_emotion_cursor_python/douyin_words_20250826_212805.json",
            "page_size": 50
        }
    )
    
    print(f"Processing event: {event_data.event_name}")
    print(f"Timestamp: {event_data.timestamp}")
    print(f"User ID: {event_data.user_id}")
    
    try:
        # Process the event (this would normally use real LLM)
        # For demo, we'll show the fallback content generation
        context_data = agent.data_reader.read_event_context(event_data)
        fallback_content = agent._generate_trending_fallback_content(event_data, context_data)
        
        print(f"\nGenerated diary content:")
        print(f"Title: {fallback_content['title']}")
        print(f"Content: {fallback_content['content']}")
        print(f"Emotion tags: {fallback_content['emotion_tags']}")
        
        # Show context information
        print(f"\nContext information:")
        print(f"Trending words: {context_data.social_context.get('trending_words', [])[:5]}")
        print(f"Event classification: {context_data.social_context.get('event_classification', 'unknown')}")
        print(f"Social sentiment: {context_data.social_context.get('social_sentiment', 'neutral')}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_disaster_event():
    """Example of processing a disaster trending event."""
    print("\n=== Disaster Event Example ===")
    
    # Create trending agent
    agent = await create_trending_agent()
    
    # Create sample disaster event data
    event_data = EventData(
        event_id="disaster_001",
        event_type="trending",
        event_name="disaster",
        timestamp=datetime(2024, 1, 15, 16, 45),
        user_id=1,
        context_data={},
        metadata={
            "douyin_file_path": "hewan_emotion_cursor_python/douyin_words_20250826_212805.json",
            "page_size": 30
        }
    )
    
    print(f"Processing event: {event_data.event_name}")
    print(f"Timestamp: {event_data.timestamp}")
    print(f"User ID: {event_data.user_id}")
    
    try:
        # Process the event
        context_data = agent.data_reader.read_event_context(event_data)
        fallback_content = agent._generate_trending_fallback_content(event_data, context_data)
        
        print(f"\nGenerated diary content:")
        print(f"Title: {fallback_content['title']}")
        print(f"Content: {fallback_content['content']}")
        print(f"Emotion tags: {fallback_content['emotion_tags']}")
        
        # Show context information
        print(f"\nContext information:")
        print(f"Trending words: {context_data.social_context.get('trending_words', [])[:5]}")
        print(f"Event classification: {context_data.social_context.get('event_classification', 'unknown')}")
        print(f"Social sentiment: {context_data.social_context.get('social_sentiment', 'neutral')}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_emotion_tag_selection():
    """Example of emotion tag selection for different scenarios."""
    print("\n=== Emotion Tag Selection Examples ===")
    
    agent = await create_trending_agent()
    
    # Test different scenarios
    scenarios = [
        {
            "name": "High intensity celebration",
            "event_name": "celebration",
            "social_sentiment": "positive",
            "emotional_intensity": 2.0
        },
        {
            "name": "Moderate celebration",
            "event_name": "celebration", 
            "social_sentiment": "positive",
            "emotional_intensity": 1.5
        },
        {
            "name": "High intensity disaster",
            "event_name": "disaster",
            "social_sentiment": "negative", 
            "emotional_intensity": 1.5
        },
        {
            "name": "Moderate disaster",
            "event_name": "disaster",
            "social_sentiment": "negative",
            "emotional_intensity": 1.0
        }
    ]
    
    for scenario in scenarios:
        from diary_agent.utils.data_models import DiaryContextData
        
        context_data = DiaryContextData(
            user_profile={},
            event_details={},
            environmental_context={},
            social_context={"social_sentiment": scenario["social_sentiment"]},
            emotional_context={"emotional_intensity": scenario["emotional_intensity"]},
            temporal_context={}
        )
        
        tags = agent._select_trending_emotion_tags(scenario["event_name"], context_data)
        
        print(f"{scenario['name']}: {tags[0]}")


async def example_prompt_generation():
    """Example of trending prompt generation."""
    print("\n=== Prompt Generation Example ===")
    
    agent = await create_trending_agent()
    
    # Create sample event and context
    event_data = EventData(
        event_id="prompt_example",
        event_type="trending",
        event_name="celebration",
        timestamp=datetime(2024, 1, 15, 20, 0),
        user_id=1,
        context_data={},
        metadata={}
    )
    
    from diary_agent.utils.data_models import DiaryContextData
    
    context_data = DiaryContextData(
        user_profile={"id": 1, "name": "test_user", "role": "lively"},
        event_details={
            "event_name": "celebration",
            "user_role": "lively",
            "sample_trending_words": ["演唱会", "明星", "可爱"]
        },
        environmental_context={},
        social_context={
            "trending_words": ["演唱会", "明星", "可爱", "挑战", "加油"],
            "trending_topics": ["演唱会", "明星见面会"],
            "social_sentiment": "positive",
            "event_classification": "celebration"
        },
        emotional_context={
            "event_emotional_impact": "high_positive",
            "emotional_intensity": 2.0
        },
        temporal_context={"timestamp": event_data.timestamp}
    )
    
    # Generate prompt
    prompt = agent._prepare_trending_prompt(event_data, context_data)
    
    print("Generated prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)


async def main():
    """Run all trending agent examples."""
    print("Trending Agent Examples")
    print("=" * 50)
    
    await example_celebration_event()
    await example_disaster_event()
    await example_emotion_tag_selection()
    await example_prompt_generation()
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())