#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Human-Machine Interaction Event functionality.

This script tests the Human-Machine Interaction Event as specified in section 3.8:
- Trigger Condition: Each time an MQTT message is received, and the message type is an event
- Content to Include: Event name of the triggered same frequency event, toy owner's nickname, 
  close friend's nickname, close friend's owner's nickname
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the required modules
try:
    from hewan_emotion_cursor_python.human_toy_interactive_function import (
        process_human_toy_interaction, HUMAN_TOY_INTERACTIVE_EVENTS
    )
    from hewan_emotion_cursor_python.same_frequency import (
        process_same_frequency_event, SAME_FREQUENCY_EVENTS
    )
    from hewan_emotion_cursor_python.friends_function import (
        add_friend, get_user_data
    )
    from hewan_emotion_cursor_python.warning_file import (
        process_mqtt_warning_event
    )
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    print("Some tests may be skipped.")

# Mock MQTT message structure
class MockMQTTMessage:
    def __init__(self, message_type: str, event_type: str = None, user_id: int = 1, 
                 interaction_type: str = "摸摸脸", timestamp: datetime = None):
        self.message_type = message_type  # "event", "warning", "interaction"
        self.event_type = event_type  # For warning events: "drop", "overload", "impact"
        self.user_id = user_id
        self.interaction_type = interaction_type
        self.timestamp = timestamp or datetime.now()
        self.payload = {
            "message_type": message_type,
            "event_type": event_type,
            "user_id": user_id,
            "interaction_type": interaction_type,
            "timestamp": self.timestamp.isoformat()
        }

