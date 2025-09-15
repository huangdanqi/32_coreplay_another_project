#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Usage Examples for Diary System
This file contains examples of how to use the Diary System API.
"""

import requests
import json
from datetime import datetime, timedelta

# API Base URL
API_BASE_URL = "http://localhost:5000/api"

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing Health Check...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def test_single_diary_generation():
    """Test single diary generation."""
    print("📝 Testing Single Diary Generation...")
    
    # Sample request data
    request_data = {
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
    
    response = requests.post(
        f"{API_BASE_URL}/diary/generate",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def test_batch_diary_generation():
    """Test batch diary generation."""
    print("📚 Testing Batch Diary Generation...")
    
    # Sample batch request data
    batch_request_data = {
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
    
    response = requests.post(
        f"{API_BASE_URL}/diary/batch",
        json=batch_request_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def test_get_templates():
    """Test getting event templates."""
    print("📋 Testing Event Templates...")
    
    response = requests.get(f"{API_BASE_URL}/diary/templates")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def test_diary_system():
    """Test the diary system with sample data."""
    print("🧪 Testing Diary System...")
    
    response = requests.post(f"{API_BASE_URL}/diary/test")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def test_error_handling():
    """Test error handling with invalid data."""
    print("❌ Testing Error Handling...")
    
    # Test with missing required field
    invalid_request = {
        "event_type": "human_machine_interaction",
        # Missing event_name and event_details
    }
    
    response = requests.post(
        f"{API_BASE_URL}/diary/generate",
        json=invalid_request,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print("-" * 50)

def interactive_diary_generator():
    """Interactive diary generator using the API."""
    print("🎮 Interactive Diary Generator")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 生成单篇日记")
        print("2. 批量生成日记")
        print("3. 查看事件模板")
        print("4. 测试系统")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            generate_single_diary_interactive()
        elif choice == "2":
            generate_batch_diary_interactive()
        elif choice == "3":
            test_get_templates()
        elif choice == "4":
            test_diary_system()
        elif choice == "5":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

def generate_single_diary_interactive():
    """Interactive single diary generation."""
    print("\n📝 生成单篇日记")
    print("-" * 30)
    
    # Get event type
    print("事件类型:")
    print("1. human_machine_interaction (人机互动)")
    print("2. dialogue (对话)")
    print("3. neglect (忽视)")
    
    event_type_choice = input("选择事件类型 (1-3): ").strip()
    event_type_map = {
        "1": "human_machine_interaction",
        "2": "dialogue", 
        "3": "neglect"
    }
    
    if event_type_choice not in event_type_map:
        print("❌ 无效选择")
        return
    
    event_type = event_type_map[event_type_choice]
    event_name = input("输入事件名称: ").strip()
    
    # Get event details
    print("输入事件详情 (JSON格式):")
    print("示例: {\"interaction_type\": \"抚摸\", \"duration\": \"5分钟\", \"toy_emotion\": \"开心\"}")
    event_details_str = input("事件详情: ").strip()
    
    try:
        event_details = json.loads(event_details_str)
    except json.JSONDecodeError:
        print("❌ 无效的JSON格式")
        return
    
    # Make API request
    request_data = {
        "event_type": event_type,
        "event_name": event_name,
        "event_details": event_details,
        "user_id": 1
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/diary/generate",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                diary_data = result["data"]
                print(f"\n✅ 日记生成成功!")
                print(f"标题: {diary_data['title']}")
                print(f"内容: {diary_data['content']}")
                print(f"情感标签: {', '.join(diary_data['emotion_tags'])}")
            else:
                print(f"❌ 生成失败: {result['message']}")
        else:
            print(f"❌ API错误: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器正在运行")

def generate_batch_diary_interactive():
    """Interactive batch diary generation."""
    print("\n📚 批量生成日记")
    print("-" * 30)
    
    events = []
    
    while True:
        print(f"\n当前事件数量: {len(events)}")
        print("1. 添加事件")
        print("2. 生成日记")
        print("3. 返回主菜单")
        
        choice = input("选择操作 (1-3): ").strip()
        
        if choice == "1":
            # Add event
            print("\n添加事件:")
            print("事件类型:")
            print("1. human_machine_interaction (人机互动)")
            print("2. dialogue (对话)")
            print("3. neglect (忽视)")
            
            event_type_choice = input("选择事件类型 (1-3): ").strip()
            event_type_map = {
                "1": "human_machine_interaction",
                "2": "dialogue",
                "3": "neglect"
            }
            
            if event_type_choice not in event_type_map:
                print("❌ 无效选择")
                continue
            
            event_type = event_type_map[event_type_choice]
            event_name = input("输入事件名称: ").strip()
            
            print("输入事件详情 (JSON格式):")
            event_details_str = input("事件详情: ").strip()
            
            try:
                event_details = json.loads(event_details_str)
                events.append({
                    "event_type": event_type,
                    "event_name": event_name,
                    "event_details": event_details
                })
                print("✅ 事件添加成功")
            except json.JSONDecodeError:
                print("❌ 无效的JSON格式")
                
        elif choice == "2":
            if not events:
                print("❌ 没有事件可生成")
                continue
            
            # Generate batch diary
            batch_request_data = {
                "events": events,
                "daily_diary_count": len(events),
                "user_id": 1
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/diary/batch",
                    json=batch_request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        diary_entries = result["data"]["diary_entries"]
                        print(f"\n✅ 批量生成成功! 共生成 {len(diary_entries)} 篇日记")
                        
                        for i, diary in enumerate(diary_entries, 1):
                            print(f"\n日记 {i}:")
                            print(f"  标题: {diary['title']}")
                            print(f"  内容: {diary['content']}")
                            print(f"  情感标签: {', '.join(diary['emotion_tags'])}")
                    else:
                        print(f"❌ 生成失败: {result['message']}")
                else:
                    print(f"❌ API错误: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print("❌ 无法连接到API服务器，请确保服务器正在运行")
                
        elif choice == "3":
            break
        else:
            print("❌ 无效选择")

def main():
    """Main function to run all tests."""
    print("🚀 Diary System API Usage Examples")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务器正在运行")
        else:
            print("❌ API服务器响应异常")
            return
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("请先启动API服务器: python api_diary_system.py")
        return
    
    print("\n选择运行模式:")
    print("1. 运行所有测试")
    print("2. 交互式日记生成器")
    
    mode = input("请选择模式 (1-2): ").strip()
    
    if mode == "1":
        # Run all tests
        test_health_check()
        test_single_diary_generation()
        test_batch_diary_generation()
        test_get_templates()
        test_diary_system()
        test_error_handling()
        print("\n🎉 所有测试完成!")
        
    elif mode == "2":
        # Interactive mode
        interactive_diary_generator()
        
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()

