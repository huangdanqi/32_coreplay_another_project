"""
Event Manager utility for loading and managing event definitions.
This module provides easy access to event configurations and validation.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EventDefinition:
    """Represents a single event definition."""
    name: str
    description: str
    emotional_impact: str
    weight_key: Optional[str]
    requires_weather_api: bool
    requires_user_preferences: bool
    agent_type: str
    category: str

@dataclass
class EventCategory:
    """Represents an event category with its associated agent."""
    name: str
    agent_type: str
    description: str
    events: Dict[str, EventDefinition]

class EventManager:
    """Manages event definitions and provides lookup functionality."""
    
    def __init__(self, config_path: str = "config/event_definitions.json"):
        """Initialize the event manager with configuration file."""
        self.config_path = Path(config_path)
        self.config = {}
        self.categories = {}
        self.events_by_name = {}
        self.events_by_agent = {}
        self.load_configuration()
    
    def load_configuration(self) -> None:
        """Load event configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self._parse_events()
            print(f"✅ Loaded {len(self.events_by_name)} events from {len(self.categories)} categories")
            
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            raise
    
    def _parse_events(self) -> None:
        """Parse events from configuration into structured objects."""
        event_categories = self.config.get("event_categories", {})
        
        for category_name, category_data in event_categories.items():
            agent_type = category_data.get("agent_type")
            description = category_data.get("description", "")
            events = {}
            
            # Parse individual events
            for event_name, event_data in category_data.get("events", {}).items():
                event_def = EventDefinition(
                    name=event_data["name"],
                    description=event_data["description"],
                    emotional_impact=event_data["emotional_impact"],
                    weight_key=event_data.get("weight_key"),
                    requires_weather_api=event_data["requires_weather_api"],
                    requires_user_preferences=event_data["requires_user_preferences"],
                    agent_type=agent_type,
                    category=category_name
                )
                
                events[event_name] = event_def
                self.events_by_name[event_name] = event_def
                
                # Group by agent type
                if agent_type not in self.events_by_agent:
                    self.events_by_agent[agent_type] = []
                self.events_by_agent[agent_type].append(event_def)
            
            # Create category object
            self.categories[category_name] = EventCategory(
                name=category_name,
                agent_type=agent_type,
                description=description,
                events=events
            )
    
    def get_event(self, event_name: str) -> Optional[EventDefinition]:
        """Get event definition by name."""
        return self.events_by_name.get(event_name)
    
    def get_events_by_agent(self, agent_type: str) -> List[EventDefinition]:
        """Get all events handled by a specific agent."""
        return self.events_by_agent.get(agent_type, [])
    
    def get_category(self, category_name: str) -> Optional[EventCategory]:
        """Get event category by name."""
        return self.categories.get(category_name)
    
    def get_agent_for_event(self, event_name: str) -> Optional[str]:
        """Get the agent type that handles a specific event."""
        event = self.get_event(event_name)
        return event.agent_type if event else None
    
    def get_role_weights(self, role: str = "clam") -> Dict[str, float]:
        """Get role-based weights for emotion calculation."""
        return self.config.get("role_weights", {}).get(role, {})
    
    def get_emotional_tags(self, impact_type: str = "positive") -> List[str]:
        """Get emotional tags for a specific impact type."""
        return self.config.get("emotional_tags", {}).get(impact_type, [])
    
    def get_diary_constraints(self) -> Dict[str, Any]:
        """Get diary formatting constraints."""
        return self.config.get("diary_constraints", {})
    
    def get_api_config(self, api_name: str = "weather_api") -> Dict[str, Any]:
        """Get API configuration."""
        return self.config.get("api_configuration", {}).get(api_name, {})
    
    def validate_event(self, event_name: str, event_data: Dict[str, Any]) -> bool:
        """Validate if event data meets requirements."""
        event_def = self.get_event(event_name)
        if not event_def:
            return False
        
        # Check required fields based on event definition
        if event_def.requires_weather_api:
            if not event_data.get("weather_data"):
                print(f"❌ Event {event_name} requires weather data")
                return False
        
        if event_def.requires_user_preferences:
            if not event_data.get("user_preferences"):
                print(f"❌ Event {event_name} requires user preferences")
                return False
        
        return True
    
    def list_all_events(self) -> List[str]:
        """Get list of all available event names."""
        return list(self.events_by_name.keys())
    
    def list_all_agents(self) -> List[str]:
        """Get list of all agent types."""
        return list(self.events_by_agent.keys())
    
    def get_weather_events(self) -> List[EventDefinition]:
        """Get all weather-related events."""
        return self.get_events_by_agent("weather_agent")
    
    def print_summary(self) -> None:
        """Print a summary of loaded events."""
        print("\n📋 Event Manager Summary")
        print("=" * 50)
        
        for category_name, category in self.categories.items():
            print(f"\n🏷️  {category_name} ({category.agent_type})")
            print(f"   {category.description}")
            print(f"   Events: {len(category.events)}")
            
            for event_name, event in category.events.items():
                impact_icon = "✅" if event.emotional_impact == "positive" else "❌" if event.emotional_impact == "negative" else "⚪"
                print(f"   {impact_icon} {event_name}: {event.description}")
        
        print(f"\n📊 Total: {len(self.events_by_name)} events across {len(self.categories)} categories")

# Example usage and testing
if __name__ == "__main__":
    # Test the event manager
    try:
        manager = EventManager()
        manager.print_summary()
        
        # Test specific lookups
        print(f"\n🔍 Testing Event Lookups:")
        
        # Test weather events
        weather_events = manager.get_weather_events()
        print(f"Weather events: {[e.name for e in weather_events]}")
        
        # Test role weights
        clam_weights = manager.get_role_weights("clam")
        print(f"Clam role weights: {clam_weights}")
        
        # Test emotional tags
        positive_tags = manager.get_emotional_tags("positive")
        print(f"Positive emotional tags: {positive_tags}")
        
        # Test event validation
        test_event_data = {
            "weather_data": {"temperature": 25, "condition": "Clear"},
            "user_preferences": {"favorite_weathers": ["Clear", "Sunny"]}
        }
        
        is_valid = manager.validate_event("favorite_weather", test_event_data)
        print(f"Event validation result: {is_valid}")
        
    except Exception as e:
        print(f"❌ Error testing event manager: {e}")