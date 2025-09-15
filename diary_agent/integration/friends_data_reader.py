"""
Friends data reader for integrating with existing friends_function.py module.
Provides read-only access to friend event data for diary generation context.
"""

import json
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

try:
    from friends_function import (
        get_user_data, get_interaction_count_in_timeframe, 
        is_liked_interaction, is_disliked_interaction,
        FRIEND_EVENTS, INTERACTION_EVENTS
    )
except ImportError as e:
    print(f"Warning: Could not import friends functions: {e}")
    # Define fallback functions for testing
    def get_user_data(user_id): return None
    def get_interaction_count_in_timeframe(user_id, interaction_type, minutes): return 0
    def is_liked_interaction(user_id, interaction_type): return False
    def is_disliked_interaction(user_id, interaction_type): return False
    FRIEND_EVENTS = {}
    INTERACTION_EVENTS = {}

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader


class FriendsDataReader(DataReader):
    """
    Data reader for friend events that interfaces with existing friends_function.py.
    Provides read-only access to friend data for diary generation context.
    """
    
    def __init__(self):
        super().__init__(module_name="friends_function", read_only=True)
        self.supported_events = [
            "made_new_friend", "friend_deleted", 
            "liked_single", "liked_3_to_5", "liked_5_plus",
            "disliked_single", "disliked_3_to_5", "disliked_5_plus"
        ]
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read friend event context from existing friends_function.py module.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            DiaryContextData with friend context for diary generation
        """
        try:
            # Get user data from emotion database
            user_profile = self.get_user_preferences(event_data.user_id)
            if not user_profile:
                return self._create_minimal_context(event_data)
            
            # Determine event type and get relevant context
            event_details = self._analyze_friend_event(event_data, user_profile)
            
            # Build social context
            social_context = self._build_social_context(event_data, user_profile)
            
            # Build emotional context
            emotional_context = self._build_emotional_context(event_data, user_profile)
            
            # Build temporal context
            temporal_context = {
                "timestamp": event_data.timestamp,
                "time_of_day": self._get_time_of_day(event_data.timestamp),
                "recent_interactions": self._get_recent_interaction_summary(event_data.user_id)
            }
            
            return DiaryContextData(
                user_profile=user_profile,
                event_details=event_details,
                environmental_context={},  # Friend events don't have environmental context
                social_context=social_context,
                emotional_context=emotional_context,
                temporal_context=temporal_context
            )
            
        except Exception as e:
            print(f"Error reading friend event context: {e}")
            return self._create_minimal_context(event_data)
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from emotion database via friends_function.
        
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
            event_details={"event_name": event_data.event_name, "event_type": "friend"},
            environmental_context={},
            social_context={"friend_count": 0},
            emotional_context={"interaction_preference": "neutral"},
            temporal_context={"timestamp": event_data.timestamp}
        )
    
    def _analyze_friend_event(self, event_data: EventData, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze friend event to determine context details.
        
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
            "event_category": self._categorize_event(event_name)
        }
        
        # Get event configuration from friends_function
        if event_name in FRIEND_EVENTS:
            event_config = FRIEND_EVENTS[event_name]
            event_details.update({
                "event_type": "friendship_change",
                "chinese_name": event_config["name"],
                "trigger_condition": event_config["trigger_condition"],
                "emotion_impact": {
                    "x_change": event_config["x_change"],
                    "y_change_logic": event_config["y_change_logic"],
                    "weights": event_config["weights"]
                }
            })
        elif event_name in INTERACTION_EVENTS:
            event_config = INTERACTION_EVENTS[event_name]
            event_details.update({
                "event_type": "friend_interaction",
                "chinese_name": event_config["name"],
                "trigger_condition": event_config["trigger_condition"],
                "interaction_frequency": self._parse_frequency_from_name(event_name),
                "interaction_preference": self._get_interaction_preference(event_name),
                "emotion_impact": {
                    "x_change": event_config["x_change"],
                    "y_change_logic": event_config["y_change_logic"],
                    "weights": event_config["weights"]
                }
            })
            
            # Add interaction type from metadata if available
            interaction_type = event_data.metadata.get("interaction_type", "摸摸脸")
            event_details["interaction_type"] = interaction_type
            
            # Check user's preference for this interaction type
            event_details["user_likes_interaction"] = is_liked_interaction(
                event_data.user_id, interaction_type
            )
            event_details["user_dislikes_interaction"] = is_disliked_interaction(
                event_data.user_id, interaction_type
            )
        
        return event_details
    
    def _build_social_context(self, event_data: EventData, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Build social context for friend events."""
        social_context = {
            "current_friend_count": user_profile.get("friend_count", 0),
            "user_role": user_profile.get("role", "clam")
        }
        
        # Parse user's social preferences
        try:
            favorite_actions = json.loads(user_profile.get("favorite_action", "[]"))
            annoying_actions = json.loads(user_profile.get("annoying_action", "[]"))
            
            social_context.update({
                "favorite_interactions": favorite_actions,
                "disliked_interactions": annoying_actions,
                "social_preferences_defined": len(favorite_actions) > 0 or len(annoying_actions) > 0
            })
        except (json.JSONDecodeError, TypeError):
            social_context.update({
                "favorite_interactions": [],
                "disliked_interactions": [],
                "social_preferences_defined": False
            })
        
        # Add friend-specific context from metadata
        if "friend_id" in event_data.metadata:
            friend_id = event_data.metadata["friend_id"]
            social_context["friend_id"] = friend_id
            social_context["friendship_context"] = self._get_friendship_context(
                event_data.user_id, friend_id
            )
        
        return social_context
    
    def _build_emotional_context(self, event_data: EventData, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Build emotional context for friend events."""
        event_name = event_data.event_name
        
        emotional_context = {
            "current_x": user_profile.get("update_x_value", 0),
            "current_y": user_profile.get("update_y_value", 0),
            "current_intimacy": user_profile.get("intimacy_value", 0),
            "emotional_intensity": self._calculate_emotional_intensity(
                user_profile.get("role", "clam"), event_name
            )
        }
        
        # Determine emotional tone based on event type
        if "made_new_friend" in event_name:
            emotional_context["emotional_tone"] = "positive"
            emotional_context["social_impact"] = "expansion"
        elif "friend_deleted" in event_name:
            emotional_context["emotional_tone"] = "negative"
            emotional_context["social_impact"] = "loss"
        elif "liked" in event_name:
            emotional_context["emotional_tone"] = "positive"
            emotional_context["social_impact"] = "bonding"
        elif "disliked" in event_name:
            emotional_context["emotional_tone"] = "negative"
            emotional_context["social_impact"] = "tension"
        else:
            emotional_context["emotional_tone"] = "neutral"
            emotional_context["social_impact"] = "maintenance"
        
        return emotional_context
    
    def _categorize_event(self, event_name: str) -> str:
        """Categorize the friend event type."""
        if event_name in ["made_new_friend", "friend_deleted"]:
            return "friendship_management"
        elif "liked" in event_name or "disliked" in event_name:
            return "friend_interaction"
        else:
            return "unknown"
    
    def _parse_frequency_from_name(self, event_name: str) -> str:
        """Parse interaction frequency from event name."""
        if "single" in event_name:
            return "once"
        elif "3_to_5" in event_name:
            return "3-5 times"
        elif "5_plus" in event_name:
            return "5+ times"
        else:
            return "unknown"
    
    def _get_interaction_preference(self, event_name: str) -> str:
        """Get interaction preference from event name."""
        if "liked" in event_name:
            return "liked"
        elif "disliked" in event_name:
            return "disliked"
        else:
            return "neutral"
    
    def _calculate_emotional_intensity(self, role: str, event_name: str) -> float:
        """Calculate emotional intensity based on role and event type."""
        # Role weights from friends_function.py
        role_weights = {
            "lively": 1.5,
            "clam": 1.0
        }
        
        role = role.lower()
        base_weight = role_weights.get(role, 1.0)
        
        # Adjust based on event intensity
        if "5_plus" in event_name:
            return base_weight * 1.5
        elif "3_to_5" in event_name:
            return base_weight * 1.2
        elif "made_new_friend" in event_name or "friend_deleted" in event_name:
            return base_weight * 1.3
        else:
            return base_weight
    
    def _get_friendship_context(self, user_id: int, friend_id: int) -> Dict[str, Any]:
        """Get context about a specific friendship."""
        # This would typically query the friendship database
        # For now, return basic context
        return {
            "friend_id": friend_id,
            "relationship_status": "active",
            "interaction_history": "available"
        }
    
    def _get_recent_interaction_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary of recent interactions for context."""
        try:
            # Get interaction counts for different types in the last hour
            interaction_types = ["摸摸脸", "拍拍头", "捏一下", "摇一摇"]
            recent_interactions = {}
            
            for interaction_type in interaction_types:
                count = get_interaction_count_in_timeframe(user_id, interaction_type, 60)  # Last hour
                if count > 0:
                    recent_interactions[interaction_type] = count
            
            return {
                "total_recent_interactions": sum(recent_interactions.values()),
                "interaction_breakdown": recent_interactions,
                "most_frequent_interaction": max(recent_interactions.items(), key=lambda x: x[1])[0] if recent_interactions else None
            }
        except Exception as e:
            print(f"Error getting recent interaction summary: {e}")
            return {"total_recent_interactions": 0, "interaction_breakdown": {}}
    
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
        """Get list of supported friend events."""
        return self.supported_events.copy()