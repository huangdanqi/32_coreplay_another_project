"""
Same frequency data reader for integrating with existing same_frequency.py module.
Provides read-only access to same frequency event data for diary generation context.
"""

import json
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

try:
    from same_frequency import (
        get_user_data, get_close_friends, get_recent_interactions,
        check_same_frequency_event, SAME_FREQUENCY_EVENTS
    )
except ImportError as e:
    print(f"Warning: Could not import same frequency functions: {e}")
    # Define fallback functions for testing
    def get_user_data(user_id): return None
    def get_close_friends(user_id): return []
    def get_recent_interactions(user_id, minutes): return []
    def check_same_frequency_event(user1_id, user2_id, time_window): return None
    SAME_FREQUENCY_EVENTS = {}

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader


class FrequencyDataReader(DataReader):
    """
    Data reader for same frequency events that interfaces with existing same_frequency.py.
    Provides read-only access to frequency synchronization data for diary generation context.
    """
    
    def __init__(self):
        super().__init__(module_name="same_frequency", read_only=True)
        self.supported_events = ["close_friend_frequency"]
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read same frequency event context from existing same_frequency.py module.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            DiaryContextData with frequency synchronization context for diary generation
        """
        try:
            # Get user data from emotion database
            user_profile = self.get_user_preferences(event_data.user_id)
            if not user_profile:
                return self._create_minimal_context(event_data)
            
            # Get frequency event details
            event_details = self._analyze_frequency_event(event_data, user_profile)
            
            # Build social context with friend synchronization info
            social_context = self._build_social_context(event_data, user_profile)
            
            # Build emotional context
            emotional_context = self._build_emotional_context(event_data, user_profile)
            
            # Build temporal context with synchronization timing
            temporal_context = self._build_temporal_context(event_data)
            
            return DiaryContextData(
                user_profile=user_profile,
                event_details=event_details,
                environmental_context={},  # Frequency events don't have environmental context
                social_context=social_context,
                emotional_context=emotional_context,
                temporal_context=temporal_context
            )
            
        except Exception as e:
            print(f"Error reading frequency event context: {e}")
            return self._create_minimal_context(event_data)
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from emotion database via same_frequency.
        
        Args:
            user_id: User ID to get preferences for
            
        Returns:
            User profile dictionary or None if not found
        """
        try:
            return get_user_data(user_id)
        except Exception as e:
            print(f"Error getting user preferences for user {user_id}: {e}")
            return None
    
    def _create_minimal_context(self, event_data: EventData) -> DiaryContextData:
        """Create minimal context when data reading fails."""
        return DiaryContextData(
            user_profile={"id": event_data.user_id, "role": "clam"},
            event_details={"event_name": event_data.event_name, "event_type": "frequency"},
            environmental_context={},
            social_context={"synchronization_detected": False},
            emotional_context={"synchronization_strength": "weak"},
            temporal_context={"timestamp": event_data.timestamp}
        )
    
    def _analyze_frequency_event(self, event_data: EventData, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze frequency event to determine synchronization context.
        
        Args:
            event_data: Event data
            user_profile: User profile data
            
        Returns:
            Event details dictionary
        """
        event_name = event_data.event_name
        
        event_details = {
            "event_name": event_name,
            "user_role": user_profile.get("role", "clam"),
            "event_type": "synchronization"
        }
        
        # Get event configuration from same_frequency
        if event_name in SAME_FREQUENCY_EVENTS:
            event_config = SAME_FREQUENCY_EVENTS[event_name]
            event_details.update({
                "chinese_name": event_config["name"],
                "english_name": event_config["english_name"],
                "trigger_condition": event_config["trigger_condition"],
                "synchronization_window": "5 seconds",
                "emotion_impact": {
                    "x_change": event_config["x_change"],
                    "y_change_logic": event_config["y_change_logic"],
                    "weights": event_config["weights"]
                }
            })
        
        # Add synchronization details from metadata
        if "friend_id" in event_data.metadata:
            friend_id = event_data.metadata["friend_id"]
            interaction_type = event_data.metadata.get("interaction_type", "摸摸脸")
            time_difference = event_data.metadata.get("time_difference_seconds", 0)
            
            event_details.update({
                "friend_id": friend_id,
                "synchronized_interaction": interaction_type,
                "time_difference_seconds": time_difference,
                "synchronization_quality": self._assess_synchronization_quality(time_difference)
            })
            
            # Check for frequency event between users
            frequency_event = check_same_frequency_event(
                event_data.user_id, friend_id, time_window_seconds=5
            )
            if frequency_event:
                event_details["frequency_event_detected"] = True
                event_details["frequency_details"] = frequency_event
            else:
                event_details["frequency_event_detected"] = False
        
        return event_details
    
    def _build_social_context(self, event_data: EventData, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Build social context for frequency events."""
        user_id = event_data.user_id
        
        social_context = {
            "user_role": user_profile.get("role", "clam"),
            "close_friends": self._get_close_friends_info(user_id),
            "synchronization_partner": None
        }
        
        # Get close friends list
        try:
            close_friends = get_close_friends(user_id)
            social_context["close_friends_count"] = len(close_friends)
            social_context["close_friends_list"] = close_friends
        except Exception as e:
            print(f"Error getting close friends: {e}")
            social_context["close_friends_count"] = 0
            social_context["close_friends_list"] = []
        
        # Add synchronization partner info if available
        if "friend_id" in event_data.metadata:
            friend_id = event_data.metadata["friend_id"]
            social_context["synchronization_partner"] = {
                "friend_id": friend_id,
                "is_close_friend": friend_id in social_context["close_friends_list"],
                "synchronized_interaction": event_data.metadata.get("interaction_type", "摸摸脸")
            }
        
        # Get recent interaction patterns
        social_context["recent_interactions"] = self._get_recent_interaction_patterns(user_id)
        
        return social_context
    
    def _build_emotional_context(self, event_data: EventData, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Build emotional context for frequency events."""
        emotional_context = {
            "current_x": user_profile.get("update_x_value", 0),
            "current_y": user_profile.get("update_y_value", 0),
            "current_intimacy": user_profile.get("intimacy_value", 0),
            "emotional_tone": "positive",  # Frequency events are generally positive
            "synchronization_impact": "bonding"
        }
        
        # Calculate emotional intensity based on role
        role = user_profile.get("role", "clam").lower()
        if role == "lively":
            emotional_context["emotional_intensity"] = 1.0  # Same weight for both roles in frequency events
        else:  # clam
            emotional_context["emotional_intensity"] = 1.0
        
        # Assess synchronization strength
        if "time_difference_seconds" in event_data.metadata:
            time_diff = event_data.metadata["time_difference_seconds"]
            emotional_context["synchronization_strength"] = self._assess_synchronization_quality(time_diff)
        else:
            emotional_context["synchronization_strength"] = "unknown"
        
        return emotional_context
    
    def _build_temporal_context(self, event_data: EventData) -> Dict[str, Any]:
        """Build temporal context with synchronization timing."""
        temporal_context = {
            "timestamp": event_data.timestamp,
            "time_of_day": self._get_time_of_day(event_data.timestamp),
            "synchronization_window": "5 seconds"
        }
        
        # Add synchronization timing details
        if "time_difference_seconds" in event_data.metadata:
            time_diff = event_data.metadata["time_difference_seconds"]
            temporal_context.update({
                "time_difference_seconds": time_diff,
                "synchronization_precision": f"{time_diff:.1f}s",
                "within_window": time_diff <= 5.0
            })
        
        return temporal_context
    
    def _get_close_friends_info(self, user_id: int) -> Dict[str, Any]:
        """Get detailed information about close friends."""
        try:
            close_friends = get_close_friends(user_id)
            return {
                "count": len(close_friends),
                "friend_ids": close_friends,
                "has_close_friends": len(close_friends) > 0
            }
        except Exception as e:
            print(f"Error getting close friends info: {e}")
            return {"count": 0, "friend_ids": [], "has_close_friends": False}
    
    def _get_recent_interaction_patterns(self, user_id: int) -> Dict[str, Any]:
        """Get recent interaction patterns for context."""
        try:
            # Get recent interactions in the last 5 minutes
            recent_interactions = get_recent_interactions(user_id, minutes=5)
            
            interaction_summary = {
                "total_interactions": len(recent_interactions),
                "interaction_types": {},
                "most_recent": None
            }
            
            # Analyze interaction types
            for interaction in recent_interactions:
                interaction_type = interaction.get("interaction_type", "unknown")
                if interaction_type in interaction_summary["interaction_types"]:
                    interaction_summary["interaction_types"][interaction_type] += 1
                else:
                    interaction_summary["interaction_types"][interaction_type] = 1
            
            # Get most recent interaction
            if recent_interactions:
                interaction_summary["most_recent"] = recent_interactions[0]
            
            return interaction_summary
            
        except Exception as e:
            print(f"Error getting recent interaction patterns: {e}")
            return {"total_interactions": 0, "interaction_types": {}}
    
    def _assess_synchronization_quality(self, time_difference_seconds: float) -> str:
        """Assess the quality of synchronization based on time difference."""
        if time_difference_seconds <= 1.0:
            return "perfect"
        elif time_difference_seconds <= 2.0:
            return "excellent"
        elif time_difference_seconds <= 3.0:
            return "good"
        elif time_difference_seconds <= 5.0:
            return "acceptable"
        else:
            return "poor"
    
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
        """Get list of supported frequency events."""
        return self.supported_events.copy()