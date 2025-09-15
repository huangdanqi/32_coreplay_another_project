"""
Data reader for human-toy dialogue events.
Provides read-only access to human_toy_talk.py for diary generation context.
"""

import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader

try:
    from human_toy_talk import get_user_data, HUMAN_TOY_TALK_EVENTS
except ImportError:
    print("Warning: Could not import human_toy_talk. Using mock data.")
    HUMAN_TOY_TALK_EVENTS = {}
    def get_user_data(user_id):
        return None


class DialogueDataReader(DataReader):
    """
    Data reader for human-toy dialogue events.
    Reads context from human_toy_talk.py for diary generation.
    """
    
    def __init__(self):
        super().__init__(module_name="human_toy_talk", read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read dialogue event context for diary generation.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            Context data for diary generation
        """
        try:
            # Get user data from emotion database
            user_data = get_user_data(event_data.user_id)
            
            # Get event configuration
            event_config = HUMAN_TOY_TALK_EVENTS.get(event_data.event_name, {})
            
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
            
            # Extract dialogue information from context
            dialogue_message = event_data.context_data.get("dialogue_message", "")
            owner_emotion = event_data.context_data.get("owner_emotion", "")
            
            event_details = {
                "event_name": event_data.event_name,
                "event_config": event_config,
                "dialogue_message": dialogue_message,
                "owner_emotion": owner_emotion,
                "emotion_category": self._categorize_emotion(event_data.event_name),
                "trigger_condition": event_config.get("trigger_condition", ""),
                "probability": event_config.get("probability", 1.0),
                "x_change": event_config.get("x_change", 0),
                "y_change_logic": event_config.get("y_change_logic", {}),
                "intimacy_change": event_config.get("intimacy_change", 0),
                "weights": event_config.get("weights", {})
            }
            
            environmental_context = {
                "dialogue_environment": "home",
                "communication_mode": "voice_interaction",
                "dialogue_context": self._get_dialogue_context(event_data.event_name)
            }
            
            social_context = {
                "owner_toy_relationship": "communicative",
                "dialogue_type": self._get_dialogue_type(event_data.event_name),
                "emotional_exchange": True,
                "intimacy_building": event_config.get("intimacy_change", 0) > 0
            }
            
            emotional_context = {
                "owner_emotional_state": self._get_owner_emotional_state(event_data.event_name),
                "toy_emotional_response": self._get_toy_emotional_response(event_data.event_name),
                "emotional_contagion": self._get_emotional_contagion(event_data.event_name),
                "dialogue_sentiment": self._get_dialogue_sentiment(event_data.event_name)
            }
            
            temporal_context = {
                "timestamp": event_data.timestamp,
                "dialogue_timing": "real_time",
                "emotional_moment": True,
                "communication_event": True
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
            print(f"Error reading dialogue event context: {e}")
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
        Get user preferences for dialogue events.
        
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
                    "personality_weights": {
                        "positive_dialogue": HUMAN_TOY_TALK_EVENTS.get("positive_emotional_dialogue", {}).get("weights", {}),
                        "negative_dialogue": HUMAN_TOY_TALK_EVENTS.get("negative_emotional_dialogue", {}).get("weights", {})
                    },
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
    
    def get_dialogue_event_info(self, event_name: str) -> Dict[str, Any]:
        """
        Get dialogue event configuration information.
        
        Args:
            event_name: Name of the dialogue event
            
        Returns:
            Event configuration dictionary
        """
        return HUMAN_TOY_TALK_EVENTS.get(event_name, {})
    
    def get_supported_events(self) -> List[str]:
        """
        Get list of supported dialogue events.
        
        Returns:
            List of supported event names
        """
        return list(HUMAN_TOY_TALK_EVENTS.keys())
    
    def _categorize_emotion(self, event_name: str) -> str:
        """Categorize emotion based on event name."""
        if "positive" in event_name:
            return "positive"
        elif "negative" in event_name:
            return "negative"
        else:
            return "neutral"
    
    def _get_dialogue_context(self, event_name: str) -> str:
        """Get dialogue context based on event name."""
        if "positive" in event_name:
            return "happy_conversation"
        elif "negative" in event_name:
            return "emotional_support"
        else:
            return "general_conversation"
    
    def _get_dialogue_type(self, event_name: str) -> str:
        """Get dialogue type based on event name."""
        if "positive" in event_name:
            return "joyful_sharing"
        elif "negative" in event_name:
            return "emotional_venting"
        else:
            return "casual_chat"
    
    def _get_owner_emotional_state(self, event_name: str) -> str:
        """Get owner's emotional state based on event name."""
        if "positive" in event_name:
            return "happy_excited"
        elif "negative" in event_name:
            return "sad_angry_worried"
        else:
            return "neutral"
    
    def _get_toy_emotional_response(self, event_name: str) -> str:
        """Get toy's emotional response based on event name."""
        if "positive" in event_name:
            return "empathetic_joy"
        elif "negative" in event_name:
            return "empathetic_concern"
        else:
            return "neutral_response"
    
    def _get_emotional_contagion(self, event_name: str) -> str:
        """Get emotional contagion effect based on event name."""
        if "positive" in event_name:
            return "shared_happiness"
        elif "negative" in event_name:
            return "shared_concern"
        else:
            return "neutral_sharing"
    
    def _get_dialogue_sentiment(self, event_name: str) -> str:
        """Get dialogue sentiment based on event name."""
        if "positive" in event_name:
            return "uplifting"
        elif "negative" in event_name:
            return "supportive"
        else:
            return "neutral"