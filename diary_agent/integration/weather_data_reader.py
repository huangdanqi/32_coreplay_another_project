"""
Weather data reader for integrating with existing weather_function.py module.
Provides read-only access to weather event data for diary generation context.
"""

import json
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

try:
    from weather_function import get_weather_data, get_current_season, calculate_emotion_changes
    from db_utils import get_emotion_data
    from ip_lookup import get_ip_city
except ImportError as e:
    print(f"Warning: Could not import weather functions: {e}")
    # Define fallback functions for testing
    def get_weather_data(city_name): return "Clear"
    def get_current_season(): return "Spring"
    def calculate_emotion_changes(user_data, weather, season): return (0, 0, 0)
    def get_emotion_data(): return []
    def get_ip_city(ip): return "Unknown"

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader


class WeatherDataReader(DataReader):
    """
    Data reader for weather events that interfaces with existing weather_function.py.
    Provides read-only access to weather data for diary generation context.
    """
    
    def __init__(self):
        super().__init__(module_name="weather_function", read_only=True)
        self.supported_events = [
            "favorite_weather", "dislike_weather", 
            "favorite_season", "dislike_season"
        ]
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read weather event context from existing weather_function.py module.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            DiaryContextData with weather context for diary generation
        """
        try:
            # Get user data from emotion database
            user_profile = self.get_user_preferences(event_data.user_id)
            if not user_profile:
                return self._create_minimal_context(event_data)
            
            # Get user IP from metadata or use default
            user_ip = event_data.metadata.get("user_ip", "8.8.8.8")
            
            # Get city from IP
            city = get_ip_city(user_ip)
            if city == "Unknown" or city.startswith("Error"):
                city = "Beijing"  # Default city
            
            # Get current weather and season
            current_weather = get_weather_data(city)
            current_season = get_current_season()
            
            # Calculate emotion changes (for context, not for database update)
            x_change, y_change, intimacy_change = calculate_emotion_changes(
                user_profile, current_weather, current_season
            )
            
            # Determine event context based on event name
            event_details = self._analyze_weather_event(
                event_data.event_name, user_profile, current_weather, current_season
            )
            
            # Build environmental context
            environmental_context = {
                "city": city,
                "current_weather": current_weather,
                "current_season": current_season,
                "weather_description": self._get_weather_description(current_weather),
                "season_description": self._get_season_description(current_season),
                "emotion_impact": {
                    "x_change": x_change,
                    "y_change": y_change,
                    "intimacy_change": intimacy_change
                }
            }
            
            # Build emotional context
            emotional_context = {
                "weather_preference_match": self._check_weather_preference(
                    event_data.event_name, current_weather, user_profile
                ),
                "season_preference_match": self._check_season_preference(
                    event_data.event_name, current_season, user_profile
                ),
                "emotional_intensity": self._calculate_emotional_intensity(
                    user_profile.get("role", "clam"), event_data.event_name
                )
            }
            
            # Build temporal context
            temporal_context = {
                "timestamp": event_data.timestamp,
                "time_of_day": self._get_time_of_day(event_data.timestamp),
                "month": event_data.timestamp.month,
                "season": current_season
            }
            
            return DiaryContextData(
                user_profile=user_profile,
                event_details=event_details,
                environmental_context=environmental_context,
                social_context={},  # Weather events don't have social context
                emotional_context=emotional_context,
                temporal_context=temporal_context
            )
            
        except Exception as e:
            print(f"Error reading weather event context: {e}")
            return self._create_minimal_context(event_data)
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from emotion database.
        
        Args:
            user_id: User ID to get preferences for
            
        Returns:
            User profile dictionary or None if not found
        """
        try:
            all_emotion_data = get_emotion_data()
            user_data = next((item for item in all_emotion_data if item["id"] == user_id), None)
            return user_data
        except Exception as e:
            print(f"Error getting user preferences for user {user_id}: {e}")
            return None
    
    def _create_minimal_context(self, event_data: EventData) -> DiaryContextData:
        """Create minimal context when data reading fails."""
        return DiaryContextData(
            user_profile={"id": event_data.user_id, "role": "clam"},
            event_details={"event_name": event_data.event_name, "event_type": "weather"},
            environmental_context={"current_weather": "Clear", "current_season": "Spring"},
            social_context={},
            emotional_context={"preference_match": False},
            temporal_context={"timestamp": event_data.timestamp}
        )
    
    def _analyze_weather_event(self, event_name: str, user_profile: Dict[str, Any], 
                              current_weather: str, current_season: str) -> Dict[str, Any]:
        """
        Analyze weather event to determine context details.
        
        Args:
            event_name: Name of the weather event
            user_profile: User profile data
            current_weather: Current weather condition
            current_season: Current season
            
        Returns:
            Event details dictionary
        """
        event_details = {
            "event_name": event_name,
            "event_type": "weather" if "weather" in event_name else "season",
            "current_condition": current_weather if "weather" in event_name else current_season,
            "user_role": user_profile.get("role", "clam")
        }
        
        # Parse user preferences
        try:
            if "weather" in event_name:
                favorite_weathers = json.loads(user_profile.get("favorite_weathers", "[]"))
                dislike_weathers = json.loads(user_profile.get("dislike_weathers", "[]"))
                event_details["user_preferences"] = {
                    "favorites": favorite_weathers,
                    "dislikes": dislike_weathers
                }
                event_details["preference_match"] = (
                    current_weather in favorite_weathers if "favorite" in event_name 
                    else current_weather in dislike_weathers
                )
            else:  # season event
                favorite_seasons = json.loads(user_profile.get("favorite_seasons", "[]"))
                dislike_seasons = json.loads(user_profile.get("dislike_seasons", "[]"))
                event_details["user_preferences"] = {
                    "favorites": favorite_seasons,
                    "dislikes": dislike_seasons
                }
                event_details["preference_match"] = (
                    current_season in favorite_seasons if "favorite" in event_name 
                    else current_season in dislike_seasons
                )
        except (json.JSONDecodeError, KeyError):
            event_details["user_preferences"] = {"favorites": [], "dislikes": []}
            event_details["preference_match"] = False
        
        return event_details
    
    def _check_weather_preference(self, event_name: str, current_weather: str, 
                                 user_profile: Dict[str, Any]) -> bool:
        """Check if current weather matches user preference for the event."""
        if "weather" not in event_name:
            return False
        
        try:
            if "favorite" in event_name:
                favorite_weathers = json.loads(user_profile.get("favorite_weathers", "[]"))
                return current_weather in favorite_weathers
            elif "dislike" in event_name:
                dislike_weathers = json.loads(user_profile.get("dislike_weathers", "[]"))
                return current_weather in dislike_weathers
        except (json.JSONDecodeError, KeyError):
            pass
        
        return False
    
    def _check_season_preference(self, event_name: str, current_season: str, 
                                user_profile: Dict[str, Any]) -> bool:
        """Check if current season matches user preference for the event."""
        if "season" not in event_name:
            return False
        
        try:
            if "favorite" in event_name:
                favorite_seasons = json.loads(user_profile.get("favorite_seasons", "[]"))
                return current_season in favorite_seasons
            elif "dislike" in event_name:
                dislike_seasons = json.loads(user_profile.get("dislike_seasons", "[]"))
                return current_season in dislike_seasons
        except (json.JSONDecodeError, KeyError):
            pass
        
        return False
    
    def _calculate_emotional_intensity(self, role: str, event_name: str) -> float:
        """Calculate emotional intensity based on role and event type."""
        # Role weights from weather_function.py
        role_weights = {
            "clam": {"favorite": 1.0, "dislike": 0.5},
            "lively": {"favorite": 1.5, "dislike": 1.0}
        }
        
        role = role.lower()
        if role not in role_weights:
            role = "clam"
        
        if "favorite" in event_name:
            return role_weights[role]["favorite"]
        elif "dislike" in event_name:
            return role_weights[role]["dislike"]
        else:
            return 1.0
    
    def _get_weather_description(self, weather: str) -> str:
        """Get descriptive text for weather condition."""
        weather_descriptions = {
            "Clear": "晴朗的天空",
            "Sunny": "阳光明媚",
            "Cloudy": "多云天气",
            "Overcast": "阴天",
            "Rain": "下雨天",
            "Storm": "暴风雨",
            "Snow": "下雪天",
            "Fog": "雾天"
        }
        return weather_descriptions.get(weather, f"{weather}天气")
    
    def _get_season_description(self, season: str) -> str:
        """Get descriptive text for season."""
        season_descriptions = {
            "Spring": "春暖花开的季节",
            "Summer": "炎热的夏日",
            "Autumn": "秋高气爽的时节", 
            "Winter": "寒冷的冬天"
        }
        return season_descriptions.get(season, f"{season}季节")
    
    def _get_time_of_day(self, timestamp: datetime) -> str:
        """Get time of day description."""
        hour = timestamp.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def get_supported_events(self) -> list:
        """Get list of supported weather events."""
        return self.supported_events.copy()