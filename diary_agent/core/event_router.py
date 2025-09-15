"""
Event routing and classification system for the diary agent.

This module handles:
- Event type classification based on events.json
- Event metadata parsing and validation
- Routing logic to map events to appropriate sub-agents
- Query function calling system
- Claimed events identification
- Random diary selection logic for non-claimed events
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from ..utils.data_models import EventData, DiaryContextData, DailyQuota, ClaimedEvent
from ..utils.event_mapper import EventMapper
from ..utils.validators import EventValidator


class EventRouter:
    """
    Routes events to appropriate sub-agents based on event type classification.
    
    Handles event processing workflow including:
    - Event validation and metadata parsing
    - Agent type determination
    - Query function calling for event context
    - Claimed event processing
    - Random diary selection for non-claimed events
    """
    
    def __init__(self, 
                 events_json_path: str = "diary_agent/events.json",
                 daily_quota: Optional[DailyQuota] = None):
        """
        Initialize the EventRouter.
        
        Args:
            events_json_path: Path to events.json configuration file
            daily_quota: Daily diary generation quota (optional)
        """
        self.event_mapper = EventMapper(events_json_path)
        self.validator = EventValidator()
        self.daily_quota = daily_quota or DailyQuota(
            date=datetime.now().date(),
            total_quota=random.randint(0, 5)
        )
        
        # Query function registry for calling corresponding query functions
        self.query_functions: Dict[str, Callable] = {}
        
        # Agent registry for routing to appropriate agents
        self.agent_registry: Dict[str, Any] = {}
        
        # Claimed events cache
        self._claimed_events_cache: Optional[List[str]] = None
    
    def register_query_function(self, event_type: str, query_func: Callable):
        """
        Register a query function for a specific event type.
        
        Args:
            event_type: Event type (e.g., "weather_events", "friends_function")
            query_func: Function to call for querying event context
        """
        self.query_functions[event_type] = query_func
    
    def register_agent(self, agent_type: str, agent_instance: Any):
        """
        Register a sub-agent instance for routing.
        
        Args:
            agent_type: Agent type (e.g., "weather_agent", "friends_agent")
            agent_instance: Agent instance to handle events
        """
        self.agent_registry[agent_type] = agent_instance
    
    def route_event(self, event_data: EventData) -> Optional[Dict[str, Any]]:
        """
        Route an event to the appropriate sub-agent for processing.
        
        Args:
            event_data: Event data to route
            
        Returns:
            Dictionary containing routing result or None if routing failed
        """
        try:
            # Step 1: Validate event data
            if not self.validator.validate_event_data(event_data):
                return {
                    "success": False,
                    "error": "Event data validation failed",
                    "event_id": event_data.event_id
                }
            
            # Step 2: Classify event and determine agent type
            classification_result = self.classify_event(event_data)
            if not classification_result["success"]:
                return classification_result
            
            event_type = classification_result["event_type"]
            agent_type = classification_result["agent_type"]
            
            # Step 3: Check if diary should be generated for this event
            should_generate = self.should_generate_diary(event_data, event_type)
            if not should_generate:
                return {
                    "success": True,
                    "action": "skipped",
                    "reason": "Daily quota reached or event type already processed",
                    "event_id": event_data.event_id
                }
            
            # Step 4: Call query function to get event context
            context_data = self.call_query_function(event_type, event_data)
            if context_data is None:
                return {
                    "success": False,
                    "error": "Failed to retrieve event context",
                    "event_id": event_data.event_id
                }
            
            # Step 5: Route to appropriate agent
            agent_result = self.route_to_agent(agent_type, event_data, context_data)
            
            # Step 6: Update daily quota if diary was generated
            if agent_result.get("success") and agent_result.get("diary_generated"):
                self.daily_quota.add_diary_entry(event_type)
            
            return agent_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Event routing failed: {str(e)}",
                "event_id": event_data.event_id
            }
    
    def classify_event(self, event_data: EventData) -> Dict[str, Any]:
        """
        Classify event and determine appropriate agent type.
        
        Args:
            event_data: Event data to classify
            
        Returns:
            Dictionary containing classification results
        """
        event_name = event_data.event_name
        
        # Get event type from event mapper
        event_type = self.event_mapper.get_event_type_for_event(event_name)
        if event_type is None:
            return {
                "success": False,
                "error": f"Unknown event name: {event_name}",
                "event_id": event_data.event_id
            }
        
        # Get corresponding agent type
        agent_type = self.event_mapper.get_agent_type_for_event(event_name)
        if agent_type is None:
            return {
                "success": False,
                "error": f"No agent mapped for event type: {event_type}",
                "event_id": event_data.event_id
            }
        
        # Parse and validate event metadata
        metadata = self.parse_event_metadata(event_data)
        
        return {
            "success": True,
            "event_type": event_type,
            "agent_type": agent_type,
            "metadata": metadata,
            "event_id": event_data.event_id
        }
    
    def parse_event_metadata(self, event_data: EventData) -> Dict[str, Any]:
        """
        Parse and validate event metadata.
        
        Args:
            event_data: Event data containing metadata
            
        Returns:
            Parsed and validated metadata dictionary
        """
        metadata = event_data.metadata.copy()
        
        # Add standard metadata fields
        metadata.update({
            "timestamp": event_data.timestamp.isoformat(),
            "user_id": event_data.user_id,
            "event_type": event_data.event_type,
            "event_name": event_data.event_name,
            "is_claimed": self.is_claimed_event(event_data.event_name),
            "source_module": self.event_mapper.get_source_module_for_event_type(
                self.event_mapper.get_event_type_for_event(event_data.event_name)
            )
        })
        
        return metadata
    
    def should_generate_diary(self, event_data: EventData, event_type: str) -> bool:
        """
        Determine if a diary should be generated for this event.
        
        Args:
            event_data: Event data
            event_type: Classified event type
            
        Returns:
            True if diary should be generated, False otherwise
        """
        # Always generate for claimed events
        if self.is_claimed_event(event_data.event_name):
            return True
        
        # Check daily quota constraints
        if not self.daily_quota.can_generate_diary(event_type):
            return False
        
        # Random selection for non-claimed events
        # Use probability based on remaining quota
        remaining_quota = self.daily_quota.total_quota - self.daily_quota.current_count
        if remaining_quota <= 0:
            return False
        
        # Higher probability when more quota remaining
        probability = min(0.8, remaining_quota / self.daily_quota.total_quota)
        return random.random() < probability
    
    def call_query_function(self, event_type: str, event_data: EventData) -> Optional[DiaryContextData]:
        """
        Call the corresponding query function to get event context.
        
        Args:
            event_type: Event type for function lookup
            event_data: Event data to pass to query function
            
        Returns:
            DiaryContextData with event context or None if failed
        """
        query_func = self.query_functions.get(event_type)
        if query_func is None:
            # Return basic context if no query function registered
            return DiaryContextData(
                user_profile={},
                event_details={"event_name": event_data.event_name},
                environmental_context={},
                social_context={},
                emotional_context={},
                temporal_context={"timestamp": event_data.timestamp}
            )
        
        try:
            # Call query function with event data as input parameter
            context_result = query_func(event_data)
            
            # Ensure result is DiaryContextData
            if isinstance(context_result, DiaryContextData):
                return context_result
            elif isinstance(context_result, dict):
                # Convert dict to DiaryContextData
                return DiaryContextData(
                    user_profile=context_result.get("user_profile", {}),
                    event_details=context_result.get("event_details", {}),
                    environmental_context=context_result.get("environmental_context", {}),
                    social_context=context_result.get("social_context", {}),
                    emotional_context=context_result.get("emotional_context", {}),
                    temporal_context=context_result.get("temporal_context", {})
                )
            else:
                return None
                
        except Exception as e:
            print(f"Error calling query function for {event_type}: {e}")
            return None
    
    def route_to_agent(self, agent_type: str, event_data: EventData, 
                      context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Route event to the appropriate sub-agent for processing.
        
        Args:
            agent_type: Type of agent to route to
            event_data: Event data
            context_data: Context data from query function
            
        Returns:
            Dictionary containing agent processing results
        """
        agent = self.agent_registry.get(agent_type)
        if agent is None:
            return {
                "success": False,
                "error": f"Agent not registered: {agent_type}",
                "event_id": event_data.event_id
            }
        
        try:
            # Call agent to process event and generate diary
            diary_entry = agent.process_event(event_data, context_data)
            
            return {
                "success": True,
                "agent_type": agent_type,
                "diary_entry": diary_entry,
                "diary_generated": diary_entry is not None,
                "event_id": event_data.event_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent processing failed: {str(e)}",
                "agent_type": agent_type,
                "event_id": event_data.event_id
            }
    
    def is_claimed_event(self, event_name: str) -> bool:
        """
        Check if an event is a claimed event (must result in diary entry).
        
        Args:
            event_name: Name of the event to check
            
        Returns:
            True if event is claimed, False otherwise
        """
        return self.event_mapper.is_claimed_event(event_name)
    
    def get_claimed_events(self) -> List[str]:
        """
        Get list of all claimed events.
        
        Returns:
            List of claimed event names
        """
        if self._claimed_events_cache is None:
            self._claimed_events_cache = self.event_mapper.get_claimed_events()
        return self._claimed_events_cache
    
    def update_daily_quota(self, new_quota: DailyQuota):
        """
        Update the daily diary generation quota.
        
        Args:
            new_quota: New daily quota configuration
        """
        self.daily_quota = new_quota
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """
        Get routing statistics for monitoring and debugging.
        
        Returns:
            Dictionary containing routing statistics
        """
        return {
            "daily_quota": {
                "date": self.daily_quota.date.isoformat(),
                "total_quota": self.daily_quota.total_quota,
                "current_count": self.daily_quota.current_count,
                "completed_event_types": self.daily_quota.completed_event_types
            },
            "registered_agents": list(self.agent_registry.keys()),
            "registered_query_functions": list(self.query_functions.keys()),
            "available_event_types": self.event_mapper.get_all_event_types(),
            "claimed_events": self.get_claimed_events()
        }
    
    def reset_daily_quota(self, new_quota: Optional[int] = None):
        """
        Reset daily quota for a new day.
        
        Args:
            new_quota: Specific quota to set, or None for random 0-5
        """
        quota = new_quota if new_quota is not None else random.randint(0, 5)
        self.daily_quota = DailyQuota(
            date=datetime.now().date(),
            total_quota=quota
        )
    
    def get_available_event_types_for_today(self) -> List[str]:
        """
        Get event types that can still generate diaries today.
        
        Returns:
            List of available event types
        """
        all_types = self.event_mapper.get_all_event_types()
        return [
            event_type for event_type in all_types
            if event_type not in self.daily_quota.completed_event_types
        ]
    
    def select_random_event_types_for_today(self) -> List[str]:
        """
        Alternative approach: Randomly select event types for today's diary generation.
        
        Returns:
            List of randomly selected event types for today
        """
        available_types = self.event_mapper.get_all_event_types()
        remaining_quota = self.daily_quota.total_quota - self.daily_quota.current_count
        
        if remaining_quota <= 0:
            return []
        
        # Randomly select event types up to remaining quota
        selected_count = min(remaining_quota, len(available_types))
        return random.sample(available_types, selected_count)