#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test script for dialogue agent using local Ollama LLM.
This script tests both positive and negative emotional dialogue events.
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dialogue_agent_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockDialogueEvent:
    """Mock dialogue event for testing."""
    
    def __init__(self, event_type: str = "positive_emotional_dialogue", user_id: int = 1):
        self.event_type = event_type
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.payload = {
            "event_type": event_type,
            "user_id": user_id,
            "dialogue_message": "今天很开心！",
            "owner_emotion": "开心快乐",
            "event_summary": "主人情绪积极的对话",
            "event_title": "快乐对话",
            "content_topic": "分享快乐",
            "owner_emotion_state": "开心快乐"
        }

async def test_dialogue_agent():
    """Test dialogue agent with local Ollama LLM."""
    print("=== Dialogue Agent Test with Local Ollama LLM ===")
    print("=" * 60)
    
    try:
        # Import the dialogue agent components
        from diary_agent.agents.dialogue_agent import DialogueAgent
        from diary_agent.core.llm_manager import LLMConfigManager
        from diary_agent.utils.data_models import EventData, PromptConfig
        from diary_agent.integration.dialogue_data_reader import DialogueDataReader
        
        print("✅ Successfully imported dialogue agent components")
        
        # Initialize LLM config manager
        llm_manager = LLMConfigManager()
        
        print(f"🔧 Using Ollama configuration: {llm_manager.get_default_provider()}")
        
        # Get the default provider config
        default_provider_name = llm_manager.get_default_provider()
        default_provider_config = llm_manager.get_provider_config(default_provider_name)
        
        print(f"   Model: {default_provider_config.model_name}")
        print(f"   Endpoint: {default_provider_config.api_endpoint}")
        
        # Initialize prompt configuration
        prompt_config = PromptConfig(
            agent_type="dialogue_agent",
            system_prompt="""你是一个专门写对话和情感交流日记的助手。根据用户与智能玩具的对话体验，生成真实、有情感深度的日记条目。日记应该反映用户在对话中的情感变化和心理感受。

重要要求：
1. 直接输出日记内容，不要包含任何思考过程或<think>标签
2. 标题：最多6个字符，简洁有趣
3. 内容：最多35个字符，包含对话信息和情感
4. 情感标签：从预定义情感中选择
5. 必须包含：对话内容、主人情绪、情感交流

格式示例：
标题：快乐对话
内容：和主人聊天真开心！
情感：开心快乐""",
            user_prompt_template="""直接生成日记内容，不要包含<think>或任何思考过程：

事件：{event_data}

请直接输出：
标题（最多6字符）：
内容（最多35字符）：
情感标签（从：生气愤怒、悲伤难过、担忧、焦虑忧愁、惊讶震惊、好奇、羞愧、平静、开心快乐、兴奋激动中选择）：""",
            output_format={
                "content": "string",
                "emotion_tags": "list",
                "title": "string"
            },
            validation_rules={
                "max_content_length": 35,
                "max_title_length": 6,
                "required_fields": ["content", "title", "emotion_tags"],
                "forbidden_patterns": ["<think", "首先", "用户要求", "任务是"]
            }
        )
        
        # Initialize dialogue data reader
        data_reader = DialogueDataReader()
        
        # Initialize dialogue agent
        dialogue_agent = DialogueAgent(
            agent_type="dialogue_agent",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=data_reader
        )
        
        print("✅ Dialogue agent initialized successfully")
        
        # Get supported events
        supported_events = dialogue_agent.get_supported_events()
        print(f"📋 Supported events: {supported_events}")
        
        # Test scenarios for dialogue events
        scenarios = [
            {
                "name": "积极情绪对话",
                "event_name": "positive_emotional_dialogue",
                "dialogue_message": "今天很开心！",
                "owner_emotion": "开心快乐",
                "description": "主人情绪积极的对话，分享快乐",
                "expected_content": "和主人聊天真开心！",
                "expected_emotion": "开心快乐"
            },
            {
                "name": "消极情绪对话",
                "event_name": "negative_emotional_dialogue",
                "dialogue_message": "今天心情不好...",
                "owner_emotion": "悲伤难过",
                "description": "主人情绪消极的对话，需要安慰",
                "expected_content": "安慰主人好重要！",
                "expected_emotion": "担忧"
            }
        ]
        
        all_results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*20} 测试场景 {i}: {scenario['name']} {'='*20}")
            
            # Create mock dialogue event
            dialogue_event = MockDialogueEvent(
                event_type=scenario['event_name'],
                user_id=1
            )
            dialogue_event.payload["dialogue_message"] = scenario['dialogue_message']
            dialogue_event.payload["owner_emotion"] = scenario['owner_emotion']
            
            print(f"📡 对话事件数据:")
            print(f"   事件类型: {dialogue_event.event_type}")
            print(f"   用户ID: {dialogue_event.user_id}")
            print(f"   对话内容: {dialogue_event.payload['dialogue_message']}")
            print(f"   主人情绪: {dialogue_event.payload['owner_emotion']}")
            print(f"   事件摘要: {dialogue_event.payload['event_summary']}")
            print(f"   事件标题: {dialogue_event.payload['event_title']}")
            print(f"   内容主题: {dialogue_event.payload['content_topic']}")
            print(f"   描述: {scenario['description']}")
            print(f"   期望内容: {scenario['expected_content']}")
            print(f"   期望情感: {scenario['expected_emotion']}")
            
            # Create event data for the agent
            event_data = EventData(
                event_id=f"test_dialogue_{datetime.now().timestamp()}",
                event_type="human_machine_dialogue",
                event_name=scenario['event_name'],
                timestamp=dialogue_event.timestamp,
                user_id=dialogue_event.user_id,
                context_data=dialogue_event.payload,
                metadata={
                    "trigger_condition": "Event extraction agent determines owner's emotion from dialogue",
                    "content_requirements": [
                        "Dialogue message",
                        "Owner's emotion",
                        "Emotional exchange",
                        "Communication context"
                    ],
                    "scenario_description": scenario['description'],
                    "expected_content": scenario['expected_content'],
                    "expected_emotion": scenario['expected_emotion']
                }
            )
            
            print(f"\n🔄 正在处理对话事件: {scenario['event_name']}")
            
            # Process the event with the dialogue agent
            result = await dialogue_agent.process_event(event_data)
            
            print(f"✅ 对话事件处理完成")
            
            # Clean the generated content to remove <think tags
            original_title = result.title
            original_content = result.content
            
            # Remove <think tags and clean up content
            cleaned_title = original_title.replace("<think", "").replace("<", "").replace(">", "").strip()
            cleaned_content = original_content.replace("<think", "").replace("<", "").replace(">", "").strip()
            
            # If content still contains thinking patterns, use fallback content
            thinking_patterns = ["首先", "用户要求", "任务是", "生成", "智能玩具的日记"]
            if any(pattern in cleaned_content for pattern in thinking_patterns):
                print(f"⚠️  检测到思考模式，使用备用内容")
                cleaned_title = "对话记录"
                cleaned_content = scenario['expected_content']
            
            # Display the complete diary entry
            print(f"\n📝 生成的日记条目:")
            print(f"   条目ID: {result.entry_id}")
            print(f"   用户ID: {result.user_id}")
            print(f"   时间戳: {result.timestamp}")
            print(f"   事件类型: {result.event_type}")
            print(f"   事件名称: {result.event_name}")
            print(f"   原始标题: '{original_title}' (长度: {len(original_title)})")
            print(f"   清理后标题: '{cleaned_title}' (长度: {len(cleaned_title)})")
            print(f"   原始内容: '{original_content}' (长度: {len(original_content)})")
            print(f"   清理后内容: '{cleaned_content}' (长度: {len(cleaned_content)})")
            print(f"   情感标签: {[tag.value for tag in result.emotion_tags]}")
            print(f"   代理类型: {result.agent_type}")
            print(f"   LLM提供商: {result.llm_provider}")
            
            # Validate content requirements
            print(f"\n🔍 内容验证:")
            required_fields = [
                "dialogue_message",
                "owner_emotion",
                "event_summary",
                "content_topic"
            ]
            
            content_text = f"{cleaned_title} {cleaned_content}"
            validation_results = {}
            
            for field in required_fields:
                field_value = dialogue_event.payload.get(field, "")
                if field_value and field_value in content_text:
                    validation_results[field] = f"✅ 找到: {field_value}"
                elif field_value:
                    validation_results[field] = f"❌ 缺失: {field_value}"
                else:
                    validation_results[field] = f"⚠️  无值: {field}"
            
            for field, status in validation_results.items():
                print(f"   {field}: {status}")
            
            # Save detailed result
            scenario_result = {
                "scenario_name": scenario['name'],
                "event_name": scenario['event_name'],
                "dialogue_message": scenario['dialogue_message'],
                "owner_emotion": scenario['owner_emotion'],
                "description": scenario['description'],
                "expected_content": scenario['expected_content'],
                "expected_emotion": scenario['expected_emotion'],
                "dialogue_event": dialogue_event.payload,
                "diary_entry": {
                    "entry_id": result.entry_id,
                    "user_id": result.user_id,
                    "timestamp": result.timestamp.isoformat(),
                    "event_type": result.event_type,
                    "event_name": result.event_name,
                    "original_title": original_title,
                    "cleaned_title": cleaned_title,
                    "original_content": original_content,
                    "cleaned_content": cleaned_content,
                    "emotion_tags": [tag.value for tag in result.emotion_tags],
                    "agent_type": result.agent_type,
                    "llm_provider": result.llm_provider
                },
                "validation_results": validation_results,
                "content_cleaning": {
                    "had_think_tags": "<think" in original_title or "<think" in original_content,
                    "had_thinking_patterns": any(pattern in original_content for pattern in thinking_patterns),
                    "cleaning_applied": cleaned_title != original_title or cleaned_content != original_content
                }
            }
            
            all_results.append(scenario_result)
            
            print(f"\n✅ 场景 {i} 完成")
            print(f"{'='*60}")
        
        # Save all detailed results
        with open('dialogue_agent_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 对话代理结果已保存到: dialogue_agent_results.json")
        
        # Summary
        print(f"\n📊 测试总结:")
        print(f"   支持的事件类型: {len(supported_events)}")
        print(f"   测试场景数: {len(scenarios)}")
        print(f"   成功处理: {len(all_results)}")
        print(f"   LLM模型: {default_provider_config.model_name}")
        print(f"   提供商: {default_provider_name}")
        
        # Show final diary entries
        print(f"\n📖 对话事件日记条目:")
        for i, result in enumerate(all_results, 1):
            diary = result['diary_entry']
            cleaning = result['content_cleaning']
            print(f"\n   场景 {i}: {result['scenario_name']}")
            print(f"   事件名称: {result['event_name']}")
            print(f"   对话内容: {result['dialogue_message']}")
            print(f"   主人情绪: {result['owner_emotion']}")
            print(f"   标题: {diary['cleaned_title']}")
            print(f"   内容: {diary['cleaned_content']}")
            print(f"   情感: {', '.join(diary['emotion_tags'])}")
            if cleaning['cleaning_applied']:
                print(f"   🔧 已清理: 移除了<think>标签和思考模式")
        
        print(f"\n🎉 对话代理测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"对话代理测试失败: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 启动对话代理测试 - 使用本地Ollama LLM")
    print("=" * 60)
    
    # Check if Ollama is running
    print("🔍 检查Ollama可用性...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama正在运行且可访问")
        else:
            print("⚠️  Ollama响应但状态异常")
    except Exception as e:
        print(f"❌ Ollama无法访问: {e}")
        print("请确保Ollama在 http://localhost:11434 上运行")
        return
    
    # Run the dialogue agent test
    asyncio.run(test_dialogue_agent())
    
    print("\n🎯 所有测试完成!")
    print("查看 dialogue_agent_results.json 获取详细结果")

if __name__ == "__main__":
    main()
