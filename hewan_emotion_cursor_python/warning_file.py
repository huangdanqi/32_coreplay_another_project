# -*- coding: utf-8 -*-
import mysql.connector
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from emotion_database import update_emotion_in_database

# --- Configuration ---
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "h05010501",
    "database": "page_test"
}

# --- Event Definitions Based on Image Requirements ---
# 告警事件 (Warning Events)
# Based on the image specification:
# 事件类型: 告警事件 (Warning Event)
# 事件名称: Three specific warning events that affect toy emotions
# 触发事件: When MQTT receives device messages with specific event_type values

WARNING_EVENTS = {
    "fall_event": {
        "name": "坠落事件",
        "english_name": "Fall Event",
        "event_type": "告警事件",
        "trigger_condition": "mqtt接收到设备消息, event_type值为drop (掉落)",
        "query_params": [
            "mqtt消息"
        ],
        "probability": 0.8,
        "x_change": -1,  # -1 (开心值)
        "y_change_logic": {
            "x_less_than_0": 1,  # x<0时, y+1
            "x_greater_equal_0": -1  # x>=0时, y-1
        },
        "intimacy_change": 0,  # 0 (亲密度不变)
        "weights": {"lively": 1.5, "clam": 1.0}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.0
    },
    
    "violent_squeeze_event": {
        "name": "暴力挤压事件",
        "english_name": "Violent Squeeze Event",
        "event_type": "告警事件",
        "trigger_condition": "mqtt接收到设备消息, event_type值为overload",
        "query_params": [
            "mqtt消息"
        ],
        "probability": 0.5,
        "x_change": -1,  # -1 (开心值)
        "y_change_logic": {
            "x_less_than_0": 1,  # x<0时, y+1
            "x_greater_equal_0": -1  # x>=0时, y-1
        },
        "intimacy_change": 0,  # 0 (亲密度不变)
        "weights": {"lively": 1.5, "clam": 1.0}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.0
    },
    
    "throw_event": {
        "name": "抛出事件",
        "english_name": "Throw Event",
        "event_type": "告警事件",
        "trigger_condition": "mqtt接收到设备消息, event_type值为impact (抛落撞击)",
        "query_params": [
            "mqtt消息"
        ],
        "probability": 0.9,
        "x_change": -2,  # -2 (开心值)
        "y_change_logic": {
            "x_less_than_0": 2,  # x<0时, y+2
            "x_greater_equal_0": -2  # x>=0时, y-2
        },
        "intimacy_change": 0,  # 0 (亲密度不变)
        "weights": {"lively": 1.0, "clam": 1.0}  # 性格活泼角色分值权重1.0, 性格平和角色分值权重1.0
    }
}

