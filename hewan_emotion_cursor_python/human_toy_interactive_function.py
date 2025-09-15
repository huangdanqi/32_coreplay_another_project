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
# 人机互动 (Human-computer interaction) Events
# Based on the image specification:
# 事件类型: 人机互动 (Human-computer interaction)
# 事件名称: Various interaction events between owner and toy
# 触发事件: When device sub-account attributes have new data; When receiving event-type messages from mqtt

HUMAN_TOY_INTERACTIVE_EVENTS = {
    "liked_interaction_once": {
        "name": "主人触发玩具喜欢的互动1次",
        "english_name": "Owner triggers toy's liked interaction 1 time",
        "event_type": "人机互动",
        "trigger_condition": "主人对玩具触发了动作事件,需查看玩具角色对互动的喜好,是否喜欢该类互动,互动1次",
        "examples": ["摸摸脸", "拍拍头", "捏一下", "摇一摇"],
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称,出现新增数据时",
            "查询IP角色表-个性化参数-favorite_action"
        ],
        "probability": 0.6,
        "x_change": 1,  # +1 (开心值)
        "y_change_logic": {
            "x_less_than_0": -1,  # x<0时, y-1
            "x_greater_equal_0": 1  # x>=0时, y+1
        },
        "intimacy_change": 1,  # +1 (亲密度)
        "weights": {"lively": 1, "clam": 0.5}  # 性格活泼角色分值权重1, 性格平和角色分值权重0.5
    },
    
    "liked_interaction_3_to_5_times": {
        "name": "主人触发玩具喜欢的互动,1分钟内出现3-5次",
        "english_name": "Owner triggers toy's liked interaction, 3-5 times within 1 minute",
        "event_type": "人机互动",
        "trigger_condition": "同上,1分钟内喜欢的互动事件(可不同)出现3-5次",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算喜欢事件的次数",
            "查询IP角色表-个性化参数-favorite_action"
        ],
        "probability": 0.8,
        "x_change": 2,  # +2 (开心值)
        "y_change_logic": {
            "x_less_than_0": -2,  # x<0时, y-2
            "x_greater_equal_0": 2  # x>=0时, y+2
        },
        "intimacy_change": 2,  # +2 (亲密度)
        "weights": {"lively": 1, "clam": 1}  # 性格活泼角色分值权重1, 性格平和角色分值权重1
    },
    
    "liked_interaction_over_5_times": {
        "name": "主人触发玩具喜欢的互动,1分钟内出现5次以上",
        "english_name": "Owner triggers toy's liked interaction, more than 5 times within 1 minute",
        "event_type": "人机互动",
        "trigger_condition": "同上,1分钟内喜欢的互动事件(可不同)出现5次以上(不含5)",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算喜欢事件的次数",
            "查询IP角色表-个性化参数-favorite_action"
        ],
        "probability": 1.0,
        "x_change": 3,  # +3 (开心值)
        "y_change_logic": {
            "x_less_than_0": -3,  # x<0时, y-3
            "x_greater_equal_0": 3  # x>=0时, y+3
        },
        "intimacy_change": 3,  # +3 (亲密度)
        "weights": {"lively": 1.5, "clam": 1.5}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.5
    },
    
    "disliked_interaction_once": {
        "name": "主人触发玩具讨厌的互动1次",
        "english_name": "Owner triggers toy's disliked interaction 1 time",
        "event_type": "人机互动",
        "trigger_condition": "主人对玩具触发了动作事件,需查看玩具角色对互动的喜好,是否讨厌该类互动,互动1次",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称,出现新增数据时",
            "查询IP角色表-个性化参数-annoying_action"
        ],
        "probability": 0.3,
        "x_change": -1,  # -1 (开心值)
        "y_change_logic": {
            "x_less_than_0": 1,  # x<0时, y+1
            "x_greater_equal_0": -1  # x>=0时, y-1
        },
        "intimacy_change": -1,  # -1 (亲密度)
        "weights": {"lively": 1, "clam": 0.5}  # 性格活泼角色分值权重1, 性格平和角色分值权重0.5
    },
    
    "disliked_interaction_3_to_5_times": {
        "name": "主人触发玩具讨厌的互动,1分钟内出现3-5次",
        "english_name": "Owner triggers toy's disliked interaction, 3-5 times within 1 minute",
        "event_type": "人机互动",
        "trigger_condition": "同上,1分钟内讨厌的互动事件(可不同)出现3-5次",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算讨厌事件的次数",
            "查询IP角色表-个性化参数-annoying_action"
        ],
        "probability": 0.6,
        "x_change": -2,  # -2 (开心值)
        "y_change_logic": {
            "x_less_than_0": 2,  # x<0时, y+2
            "x_greater_equal_0": -2  # x>=0时, y-2
        },
        "intimacy_change": -2,  # -2 (亲密度)
        "weights": {"lively": 1, "clam": 1}  # 性格活泼角色分值权重1, 性格平和角色分值权重1
    },
    
    "disliked_interaction_over_5_times": {
        "name": "主人触发玩具讨厌的互动,1分钟内出现5次以上",
        "english_name": "Owner triggers toy's disliked interaction, more than 5 times within 1 minute",
        "event_type": "人机互动",
        "trigger_condition": "同上,1分钟内讨厌的互动事件(可不同)出现5次以上(不含5)",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算讨厌事件的次数",
            "查询IP角色表-个性化参数-annoying_action"
        ],
        "probability": 0.8,
        "x_change": -3,  # -3 (开心值)
        "y_change_logic": {
            "x_less_than_0": 3,  # x<0时, y+3
            "x_greater_equal_0": -3  # x>=0时, y-3
        },
        "intimacy_change": -3,  # -3 (亲密度)
        "weights": {"lively": 1.5, "clam": 1.5}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1.5
    },
    
    "neutral_interaction_over_5_times": {
        "name": "主人触发玩具非喜欢非讨厌的互动,事件表中事件类型为人机互动,1分钟内出现5次以上",
        "english_name": "Owner triggers toy's neither liked nor disliked interaction, event type in event table is human-machine interaction, occurs 5+ times within 1 minute",
        "event_type": "人机互动",
        "trigger_condition": "主人对玩具触发了动作事件,需查看玩具角色对互动的喜好,是否不喜欢也不讨厌该类互动,1分钟内出现5次以上(事件可不同,不含5)",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算事件的次数",
            "查询IP角色表-个性化参数-annoying_action",
            "查询事件表-事件类型=人机互动"
        ],
        "probability": 0.8,
        "x_change": 1,  # +1 (开心值)
        "y_change_logic": {
            "x_less_than_0": -1,  # x<0时, y-1
            "x_greater_equal_0": 1  # x>=0时, y+1
        },
        "intimacy_change": 1,  # +1 (亲密度)
        "weights": {"lively": 1, "clam": 1}  # 性格活泼角色分值权重1, 性格平和角色分值权重1
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
            "SELECT id, name, role, update_x_value, update_y_value, intimacy_value, favorite_action, annoying_action FROM emotion WHERE id = %s",
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

