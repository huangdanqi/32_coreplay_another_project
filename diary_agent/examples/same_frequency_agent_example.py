"""
Example usage of SameFrequencyAgent for generating synchronization diary entries.
Demonstrates integration with existing same_frequency.py module.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.agents.same_frequency_agent import SameFrequencyAgent
from diary_agent.integration.frequency_data_reader import FrequencyDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, PromptConfig


async def create_frequency_agent():
    """Create and configure SameFrequencyAgent instance."""
    
    # Create LLM manager
    llm_manager = LLMConfigManager()
    
    # Create data reader
    data_reader = FrequencyDataReader()
    
    # Create prompt configuration
    prompt_config = PromptConfig(
        agent_type="same_frequency_agent",
        system_prompt="""你是一个专门写同频事件日记的助手。同频事件是指两个密友在5秒内同时被各自主人触发相同的互动，
这种神奇的同步体验会带来特殊的情感连接和惊喜。请生成体现这种奇妙同步感受的日记内容。""",
        user_prompt_template="""请为以下同频事件写一篇日记：

事件名称：{event_name}
时间：{timestamp}
用户资料：{user_profile}
事件详情：{event_details}
社交背景：{social_context}
情感背景：{emotional_context}
时间背景：{temporal_context}

请生成JSON格式的日记，包含：
- title: 标题（最多6个字符）
- content: 内容（最多35个字符，可包含表情符号）
- emotion_tags: 情感标签列表