def get_database_connection():
    """Get database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def get_user_data(user_id: int) -> Optional[Dict]:
    """Get user data from the emotion table."""
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, role, update_x_value, update_y_value, intimacy_value FROM emotion WHERE id = %s",
            (user_id,)
        )
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return user_data
    except mysql.connector.Error as e:
        print(f"Error fetching user data: {e}")
        if conn:
            conn.close()
        return None

# These functions are no longer needed since we're not querying MySQL for events
# Events will be passed directly as arguments to the function

def determine_warning_event_type(user_id: int, warning_type: str) -> Optional[str]:
    """
    Determine which warning event type should be triggered based on MQTT event_type.
    
    :param user_id: User ID
    :param warning_type: MQTT event_type value (drop, overload, impact)
    :return: Event type key or None
    """
    if warning_type == "drop":
        return 'fall_event'
    elif warning_type == "overload":
        return 'violent_squeeze_event'
    elif warning_type == "impact":
        return 'throw_event'
    
    return None

def calculate_warning_emotion_changes(user_data: Dict, event_type: str, current_x: float) -> Tuple[float, float, int]:
    """Calculate emotion changes based on warning event and user data."""
    if event_type not in WARNING_EVENTS:
        return 0.0, 0.0, 0
    
    event_config = WARNING_EVENTS[event_type]
    
    # Get base changes
    x_change = event_config["x_change"]
    intimacy_change = event_config["intimacy_change"]
    
    # Calculate Y change based on current X value
    if current_x < 0:
        y_change = event_config["y_change_logic"]["x_less_than_0"]
    else:
        y_change = event_config["y_change_logic"]["x_greater_equal_0"]
    
    # Apply role weights
    role = user_data.get("role", "clam").lower()
    if role not in ["lively", "clam"]:
        role = "clam"
    
    weight = event_config["weights"][role]
    x_change = x_change * weight
    y_change = y_change * weight
    
    return x_change, y_change, intimacy_change

def process_warning_event(user_id: int, mqtt_event_type: str, warning_message: str = "") -> Dict:
    """
    Process warning event for a user based on MQTT event_type.
    
    :param user_id: User ID
    :param mqtt_event_type: MQTT event_type value (drop, overload, impact)
    :param warning_message: Warning message content
    :return: Result dictionary
    """
    print(f"\n=== Processing Warning Event ===")
    print(f"User {user_id}, MQTT Event Type: {mqtt_event_type}")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        return {"success": False, "error": "User not found"}
    
    print(f"User: {user_data.get('name', 'Unknown')} (Role: {user_data.get('role', 'Unknown')})")
    
    # Determine event type based on MQTT event_type
    event_type = determine_warning_event_type(user_id, mqtt_event_type)
    if not event_type:
        return {"success": False, "message": "No matching event type found for this MQTT event_type"}
    
    event_config = WARNING_EVENTS[event_type]
    print(f"Event: {event_config['name']}")
    
    # Check probability
    if random.random() > event_config["probability"]:
        return {"success": False, "message": "Event not triggered due to probability"}
    
    # Get current values
    current_x = user_data.get('update_x_value', 0)
    current_y = user_data.get('update_y_value', 0)
    current_intimacy = user_data.get('intimacy_value', 0)
    
    print(f"Current values - X: {current_x}, Y: {current_y}, Intimacy: {current_intimacy}")
    
    # Calculate changes
    x_change, y_change, intimacy_change = calculate_warning_emotion_changes(
        user_data, event_type, current_x
    )
    
    print(f"Calculated changes - X: {x_change}, Y: {y_change}, Intimacy: {intimacy_change}")
    
    # Update database
    try:
        update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
        
        print(f"✅ Successfully updated database")
        
        return {
            "success": True,
            "event": event_config['name'],
            "mqtt_event_type": mqtt_event_type,
            "changes": {
                "x_change": x_change,
                "y_change": y_change,
                "intimacy_change": intimacy_change
            },
            "user_role": user_data["role"],
            "weights_applied": event_config["weights"],
            "probability": event_config["probability"]
        }
        
    except Exception as e:
        return {"success": False, "error": f"Database update failed: {e}"}

def process_mqtt_warning_event(mqtt_event_type: str, user_id: int = 1, warning_message: str = "") -> Dict:
    """
    Simple function to process MQTT warning events directly.
    This is the main function you can call with MQTT event data.
    
    :param mqtt_event_type: MQTT event_type value (drop, overload, impact)
    :param user_id: User ID (default: 1)
    :param warning_message: Optional warning message
    :return: Result dictionary
    """
    return process_warning_event(user_id, mqtt_event_type, warning_message)

def simulate_warning_scenarios():
    """Simulate various warning scenarios for testing."""
    print("=== Simulating Warning Scenarios ===\n")
    
    # Get a user from database
    conn = get_database_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM emotion ORDER BY id LIMIT 1")
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            print("❌ No users found in database")
            return
        
        user_id = user['id']
        print(f"Testing with User {user_id} ({user['name']})")
        
        # Test different MQTT event types from the image
        test_warnings = [
            ("drop", "Device fall detected"),
            ("overload", "Device violent squeeze detected"),
            ("impact", "Device throw/impact detected")
        ]
        
        for mqtt_event_type, message in test_warnings:
            print(f"\n--- Testing MQTT event: {mqtt_event_type} ---")
            result = process_warning_event(user_id, mqtt_event_type, message)
            
            if result.get('success'):
                print(f"✅ Success: {result['event']}")
                print(f"   Changes: X={result['changes']['x_change']}, Y={result['changes']['y_change']}, Intimacy={result['changes']['intimacy_change']}")
            else:
                print(f"❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")

def test_warning_function():
    """Test the warning function with sample data."""
    print("=== Testing Warning Function ===\n")
    
    # Test with a specific user
    print("1. Testing fall event processing:")
    result = process_warning_event(1, "drop", "Test fall event")
    if result.get('success'):
        print(f"   ✅ Success: {result['event']}")
    else:
        print(f"   ❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
    
    # Test with non-existent user
    print("\n2. Testing with non-existent user:")
    result = process_warning_event(999, "overload", "Test violent squeeze event")
    if result.get('success'):
        print(f"   ✅ Success: {result['event']}")
    else:
        print(f"   ❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")

if __name__ == "__main__":
    print("Warning Function System")
    print("Based on Image Requirements: 告警事件 (Warning Events)")
    
    print("\nChoose an option:")
    print("1. Run basic tests")
    print("2. Simulate warning scenarios")
    print("3. Run both")
    
    choice = input("Enter your choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        test_warning_function()
    elif choice == "2":
        simulate_warning_scenarios()
    elif choice == "3":
        test_warning_function()
        print("\n" + "="*50 + "\n")
        simulate_warning_scenarios()
    else:
        print("Invalid choice. Running basic tests...")
        test_warning_function()