def get_recent_interactions(user_id: int, minutes: int = 1) -> List[Dict]:
    """Get recent interactions for a user within specified timeframe."""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        cursor.execute("""
            SELECT toy_id, target_toy_id, interaction_type, trigger_time, event_name
            FROM toy_interaction_events 
            WHERE target_toy_id = %s 
            AND trigger_time >= %s
            ORDER BY trigger_time DESC
        """, (user_id, cutoff_time))
        
        interactions = cursor.fetchall()
        cursor.close()
        conn.close()
        return interactions
    except mysql.connector.Error as e:
        print(f"Error fetching recent interactions: {e}")
        if conn:
            conn.close()
        return []

def check_interaction_preference(interaction_type: str, user_data: Dict) -> str:
    """
    Check if the interaction type is liked, disliked, or neutral for the user.
    
    :param interaction_type: Type of interaction
    :param user_data: User data containing preferences
    :return: 'liked', 'disliked', or 'neutral'
    """
    import json
    
    # Handle JSON format for favorite_action and annoying_action
    favorite_actions = []
    annoying_actions = []
    
    try:
        if user_data.get('favorite_action'):
            if user_data['favorite_action'].startswith('['):
                # JSON format
                favorite_actions = json.loads(user_data['favorite_action'])
            else:
                # Comma-separated format
                favorite_actions = user_data['favorite_action'].split(',')
    except (json.JSONDecodeError, AttributeError):
        favorite_actions = []
    
    try:
        if user_data.get('annoying_action'):
            if user_data['annoying_action'].startswith('['):
                # JSON format
                annoying_actions = json.loads(user_data['annoying_action'])
            else:
                # Comma-separated format
                annoying_actions = user_data['annoying_action'].split(',')
    except (json.JSONDecodeError, AttributeError):
        annoying_actions = []
    
    # Clean up the action lists
    favorite_actions = [action.strip() for action in favorite_actions if action and action.strip()]
    annoying_actions = [action.strip() for action in annoying_actions if action and action.strip()]
    
    if interaction_type in favorite_actions:
        return 'liked'
    elif interaction_type in annoying_actions:
        return 'disliked'
    else:
        return 'neutral'

