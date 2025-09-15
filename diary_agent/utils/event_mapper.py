"""
Event mapping utilities based on events.json structure.
"""

import json
from typing import Dict, List, Optional
from pathlib import Path


class EventMapper:
    """Maps events to appropriate sub-agents based on events.json."""
    
    def __init__(self, events_json_path: str = "events.json"):
        self.events_json_path = events_json_path
        self.event_mappings = self._load_event_mappings()
        self.agent_mappings = self._create_agent_mappings()
    
    def _load_event_mappings(self) -> Dict[str, List[str]]:
        """Load event mappings from events.json."""
        try:
            with open(self.events_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {self.events_json_path} not found, using default mappings")
            return self._get_default_mappings()
        except json.JSONDecodeError as e:
            print(f"Error parsing {self.events_json_path}: {e}")
            return self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict[str, List[str]]:
        """Get default event mappings if events.json is not available."""
        return {
            "weather_events": [
                "favorite_weather",
                "dislike_weather",
                "favorite_season",
                "dislike_season"
            ],
            "seasonal_events": [
                "favorite_season", 
                "dislike_season"
            ],
            "trending_events": [
                "celebration",
                "disaster"
            ],
            "holiday_events": [
                "approaching_holiday",
                "during_holiday",
                "holiday_ends"
            ],
            "friends_function": [
                "made_new_friend",
                "friend_deleted",
                "liked_single",
                "liked_3_to_5",
                "liked_5_plus",
                "disliked_single",
                "disliked_3_to_5",
                "disliked_5_plus"
            ],
            "same_frequency": [
                "close_friend_frequency"
            ],
            "adopted_function": [
                "toy_claimed"
            ],
            "human_toy_interactive_function": [
                "liked_interaction_once",
                "liked_interaction_3_to_5_times",
                "liked_interaction_over_5_times",
                "disliked_interaction_once",
                "disliked_interaction_3_to_5_times",
                "neutral_interaction_over_5_times"
            ],
            "human_toy_talk": [
                "positive_emotional_dialogue",
                "negative_emotional_dialogue"
            ],
            "unkeep_interactive": [
                "neglect_1_day_no_dialogue",
                "neglect_1_day_no_interaction",
                "neglect_3_days_no_dialogue",
                "neglect_3_days_no_interaction",
                "neglect_7_days_no_dialogue",
                "neglect_7_days_no_interaction",
                "neglect_15_days_no_interaction",
                "neglect_30_days_no_dialogue",
                "neglect_30_days_no_interaction"
            ]
        }
    
    def _create_agent_mappings(self) -> Dict[str, str]:
        """Create mappings from event types to agent types."""
        return {
            "weather_events": "weather_agent",
            "seasonal_events": "weather_agent",  # Uses same agent as weather
            "trending_events": "trending_agent",
            "holiday_events": "holiday_agent",
            "friends_function": "friends_agent",
            "same_frequency": "same_frequency_agent",
            "adopted_function": "adoption_agent",
            "human_toy_interactive_function": "interactive_agent",
            "human_toy_talk": "dialogue_agent",
            "unkeep_interactive": "neglect_agent"
        }
    
    def get_agent_type_for_event(self, event_name: str) -> Optional[str]:
        """Get the appropriate agent type for a given event name."""
        for event_type, event_names in self.event_mappings.items():
            if event_name in event_names:
                return self.agent_mappings.get(event_type)
        return None
    
    def get_event_type_for_event(self, event_name: str) -> Optional[str]:
        """Get the event type category for a given event name."""
        for event_type, event_names in self.event_mappings.items():
            if event_name in event_names:
                return event_type
        return None
    
    def get_all_event_types(self) -> List[str]:
        """Get all available event types."""
        return list(self.event_mappings.keys())
    
    def get_events_for_type(self, event_type: str) -> List[str]:
        """Get all event names for a given event type."""
        return self.event_mappings.get(event_type, [])
    
    def is_valid_event(self, event_name: str) -> bool:
        """Check if an event name is valid."""
        return self.get_event_type_for_event(event_name) is not None
    
    def get_source_module_for_event_type(self, event_type: str) -> Optional[str]:
        """Get the source module name for reading event data."""
        module_mappings = {
            "weather_events": "weather_function.py",
            "seasonal_events": "weather_function.py",
            "trending_events": "douyin_news.py",
            "holiday_events": "holiday_function.py",
            "friends_function": "friends_function.py",
            "same_frequency": "same_frequency.py",
            "adopted_function": "adopted_function.py",
            "human_toy_interactive_function": "human_toy_interactive_function.py",
            "human_toy_talk": "human_toy_talk.py",
            "unkeep_interactive": "unkeep_interactive.py"
        }
        return module_mappings.get(event_type)
    
    def get_claimed_events(self) -> List[str]:
        """Get list of events that must always result in diary entries."""
        # Based on diary specifications, certain events are "claimed"
        claimed_events = [
            "toy_claimed",  # Adoption events are always claimed
            # Add other claimed events as specified
        ]
        return claimed_events
    
    def is_claimed_event(self, event_name: str) -> bool:
        """Check if an event is a claimed event."""
        return event_name in self.get_claimed_events()