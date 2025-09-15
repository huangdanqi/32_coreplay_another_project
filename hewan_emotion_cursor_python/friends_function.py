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
FRIEND_EVENTS = {
    "made_new_friend": {
        "name": "交到新朋友",
        "trigger_condition": "该玩具通过手机APP成功添加了好友(接受密友申请/发送的密友申请被通过)",
        "query_params": "查询玩具日志数据表-玩具的朋友属性有新增数据",
        "probability": 1.0,
        "x_change": 2,
        "y_change_logic": {
            "x_less_than_0": -2,  # x<0时, y-2
            "x_greater_equal_0": 2  # x>=0时, y+2
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.5, "clam": 1.0}
    },
    "friend_deleted": {
        "name": "被删除好友",
        "trigger_condition": "该玩具被已成为密友的玩具删除好友",
        "query_params": "查询玩具日志数据表-有玩具的朋友属性值被删除的与本玩具相同",
        "probability": 1.0,
        "x_change": -2,
        "y_change_logic": {
            "x_less_than_0": 2,  # x<0时, y+2
            "x_greater_equal_0": -2  # x>=0时, y-2
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.5, "clam": 1.0}
    }
}

INTERACTION_EVENTS = {
    "liked_single": {
        "name": "玩具密友触发喜欢的远程互动1次",
        "trigger_condition": "A玩具在列表中点击B玩具,远程互动,影响B玩具的心情坐标,需查看B玩具角色对互动的喜好,是否喜欢该类互动,互动1次",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称,出现新增数据时",
            "查询IP角色表-个性化参数-favorite_action"
        ],
        "probability": 0.5,
        "x_change": 1,
        "y_change_logic": {
            "x_less_than_0": -1,  # x<0时, y-1
            "x_greater_equal_0": 1  # x>=0时, y+1
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.0, "clam": 0.5}
    },
    "liked_3_to_5": {
        "name": "玩具密友触发喜欢的远程互动,1分钟内出现3-5次",
        "trigger_condition": "同上,1分钟内喜欢的互动事件(可不同)出现3-5次",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算喜欢事件的次数",
            "查询IP角色表-个性化参数-favorite_action"
        ],
        "probability": 0.7,
        "x_change": 2,
        "y_change_logic": {
            "x_less_than_0": -2,  # x<0时, y-2
            "x_greater_equal_0": 2  # x>=0时, y+2
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.0, "clam": 1.0}
    },
    "liked_5_plus": {
        "name": "玩具密友触发喜欢的远程互动,1分钟内出现5次以上",
        "trigger_condition": "同上,1分钟内喜欢的互动事件(可不同)出现5次以上(不含5)",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算喜欢事件的次数",
            "查询IP角色表-个性化参数-favorite_action"
        ],
        "probability": 1.0,
        "x_change": 3,
        "y_change_logic": {
            "x_less_than_0": -3,  # x<0时, y-3
            "x_greater_equal_0": 3  # x>=0时, y+3
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.5, "clam": 1.5}
    },
    "disliked_single": {
        "name": "玩具密友触发讨厌的远程互动1次",
        "trigger_condition": "A玩具在列表中点击B玩具,远程互动,影响B玩具的心情坐标,需查看B玩具角色对互动的喜好,是否讨厌该类互动,互动1次",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称,出现新增数据时",
            "查询IP角色表-个性化参数-annoying_action"
        ],
        "probability": 0.5,
        "x_change": -1,
        "y_change_logic": {
            "x_less_than_0": 1,  # x<0时, y+1
            "x_greater_equal_0": -1  # x>=0时, y-1
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.0, "clam": 0.5}
    },
    "disliked_3_to_5": {
        "name": "玩具密友触发讨厌的远程互动,1分钟内出现3-5次",
        "trigger_condition": "同上,1分钟内讨厌的互动事件(可不同)出现3-5次",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算讨厌事件的次数",
            "查询IP角色表-个性化参数-annoying_action"
        ],
        "probability": 0.7,
        "x_change": -2,
        "y_change_logic": {
            "x_less_than_0": 2,  # x<0时, y+2
            "x_greater_equal_0": -2  # x>=0时, y-2
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.0, "clam": 1.0}
    },
    "disliked_5_plus": {
        "name": "玩具密友触发讨厌的远程互动,1分钟内出现5次以上",
        "trigger_condition": "同上,1分钟内讨厌的互动事件(可不同)出现5次以上(不含5)",
        "query_params": [
            "查询玩具互动事件表-事件类型=互动-事件名称;触发时间,出现新增数据时,计算讨厌事件的次数",
            "查询IP角色表-个性化参数-annoying_action"
        ],
        "probability": 1.0,
        "x_change": -3,
        "y_change_logic": {
            "x_less_than_0": 3,  # x<0时, y+3
            "x_greater_equal_0": -3  # x>=0时, y-3
        },
        "intimacy_change": 0,
        "weights": {"lively": 1.5, "clam": 1.5}
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
            "SELECT id, role, update_x_value, update_y_value, intimacy_value, favorite_action, annoying_action FROM emotion WHERE id = %s",
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

def calculate_y_change(current_x: float, y_change_logic: Dict) -> int:
    """Calculate Y change based on current X value and logic rules."""
    if current_x < 0:
        return y_change_logic.get("x_less_than_0", 0)
    else:
        return y_change_logic.get("x_greater_equal_0", 0)

def apply_character_weight(change: int, user_role: str, weights: Dict) -> int:
    """Apply character role weight to the change value."""
    role_weight = weights.get(user_role.lower(), 1.0)
    return int(change * role_weight)

def process_friend_event(user_id: int, event_type: str) -> Dict:
    """Process friend-related events (add/delete friend)."""
    if event_type not in FRIEND_EVENTS:
        return {"success": False, "error": f"Unknown event type: {event_type}"}
    
    event_config = FRIEND_EVENTS[event_type]
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        return {"success": False, "error": "User not found"}
    
    # Check probability
    if random.random() > event_config["probability"]:
        return {"success": False, "message": "Event not triggered due to probability"}
    
    # Calculate changes
    x_change = event_config["x_change"]
    y_change = calculate_y_change(user_data["update_x_value"], event_config["y_change_logic"])
    intimacy_change = event_config["intimacy_change"]
    
    # Apply character weights
    x_change_weighted = apply_character_weight(x_change, user_data["role"], event_config["weights"])
    y_change_weighted = apply_character_weight(y_change, user_data["role"], event_config["weights"])
    
    # Update database
    try:
        update_emotion_in_database(user_id, x_change_weighted, y_change_weighted, intimacy_change)
        
        # Update friend count in database
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            if event_type == "made_new_friend":
                cursor.execute("UPDATE emotion SET friend_count = friend_count + 1 WHERE id = %s", (user_id,))
            elif event_type == "friend_deleted":
                cursor.execute("UPDATE emotion SET friend_count = GREATEST(friend_count - 1, 0) WHERE id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
        
        return {
            "success": True,
            "event": event_config["name"],
            "changes": {
                "x_change": x_change_weighted,
                "y_change": y_change_weighted,
                "intimacy_change": intimacy_change
            },
            "user_role": user_data["role"],
            "weights_applied": event_config["weights"]
        }
    except Exception as e:
        return {"success": False, "error": f"Database update failed: {e}"}

def get_interaction_count_in_timeframe(user_id: int, interaction_type: str, minutes: int = 1) -> int:
    """Get count of interactions of a specific type within the specified timeframe."""
    conn = get_database_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        cursor.execute("""
            SELECT COUNT(*) FROM toy_interaction_events 
            WHERE target_toy_id = %s 
            AND interaction_type = %s 
            AND trigger_time >= %s
        """, (user_id, interaction_type, cutoff_time))
        
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except mysql.connector.Error as e:
        print(f"Error counting interactions: {e}")
        if conn:
            conn.close()
        return 0

def is_liked_interaction(user_id: int, interaction_type: str) -> bool:
    """Check if an interaction type is liked by the user."""
    user_data = get_user_data(user_id)
    if not user_data or not user_data.get("favorite_action"):
        return False
    
    try:
        favorite_actions = json.loads(user_data["favorite_action"]) if isinstance(user_data["favorite_action"], str) else user_data["favorite_action"]
        return interaction_type in favorite_actions
    except (json.JSONDecodeError, TypeError):
        return False

def is_disliked_interaction(user_id: int, interaction_type: str) -> bool:
    """Check if an interaction type is disliked by the user."""
    user_data = get_user_data(user_id)
    if not user_data or not user_data.get("annoying_action"):
        return False
    
    try:
        annoying_actions = json.loads(user_data["annoying_action"]) if isinstance(user_data["annoying_action"], str) else user_data["annoying_action"]
        return interaction_type in annoying_actions
    except (json.JSONDecodeError, TypeError):
        return False

def process_interaction_event(user_id: int, interaction_type: str, source_toy_id: int) -> Dict:
    """Process interaction events based on frequency and user preferences."""
    # Check if interaction is liked or disliked
    is_liked = is_liked_interaction(user_id, interaction_type)
    is_disliked = is_disliked_interaction(user_id, interaction_type)
    
    if not is_liked and not is_disliked:
        return {"success": False, "message": "Interaction type not in user preferences"}
    
    # Get interaction count in last minute
    interaction_count = get_interaction_count_in_timeframe(user_id, interaction_type, 1)
    
    # Determine event type based on count and preference
    if is_liked:
        if interaction_count == 0:  # First interaction
            event_key = "liked_single"
        elif 3 <= interaction_count <= 5:
            event_key = "liked_3_to_5"
        elif interaction_count > 5:
            event_key = "liked_5_plus"
        else:
            event_key = "liked_single"  # Default for 1-2 interactions
    else:  # is_disliked
        if interaction_count == 0:  # First interaction
            event_key = "disliked_single"
        elif 3 <= interaction_count <= 5:
            event_key = "disliked_3_to_5"
        elif interaction_count > 5:
            event_key = "disliked_5_plus"
        else:
            event_key = "disliked_single"  # Default for 1-2 interactions
    
    event_config = INTERACTION_EVENTS[event_key]
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        return {"success": False, "error": "User not found"}
    
    # Check probability
    if random.random() > event_config["probability"]:
        return {"success": False, "message": "Event not triggered due to probability"}
    
    # Calculate changes
    x_change = event_config["x_change"]
    y_change = calculate_y_change(user_data["update_x_value"], event_config["y_change_logic"])
    intimacy_change = event_config["intimacy_change"]
    
    # Apply character weights
    x_change_weighted = apply_character_weight(x_change, user_data["role"], event_config["weights"])
    y_change_weighted = apply_character_weight(y_change, user_data["role"], event_config["weights"])
    
    # Update database
    try:
        update_emotion_in_database(user_id, x_change_weighted, y_change_weighted, intimacy_change)
        
        # Record the interaction event
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO toy_interaction_events 
                (toy_id, target_toy_id, event_type, event_name, interaction_type, trigger_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (source_toy_id, user_id, "interaction", event_config["name"], interaction_type, datetime.now()))
            conn.commit()
            cursor.close()
            conn.close()
        
        return {
            "success": True,
            "event": event_config["name"],
            "interaction_type": interaction_type,
            "interaction_count": interaction_count + 1,
            "changes": {
                "x_change": x_change_weighted,
                "y_change": y_change_weighted,
                "intimacy_change": intimacy_change
            },
            "user_role": user_data["role"],
            "weights_applied": event_config["weights"]
        }
    except Exception as e:
        return {"success": False, "error": f"Database update failed: {e}"}

def add_friend(user_id: int, friend_id: int) -> Dict:
    """Add a new friend relationship."""
    conn = get_database_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed"}
    
    try:
        cursor = conn.cursor()
        
        # Check if friendship already exists
        cursor.execute("""
            SELECT id FROM toy_friendships 
            WHERE toy_id = %s AND friend_toy_id = %s AND deleted_at IS NULL
        """, (user_id, friend_id))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return {"success": False, "error": "Friendship already exists"}
        
        # Add friendship
        cursor.execute("""
            INSERT INTO toy_friendships (toy_id, friend_toy_id, friendship_type)
            VALUES (%s, %s, 'regular_friend')
        """, (user_id, friend_id))
        
        # Add reverse friendship
        cursor.execute("""
            INSERT INTO toy_friendships (toy_id, friend_toy_id, friendship_type)
            VALUES (%s, %s, 'regular_friend')
        """, (friend_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Process emotion changes for both users
        user_result = process_friend_event(user_id, "made_new_friend")
        friend_result = process_friend_event(friend_id, "made_new_friend")
        
        return {
            "success": True,
            "message": "Friendship added successfully",
            "user_emotion_update": user_result,
            "friend_emotion_update": friend_result
        }
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return {"success": False, "error": f"Database error: {e}"}

def remove_friend(user_id: int, friend_id: int) -> Dict:
    """Remove a friend relationship."""
    conn = get_database_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed"}
    
    try:
        cursor = conn.cursor()
        
        # Soft delete friendships
        cursor.execute("""
            UPDATE toy_friendships 
            SET deleted_at = NOW() 
            WHERE (toy_id = %s AND friend_toy_id = %s) 
            OR (toy_id = %s AND friend_toy_id = %s)
        """, (user_id, friend_id, friend_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Process emotion changes for both users
        user_result = process_friend_event(user_id, "friend_deleted")
        friend_result = process_friend_event(friend_id, "friend_deleted")
        
        return {
            "success": True,
            "message": "Friendship removed successfully",
            "user_emotion_update": user_result,
            "friend_emotion_update": friend_result
        }
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return {"success": False, "error": f"Database error: {e}"}

def simulate_app_data():
    """Simulate data that would normally come from the mobile app."""
    print("=== Simulating Mobile App Data ===\n")
    
    # Simulate user IDs (assuming these exist in your emotion table)
    user_ids = [1, 2, 3, 4, 5]
    interaction_types = ["摸摸脸", "拍拍头", "捏一下", "摇一摇"]
    
    print("1. Simulating Friend Requests and Acceptances:")
    print("   - User 1 sends friend request to User 2")
    result = add_friend(1, 2)
    print(f"     Result: {result}")
    
    print("   - User 3 sends friend request to User 1")
    result = add_friend(3, 1)
    print(f"     Result: {result}")
    
    print("   - User 4 sends friend request to User 2")
    result = add_friend(4, 2)
    print(f"     Result: {result}")
    
    print("\n2. Simulating Toy Interactions (Liked Actions):")
    print("   - User 1 interacts with User 2 (摸摸脸)")
    result = process_interaction_event(2, "摸摸脸", 1)
    print(f"     Result: {result}")
    
    print("   - User 1 interacts with User 2 again (拍拍头)")
    result = process_interaction_event(2, "拍拍头", 1)
    print(f"     Result: {result}")
    
    print("   - User 3 interacts with User 1 (捏一下)")
    result = process_interaction_event(1, "捏一下", 3)
    print(f"     Result: {result}")
    
    print("   - User 4 interacts with User 2 (摇一摇)")
    result = process_interaction_event(2, "摇一摇", 4)
    print(f"     Result: {result}")
    
    print("\n3. Simulating High-Frequency Interactions (Testing 3-5 rule):")
    print("   - User 1 sends multiple interactions to User 2 within 1 minute:")
    for i in range(3):
        result = process_interaction_event(2, "摸摸脸", 1)
        print(f"     Interaction {i+1}: {result}")
    
    print("\n4. Simulating Disliked Interactions:")
    print("   - User 1 sends disliked interaction to User 3 (assuming 拍拍头 is disliked)")
    result = process_interaction_event(3, "拍拍头", 1)
    print(f"     Result: {result}")
    
    print("\n5. Simulating Friend Removal:")
    print("   - User 1 removes User 3 as friend")
    result = remove_friend(1, 3)
    print(f"     Result: {result}")
    
    print("\n6. Simulating Real-time Interaction Stream:")
    print("   - Simulating rapid interactions from multiple users:")
    
    # Simulate rapid interactions from different users
    interactions = [
        (1, 2, "摸摸脸"),
        (2, 1, "拍拍头"),
        (4, 2, "捏一下"),
        (1, 2, "摇一摇"),
        (3, 4, "摸摸脸"),
        (2, 4, "拍拍头"),
        (1, 2, "摸摸脸"),  # This should trigger 3-5 rule
        (4, 2, "捏一下"),   # This should trigger 3-5 rule
    ]
    
    for source_id, target_id, action in interactions:
        result = process_interaction_event(target_id, action, source_id)
        print(f"     {source_id} -> {target_id} ({action}): {result.get('success', False)}")
    
    print("\n7. Checking Current Database State:")
    print("   - Current friend counts and emotion values:")
    for user_id in user_ids[:3]:  # Check first 3 users
        user_data = get_user_data(user_id)
        if user_data:
            print(f"     User {user_id}: X={user_data['update_x_value']}, Y={user_data['update_y_value']}, Intimacy={user_data['intimacy_value']}")

def test_friends_function():
    """Test the friends function with sample data."""
    print("=== Testing Friends Function ===\n")
    
    # Test friend events
    print("1. Testing friend events:")
    print("   - Made new friend (user_id=1):")
    result = process_friend_event(1, "made_new_friend")
    print(f"     Result: {result}")
    
    print("   - Friend deleted (user_id=1):")
    result = process_friend_event(1, "friend_deleted")
    print(f"     Result: {result}")
    
    # Test interaction events
    print("\n2. Testing interaction events:")
    print("   - Liked interaction (摸摸脸, user_id=2, source_toy_id=1):")
    result = process_interaction_event(2, "摸摸脸", 1)
    print(f"     Result: {result}")
    
    print("   - Disliked interaction (拍拍头, user_id=2, source_toy_id=1):")
    result = process_interaction_event(2, "拍拍头", 1)
    print(f"     Result: {result}")
    
    # Test friendship management
    print("\n3. Testing friendship management:")
    print("   - Adding friend (user_id=1, friend_id=3):")
    result = add_friend(1, 3)
    print(f"     Result: {result}")
    
    print("   - Removing friend (user_id=1, friend_id=3):")
    result = remove_friend(1, 3)
    print(f"     Result: {result}")

def test_with_mysql_data():
    """Test the friends function using actual MySQL data and updating tables."""
    print("=== Testing with MySQL Data and Table Updates ===\n")
    
    # Get all users from database to see their current state
    print("1. Current Database State:")
    print("   - Reading all users from emotion table:")
    conn = get_database_connection()
    if not conn:
        print("     ❌ Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all users with their preferences
        cursor.execute("""
            SELECT id, name, role, update_x_value, update_y_value, intimacy_value, 
                   friend_count, favorite_action, annoying_action
            FROM emotion 
            ORDER BY id
        """)
        users = cursor.fetchall()
        
        if not users:
            print("     ❌ No users found in emotion table")
            return
        
        print(f"     ✅ Found {len(users)} users in database")
        
        # Display each user's current state
        for user in users:
            print(f"     User {user['id']} ({user['name']}):")
            print(f"       Role: {user['role']}")
            print(f"       X: {user['update_x_value']}, Y: {user['update_y_value']}, Intimacy: {user['intimacy_value']}")
            print(f"       Friends: {user['friend_count']}")
            
            # Parse and display favorite actions
            try:
                if user['favorite_action']:
                    if isinstance(user['favorite_action'], str):
                        favorite_actions = json.loads(user['favorite_action'])
                    else:
                        favorite_actions = user['favorite_action']
                    print(f"       Favorite actions: {favorite_actions}")
                else:
                    print(f"       Favorite actions: None")
            except:
                print(f"       Favorite actions: Error parsing")
            
            # Parse and display annoying actions
            try:
                if user['annoying_action']:
                    if isinstance(user['annoying_action'], str):
                        annoying_actions = json.loads(user['annoying_action'])
                    else:
                        annoying_actions = user['annoying_action']
                    print(f"       Annoying actions: {annoying_actions}")
                else:
                    print(f"       Annoying actions: None")
            except:
                print(f"       Annoying actions: Error parsing")
            print()
        
        # Test interactions based on actual user preferences
        print("2. Testing Interactions Based on User Preferences:")
        
        # Test liked interactions for each user
        for user in users[:3]:  # Test first 3 users
            user_id = user['id']
            print(f"   Testing User {user_id} ({user['name']}):")
            
            # Get their favorite actions
            try:
                if user['favorite_action']:
                    if isinstance(user['favorite_action'], str):
                        favorite_actions = json.loads(user['favorite_action'])
                    else:
                        favorite_actions = user['favorite_action']
                    
                    # Test each favorite action
                    for action in favorite_actions[:2]:  # Test first 2 actions
                        print(f"     Testing liked action: {action}")
                        result = process_interaction_event(user_id, action, 999)  # Use 999 as source
                        if result.get('success'):
                            print(f"       ✅ Success: {result['event']}")
                            print(f"       Changes: X={result['changes']['x_change']}, Y={result['changes']['y_change']}")
                        else:
                            print(f"       ❌ Failed: {result.get('message', 'Unknown error')}")
                else:
                    print(f"     No favorite actions defined")
            except Exception as e:
                print(f"     Error testing favorite actions: {e}")
            
            # Test annoying actions
            try:
                if user['annoying_action']:
                    if isinstance(user['annoying_action'], str):
                        annoying_actions = json.loads(user['annoying_action'])
                    else:
                        annoying_actions = user['annoying_action']
                    
                    # Test first annoying action
                    if annoying_actions:
                        action = annoying_actions[0]
                        print(f"     Testing annoying action: {action}")
                        result = process_interaction_event(user_id, action, 999)
                        if result.get('success'):
                            print(f"       ✅ Success: {result['event']}")
                            print(f"       Changes: X={result['changes']['x_change']}, Y={result['changes']['y_change']}")
                        else:
                            print(f"       ❌ Failed: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"     Error testing annoying actions: {e}")
            print()
        
        # Test friend management
        print("3. Testing Friend Management:")
        if len(users) >= 2:
            user1_id = users[0]['id']
            user2_id = users[1]['id']
            
            print(f"   Adding friendship between User {user1_id} and User {user2_id}:")
            result = add_friend(user1_id, user2_id)
            if result.get('success'):
                print(f"     ✅ Friendship added successfully")
                print(f"     User {user1_id} emotion update: {result['user_emotion_update'].get('success', False)}")
                print(f"     User {user2_id} emotion update: {result['friend_emotion_update'].get('success', False)}")
            else:
                print(f"     ❌ Failed to add friendship: {result.get('error', 'Unknown error')}")
        
        # Show updated database state
        print("\n4. Updated Database State:")
        cursor.execute("""
            SELECT id, name, update_x_value, update_y_value, intimacy_value, friend_count
            FROM emotion 
            ORDER BY id
        """)
        updated_users = cursor.fetchall()
        
        for user in updated_users:
            print(f"   User {user['id']} ({user['name']}):")
            print(f"     X: {user['update_x_value']}, Y: {user['update_y_value']}, Intimacy: {user['intimacy_value']}")
            print(f"     Friends: {user['friend_count']}")
        
        # Show interaction events table
        print("\n5. Interaction Events Table:")
        cursor.execute("""
            SELECT toy_id, target_toy_id, interaction_type, event_name, trigger_time
            FROM toy_interaction_events 
            ORDER BY trigger_time DESC 
            LIMIT 10
        """)
        events = cursor.fetchall()
        
        if events:
            print(f"   Found {len(events)} recent interaction events:")
            for event in events:
                print(f"     {event['toy_id']} -> {event['target_toy_id']} ({event['interaction_type']}) at {event['trigger_time']}")
        else:
            print("   No interaction events found")
        
        # Show friendships table
        print("\n6. Friendships Table:")
        cursor.execute("""
            SELECT toy_id, friend_toy_id, friendship_type, created_at
            FROM toy_friendships 
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
        """)
        friendships = cursor.fetchall()
        
        if friendships:
            print(f"   Found {len(friendships)} active friendships:")
            for friendship in friendships:
                print(f"     User {friendship['toy_id']} <-> User {friendship['friend_toy_id']} ({friendship['friendship_type']})")
        else:
            print("   No active friendships found")
        
        cursor.close()
        
    except mysql.connector.Error as e:
        print(f"     ❌ Database error: {e}")
    finally:
        conn.close()
    
    print("\n=== MySQL Test Complete ===")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Run basic tests")
    print("2. Simulate mobile app data")
    print("3. Run both")
    print("4. Test with MySQL data and update tables")
    
    choice = input("Enter your choice (1, 2, 3, or 4): ").strip()
    
    if choice == "1":
        test_friends_function()
    elif choice == "2":
        simulate_app_data()
    elif choice == "3":
        test_friends_function()
        print("\n" + "="*50 + "\n")
        simulate_app_data()
    elif choice == "4":
        test_with_mysql_data()
    else:
        print("Invalid choice. Running basic tests...")
        test_friends_function()
