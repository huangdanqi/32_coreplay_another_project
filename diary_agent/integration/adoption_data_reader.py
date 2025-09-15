"""
Data reader for adoption events.
Provides read-only access to adopted_function.py for diary generation context.
"""

import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader

try:
    from adopted_function import get_user_data, ADOPTED_EVENTS
except ImportError:
    print("Warning: Could not import adopted_function. Using mock data.")
    ADOPTED_EVENTS = {}
    def get_user_data(user_id):
        return None


class AdoptionDataReader(DataReader):
    """
    Data reader for adoption events.
    Reads context from adopted_function.py for diary generation.
    """
    
    def __init__(self):
        super().__init__(module_name="adopted_function", read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read adoption event context for diary generation.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            Context data for diary generation
        """
        try:
            # Get user data from emotion database
            user_data = get_user_data(event_data.user_id)
            
            # Get event configuration
            event_config = ADOPTED_EVENTS.get(event_data.event_name, {})
            
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
            
            event_details = {
                "event_name": event_data.event_name,
                "event_config": event_config,
                "trigger_condition": event_config.get("trigger_condition", ""),
                "probability": event_config.get("probability", 1.0),
                "x_change": event_config.get("x_change", 0),
                "y_change_logic": event_config.get("y_change_logic", {}),
                "intimacy_change": event_config.get("intimacy_change", 0),
                "weights": event_config.get("weights", {})
            }
            
            environmental_context = {
                "adoption_status": "claimed",
                "device_binding": "successful"
            }
            
            social_context = {
                "new_owner_relationship": "established",
                "bonding_event": True
            }
            
            emotional_context = {
                "adoption_emotion": "excitement",
                "bonding_feeling": "positive",
                "security_level": "increased"
            }
            
            temporal_context = {
                "timestamp": event_data.timestamp,
                "event_timing": "immediate",
                "adoption_moment": True
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
            print(f"Error reading adoption event context: {e}")
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
        Get user preferences for adoption events.
        
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
                    "personality_weights": ADOPTED_EVENTS.get("toy_claimed", {}).get("weights", {}),
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
    
    def get_adoption_event_info(self, event_name: str) -> Dict[str, Any]:
        """
        Get adoption event configuration information.
        
        Args:
            event_name: Name of the adoption event
            
        Returns:
            Event configuration dictionary
        """
        return ADOPTED_EVENTS.get(event_name, {})
    
    def get_supported_events(self) -> list:
        """
        Get list of supported adoption events.
        
        Returns:
            List of supported event names
        """
        return list(ADOPTED_EVENTS.keys())