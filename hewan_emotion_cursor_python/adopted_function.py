import mysql.connector
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
# 认领事件 (Claim Event)
# Based on the image specification:
# 事件类型: 认领事件 (Claim Event)
# 事件名称: 被认领 (Claimed)
# 触发事件: 该玩具通过手机APP成功添加了好友

ADOPTED_EVENTS = {
    "toy_claimed": {
        "name": "被认领",
        "trigger_condition": "该玩具通过手机APP成功添加了好友",
        "query_params": "查询设备数据表-绑定子账户属性有新增数据",
        "probability": 1.0,  # 100% chance when conditions are met
        "x_change": 2,  # +2
        "y_change_logic": {
            "x_less_than_0": -2,  # x<0时, y-2
            "x_greater_equal_0": 2  # x>=0时, y+2
        },
        "intimacy_change": 1,  # +1 (亲密度)
        "weights": {"lively": 1.5, "clam": 1}  # 性格活泼角色分值权重1.5, 性格平和角色分值权重1
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

def get_user_data(user_id):
    """Get user data from the emotion table."""
    conn = get_database_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, role, update_x_value, update_y_value, intimacy_value FROM emotion WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return user_data
    except mysql.connector.Error as e:
        print(f"Error fetching user data: {e}")
        if conn:
            conn.close()
        return None

def calculate_adopted_emotion_changes(user_data, event_type, current_x):
    """Calculate emotion changes based on adopted event and user data."""
    if event_type not in ADOPTED_EVENTS:
        return 0, 0, 0
    event_config = ADOPTED_EVENTS[event_type]
    x_change = event_config["x_change"]
    intimacy_change = event_config["intimacy_change"]
    if current_x < 0:
        y_change = event_config["y_change_logic"]["x_less_than_0"]
    else:
        y_change = event_config["y_change_logic"]["x_greater_equal_0"]
    role = user_data.get("role", "clam").lower()
    if role not in ["lively", "clam"]:
        role = "clam"
    weight = event_config["weights"][role]
    x_change = int(x_change * weight)
    y_change = int(y_change * weight)
    return x_change, y_change, intimacy_change

def process_adopted_event(user_id):
    """Process adopted event for a user."""
    print(f"=== Processing Adopted Event for User {user_id} ===")
    user_data = get_user_data(user_id)
    if not user_data:
        return {"success": False, "error": "User not found"}
    event_config = ADOPTED_EVENTS["toy_claimed"]
    if random.random() > event_config["probability"]:
        return {"success": False, "message": "Event not triggered due to probability"}
    current_x = user_data.get("update_x_value", 0)
    current_y = user_data.get("update_y_value", 0)
    current_intimacy = user_data.get("intimacy_value", 0)
    x_change, y_change, intimacy_change = calculate_adopted_emotion_changes(user_data, "toy_claimed", current_x)
    print(f"Current X: {current_x}, Y: {current_y}, Intimacy: {current_intimacy}")
    print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
    try:
        update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
        print(f"Successfully updated database for adopted event: {event_config['name']}")
        return {"success": True, "event": event_config["name"], "changes": {"x_change": x_change, "y_change": y_change, "intimacy_change": intimacy_change}}
    except Exception as e:
        return {"success": False, "error": f"Database update failed: {e}"}

if __name__ == "__main__":
    print("Adopted Event Processing System")
    print("Based on Image Requirements: 认领事件 (Claim Event)")
    result = process_adopted_event(1)
    if result.get("success"):
        print(f" Success: {result}")
    else:
        print(f" Failed: {result.get('error', result.get('message', 'Unknown error'))}")
