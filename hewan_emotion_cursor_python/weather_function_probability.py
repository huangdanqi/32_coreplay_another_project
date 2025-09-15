import random
from weather_function import get_emotion_data, get_ip_city, get_weather_data, get_current_season, calculate_emotion_changes, update_emotion_in_database
import json

def run_with_probability(func, probability, *args, **kwargs):
    """
    Runs `func` with a given probability.

    :param func: Function to run
    :param probability: Probability to run the function (0.0 - 1.0)
    :param args: Positional arguments to pass to func
    :param kwargs: Keyword arguments to pass to func
    :return: The result of func if run, else None
    """
    if random.random() < probability:
        return func(*args, **kwargs)
    else:
        print("Function not executed due to probability check.")
        return None

def favorite_weather_event(user_id, user_ip_address):
    """
    Process favorite weather event with 30% probability (0.3)
    """
    print(f"\n=== Favorite Weather Event for User {user_id} ===")
    
    # Get user data and weather info
    all_emotion_data = get_emotion_data()
    user_data = next((item for item in all_emotion_data if item["id"] == user_id), None)
    
    if not user_data:
        print(f"User with ID {user_id} not found in the database.")
        return None
    
    city = get_ip_city(user_ip_address)
    if city == "Unknown" or city.startswith("Error"):
        print(f"Could not determine city for IP {user_ip_address}.")
        return None
    
    current_weather = get_weather_data(city)
    if not current_weather:
        print(f"Could not get current weather for {city}.")
        return None
    
    # Parse user preferences
    try:
        favorite_weathers = json.loads(user_data.get("favorite_weathers", "[]"))
    except json.JSONDecodeError as e:
        print(f"Error parsing favorite weathers: {e}")
        return None
    
    # Check if current weather is in favorite weathers
    if current_weather in favorite_weathers:
        print(f"✓ Current weather '{current_weather}' is in user's favorite weathers!")
        
        # Calculate emotion changes
        current_season = get_current_season()
        x_change, y_change, intimacy_change = calculate_emotion_changes(user_data, current_weather, current_season)
        
        print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
        
        # Apply probability check before updating database
        probability = 0.3  # 30% chance for favorite weather
        print(f"Checking probability: {probability} ({probability*100}% chance)")
        
        if random.random() < probability:
            print("✓ Probability check passed! Updating database...")
            update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
            return {"event": "favorite_weather", "triggered": True, "weather": current_weather}
        else:
            print("✗ Probability check failed. Database not updated.")
            return {"event": "favorite_weather", "triggered": False, "weather": current_weather}
    else:
        print(f"Current weather '{current_weather}' is not in user's favorite weathers.")
        return None

def disliked_weather_event(user_id, user_ip_address):
    """
    Process disliked weather event with 60% probability (0.6)
    """
    print(f"\n=== Disliked Weather Event for User {user_id} ===")
    
    # Get user data and weather info
    all_emotion_data = get_emotion_data()
    user_data = next((item for item in all_emotion_data if item["id"] == user_id), None)
    
    if not user_data:
        print(f"User with ID {user_id} not found in the database.")
        return None
    
    city = get_ip_city(user_ip_address)
    if city == "Unknown" or city.startswith("Error"):
        print(f"Could not determine city for IP {user_ip_address}.")
        return None
    
    current_weather = get_weather_data(city)
    if not current_weather:
        print(f"Could not get current weather for {city}.")
        return None
    
    # Parse user preferences
    try:
        dislike_weathers = json.loads(user_data.get("dislike_weathers", "[]"))
    except json.JSONDecodeError as e:
        print(f"Error parsing dislike weathers: {e}")
        return None
    
    # Check if current weather is in dislike weathers
    if current_weather in dislike_weathers:
        print(f"✓ Current weather '{current_weather}' is in user's disliked weathers!")
        
        # Calculate emotion changes
        current_season = get_current_season()
        x_change, y_change, intimacy_change = calculate_emotion_changes(user_data, current_weather, current_season)
        
        print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
        
        # Apply probability check before updating database
        probability = 0.6  # 60% chance for disliked weather
        print(f"Checking probability: {probability} ({probability*100}% chance)")
        
        if random.random() < probability:
            print("✓ Probability check passed! Updating database...")
            update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
            return {"event": "disliked_weather", "triggered": True, "weather": current_weather}
        else:
            print("✗ Probability check failed. Database not updated.")
            return {"event": "disliked_weather", "triggered": False, "weather": current_weather}
    else:
        print(f"Current weather '{current_weather}' is not in user's disliked weathers.")
        return None

