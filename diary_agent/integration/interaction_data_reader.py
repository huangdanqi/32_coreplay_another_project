"""
Data reader for human-toy interaction events.
Provides read-only access to human_toy_interactive_function.py for diary generation context.
"""

import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader

try:
    from human_toy_interactive_function import (
        get_user_data, 
        HUMAN_TOY_INTERACTIVE_EVENTS,
        get_recent_interactions,
        check_interaction_preference,
        count_recent_interactions_by_preference,
        determine_interaction_event_type
    )
except ImportError:
    print("Warning: Could not import human_toy_interactive_function. Using mock data.")
    HUMAN_TOY_INTERACTIVE_EVENTS = {}
    def get_user_data(user_id):
        return None
    def get_recent_interactions(user_id, minutes=1):
        return []
    def check_interaction_preference(interaction_type, user_data):
        return "neutral"
    def count_recent_interactions_by_preference(user_id, preference, minutes=1):
        return 0
    def determine_interaction_event_type(user_id, interaction_type):
        return None


class InteractionDataReader(DataReader):
    """
    Data reader for human-toy interaction events.
    Reads context from human_toy_interactive_function.py for diary generation.
    """
    
    def __init__(self):
        super().__init__(module_name="human_toy_interactive_function", read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read interaction event context for diary generation.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            Context data for diary generation
        """
        try:
            # Get user data from emotion database
            user_data = get_user_data(event_data.user_id)
            
            # Get event configuration
            event_config = HUMAN_TOY_INTERACTIVE_EVENTS.get(event_data.event_name, {})
            
            # Get recent interactions
            recent_interactions = get_recent_interactions(event_data.user_id, minutes=1)
            
            # Build context data
            user_profile = {}
            if user_data:
                user_profile = {
                    "user_id": user_data.get("id"),
                    "name": user_data.get("name"),
                    "role": user_data.get("role"),
                    "current_x": user_data.get("update_x_value", 0),
                    "current_y": user_data.get("update_y_value", 0),
                    "current_intimacy": user_data.get("intimacy_value", 0),
                    "favorite_actions": user_data.get("favorite_action", ""),
                    "annoying_actions": user_data.get("annoying_action", "")
                }
            
            # Determine interaction preference and frequency
            interaction_type = event_data.context_data.get("interaction_type", "")
            preference = "neutral"
            if user_data and interaction_type:
                preference = check_interaction_preference(interaction_type, user_data)
            
            # Count recent interactions by preference
            liked_count = count_recent_interactions_by_preference(event_data.user_id, "liked", minutes=1)
            disliked_count = count_recent_interactions_by_preference(event_data.user_id, "disliked", minutes=1)
            neutral_count = count_recent_interactions_by_preference(event_data.user_id, "neutral", minutes=1)
            
            event_details = {
                "event_name": event_data.event_name,
                "event_config": event_config,
                "interaction_type": interaction_type,
                "interaction_preference": preference,
                "trigger_condition": event_config.get("trigger_condition", ""),
                "probability": event_config.get("probability", 1.0),
                "x_change": event_config.get("x_change", 0),
                "y_change_logic": event_config.get("y_change_logic", {}),
                "intimacy_change": event_config.get("intimacy_change", 0),
                "weights": event_config.get("weights", {}),
                "recent_interaction_counts": {
                    "liked": liked_count,
                    "disliked": disliked_count,
                    "neutral": neutral_count
                }
            }
            
            environmental_context = {
                "interaction_environment": "home",
                "interaction_frequency": self._categorize_frequency(event_data.event_name),
                "interaction_intensity": self._get_interaction_intensity(event_data.event_name)
            }
            
            social_context = {
                "owner_toy_relationship": "interactive",
                "interaction_history": recent_interactions[-5:] if recent_interactions else [],
                "interaction_pattern": self._analyze_interaction_pattern(recent_interactions)
            }
            
            emotional_context = {
                "interaction_emotion": self._get_interaction_emotion(preference, event_data.event_name),
                "preference_match": preference,
                "emotional_response": self._get_emotional_response(event_data.event_name)
            }
            
            temporal_context = {
                "timestamp": event_data.timestamp,
                "interaction_timing": "real_time",
                "frequency_window": "1_minute",
                "recent_interactions": len(recent_interactions)
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
            print(f"Error reading interaction event context: {e}")
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
        Get user preferences for interaction events.
        
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
                    "favorite_actions": user_data.get("favorite_action", ""),
                    "annoying_actions": user_data.get("annoying_action", ""),
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
    
    def get_interaction_event_info(self, event_name: str) -> Dict[str, Any]:
        """
        Get interaction event configuration information.
        
        Args:
            event_name: Name of the interaction event
            
        Returns:
            Event configuration dictionary
        """
        return HUMAN_TOY_INTERACTIVE_EVENTS.get(event_name, {})
    
    def get_supported_events(self) -> List[str]:
        """
        Get list of supported interaction events.
        
        Returns:
            List of supported event names
        """
        return list(HUMAN_TOY_INTERACTIVE_EVENTS.keys())
    
    def _categorize_frequency(self, event_name: str) -> str:
        """Categorize interaction frequency based on event name."""
        if "once" in event_name:
            return "single"
        elif "3_to_5" in event_name:
            return "moderate"
        elif "over_5" in event_name:
            return "frequent"
        else:
            return "unknown"
    
    def _get_interaction_intensity(self, event_name: str) -> str:
        """Get interaction intensity based on event name."""
        if "liked" in event_name:
            return "positive"
        elif "disliked" in event_name:
            return "negative"
        elif "neutral" in event_name:
            return "neutral"
        else:
            return "unknown"
    
    def _analyze_interaction_pattern(self, interactions: List[Dict]) -> str:
        """Analyze pattern from recent interactions."""
        if not interactions:
            return "no_pattern"
        
        if len(interactions) == 1:
            return "single_interaction"
        elif len(interactions) <= 3:
            return "light_interaction"
        elif len(interactions) <= 5:
            return "moderate_interaction"
        else:
            return "heavy_interaction"
    
    def _get_interaction_emotion(self, preference: str, event_name: str) -> str:
        """Get emotion based on preference and event."""
        if preference == "liked":
            if "over_5" in event_name:
                return "very_happy"
            elif "3_to_5" in event_name:
                return "happy"
            else:
                return "pleased"
        elif preference == "disliked":
            if "over_5" in event_name:
                return "very_upset"
            elif "3_to_5" in event_name:
                return "upset"
            else:
                return "annoyed"
        else:
            return "neutral"
    
    def _get_emotional_response(self, event_name: str) -> str:
        """Get emotional response based on event name."""
        if "liked" in event_name:
            return "positive_response"
        elif "disliked" in event_name:
            return "negative_response"
        elif "neutral" in event_name:
            return "neutral_response"
        else:
            return "unknown_response"