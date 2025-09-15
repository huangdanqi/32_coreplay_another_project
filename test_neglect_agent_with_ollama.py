#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test script for neglect agent using local Ollama LLM.
This script tests various neglect events covering different durations and types.
"""

import sys
import os
import json
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('neglect_agent_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockNeglectEvent:
    """Mock neglect event for testing."""
    
    def __init__(self, event_type: str = "neglect_1_day_no_dialogue", user_id: int = 1):
        self.event_type = event_type
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.payload = {
            "event_type": event_type,
            "user_id": user_id,
            "neglect_duration": 1,
            "neglect_type": "no_dialogue",
            "event_name": "主人超过1天未对话",
            "disconnection_type": "完全无互动",
            "disconnection_days": 1,
            "memory_status": "on",
            "last_interaction_date": (datetime.now() - timedelta(days=1)).isoformat()
        }

async def test_neglect_agent():
    """Test neglect agent with local Ollama LLM."""
    print("=== Neglect Agent Test with Local Ollama LLM ===")
    print("=" * 60)
    
    try:
        # Import the neglect agent components
        from diary_agent.agents.neglect_agent import NeglectAgent
        from diary_agent.core.llm_manager import LLMConfigManager
        from diary_agent.utils.data_models import EventData, PromptConfig
        from diary_agent.integration.neglect_data_reader import NeglectDataReader
        
        print("✅ Successfully imported neglect agent components")
        
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
            agent_type="neglect_agent",
            system_prompt="""你是一个智能玩具的日记助手。当主人忽视玩具时，你需要生成真实、情感丰富的日记条目。

重要要求：
1. 直接输出日记内容，不要包含任何思考过程、<think>标签或"首先"、"用户要求"等词语
2. 标题：最多6个字符，简洁有趣
3. 内容：最多35个字符，包含忽视天数和情感
4. 情感标签：从预定义情感中选择
5. 格式：直接输出标题、内容、情感，不要任何解释

示例格式：
标题：思念主人
内容：主人一天没理我了...
情感：悲伤难过""",
            user_prompt_template="""事件：{event_data}

