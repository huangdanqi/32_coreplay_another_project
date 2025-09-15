"""
Data reader for continuous neglect events.
Provides read-only access to unkeep_interactive.py for diary generation context.
"""

import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader

try:
    from unkeep_interactive import get_user_data, CONTINUOUS_NEGLECT_EVENTS
except ImportError:
    print("Warning: Could not import unkeep_interactive. Using mock data.")
    CONTINUOUS_NEGLECT_EVENTS = {}
    def get_user_data(user_id):
        return None


class NeglectDataReader(DataReader):
    """
    Data reader for continuous neglect events.
    Reads context from unkeep_interactive.py for diary generation.
    """
    
    def __init__(self):
        super().__init__(module_name="unkeep_interactive", read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read neglect event context for diary generation.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            Context data for diary generation
        """
        try:
            # Get user data from emotion database
            user_data = get_user_data(event_data.user_id)
            
            # Get event configuration
            event_config = CONTINUOUS_NEGLECT_EVENTS.get(event_data.event_name, {})
            
            # Build context data
            user_profile = {}
            if user_data:
                user_profile = {
                    "user_id": user_data.get("id"),
                    "name": user_data.get("name"),
                    "role": user_data.get("role"),
                    "current_x": user_data.get("update_x_value", 0),
                    "current_y": user_data.get("update_y_value", 0),
                    "current_intimacy": user_data.get("intimacy_value", 0)
                }
            
            # Extract neglect information
            neglect_duration = self._extract_neglect_duration(event_data.event_name)
            neglect_type = self._extract_neglect_type(event_data.event_name)
            
            event_details = {
                "event_name": event_data.event_name,
                "event_config": event_config,
                "neglect_duration": neglect_duration,
                "neglect_type": neglect_type,
                "severity_level": self._get_severity_level(neglect_duration),
                "trigger_condition": event_config.get("trigger_condition", ""),
                "probability": event_config.get("probability", 1.0),
                "x_change": event_config.get("x_change", 0),
                "y_change_logic": event_config.get("y_change_logic", {}),
                "intimacy_change": event_config.get("intimacy_change", 0),
                "weights": event_config.get("weights", {})
            }
            
            environmental_context = {
                "neglect_environment": "isolation",
                "interaction_absence": True,
                "loneliness_factor": self._get_loneliness_factor(neglect_duration)
            }
            
            social_context = {
                "owner_toy_relationship": "distant",
                "social_isolation": True,
                "abandonment_feeling": self._get_abandonment_feeling(neglect_duration),
                "relationship_deterioration": neglect_duration >= 7
            }
            
            emotional_context = {
                "neglect_emotion": self._get_neglect_emotion(neglect_duration, neglect_type),
                "loneliness_level": self._get_loneliness_level(neglect_duration),
                "sadness_intensity": self._get_sadness_intensity(neglect_duration),
                "abandonment_fear": self._get_abandonment_fear(neglect_duration)
            }
            
            temporal_context = {
                "timestamp": event_data.timestamp,
                "neglect_duration_days": neglect_duration,
                "neglect_type": neglect_type,
                "continuous_period": True,
                "daily_check_time": "23:59"
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
            print(f"Error reading neglect event context: {e}")
            # Return minimal context on error
            return DiaryContextData(
                user_profile={"user_id": event_data.user_id},
                event_details={"event_name": event_data.event_name},
                environmental_context={},
                social_context={},
                emotional_context={},
                temporal_context={"timestamp": event_data.timestamp}
            )
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences for neglect events.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences dictionary
        """
        try:
            user_data = get_user_data(user_id)
            if user_data:
                return {
                    "role": user_data.get("role", "clam"),
                    "personality_weights": self._get_all_neglect_weights(),
                    "emotional_baseline": {
                        "x": user_data.get("update_x_value", 0),
                        "y": user_data.get("update_y_value", 0),
                        "intimacy": user_data.get("intimacy_value", 0)
                    }
                }
            return {}
        except Exception as e:
            print(f"Error getting user preferences: {e}")
            return {}
    
    def get_neglect_event_info(self, event_name: str) -> Dict[str, Any]:
        """
        Get neglect event configuration information.
        
        Args:
            event_name: Name of the neglect event
            
        Returns:
            Event configuration dictionary
        """
        return CONTINUOUS_NEGLECT_EVENTS.get(event_name, {})
    
    def get_supported_events(self) -> List[str]:
        """
        Get list of supported neglect events.
        
        Returns:
            List of supported event names
        """
        return list(CONTINUOUS_NEGLECT_EVENTS.keys())
    
    def _extract_neglect_duration(self, event_name: str) -> int:
        """Extract neglect duration in days from event name."""
        if "1_day" in event_name:
            return 1
        elif "3_days" in event_name:
            return 3
        elif "7_days" in event_name:
            return 7
        elif "15_days" in event_name:
            return 15
        elif "30_days" in event_name:
            return 30
        else:
            return 0
    
    def _extract_neglect_type(self, event_name: str) -> str:
        """Extract neglect type from event name."""
        if "no_dialogue" in event_name:
            return "dialogue"
        elif "no_interaction" in event_name:
            return "interaction"
        else:
            return "unknown"
    
    def _get_severity_level(self, duration: int) -> str:
        """Get severity level based on duration."""
        if duration <= 1:
            return "mild"
        elif duration <= 3:
            return "moderate"
        elif duration <= 7:
            return "serious"
        elif duration <= 15:
            return "severe"
        else:
            return "critical"
    
    def _get_loneliness_factor(self, duration: int) -> str:
        """Get loneliness factor based on duration."""
        if duration <= 1:
            return "slight"
        elif duration <= 3:
            return "noticeable"
        elif duration <= 7:
            return "significant"
        elif duration <= 15:
            return "intense"
        else:
            return "overwhelming"
    
    def _get_abandonment_feeling(self, duration: int) -> str:
        """Get abandonment feeling based on duration."""
        if duration <= 1:
            return "concern"
        elif duration <= 3:
            return "worry"
        elif duration <= 7:
            return "fear"
        elif duration <= 15:
            return "despair"
        else:
            return "hopelessness"
    
    def _get_neglect_emotion(self, duration: int, neglect_type: str) -> str:
        """Get neglect emotion based on duration and type."""
        base_emotions = {
            1: "sad",
            3: "lonely",
            7: "abandoned",
            15: "desperate",
            30: "hopeless"
        }
        
        base_emotion = base_emotions.get(duration, "sad")
        
        if neglect_type == "dialogue":
            return f"{base_emotion}_silent"
        elif neglect_type == "interaction":
            return f"{base_emotion}_isolated"
        else:
            return base_emotion
    
    def _get_loneliness_level(self, duration: int) -> str:
        """Get loneliness level based on duration."""
        levels = {
            1: "mild_loneliness",
            3: "moderate_loneliness",
            7: "deep_loneliness",
            15: "profound_loneliness",
            30: "overwhelming_loneliness"
        }
        return levels.get(duration, "mild_loneliness")
    
    def _get_sadness_intensity(self, duration: int) -> str:
        """Get sadness intensity based on duration."""
        intensities = {
            1: "light_sadness",
            3: "moderate_sadness",
            7: "deep_sadness",
            15: "intense_sadness",
            30: "overwhelming_sadness"
        }
        return intensities.get(duration, "light_sadness")
    
    def _get_abandonment_fear(self, duration: int) -> str:
        """Get abandonment fear based on duration."""
        fears = {
            1: "slight_concern",
            3: "growing_worry",
            7: "abandonment_fear",
            15: "deep_abandonment_fear",
            30: "complete_abandonment_terror"
        }
        return fears.get(duration, "slight_concern")
    
    def _get_all_neglect_weights(self) -> Dict[str, Dict[str, float]]:
        """Get all neglect event weights for different personality types."""
        weights = {}
        for event_name, config in CONTINUOUS_NEGLECT_EVENTS.items():
            weights[event_name] = config.get("weights", {})
        return weights