#!/usr/bin/env python3
"""
Test script for the Chinese cute sensor event translation agent.
Tests both fallback and LLM translation capabilities.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the sensor_event_agent to Python path
sys.path.append(str(Path(__file__).parent))

from core.sensor_event_agent import SensorEventAgent


async def test_fallback_translations():
    """Test the fallback translation system using sync translate method."""
    print("🧪 Testing fallback translations (using sync method)...")
    
    # Initialize the agent
    agent = SensorEventAgent()
    
    test_cases = [
        {
            "name": "Motion sensor",
            "mqtt_data": {"sensor_type": "accelerometer", "count": 5}
        },
        {
            "name": "Temperature sensor", 
            "mqtt_data": {"sensor_type": "temperature", "value": 25.5, "unit": "°C"}
        },
        {
            "name": "Light sensor",
            "mqtt_data": {"sensor_type": "light", "brightness": 80, "unit": "lux"}
        },
        {
            "name": "Sound sensor",
            "mqtt_data": {"sensor_type": "microphone", "volume": 65, "duration": 2.3}
        },
        {
            "name": "Unknown sensor",
            "mqtt_data": {"sensor_type": "mystery", "value": 42}
        }
    ]
    
    print("\n📋 Fallback Translation Results:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Convert to JSON string as the agent expects
            mqtt_message = json.dumps(test_case["mqtt_data"], ensure_ascii=False)
            
            # Get fallback translation using sync method
            result = agent.translate_sensor_event_sync(mqtt_message)
            
            print(f"{i}. {test_case['name']}")
            print(f"   Input: {mqtt_message}")
            print(f"   Output: {result['description']}")
            print(f"   Success: {'✅' if result['success'] else '❌'}")
            if not result['success']:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            print()
            
        except Exception as e:
            print(f"❌ Error testing {test_case['name']}: {e}")
            print()


async def test_llm_translations():
    """Test the LLM translation system."""
    print("\n🤖 Testing LLM translations...")
    
    # Initialize the agent
    agent = SensorEventAgent()
    
    # Test cases designed for Chinese cute translation
    test_cases = [
        {
            "name": "Simple motion",
            "mqtt_data": {"sensor_type": "accelerometer", "count": 3}
        },
        {
            "name": "Temperature reading",
            "mqtt_data": {"sensor_type": "temperature", "value": 23.2}
        },
        {
            "name": "Light detection",
            "mqtt_data": {"sensor_type": "light", "brightness": 45}
        }
    ]
    
    print("\n📋 LLM Translation Results:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # Convert to JSON string
            mqtt_message = json.dumps(test_case["mqtt_data"], ensure_ascii=False)
            
            print(f"{i}. Testing {test_case['name']}")
            print(f"   Input: {mqtt_message}")
            
            # Try LLM translation (note: method only takes mqtt_message parameter)
            result = await agent.translate_sensor_event(mqtt_message)
            
            print(f"   Output: {result['description']}")
            print(f"   Success: {'✅' if result['success'] else '❌'}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            print()
            
        except Exception as e:
            print(f"❌ Error testing {test_case['name']}: {e}")
            print()


async def test_mqtt_parsing():
    """Test MQTT message parsing."""
    print("\n🔍 Testing MQTT message parsing...")
    
    agent = SensorEventAgent()
    
    # Test various MQTT message formats
    test_messages = [
        '{"sensor_type": "accelerometer", "count": 3}',
        '{"sensor_type": "temperature", "value": 23.5, "unit": "celsius"}',
        '{"sensor_type": "light", "brightness": 75}',
        'invalid_json_format',  # Should be handled gracefully
        '{"malformed": json}',  # Invalid JSON
        '{}',  # Empty JSON
    ]
    
    print("\n📋 MQTT Parsing Results:")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        try:
            # Test with sync method which has better error handling
            result = agent.translate_sensor_event_sync(message)
            status = "✅ Success" if result['success'] else "❌ Failed"
            
            print(f"{i}. {status}")
            print(f"   Input: {message}")
            print(f"   Output: {result['description']}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            print()
            
        except Exception as e:
            print(f"{i}. ❌ Exception")
            print(f"   Input: {message}")
            print(f"   Error: {e}")
            print()


async def main():
    """Run all tests."""
    print("🚀 Starting sensor event translation agent tests...")
    print("=" * 60)
    
    try:
        # Test fallback system
        await test_fallback_translations()
        
        # Test LLM system  
        await test_llm_translations()
        
        # Test MQTT parsing
        await test_mqtt_parsing()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
