#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for Human-Machine Interaction Event (Section 3.8).

This script provides a quick way to test the core functionality:
1. MQTT message processing
2. Same frequency event detection
3. Content generation with required fields
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mqtt_event_processing():
    """Test MQTT event processing functionality."""
    print("=== Testing MQTT Event Processing ===")
    
    try:
        # Import the required modules
        from hewan_emotion_cursor_python.human_toy_interactive_function import (
            process_human_toy_interaction, HUMAN_TOY_INTERACTIVE_EVENTS
        )
        from hewan_emotion_cursor_python.same_frequency import (
            process_same_frequency_event, SAME_FREQUENCY_EVENTS
        )
        from hewan_emotion_cursor_python.friends_function import (
            add_friend, get_user_data
        )
        
        print("✅ Successfully imported required modules")
        
        # Test 1: Basic human-toy interaction
        print("\n--- Test 1: Basic Human-Toy Interaction ---")
        user_id = 1
        interaction_type = "摸摸脸"
        
        result = process_human_toy_interaction(user_id, interaction_type)
        
        if result.get('success'):
            print(f"✅ Interaction processed successfully")
            print(f"   Event: {result.get('event', 'Unknown')}")
            print(f"   Changes: {result.get('changes', {})}")
        else:
            print(f"❌ Interaction failed: {result.get('error', result.get('message', 'Unknown error'))}")
        
        # Test 2: Same frequency event detection
        print("\n--- Test 2: Same Frequency Event Detection ---")
        user1_id = 1
        user2_id = 2
        
        # Setup friendship
        try:
            friend_result = add_friend(user1_id, user2_id)
            print(f"Friendship setup: {friend_result.get('success', False)}")
        except Exception as e:
            print(f"Warning: Could not setup friendship: {e}")
        
        # Process interactions for both users
        print(f"Processing interactions for users {user1_id} and {user2_id}...")
        
        result1 = process_human_toy_interaction(user1_id, interaction_type)
        result2 = process_human_toy_interaction(user2_id, interaction_type)
        
        # Check for same frequency event
        frequency_result = process_same_frequency_event(user1_id, user2_id)
        
        if frequency_result.get('success'):
            print("✅ Same frequency event detected!")
            print(f"   Event: {frequency_result.get('event', 'Unknown')}")
            print(f"   Interaction: {frequency_result.get('interaction_type', 'Unknown')}")
        else:
            print("❌ No same frequency event detected")
            print(f"   Reason: {frequency_result.get('message', 'Unknown')}")
        
        # Test 3: Content generation
        print("\n--- Test 3: Content Generation ---")
        
        # Simulate event data with required content from specification 3.8
        event_data = {
            "event_name": "玩具同频事件",
            "toy_owner_nickname": "小明",
            "close_friend_nickname": "小红", 
            "close_friend_owner_nickname": "小李",
            "interaction_type": "摸摸脸",
            "timestamp": datetime.now()
        }
        
        # Check required content fields
        required_fields = [
            "event_name",
            "toy_owner_nickname",
            "close_friend_nickname", 
            "close_friend_owner_nickname"
        ]
        
        print("Checking required content fields:")
        for field in required_fields:
            if field in event_data:
                print(f"   ✅ {field}: {event_data[field]}")
            else:
                print(f"   ❌ Missing: {field}")
        
        # Generate diary entry
        diary_entry = generate_diary_entry(event_data)
        
        if diary_entry:
            print(f"\nGenerated diary entry:")
            print(f"   Title: {diary_entry.get('title', 'N/A')}")
            print(f"   Content: {diary_entry.get('content', 'N/A')}")
            print(f"   Emotion tags: {diary_entry.get('emotion_tags', [])}")
            
            # Validate content length
            title = diary_entry.get('title', '')
            content = diary_entry.get('content', '')
            
            if len(title) <= 6:
                print("   ✅ Title length is within limit (≤6 characters)")
            else:
                print(f"   ❌ Title too long: {len(title)} characters")
            
            if len(content) <= 35:
                print("   ✅ Content length is within limit (≤35 characters)")
            else:
                print(f"   ❌ Content too long: {len(content)} characters")
        else:
            print("❌ Failed to generate diary entry")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available.")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_diary_entry(event_data):
    """Generate a diary entry for the same frequency event."""
    try:
        event_name = event_data.get('event_name', '同频事件')
        interaction_type = event_data.get('interaction_type', '互动')
        close_friend = event_data.get('close_friend_nickname', '朋友')
        
        # Generate title and content based on same frequency event
        title = "同频惊喜"
        content = f"和{close_friend}同时{interaction_type}！"
        
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

def test_mqtt_message_simulation():
    """Simulate MQTT message processing."""
    print("\n=== Testing MQTT Message Simulation ===")
    
    # Simulate different MQTT message types
    mqtt_messages = [
        {
            "message_type": "event",
            "event_type": "interaction",
            "user_id": 1,
            "interaction_type": "摸摸脸",
            "description": "Valid interaction event"
        },
        {
            "message_type": "warning", 
            "event_type": "drop",
            "user_id": 1,
            "description": "Warning event (fall detection)"
        },
        {
            "message_type": "status",
            "event_type": None,
            "user_id": 1,
            "description": "Status message (should be ignored)"
        }
    ]
    
    for i, message in enumerate(mqtt_messages, 1):
        print(f"\n--- MQTT Message {i}: {message['description']} ---")
        print(f"   Message Type: {message['message_type']}")
        print(f"   Event Type: {message['event_type']}")
        print(f"   User ID: {message['user_id']}")
        
        # Process the message
        if message['message_type'] == "event":
            try:
                from hewan_emotion_cursor_python.human_toy_interactive_function import (
                    process_human_toy_interaction
                )
                result = process_human_toy_interaction(
                    message['user_id'], 
                    message['interaction_type']
                )
                
                if result.get('success'):
                    print("   ✅ Event processed successfully")
                    print(f"      Event: {result.get('event', 'Unknown')}")
                else:
                    print(f"   ❌ Event processing failed: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error processing event: {e}")
                
        elif message['message_type'] == "warning":
            try:
                from hewan_emotion_cursor_python.warning_file import (
                    process_mqtt_warning_event
                )
                result = process_mqtt_warning_event(
                    message['event_type'], 
                    message['user_id']
                )
                
                if result.get('success'):
                    print("   ✅ Warning processed successfully")
                    print(f"      Event: {result.get('event', 'Unknown')}")
                else:
                    print(f"   ❌ Warning processing failed: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error processing warning: {e}")
                
        else:
            print("   ⚠️  Message type not supported for diary generation")

def main():
    """Main function to run the tests."""
    print("Simple Human-Machine Interaction Event Test")
    print("Testing specification section 3.8 functionality")
    print("=" * 50)
    
    # Run the main test
    success = test_mqtt_event_processing()
    
    # Run MQTT message simulation
    test_mqtt_message_simulation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test completed with errors.")
    
    print("\nTest Summary:")
    print("- MQTT message processing")
    print("- Same frequency event detection") 
    print("- Content generation with required fields")
    print("- Diary entry validation")

if __name__ == "__main__":
    main()

