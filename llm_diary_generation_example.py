#!/usr/bin/env python3
"""
Simple LLM Diary Generation Example
Shows how to use LLM to generate diary entries for different events
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'diary_agent'))

from diary_agent.agents.friends_agent import FriendsAgent
from diary_agent.integration.friends_data_reader import FriendsDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData


async def generate_diary_with_llm():
    """Generate diary entries using LLM for different events"""
    
    print("🤖 LLM Diary Generation Example")
    print("=" * 50)
    
    # Initialize components
    llm_manager = LLMConfigManager()  # Uses your JSON config
    data_reader = FriendsDataReader()
    
    # Load friends agent prompt configuration
    import json
    prompt_config_path = "diary_agent/config/agent_prompts/friends_agent.json"
    with open(prompt_config_path, 'r', encoding='utf-8') as f:
        prompt_config = json.load(f)
    
    # Create friends agent
    friends_agent = FriendsAgent(
        agent_type="friends_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )
    
    print(f"✓ Using LLM Provider: {llm_manager.get_default_provider()}")
    print(f"✓ Model: qwen3:4b (via Ollama)")
    
    # Example 1: New friend event
    print(f"\n📝 Example 1: New Friend Event")
    event_data = EventData(
        event_id="friend_001",
        event_type="friend",
        event_name="made_new_friend",
        timestamp=datetime.now(),
        user_id=1,
        context_data={
            "friend_info": {
                "friend_nickname": "小猫咪",
                "friend_owner_nickname": "小明"
            }
        },
        metadata={
            "friend_nickname": "小猫咪",
            "friend_owner_nickname": "小明",
            "interaction_type": "打招呼",
            "toy_preference": "喜欢"
        }
    )
    
    try:
        diary_entry = await friends_agent.process_event(event_data)
        print(f"  Title: '{diary_entry.title}'")
        print(f"  Content: '{diary_entry.content}'")
        print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"  LLM Provider: {diary_entry.llm_provider}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Example 2: Liked interaction
    print(f"\n📝 Example 2: Liked Interaction")
    event_data = EventData(
        event_id="friend_002",
        event_type="friend",
        event_name="liked_single",
        timestamp=datetime.now(),
        user_id=1,
        context_data={
            "friend_info": {
                "friend_nickname": "小兔子",
                "friend_owner_nickname": "小李"
            }
        },
        metadata={
            "friend_nickname": "小兔子",
            "friend_owner_nickname": "小李",
            "interaction_type": "摸头",
            "toy_preference": "喜欢"
        }
    )
    
    try:
        diary_entry = await friends_agent.process_event(event_data)
        print(f"  Title: '{diary_entry.title}'")
        print(f"  Content: '{diary_entry.content}'")
        print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"  LLM Provider: {diary_entry.llm_provider}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Example 3: Disliked interaction
    print(f"\n📝 Example 3: Disliked Interaction")
    event_data = EventData(
        event_id="friend_003",
        event_type="friend",
        event_name="disliked_single",
        timestamp=datetime.now(),
        user_id=1,
        context_data={
            "friend_info": {
                "friend_nickname": "小老虎",
                "friend_owner_nickname": "小陈"
            }
        },
        metadata={
            "friend_nickname": "小老虎",
            "friend_owner_nickname": "小陈",
            "interaction_type": "拍打",
            "toy_preference": "不喜欢"
        }
    )
    
    try:
        diary_entry = await friends_agent.process_event(event_data)
        print(f"  Title: '{diary_entry.title}'")
        print(f"  Content: '{diary_entry.content}'")
        print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
        print(f"  LLM Provider: {diary_entry.llm_provider}")
    except Exception as e:
        print(f"  Error: {e}")


async def generate_custom_diary():
    """Generate custom diary using LLM directly"""
    
    print(f"\n🎨 Custom LLM Diary Generation")
    print("=" * 50)
    
    # Initialize LLM manager
    llm_manager = LLMConfigManager()
    
    # Custom prompt for diary generation
    system_prompt = """你是一个专门写玩具日记的助手。你需要根据事件生成真实、有情感的日记条目。
日记应该体现玩具的性格和情感，使用自然的中文表达，可以包含表情符号。"""
    
    user_prompt = """请为以下事件写一篇日记：

事件类型：{event_type}
事件描述：{event_description}
玩具性格：{toy_personality}

请生成JSON格式的日记，包含：
- title: 标题（最多6个字符）
- content: 内容（最多35个字符，可包含表情符号）
- emotion_tags: 情感标签列表（从以下选择：生气愤怒、悲伤难过、担忧、焦虑忧愁、惊讶震惊、好奇、羞愧、平静、开心快乐、兴奋激动）

要求：
1. 体现事件的重要性
2. 反映玩具的性格特点
3. 符合事件的情感色彩
4. 使用自然的中文表达
5. 可以适当使用表情符号增强情感表达"""
    
    # Example custom events
    custom_events = [
        {
            "event_type": "天气事件",
            "event_description": "今天下雨了，玩具不能出去玩",
            "toy_personality": "活泼好动"
        },
        {
            "event_type": "主人互动",
            "event_description": "主人给玩具买了新玩具",
            "toy_personality": "好奇"
        },
        {
            "event_type": "朋友互动",
            "event_description": "朋友小猫咪来家里做客",
            "toy_personality": "友好"
        }
    ]
    
    for i, event in enumerate(custom_events, 1):
        print(f"\n📝 Custom Event {i}: {event['event_type']}")
        
        # Format the prompt
        formatted_prompt = user_prompt.format(
            event_type=event['event_type'],
            event_description=event['event_description'],
            toy_personality=event['toy_personality']
        )
        
        try:
            # Generate diary using LLM
            result = await llm_manager.generate_text_with_failover(
                prompt=formatted_prompt,
                system_prompt=system_prompt
            )
            
            print(f"  LLM Response: {result}")
            
            # Try to parse JSON response
            try:
                import json
                diary_data = json.loads(result)
                print(f"  Title: '{diary_data.get('title', 'N/A')}'")
                print(f"  Content: '{diary_data.get('content', 'N/A')}'")
                print(f"  Emotions: {diary_data.get('emotion_tags', [])}")
            except json.JSONDecodeError:
                print(f"  Raw LLM Response: {result}")
                
        except Exception as e:
            print(f"  Error: {e}")


async def main():
    """Main function to demonstrate LLM diary generation"""
    print("🚀 Starting LLM Diary Generation Examples")
    
    # Test 1: Using specialized agents
    await generate_diary_with_llm()
    
    # Test 2: Using LLM directly for custom diaries
    await generate_custom_diary()
    
    print(f"\n✅ LLM Diary Generation Complete!")


if __name__ == "__main__":
    asyncio.run(main())
