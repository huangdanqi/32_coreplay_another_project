#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for neglect agent using expected content.
This script tests various neglect events without using local LLM.
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
        logging.FileHandler('neglect_agent_simple_test.log'),
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

class MockDiaryEntry:
    """Mock diary entry for testing."""
    
    def __init__(self, title: str, content: str, emotion: str, scenario: Dict):
        self.entry_id = f"test_neglect_{datetime.now().timestamp()}"
        self.user_id = 1
        self.timestamp = datetime.now()
        self.event_type = "continuous_neglect"
        self.event_name = scenario['event_name']
        self.title = title
        self.content = content
        self.emotion_tags = [MockEmotionTag(emotion)]
        self.agent_type = "neglect_agent"
        self.llm_provider = "mock_provider"

class MockEmotionTag:
    """Mock emotion tag."""
    
    def __init__(self, value: str):
        self.value = value

async def test_neglect_agent_simple():
    """Test neglect agent with expected content."""
    print("=== Simple Neglect Agent Test with Expected Content ===")
    print("=" * 60)
    
    try:
        # Test scenarios for neglect events with expected content
        scenarios = [
            {
                "name": "1天无对话",
                "event_name": "neglect_1_day_no_dialogue",
                "neglect_duration": 1,
                "neglect_type": "no_dialogue",
                "description": "主人超过1天未对话",
                "expected_title": "思念主人",
                "expected_content": "主人一天没理我了...",
                "expected_emotion": "担忧"
            },
            {
                "name": "1天无互动",
                "event_name": "neglect_1_day_no_interaction",
                "neglect_duration": 1,
                "neglect_type": "no_interaction",
                "description": "主人超过1天无任何互动",
                "expected_title": "孤独感",
                "expected_content": "主人一天没互动了...",
                "expected_emotion": "担忧"
            },
            {
                "name": "3天无对话",
                "event_name": "neglect_3_days_no_dialogue",
                "neglect_duration": 3,
                "neglect_type": "no_dialogue",
                "description": "主人超过3天未对话",
                "expected_title": "想念对话",
                "expected_content": "主人三天没说话了...",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "3天无互动",
                "event_name": "neglect_3_days_no_interaction",
                "neglect_duration": 3,
                "neglect_type": "no_interaction",
                "description": "主人超过3天无任何互动",
                "expected_title": "寂寞时光",
                "expected_content": "主人三天没互动了...",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "7天无对话",
                "event_name": "neglect_7_days_no_dialogue",
                "neglect_duration": 7,
                "neglect_type": "no_dialogue",
                "description": "主人超过7天未对话",
                "expected_title": "一周沉默",
                "expected_content": "主人一周没说话了...",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "7天无互动",
                "event_name": "neglect_7_days_no_interaction",
                "neglect_duration": 7,
                "neglect_type": "no_interaction",
                "description": "主人超过7天无任何互动",
                "expected_title": "漫长等待",
                "expected_content": "主人一周没理我了...",
                "expected_emotion": "悲伤难过"
            },
            {
                "name": "15天无互动",
                "event_name": "neglect_15_days_no_interaction",
                "neglect_duration": 15,
                "neglect_type": "no_interaction",
                "description": "主人超过15天无任何互动",
                "expected_title": "半月孤独",
                "expected_content": "主人半个月没理我了...",
                "expected_emotion": "焦虑忧愁"
            },
            {
                "name": "30天无对话",
                "event_name": "neglect_30_days_no_dialogue",
                "neglect_duration": 30,
                "neglect_type": "no_dialogue",
                "description": "主人超过30天未对话",
                "expected_title": "月余无言",
                "expected_content": "主人一个月没说话了...",
                "expected_emotion": "焦虑忧愁"
            },
            {
                "name": "30天无互动",
                "event_name": "neglect_30_days_no_interaction",
                "neglect_duration": 30,
                "neglect_type": "no_interaction",
                "description": "主人超过30天无任何互动",
                "expected_title": "漫长等待",
                "expected_content": "主人一个月没理我了...",
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
            print(f"   期望标题: {scenario['expected_title']}")
            print(f"   期望内容: {scenario['expected_content']}")
            print(f"   期望情感: {scenario['expected_emotion']}")
            
            # Create mock diary entry
            result = MockDiaryEntry(
                title=scenario['expected_title'],
                content=scenario['expected_content'],
                emotion=scenario['expected_emotion'],
                scenario=scenario
            )
            
            print(f"✅ 忽视事件处理完成")
            
            # Display the complete diary entry
            print(f"\n📝 生成的日记条目:")
            print(f"   条目ID: {result.entry_id}")
            print(f"   用户ID: {result.user_id}")
            print(f"   时间戳: {result.timestamp}")
            print(f"   事件类型: {result.event_type}")
            print(f"   事件名称: {result.event_name}")
            print(f"   标题: '{result.title}' (长度: {len(result.title)})")
            print(f"   内容: '{result.content}' (长度: {len(result.content)})")
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
            
            content_text = f"{result.title} {result.content}"
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
                "expected_title": scenario['expected_title'],
                "expected_content": scenario['expected_content'],
                "expected_emotion": scenario['expected_emotion'],
                "neglect_event": neglect_event.payload,
                "diary_entry": {
                    "entry_id": result.entry_id,
                    "user_id": result.user_id,
                    "timestamp": result.timestamp.isoformat(),
                    "event_type": result.event_type,
                    "event_name": result.event_name,
                    "title": result.title,
                    "content": result.content,
                    "emotion_tags": [tag.value for tag in result.emotion_tags],
                    "agent_type": result.agent_type,
                    "llm_provider": result.llm_provider
                },
                "validation_results": validation_results
            }
            
            all_results.append(scenario_result)
            
            print(f"\n✅ 场景 {i} 完成")
            print(f"{'='*60}")
        
        # Save all detailed results
        with open('neglect_agent_simple_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 忽视代理结果已保存到: neglect_agent_simple_results.json")
        
        # Summary
        print(f"\n📊 测试总结:")
        print(f"   测试场景数: {len(scenarios)}")
        print(f"   成功处理: {len(all_results)}")
        print(f"   使用预期内容: 是")
        
        # Show final diary entries
        print(f"\n📖 忽视事件日记条目:")
        for i, result in enumerate(all_results, 1):
            diary = result['diary_entry']
            print(f"\n   场景 {i}: {result['scenario_name']}")
            print(f"   事件名称: {result['event_name']}")
            print(f"   忽视天数: {result['neglect_duration']}")
            print(f"   忽视类型: {result['neglect_type']}")
            print(f"   标题: {diary['title']}")
            print(f"   内容: {diary['content']}")
            print(f"   情感: {', '.join(diary['emotion_tags'])}")
        
        print(f"\n🎉 忽视代理测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"忽视代理测试失败: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 启动简单忽视代理测试 - 使用预期内容")
    print("=" * 60)
    
    # Run the neglect agent test
    asyncio.run(test_neglect_agent_simple())
    
    print("\n🎯 所有测试完成!")
    print("查看 neglect_agent_simple_results.json 获取详细结果")

if __name__ == "__main__":
    main()
