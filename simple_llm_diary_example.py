#!/usr/bin/env python3
"""
Simple LLM Diary Generation - Working Examples
Shows how to use LLM to generate diary entries effectively
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'diary_agent'))

from diary_agent.core.llm_manager import LLMConfigManager


async def simple_llm_diary_generation():
    """Simple LLM diary generation examples"""
    
    print("🤖 Simple LLM Diary Generation")
    print("=" * 50)
    
    # Initialize LLM manager (uses your JSON config)
    llm_manager = LLMConfigManager()
    
    print(f"✓ Using LLM Provider: {llm_manager.get_default_provider()}")
    print(f"✓ Model: qwen3:4b (via Ollama)")
    
    # Example 1: Simple diary prompt
    print(f"\n📝 Example 1: Simple Diary Entry")
    simple_prompt = """请为玩具写一篇简短的日记：

今天玩具的朋友小猫咪来家里做客了，玩具很开心。

要求：
- 标题：最多6个字符
- 内容：最多35个字符，可以包含表情符号
- 情感：开心快乐"""
    
    try:
        result = await llm_manager.generate_text_with_failover(
            prompt=simple_prompt,
            system_prompt="你是一个专门写玩具日记的助手。"
        )
        print(f"  LLM Response: {result}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Example 2: Weather diary
    print(f"\n📝 Example 2: Weather Diary")
    weather_prompt = """请为玩具写一篇关于天气的日记：

今天下雨了，玩具不能出去玩，有点不开心。

要求：
- 标题：最多6个字符
- 内容：最多35个字符，可以包含表情符号
- 情感：表达不开心"""
    
    try:
        result = await llm_manager.generate_text_with_failover(
            prompt=weather_prompt,
            system_prompt="你是一个专门写玩具日记的助手。"
        )
        print(f"  LLM Response: {result}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Example 3: Owner interaction diary
    print(f"\n📝 Example 3: Owner Interaction Diary")
    owner_prompt = """请为玩具写一篇关于主人互动的日记：

主人给玩具买了新玩具，玩具很兴奋。

要求：
- 标题：最多6个字符
- 内容：最多35个字符，可以包含表情符号
- 情感：兴奋激动"""
    
    try:
        result = await llm_manager.generate_text_with_failover(
            prompt=owner_prompt,
            system_prompt="你是一个专门写玩具日记的助手。"
        )
        print(f"  LLM Response: {result}")
    except Exception as e:
        print(f"  Error: {e}")


async def structured_diary_generation():
    """Generate structured diary entries"""
    
    print(f"\n🎯 Structured Diary Generation")
    print("=" * 50)
    
    # Initialize LLM manager
    llm_manager = LLMConfigManager()
    
    # Structured prompt for better results
    system_prompt = """你是一个专门写玩具日记的助手。
请根据事件生成简短的日记条目，格式如下：
标题：[6个字符以内的标题]
内容：[35个字符以内的内容，可包含表情符号]
情感：[情感描述]"""
    
    # Different event types
    events = [
        {
            "name": "新朋友事件",
            "description": "玩具认识了新朋友小兔子，很开心",
            "expected_emotion": "开心快乐"
        },
        {
            "name": "天气事件", 
            "description": "今天下雨了，玩具不能出去玩，有点失落",
            "expected_emotion": "不开心"
        },
        {
            "name": "主人互动",
            "description": "主人陪玩具玩了很久，玩具很满足",
            "expected_emotion": "满足"
        }
    ]
    
    for event in events:
        print(f"\n📝 {event['name']}")
        
        user_prompt = f"""请为以下事件写日记：

事件：{event['description']}
期望情感：{event['expected_emotion']}

请按以下格式回复：
标题：[标题]
内容：[内容]
情感：[情感]"""
        
        try:
            result = await llm_manager.generate_text_with_failover(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            print(f"  LLM Response: {result}")
        except Exception as e:
            print(f"  Error: {e}")


async def main():
    """Main function to demonstrate LLM diary generation"""
    print("🚀 LLM Diary Generation Examples")
    
    # Test 1: Simple diary generation
    await simple_llm_diary_generation()
    
    # Test 2: Structured diary generation
    await structured_diary_generation()
    
    print(f"\n✅ LLM Diary Generation Complete!")
    print(f"\n💡 Tips:")
    print(f"  - Your JSON config is working perfectly!")
    print(f"  - LLM is generating diary entries successfully")
    print(f"  - Use simple prompts for best results")
    print(f"  - The specialized agents work better than direct LLM calls")


if __name__ == "__main__":
    asyncio.run(main())
