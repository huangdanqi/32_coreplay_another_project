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
# 持续互动 (Continuous Interaction)
# Based on the image specification:
# 事件类型: 持续互动 (Continuous Interaction)
# 事件名称: Events that track consecutive days of interactions (3, 7, 15 days)
# 触发事件: When memory status is 'on' and consecutive day counts meet thresholds

CONTINUOUS_INTERACTION_EVENTS = {
    "consecutive_3_days_action": {
        "name": "主人连续3天有动作互动",
        "english_name": "Owner has action interaction for 3 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续3天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有事件",
        "query_params": [
            "设备ID差记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=事件",
            "当天数量>=1",
            "连续天数=3"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 1,  # +1 (开心值)
        "y_change_logic": {
            "x_less_than_0": -1,  # x<0时, y-1
            "x_greater_equal_0": 1  # x>=0时, y+1
        },
        "intimacy_change": 1,  # +1 (亲密度)
        "weights": {"lively": 1.0, "clam": 1.0}  # 性格活泼角色分值权重1.0, 性格平和角色分值权重1.0
    },
    
    "consecutive_3_days_dialogue": {
        "name": "主人连续3天有对话互动",
        "english_name": "Owner has dialogue interaction for 3 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续3天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有query",
        "query_params": [
            "设备ID差记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=query",
            "当天数量>=1",
            "连续天数=3"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 1,  # +1 (开心值)
        "y_change_logic": {
            "x_less_than_0": -1,  # x<0时, y-1
            "x_greater_equal_0": 1  # x>=0时, y+1
        },
        "intimacy_change": 1,  # +1 (亲密度)
        "weights": {"lively": 1.0, "clam": 1.0}  # 性格活泼角色分值权重1.0, 性格平和角色分值权重1.0
    },
    
    "consecutive_7_days_action": {
        "name": "主人连续7天有动作互动",
        "english_name": "Owner has action interaction for 7 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续7天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有事件",
        "query_params": [
            "设备ID差记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=事件",
            "当天数量>=1",
            "连续天数=7"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 2,  # +2 (开心值)
        "y_change_logic": {
            "x_less_than_0": -2,  # x<0时, y-2
            "x_greater_equal_0": 2  # x>=0时, y+2
        },
        "intimacy_change": 2,  # +2 (亲密度)
        "weights": {"lively": 1.0, "clam": 1.0}  # 性格活泼角色分值权重1.0, 性格平和角色分值权重1.0
    },
    
    "consecutive_7_days_dialogue": {
        "name": "主人连续7天有对话互动",
        "english_name": "Owner has dialogue interaction for 7 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续7天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有query",
        "query_params": [
            "设备ID差记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=query",
            "当天数量>=1",
            "连续天数=7"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 2,  # +2 (开心值)
        "y_change_logic": {
            "x_less_than_0": -2,  # x<0时, y-2
            "x_greater_equal_0": 2  # x>=0时, y+2
        },
        "intimacy_change": 2,  # +2 (亲密度)
        "weights": {"lively": 1.5, "clam": 1.0}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.0
    },
    
    "consecutive_15_days_action": {
        "name": "主人连续15天有动作互动",
        "english_name": "Owner has action interaction for 15 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续15天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有事件",
        "query_params": [
            "设备ID差记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=事件",
            "当天数量>=1",
            "连续天数=15"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 3,  # +3 (开心值)
        "y_change_logic": {
            "x_less_than_0": -3,  # x<0时, y-3
            "x_greater_equal_0": 3  # x>=0时, y+3
        },
        "intimacy_change": 3,  # +3 (亲密度)
        "weights": {"lively": 1.5, "clam": 1.0}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.0
    },
    
    "consecutive_15_days_dialogue": {
        "name": "主人连续15天有对话互动",
        "english_name": "Owner has dialogue interaction for 15 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续15天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有query",
        "query_params": [
            "设备ID差记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=query",
            "当天数量>=1",
            "连续天数=15"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 3,  # +3 (开心值)
        "y_change_logic": {
            "x_less_than_0": -3,  # x<0时, y-3
            "x_greater_equal_0": 3  # x>=0时, y+3
        },
        "intimacy_change": 3,  # +3 (亲密度)
        "weights": {"lively": 1.5, "clam": 1.0}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.0
    },
    
    "consecutive_30_days_action": {
        "name": "主人连续30天有动作互动",
        "english_name": "Owner has action interaction for 30 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续30天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有事件",
        "query_params": [
            "设备ID签记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=事件",
            "当天数量>=1",
            "连续天数=30"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 4,  # +4 (开心值)
        "y_change_logic": {
            "x_less_than_0": -4,  # x<0时, y-4
            "x_greater_equal_0": 4  # x>=0时, y+4
        },
        "intimacy_change": 1.5,  # +1.5 (亲密度)
        "weights": {"lively": 1.5, "clam": 1.0}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.0
    },
    
    "consecutive_30_days_dialogue": {
        "name": "主人连续30天有对话互动",
        "english_name": "Owner has dialogue interaction for 30 consecutive days",
        "event_type": "持续互动",
        "trigger_condition": "连续30天 memory状态为on的相关消息表中,每天有至少一条新增的消息类型有query",
        "query_params": [
            "设备ID签记忆表-状态=on,得到记忆ID",
            "记忆ID查消息表-消息类型=query",
            "当天数量>=1",
            "连续天数=30"
        ],
        "probability": 1.0,  # Always triggers if conditions are met
        "x_change": 4,  # +4 (开心值)
        "y_change_logic": {
            "x_less_than_0": -4,  # x<0时, y-4
            "x_greater_equal_0": 4  # x>=0时, y+4
        },
        "intimacy_change": 1.5,  # +1.5 (亲密度)
        "weights": {"lively": 1.5, "clam": 1.0}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.0
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

# This function is no longer needed since we're passing event type directly
# def determine_dialogue_event_type(owner_emotion: str) -> Optional[str]:
#     """
#     Determine which dialogue event type should be triggered based on owner's emotion.
#     
#     :param owner_emotion: Owner's emotional state from event extraction agent
#     :return: Event type key or None
#     """
#     # Positive emotions: 开心快乐、兴奋激动
#     positive_emotions = ["开心", "快乐", "兴奋", "激动", "happy", "joyful", "excited", "thrilled"]
#     
#     # Negative emotions: 生气愤怒、悲伤难过、担忧、焦虑忧愁
#     negative_emotions = ["生气", "愤怒", "悲伤", "难过", "担忧", "焦虑", "忧愁", "angry", "furious", "sad", "distressed", "worried", "anxious", "melancholic"]
#     
#     owner_emotion_lower = owner_emotion.lower()
#     
#     # Check for positive emotions
#     for emotion in positive_emotions:
#         if emotion.lower() in owner_emotion_lower:
#             return 'positive_emotional_dialogue'
#     
#     # Check for negative emotions
#     for emotion in negative_emotions:
#         if emotion.lower() in owner_emotion_lower:
#             return 'negative_emotional_dialogue'
#     
#     return None

def calculate_continuous_interaction_emotion_changes(user_data: Dict, event_type: str, current_x: float) -> Tuple[float, float, int]:
    """Calculate emotion changes based on continuous interaction event and user data."""
    if event_type not in CONTINUOUS_INTERACTION_EVENTS:
        return 0.0, 0.0, 0
    
    event_config = CONTINUOUS_INTERACTION_EVENTS[event_type]
    
    # Get base changes
    x_change = event_config["x_change"]
    intimacy_change = event_config["intimacy_change"]
    
    # Calculate Y change based on current X value
    if current_x < 0:
        y_change = event_config["y_change_logic"]["x_less_than_0"]
    else:
        y_change = event_config["y_change_logic"]["x_greater_equal_0"]
    
    # Apply role weights (only to X and Y, not intimacy as per image requirement)
    role = user_data.get("role", "clam").lower()
    if role not in ["lively", "clam"]:
        role = "clam"
    
    weight = event_config["weights"][role]
    x_change = x_change * weight
    y_change = y_change * weight
    
    # Intimacy is not affected by weights as specified in the image
    return x_change, y_change, intimacy_change

def process_continuous_interaction_event(user_id: int, event_type: str, interaction_message: str = "") -> Dict:
    """
    Process continuous interaction event for a user based on event type.
    
    :param user_id: User ID
    :param event_type: Event type (e.g., 'consecutive_3_days_action', 'consecutive_7_days_dialogue', etc.)
    :param interaction_message: Optional interaction message content
    :return: Result dictionary
    """
    print(f"\n=== Processing Continuous Interaction Event ===")
    print(f"User {user_id}, Event Type: {event_type}")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        return {"success": False, "error": "User not found"}
    
    print(f"User: {user_data.get('name', 'Unknown')} (Role: {user_data.get('role', 'Unknown')})")
    
    # Check if event type is valid
    if event_type not in CONTINUOUS_INTERACTION_EVENTS:
        return {"success": False, "message": f"Invalid event type. Use one of: {list(CONTINUOUS_INTERACTION_EVENTS.keys())}"}
    
    event_config = CONTINUOUS_INTERACTION_EVENTS[event_type]
    print(f"Event: {event_config['name']}")
    
    # Check probability (should always be 1.0 for continuous interaction events)
    if random.random() > event_config["probability"]:
        return {"success": False, "message": "Event not triggered due to probability"}
    
    # Get current values
    current_x = user_data.get('update_x_value', 0)
    current_y = user_data.get('update_y_value', 0)
    current_intimacy = user_data.get('intimacy_value', 0)
    
    print(f"Current values - X: {current_x}, Y: {current_y}, Intimacy: {current_intimacy}")
    
    # Calculate changes
    x_change, y_change, intimacy_change = calculate_continuous_interaction_emotion_changes(
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
            "event_type": event_type,
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

def process_keep_interactive_event(event_type: str, user_id: int = 1, interaction_message: str = "") -> Dict:
    """
    Simple function to process continuous interaction events directly.
    This is the main function you can call with event type and user ID.
    
    :param event_type: Event type (e.g., 'consecutive_3_days_action', 'consecutive_7_days_dialogue', etc.)
    :param user_id: User ID (default: 1)
    :param interaction_message: Optional interaction message content
    :return: Result dictionary
    """
    return process_continuous_interaction_event(user_id, event_type, interaction_message)

def simulate_continuous_interaction_scenarios():
    """Simulate various continuous interaction scenarios for testing."""
    print("=== Simulating Continuous Interaction Scenarios ===\n")
    
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
        
        # Test different event types from the image
        test_events = [
            ("consecutive_3_days_action", "Owner had action interactions for 3 consecutive days"),
            ("consecutive_7_days_dialogue", "Owner had dialogue interactions for 7 consecutive days"),
            ("consecutive_15_days_action", "Owner had action interactions for 15 consecutive days"),
            ("consecutive_30_days_action", "Owner had action interactions for 30 consecutive days"),
            ("consecutive_30_days_dialogue", "Owner had dialogue interactions for 30 consecutive days")
        ]
        
        for event_type, message in test_events:
            print(f"\n--- Testing event type: {event_type} ---")
            result = process_continuous_interaction_event(user_id, event_type, message)
            
            if result.get('success'):
                print(f"✅ Success: {result['event']}")
                print(f"   Changes: X={result['changes']['x_change']}, Y={result['changes']['y_change']}, Intimacy={result['changes']['intimacy_change']}")
            else:
                print(f"❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")

def test_continuous_interaction_function():
    """Test the continuous interaction function with sample data."""
    print("=== Testing Continuous Interaction Function ===\n")
    
    # Test with a specific user
    print("1. Testing consecutive 3 days action:")
    result = process_continuous_interaction_event(1, "consecutive_3_days_action", "Owner had actions for 3 days")
    if result.get('success'):
        print(f"   ✅ Success: {result['event']}")
    else:
        print(f"   ❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
    
    # Test with non-existent user
    print("\n2. Testing with non-existent user:")
    result = process_continuous_interaction_event(999, "consecutive_7_days_dialogue", "Owner had dialogue for 7 days")
    if result.get('success'):
        print(f"   ✅ Success: {result['event']}")
    else:
        print(f"   ❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")

if __name__ == "__main__":
    print("Keep Interactive Function System")
    print("Based on Image Requirements: 持续互动 (Continuous Interaction)")
    
    print("\nChoose an option:")
    print("1. Run basic tests")
    print("2. Simulate continuous interaction scenarios")
    print("3. Run both")
    
    choice = input("Enter your choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        test_continuous_interaction_function()
    elif choice == "2":
        simulate_continuous_interaction_scenarios()
    elif choice == "3":
        test_continuous_interaction_function()
        print("\n" + "="*50 + "\n")
        simulate_continuous_interaction_scenarios()
    else:
        print("Invalid choice. Running basic tests...")
        test_continuous_interaction_function()
