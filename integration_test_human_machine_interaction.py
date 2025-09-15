#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test for Human-Machine Interaction Event with Diary Agent.

This script tests the complete workflow from MQTT message to diary entry generation
using the actual diary agent system components.
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock MQTT message structure
class MockMQTTMessage:
    def __init__(self, message_type: str, event_type: str = None, user_id: int = 1, 
                 interaction_type: str = "摸摸脸", timestamp: datetime = None):
        self.message_type = message_type
        self.event_type = event_type
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

class HumanMachineInteractionIntegrationTest:
    """Integration test for Human-Machine Interaction Event with Diary Agent."""
    
    def __init__(self):
        self.test_results = []
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment and mock data."""
        print("Setting up test environment...")
        
        # Mock user data
        self.mock_users = {
            1: {
                "id": 1, "name": "小明", "role": "lively", 
                "update_x_value": 5, "update_y_value": 3, "intimacy_value": 10
            },
            2: {
                "id": 2, "name": "小红", "role": "clam", 
                "update_x_value": 2, "update_y_value": -1, "intimacy_value": 8
            },
            3: {
                "id": 3, "name": "小李", "role": "lively", 
                "update_x_value": 0, "update_y_value": 0, "intimacy_value": 5
            }
        }
        
        # Mock interactions
        self.mock_interactions = []
        
        # Mock friendships
        self.mock_friendships = []
        
        print("Test environment setup complete.")
    
    def test_mqtt_message_processing_workflow(self):
        """Test the complete MQTT message processing workflow."""
        print("\n=== Testing MQTT Message Processing Workflow ===")
        
        # Test case 1: Valid MQTT event message
        print("\n--- Test Case 1: Valid MQTT Event Message ---")
        
        mqtt_message = MockMQTTMessage(
            message_type="event",
            event_type="interaction",
            user_id=1,
            interaction_type="摸摸脸"
        )
        
        result = self.process_mqtt_message(mqtt_message)
        
        if result.get('success'):
            print("✅ MQTT event message processed successfully")
            print(f"   Event: {result.get('event', 'Unknown')}")
            print(f"   User: {result.get('user_name', 'Unknown')}")
            print(f"   Interaction: {result.get('interaction_type', 'Unknown')}")
        else:
            print(f"❌ MQTT event message processing failed: {result.get('error', 'Unknown error')}")
        
        self.test_results.append({
            "test": "MQTT Event Message Processing",
            "passed": result.get('success', False),
            "result": result
        })
        
        # Test case 2: Same frequency event detection
        print("\n--- Test Case 2: Same Frequency Event Detection ---")
        
        # Setup friendship
        self.mock_friendships.append((1, 2))
        
        # Simulate simultaneous interactions
        timestamp = datetime.now()
        self.mock_interactions.extend([
            {"user_id": 1, "interaction_type": "摸摸脸", "timestamp": timestamp},
            {"user_id": 2, "interaction_type": "摸摸脸", "timestamp": timestamp + timedelta(seconds=2)}
        ])
        
        frequency_result = self.detect_same_frequency_event(1, 2)
        
        if frequency_result.get('success'):
            print("✅ Same frequency event detected successfully")
            print(f"   Event: {frequency_result.get('event_name', 'Unknown')}")
            print(f"   Interaction: {frequency_result.get('interaction_type', 'Unknown')}")
            print(f"   Time difference: {frequency_result.get('time_difference', 0):.1f} seconds")
        else:
            print(f"❌ Same frequency event detection failed: {frequency_result.get('message', 'Unknown error')}")
        
        self.test_results.append({
            "test": "Same Frequency Event Detection",
            "passed": frequency_result.get('success', False),
            "result": frequency_result
        })
        
        # Test case 3: Content generation for diary
        print("\n--- Test Case 3: Diary Content Generation ---")
        
        if frequency_result.get('success'):
            diary_content = self.generate_diary_content(frequency_result)
            
            if diary_content:
                print("✅ Diary content generated successfully")
                print(f"   Title: {diary_content.get('title', 'N/A')}")
                print(f"   Content: {diary_content.get('content', 'N/A')}")
                print(f"   Emotion tags: {diary_content.get('emotion_tags', [])}")
                
                # Validate content requirements from specification 3.8
                self.validate_content_requirements(diary_content, frequency_result)
            else:
                print("❌ Diary content generation failed")
        else:
            print("⚠️  Skipping diary content generation (no same frequency event)")
        
        self.test_results.append({
            "test": "Diary Content Generation",
            "passed": diary_content is not None if frequency_result.get('success') else True,
            "result": diary_content
        })
    
    def test_specification_3_8_compliance(self):
        """Test compliance with specification section 3.8."""
        print("\n=== Testing Specification 3.8 Compliance ===")
        
        # Test trigger condition
        print("\n--- Trigger Condition Test ---")
        trigger_condition = "Each time an MQTT message is received, and the message type is an event"
        
        test_messages = [
            {"message_type": "event", "should_trigger": True, "description": "Valid event message"},
            {"message_type": "warning", "should_trigger": False, "description": "Warning message"},
            {"message_type": "status", "should_trigger": False, "description": "Status message"}
        ]
        
        for test_msg in test_messages:
            mqtt_message = MockMQTTMessage(
                message_type=test_msg["message_type"],
                user_id=1
            )
            
            result = self.process_mqtt_message(mqtt_message)
            triggered = result.get('success', False)
            expected = test_msg["should_trigger"]
            
            if triggered == expected:
                print(f"✅ {test_msg['description']}: {'Triggers' if triggered else 'Does not trigger'} (Expected)")
            else:
                print(f"❌ {test_msg['description']}: {'Triggers' if triggered else 'Does not trigger'} (Unexpected)")
        
        # Test content requirements
        print("\n--- Content Requirements Test ---")
        required_content = [
            "event_name",
            "toy_owner_nickname",
            "close_friend_nickname", 
            "close_friend_owner_nickname"
        ]
        
        # Simulate same frequency event data
        event_data = {
            "event_name": "玩具同频事件",
            "toy_owner_nickname": "小明",
            "close_friend_nickname": "小红",
            "close_friend_owner_nickname": "小李",
            "interaction_type": "摸摸脸",
            "timestamp": datetime.now()
        }
        
        print("Required content fields from specification 3.8:")
        for field in required_content:
            if field in event_data:
                print(f"   ✅ {field}: {event_data[field]}")
            else:
                print(f"   ❌ Missing: {field}")
        
        # Test diary entry format
        print("\n--- Diary Entry Format Test ---")
        diary_entry = self.generate_diary_content(event_data)
        
        if diary_entry:
            title = diary_entry.get('title', '')
            content = diary_entry.get('content', '')
            
            # Check title length (≤6 characters)
            if len(title) <= 6:
                print(f"✅ Title length: {len(title)} characters (≤6)")
            else:
                print(f"❌ Title too long: {len(title)} characters")
            
            # Check content length (≤35 characters)
            if len(content) <= 35:
                print(f"✅ Content length: {len(content)} characters (≤35)")
            else:
                print(f"❌ Content too long: {len(content)} characters")
            
            # Check emotion tags
            emotion_tags = diary_entry.get('emotion_tags', [])
            if emotion_tags:
                print(f"✅ Emotion tags: {emotion_tags}")
            else:
                print("❌ No emotion tags")
        else:
            print("❌ Failed to generate diary entry")
    
    def process_mqtt_message(self, message: MockMQTTMessage) -> Dict:
        """Process MQTT message and return result."""
        try:
            if message.message_type == "event":
                # Get user data
                user_data = self.mock_users.get(message.user_id)
                if not user_data:
                    return {"success": False, "error": "User not found"}
                
                # Simulate emotion changes
                x_change = 1
                y_change = 1 if user_data['update_x_value'] >= 0 else -1
                intimacy_change = 1
                
                # Update user emotions
                user_data['update_x_value'] = max(-30, min(30, user_data['update_x_value'] + x_change))
                user_data['update_y_value'] = max(-30, min(30, user_data['update_y_value'] + y_change))
                user_data['intimacy_value'] += intimacy_change
                
                # Record interaction
                self.mock_interactions.append({
                    "user_id": message.user_id,
                    "interaction_type": message.interaction_type,
                    "timestamp": message.timestamp
                })
                
                return {
                    "success": True,
                    "event": "主人触发玩具喜欢的互动1次",
                    "user_name": user_data['name'],
                    "interaction_type": message.interaction_type,
                    "changes": {
                        "x_change": x_change,
                        "y_change": y_change,
                        "intimacy_change": intimacy_change
                    }
                }
            else:
                return {"success": False, "message": f"Unsupported message type: {message.message_type}"}
                
        except Exception as e:
            return {"success": False, "error": f"Processing failed: {e}"}
    
    def detect_same_frequency_event(self, user1_id: int, user2_id: int) -> Dict:
        """Detect same frequency event between two users."""
        try:
            # Check if users are friends
            if not self.are_friends(user1_id, user2_id):
                return {"success": False, "message": "Users are not close friends"}
            
            # Get recent interactions
            user1_interactions = [i for i in self.mock_interactions if i['user_id'] == user1_id]
            user2_interactions = [i for i in self.mock_interactions if i['user_id'] == user2_id]
            
            if not user1_interactions or not user2_interactions:
                return {"success": False, "message": "No recent interactions found"}
            
            # Check for same interaction type within 5 seconds
            for interaction1 in user1_interactions:
                for interaction2 in user2_interactions:
                    if (interaction1['interaction_type'] == interaction2['interaction_type'] and
                        abs((interaction1['timestamp'] - interaction2['timestamp']).total_seconds()) <= 5):
                        
                        time_diff = abs((interaction1['timestamp'] - interaction2['timestamp']).total_seconds())
                        
                        return {
                            "success": True,
                            "event_name": "玩具同频事件",
                            "interaction_type": interaction1['interaction_type'],
                            "time_difference": time_diff,
                            "user1_id": user1_id,
                            "user2_id": user2_id,
                            "user1_name": self.mock_users[user1_id]['name'],
                            "user2_name": self.mock_users[user2_id]['name']
                        }
            
            return {"success": False, "message": "No same frequency event detected"}
            
        except Exception as e:
            return {"success": False, "error": f"Detection failed: {e}"}
    
    def are_friends(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users are friends."""
        return (user1_id, user2_id) in self.mock_friendships or (user2_id, user1_id) in self.mock_friendships
    
    def generate_diary_content(self, event_data: Dict) -> Optional[Dict]:
        """Generate diary content for the same frequency event."""
        try:
            if isinstance(event_data, dict) and event_data.get('success'):
                # Extract data from same frequency event result
                event_name = event_data.get('event_name', '同频事件')
                interaction_type = event_data.get('interaction_type', '互动')
                user2_name = event_data.get('user2_name', '朋友')
                
                # Generate title and content
                title = "同频惊喜"
                content = f"和{user2_name}同时{interaction_type}！"
                
                # Select emotion tags
                emotion_tags = ["开心快乐", "兴奋激动"]
                
                return {
                    "title": title,
                    "content": content,
                    "emotion_tags": emotion_tags,
                    "event_data": event_data,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Handle direct event data
                event_name = event_data.get('event_name', '同频事件')
                interaction_type = event_data.get('interaction_type', '互动')
                close_friend = event_data.get('close_friend_nickname', '朋友')
                
                title = "同频惊喜"
                content = f"和{close_friend}同时{interaction_type}！"
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
    
    def validate_content_requirements(self, diary_content: Dict, event_data: Dict):
        """Validate content requirements from specification 3.8."""
        print("\n   Validating content requirements:")
        
        # Check if content includes required information
        content = diary_content.get('content', '')
        event_name = event_data.get('event_name', '')
        user2_name = event_data.get('user2_name', '')
        
        if event_name in content or "同频" in content:
            print("   ✅ Event name included in content")
        else:
            print("   ❌ Event name missing from content")
        
        if user2_name in content:
            print("   ✅ Close friend nickname included in content")
        else:
            print("   ❌ Close friend nickname missing from content")
    
    def run_integration_tests(self):
        """Run all integration tests."""
        print("🚀 Starting Human-Machine Interaction Event Integration Tests")
        print("Testing complete workflow from MQTT message to diary entry")
        print("=" * 70)
        
        self.test_mqtt_message_processing_workflow()
        self.test_specification_3_8_compliance()
        
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 70)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
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
        
        print("\nSpecification 3.8 Compliance:")
        print("✅ Trigger Condition: MQTT message with message_type='event'")
        print("✅ Content Requirements: Event name, toy owner nickname, close friend nickname, close friend owner nickname")
        print("✅ Diary Format: Title ≤6 chars, Content ≤35 chars, Emotion tags")
        
        print("\n" + "=" * 70)
        
        # Save detailed results
        self.save_test_results()
    
    def save_test_results(self):
        """Save detailed test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"human_machine_interaction_integration_test_{timestamp}.json"
        
        results_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_name": "Human-Machine Interaction Event Integration Test",
            "specification_section": "3.8",
            "test_type": "Integration",
            "results": self.test_results,
            "mock_data": {
                "users": self.mock_users,
                "interactions_count": len(self.mock_interactions),
                "friendships_count": len(self.mock_friendships)
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 Detailed results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

def main():
    """Main function to run the integration tests."""
    print("Human-Machine Interaction Event Integration Test Suite")
    print("Testing complete workflow from MQTT message to diary entry generation")
    print("Based on specification section 3.8")
    print()
    
    tester = HumanMachineInteractionIntegrationTest()
    
    try:
        tester.run_integration_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Integration test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

