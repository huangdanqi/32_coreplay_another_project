"""
Example usage of HolidayAgent for generating diary entries about holiday and festival events.
Demonstrates integration with holiday_function.py module.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from diary_agent.agents.holiday_agent import HolidayAgent
from diary_agent.integration.holiday_data_reader import HolidayDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, PromptConfig


async def create_holiday_agent():
    """Create and configure a HolidayAgent instance."""
    
    # Create LLM manager (mock for example)
    llm_manager = LLMConfigManager()
    
    # Create holiday data reader
    data_reader = HolidayDataReader()
    
    # Create prompt configuration
    prompt_config = PromptConfig(
        agent_type="holiday_agent",
        system_prompt="你是一个专门写关于节假日和传统节日日记的助手。你需要根据节假日的不同阶段生成真实、有情感的日记条目。",
        user_prompt_template="""请为以下节假日事件写一篇日记：

事件类型：{event_name}
时间：{timestamp}
用户信息：{user_profile}
节假日背景：{social_context}
情感背景：{emotional_context}
时间背景：{temporal_context}

要求：
1. 标题最多6个字符
2. 内容最多35个字符，可以包含表情符号
3. 选择合适的情感标签
4. 体现用户对节假日的真实感受
5. 符合节假日的文化背景和传统

请以JSON格式输出：
{{"title": "标题", "content": "内容", "emotion_tags": ["情感标签"]}}""",
        output_format={"title": "string", "content": "string", "emotion_tags": "list"},
        validation_rules={"title_max_length": 6, "content_max_length": 35}
    )
    
    # Create holiday agent
    agent = HolidayAgent(
        agent_type="holiday_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )
    
    return agent


async def example_approaching_holiday():
    """Example of processing an approaching holiday event."""
    print("=== Approaching Holiday Example ===")
    
    # Create holiday agent
    agent = await create_holiday_agent()
    
    # Create sample approaching holiday event data (3 days before Spring Festival)
    event_data = EventData(
        event_id="approaching_001",
        event_type="holiday",
        event_name="approaching_holiday",
        timestamp=datetime(2024, 1, 28, 10, 0),
        user_id=1,
        context_data={},
        metadata={"event_date": "2024-01-28"}
    )
    
    print(f"Processing event: {event_data.event_name}")
    print(f"Timestamp: {event_data.timestamp}")
    print(f"User ID: {event_data.user_id}")
    
    try:
        # Process the event (this would normally use real LLM)
        # For demo, we'll show the fallback content generation
        context_data = agent.data_reader.read_event_context(event_data)
        fallback_content = agent._generate_holiday_fallback_content(event_data, context_data)
        
        print(f"\nGenerated diary content:")
        print(f"Title: {fallback_content['title']}")
        print(f"Content: {fallback_content['content']}")
        print(f"Emotion tags: {fallback_content['emotion_tags']}")
        
        # Show context information
        print(f"\nContext information:")
        print(f"Holiday name: {context_data.event_details.get('holiday_name', 'Unknown')}")
        print(f"Days to holiday: {context_data.temporal_context.get('days_to_holiday', 0)}")
        print(f"Cultural significance: {context_data.social_context.get('cultural_significance', 'unknown')}")
        print(f"Typical activities: {context_data.social_context.get('typical_activities', [])}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_during_holiday():
    """Example of processing a during holiday event."""
    print("\n=== During Holiday Example ===")
    
    # Create holiday agent
    agent = await create_holiday_agent()
    
    # Create sample during holiday event data (Spring Festival day)
    event_data = EventData(
        event_id="during_001",
        event_type="holiday",
        event_name="during_holiday",
        timestamp=datetime(2024, 2, 1, 12, 0),
        user_id=1,
        context_data={},
        metadata={"event_date": "2024-02-01"}
    )
    
    print(f"Processing event: {event_data.event_name}")
    print(f"Timestamp: {event_data.timestamp}")
    print(f"User ID: {event_data.user_id}")
    
    try:
        # Process the event
        context_data = agent.data_reader.read_event_context(event_data)
        fallback_content = agent._generate_holiday_fallback_content(event_data, context_data)
        
        print(f"\nGenerated diary content:")
        print(f"Title: {fallback_content['title']}")
        print(f"Content: {fallback_content['content']}")
        print(f"Emotion tags: {fallback_content['emotion_tags']}")
        
        # Show context information
        print(f"\nContext information:")
        print(f"Holiday name: {context_data.event_details.get('holiday_name', 'Unknown')}")
        print(f"Holiday atmosphere: {context_data.environmental_context.get('holiday_atmosphere', 'unknown')}")
        print(f"Celebration scale: {context_data.environmental_context.get('celebration_scale', 'unknown')}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_holiday_ends():
    """Example of processing a holiday ending event."""
    print("\n=== Holiday Ends Example ===")
    
    # Create holiday agent
    agent = await create_holiday_agent()
    
    # Create sample holiday ending event data (3 days after Spring Festival)
    event_data = EventData(
        event_id="ends_001",
        event_type="holiday",
        event_name="holiday_ends",
        timestamp=datetime(2024, 2, 8, 18, 0),
        user_id=1,
        context_data={},
        metadata={"event_date": "2024-02-08"}
    )
    
    print(f"Processing event: {event_data.event_name}")
    print(f"Timestamp: {event_data.timestamp}")
    print(f"User ID: {event_data.user_id}")
    
    try:
        # Process the event
        context_data = agent.data_reader.read_event_context(event_data)
        fallback_content = agent._generate_holiday_fallback_content(event_data, context_data)
        
        print(f"\nGenerated diary content:")
        print(f"Title: {fallback_content['title']}")
        print(f"Content: {fallback_content['content']}")
        print(f"Emotion tags: {fallback_content['emotion_tags']}")
        
        # Show context information
        print(f"\nContext information:")
        print(f"Holiday name: {context_data.event_details.get('holiday_name', 'Unknown')}")
        print(f"Holiday emotional tone: {context_data.emotional_context.get('holiday_emotional_tone', 'unknown')}")
        print(f"Holiday stress level: {context_data.emotional_context.get('holiday_stress_level', 'unknown')}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_emotion_tag_selection():
    """Example of emotion tag selection for different holiday scenarios."""
    print("\n=== Emotion Tag Selection Examples ===")
    
    agent = await create_holiday_agent()
    
    # Test different scenarios
    scenarios = [
        {
            "name": "Approaching Spring Festival (very high anticipation)",
            "event_name": "approaching_holiday",
            "holiday_name": "春节",
            "anticipation_level": "very_high",
            "emotional_intensity": 2.0
        },
        {
            "name": "Approaching regular holiday (moderate anticipation)",
            "event_name": "approaching_holiday",
            "holiday_name": "劳动节",
            "anticipation_level": "high",
            "emotional_intensity": 1.5
        },
        {
            "name": "During major holiday (high joy)",
            "event_name": "during_holiday",
            "holiday_name": "国庆节",
            "anticipation_level": "fulfilled",
            "emotional_intensity": 2.0
        },
        {
            "name": "Holiday ending (sadness)",
            "event_name": "holiday_ends",
            "holiday_name": "春节",
            "anticipation_level": "diminishing",
            "emotional_intensity": 1.5
        }
    ]
    
    for scenario in scenarios:
        from diary_agent.utils.data_models import DiaryContextData
        
        context_data = DiaryContextData(
            user_profile={},
            event_details={"holiday_name": scenario["holiday_name"]},
            environmental_context={},
            social_context={},
            emotional_context={
                "anticipation_level": scenario["anticipation_level"],
                "emotional_intensity": scenario["emotional_intensity"]
            },
            temporal_context={}
        )
        
        tags = agent._select_holiday_emotion_tags(scenario["event_name"], context_data)
        
        print(f"{scenario['name']}: {tags[0]}")


async def example_different_holidays():
    """Example of processing different types of holidays."""
    print("\n=== Different Holiday Types Example ===")
    
    agent = await create_holiday_agent()
    
    holidays = [
        {"name": "春节", "date": "2024-02-01", "type": "traditional_major"},
        {"name": "清明节", "date": "2024-04-05", "type": "traditional_cultural"},
        {"name": "劳动节", "date": "2024-05-01", "type": "international"},
        {"name": "国庆节", "date": "2024-10-01", "type": "national_major"}
    ]
    
    for holiday in holidays:
        print(f"\n--- {holiday['name']} ---")
        
        event_data = EventData(
            event_id=f"holiday_{holiday['name']}",
            event_type="holiday",
            event_name="approaching_holiday",
            timestamp=datetime.strptime(holiday['date'], "%Y-%m-%d"),
            user_id=1,
            context_data={},
            metadata={"event_date": holiday['date']}
        )
        
        try:
            context_data = agent.data_reader.read_event_context(event_data)
            fallback_content = agent._generate_holiday_fallback_content(event_data, context_data)
            
            print(f"Title: {fallback_content['title']}")
            print(f"Content: {fallback_content['content']}")
            print(f"Holiday type: {context_data.social_context.get('holiday_type', 'unknown')}")
            print(f"Cultural significance: {context_data.social_context.get('cultural_significance', 'unknown')}")
            
        except Exception as e:
            print(f"Error processing {holiday['name']}: {e}")


async def example_prompt_generation():
    """Example of holiday prompt generation."""
    print("\n=== Prompt Generation Example ===")
    
    agent = await create_holiday_agent()
    
    # Create sample event and context
    event_data = EventData(
        event_id="prompt_example",
        event_type="holiday",
        event_name="approaching_holiday",
        timestamp=datetime(2024, 1, 28, 15, 30),
        user_id=1,
        context_data={},
        metadata={}
    )
    
    from diary_agent.utils.data_models import DiaryContextData
    
    context_data = DiaryContextData(
        user_profile={"id": 1, "name": "test_user", "role": "lively"},
        event_details={
            "event_name": "approaching_holiday",
            "holiday_name": "春节",
            "user_role": "lively"
        },
        environmental_context={
            "holiday_atmosphere": "anticipatory_festive",
            "cultural_environment": "chinese_traditional"
        },
        social_context={
            "cultural_significance": "highest",
            "typical_activities": ["团圆", "拜年", "放鞭炮", "吃年夜饭"]
        },
        emotional_context={
            "holiday_emotional_tone": "anticipation_excitement",
            "anticipation_level": "very_high",
            "emotional_intensity": 2.0
        },
        temporal_context={
            "timestamp": event_data.timestamp,
            "days_to_holiday": 4
        }
    )
    
    # Generate prompt
    prompt = agent._prepare_holiday_prompt(event_data, context_data)
    
    print("Generated prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)


async def main():
    """Run all holiday agent examples."""
    print("Holiday Agent Examples")
    print("=" * 50)
    
    await example_approaching_holiday()
    await example_during_holiday()
    await example_holiday_ends()
    await example_emotion_tag_selection()
    await example_different_holidays()
    await example_prompt_generation()
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())