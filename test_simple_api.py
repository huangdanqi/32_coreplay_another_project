#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Diary API Test Client
Tests the simple API that processes events from events.json
"""

import requests
import json
import time
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add sensor event agent to path
current_dir = Path(__file__).parent
sensor_agent_path = current_dir / "sensor_event_agent"
sys.path.append(str(sensor_agent_path))

try:
    from sensor_event_agent.core.sensor_event_agent import SensorEventAgent
except ImportError:
    print("⚠️ Sensor Event Agent not available - sensor tests will be skipped")
    SensorEventAgent = None

# Configuration
API_CONFIG = {
    "base_url": "http://localhost:5003/api",
    "timeout": 30,
    "retry_attempts": 3
}

def make_api_request(method, endpoint, data=None):
    """Make API request with error handling."""
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
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    return None

def test_health_check():
    """Test health check."""
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

def test_bazi_wuxing_calc():
    """Test BaZi/WuXing calculation endpoint."""
    print("\n🈷️ Testing BaZi/WuXing Calc...")
    print("-" * 40)

    post_data = {
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 20,
        "birth_hour": 14,
        "birthplace": "北京"
    }

    print("📤 Sending payload:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    response = make_api_request('POST', '/bazi_wuxing/calc', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print("📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ BaZi/WuXing calc failed!")
        return False

def test_get_events():
    """Test getting events from events.json."""
    print("\n📋 Testing Get Events...")
    print("-" * 40)
    
    response = make_api_request('GET', '/events')
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Get events failed!")
        return False

def test_single_event_processing():
    """Test processing a single event."""
    print("\n🎯 Testing Single Event Processing...")
    print("-" * 50)
    
    # Test with a valid event from events.json (no event_details needed)
    post_data = {
        "event_category": "human_toy_interactive_function",
        "event_name": "liked_interaction_once"
    }
    
    print("📤 Sending single event:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/process', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            data = result.get('data', {})
            if data.get('diary_generated'):
                diary_entry = data.get('diary_entry', {})
                print(f"\n🎯 Generated Diary:")
                print(f"   📖 Title: {diary_entry.get('title', 'N/A')}")
                print(f"   📄 Content: {diary_entry.get('content', 'N/A')}")
                print(f"   😊 Emotion: {', '.join(diary_entry.get('emotion_tags', []))}")
            else:
                print(f"\n⏭️ No diary generated: {data.get('reason', 'Unknown')}")
        
        return result.get('success', False)
    else:
        print("❌ Single event processing failed!")
        return False

def test_batch_event_processing():
    """Test processing multiple events."""
    print("\n📚 Testing Batch Event Processing...")
    print("-" * 50)
    
    # Test with multiple events from different categories (no event_details needed)
    batch_data = {
        "events": [
            {
                "event_category": "human_toy_interactive_function",
                "event_name": "liked_interaction_3_to_5_times"
            },
            {
                "event_category": "human_toy_talk",
                "event_name": "positive_emotional_dialogue"
            },
            {
                "event_category": "unkeep_interactive",
                "event_name": "neglect_1_day_no_dialogue"
            }
        ]
    }
    
    print("📤 Sending batch events:")
    print(json.dumps(batch_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/batch-process', batch_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            data = result.get('data', {})
            generated_diaries = data.get('generated_diaries', [])
            results = data.get('results', [])
            
            print(f"\n🎯 Batch Processing Results:")
            print(f"   📝 Total Events: {data.get('total_events', 0)}")
            print(f"   📖 Diaries Generated: {data.get('diaries_generated', 0)}")
            
            for i, result_item in enumerate(results):
                status = result_item.get('status', 'unknown')
                event_name = result_item.get('event_name', 'N/A')
                print(f"   Event {i+1} ({event_name}): {status}")
                
                if status == "diary_generated":
                    diary_entry = result_item.get('diary_entry', {})
                    print(f"      📖 Title: {diary_entry.get('title', 'N/A')}")
                    print(f"      📄 Content: {diary_entry.get('content', 'N/A')}")
        
        return result.get('success', False)
    else:
        print("❌ Batch event processing failed!")
        return False

def test_invalid_event():
    """Test with invalid event."""
    print("\n❌ Testing Invalid Event...")
    print("-" * 40)
    
    # Test with invalid event (no event_details needed)
    post_data = {
        "event_category": "invalid_category",
        "event_name": "invalid_event"
    }
    
    print("📤 Sending invalid event:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/process', post_data)
    if response:
        print(f"📊 Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Check if error was handled properly
        if response.status_code == 400 and not result.get('success'):
            print("✅ Error handling working correctly!")
            return True
        else:
            print("❌ Error handling not working as expected!")
            return False
    else:
        print("❌ Invalid event test failed!")
        return False

def test_diary_generation():
    """Test diary generation with sample events."""
    print("\n🧪 Testing Diary Generation...")
    print("-" * 40)
    
    response = make_api_request('POST', '/diary/test', {})
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            data = result.get('data', {})
            test_results = data.get('test_results', [])
            
            print(f"\n🎯 Test Results:")
            print(f"   📝 Generated: {data.get('total_generated', 0)} diary entries")
            
            for i, test_result in enumerate(test_results):
                event_name = test_result.get('event_name', 'N/A')
                diary_entry = test_result.get('diary_entry', {})
                print(f"\n   📖 Diary {i+1} ({event_name}):")
                print(f"      Title: {diary_entry.get('title', 'N/A')}")
                print(f"      Content: {diary_entry.get('content', 'N/A')}")
                print(f"      Emotion: {', '.join(diary_entry.get('emotion_tags', []))}")
        
        return result.get('success', False)
    else:
        print("❌ Diary generation test failed!")
        return False

def test_event_extract():
    """Test Event Extraction Agent via API."""
    print("\n🧪 Testing Event Extraction (API)...")
    print("-" * 40)
    post_data = {
        "chat_uuid": "cu-1",
        "chat_event_uuid": "evt-1",
        "memory_uuid": "mem-1",
        "dialogue": "今天考试压力有点大，但朋友安慰了我，心里好受些了。"
    }
    print("📤 Sending extraction payload:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    response = make_api_request('POST', '/event/extract', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print("📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Event extraction failed!")
        return False

def test_event_update():
    """Test Event Update Agent via API (uses extraction then update)."""
    print("\n🧪 Testing Event Update (API)...")
    print("-" * 40)
    # First, call extraction to get a base event
    extract_payload = {
        "chat_uuid": "cu-2",
        "chat_event_uuid": "evt-2",
        "memory_uuid": "mem-1",
        "dialogue": "又要考试了，有点紧张，还好朋友继续鼓励我。"
    }
    extract_resp = make_api_request('POST', '/event/extract', extract_payload)
    if not extract_resp:
        print("❌ Pre-extraction failed!")
        return False
    extraction_result = extract_resp.json().get('data', {})
    # Provide a sample related event to exercise merge path
    related_events = [
        {
            "chat_uuid": "chat-history-1",
            "chat_event_uuid": "evt-history-1",
            "memory_uuid": "mem-1",
            "topic": "日常交流",
            "title": "考试担忧",
            "summary": "之前也为考试紧张，并得到朋友安慰。",
            "type": "new",
            "emotion": ["担忧", "平静"],
            "created_at": "2025-09-01T12:00:00"
        }
    ]
    post_data = {"extraction_result": extraction_result, "related_events": related_events}
    print("📤 Sending update payload:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    response = make_api_request('POST', '/event/update', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print("📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Event update failed!")
        return False

def test_event_pipeline():
    """Test Extraction→Update pipeline via API."""
    print("\n🧪 Testing Event Pipeline (API)...")
    print("-" * 40)
    body = {
        "dialogue_payload": {
            "chat_uuid": "cu-3",
            "chat_event_uuid": "evt-3",
            "memory_uuid": "mem-1",
            "dialogue": "这段时间复习考试，偶尔会焦虑，但朋友的安慰让我放松。"
        },
        "related_events": []
    }
    print("📤 Sending pipeline payload:")
    print(json.dumps(body, indent=2, ensure_ascii=False))
    response = make_api_request('POST', '/event/pipeline', body)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print("📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Event pipeline failed!")
        return False
async def test_sensor_event_single():
    """Test single sensor event translation."""
    if not SensorEventAgent:
        print("❌ Sensor Event Agent not available!")
        return False
    
    print("\n🤖 Testing Single Sensor Event Translation...")
    print("-" * 50)
    
    try:
        # Initialize sensor event agent
        agent = SensorEventAgent()
        
        # Test touch sensor event
        mqtt_message = {
            "sensor_type": "touch",
            "value": 1,
            "duration": 2.5
        }
        
        print("📤 Processing touch sensor event:")
        print(json.dumps(mqtt_message, indent=2, ensure_ascii=False))
        
        result = await agent.translate_sensor_event(mqtt_message)
        
        if result["success"]:
            print(f"✅ Translation successful!")
            print(f"   📝 Description: \"{result['description']}\"")
            print(f"   🔧 Sensor Type: {result['sensor_type']}")
            print(f"   📊 Event Type: {result['event_type']}")
            print(f"   🕐 Timestamp: {result['timestamp']}")
            return True
        else:
            print(f"❌ Translation failed!")
            print(f"   📝 Fallback: \"{result['description']}\"")
            print(f"   ⚠️ Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"💥 Sensor event test error: {e}")
        return False

async def test_sensor_event_batch():
    """Test batch sensor event processing."""
    if not SensorEventAgent:
        print("❌ Sensor Event Agent not available!")
        return False
    
    print("\n📚 Testing Batch Sensor Event Processing...")
    print("-" * 50)
    
    try:
        # Initialize sensor event agent
        agent = SensorEventAgent()
        
        # Test multiple sensor events
        mqtt_messages = [
            {
                "sensor_type": "touch",
                "value": 1,
                "duration": 2.5
            },
            {
                "sensor_type": "accelerometer",
                "x": 0.1,
                "y": 0.2,
                "z": 9.8,
                "count": 3
            },
            {
                "sensor_type": "gesture",
                "gesture_type": "shake",
                "confidence": 0.9
            },
            {
                "sensor_type": "sound",
                "decibel": 65,
                "frequency": 440
            }
        ]
        
        print("📤 Processing batch sensor events:")
        print(json.dumps(mqtt_messages, indent=2, ensure_ascii=False))
        
        results = agent.process_batch_messages(mqtt_messages)
        
        print(f"\n🎯 Batch Processing Results:")
        print(f"   📝 Total Events: {len(results)}")
        
        success_count = 0
        for i, result in enumerate(results):
            if result["success"]:
                print(f"   Event {i+1}: ✅ \"{result['description']}\" ({result.get('sensor_type', 'unknown')})")
                success_count += 1
            else:
                print(f"   Event {i+1}: ❌ Failed - {result.get('error', 'Unknown error')}")
        
        print(f"\n📈 Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        return success_count > 0
        
    except Exception as e:
        print(f"💥 Batch sensor event test error: {e}")
        return False

def test_sensor_event_interactive():
    """Interactive sensor event testing."""
    if not SensorEventAgent:
        print("❌ Sensor Event Agent not available!")
        return False
    
    print("\n🎮 Interactive Sensor Event Testing")
    print("-" * 50)
    print("Available sensor types:")
    print("1. touch - Touch sensor events")
    print("2. accelerometer - Motion/acceleration events")
    print("3. gesture - Gesture recognition events")
    print("4. sound - Sound/speech events")
    print("5. light - Light sensor events")
    print("6. temperature - Temperature sensor events")
    print("7. gyroscope - Rotation events")
    print("8. proximity - Proximity detection events")
    print("9. vibration - Vibration events")
    print("10. pressure - Pressure sensor events")
    print("11. humidity - Humidity sensor events")
    print("12. Exit")
    
    while True:
        try:
            choice = input("\n请选择传感器类型 (1-12): ").strip()
            
            if choice == "12":
                print("👋 退出传感器测试")
                break
            
            sensor_configs = {
                "1": {"sensor_type": "touch", "value": 1, "duration": 2.5},
                "2": {"sensor_type": "accelerometer", "x": 0.1, "y": 0.2, "z": 9.8, "count": 3},
                "3": {"sensor_type": "gesture", "gesture_type": "shake", "confidence": 0.9},
                "4": {"sensor_type": "sound", "decibel": 65, "frequency": 440},
                "5": {"sensor_type": "light", "lux": 300, "color": "white"},
                "6": {"sensor_type": "temperature", "temperature": 25.5, "humidity": 60},
                "7": {"sensor_type": "gyroscope", "yaw": 45, "pitch": 10, "roll": 5},
                "8": {"sensor_type": "proximity", "distance": 10, "detected": True},
                "9": {"sensor_type": "vibration", "intensity": 0.7, "frequency": 50},
                "10": {"sensor_type": "pressure", "pressure": 1013.25, "unit": "hPa"},
                "11": {"sensor_type": "humidity", "humidity": 60, "temperature": 25}
            }
            
            if choice in sensor_configs:
                sensor_data = sensor_configs[choice]
                print(f"\n📤 Testing {sensor_data['sensor_type']} sensor:")
                print(json.dumps(sensor_data, indent=2, ensure_ascii=False))
                
                # Run async test
                async def run_test():
                    agent = SensorEventAgent()
                    result = await agent.translate_sensor_event(sensor_data)
                    
                    if result["success"]:
                        print(f"✅ Translation: \"{result['description']}\"")
                    else:
                        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
                asyncio.run(run_test())
            else:
                print("❌ 无效选择")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    return True

async def run_all_tests():
    """Run all tests."""
    print("🚀 Running All Simple API Tests")
    print("=" * 60)
    
    # Original API tests
    api_tests = [
        ("Health Check", test_health_check),
        ("BaZi/WuXing Calc", test_bazi_wuxing_calc),
        ("Get Events", test_get_events),
        ("Single Event Processing", test_single_event_processing),
        ("Batch Event Processing", test_batch_event_processing),
        ("Invalid Event", test_invalid_event),
        ("Diary Generation", test_diary_generation),
        ("Event Extract (API)", test_event_extract),
        ("Event Update (API)", test_event_update),
        ("Event Pipeline (API)", test_event_pipeline)
    ]
    
    # Sensor event tests (if available)
    sensor_tests = []
    if SensorEventAgent:
        sensor_tests = [
            ("Single Sensor Event", test_sensor_event_single),
            ("Batch Sensor Events", test_sensor_event_batch)
        ]
    
    all_tests = api_tests + sensor_tests
    results = []
    
    for test_name, test_func in all_tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
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

def main():
    """Main function."""
    print("🚀 Simple Diary API Test Client")
    print("=" * 50)
    print(f"🌐 API Base URL: {API_CONFIG['base_url']}")
    print(f"⏰ Timeout: {API_CONFIG['timeout']} seconds")
    print(f"🔄 Retry Attempts: {API_CONFIG['retry_attempts']}")
    print("=" * 50)
    
    # Check if server is running (don't exit if down; allow sensor tests)
    print("🔍 Checking if simple API server is running...")
    api_ok = test_health_check()
    if not api_ok:
        print("\n⚠️ API server is not running. API tests may fail, but sensor tests are available.")
    
    print("\n选择运行模式:")
    print("1. 运行所有测试")
    print("2. 交互式测试")
    print("3. 传感器事件测试")
    print("4. 事件Agent接口测试")
    print("5. 八字五行计算测试")
    
    mode = input("请选择模式 (1-5): ").strip()
    
    if mode == "1":
        asyncio.run(run_all_tests())
    elif mode == "2":
        print("🎮 Interactive mode - run individual tests")
        while True:
            print("\n选择测试:")
            print("1. 健康检查")
            print("2. 获取事件")
            print("3. 八字五行计算")
            print("4. 单事件处理")
            print("5. 批量事件处理")
            print("6. 无效事件测试")
            print("7. 日记生成测试")
            if SensorEventAgent:
                print("8. 单传感器事件测试")
                print("9. 批量传感器事件测试")
                print("10. 交互式传感器测试")
                print("11. 退出")
            else:
                print("8. 退出")
            
            choice = input(f"请选择 (1-{'11' if SensorEventAgent else '8'}): ").strip()
            
            if choice == "1":
                test_health_check()
            elif choice == "2":
                test_get_events()
            elif choice == "3":
                test_bazi_wuxing_calc()
            elif choice == "4":
                test_single_event_processing()
            elif choice == "5":
                test_batch_event_processing()
            elif choice == "6":
                test_invalid_event()
            elif choice == "7":
                test_diary_generation()
            elif choice == "8" and SensorEventAgent:
                asyncio.run(test_sensor_event_single())
            elif choice == "9" and SensorEventAgent:
                asyncio.run(test_sensor_event_batch())
            elif choice == "10" and SensorEventAgent:
                test_sensor_event_interactive()
            elif choice == "11" and SensorEventAgent:
                print("👋 再见!")
                break
            elif choice == "8" and not SensorEventAgent:
                print("👋 再见!")
                break
            else:
                print("❌ 无效选择")
    elif mode == "3":
        if SensorEventAgent:
            print("🤖 Sensor Event Agent Testing")
            print("=" * 50)
            print("选择传感器测试模式:")
            print("1. 单传感器事件测试")
            print("2. 批量传感器事件测试")
            print("3. 交互式传感器测试")
            print("4. 运行所有传感器测试")
            
            sensor_choice = input("请选择 (1-4): ").strip()
            
            if sensor_choice == "1":
                asyncio.run(test_sensor_event_single())
            elif sensor_choice == "2":
                asyncio.run(test_sensor_event_batch())
            elif sensor_choice == "3":
                test_sensor_event_interactive()
            elif sensor_choice == "4":
                print("🚀 Running All Sensor Event Tests")
                print("=" * 50)
                asyncio.run(test_sensor_event_single())
                asyncio.run(test_sensor_event_batch())
            else:
                print("❌ 无效选择")
        else:
            print("❌ Sensor Event Agent not available!")
    elif mode == "4":
        print("🧩 事件Agent接口测试")
        print("=" * 50)
        print("1. 事件抽取 (POST /event/extract)")
        print("2. 事件更新 (POST /event/update)")
        print("3. 抽取→更新流水线 (POST /event/pipeline)")
        print("4. 运行全部事件Agent接口测试")
        choice = input("请选择 (1-4): ").strip()
        if choice == "1":
            test_event_extract()
        elif choice == "2":
            test_event_update()
        elif choice == "3":
            test_event_pipeline()
        elif choice == "4":
            print("🚀 Running All Event Agent API Tests")
            ok1 = test_event_extract()
            ok2 = test_event_update()
            ok3 = test_event_pipeline()
            print(f"\n结果: extract={ok1}, update={ok2}, pipeline={ok3}")
        else:
            print("❌ 无效选择")
    elif mode == "5":
        test_bazi_wuxing_calc()
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()