def favorite_season_event(user_id, user_ip_address):
    """
    Process favorite season event with 10% probability (0.1)
    """
    print(f"\n=== Favorite Season Event for User {user_id} ===")
    
    # Get user data and season info
    all_emotion_data = get_emotion_data()
    user_data = next((item for item in all_emotion_data if item["id"] == user_id), None)
    
    if not user_data:
        print(f"User with ID {user_id} not found in the database.")
        return None
    
    current_season = get_current_season()
    
    # Parse user preferences
    try:
        favorite_seasons = json.loads(user_data.get("favorite_seasons", "[]"))
    except json.JSONDecodeError as e:
        print(f"Error parsing favorite seasons: {e}")
        return None
    
    # Check if current season is in favorite seasons
    if current_season in favorite_seasons:
        print(f"✓ Current season '{current_season}' is in user's favorite seasons!")
        
        # Calculate emotion changes (need weather for calculation)
        city = get_ip_city(user_ip_address)
        if city == "Unknown" or city.startswith("Error"):
            print(f"Could not determine city for IP {user_ip_address}.")
            return None
        
        current_weather = get_weather_data(city)
        if not current_weather:
            print(f"Could not get current weather for {city}.")
            return None
        
        x_change, y_change, intimacy_change = calculate_emotion_changes(user_data, current_weather, current_season)
        
        print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
        
        # Apply probability check before updating database
        probability = 0.1  # 10% chance for favorite season
        print(f"Checking probability: {probability} ({probability*100}% chance)")
        
        if random.random() < probability:
            print("✓ Probability check passed! Updating database...")
            update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
            return {"event": "favorite_season", "triggered": True, "season": current_season}
        else:
            print("✗ Probability check failed. Database not updated.")
            return {"event": "favorite_season", "triggered": False, "season": current_season}
    else:
        print(f"Current season '{current_season}' is not in user's favorite seasons.")
        return None

def disliked_season_event(user_id, user_ip_address):
    """
    Process disliked season event with 10% probability (0.1)
    """
    print(f"\n=== Disliked Season Event for User {user_id} ===")
    
    # Get user data and season info
    all_emotion_data = get_emotion_data()
    user_data = next((item for item in all_emotion_data if item["id"] == user_id), None)
    
    if not user_data:
        print(f"User with ID {user_id} not found in the database.")
        return None
    
    current_season = get_current_season()
    
    # Parse user preferences
    try:
        dislike_seasons = json.loads(user_data.get("dislike_seasons", "[]"))
    except json.JSONDecodeError as e:
        print(f"Error parsing dislike seasons: {e}")
        return None
    
    # Check if current season is in dislike seasons
    if current_season in dislike_seasons:
        print(f"✓ Current season '{current_season}' is in user's disliked seasons!")
        
        # Calculate emotion changes (need weather for calculation)
        city = get_ip_city(user_ip_address)
        if city == "Unknown" or city.startswith("Error"):
            print(f"Could not determine city for IP {user_ip_address}.")
            return None
        
        current_weather = get_weather_data(city)
        if not current_weather:
            print(f"Could not get current weather for {city}.")
            return None
        
        x_change, y_change, intimacy_change = calculate_emotion_changes(user_data, current_weather, current_season)
        
        print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
        
        # Apply probability check before updating database
        probability = 0.1  # 10% chance for disliked season
        print(f"Checking probability: {probability} ({probability*100}% chance)")
        
        if random.random() < probability:
            print("✓ Probability check passed! Updating database...")
            update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
            return {"event": "disliked_season", "triggered": True, "season": current_season}
        else:
            print("✗ Probability check failed. Database not updated.")
            return {"event": "disliked_season", "triggered": False, "season": current_season}
    else:
        print(f"Current season '{current_season}' is not in user's disliked seasons.")
        return None

def process_all_weather_events(user_id, user_ip_address):
    """
    Process all weather and season events for a user
    """
    print(f"\n{'='*50}")
    print(f"Processing all weather events for User {user_id}")
    print(f"{'='*50}")
    
    results = []
    
    # Check favorite weather
    result = favorite_weather_event(user_id, user_ip_address)
    if result:
        results.append(result)
    
    # Check disliked weather
    result = disliked_weather_event(user_id, user_ip_address)
    if result:
        results.append(result)
    
    # Check favorite season
    result = favorite_season_event(user_id, user_ip_address)
    if result:
        results.append(result)
    
    # Check disliked season
    result = disliked_season_event(user_id, user_ip_address)
    if result:
        results.append(result)
    
    print(f"\n=== Summary ===")
    print(f"Total events processed: {len(results)}")
    triggered_events = [r for r in results if r.get('triggered', False)]
    print(f"Events triggered: {len(triggered_events)}")
    
    return results

# Example usage:
if __name__ == "__main__":
    print("Weather Probability System Demo")
    print("==============================")
    
    # Test individual events
    print("\n1. Testing Favorite Weather Event:")
    favorite_weather_event(user_id=1, user_ip_address="8.8.8.8")
    
    print("\n2. Testing Disliked Weather Event:")
    disliked_weather_event(user_id=1, user_ip_address="8.8.8.8")
    
    print("\n3. Testing Favorite Season Event:")
    favorite_season_event(user_id=1, user_ip_address="8.8.8.8")
    
    print("\n4. Testing Disliked Season Event:")
    disliked_season_event(user_id=1, user_ip_address="8.8.8.8")
    
    print("\n5. Testing All Events:")
    results = process_all_weather_events(user_id=1, user_ip_address="8.8.8.8")
    print(f"Final results: {results}")