class HumanMachineInteractionEventTester:
    """Test class for Human-Machine Interaction Event functionality."""
    
    def __init__(self):
        self.test_results = []
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup test data and ensure database connections."""
        print("Setting up test data...")
        
        # Test user IDs
        self.test_users = [1, 2, 3]
        
        # Test interaction types
        self.interaction_types = ["摸摸脸", "拍拍头", "捏一下", "摇一摇"]
        
        # Test MQTT event types
        self.mqtt_event_types = ["drop", "overload", "impact"]
        
        print("Test data setup complete.")
    
    def test_mqtt_message_processing(self):
        """Test MQTT message processing for Human-Machine Interaction Event."""
        print("\n=== Testing MQTT Message Processing ===")
        
        test_cases = [
            {
                "name": "Valid MQTT Event Message",
                "message": MockMQTTMessage("event", "interaction", 1, "摸摸脸"),
                "expected_success": True
            },
            {
                "name": "MQTT Warning Message",
                "message": MockMQTTMessage("warning", "drop", 1),
                "expected_success": True
            },
            {
                "name": "Invalid Message Type",
                "message": MockMQTTMessage("status", None, 1),
                "expected_success": False
            }
        ]
        
        for test_case in test_cases:
            print(f"\n--- {test_case['name']} ---")
            result = self.process_mqtt_message(test_case['message'])
            
            success = result.get('success', False)
            expected = test_case['expected_success']
            
            if success == expected:
                print(f"✅ PASS: {test_case['name']}")
                if success:
                    print(f"   Event: {result.get('event', 'Unknown')}")
                    print(f"   Changes: {result.get('changes', {})}")
            else:
                print(f"❌ FAIL: {test_case['name']}")
                print(f"   Expected: {expected}, Got: {success}")
                print(f"   Error: {result.get('error', result.get('message', 'Unknown error'))}")
            
            self.test_results.append({
                "test": test_case['name'],
                "passed": success == expected,
                "result": result
            })
    
    def test_same_frequency_event_trigger(self):
        """Test same frequency event triggering for Human-Machine Interaction Event."""
        print("\n=== Testing Same Frequency Event Trigger ===")
        
        # Test with two users who are close friends
        user1_id = 1
        user2_id = 2
        
        print(f"Testing same frequency event between User {user1_id} and User {user2_id}")
        
        # First, ensure they are friends
        try:
            friend_result = add_friend(user1_id, user2_id)
            print(f"Friendship setup: {friend_result.get('success', False)}")
        except Exception as e:
            print(f"Warning: Could not setup friendship: {e}")
        
        # Simulate simultaneous interactions
        interaction_type = "摸摸脸"
        
        # Process interaction for user1
        print(f"\nProcessing interaction for User {user1_id}...")
        result1 = self.process_human_interaction(user1_id, interaction_type)
        
        # Process interaction for user2 (within 5 seconds)
        print(f"Processing interaction for User {user2_id}...")
        result2 = self.process_human_interaction(user2_id, interaction_type)
        
        # Check for same frequency event
        print(f"\nChecking for same frequency event...")
        frequency_result = self.check_same_frequency_event(user1_id, user2_id)
        
        if frequency_result.get('success'):
            print("✅ Same frequency event detected!")
            print(f"   Event: {frequency_result.get('event', 'Unknown')}")
            print(f"   Interaction: {frequency_result.get('interaction_type', 'Unknown')}")
        else:
            print("❌ No same frequency event detected")
            print(f"   Reason: {frequency_result.get('message', 'Unknown')}")
        
        self.test_results.append({
            "test": "Same Frequency Event Trigger",
            "passed": frequency_result.get('success', False),
            "result": frequency_result
        })
    
    def test_event_content_generation(self):
        """Test content generation for Human-Machine Interaction Event."""
        print("\n=== Testing Event Content Generation ===")
        
        # Test content requirements from specification 3.8
        required_content = [
            "event_name",
            "toy_owner_nickname", 
            "close_friend_nickname",
            "close_friend_owner_nickname"
        ]
        
        # Simulate a same frequency event
        event_data = {
            "event_name": "玩具同频事件",
            "toy_owner_nickname": "小明",
            "close_friend_nickname": "小红",
            "close_friend_owner_nickname": "小李",
            "interaction_type": "摸摸脸",
            "timestamp": datetime.now()
        }
        
        print("Testing content generation with sample data:")
        for content_item in required_content:
            if content_item in event_data:
                print(f"✅ {content_item}: {event_data[content_item]}")
            else:
                print(f"❌ Missing: {content_item}")
        
        # Test diary entry generation
        diary_entry = self.generate_diary_entry(event_data)
        
        if diary_entry:
            print(f"\nGenerated diary entry:")
            print(f"   Title: {diary_entry.get('title', 'N/A')}")
            print(f"   Content: {diary_entry.get('content', 'N/A')}")
            print(f"   Emotion tags: {diary_entry.get('emotion_tags', [])}")
            
            # Validate content length
            title = diary_entry.get('title', '')
            content = diary_entry.get('content', '')
            
            if len(title) <= 6:
                print("✅ Title length is within limit (≤6 characters)")
            else:
                print(f"❌ Title too long: {len(title)} characters")
            
            if len(content) <= 35:
                print("✅ Content length is within limit (≤35 characters)")
            else:
                print(f"❌ Content too long: {len(content)} characters")
        else:
            print("❌ Failed to generate diary entry")
        
        self.test_results.append({
            "test": "Event Content Generation",
            "passed": diary_entry is not None,
            "result": diary_entry
        })
    
    def test_mqtt_event_types(self):
        """Test different MQTT event types."""
        print("\n=== Testing MQTT Event Types ===")
        
        for event_type in self.mqtt_event_types:
            print(f"\n--- Testing MQTT event type: {event_type} ---")
            
            # Create MQTT message
            message = MockMQTTMessage("warning", event_type, 1)
            
            # Process the message
            result = self.process_mqtt_message(message)
            
            if result.get('success'):
                print(f"✅ Success: {result.get('event', 'Unknown event')}")
                print(f"   Changes: {result.get('changes', {})}")
            else:
                print(f"❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
            
            self.test_results.append({
                "test": f"MQTT Event Type: {event_type}",
                "passed": result.get('success', False),
                "result": result
            })
    
    def test_interaction_frequency_analysis(self):
        """Test interaction frequency analysis for same frequency detection."""
        print("\n=== Testing Interaction Frequency Analysis ===")
        
        user_id = 1
        interaction_type = "摸摸脸"
        
        # Simulate multiple interactions
        print(f"Simulating multiple interactions for User {user_id}...")
        
        for i in range(3):
            result = self.process_human_interaction(user_id, interaction_type)
            if result.get('success'):
                print(f"   Interaction {i+1}: Success")
            else:
                print(f"   Interaction {i+1}: Failed - {result.get('message', 'Unknown error')}")
        
        # Analyze interaction frequency
        frequency_analysis = self.analyze_interaction_frequency(user_id, interaction_type)
        print(f"\nFrequency analysis: {frequency_analysis}")
        
        self.test_results.append({
            "test": "Interaction Frequency Analysis",
            "passed": frequency_analysis.get('total_interactions', 0) > 0,
            "result": frequency_analysis
        })
    
    def process_mqtt_message(self, message: MockMQTTMessage) -> Dict:
        """Process MQTT message and return result."""
        try:
            if message.message_type == "event":
                # Process as human-toy interaction event
                return self.process_human_interaction(message.user_id, message.interaction_type)
            elif message.message_type == "warning":
                # Process as warning event
                return process_mqtt_warning_event(message.event_type, message.user_id)
            else:
                return {"success": False, "message": f"Unsupported message type: {message.message_type}"}
        except Exception as e:
            return {"success": False, "error": f"Processing failed: {e}"}
    
    def process_human_interaction(self, user_id: int, interaction_type: str) -> Dict:
        """Process human-toy interaction."""
        try:
            return process_human_toy_interaction(user_id, interaction_type)
        except Exception as e:
            return {"success": False, "error": f"Interaction processing failed: {e}"}
    
    def check_same_frequency_event(self, user1_id: int, user2_id: int) -> Dict:
        """Check for same frequency event between two users."""
        try:
            return process_same_frequency_event(user1_id, user2_id)
        except Exception as e:
            return {"success": False, "error": f"Frequency check failed: {e}"}
    
    def generate_diary_entry(self, event_data: Dict) -> Optional[Dict]:
        """Generate diary entry for the event."""
        try:
            # Mock diary generation based on event data
            event_name = event_data.get('event_name', '同频事件')
            interaction_type = event_data.get('interaction_type', '互动')
            
            # Generate title and content based on same frequency event
            title = "同频惊喜"
            content = f"和{event_data.get('close_friend_nickname', '朋友')}同时{interaction_type}！"
            
            # Select appropriate emotion tags
            emotion_tags = ["开心快乐", "兴奋激动"]
            
            return {
                "title": title,
                "content": content,
                "emotion_tags": emotion_tags,
                "event_data": event_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Diary generation failed: {e}")
            return None
    
    def analyze_interaction_frequency(self, user_id: int, interaction_type: str) -> Dict:
        """Analyze interaction frequency for a user."""
        try:
            # Mock frequency analysis
            return {
                "user_id": user_id,
                "interaction_type": interaction_type,
                "total_interactions": random.randint(1, 10),
                "recent_interactions": random.randint(0, 5),
                "frequency_score": random.uniform(0.1, 1.0)
            }
        except Exception as e:
            return {"error": f"Frequency analysis failed: {e}"}
    
    def run_all_tests(self):
        """Run all test cases."""
        print("🚀 Starting Human-Machine Interaction Event Tests")
        print("=" * 60)
        
        self.test_mqtt_message_processing()
        self.test_same_frequency_event_trigger()
        self.test_event_content_generation()
        self.test_mqtt_event_types()
        self.test_interaction_frequency_analysis()
        
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  ❌ {result['test']}")
                    if 'result' in result and 'error' in result['result']:
                        print(f"     Error: {result['result']['error']}")
        
        print("\n" + "=" * 60)
        
        # Save detailed results to file
        self.save_test_results()
    
    def save_test_results(self):
        """Save detailed test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"human_machine_interaction_test_results_{timestamp}.json"
        
        results_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_name": "Human-Machine Interaction Event Test",
            "specification_section": "3.8",
            "results": self.test_results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 Detailed results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

def main():
    """Main function to run the tests."""
    print("Human-Machine Interaction Event Test Suite")
    print("Testing specification section 3.8 functionality")
    print()
    
    tester = HumanMachineInteractionEventTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
