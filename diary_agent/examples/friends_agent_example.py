"""
Example usage of FriendsAgent for generating friend-related diary entries.
Demonstrates integration with existing friends_function.py module.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.agents.friends_agent import FriendsAgent
from diary_agent.integration.friends_data_reader import FriendsDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, PromptConfig


async def create_friends_agent():
    """Create and configure FriendsAgent instance."""
    
    # Create LLM manager
    llm_manager = LLMConfigManager()
    
    # Create data reader
    data_reader = FriendsDataReader()
    
    # Create prompt configuration
    prompt_config = PromptConfig(
        agent_type="friends_agent",
        system_prompt="""你是一个专门写朋友相关日记的助手。你需要根据朋友事件生成真实、有情感的日记条目。
朋友关系的变化会带来不同的情感体验，包括交新朋友的喜悦、被删除好友的失落、朋友互动的开心或不快。
请生成符合用户性格和事件情境的日记内容。""",
        user_prompt_template="""请为以下朋友事件写一篇日记：

事件名称：{event_name}
时间：{timestamp}
用户资料：{user_profile}
事件详情：{event_details}
社交背景：{social_context}
情感背景：{emotional_context}

请生成JSON格式的日记，包含：
- title: 标题（最多6个字符）
- content: 内容（最多35个字符，可包含表情符号）
- emotion_tags: 情感标签列表

要求：
1. 体现朋友关系的重要性
2. 反映用户的性格特点（活泼/平和）
3. 符合事件的情感色彩
4. 使用自然的中文表达
5. 可以适当使用表情符号增强情感表达""",
        output_format={"title": "string", "content": "string", "emotion_tags": "list"},
        validation_rules={"title_max_length": 6, "content_max_length": 35}
    )
    
    # Create agent
    agent = FriendsAgent(
        agent_type="friends_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )
    
    return agent


async def example_made_new_friend():
    """Example: Processing made_new_friend event."""
    print("=== Made New Friend Event Example ===")
    
    agent = await create_friends_agent()
    
    # Create event data
    event_data = EventData(
        event_id="friend_001",
        event_type="friend",
        event_name="made_new_friend",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={"friend_id": 2}
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


async def example_friend_deleted():
    """Example: Processing friend_deleted event."""
    print("\n=== Friend Deleted Event Example ===")
    
    agent = await create_friends_agent()
    
    # Create event data
    event_data = EventData(
        event_id="friend_002",
        event_type="friend",
        event_name="friend_deleted",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={"friend_id": 3}
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


async def example_liked_interaction():
    """Example: Processing liked interaction event."""
    print("\n=== Liked Interaction Event Example ===")
    
    agent = await create_friends_agent()
    
    # Create event data for multiple interactions
    event_data = EventData(
        event_id="friend_003",
        event_type="friend",
        event_name="liked_3_to_5",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={
            "friend_id": 2,
            "interaction_type": "摸摸脸",
            "interaction_count": 4
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


async def example_disliked_interaction():
    """Example: Processing disliked interaction event."""
    print("\n=== Disliked Interaction Event Example ===")
    
    agent = await create_friends_agent()
    
    # Create event data for disliked interaction
    event_data = EventData(
        event_id="friend_004",
        event_type="friend",
        event_name="disliked_5_plus",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={
            "friend_id": 4,
            "interaction_type": "捏一下",
            "interaction_count": 6
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


async def example_batch_processing():
    """Example: Processing multiple friend events in batch."""
    print("\n=== Batch Processing Example ===")
    
    agent = await create_friends_agent()
    
    # Create multiple events
    events = [
        EventData(
            event_id="batch_001",
            event_type="friend",
            event_name="made_new_friend",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={"friend_id": 5}
        ),
        EventData(
            event_id="batch_002",
            event_type="friend",
            event_name="liked_single",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={"friend_id": 5, "interaction_type": "拍拍头"}
        ),
        EventData(
            event_id="batch_003",
            event_type="friend",
            event_name="disliked_single",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={"friend_id": 6, "interaction_type": "摇一摇"}
        )
    ]
    
    print(f"Processing {len(events)} friend events...")
    
    for i, event in enumerate(events, 1):
        try:
            diary_entry = await agent.process_event(event)
            print(f"\nEvent {i} ({event.event_name}):")
            print(f"  Title: {diary_entry.title}")
            print(f"  Content: {diary_entry.content}")
            print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
            
        except Exception as e:
            print(f"  Error: {e}")


def test_supported_events():
    """Test and display supported events."""
    print("\n=== Supported Events ===")
    
    # Create a simple agent instance for testing
    from diary_agent.agents.friends_agent import FriendsAgent
    
    # Mock dependencies for testing
    class MockPromptConfig:
        def __init__(self):
            self.agent_type = "friends_agent"
            self.system_prompt = "test"
            self.user_prompt_template = "test"
            self.output_format = {}
            self.validation_rules = {}
    
    class MockLLMManager:
        pass
    
    class MockDataReader:
        pass
    
    agent = FriendsAgent(
        agent_type="friends_agent",
        prompt_config=MockPromptConfig(),
        llm_manager=MockLLMManager(),
        data_reader=MockDataReader()
    )
    
    supported_events = agent.get_supported_events()
    print(f"FriendsAgent supports {len(supported_events)} event types:")
    for event in supported_events:
        print(f"  - {event}")


async def main():
    """Run all examples."""
    print("Friends Agent Examples")
    print("=" * 50)
    
    # Test supported events first
    test_supported_events()
    
    # Run async examples
    try:
        await example_made_new_friend()
        await example_friend_deleted()
        await example_liked_interaction()
        await example_disliked_interaction()
        await example_batch_processing()
        
    except Exception as e:
        print(f"Example execution error: {e}")
        print("Note: Some examples may fail if LLM configuration is not set up")
    
    print("\n" + "=" * 50)
    print("Friends Agent examples completed!")


if __name__ == "__main__":
    asyncio.run(main())