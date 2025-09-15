#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete diary system test.
This script tests the complete diary writing system using daily conditions and real agents.
"""

import sys
import os
import json
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual agents and configurations
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import PromptConfig, EventData, DiaryEntry, DataReader, DiaryContextData
from diary_agent.agents.interactive_agent import InteractiveAgent
from diary_agent.agents.dialogue_agent import DialogueAgent
from diary_agent.agents.neglect_agent import NeglectAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_diary_system_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockDataReader(DataReader):
    """Mock data reader for testing."""
    
    def __init__(self, module_name: str = "mock_module"):
        super().__init__(module_name=module_name, read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """Mock event context reading."""
        return DiaryContextData(
            user_profile={"name": "主人"},
            event_details=event_data.context_data,
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": event_data.timestamp.isoformat()}
        )

class DailyDiaryManager:
    """Manages daily diary writing process with real agents."""
    
    def __init__(self):
        self.daily_diary_count = 0
        self.written_event_types = set()
        self.diary_entries = []
        
        # Initialize LLM configuration
        self.llm_config_manager = LLMConfigManager()
        
        # Initialize prompt configuration
        self.prompt_config = PromptConfig(
            agent_type="diary_agent",
            system_prompt="你是一个可爱的玩具日记助手，请根据事件信息写一篇简短的日记。直接输出日记内容，不要包含任何思考过程或标签。",
            user_prompt_template="事件类型: {event_type}\n事件名称: {event_name}\n事件详情: {event_details}\n\n请写一篇简短的日记，包含标题和内容。",
            output_format={
                "title": "string",
                "content": "string",
                "emotion": "string"
            },
            validation_rules={
                "title_max_length": 6,
                "content_max_length": 35,
                "required_fields": ["title", "content", "emotion"]
            }
        )
        
        # Initialize agents with mock data readers
        mock_interaction_reader = MockDataReader()
        mock_dialogue_reader = MockDataReader()
        mock_neglect_reader = MockDataReader()
        
        self.interactive_agent = InteractiveAgent(
            agent_type="interactive_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=mock_interaction_reader
        )
        self.dialogue_agent = DialogueAgent(
            agent_type="dialogue_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=mock_dialogue_reader
        )
        self.neglect_agent = NeglectAgent(
            agent_type="neglect_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=mock_neglect_reader
        )
        
    def determine_daily_diary_count(self):
        """At 00:00, randomly determine how many diaries to write (0-5)."""
        self.daily_diary_count = random.randint(0, 5)
        self.written_event_types = set()
        self.diary_entries = []
        return self.daily_diary_count
    
    def should_write_diary_for_event(self, event_type: str) -> bool:
        """Randomly determine if a diary should be written for this event."""
        # Only one diary per event type per day
        if event_type in self.written_event_types:
            return False
        
        # If we've already written all required diaries, don't write more
        if len(self.diary_entries) >= self.daily_diary_count:
            return False
        
        # Randomly decide if we should write a diary for this event
        should_write = random.choice([True, False])
        
        if should_write:
            self.written_event_types.add(event_type)
        
        return should_write
    
    def clean_llm_output(self, content: str) -> str:
        """Clean LLM output to remove thinking patterns and tags."""
        if not content:
            return ""
        
        # Remove thinking patterns
        thinking_patterns = [
            "<think>", "</think>", "首先", "用户要求", "关于持续忽", 
            "根据事件信息", "作为日记助手", "让我来写", "我来写",
            "思考过程", "分析", "理解", "总结"
        ]
        
        cleaned_content = content
        for pattern in thinking_patterns:
            cleaned_content = cleaned_content.replace(pattern, "")
        
        # Remove extra whitespace
        cleaned_content = " ".join(cleaned_content.split())
        
        # If content is too short after cleaning, try to extract meaningful content
        if len(cleaned_content) < 10:
            # Try to find content after common patterns
            import re
            content_match = re.search(r'内容[：:]\s*(.+)', content)
            if content_match:
                cleaned_content = content_match.group(1).strip()
        
        return cleaned_content
    
    async def write_diary_entry_with_agent(self, event_data: EventData) -> Optional[DiaryEntry]:
        """Write a diary entry using the appropriate agent."""
        try:
            # Select the appropriate agent based on event type
            if event_data.event_type == "human_machine_interaction":
                agent = self.interactive_agent
            elif event_data.event_type == "dialogue":
                agent = self.dialogue_agent
            elif event_data.event_type == "neglect":
                agent = self.neglect_agent
            else:
                logger.warning(f"Unknown event type: {event_data.event_type}")
                return None
            
            # Generate diary entry using the agent
            diary_entry = await agent.process_event(event_data)
            
            if diary_entry:
                # Clean the content
                diary_entry.content = self.clean_llm_output(diary_entry.content)
                diary_entry.title = self.clean_llm_output(diary_entry.title)
                
                # Add to daily entries
                self.diary_entries.append(diary_entry)
                return diary_entry
            
        except Exception as e:
            logger.error(f"Error writing diary entry: {e}")
            return None
    
    def get_daily_summary(self) -> Dict:
        """Get summary of the day's diary writing."""
        return {
            "daily_diary_count": self.daily_diary_count,
            "written_diary_count": len(self.diary_entries),
            "written_event_types": list(self.written_event_types),
            "remaining_diaries": max(0, self.daily_diary_count - len(self.diary_entries))
        }

