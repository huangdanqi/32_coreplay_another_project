"""
Holiday data reader for integrating with existing holiday_function.py module.
Provides read-only access to holiday event data for diary generation context.
"""

import json
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

try:
    from holiday_function import (
        get_chinese_holidays, get_holiday_event_type, is_holiday_period,
        calculate_holiday_emotion_changes, HOLIDAY_EVENTS, MAJOR_CHINESE_HOLIDAYS
    )
    from db_utils import get_emotion_data
except ImportError as e:
    print(f"Warning: Could not import holiday_function functions: {e}")
    # Define fallback functions for testing
    def get_chinese_holidays(year=None): return []
    def get_holiday_event_type(date, holidays): return None
    def is_holiday_period(date, holidays): return None
    def calculate_holiday_emotion_changes(user_data, event_type, current_x): return (0, 0, 0)
    def get_emotion_data(): return []
    HOLIDAY_EVENTS = {}
    MAJOR_CHINESE_HOLIDAYS = {}

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader


class HolidayDataReader(DataReader):
    """
    Data reader for holiday events that interfaces with existing holiday_function.py.
    Provides read-only access to holiday data for diary generation context.
    """
    
    def __init__(self):
        super().__init__(module_name="holiday_function", read_only=True)
        self.supported_events = ["approaching_holiday", "during_holiday", "holiday_ends"]
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read holiday event context from existing holiday_function.py module.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            DiaryContextData with holiday context for diary generation
        """
        try:
            # Get user data from emotion database
            user_profile = self.get_user_preferences(event_data.user_id)
            if not user_profile:
                return self._create_minimal_context(event_data)
            
            # Get date from event data or use current date
            event_date = event_data.metadata.get("event_date", event_data.timestamp)
            if isinstance(event_date, str):
                event_date = datetime.strptime(event_date, "%Y-%m-%d")
            
            # Get Chinese holidays for the year
            holidays = get_chinese_holidays(event_date.year)
            
            # Determine holiday event type and related holiday
            holiday_event_type = get_holiday_event_type(event_date, holidays)
            related_holiday = self._find_related_holiday(event_date, holidays, holiday_event_type)
            
            # Analyze event details
            event_details = self._analyze_holiday_event(
                event_data.event_name, holiday_event_type, related_holiday, user_profile, event_date
            )
            
            # Build temporal context with holiday information
            temporal_context = {
                "timestamp": event_data.timestamp,
                "event_date": event_date,
                "holiday_year": event_date.year,
                "related_holiday": related_holiday,
                "holiday_timing": self._analyze_holiday_timing(event_date, related_holiday),
                "days_to_holiday": self._calculate_days_to_holiday(event_date, related_holiday),
                "holiday_season": self._get_holiday_season(related_holiday),
                "time_of_day": self._get_time_of_day(event_data.timestamp)
            }
            
            # Build social context (holiday social aspects)
            social_context = {
                "holiday_type": self._classify_holiday_type(related_holiday),
                "cultural_significance": self._get_cultural_significance(related_holiday),
                "typical_activities": self._get_typical_holiday_activities(related_holiday),
                "social_expectations": self._get_social_expectations(event_data.event_name, related_holiday),
                "family_context": self._analyze_family_context(event_data.event_name)
            }
            
            # Build emotional context
            emotional_context = {
                "holiday_emotional_tone": self._determine_holiday_emotional_tone(event_data.event_name),
                "anticipation_level": self._calculate_anticipation_level(event_data.event_name, related_holiday),
                "emotional_intensity": self._calculate_emotional_intensity(
                    user_profile.get("role", "clam"), event_data.event_name
                ),
                "holiday_stress_level": self._assess_holiday_stress(event_data.event_name, related_holiday)
            }
            
            # Build environmental context (holiday environment)
            environmental_context = {
                "holiday_atmosphere": self._describe_holiday_atmosphere(event_data.event_name, related_holiday),
                "seasonal_context": self._get_seasonal_context(event_date),
                "cultural_environment": "chinese_traditional",
                "celebration_scale": self._assess_celebration_scale(related_holiday)
            }
            
            return DiaryContextData(
                user_profile=user_profile,
                event_details=event_details,
                environmental_context=environmental_context,
                social_context=social_context,
                emotional_context=emotional_context,
                temporal_context=temporal_context
            )
            
        except Exception as e:
            print(f"Error reading holiday event context: {e}")
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
            event_details={"event_name": event_data.event_name, "event_type": "holiday"},
            environmental_context={"holiday_atmosphere": "festive"},
            social_context={"holiday_type": "traditional"},
            emotional_context={"holiday_emotional_tone": "positive"},
            temporal_context={"timestamp": event_data.timestamp}
        )
    
    def _analyze_holiday_event(self, event_name: str, holiday_event_type: Optional[str], 
                              related_holiday: Optional[Dict[str, Any]], user_profile: Dict[str, Any],
                              event_date: datetime) -> Dict[str, Any]:
        """
        Analyze holiday event to determine context details.
        
        Args:
            event_name: Name of the holiday event
            holiday_event_type: Type detected by holiday_function
            related_holiday: Related holiday information
            user_profile: User profile data
            event_date: Date of the event
            
        Returns:
            Event details dictionary
        """
        event_details = {
            "event_name": event_name,
            "event_type": "holiday",
            "holiday_event_type": holiday_event_type,
            "user_role": user_profile.get("role", "clam"),
            "event_date": event_date.strftime("%Y-%m-%d")
        }
        
        if related_holiday:
            event_details.update({
                "holiday_name": related_holiday.get("name", "Unknown"),
                "holiday_date": related_holiday.get("date", "Unknown"),
                "holiday_duration": related_holiday.get("duration", 1),
                "is_major_holiday": self._is_major_holiday(related_holiday)
            })
            
            # Calculate emotion changes for context (not for database update)
            if holiday_event_type and holiday_event_type in HOLIDAY_EVENTS:
                current_x = user_profile.get("update_x_value", 0)
                x_change, y_change, intimacy_change = calculate_holiday_emotion_changes(
                    user_profile, holiday_event_type, current_x
                )
                event_details["emotion_impact"] = {
                    "x_change": x_change,
                    "y_change": y_change,
                    "intimacy_change": intimacy_change
                }
        else:
            event_details.update({
                "holiday_name": "Unknown",
                "holiday_date": "Unknown",
                "holiday_duration": 1,
                "is_major_holiday": False,
                "emotion_impact": {"x_change": 0, "y_change": 0, "intimacy_change": 0}
            })
        
        return event_details
    
    def _find_related_holiday(self, event_date: datetime, holidays: List[Dict], 
                             holiday_event_type: Optional[str]) -> Optional[Dict[str, Any]]:
        """Find the holiday related to the current event."""
        if not holiday_event_type or not holidays:
            return None
        
        # Check if currently in holiday period
        current_holiday = is_holiday_period(event_date, holidays)
        if current_holiday and holiday_event_type == "during_holiday":
            return current_holiday
        
        # Find closest holiday for approaching/ending events
        closest_holiday = None
        min_distance = float('inf')
        
        for holiday in holidays:
            try:
                holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
                distance = abs((holiday_date - event_date).days)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_holiday = holiday
            except (ValueError, KeyError):
                continue
        
        return closest_holiday
    
    def _analyze_holiday_timing(self, event_date: datetime, related_holiday: Optional[Dict]) -> str:
        """Analyze timing relative to holiday."""
        if not related_holiday:
            return "no_holiday"
        
        try:
            holiday_date = datetime.strptime(related_holiday["date"], "%Y-%m-%d")
            days_diff = (holiday_date - event_date).days
            
            if days_diff > 0:
                return f"before_holiday_{days_diff}_days"
            elif days_diff == 0:
                return "on_holiday"
            else:
                return f"after_holiday_{abs(days_diff)}_days"
        except (ValueError, KeyError):
            return "unknown_timing"
    
    def _calculate_days_to_holiday(self, event_date: datetime, related_holiday: Optional[Dict]) -> int:
        """Calculate days until/since holiday."""
        if not related_holiday:
            return 0
        
        try:
            holiday_date = datetime.strptime(related_holiday["date"], "%Y-%m-%d")
            return (holiday_date - event_date).days
        except (ValueError, KeyError):
            return 0
    
    def _get_holiday_season(self, related_holiday: Optional[Dict]) -> str:
        """Get season associated with holiday."""
        if not related_holiday:
            return "unknown"
        
        holiday_name = related_holiday.get("name", "").lower()
        
        if "春节" in holiday_name or "新年" in holiday_name:
            return "winter_spring"
        elif "清明" in holiday_name:
            return "spring"
        elif "劳动" in holiday_name or "端午" in holiday_name:
            return "spring_summer"
        elif "中秋" in holiday_name:
            return "autumn"
        elif "国庆" in holiday_name:
            return "autumn"
        else:
            return "unknown"
    
    def _classify_holiday_type(self, related_holiday: Optional[Dict]) -> str:
        """Classify type of holiday."""
        if not related_holiday:
            return "unknown"
        
        holiday_name = related_holiday.get("name", "").lower()
        
        if "春节" in holiday_name:
            return "traditional_major"
        elif "国庆" in holiday_name:
            return "national_major"
        elif "劳动" in holiday_name:
            return "international"
        elif any(name in holiday_name for name in ["清明", "端午", "中秋"]):
            return "traditional_cultural"
        else:
            return "general"
    
    def _get_cultural_significance(self, related_holiday: Optional[Dict]) -> str:
        """Get cultural significance of holiday."""
        if not related_holiday:
            return "low"
        
        holiday_name = related_holiday.get("name", "").lower()
        
        if "春节" in holiday_name:
            return "highest"
        elif "国庆" in holiday_name:
            return "very_high"
        elif any(name in holiday_name for name in ["清明", "端午", "中秋"]):
            return "high"
        else:
            return "moderate"
    
    def _get_typical_holiday_activities(self, related_holiday: Optional[Dict]) -> List[str]:
        """Get typical activities for the holiday."""
        if not related_holiday:
            return ["休息"]
        
        holiday_name = related_holiday.get("name", "").lower()
        
        activities_map = {
            "春节": ["团圆", "拜年", "放鞭炮", "吃年夜饭"],
            "清明": ["扫墓", "踏青", "祭祖"],
            "劳动": ["休息", "旅游", "聚会"],
            "端午": ["吃粽子", "赛龙舟", "挂艾草"],
            "中秋": ["赏月", "吃月饼", "团圆"],
            "国庆": ["旅游", "庆祝", "休息", "看阅兵"]
        }
        
        for key, activities in activities_map.items():
            if key in holiday_name:
                return activities
        
        return ["休息", "庆祝"]
    
    def _get_social_expectations(self, event_name: str, related_holiday: Optional[Dict]) -> str:
        """Get social expectations for the holiday event."""
        if event_name == "approaching_holiday":
            return "preparation_excitement"
        elif event_name == "during_holiday":
            return "celebration_joy"
        elif event_name == "holiday_ends":
            return "return_to_routine"
        else:
            return "neutral"
    
    def _analyze_family_context(self, event_name: str) -> str:
        """Analyze family context for holiday event."""
        if event_name == "approaching_holiday":
            return "anticipation_planning"
        elif event_name == "during_holiday":
            return "family_gathering"
        elif event_name == "holiday_ends":
            return "separation_nostalgia"
        else:
            return "normal"
    
    def _determine_holiday_emotional_tone(self, event_name: str) -> str:
        """Determine emotional tone of holiday event."""
        tone_mapping = {
            "approaching_holiday": "anticipation_excitement",
            "during_holiday": "joy_celebration",
            "holiday_ends": "nostalgia_sadness"
        }
        return tone_mapping.get(event_name, "neutral")
    
    def _calculate_anticipation_level(self, event_name: str, related_holiday: Optional[Dict]) -> str:
        """Calculate anticipation level for holiday."""
        if event_name == "approaching_holiday":
            if related_holiday and "春节" in related_holiday.get("name", ""):
                return "very_high"
            else:
                return "high"
        elif event_name == "during_holiday":
            return "fulfilled"
        elif event_name == "holiday_ends":
            return "diminishing"
        else:
            return "low"
    
    def _calculate_emotional_intensity(self, role: str, event_name: str) -> float:
        """Calculate emotional intensity based on role and event type."""
        if event_name not in HOLIDAY_EVENTS:
            return 1.0
        
        role = role.lower()
        if role not in ["lively", "clam"]:
            role = "clam"
        
        return HOLIDAY_EVENTS[event_name]["weights"][role]
    
    def _assess_holiday_stress(self, event_name: str, related_holiday: Optional[Dict]) -> str:
        """Assess stress level associated with holiday event."""
        if event_name == "approaching_holiday":
            if related_holiday and "春节" in related_holiday.get("name", ""):
                return "moderate"  # Preparation stress
            else:
                return "low"
        elif event_name == "during_holiday":
            return "low"  # Enjoying holiday
        elif event_name == "holiday_ends":
            return "moderate"  # Back to work stress
        else:
            return "low"
    
    def _describe_holiday_atmosphere(self, event_name: str, related_holiday: Optional[Dict]) -> str:
        """Describe the atmosphere of holiday event."""
        if event_name == "approaching_holiday":
            return "anticipatory_festive"
        elif event_name == "during_holiday":
            return "celebratory_joyful"
        elif event_name == "holiday_ends":
            return "nostalgic_transitional"
        else:
            return "neutral"
    
    def _get_seasonal_context(self, event_date: datetime) -> str:
        """Get seasonal context for the event date."""
        month = event_date.month
        
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _assess_celebration_scale(self, related_holiday: Optional[Dict]) -> str:
        """Assess the scale of celebration for the holiday."""
        if not related_holiday:
            return "small"
        
        holiday_name = related_holiday.get("name", "").lower()
        duration = related_holiday.get("duration", 1)
        
        if "春节" in holiday_name or duration >= 7:
            return "national_major"
        elif "国庆" in holiday_name or duration >= 3:
            return "national_moderate"
        else:
            return "regional_small"
    
    def _is_major_holiday(self, holiday: Dict[str, Any]) -> bool:
        """Check if holiday is a major holiday."""
        holiday_name = holiday.get("name", "").lower()
        duration = holiday.get("duration", 1)
        
        return ("春节" in holiday_name or "国庆" in holiday_name or duration >= 3)
    
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
    
    def get_supported_events(self) -> List[str]:
        """Get list of supported holiday events."""
        return self.supported_events.copy()