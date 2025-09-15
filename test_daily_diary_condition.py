#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily diary writing condition test.
This script tests the daily diary writing process based on the specification.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_diary_condition_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockEvent:
    """Mock event for testing."""
    
    def __init__(self, event_type: str, event_name: str, user_id: int = 1):
        self.event_type = event_type
        self.event_name = event_name
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.payload = {
            "event_type": event_type,
            "event_name": event_name,
            "user_id": user_id,
            "timestamp": self.timestamp.isoformat()
        }

class MockDiaryEntry:
    """Mock diary entry for testing."""
    
    def __init__(self, title: str, content: str, emotion: str, event_type: str, event_name: str):
        self.entry_id = f"diary_{datetime.now().timestamp()}"
        self.user_id = 1
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.event_name = event_name
        self.title = title
        self.content = content
        self.emotion_tags = [MockEmotionTag(emotion)]
        self.agent_type = f"{event_type}_agent"
        self.llm_provider = "mock_provider"

class MockEmotionTag:
    """Mock emotion tag."""
    
    def __init__(self, value: str):
        self.value = value

class DailyDiaryManager:
    """Manages daily diary writing process."""
    
    def __init__(self):
        self.daily_diary_count = 0
        self.written_event_types = set()
        self.diary_entries = []
        
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
    
    def write_diary_entry(self, event: MockEvent, title: str, content: str, emotion: str):
        """Write a diary entry for the event."""
        diary_entry = MockDiaryEntry(
            title=title,
            content=content,
            emotion=emotion,
            event_type=event.event_type,
            event_name=event.event_name
        )
        self.diary_entries.append(diary_entry)
        return diary_entry
    
    def get_daily_summary(self) -> Dict:
        """Get summary of the day's diary writing."""
        return {
            "daily_diary_count": self.daily_diary_count,
            "written_diary_count": len(self.diary_entries),
            "written_event_types": list(self.written_event_types),
            "remaining_diaries": max(0, self.daily_diary_count - len(self.diary_entries))
        }

async def test_daily_diary_condition():
    """Test the daily diary writing condition."""
    print("=== Daily Diary Writing Condition Test ===")
    print("=" * 60)
    
    try:
        # Define event types and their expected content
        event_types = {
            "human_machine_interaction": {
                "name": "人机互动事件",
                "events": [
                    {"name": "liked_interaction_once", "title": "同频惊喜", "content": "和小红一起玩耍真开心！", "emotion": "开心快乐"},
                    {"name": "liked_interaction_3_to_5_times", "title": "摸摸头", "content": "被摸摸头好舒服！", "emotion": "平静"},
                    {"name": "liked_interaction_over_5_times", "title": "喂食时光", "content": "和小红一起吃饭真棒！", "emotion": "开心快乐"}
                ]
            },
            "dialogue": {
                "name": "对话事件",
                "events": [
                    {"name": "positive_emotional_dialogue", "title": "开心对话", "content": "和主人聊天真开心！", "emotion": "开心快乐"},
                    {"name": "negative_emotional_dialogue", "title": "安慰主人", "content": "安慰主人好重要！", "emotion": "平静"}
                ]
            },
            "neglect": {
                "name": "忽视事件",
                "events": [
                    {"name": "neglect_1_day_no_dialogue", "title": "思念主人", "content": "主人一天没理我了...", "emotion": "担忧"},
                    {"name": "neglect_3_days_no_interaction", "title": "寂寞时光", "content": "主人三天没互动了...", "emotion": "悲伤难过"},
                    {"name": "neglect_7_days_no_dialogue", "title": "一周沉默", "content": "主人一周没说话了...", "emotion": "悲伤难过"}
                ]
            }
        }
        
        # Test multiple days
        test_days = 5
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
            
            # Generate random events for the day (3-8 events)
            num_events = random.randint(3, 8)
            print(f"📡 第 {day} 天发生 {num_events} 个事件:")
            
            for event_num in range(1, num_events + 1):
                # Randomly select event type and specific event
                event_type = random.choice(list(event_types.keys()))
                event_info = random.choice(event_types[event_type]["events"])
                
                # Create mock event
                event = MockEvent(
                    event_type=event_type,
                    event_name=event_info["name"],
                    user_id=1
                )
                
                daily_events.append({
                    "event_num": event_num,
                    "event": event,
                    "event_info": event_info
                })
                
                print(f"   事件 {event_num}: {event_types[event_type]['name']} - {event_info['name']}")
                
                # Step 3: Randomly decide if diary should be written for this event
                should_write = diary_manager.should_write_diary_for_event(event_type)
                
                if should_write:
                    # Write diary entry
                    diary_entry = diary_manager.write_diary_entry(
                        event=event,
                        title=event_info["title"],
                        content=event_info["content"],
                        emotion=event_info["emotion"]
                    )
                    
                    print(f"      ✍️  为事件 {event_num} 写日记: '{diary_entry.title}' - '{diary_entry.content}' ({diary_entry.emotion_tags[0].value})")
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
                        "event_type": e["event"].event_type,
                        "event_name": e["event"].event_name,
                        "title": e["event_info"]["title"],
                        "content": e["event_info"]["content"],
                        "emotion": e["event_info"]["emotion"]
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
                        "emotion": d.emotion_tags[0].value,
                        "timestamp": d.timestamp.isoformat()
                    }
                    for d in diary_manager.diary_entries
                ],
                "summary": summary
            }
            
            all_daily_results.append(daily_result)
        
        # Save all results
        with open('daily_diary_condition_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_daily_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 每日日记条件测试结果已保存到: daily_diary_condition_results.json")
        
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
                    print(f"     - {diary['title']}: {diary['content']} ({diary['emotion']})")
        
        print(f"\n🎉 每日日记条件测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.error(f"每日日记条件测试失败: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 启动每日日记条件测试")
    print("=" * 60)
    
    # Run the daily diary condition test
    asyncio.run(test_daily_diary_condition())
    
    print("\n🎯 所有测试完成!")
    print("查看 daily_diary_condition_results.json 获取详细结果")

if __name__ == "__main__":
    main()
