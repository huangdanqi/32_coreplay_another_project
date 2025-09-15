# weather_function.py
import json
import requests
from datetime import datetime
from db_utils import get_emotion_data
from ip_lookup import get_ip_city
from emotion_database import update_emotion_in_database

# Configuration - Updated to use WeatherAPI.com
WEATHERAPI_API_KEY = "3f7b39a8c1f4404f8f291326252508"  # Replace with your WeatherAPI.com API key
WEATHERAPI_BASE_URL = "http://api.weatherapi.com/v1/current.json"

# Role weights based on the specification table
ROLE_WEIGHTS = {
    "clam": {
        "favorite_weather": 1.0,      # Calm personality weight
        "dislike_weather": 0.5,       # Calm personality weight
        "favorite_season": 1.0,       # Calm personality weight
        "dislike_season": 0.5         # Calm personality weight
    },
    "lively": {
        "favorite_weather": 1.5,      # Lively personality weight
        "dislike_weather": 1.0,       # Lively personality weight
        "favorite_season": 1.5,       # Lively personality weight
        "dislike_season": 1.0         # Lively personality weight
    }
}

def get_weather_data(city_name):
    """
    Fetches current weather data for a given city from WeatherAPI.com.
    Returns weather description (e.g., "Clear", "Cloudy", "Rain") or None on error.
    """
    params = {
        "key": WEATHERAPI_API_KEY,
        "q": city_name,
        "aqi": "no"  # We don't need air quality data for this use case
    }
    try:
        response = requests.get(WEATHERAPI_BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # WeatherAPI.com returns weather condition in data['current']['condition']['text']
        if data and data.get("current") and data["current"].get("condition"):
            return data["current"]["condition"]["text"]
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather for {city_name}: {e}")
        return None

def get_current_season():
    """
    Determines current season based on month.
    Returns: "Spring", "Summer", "Autumn", or "Winter"
    """
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    elif month in [9, 10, 11]:
        return "Autumn"
    else:
        return "Winter"

def calculate_emotion_changes(user_data, current_weather, current_season):
    """
    Calculates emotion changes based on weather and season preferences.
    Returns: (x_change, y_change, intimacy_change)
    """
    role = user_data.get("role", "").lower()
    if role not in ROLE_WEIGHTS:
        print(f"Unknown role: {role}. Using default weights.")
        role = "clam"  # Default to calm
    
    weights = ROLE_WEIGHTS[role]
    
    # Parse JSON arrays for preferences
    try:
        favorite_weathers = json.loads(user_data.get("favorite_weathers", "[]"))
        dislike_weathers = json.loads(user_data.get("dislike_weathers", "[]"))
        favorite_seasons = json.loads(user_data.get("favorite_seasons", "[]"))
        dislike_seasons = json.loads(user_data.get("dislike_seasons", "[]"))
    except json.JSONDecodeError as e:
        print(f"Error parsing preferences for user {user_data.get('id')}: {e}")
        return 0, 0, 0
    
    x_change = 0
    y_change = 0
    intimacy_change = 0
    
    # Weather-based calculations
    if current_weather in favorite_weathers:
        # Favorite weather: +1 happiness, conditional Y-axis change
        x_change += 1
        if x_change < 0:  # If X-axis is negative
            y_change -= 1
        else:  # If X-axis is positive or zero
            y_change += 1
        print(f"User {user_data['id']} (role: {role}) likes weather: {current_weather}")
        
    elif current_weather in dislike_weathers:
        # Dislike weather: -1 happiness, conditional Y-axis change
        x_change -= 1
        if x_change < 0:  # If X-axis is negative
            y_change += 1
        else:  # If X-axis is positive or zero
            y_change -= 1
        print(f"User {user_data['id']} (role: {role}) dislikes weather: {current_weather}")
    
    # Season-based calculations
    if current_season in favorite_seasons:
        # Favorite season: +1 happiness, conditional Y-axis change
        x_change += 1
        if x_change < 0:  # If X-axis is negative
            y_change -= 1
        else:  # If X-axis is positive or zero
            y_change += 1
        print(f"User {user_data['id']} (role: {role}) likes season: {current_season}")
        
    elif current_season in dislike_seasons:
        # Dislike season: -1 happiness, conditional Y-axis change
        x_change -= 1
        if x_change < 0:  # If X-axis is negative
            y_change += 1
        else:  # If X-axis is positive or zero
            y_change -= 1
        print(f"User {user_data['id']} (role: {role}) dislikes season: {current_season}")
    
    # Apply role-specific weights
    if current_weather in favorite_weathers or current_weather in dislike_weathers:
        weight = weights["favorite_weather"] if current_weather in favorite_weathers else weights["dislike_weather"]
        x_change = int(x_change * weight)
        y_change = int(y_change * weight)
    
    if current_season in favorite_seasons or current_season in dislike_seasons:
        weight = weights["favorite_season"] if current_season in favorite_seasons else weights["dislike_season"]
        x_change = int(x_change * weight)
        y_change = int(y_change * weight)
    
    # Intimacy remains 0 for weather/season events (as per specification)
    intimacy_change = 0
    
    return x_change, y_change, intimacy_change



def process_weather_event(user_id, user_ip_address):
    """
    Main function to process weather events for a given user.
    """
    print(f"\n=== Processing weather event for user ID: {user_id}, IP: {user_ip_address} ===")
    
    # 1. Get user data from database
    all_emotion_data = get_emotion_data()
    user_data = next((item for item in all_emotion_data if item["id"] == user_id), None)
    
    if not user_data:
        print(f"User with ID {user_id} not found in the database.")
        return
    
    print(f"Found user: {user_data['name']} (role: {user_data['role']})")
    
    # 2. Get city from IP address
    city = get_ip_city(user_ip_address)
    if city == "Unknown" or city.startswith("Error"):
        print(f"Could not determine city for IP {user_ip_address}. Skipping weather processing.")
        return
    
    print(f"Determined city: {city}")
    
    # 3. Get current weather and season
    current_weather = get_weather_data(city)
    current_season = get_current_season()
    
    if not current_weather:
        print(f"Could not get current weather for {city}. Skipping emotion calculation.")
        return
    
    print(f"Current weather: {current_weather}, Current season: {current_season}")
    
    # 4. Calculate emotion changes
    x_change, y_change, intimacy_change = calculate_emotion_changes(user_data, current_weather, current_season)
    
    print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
    
    # 5. Update database
    if x_change != 0 or y_change != 0 or intimacy_change != 0:
        update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
    else:
        print("No changes to apply.")

if __name__ == "__main__":
    # Example usage
    print("Weather Function Demo")
    print("===================")
    
    # Example for user 1 (clam)
    process_weather_event(user_id=1, user_ip_address="8.8.8.8")
    
    # Example for user 2 (lively)
    process_weather_event(user_id=2, user_ip_address="203.0.113.45")