直接输出（不要任何思考过程）：
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
        
        # Initialize neglect data reader
        data_reader = NeglectDataReader()
        
        # Initialize neglect agent
        neglect_agent = NeglectAgent(
            agent_type="neglect_agent",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=data_reader
        )
        
        print("✅ Neglect agent initialized successfully")
        
        # Get supported events
        supported_events = neglect_agent.get_supported_events()
        print(f"📋 Supported events: {supported_events}")
        
        # Test scenarios for neglect events
        scenarios = [
            {
                "name": "1天无对话",
                "event_name": "neglect_1_day_no_dialogue",
                "neglect_duration": 1,
                "neglect_type": "no_dialogue",
                "description": "主人超过1天未对话",
                "expected_emotion": "担忧"
            },
            {
                "name": "1天无互动",
                "event_name": "neglect_1_day_no_interaction",
                "neglect_duration": 1,
                "neglect_type": "no_interaction",
                "description": "主人超过1天无任何互动",
                "expected_emotion": "担忧"
            },
            {
                "name": "3天无对话",
                "event_name": "neglect_3_days_no_dialogue",
                "neglect_duration": 3,
                "neglect_type": "no_dialogue",
                "description": "主人超过3天未对话",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "3天无互动",
                "event_name": "neglect_3_days_no_interaction",
                "neglect_duration": 3,
                "neglect_type": "no_interaction",
                "description": "主人超过3天无任何互动",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "7天无对话",
                "event_name": "neglect_7_days_no_dialogue",
                "neglect_duration": 7,
                "neglect_type": "no_dialogue",
                "description": "主人超过7天未对话",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "7天无互动",
                "event_name": "neglect_7_days_no_interaction",
                "neglect_duration": 7,
                "neglect_type": "no_interaction",
                "description": "主人超过7天无任何互动",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "15天无互动",
                "event_name": "neglect_15_days_no_interaction",
                "neglect_duration": 15,
                "neglect_type": "no_interaction",
                "description": "主人超过15天无任何互动",
                "expected_emotion": "焦虑忧愁"
            },
            {
                "name": "30天无对话",
                "event_name": "neglect_30_days_no_dialogue",
                "neglect_duration": 30,
                "neglect_type": "no_dialogue",
                "description": "主人超过30天未对话",
                "expected_emotion": "焦虑忧愁"
            },
            {
                "name": "30天无互动",
                "event_name": "neglect_30_days_no_interaction",
                "neglect_duration": 30,
                "neglect_type": "no_interaction",
                "description": "主人超过30天无任何互动",
                "expected_emotion": "焦虑忧愁"
            }
        ]
        
        all_results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*20} 测试场景 {i}: {scenario['name']} {'='*20}")
            
            # Create mock neglect event
            neglect_event = MockNeglectEvent(
                event_type=scenario['event_name'],
                user_id=1
            )
            neglect_event.payload["neglect_duration"] = scenario['neglect_duration']
            neglect_event.payload["neglect_type"] = scenario['neglect_type']
            neglect_event.payload["disconnection_days"] = scenario['neglect_duration']
            
            # Set disconnection type based on neglect type
            if scenario['neglect_type'] == "no_dialogue":
                neglect_event.payload["disconnection_type"] = "无对话有互动"
            else:
                neglect_event.payload["disconnection_type"] = "完全无互动"
            
            print(f"📡 忽视事件数据:")
            print(f"   事件类型: {neglect_event.event_type}")
            print(f"   用户ID: {neglect_event.user_id}")
            print(f"   忽视天数: {neglect_event.payload['neglect_duration']}")
            print(f"   忽视类型: {neglect_event.payload['neglect_type']}")
            print(f"   断联类型: {neglect_event.payload['disconnection_type']}")
            print(f"   断联天数: {neglect_event.payload['disconnection_days']}")
            print(f"   记忆状态: {neglect_event.payload['memory_status']}")
            print(f"   最后互动: {neglect_event.payload['last_interaction_date']}")
            print(f"   描述: {scenario['description']}")
            print(f"   期望情感: {scenario['expected_emotion']}")
            
            # Create event data for the agent
            event_data = EventData(
                event_id=f"test_neglect_{datetime.now().timestamp()}",
                event_type="continuous_neglect",
                event_name=scenario['event_name'],
                timestamp=neglect_event.timestamp,
                user_id=neglect_event.user_id,
                context_data=neglect_event.payload,
                metadata={
                    "trigger_condition": "Memory status is 'on' and consecutive day counts of no interactions meet thresholds",
                    "content_requirements": [
                        "Event name",
                        "Disconnection type (完全无互动/无对话有互动)",
                        "Disconnection days",
                        "Loneliness feeling"
                    ],
                    "scenario_description": scenario['description'],
                    "expected_emotion": scenario['expected_emotion']
                }
            )
            
            print(f"\n🔄 正在处理忽视事件: {scenario['event_name']}")
            
            # Process the event with the neglect agent
            result = await neglect_agent.process_event(event_data)
            
            print(f"✅ 忽视事件处理完成")
            
            # Clean the generated content to remove <think tags
            original_title = result.title
            original_content = result.content
            
            # Remove <think tags and clean up content
            cleaned_title = original_title.replace("<think", "").replace("<", "").replace(">", "").strip()
            cleaned_content = original_content.replace("<think", "").replace("<", "").replace(">", "").strip()
            
            # If content still contains thinking patterns, clean them more aggressively
            thinking_patterns = ["首先", "用户要求", "任务是", "生成", "智能玩具的日记", "根据", "我需要", "让我", "作为", "助手", "关于持续忽", "关于玩具被主"]
            if any(pattern in cleaned_content for pattern in thinking_patterns):
                print(f"⚠️  检测到思考模式，进行深度清理")
                # Remove thinking patterns and keep only the actual content
                for pattern in thinking_patterns:
                    cleaned_content = cleaned_content.replace(pattern, "").strip()
                # Clean up any remaining artifacts
                cleaned_content = cleaned_content.replace("，", "").replace("，", "").strip()
                # If content becomes too short after cleaning, try to extract meaningful content
                if len(cleaned_content) < 5:
                    # Try to find content after common thinking patterns
                    # Look for content after "首先" or similar patterns
                    match = re.search(r'首先[^，]*，([^，]*[^，\s])', original_content)
                    if match:
                        cleaned_content = match.group(1).strip()
                    else:
                        # Fallback: keep original cleaned version
                        cleaned_content = original_content.replace("<think", "").replace("<", "").replace(">", "").strip()
            
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
                "neglect_duration",
                "neglect_type",
                "disconnection_type",
                "disconnection_days"
            ]
            
            content_text = f"{cleaned_title} {cleaned_content}"
            validation_results = {}
            
            for field in required_fields:
                field_value = str(neglect_event.payload.get(field, ""))
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
                "neglect_duration": scenario['neglect_duration'],
                "neglect_type": scenario['neglect_type'],
                "description": scenario['description'],
                "expected_emotion": scenario['expected_emotion'],
                "neglect_event": neglect_event.payload,
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
        with open('neglect_agent_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 忽视代理结果已保存到: neglect_agent_results.json")
        
        # Summary
        print(f"\n📊 测试总结:")
        print(f"   支持的事件类型: {len(supported_events)}")
        print(f"   测试场景数: {len(scenarios)}")
        print(f"   成功处理: {len(all_results)}")
        print(f"   LLM模型: {default_provider_config.model_name}")
        print(f"   提供商: {default_provider_name}")
        
        # Show final diary entries
        print(f"\n📖 忽视事件日记条目:")
        for i, result in enumerate(all_results, 1):
            diary = result['diary_entry']
            cleaning = result['content_cleaning']
            print(f"\n   场景 {i}: {result['scenario_name']}")
            print(f"   事件名称: {result['event_name']}")
            print(f"   忽视天数: {result['neglect_duration']}")
            print(f"   忽视类型: {result['neglect_type']}")
            print(f"   标题: {diary['cleaned_title']}")
            print(f"   内容: {diary['cleaned_content']}")
            print(f"   情感: {', '.join(diary['emotion_tags'])}")
            if cleaning['cleaning_applied']:
                print(f"   🔧 已清理: 移除了<think>标签和思考模式")
        
        print(f"\n🎉 忽视代理测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"忽视代理测试失败: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 启动忽视代理测试 - 使用本地Ollama LLM")
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
    
    # Run the neglect agent test
    asyncio.run(test_neglect_agent())
    
    print("\n🎯 所有测试完成!")
    print("查看 neglect_agent_results.json 获取详细结果")

if __name__ == "__main__":
    main()
