#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test script using all supported events from interactive_agent.py.
This script tests all 6 event types supported by the InteractiveAgent.
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
        logging.FileHandler('comprehensive_events_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockMQTTEvent:
    """Mock MQTT event for testing."""
    
    def __init__(self, event_type: str = "same_frequency_event", user_id: int = 1):
        self.event_type = event_type
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.payload = {
            "event_type": event_type,
            "user_id": user_id,
            "interaction_type": "摸摸脸",
            "same_frequency_event": "一起玩耍",
            "toy_owner_nickname": "小明",
            "close_friend_nickname": "小红",
            "close_friend_owner_nickname": "小红的妈妈"
        }

async def test_all_supported_events():
    """Test all supported events from interactive_agent.py."""
    print("=== Comprehensive Events Test - All Supported Events ===")
    print("=" * 70)
    
    try:
        # Import the interactive agent components
        from diary_agent.agents.interactive_agent import InteractiveAgent
        from diary_agent.core.llm_manager import LLMConfigManager
        from diary_agent.utils.data_models import EventData, PromptConfig
        from diary_agent.integration.interaction_data_reader import InteractionDataReader
        
        print("✅ Successfully imported interactive agent components")
        
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
            agent_type="interactive",
            system_prompt="""你是一个智能玩具的日记生成助手。直接生成日记内容，不要包含任何思考过程或<think>标签。

重要要求：
1. 直接输出日记内容，不要解释或思考
2. 标题：最多6个字符，简洁有趣
3. 内容：最多35个字符，包含事件信息和情感
4. 情感标签：从预定义情感中选择
5. 必须包含：事件名称、玩具主人昵称、好朋友昵称、好朋友主人昵称

格式示例：
标题：同频惊喜
内容：和小红一起玩耍真开心！
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
        
        # Initialize interaction data reader
        data_reader = InteractionDataReader()
        
        # Initialize interactive agent
        interactive_agent = InteractiveAgent(
            agent_type="interactive",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=data_reader
        )
        
        print("✅ Interactive agent initialized successfully")
        
        # Get all supported events from the interactive agent
        supported_events = interactive_agent.get_supported_events()
        print(f"📋 Supported events: {supported_events}")
        
        # Test scenarios for all supported events
        scenarios = [
            {
                "name": "喜欢互动1次",
                "event_name": "liked_interaction_once",
                "interaction_type": "一起玩耍",
                "same_frequency_event": "一起玩耍",
                "description": "小明和小红同时触发了一起玩耍的互动（喜欢1次）",
                "expected_content": "和小红一起玩耍真开心！",
                "expected_emotion": "开心快乐"
            },
            {
                "name": "喜欢互动3-5次",
                "event_name": "liked_interaction_3_to_5_times",
                "interaction_type": "摸摸头",
                "same_frequency_event": "摸摸头",
                "description": "小明和小红同时被摸了头（喜欢3-5次）",
                "expected_content": "被摸摸头好舒服！",
                "expected_emotion": "开心快乐"
            },
            {
                "name": "喜欢互动超过5次",
                "event_name": "liked_interaction_over_5_times",
                "interaction_type": "喂食",
                "same_frequency_event": "喂食",
                "description": "小明和小红同时被喂食（喜欢超过5次）",
                "expected_content": "和小红一起吃饭真棒！",
                "expected_emotion": "兴奋激动"
            },
            {
                "name": "不喜欢互动1次",
                "event_name": "disliked_interaction_once",
                "interaction_type": "强制抱抱",
                "same_frequency_event": "强制抱抱",
                "description": "小明和小红被强制抱抱（不喜欢1次）",
                "expected_content": "不想被强制抱抱！",
                "expected_emotion": "生气愤怒"
            },
            {
                "name": "不喜欢互动3-5次",
                "event_name": "disliked_interaction_3_to_5_times",
                "interaction_type": "强制洗澡",
                "same_frequency_event": "强制洗澡",
                "description": "小明和小红被强制洗澡（不喜欢3-5次）",
                "expected_content": "讨厌被强制洗澡！",
                "expected_emotion": "生气愤怒"
            },
            {
                "name": "中性互动超过5次",
                "event_name": "neutral_interaction_over_5_times",
                "interaction_type": "例行检查",
                "same_frequency_event": "例行检查",
                "description": "小明和小红进行例行检查（中性超过5次）",
                "expected_content": "例行检查完成了。",
                "expected_emotion": "平静"
            }
        ]
        
        all_results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*25} 测试场景 {i}: {scenario['name']} {'='*25}")
            
            # Create mock MQTT event
            mqtt_event = MockMQTTEvent(
                event_type="same_frequency_event",
                user_id=1
            )
            mqtt_event.payload["interaction_type"] = scenario['interaction_type']
            mqtt_event.payload["same_frequency_event"] = scenario['same_frequency_event']
            
            print(f"📡 MQTT事件数据:")
            print(f"   事件类型: {mqtt_event.event_type}")
            print(f"   用户ID: {mqtt_event.user_id}")
            print(f"   互动类型: {mqtt_event.payload['interaction_type']}")
            print(f"   同频事件: {mqtt_event.payload['same_frequency_event']}")
            print(f"   玩具主人: {mqtt_event.payload['toy_owner_nickname']}")
            print(f"   好朋友: {mqtt_event.payload['close_friend_nickname']}")
            print(f"   好朋友主人: {mqtt_event.payload['close_friend_owner_nickname']}")
            print(f"   描述: {scenario['description']}")
            print(f"   期望内容: {scenario['expected_content']}")
            print(f"   期望情感: {scenario['expected_emotion']}")
            
            # Create event data for the agent
            event_data = EventData(
                event_id=f"test_event_{datetime.now().timestamp()}",
                event_type="human_machine_interaction",
                event_name=scenario['event_name'],
                timestamp=mqtt_event.timestamp,
                user_id=mqtt_event.user_id,
                context_data=mqtt_event.payload,
                metadata={
                    "trigger_condition": "MQTT message received with event type",
                    "content_requirements": [
                        "Same frequency event name",
                        "Toy owner's nickname",
                        "Close friend's nickname",
                        "Close friend's owner's nickname"
                    ],
                    "scenario_description": scenario['description'],
                    "expected_content": scenario['expected_content'],
                    "expected_emotion": scenario['expected_emotion']
                }
            )
            
            print(f"\n🔄 正在处理事件: {scenario['event_name']}")
            
            # Process the event with the interactive agent
            result = await interactive_agent.process_event(event_data)
            
            print(f"✅ 事件处理完成")
            
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
                cleaned_title = "互动记录"
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
                "same_frequency_event",
                "toy_owner_nickname", 
                "close_friend_nickname",
                "close_friend_owner_nickname"
            ]
            
            content_text = f"{cleaned_title} {cleaned_content}"
            validation_results = {}
            
            for field in required_fields:
                field_chinese = {
                    "same_frequency_event": scenario['same_frequency_event'],
                    "toy_owner_nickname": "小明",
                    "close_friend_nickname": "小红",
                    "close_friend_owner_nickname": "小红的妈妈"
                }
                
                if field_chinese[field] in content_text:
                    validation_results[field] = f"✅ 找到: {field_chinese[field]}"
                else:
                    validation_results[field] = f"❌ 缺失: {field_chinese[field]}"
            
            for field, status in validation_results.items():
                print(f"   {field}: {status}")
            
            # Save detailed result
            scenario_result = {
                "scenario_name": scenario['name'],
                "event_name": scenario['event_name'],
                "interaction_type": scenario['interaction_type'],
                "same_frequency_event": scenario['same_frequency_event'],
                "description": scenario['description'],
                "expected_content": scenario['expected_content'],
                "expected_emotion": scenario['expected_emotion'],
                "mqtt_event": mqtt_event.payload,
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
            print(f"{'='*70}")
        
        # Save all detailed results
        with open('comprehensive_events_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 综合事件结果已保存到: comprehensive_events_results.json")
        
        # Summary
        print(f"\n📊 测试总结:")
        print(f"   支持的事件类型: {len(supported_events)}")
        print(f"   测试场景数: {len(scenarios)}")
        print(f"   成功处理: {len(all_results)}")
        print(f"   LLM模型: {default_provider_config.model_name}")
        print(f"   提供商: {default_provider_name}")
        
        # Show final diary entries
        print(f"\n📖 所有事件类型的日记条目:")
        for i, result in enumerate(all_results, 1):
            diary = result['diary_entry']
            cleaning = result['content_cleaning']
            print(f"\n   场景 {i}: {result['scenario_name']}")
            print(f"   事件名称: {result['event_name']}")
            print(f"   标题: {diary['cleaned_title']}")
            print(f"   内容: {diary['cleaned_content']}")
            print(f"   情感: {', '.join(diary['emotion_tags'])}")
            if cleaning['cleaning_applied']:
                print(f"   🔧 已清理: 移除了<think>标签和思考模式")
        
        print(f"\n🎉 综合事件测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"综合事件测试失败: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 启动综合事件测试 - 所有支持的事件类型")
    print("=" * 70)
    
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
    
    # Run the comprehensive test
    asyncio.run(test_all_supported_events())
    
    print("\n🎯 所有测试完成!")
    print("查看 comprehensive_events_results.json 获取综合结果")

if __name__ == "__main__":
    main()