def count_recent_interactions_by_preference(user_id: int, preference: str, minutes: int = 1) -> int:
    """
    Count recent interactions by preference type within specified timeframe.
    
    :param user_id: User ID
    :param preference: 'liked', 'disliked', or 'neutral'
    :param minutes: Timeframe in minutes
    :return: Count of interactions
    """
    user_data = get_user_data(user_id)
    if not user_data:
        return 0
    
    interactions = get_recent_interactions(user_id, minutes)
    if not interactions:
        return 0
    
    count = 0
    for interaction in interactions:
        interaction_type = interaction.get('interaction_type', '')
        if check_interaction_preference(interaction_type, user_data) == preference:
            count += 1
    
    return count

def determine_interaction_event_type(user_id: int, interaction_type: str) -> Optional[str]:
    """
    Determine which event type should be triggered based on interaction history.
    
    :param user_id: User ID
    :param interaction_type: Type of interaction
    :return: Event type key or None
    """
    user_data = get_user_data(user_id)
    if not user_data:
        return None
    
    preference = check_interaction_preference(interaction_type, user_data)
    
    if preference == 'liked':
        count = count_recent_interactions_by_preference(user_id, 'liked', minutes=1)
        # For the first interaction (count = 0), we should trigger the "once" event
        # We add 1 to the count to simulate the current interaction being processed
        effective_count = count + 1
        if effective_count == 1:
            return 'liked_interaction_once'
        elif 3 <= effective_count <= 5:
            return 'liked_interaction_3_to_5_times'
        elif effective_count > 5:
            return 'liked_interaction_over_5_times'
    
    elif preference == 'disliked':
        count = count_recent_interactions_by_preference(user_id, 'disliked', minutes=1)
        # For the first interaction (count = 0), we should trigger the "once" event
        effective_count = count + 1
        if effective_count == 1:
            return 'disliked_interaction_once'
        elif 3 <= effective_count <= 5:
            return 'disliked_interaction_3_to_5_times'
        elif effective_count > 5:
            return 'disliked_interaction_over_5_times'
    
    else:  # neutral
        count = count_recent_interactions_by_preference(user_id, 'neutral', minutes=1)
        effective_count = count + 1
        if effective_count > 5:
            return 'neutral_interaction_over_5_times'
    
    return None

def calculate_interaction_emotion_changes(user_data: Dict, event_type: str, current_x: float) -> Tuple[float, float, int]:
    """Calculate emotion changes based on interaction event and user data."""
    if event_type not in HUMAN_TOY_INTERACTIVE_EVENTS:
        return 0.0, 0.0, 0
    
    event_config = HUMAN_TOY_INTERACTIVE_EVENTS[event_type]
    
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

