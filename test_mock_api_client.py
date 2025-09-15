#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock API Test Client
This client tests the mock API server by sending POST requests and displaying results.
Can easily be configured to use cloud server in the future.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration - Easy to change for cloud deployment
API_CONFIG = {
    "base_url": "http://localhost:5001/api",  # Change to cloud URL when ready
    "timeout": 10,
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

def test_single_diary_generation():
    """Test single diary generation with POST request."""
    print("\n📝 Testing Single Diary Generation (POST)...")
    print("-" * 50)
    
    # Sample POST data
    post_data = {
        "event_type": "human_machine_interaction",
        "event_name": "liked_interaction_once",
        "event_details": {
            "interaction_type": "抚摸",
            "duration": "5分钟",
            "user_response": "positive",
            "toy_emotion": "开心"
        },
        "user_id": 1
    }
    
    print("📤 Sending POST request with data:")
    print(json.dumps(post_data, indent=2, ensure_ascii=False))
    print("\n⏳ Waiting for response...")
    
    response = make_api_request('POST', '/diary/generate', post_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            diary_data = result.get('data', {})
            print(f"\n🎯 Generated Diary:")
            print(f"   📖 Title: {diary_data.get('title', 'N/A')}")
            print(f"   📄 Content: {diary_data.get('content', 'N/A')}")
            print(f"   😊 Emotion: {', '.join(diary_data.get('emotion_tags', []))}")
            print(f"   🕒 Timestamp: {diary_data.get('timestamp', 'N/A')}")
        
        return result.get('success', False)
    else:
        print("❌ Single diary generation failed!")
        return False

def test_batch_diary_generation():
    """Test batch diary generation with POST request."""
    print("\n📚 Testing Batch Diary Generation (POST)...")
    print("-" * 50)
    
    # Sample batch POST data
    batch_data = {
        "events": [
            {
                "event_type": "human_machine_interaction",
                "event_name": "liked_interaction_3_to_5_times",
                "event_details": {
                    "interaction_type": "摸摸头",
                    "count": 4,
                    "duration": "20分钟",
                    "user_response": "positive",
                    "toy_emotion": "平静"
                }
            },
            {
                "event_type": "dialogue",
                "event_name": "positive_emotional_dialogue",
                "event_details": {
                    "dialogue_type": "开心对话",
                    "content": "主人今天心情很好",
                    "duration": "10分钟",
                    "toy_emotion": "开心快乐"
                }
            },
            {
                "event_type": "neglect",
                "event_name": "neglect_1_day_no_dialogue",
                "event_details": {
                    "neglect_duration": 1,
                    "neglect_type": "no_dialogue",
                    "disconnection_type": "无对话有互动",
                    "disconnection_days": 1,
                    "memory_status": "on",
                    "last_interaction_date": (datetime.now() - timedelta(days=1)).isoformat()
                }
            }
        ],
        "daily_diary_count": 3,
        "user_id": 1
    }
    
    print("📤 Sending batch POST request with data:")
    print(json.dumps(batch_data, indent=2, ensure_ascii=False))
    print("\n⏳ Waiting for response...")
    
    response = make_api_request('POST', '/diary/batch', batch_data)
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            batch_info = result.get('data', {})
            diary_entries = batch_info.get('diary_entries', [])
            print(f"\n🎯 Generated {len(diary_entries)} Diary Entries:")
            
            for i, diary in enumerate(diary_entries, 1):
                print(f"\n   📖 Diary {i}:")
                print(f"      Title: {diary.get('title', 'N/A')}")
                print(f"      Content: {diary.get('content', 'N/A')}")
                print(f"      Emotion: {', '.join(diary.get('emotion_tags', []))}")
                print(f"      Event Type: {diary.get('event_type', 'N/A')}")
        
        return result.get('success', False)
    else:
        print("❌ Batch diary generation failed!")
        return False

def test_random_diary_generation():
    """Test random diary generation with POST request."""
    print("\n🎲 Testing Random Diary Generation (POST)...")
    print("-" * 50)
    
    print("📤 Sending POST request for random diary...")
    print("⏳ Waiting for response...")
    
    response = make_api_request('POST', '/diary/random', {})
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            diary_data = result.get('data', {})
            print(f"\n🎯 Random Generated Diary:")
            print(f"   📖 Title: {diary_data.get('title', 'N/A')}")
            print(f"   📄 Content: {diary_data.get('content', 'N/A')}")
            print(f"   😊 Emotion: {', '.join(diary_data.get('emotion_tags', []))}")
            print(f"   🎲 Event Type: {diary_data.get('event_type', 'N/A')}")
        
        return result.get('success', False)
    else:
        print("❌ Random diary generation failed!")
        return False

def test_get_templates():
    """Test getting event templates."""
    print("\n📋 Testing Event Templates (GET)...")
    print("-" * 40)
    
    response = make_api_request('GET', '/diary/templates')
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Get templates failed!")
        return False

def test_diary_system():
    """Test the diary system with sample data."""
    print("\n🧪 Testing Diary System (POST)...")
    print("-" * 40)
    
    response = make_api_request('POST', '/diary/test', {})
    if response:
        print(f"✅ Status Code: {response.status_code}")
        result = response.json()
        print(f"📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get('success', False)
    else:
        print("❌ Diary system test failed!")
        return False

def test_error_handling():
    """Test error handling with invalid data."""
    print("\n❌ Testing Error Handling...")
    print("-" * 40)
    
    # Test with missing required field
    invalid_data = {
        "event_type": "human_machine_interaction",
        # Missing event_name and event_details
    }
    
    print("📤 Sending invalid POST request:")
    print(json.dumps(invalid_data, indent=2, ensure_ascii=False))
    
    response = make_api_request('POST', '/diary/generate', invalid_data)
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
        print("❌ Error handling test failed!")
        return False

def interactive_test_mode():
    """Interactive testing mode."""
    print("🎮 Interactive Mock API Test Mode")
    print("=" * 50)
    
    while True:
        print("\n选择测试:")
        print("1. 健康检查")
        print("2. 生成单篇日记")
        print("3. 批量生成日记")
        print("4. 随机生成日记")
        print("5. 获取事件模板")
        print("6. 系统测试")
        print("7. 错误处理测试")
        print("8. 运行所有测试")
        print("9. 退出")
        
        choice = input("\n请输入选择 (1-9): ").strip()
        
        if choice == "1":
            test_health_check()
        elif choice == "2":
            test_single_diary_generation()
        elif choice == "3":
            test_batch_diary_generation()
        elif choice == "4":
            test_random_diary_generation()
        elif choice == "5":
            test_get_templates()
        elif choice == "6":
            test_diary_system()
        elif choice == "7":
            test_error_handling()
        elif choice == "8":
            run_all_tests()
        elif choice == "9":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

def run_all_tests():
    """Run all tests and show summary."""
    print("🚀 Running All Mock API Tests")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Single Diary Generation", test_single_diary_generation),
        ("Batch Diary Generation", test_batch_diary_generation),
        ("Random Diary Generation", test_random_diary_generation),
        ("Get Templates", test_get_templates),
        ("Diary System Test", test_diary_system),
        ("Error Handling", test_error_handling)
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

def main():
    """Main function."""
    print("🎭 Mock API Test Client")
    print("=" * 50)
    print(f"🌐 API Base URL: {API_CONFIG['base_url']}")
    print(f"⏰ Timeout: {API_CONFIG['timeout']} seconds")
    print(f"🔄 Retry Attempts: {API_CONFIG['retry_attempts']}")
    print("=" * 50)
    
    # Check if server is running
    print("🔍 Checking if mock server is running...")
    if not test_health_check():
        print("\n❌ Mock server is not running!")
        print("🚀 Please start the mock server first:")
        print("   python mock_api_server.py")
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

