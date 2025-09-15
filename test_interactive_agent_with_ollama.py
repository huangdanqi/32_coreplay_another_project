#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Interactive Agent with Ollama LLM for Human-Machine Interaction Event.

This script tests the complete workflow using:
1. interactive_agent.py from the diary agent system
2. Local Ollama LLM for content generation
3. Human-Machine Interaction Event (Section 3.8) processing
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
        logging.FileHandler('test_interactive_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockMQTTEvent:
    """Mock MQTT event for testing."""
    
    def __init__(self, event_type: str = "same_frequency_event", user_id: int = 1):
        self.event_type = event_type
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.payload = {
            "event_type": event_type,
            "user_id": user_id,
            "interaction_type": "摸摸脸",
            "same_frequency_event": "一起玩耍",
            "toy_owner_nickname": "小明",
            "close_friend_nickname": "小红",
            "close_friend_owner_nickname": "小红的妈妈"
        }

async def test_interactive_agent_with_ollama():
    """Test the interactive agent with Ollama LLM."""
    print("=== Testing Interactive Agent with Ollama LLM ===")
    
    try:
        # Import the interactive agent components
        from diary_agent.agents.interactive_agent import InteractiveAgent
        from diary_agent.core.llm_manager import LLMConfigManager, OllamaAPIClient
        from diary_agent.utils.data_models import EventData, DiaryEntry, PromptConfig, LLMConfig
        from diary_agent.integration.interaction_data_reader import InteractionDataReader
        
        print("✅ Successfully imported interactive agent components")
        
        # Initialize LLM config manager (uses existing configuration)
        llm_manager = LLMConfigManager()
        
        # The system already has Ollama configured as "ollama_qwen3"
        print(f"🔧 Using existing Ollama configuration: ollama_qwen3")
        print(f"   Default provider: {llm_manager.get_default_provider()}")
        print(f"   Available providers: {llm_manager.get_enabled_providers()}")
        
        # Get the default provider config
        default_provider_name = llm_manager.get_default_provider()
        default_provider_config = llm_manager.get_provider_config(default_provider_name)
        
        print(f"   Model: {default_provider_config.model_name}")
        print(f"   Endpoint: {default_provider_config.api_endpoint}")
        
        # Initialize prompt configuration
        prompt_config = PromptConfig(
            agent_type="interactive",
            system_prompt="You are an interactive agent that processes human-machine interaction events. Generate natural, engaging content based on the event data provided.",
            user_prompt_template="Process the following human-machine interaction event and generate appropriate content: {event_data}",
            output_format={
                "content": "string",
                "emotion_tags": "list",
                "title": "string"
            },
            validation_rules={
                "max_content_length": 35,
                "max_title_length": 6,
                "required_fields": ["content", "title"]
            }
        )
        
        # Initialize interaction data reader
        data_reader = InteractionDataReader()
        
        # Initialize interactive agent
        interactive_agent = InteractiveAgent(
            agent_type="interactive",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=data_reader
        )
        
        print("✅ Interactive agent initialized successfully")
        
        # Create mock MQTT event
        mqtt_event = MockMQTTEvent(
            event_type="same_frequency_event",
            user_id=1
        )
        
        print(f"📡 Mock MQTT Event created: {mqtt_event.event_type}")
        print(f"   User ID: {mqtt_event.user_id}")
        print(f"   Payload: {json.dumps(mqtt_event.payload, indent=2, ensure_ascii=False)}")
        
        # Test event processing
        print("\n🔄 Processing Human-Machine Interaction Event...")
        
        # Create event data for the agent
        event_data = EventData(
            event_id=f"test_event_{datetime.now().timestamp()}",
            event_type="human_machine_interaction",
            event_name="liked_interaction_once",
            timestamp=mqtt_event.timestamp,
            user_id=mqtt_event.user_id,
            context_data=mqtt_event.payload,
            metadata={
                "trigger_condition": "MQTT message received with event type",
                "content_requirements": [
                    "Same frequency event name",
                    "Toy owner's nickname",
                    "Close friend's nickname", 
                    "Close friend's owner's nickname"
                ]
            }
        )
        
        # Process the event with the interactive agent
        result = await interactive_agent.process_event(event_data)
        
        print("✅ Event processing completed")
        print(f"📝 Generated diary entry: {result}")
        
        # Validate the result
        print("\n🔍 Validating result...")
        
        # Check if result contains required content
        required_fields = [
            "same_frequency_event",
            "toy_owner_nickname", 
            "close_friend_nickname",
            "close_friend_owner_nickname"
        ]
        
        validation_results = {}
        result_text = str(result.content) if hasattr(result, 'content') else str(result)
        
        for field in required_fields:
            if field in result_text.lower() or field.replace('_', ' ') in result_text.lower():
                validation_results[field] = "✅ Found"
            else:
                validation_results[field] = "❌ Missing"
        
        print("Validation Results:")
        for field, status in validation_results.items():
            print(f"   {field}: {status}")
        
        # Save test results
        test_results = {
            "test_name": "Interactive Agent with Ollama LLM",
            "timestamp": datetime.now().isoformat(),
            "event_type": "Human-Machine Interaction Event",
            "mqtt_event": mqtt_event.payload,
            "generated_content": result_text,
            "validation_results": validation_results,
            "ollama_config": {
                "model_name": default_provider_config.model_name,
                "api_endpoint": default_provider_config.api_endpoint,
                "temperature": default_provider_config.temperature
            }
        }
        
        with open('test_results_interactive_agent.json', 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print("\n💾 Test results saved to: test_results_interactive_agent.json")
        
        # Summary
        success_count = sum(1 for status in validation_results.values() if "✅" in status)
        total_count = len(validation_results)
        
        print(f"\n📊 Test Summary:")
        print(f"   Success Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        print(f"   LLM Used: {default_provider_config.model_name}")
        print(f"   Event Type: {mqtt_event.event_type}")
        
        if success_count == total_count:
            print("🎉 All tests passed! Interactive agent with Ollama is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the generated content for missing fields.")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        logger.error(f"Test failed with error: {e}", exc_info=True)

async def test_multiple_interactions():
    """Test multiple interaction scenarios."""
    print("\n=== Testing Multiple Interaction Scenarios ===")
    
    try:
        from diary_agent.agents.interactive_agent import InteractiveAgent
        from diary_agent.core.llm_manager import LLMConfigManager
        from diary_agent.utils.data_models import EventData, PromptConfig, LLMConfig
        from diary_agent.integration.interaction_data_reader import InteractionDataReader
        
        # Initialize components
        llm_manager = LLMConfigManager()
        
        # The system already has Ollama configured as "ollama_qwen3"
        print(f"🔧 Using existing Ollama configuration: ollama_qwen3")
        print(f"   Default provider: {llm_manager.get_default_provider()}")
        print(f"   Available providers: {llm_manager.get_enabled_providers()}")
        
        # Get the default provider config
        default_provider_name = llm_manager.get_default_provider()
        default_provider_config = llm_manager.get_provider_config(default_provider_name)
        
        print(f"   Model: {default_provider_config.model_name}")
        print(f"   Endpoint: {default_provider_config.api_endpoint}")
        
        prompt_config = PromptConfig(
            agent_type="interactive",
            system_prompt="You are an interactive agent that processes human-machine interaction events.",
            user_prompt_template="Process the following event: {event_data}",
            output_format={
                "content": "string",
                "emotion_tags": "list",
                "title": "string"
            },
            validation_rules={
                "max_content_length": 35,
                "max_title_length": 6,
                "required_fields": ["content", "title"]
            }
        )
        
        data_reader = InteractionDataReader()
        
        interactive_agent = InteractiveAgent(
            agent_type="interactive",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=data_reader
        )
        
        # Test scenarios
        scenarios = [
            {
                "name": "Play Together Event",
                "event_name": "liked_interaction_once",
                "interaction_type": "一起玩耍",
                "same_frequency_event": "一起玩耍"
            },
            {
                "name": "Petting Event", 
                "event_name": "liked_interaction_3_to_5_times",
                "interaction_type": "摸摸头",
                "same_frequency_event": "摸摸头"
            },
            {
                "name": "Feeding Event",
                "event_name": "liked_interaction_over_5_times", 
                "interaction_type": "喂食",
                "same_frequency_event": "喂食"
            }
        ]
        
        results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🔄 Testing Scenario {i}: {scenario['name']}")
            
            mqtt_event = MockMQTTEvent(
                event_type="same_frequency_event",
                user_id=1
            )
            mqtt_event.payload["interaction_type"] = scenario['interaction_type']
            mqtt_event.payload["same_frequency_event"] = scenario['same_frequency_event']
            
            event_data = EventData(
                event_id=f"test_event_{datetime.now().timestamp()}",
                event_type="human_machine_interaction",
                event_name=scenario['event_name'],
                timestamp=mqtt_event.timestamp,
                user_id=mqtt_event.user_id,
                context_data=mqtt_event.payload,
                metadata={
                    "trigger_condition": "MQTT message received with event type",
                    "content_requirements": [
                        "Same frequency event name",
                        "Toy owner's nickname",
                        "Close friend's nickname",
                        "Close friend's owner's nickname"
                    ]
                }
            )
            
            result = await interactive_agent.process_event(event_data)
            
            result_text = str(result.content) if hasattr(result, 'content') else str(result)
            
            scenario_result = {
                "scenario": scenario['name'],
                "event_name": scenario['event_name'],
                "interaction_type": scenario['interaction_type'],
                "generated_content": result_text
            }
            
            results.append(scenario_result)
            print(f"✅ Scenario {i} completed")
        
        # Save multiple scenario results
        with open('test_results_multiple_scenarios.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Multiple scenario results saved to: test_results_multiple_scenarios.json")
        print(f"📊 Tested {len(scenarios)} different interaction scenarios")
        
    except Exception as e:
        print(f"❌ Error in multiple scenarios test: {e}")
        logger.error(f"Multiple scenarios test failed: {e}", exc_info=True)

def main():
    """Main test function."""
    print("🚀 Starting Interactive Agent with Ollama LLM Tests")
    print("=" * 60)
    
    # Check if Ollama is running
    print("🔍 Checking Ollama availability...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running and accessible")
        else:
            print("⚠️  Ollama responded but with unexpected status")
    except Exception as e:
        print(f"❌ Ollama not accessible: {e}")
        print("Please make sure Ollama is running on http://localhost:11434")
        return
    
    # Run the main test
    asyncio.run(test_interactive_agent_with_ollama())
    
    # Run multiple scenarios test
    asyncio.run(test_multiple_interactions())
    
    print("\n🎯 All tests completed!")
    print("Check the generated JSON files for detailed results.")

if __name__ == "__main__":
    main()