def process_human_toy_interaction(user_id: int, interaction_type: str) -> Dict:
    """
    Process human-toy interaction event for a user.
    
    :param user_id: User ID
    :param interaction_type: Type of interaction
    :return: Result dictionary
    """
    print(f"\n=== Processing Human-Toy Interaction ===")
    print(f"User {user_id}, Interaction: {interaction_type}")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        return {"success": False, "error": "User not found"}
    
    print(f"User: {user_data.get('name', 'Unknown')} (Role: {user_data.get('role', 'Unknown')})")
    
    # Determine event type based on interaction history
    event_type = determine_interaction_event_type(user_id, interaction_type)
    if not event_type:
        return {"success": False, "message": "No matching event type found for this interaction"}
    
    event_config = HUMAN_TOY_INTERACTIVE_EVENTS[event_type]
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
    x_change, y_change, intimacy_change = calculate_interaction_emotion_changes(
        user_data, event_type, current_x
    )
    
    print(f"Calculated changes - X: {x_change}, Y: {y_change}, Intimacy: {intimacy_change}")
    
    # Update database
    try:
        update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
        
        # Record the interaction event
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO toy_interaction_events 
                (toy_id, target_toy_id, event_type, event_name, interaction_type, trigger_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (999, user_id, "人机互动", event_config['name'], interaction_type, datetime.now()))
            conn.commit()
            cursor.close()
            conn.close()
        
        print(f"✅ Successfully updated database")
        
        return {
            "success": True,
            "event": event_config['name'],
            "interaction_type": interaction_type,
            "preference": check_interaction_preference(interaction_type, user_data),
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

def simulate_interaction_scenario():
    """Simulate various interaction scenarios for testing."""
    print("=== Simulating Human-Toy Interaction Scenarios ===\n")
    
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
        
        # Test different interaction types
        test_interactions = ["摸摸脸", "拍拍头", "捏一下", "摇一摇"]
        
        for interaction in test_interactions:
            print(f"\n--- Testing interaction: {interaction} ---")
            result = process_human_toy_interaction(user_id, interaction)
            
            if result.get('success'):
                print(f"✅ Success: {result['event']}")
                print(f"   Changes: X={result['changes']['x_change']}, Y={result['changes']['y_change']}, Intimacy={result['changes']['intimacy_change']}")
            else:
                print(f"❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")

def test_interaction_function():
    """Test the interaction function with sample data."""
    print("=== Testing Human-Toy Interaction Function ===\n")
    
    # Test with a specific user
    print("1. Testing interaction processing:")
    result = process_human_toy_interaction(1, "摸摸脸")
    if result.get('success'):
        print(f"   ✅ Success: {result['event']}")
    else:
        print(f"   ❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
    
    # Test with non-existent user
    print("\n2. Testing with non-existent user:")
    result = process_human_toy_interaction(999, "拍拍头")
    if result.get('success'):
        print(f"   ✅ Success: {result.get('error', result.get('message', 'Unknown error'))}")

def test_disliked_interaction_over_5_times():
    """Test the disliked_interaction_over_5_times event specifically."""
    print("=== Testing Disliked Interaction Over 5 Times Event ===\n")
    
    user_id = 1
    disliked_interaction = "捏一下"  # This is in the user's annoying_action list
    
    print(f"Testing with User {user_id} and disliked interaction: {disliked_interaction}")
    print("This test will simulate multiple disliked interactions to trigger the 'over 5 times' event")
    
    # First, let's check current user state
    user_data = get_user_data(user_id)
    if not user_data:
        print("❌ User not found")
        return
    
    print(f"\nCurrent user state:")
    print(f"  Name: {user_data.get('name')}")
    print(f"  Role: {user_data.get('role')}")
    print(f"  X value: {user_data.get('update_x_value')}")
    print(f"  Y value: {user_data.get('update_y_value')}")
    print(f"  Intimacy: {user_data.get('intimacy_value')}")
    print(f"  Annoying actions: {user_data.get('annoying_action')}")
    
    # Check current interaction count
    current_disliked_count = count_recent_interactions_by_preference(user_id, 'disliked', minutes=1)
    print(f"\nCurrent disliked interactions in last 1 minute: {current_disliked_count}")
    
    # Test the event type determination
    event_type = determine_interaction_event_type(user_id, disliked_interaction)
    print(f"Event type determined: {event_type}")
    
    if event_type == 'disliked_interaction_over_5_times':
        print("✅ Correctly identified as 'disliked_interaction_over_5_times' event")
        
        # Test emotion calculation
        current_x = user_data.get('update_x_value', 0)
        x_change, y_change, intimacy_change = calculate_interaction_emotion_changes(
            user_data, event_type, current_x
        )
        
        print(f"\nEmotion changes calculated:")
        print(f"  X change: {x_change}")
        print(f"  Y change: {y_change}")
        print(f"  Intimacy change: {intimacy_change}")
        
        # Show the expected changes based on current X value
        event_config = HUMAN_TOY_INTERACTIVE_EVENTS[event_type]
        if current_x < 0:
            expected_y = event_config["y_change_logic"]["x_less_than_0"]
        else:
            expected_y = event_config["y_change_logic"]["x_greater_equal_0"]
        
        print(f"\nExpected changes (before weights):")
        print(f"  X change: {event_config['x_change']}")
        print(f"  Y change: {expected_y} (X {'<' if current_x < 0 else '>='} 0)")
        print(f"  Intimacy change: {event_config['intimacy_change']}")
        
        # Show weight application
        role = user_data.get("role", "clam").lower()
        weight = event_config["weights"][role]
        print(f"  Weight for '{role}' role: {weight}")
        print(f"  Final X change: {event_config['x_change']} × {weight} = {x_change}")
        print(f"  Final Y change: {expected_y} × {weight} = {y_change}")
        
    else:
        print(f"❌ Expected 'disliked_interaction_over_5_times' but got: {event_type}")
        print("This means the interaction count doesn't meet the criteria (>5 times)")
        
        # Show what would be needed
        needed_count = 6 - current_disliked_count  # Need 6+ total for "over 5 times"
        print(f"\nTo trigger this event, you need {needed_count} more disliked interactions")
        print("(Total count must be > 5 for the 'over 5 times' event)")
        
        # Ask if user wants to simulate the scenario
        print(f"\nWould you like to simulate the scenario by adding {needed_count} disliked interactions?")
        simulate_choice = input("Enter 'y' to simulate, any other key to skip: ").strip().lower()
        
        if simulate_choice == 'y':
            simulate_disliked_interactions_for_testing(user_id, needed_count)
            print(f"\n✅ Added {needed_count} disliked interactions to database")
            print("Now run this test again to see the 'disliked_interaction_over_5_times' event!")
    
    print(f"\nEvent configuration:")
    event_config = HUMAN_TOY_INTERACTIVE_EVENTS['disliked_interaction_over_5_times']
    print(f"  Name: {event_config['name']}")
    print(f"  Probability: {event_config['probability']}")
    print(f"  X change: {event_config['x_change']}")
    print(f"  Y logic: {event_config['y_change_logic']}")
    print(f"  Intimacy change: {event_config['intimacy_change']}")
    print(f"  Weights: {event_config['weights']}")

def simulate_disliked_interactions_for_testing(user_id: int, count: int):
    """Simulate disliked interactions for testing purposes."""
    print(f"\n=== Simulating {count} Disliked Interactions ===")
    
    conn = get_database_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        current_time = datetime.now()
        
        # Add multiple disliked interactions within the last minute
        for i in range(count):
            # Each interaction is slightly different in time to simulate real scenario
            interaction_time = current_time - timedelta(seconds=i*10)  # 10 seconds apart
            
            cursor.execute("""
                INSERT INTO toy_interaction_events 
                (toy_id, target_toy_id, event_type, event_name, interaction_type, trigger_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (999, user_id, "人机互动", "测试-讨厌的互动", "捏一下", interaction_time))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully added {count} disliked interactions to database")
        print("These interactions will be counted for the next 1 minute")
        
    except Exception as e:
        print(f"❌ Error adding interactions: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Human-Toy Interactive Function System")
    print("Based on Image Requirements: 人机互动 (Human-computer interaction)")
    
    print("\nChoose an option:")
    print("1. Run basic tests")
    print("2. Simulate interaction scenarios")
    print("3. Run both")
    print("4. Test disliked_interaction_over_5_times specifically")
    
    choice = input("Enter your choice (1, 2, 3, or 4): ").strip()
    
    if choice == "1":
        test_interaction_function()
    elif choice == "2":
        simulate_interaction_scenario()
    elif choice == "3":
        test_interaction_function()
        print("\n" + "="*50 + "\n")
        simulate_interaction_scenario()
    elif choice == "4":
        test_disliked_interaction_over_5_times()
    else:
        print("Invalid choice. Running basic tests...")
        test_interaction_function()
