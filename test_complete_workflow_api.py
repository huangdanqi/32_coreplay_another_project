#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Workflow API Test Client
This client tests the complete diary agent workflow API with all event types.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration - Easy to change for cloud deployment
API_CONFIG = {
    "base_url": "http://localhost:5002/api",  # Change to cloud URL when ready
    "timeout": 30,
    "retry_attempts": 3
}

def make_api_request(method, endpoint, data=None):
    """Make API request with error handling and retries."""
    url = f"{API_CONFIG['base_url']}{endpoint}"
    
    for attempt in range(API_CONFIG['retry_attempts']):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=API_CONFIG['timeout'])
            elif method.upper() == 'POST':
                response = requests.post(
                    url, 
                    json=data, 
                    headers={"Content-Type": "application/json"},
                    timeout=API_CONFIG['timeout']
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed (attempt {attempt + 1}/{API_CONFIG['retry_attempts']})")
            if attempt < API_CONFIG['retry_attempts'] - 1:
                print("⏳ Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print("❌ All connection attempts failed!")
                return None
        except requests.exceptions.Timeout:
            print(f"⏰ Request timeout (attempt {attempt + 1}/{API_CONFIG['retry_attempts']})")
            if attempt < API_CONFIG['retry_attempts'] - 1:
                time.sleep(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    return None

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing Health Check...")
    print("-" * 40)
    
    response = make_api_request('GET', '/health')
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Health check failed!")
        return False

def test_daily_plan_creation():
    """Test daily plan creation (00:00 daily task)."""
    print("\n📅 Testing Daily Plan Creation...")
    print("-" * 50)
    
    post_data = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    print("📤 Creating daily plan:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/daily-plan', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Daily plan creation failed!")
        return False

def test_weather_event():
    """Test weather category diary generation."""
    print("\n🌤️ Testing Weather Event Diary Generation...")
    print("-" * 50)
    
    post_data = {
        "event_type": "weather",
        "event_name": "sunny_day_event",
        "event_details": {
            "city": "北京",
            "weather_changes": "晴天转多云，温度适宜",
            "liked_weather": "晴天",
            "disliked_weather": "雨天",
            "personality_type": "开朗活泼",
            "temperature": "22°C",
            "humidity": "65%"
        },
        "user_id": 1
    }
    
    print("📤 Sending weather event:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/generate', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success') and result.get('data', {}).get('should_write'):
            diary_data = result.get('data', {})
            print(f"\n🎯 Generated Weather Diary:")
            print(f"   📖 Title: {diary_data.get('title', 'N/A')}")
            print(f"   📄 Content: {diary_data.get('content', 'N/A')}")
            print(f"   😊 Emotion: {', '.join(diary_data.get('emotion_tags', []))}")
        
        return result.get('success', False)
    else:
        print("❌ Weather event test failed!")
        return False

def test_human_machine_interaction():
    """Test human-machine interaction event."""
    print("\n🤖 Testing Human-Machine Interaction Event...")
    print("-" * 50)
    
    post_data = {
        "event_type": "human_machine_interaction",
        "event_name": "petting_session",
        "event_details": {
            "interaction_type": "抚摸",
            "duration": "10分钟",
            "user_response": "positive",
            "toy_emotion": "开心",
            "interaction_intensity": "gentle",
            "location": "客厅"
        },
        "user_id": 1
    }
    
    print("📤 Sending interaction event:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/generate', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success') and result.get('data', {}).get('should_write'):
            diary_data = result.get('data', {})
            print(f"\n🎯 Generated Interaction Diary:")
            print(f"   📖 Title: {diary_data.get('title', 'N/A')}")
            print(f"   📄 Content: {diary_data.get('content', 'N/A')}")
            print(f"   😊 Emotion: {', '.join(diary_data.get('emotion_tags', []))}")
        
        return result.get('success', False)
    else:
        print("❌ Human-machine interaction test failed!")
        return False

def test_holiday_event():
    """Test holiday category event."""
    print("\n🎉 Testing Holiday Event...")
    print("-" * 50)
    
    post_data = {
        "event_type": "holiday",
        "event_name": "spring_festival_day2",
        "event_details": {
            "time_description": "春节第2天",
            "holiday_name": "春节",
            "festivity_level": "high",
            "family_gathering": True,
            "special_activities": ["拜年", "吃饺子", "放烟花"]
        },
        "user_id": 1
    }
    
    print("📤 Sending holiday event:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/generate', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success') and result.get('data', {}).get('should_write'):
            diary_data = result.get('data', {})
            print(f"\n🎯 Generated Holiday Diary:")
            print(f"   📖 Title: {diary_data.get('title', 'N/A')}")
            print(f"   📄 Content: {diary_data.get('content', 'N/A')}")
            print(f"   😊 Emotion: {', '.join(diary_data.get('emotion_tags', []))}")
        
        return result.get('success', False)
    else:
        print("❌ Holiday event test failed!")
        return False

def test_batch_events():
    """Test batch processing of multiple event types."""
    print("\n📚 Testing Batch Event Processing...")
    print("-" * 50)
    
    batch_data = {
        "events": [
            {
                "event_type": "season",
                "event_name": "spring_arrival",
                "event_details": {
                    "city": "上海",
                    "season": "春季",
                    "temperature": "18°C",
                    "liked_season": "春季",
                    "disliked_season": "冬季",
                    "personality_type": "温和"
                }
            },
            {
                "event_type": "current_affairs",
                "event_name": "major_beneficial_event",
                "event_details": {
                    "event_name": "科技突破",
                    "event_tags": ["重大利好", "科技创新"],
                    "event_type": "major_beneficial",
                    "impact_level": "high"
                }
            },
            {
                "event_type": "human_machine_dialogue",
                "event_name": "emotional_conversation",
                "event_details": {
                    "event_summary": "主人分享了一天的心情",
                    "event_title": "心情分享",
                    "content_theme": "情感交流",
                    "owner_emotion": "开心",
                    "dialogue_duration": "15分钟"
                }
            }
        ],
        "user_id": 1
    }
    
    print("📤 Sending batch events:")
    print(json.dumps(batch_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/batch', batch_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            batch_info = result.get('data', {})
            diary_entries = batch_info.get('diary_entries', [])
            skipped_events = batch_info.get('skipped_events', [])
            
            print(f"\n🎯 Batch Processing Results:")
            print(f"   📝 Generated: {len(diary_entries)} diary entries")
            print(f"   ⏭️ Skipped: {len(skipped_events)} events")
            
            for i, diary in enumerate(diary_entries, 1):
                print(f"\n   📖 Diary {i} ({diary.get('event_type', 'N/A')}):")
                print(f"      Title: {diary.get('title', 'N/A')}")
                print(f"      Content: {diary.get('content', 'N/A')}")
                print(f"      Emotion: {', '.join(diary.get('emotion_tags', []))}")
        
        return result.get('success', False)
    else:
        print("❌ Batch processing test failed!")
        return False

def test_daily_status():
    """Test getting daily status."""
    print("\n📊 Testing Daily Status...")
    print("-" * 40)
    
    response = make_api_request('GET', '/diary/daily-status')
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Daily status test failed!")
        return False

def test_event_types():
    """Test getting supported event types."""
    print("\n📋 Testing Event Types...")
    print("-" * 40)
    
    response = make_api_request('GET', '/diary/event-types')
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Event types test failed!")
        return False

def test_complete_workflow():
    """Test the complete workflow."""
    print("\n🧪 Testing Complete Workflow...")
    print("-" * 50)
    
    response = make_api_request('POST', '/diary/workflow-test', {})
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            workflow_data = result.get('data', {})
            test_results = workflow_data.get('test_results', [])
            daily_plan = workflow_data.get('daily_plan', {})
            
            print(f"\n🎯 Complete Workflow Results:")
            print(f"   📅 Daily Plan: {daily_plan.get('planned_count', 0)} planned, {daily_plan.get('written_count', 0)} written")
            print(f"   📝 Generated: {len(test_results)} diary entries")
            
            for i, diary in enumerate(test_results, 1):
                print(f"\n   📖 Diary {i} ({diary.get('event_type', 'N/A')}):")
                print(f"      Title: {diary.get('title', 'N/A')}")
                print(f"      Content: {diary.get('content', 'N/A')}")
                print(f"      Emotion: {', '.join(diary.get('emotion_tags', []))}")
        
        return result.get('success', False)
    else:
        print("❌ Complete workflow test failed!")
        return False

def run_all_tests():
    """Run all tests and show summary."""
    print("🚀 Running All Complete Workflow API Tests")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Daily Plan Creation", test_daily_plan_creation),
        ("Weather Event", test_weather_event),
        ("Human-Machine Interaction", test_human_machine_interaction),
        ("Holiday Event", test_holiday_event),
        ("Batch Events", test_batch_events),
        ("Daily Status", test_daily_status),
        ("Event Types", test_event_types),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 Test Summary:")
    print("=" * 40)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    print(f"📈 Success Rate: {(passed/total*100):.1f}%")

def interactive_test_mode():
    """Interactive testing mode."""
    print("🎮 Interactive Complete Workflow Test Mode")
    print("=" * 50)
    
    while True:
        print("\n选择测试:")
        print("1. 健康检查")
        print("2. 创建每日计划")
        print("3. 天气事件测试")
        print("4. 人机互动测试")
        print("5. 节日事件测试")
        print("6. 批量事件测试")
        print("7. 每日状态查询")
        print("8. 事件类型查询")
        print("9. 完整工作流测试")
        print("10. 运行所有测试")
        print("11. 退出")
        
        choice = input("\n请输入选择 (1-11): ").strip()
        
        if choice == "1":
            test_health_check()
        elif choice == "2":
            test_daily_plan_creation()
        elif choice == "3":
            test_weather_event()
        elif choice == "4":
            test_human_machine_interaction()
        elif choice == "5":
            test_holiday_event()
        elif choice == "6":
            test_batch_events()
        elif choice == "7":
            test_daily_status()
        elif choice == "8":
            test_event_types()
        elif choice == "9":
            test_complete_workflow()
        elif choice == "10":
            run_all_tests()
        elif choice == "11":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

def main():
    """Main function."""
    print("🚀 Complete Diary Agent Workflow API Test Client")
    print("=" * 60)
    print(f"🌐 API Base URL: {API_CONFIG['base_url']}")
    print(f"⏰ Timeout: {API_CONFIG['timeout']} seconds")
    print(f"🔄 Retry Attempts: {API_CONFIG['retry_attempts']}")
    print("=" * 60)
    
    # Check if server is running
    print("🔍 Checking if complete workflow server is running...")
    if not test_health_check():
        print("\n❌ Complete workflow server is not running!")
        print("🚀 Please start the complete workflow server first:")
        print("   python complete_diary_agent_api.py")
        return
    
    print("\n选择运行模式:")
    print("1. 运行所有测试")
    print("2. 交互式测试模式")
    
    mode = input("请选择模式 (1-2): ").strip()
    
    if mode == "1":
        run_all_tests()
    elif mode == "2":
        interactive_test_mode()
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()

