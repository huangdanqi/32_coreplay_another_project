import mysql.connector
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import random
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
# 密友同频 (Close Friend Frequency) Event
# Based on the image specification:
# 事件类型: 密友同频 (Close Friend Frequency)
# 事件名称: 玩具同频事件 (Toy Frequency Event)
# 触发事件: 两个互为密友的玩具,同时(5秒内)被各自主人触发的人机互动类事件时,触发同频事件
# (When two toys, who are close friends, are simultaneously (within 5 seconds) triggered by their respective owners with the same human-computer interaction event, a frequency event is triggered.)

SAME_FREQUENCY_EVENTS = {
    "close_friend_frequency": {
        "name": "玩具同频事件",
        "english_name": "Toy Frequency Event",
        "event_type": "密友同频",
        "trigger_condition": "两个互为密友的玩具,同时(5秒内)被各自主人触发的人机互动类事件时,触发同频事件",
        "query_params": "查询玩具互动事件数据表-事件类型=同频,出现新增数据时",
        "probability": 1.0,  # 100% chance when conditions are met
        "x_change": 3,  # +3
        "y_change_logic": {
            "x_less_than_0": -3,  # x<0时, y-3
            "x_greater_equal_0": 3  # x>=0时, y+3
        },
        "intimacy_change": 0,  # 0 (不受权重影响)
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

def get_close_friends(user_id: int) -> List[int]:
    """Get list of close friends for a given user."""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT friend_toy_id FROM toy_friendships 
            WHERE toy_id = %s AND deleted_at IS NULL
        """, (user_id,))
        
        friends = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return friends
    except mysql.connector.Error as e:
        print(f"Error fetching friends: {e}")
        if conn:
            conn.close()
        return []

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

def check_same_frequency_event(user1_id: int, user2_id: int, time_window_seconds: int = 5) -> Optional[Dict]:
    """
    Check if two close friends had the same interaction type within the time window.
    
    :param user1_id: First user ID
    :param user2_id: Second user ID  
    :param time_window_seconds: Time window in seconds (default 5 seconds)
    :return: Frequency event info if detected, None otherwise
    """
    # Get recent interactions for both users
    user1_interactions = get_recent_interactions(user1_id, minutes=1)
    user2_interactions = get_recent_interactions(user2_id, minutes=1)
    
    if not user1_interactions or not user2_interactions:
        return None
    
    # Check for same interaction type within time window
    for interaction1 in user1_interactions:
        for interaction2 in user2_interactions:
            # Check if same interaction type
            if interaction1['interaction_type'] == interaction2['interaction_type']:
                # Check if within time window
                time_diff = abs((interaction1['trigger_time'] - interaction2['trigger_time']).total_seconds())
                if time_diff <= time_window_seconds:
                    return {
                        'user1_id': user1_id,
                        'user2_id': user2_id,
                        'interaction_type': interaction1['interaction_type'],
                        'user1_time': interaction1['trigger_time'],
                        'user2_time': interaction2['trigger_time'],
                        'time_difference_seconds': time_diff
                    }
    
    return None

def calculate_frequency_emotion_changes(user_data: Dict, event_type: str, current_x: int) -> Tuple[int, int, int]:
    """Calculate emotion changes based on frequency event and user data."""
    if event_type not in SAME_FREQUENCY_EVENTS:
        return 0, 0, 0
    
    event_config = SAME_FREQUENCY_EVENTS[event_type]
    
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
    x_change = int(x_change * weight)
    y_change = int(y_change * weight)
    
    return x_change, y_change, intimacy_change

def process_same_frequency_event(user1_id: int, user2_id: int) -> Dict:
    """
    Process same frequency event for two close friends.
    
    :param user1_id: First user ID
    :param user2_id: Second user ID
    :return: Result dictionary
    """
    print(f"\n=== Processing Same Frequency Event ===")
    print(f"Checking for frequency event between User {user1_id} and User {user2_id}")
    
    # Check if they are close friends
    user1_friends = get_close_friends(user1_id)
    if user2_id not in user1_friends:
        return {
            "success": False, 
            "error": f"Users {user1_id} and {user2_id} are not close friends"
        }
    
    # Check for same frequency event
    frequency_event = check_same_frequency_event(user1_id, user2_id, time_window_seconds=5)
    if not frequency_event:
        return {
            "success": False, 
            "message": "No same frequency event detected within 5 seconds"
        }
    
    print(f"✅ Same frequency event detected!")
    print(f"   Interaction type: {frequency_event['interaction_type']}")
    print(f"   Time difference: {frequency_event['time_difference_seconds']:.1f} seconds")
    
    # Get event configuration
    event_config = SAME_FREQUENCY_EVENTS["close_friend_frequency"]
    
    # Check probability (should be 100% but keeping the check for consistency)
    if random.random() > event_config["probability"]:
        return {
            "success": False, 
            "message": "Event not triggered due to probability"
        }
    
    # Process for both users
    results = {}
    
    for user_id in [user1_id, user2_id]:
        user_data = get_user_data(user_id)
        if not user_data:
            results[user_id] = {"success": False, "error": "User not found"}
            continue
        
        print(f"\n   Processing User {user_id} ({user_data.get('name', 'Unknown')}):")
        print(f"   Current X: {user_data['update_x_value']}, Y: {user_data['update_y_value']}")
        
        # Calculate changes
        x_change, y_change, intimacy_change = calculate_frequency_emotion_changes(
            user_data, "close_friend_frequency", user_data['update_x_value']
        )
        
        print(f"   Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
        
        # Update database
        try:
            update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
            
            # Record the frequency event
            conn = get_database_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO toy_interaction_events 
                    (toy_id, target_toy_id, event_type, event_name, interaction_type, trigger_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, user_id, "同频", event_config["name"], frequency_event['interaction_type'], datetime.now()))
                conn.commit()
                cursor.close()
                conn.close()
            
            results[user_id] = {
                "success": True,
                "event": event_config["name"],
                "interaction_type": frequency_event['interaction_type'],
                "changes": {
                    "x_change": x_change,
                    "y_change": y_change,
                    "intimacy_change": intimacy_change
                },
                "user_role": user_data["role"],
                "weights_applied": event_config["weights"]
            }
            
            print(f"   ✅ Successfully updated database")
            
        except Exception as e:
            results[user_id] = {"success": False, "error": f"Database update failed: {e}"}
            print(f"   ❌ Database update failed: {e}")
    
    return {
        "success": True,
        "frequency_event": frequency_event,
        "user1_result": results.get(user1_id, {}),
        "user2_result": results.get(user2_id, {}),
        "event_config": event_config
    }

def simulate_same_frequency_scenario():
    """Simulate a same frequency scenario for testing."""
    print("=== Simulating Same Frequency Scenario ===\n")
    
    # Get all users from database
    conn = get_database_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM emotion ORDER BY id LIMIT 3")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if len(users) < 2:
            print("❌ Need at least 2 users to test frequency events")
            return
        
        user1_id = users[0]['id']
        user2_id = users[1]['id']
        
        print(f"Testing frequency event between User {user1_id} ({users[0]['name']}) and User {user2_id} ({users[1]['name']})")
        
        # First, ensure they are friends
        print(f"\n1. Ensuring friendship between users...")
        from friends_function import add_friend
        friend_result = add_friend(user1_id, user2_id)
        if not friend_result.get('success'):
            print(f"   Note: {friend_result.get('error', 'Unknown error')}")
        
        # Simulate simultaneous interactions
        print(f"\n2. Simulating simultaneous interactions...")
        interaction_type = "摸摸脸"
        
        # Record interaction for user1
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            current_time = datetime.now()
            
            # Insert interaction for user1
            cursor.execute("""
                INSERT INTO toy_interaction_events 
                (toy_id, target_toy_id, event_type, event_name, interaction_type, trigger_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (999, user1_id, "interaction", "摸摸脸", interaction_type, current_time))
            
            # Insert interaction for user2 (within 5 seconds)
            cursor.execute("""
                INSERT INTO toy_interaction_events 
                (toy_id, target_toy_id, event_type, event_name, interaction_type, trigger_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (999, user2_id, "interaction", "摸摸脸", interaction_type, current_time + timedelta(seconds=2)))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"   ✅ Recorded simultaneous interactions")
        
        # Now test the frequency event
        print(f"\n3. Testing frequency event detection...")
        result = process_same_frequency_event(user1_id, user2_id)
        
        if result.get('success'):
            print(f"\n✅ Frequency event processed successfully!")
            print(f"   User 1 result: {result['user1_result'].get('success', False)}")
            print(f"   User 2 result: {result['user2_result'].get('success', False)}")
        else:
            print(f"\n❌ Frequency event failed: {result.get('error', result.get('message', 'Unknown error'))}")
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")

def test_same_frequency_function():
    """Test the same frequency function with sample data."""
    print("=== Testing Same Frequency Function ===\n")
    
    # Test with specific users
    print("1. Testing frequency event detection:")
    result = process_same_frequency_event(1, 2)
    if result.get('success'):
        print(f"   ✅ Success: {result}")
    else:
        print(f"   ❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")
    
    # Test with non-friends
    print("\n2. Testing with non-friends:")
    result = process_same_frequency_event(1, 999)  # Non-existent user
    if result.get('success'):
        print(f"   ✅ Success: {result}")
    else:
        print(f"   ❌ Failed: {result.get('error', result.get('message', 'Unknown error'))}")

if __name__ == "__main__":
    print("Same Frequency Event Processing System")
    print("Based on Image Requirements: 密友同频 (Close Friend Frequency)")
    
    print("\nChoose an option:")
    print("1. Run basic tests")
    print("2. Simulate same frequency scenario")
    print("3. Run both")
    
    choice = input("Enter your choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        test_same_frequency_function()
    elif choice == "2":
        simulate_same_frequency_scenario()
    elif choice == "3":
        test_same_frequency_function()
        print("\n" + "="*50 + "\n")
        simulate_same_frequency_scenario()
    else:
        print("Invalid choice. Running basic tests...")
        test_same_frequency_function()