def create_mock_event_data(event_type: str, event_name: str, event_details: Dict) -> EventData:
    """Create mock event data for testing."""
    return EventData(
        event_id=f"test_event_{datetime.now().timestamp()}",
        event_type=event_type,
        event_name=event_name,
        user_id=1,
        timestamp=datetime.now(),
        context_data=event_details,
        metadata={"test": True}
    )

async def test_complete_diary_system():
    """Test the complete diary writing system."""
    print("=== Complete Diary System Test ===")
    print("=" * 60)
    
    try:
        # Define event types and their details
        event_types = {
            "human_machine_interaction": {
                "name": "人机互动事件",
                "events": [
                    {
                        "name": "liked_interaction_once",
                        "details": {
                            "interaction_type": "抚摸",
                            "duration": "5分钟",
                            "user_response": "positive",
                            "toy_emotion": "开心"
                        }
                    },
                    {
                        "name": "liked_interaction_3_to_5_times",
                        "details": {
                            "interaction_type": "摸摸头",
                            "count": 4,
                            "duration": "20分钟",
                            "user_response": "positive",
                            "toy_emotion": "平静"
                        }
                    },
                    {
                        "name": "liked_interaction_over_5_times",
                        "details": {
                            "interaction_type": "喂食",
                            "count": 7,
                            "duration": "30分钟",
                            "user_response": "positive",
                            "toy_emotion": "开心快乐"
                        }
                    }
                ]
            },
            "dialogue": {
                "name": "对话事件",
                "events": [
                    {
                        "name": "positive_emotional_dialogue",
                        "details": {
                            "dialogue_type": "开心对话",
                            "content": "主人今天心情很好",
                            "duration": "10分钟",
                            "toy_emotion": "开心快乐"
                        }
                    },
                    {
                        "name": "negative_emotional_dialogue",
                        "details": {
                            "dialogue_type": "安慰对话",
                            "content": "主人需要安慰",
                            "duration": "15分钟",
                            "toy_emotion": "平静"
                        }
                    }
                ]
            },
            "neglect": {
                "name": "忽视事件",
                "events": [
                    {
                        "name": "neglect_1_day_no_dialogue",
                        "details": {
                            "neglect_duration": 1,
                            "neglect_type": "no_dialogue",
                            "disconnection_type": "无对话有互动",
                            "disconnection_days": 1,
                            "memory_status": "on",
                            "last_interaction_date": (datetime.now() - timedelta(days=1)).isoformat()
                        }
                    },
                    {
                        "name": "neglect_3_days_no_interaction",
                        "details": {
                            "neglect_duration": 3,
                            "neglect_type": "no_interaction",
                            "disconnection_type": "完全无互动",
                            "disconnection_days": 3,
                            "memory_status": "on",
                            "last_interaction_date": (datetime.now() - timedelta(days=3)).isoformat()
                        }
                    },
                    {
                        "name": "neglect_7_days_no_dialogue",
                        "details": {
                            "neglect_duration": 7,
                            "neglect_type": "no_dialogue",
                            "disconnection_type": "无对话有互动",
                            "disconnection_days": 7,
                            "memory_status": "on",
                            "last_interaction_date": (datetime.now() - timedelta(days=7)).isoformat()
                        }
                    }
                ]
            }
        }
        
        # Test multiple days
        test_days = 3
        all_daily_results = []
        
        for day in range(1, test_days + 1):
            print(f"\n{'='*20} 测试第 {day} 天 {'='*20}")
            
            # Initialize daily diary manager
            diary_manager = DailyDiaryManager()
            
            # Step 1: At 00:00, determine daily diary count
            daily_count = diary_manager.determine_daily_diary_count()
            print(f"📅 第 {day} 天 00:00 - 决定写 {daily_count} 篇日记")
            
            if daily_count == 0:
                print("   ⏭️  今天不需要写日记")
                all_daily_results.append({
                    "day": day,
                    "daily_count": daily_count,
                    "events": [],
                    "diaries": [],
                    "summary": diary_manager.get_daily_summary()
                })
                continue
            
            # Step 2: Simulate events occurring throughout the day
            daily_events = []
            
            # Generate random events for the day (3-6 events)
            num_events = random.randint(3, 6)
            print(f"📡 第 {day} 天发生 {num_events} 个事件:")
            
            for event_num in range(1, num_events + 1):
                # Randomly select event type and specific event
                event_type = random.choice(list(event_types.keys()))
                event_info = random.choice(event_types[event_type]["events"])
                
                # Create event data
                event_data = create_mock_event_data(
                    event_type=event_type,
                    event_name=event_info["name"],
                    event_details=event_info["details"]
                )
                
                daily_events.append({
                    "event_num": event_num,
                    "event_data": event_data,
                    "event_info": event_info
                })
                
                print(f"   事件 {event_num}: {event_types[event_type]['name']} - {event_info['name']}")
                
                # Step 3: Randomly decide if diary should be written for this event
                should_write = diary_manager.should_write_diary_for_event(event_type)
                
                if should_write:
                    print(f"      ✍️  为事件 {event_num} 写日记...")
                    
                    # Write diary entry using real agent
                    diary_entry = await diary_manager.write_diary_entry_with_agent(event_data)
                    
                    if diary_entry:
                        print(f"      ✅ 日记完成: '{diary_entry.title}' - '{diary_entry.content[:50]}...' ({diary_entry.emotion_tags[0].value if diary_entry.emotion_tags else 'N/A'})")
                    else:
                        print(f"      ❌ 日记生成失败")
                else:
                    print(f"      ⏭️  跳过事件 {event_num} 的日记")
                
                # Check if we've written all required diaries
                if len(diary_manager.diary_entries) >= daily_count:
                    print(f"      ✅ 已完成今天的 {daily_count} 篇日记")
                    break
            
            # Step 4: Daily summary
            summary = diary_manager.get_daily_summary()
            print(f"\n📊 第 {day} 天总结:")
            print(f"   计划写日记数: {summary['daily_diary_count']}")
            print(f"   实际写日记数: {summary['written_diary_count']}")
            print(f"   剩余日记数: {summary['remaining_diaries']}")
            print(f"   已写事件类型: {', '.join(summary['written_event_types']) if summary['written_event_types'] else '无'}")
            
            # Save daily results
            daily_result = {
                "day": day,
                "daily_count": daily_count,
                "events": [
                    {
                        "event_num": e["event_num"],
                        "event_type": e["event_data"].event_type,
                        "event_name": e["event_data"].event_name,
                        "event_details": e["event_info"]["details"]
                    }
                    for e in daily_events
                ],
                "diaries": [
                    {
                        "entry_id": d.entry_id,
                        "event_type": d.event_type,
                        "event_name": d.event_name,
                        "title": d.title,
                        "content": d.content,
                        "emotion_tags": [tag.value for tag in d.emotion_tags] if d.emotion_tags else [],
                        "timestamp": d.timestamp.isoformat(),
                        "agent_type": d.agent_type,
                        "llm_provider": d.llm_provider
                    }
                    for d in diary_manager.diary_entries
                ],
                "summary": summary
            }
            
            all_daily_results.append(daily_result)
        
        # Save all results
        with open('complete_diary_system_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_daily_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 完整日记系统测试结果已保存到: complete_diary_system_results.json")
        
        # Overall summary
        print(f"\n📈 总体测试总结:")
        total_planned = sum(r["daily_count"] for r in all_daily_results)
        total_written = sum(r["summary"]["written_diary_count"] for r in all_daily_results)
        total_events = sum(len(r["events"]) for r in all_daily_results)
        
        print(f"   测试天数: {test_days}")
        print(f"   总计划日记数: {total_planned}")
        print(f"   总实际日记数: {total_written}")
        print(f"   总事件数: {total_events}")
        print(f"   日记完成率: {(total_written/total_planned*100):.1f}%" if total_planned > 0 else "   日记完成率: N/A")
        
        # Show daily breakdown
        print(f"\n📅 每日详细情况:")
        for result in all_daily_results:
            print(f"   第 {result['day']} 天: 计划 {result['daily_count']} 篇, 实际 {result['summary']['written_diary_count']} 篇")
            if result['diaries']:
                for diary in result['diaries']:
                    print(f"     - {diary['title']}: {diary['content'][:50]}... ({', '.join(diary['emotion_tags']) if diary['emotion_tags'] else 'N/A'})")
        
        print(f"\n🎉 完整日记系统测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"完整日记系统测试失败: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 启动完整日记系统测试")
    print("=" * 60)
    
    # Run the complete diary system test
    asyncio.run(test_complete_diary_system())
    
    print("\n🎯 所有测试完成!")
    print("查看 complete_diary_system_results.json 获取详细结果")

if __name__ == "__main__":
    main()