要求：
1. 强调同步的奇妙感和心灵相通
2. 体现与密友的特殊连接
3. 反映用户的性格特点
4. 表达对这种巧合的惊喜或感动
5. 使用自然的中文表达
6. 可以适当使用表情符号增强同步感""",
        output_format={"title": "string", "content": "string", "emotion_tags": "list"},
        validation_rules={"title_max_length": 6, "content_max_length": 35}
    )
    
    # Create agent
    agent = SameFrequencyAgent(
        agent_type="same_frequency_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )
    
    return agent


async def example_perfect_synchronization():
    """Example: Processing perfect synchronization event."""
    print("=== Perfect Synchronization Event Example ===")
    
    agent = await create_frequency_agent()
    
    # Create event data for perfect sync (within 1 second)
    event_data = EventData(
        event_id="freq_001",
        event_type="frequency",
        event_name="close_friend_frequency",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={
            "friend_id": 2,
            "interaction_type": "摸摸脸",
            "time_difference_seconds": 0.8
        }
    )
    
    try:
        # Process event
        diary_entry = await agent.process_event(event_data)
        
        print(f"Generated Diary Entry:")
        print(f"  Title: {diary_entry.title}")
        print(f"  Content: {diary_entry.content}")
        print(f"  Emotion Tags: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"  Agent Type: {diary_entry.agent_type}")
        print(f"  LLM Provider: {diary_entry.llm_provider}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_excellent_synchronization():
    """Example: Processing excellent synchronization event."""
    print("\n=== Excellent Synchronization Event Example ===")
    
    agent = await create_frequency_agent()
    
    # Create event data for excellent sync (within 2 seconds)
    event_data = EventData(
        event_id="freq_002",
        event_type="frequency",
        event_name="close_friend_frequency",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={
            "friend_id": 3,
            "interaction_type": "拍拍头",
            "time_difference_seconds": 1.5
        }
    )
    
    try:
        # Process event
        diary_entry = await agent.process_event(event_data)
        
        print(f"Generated Diary Entry:")
        print(f"  Title: {diary_entry.title}")
        print(f"  Content: {diary_entry.content}")
        print(f"  Emotion Tags: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"  Agent Type: {diary_entry.agent_type}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_good_synchronization():
    """Example: Processing good synchronization event."""
    print("\n=== Good Synchronization Event Example ===")
    
    agent = await create_frequency_agent()
    
    # Create event data for good sync (within 3 seconds)
    event_data = EventData(
        event_id="freq_003",
        event_type="frequency",
        event_name="close_friend_frequency",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={
            "friend_id": 4,
            "interaction_type": "捏一下",
            "time_difference_seconds": 2.8
        }
    )
    
    try:
        # Process event
        diary_entry = await agent.process_event(event_data)
        
        print(f"Generated Diary Entry:")
        print(f"  Title: {diary_entry.title}")
        print(f"  Content: {diary_entry.content}")
        print(f"  Emotion Tags: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"  Agent Type: {diary_entry.agent_type}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_acceptable_synchronization():
    """Example: Processing acceptable synchronization event."""
    print("\n=== Acceptable Synchronization Event Example ===")
    
    agent = await create_frequency_agent()
    
    # Create event data for acceptable sync (within 5 seconds)
    event_data = EventData(
        event_id="freq_004",
        event_type="frequency",
        event_name="close_friend_frequency",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={
            "friend_id": 5,
            "interaction_type": "摇一摇",
            "time_difference_seconds": 4.2
        }
    )
    
    try:
        # Process event
        diary_entry = await agent.process_event(event_data)
        
        print(f"Generated Diary Entry:")
        print(f"  Title: {diary_entry.title}")
        print(f"  Content: {diary_entry.content}")
        print(f"  Emotion Tags: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"  Agent Type: {diary_entry.agent_type}")
        
    except Exception as e:
        print(f"Error processing event: {e}")


async def example_different_user_roles():
    """Example: Processing events for different user personality roles."""
    print("\n=== Different User Roles Example ===")
    
    agent = await create_frequency_agent()
    
    # Test with lively user
    print("\nLively User:")
    event_lively = EventData(
        event_id="freq_005",
        event_type="frequency",
        event_name="close_friend_frequency",
        timestamp=datetime.now(),
        user_id=2,  # Assume user 2 is lively
        context_data={},
        metadata={
            "friend_id": 1,
            "interaction_type": "摸摸脸",
            "time_difference_seconds": 1.0,
            "user_role": "lively"
        }
    )
    
    try:
        diary_entry = await agent.process_event(event_lively)
        print(f"  Title: {diary_entry.title}")
        print(f"  Content: {diary_entry.content}")
        print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
        
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test with calm user
    print("\nCalm User:")
    event_calm = EventData(
        event_id="freq_006",
        event_type="frequency",
        event_name="close_friend_frequency",
        timestamp=datetime.now(),
        user_id=3,  # Assume user 3 is calm
        context_data={},
        metadata={
            "friend_id": 1,
            "interaction_type": "摸摸脸",
            "time_difference_seconds": 1.0,
            "user_role": "clam"
        }
    )
    
    try:
        diary_entry = await agent.process_event(event_calm)
        print(f"  Title: {diary_entry.title}")
        print(f"  Content: {diary_entry.content}")
        print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
        
    except Exception as e:
        print(f"  Error: {e}")


async def example_batch_synchronization_events():
    """Example: Processing multiple synchronization events in batch."""
    print("\n=== Batch Synchronization Events Example ===")
    
    agent = await create_frequency_agent()
    
    # Create multiple synchronization events with different qualities
    events = [
        EventData(
            event_id="batch_freq_001",
            event_type="frequency",
            event_name="close_friend_frequency",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={
                "friend_id": 2,
                "interaction_type": "摸摸脸",
                "time_difference_seconds": 0.5  # Perfect
            }
        ),
        EventData(
            event_id="batch_freq_002",
            event_type="frequency",
            event_name="close_friend_frequency",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={
                "friend_id": 3,
                "interaction_type": "拍拍头",
                "time_difference_seconds": 2.0  # Good
            }
        ),
        EventData(
            event_id="batch_freq_003",
            event_type="frequency",
            event_name="close_friend_frequency",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={
                "friend_id": 4,
                "interaction_type": "摇一摇",
                "time_difference_seconds": 4.5  # Acceptable
            }
        )
    ]
    
    print(f"Processing {len(events)} synchronization events...")
    
    for i, event in enumerate(events, 1):
        try:
            diary_entry = await agent.process_event(event)
            time_diff = event.metadata["time_difference_seconds"]
            print(f"\nEvent {i} (sync: {time_diff}s):")
            print(f"  Title: {diary_entry.title}")
            print(f"  Content: {diary_entry.content}")
            print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
            
        except Exception as e:
            print(f"  Error: {e}")


def test_supported_events():
    """Test and display supported events."""
    print("\n=== Supported Events ===")
    
    # Create a simple agent instance for testing
    from diary_agent.agents.same_frequency_agent import SameFrequencyAgent
    
    # Mock dependencies for testing
    class MockPromptConfig:
        def __init__(self):
            self.agent_type = "same_frequency_agent"
            self.system_prompt = "test"
            self.user_prompt_template = "test"
            self.output_format = {}
            self.validation_rules = {}
    
    class MockLLMManager:
        pass
    
    class MockDataReader:
        pass
    
    agent = SameFrequencyAgent(
        agent_type="same_frequency_agent",
        prompt_config=MockPromptConfig(),
        llm_manager=MockLLMManager(),
        data_reader=MockDataReader()
    )
    
    supported_events = agent.get_supported_events()
    print(f"SameFrequencyAgent supports {len(supported_events)} event types:")
    for event in supported_events:
        print(f"  - {event}")


def demonstrate_synchronization_quality_assessment():
    """Demonstrate how synchronization quality is assessed."""
    print("\n=== Synchronization Quality Assessment ===")
    
    from diary_agent.integration.frequency_data_reader import FrequencyDataReader
    
    reader = FrequencyDataReader()
    
    test_times = [0.5, 1.2, 2.1, 3.0, 4.8, 6.0]
    
    print("Time Difference -> Quality Assessment:")
    for time_diff in test_times:
        quality = reader._assess_synchronization_quality(time_diff)
        print(f"  {time_diff}s -> {quality}")


async def main():
    """Run all examples."""
    print("Same Frequency Agent Examples")
    print("=" * 50)
    
    # Test supported events first
    test_supported_events()
    
    # Demonstrate synchronization quality assessment
    demonstrate_synchronization_quality_assessment()
    
    # Run async examples
    try:
        await example_perfect_synchronization()
        await example_excellent_synchronization()
        await example_good_synchronization()
        await example_acceptable_synchronization()
        await example_different_user_roles()
        await example_batch_synchronization_events()
        
    except Exception as e:
        print(f"Example execution error: {e}")
        print("Note: Some examples may fail if LLM configuration is not set up")
    
    print("\n" + "=" * 50)
    print("Same Frequency Agent examples completed!")


if __name__ == "__main__":
    asyncio.run(main())