"""
Example usage of Sensor Event Translation Agent
Demonstrates how to use the agent to translate MQTT sensor messages.
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from core.sensor_event_agent import SensorEventAgent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Main example function."""
    print("🤖 传感器事件翻译Agent示例")
    print("=" * 50)
    
    # Initialize agent
    try:
        agent = SensorEventAgent()
        print("✅ Agent初始化成功")
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        return
    
    # Example MQTT messages
    example_messages = [
        # Accelerometer - Motion
        {
            "sensor_type": "accelerometer",
            "x": 0.2,
            "y": 0.1,  
            "z": 9.8,
            "count": 3,
            "device_id": "toy_001",
            "timestamp": datetime.now().isoformat()
        },
        
        # Touch sensor
        {
            "sensor_type": "touch",
            "value": 1,
            "duration": 2.5,
            "pressure": 15,
            "device_id": "toy_001",
            "timestamp": datetime.now().isoformat()
        },
        
        # Gyroscope - Rotation
        {
            "sensor_type": "gyroscope",
            "yaw": 90,
            "pitch": 10,
            "roll": 5,
            "speed": "fast",
            "device_id": "toy_001",
            "timestamp": datetime.now().isoformat()
        },
        
        # Gesture recognition
        {
            "sensor_type": "gesture",
            "gesture_type": "shake",
            "confidence": 0.95,
            "direction": "horizontal",
            "count": 2,
            "device_id": "toy_001",
            "timestamp": datetime.now().isoformat()
        },
        
        # Sound sensor
        {
            "sensor_type": "sound",
            "decibel": 65,
            "frequency": 1000,
            "sound_type": "bark",
            "duration": 1.2,
            "device_id": "toy_001",
            "timestamp": datetime.now().isoformat()
        },
        
        # Light sensor
        {
            "sensor_type": "light",
            "lux": 300,
            "brightness": 75,
            "light_type": "ambient",
            "device_id": "toy_001",
            "timestamp": datetime.now().isoformat()
        },
        
        # Temperature sensor
        {
            "sensor_type": "temperature",
            "temperature": 28.5,
            "humidity": 60,
            "unit": "celsius",
            "device_id": "toy_001",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    print("\\n📨 处理示例MQTT消息:")
    print("-" * 30)
    
    # Process each example message
    for i, message in enumerate(example_messages, 1):
        print(f"\\n📍 示例 {i}: {message['sensor_type']}")
        print(f"原始数据: {json.dumps(message, ensure_ascii=False)}")
        
        try:
            # Translate using LLM (async)
            result = await agent.translate_sensor_event(message)
            
            if result["success"]:
                print(f"✅ 翻译结果: \"{result['description']}\"")
                print(f"   传感器类型: {result['sensor_type']}")
                print(f"   事件类型: {result['event_type']}")
            else:
                print(f"❌ 翻译失败: {result.get('error', '未知错误')}")
                print(f"   备用描述: \"{result['description']}\"")
                
        except Exception as e:
            print(f"❌ 处理错误: {e}")
    
    print("\\n" + "=" * 50)
    
    # Demonstrate batch processing (synchronous)
    print("\\n🔄 批量处理示例 (同步模式):")
    print("-" * 30)
    
    batch_messages = example_messages[:3]  # Process first 3 messages
    batch_results = agent.process_batch_messages(batch_messages)
    
    for i, result in enumerate(batch_results, 1):
        if result["success"]:
            print(f"{i}. \"{result['description']}\" ({result['sensor_type']})")
        else:
            print(f"{i}. 处理失败: {result.get('error', '未知错误')}")
    
    print("\\n" + "=" * 50)
    
    # Test with invalid messages
    print("\\n⚠️  测试无效消息处理:")
    print("-" * 30)
    
    invalid_messages = [
        # Missing sensor_type
        {"value": 100, "device_id": "toy_001"},
        
        # Invalid JSON string  
        '{"sensor_type": "invalid", "missing_bracket": true',
        
        # Empty message
        {},
        
        # String message
        "this is not a valid json message"
    ]
    
    for i, invalid_msg in enumerate(invalid_messages, 1):
        print(f"\\n❌ 无效消息 {i}:")
        try:
            result = await agent.translate_sensor_event(invalid_msg)
            print(f"   处理结果: \"{result['description']}\"")
            print(f"   成功状态: {result['success']}")
            if not result['success']:
                print(f"   错误信息: {result.get('error', 'N/A')}")
        except Exception as e:
            print(f"   异常: {e}")
    
    print("\\n🎉 示例演示完成!")


def demo_mqtt_message_formats():
    """Demonstrate different MQTT message formats."""
    print("\\n📋 支持的MQTT消息格式示例:")
    print("-" * 40)
    
    formats = {
        "标准格式": {
            "sensor_type": "accelerometer",
            "value": 25.6,
            "x": 0.1,
            "y": 0.2, 
            "z": 9.8,
            "device_id": "toy_001",
            "timestamp": "2024-01-01T12:00:00"
        },
        
        "简化格式": {
            "type": "touch",
            "data": 1,
            "id": "toy_002"
        },
        
        "扩展格式": {
            "sensor_type": "gesture",
            "gesture_type": "wave",
            "confidence": 0.85,
            "count": 1,
            "device_name": "智能玩具",
            "location": "客厅",
            "battery": 85,
            "timestamp": "2024-01-01T12:00:00"
        }
    }
    
    for format_name, example in formats.items():
        print(f"\\n{format_name}:")
        print(json.dumps(example, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # Show supported message formats
    demo_mqtt_message_formats()
    
    # Run main example
    asyncio.run(main())
