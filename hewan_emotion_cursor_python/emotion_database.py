# emotion_database.py
import mysql.connector

def update_emotion_in_database(user_id, x_change, y_change, intimacy_change):
    """
    Updates the emotion values in the MySQL database.
    
    :param user_id: User ID to update
    :param x_change: Change in X value
    :param y_change: Change in Y value
    :param intimacy_change: Change in intimacy value
    """
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="h05010501",
            database="page_test"
        )
        
        cursor = conn.cursor()
        
        # Get current values
        cursor.execute("SELECT update_x_value, update_y_value, intimacy_value FROM emotion WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result:
            current_x, current_y, current_intimacy = result
            
            # Calculate new values
            new_x = current_x + x_change
            new_y = current_y + y_change
            new_intimacy = current_intimacy + intimacy_change
            
            # Ensure values stay within bounds (-30 to +30)
            new_x = max(-30, min(30, new_x))
            new_y = max(-30, min(30, new_y))
            
            # Update database
            cursor.execute("""
                UPDATE emotion 
                SET update_x_value = %s, update_y_value = %s, intimacy_value = %s 
                WHERE id = %s
            """, (new_x, new_y, new_intimacy, user_id))
            
            conn.commit()
            print(f"Updated user {user_id}: X={new_x}, Y={new_y}, Intimacy={new_intimacy}")
            
        else:
            print(f"User {user_id} not found in database")
            
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    # Example usage
    print("Emotion Database Update Function")
    print("===============================")
    
    # Example: Update user 1 with some changes
    print("Example: Updating user 1 with X=+1, Y=-1, Intimacy=0")
    update_emotion_in_database(user_id=1, x_change=1, y_change=-1, intimacy_change=0)
