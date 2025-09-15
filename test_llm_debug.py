#!/usr/bin/env python3
"""
Debug LLM issue with sensor event translation
"""

import asyncio
import json
import sys
from pathlib import Path

# Add paths
sys.path.append('diary_agent')
sys.path.append('sensor_event_agent')

from core.llm_manager import LLMConfigManager
from sensor_event_agent.core.mqtt_handler import MQTTHandler

async def test_llm_basic():
    """Test basic LLM functionality"""
    print("🧪 Testing basic LLM functionality...")
    
    try:
        llm_manager = LLMConfigManager()
        result = await llm_manager.generate_text_with_failover(
            prompt="请说'你好'",
            system_prompt="你是一个友好的助手"
        )
        print(f"✅ Basic LLM test result: '{result}'")
        return True
    except Exception as e:
        print(f"❌ Basic LLM test failed: {e}")
        return False

async def test_sensor_prompt():
    """Test the exact sensor prompt that's failing"""
    print("\n🧪 Testing sensor translation prompt...")
    
    try:
        # Load the prompt config
        with open('sensor_event_agent/config/prompt.json', 'r', encoding='utf-8') as f:
            prompt_config = json.load(f)
        
        # Create test MQTT message
        test_message = {
            "sensor_type": "accelerometer",
            "x": 0.1, "y": 0.2, "z": 9.8,
            "count": 3,
            "device_id": "toy_001"
        }
        
        # Parse using MQTT handler
        mqtt_handler = MQTTHandler()
        parsed_data = mqtt_handler.parse_mqtt_message(test_message)
        
        # Prepare the exact prompt
        template = prompt_config["user_prompt_template"]
        user_prompt = template.format(
            mqtt_message=parsed_data["mqtt_message"],
            sensor_data=json.dumps(parsed_data["sensor_data"], ensure_ascii=False),
            event_type=parsed_data["event_type"],
            timestamp=parsed_data["timestamp"],
            device_info=json.dumps(parsed_data["device_info"], ensure_ascii=False)
        )
        
        print(f"📝 System prompt: {prompt_config['system_prompt'][:100]}...")
        print(f"📝 User prompt length: {len(user_prompt)} characters")
        
        # Test with LLM
        llm_manager = LLMConfigManager()
        result = await llm_manager.generate_text_with_failover(
            prompt=user_prompt,
            system_prompt=prompt_config["system_prompt"]
        )
        
        print(f"🔍 Raw LLM result: '{result}'")
        print(f"🔍 Result type: {type(result)}")
        print(f"🔍 Result length: {len(result)}")
        
        # Try to parse as JSON
        try:
            parsed_result = json.loads(result.strip())
            print(f"✅ JSON parsing successful: {parsed_result}")
            description = parsed_result.get("description", "").strip()
            print(f"✅ Extracted description: '{description}'")
        except json.JSONDecodeError as je:
            print(f"❌ JSON parsing failed: {je}")
            print(f"🔍 Trying to extract manually...")
            
            if ":" in result:
                description = result.split(":", 1)[1].strip().strip('"')
                print(f"✅ Manually extracted: '{description}'")
            else:
                print(f"❌ Could not extract description from: '{result}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Sensor prompt test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🔧 Debugging LLM Integration Issue")
    print("=" * 50)
    
    # Test basic LLM
    basic_ok = await test_llm_basic()
    
    # Test sensor prompt
    sensor_ok = await test_sensor_prompt()
    
    print("\n" + "=" * 50)
    print("🎯 Debug Summary:")
    print(f"   Basic LLM: {'✅' if basic_ok else '❌'}")
    print(f"   Sensor prompt: {'✅' if sensor_ok else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())
