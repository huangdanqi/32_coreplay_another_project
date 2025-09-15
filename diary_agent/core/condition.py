"""
Condition checking system for diary generation triggers.

This module implements the ConditionChecker class that evaluates trigger conditions
for diary generation based on events, time, and image inputs.
"""

import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
import os
from PIL import Image
import io
import base64

try:
    from ..utils.data_models import EventData, DailyQuota, ClaimedEvent
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_models import EventData, DailyQuota, ClaimedEvent


class ConditionType(Enum):
    """Types of conditions that can trigger diary generation."""
    EVENT_BASED = "event_based"
    TIME_BASED = "time_based"
    IMAGE_BASED = "image_based"
    CLAIMED_EVENT = "claimed_event"


@dataclass
class TriggerCondition:
    """Represents a trigger condition for diary generation."""
    condition_id: str
    condition_type: ConditionType
    event_types: List[str]  # Event types this condition applies to
    time_range: Optional[tuple] = None  # (start_time, end_time) for time-based
    probability: float = 1.0  # Probability of triggering (0.0-1.0)
    is_active: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ConditionChecker:
    """
    Evaluates trigger conditions for diary generation.
    
    Handles event-based, time-based, and image-based condition evaluation
    to determine when diary entries should be generated.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConditionChecker.
        
        Args:
            config_path: Path to condition configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.conditions: List[TriggerCondition] = []
        self.claimed_events: List[ClaimedEvent] = []
        self.daily_quota: Optional[DailyQuota] = None
        self.event_handlers: Dict[str, Callable] = {}
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self.load_configuration(config_path)
        else:
            self._load_default_conditions()
    
    def load_configuration(self, config_path: str) -> None:
        """
        Load condition configuration from file.
        
        Args:
            config_path: Path to JSON configuration file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load trigger conditions
            for condition_data in config.get('trigger_conditions', []):
                condition = TriggerCondition(
                    condition_id=condition_data['condition_id'],
                    condition_type=ConditionType(condition_data['condition_type']),
                    event_types=condition_data['event_types'],
                    time_range=tuple(condition_data['time_range']) if condition_data.get('time_range') else None,
                    probability=condition_data.get('probability', 1.0),
                    is_active=condition_data.get('is_active', True),
                    metadata=condition_data.get('metadata', {})
                )
                self.conditions.append(condition)
            
            # Load claimed events
            for claimed_data in config.get('claimed_events', []):
                claimed_event = ClaimedEvent(
                    event_type=claimed_data['event_type'],
                    event_name=claimed_data['event_name'],
                    is_claimed=claimed_data.get('is_claimed', True)
                )
                self.claimed_events.append(claimed_event)
            
            self.logger.info(f"Loaded {len(self.conditions)} conditions and {len(self.claimed_events)} claimed events")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_path}: {e}")
            self._load_default_conditions()
    
    def _load_default_conditions(self) -> None:
        """Load default trigger conditions."""
        # Default claimed events (must always generate diary entries)
        claimed_event_types = [
            ("weather", "favorite_weather"),
            ("weather", "dislike_weather"),
            ("seasonal", "favorite_season"),
            ("seasonal", "dislike_season"),
            ("adoption", "toy_claimed"),
            ("dialogue", "positive_emotional_dialogue"),
            ("dialogue", "negative_emotional_dialogue")
        ]
        
        for event_type, event_name in claimed_event_types:
            self.claimed_events.append(ClaimedEvent(
                event_type=event_type,
                event_name=event_name,
                is_claimed=True
            ))
        
        # Default trigger conditions
        default_conditions = [
            TriggerCondition(
                condition_id="weather_events",
                condition_type=ConditionType.EVENT_BASED,
                event_types=["weather", "seasonal"],
                probability=1.0  # Always trigger for weather events
            ),
            TriggerCondition(
                condition_id="social_events",
                condition_type=ConditionType.EVENT_BASED,
                event_types=["friends", "same_frequency", "interactive"],
                probability=0.7  # 70% chance to trigger
            ),
            TriggerCondition(
                condition_id="trending_events",
                condition_type=ConditionType.EVENT_BASED,
                event_types=["trending"],
                probability=0.5  # 50% chance to trigger
            ),
            TriggerCondition(
                condition_id="daily_check",
                condition_type=ConditionType.TIME_BASED,
                event_types=["all"],
                time_range=(time(0, 0), time(0, 1)),  # 00:00-00:01 for daily quota reset
                probability=1.0
            )
        ]
        
        self.conditions.extend(default_conditions)
        self.logger.info("Loaded default conditions")
    
    def set_daily_quota(self, quota: DailyQuota) -> None:
        """
        Set the daily diary generation quota.
        
        Args:
            quota: Daily quota configuration
        """
        self.daily_quota = quota
        self.logger.info(f"Set daily quota: {quota.total_quota} entries for {quota.date}")
    
    def evaluate_conditions(self, event_data: EventData) -> bool:
        """
        Evaluate if conditions are met for diary generation.
        
        Args:
            event_data: Event data to evaluate
            
        Returns:
            True if conditions are met, False otherwise
        """
        try:
            # Check if this is a claimed event (must always generate diary)
            if self._is_claimed_event(event_data):
                self.logger.info(f"Claimed event detected: {event_data.event_type}.{event_data.event_name}")
                return True
            
            # Check daily quota
            if not self._check_daily_quota(event_data.event_type):
                self.logger.debug(f"Daily quota exceeded or event type already completed: {event_data.event_type}")
                return False
            
            # Evaluate trigger conditions
            for condition in self.conditions:
                if self._evaluate_condition(condition, event_data):
                    self.logger.info(f"Condition met: {condition.condition_id} for event {event_data.event_name}")
                    return True
            
            self.logger.debug(f"No conditions met for event: {event_data.event_name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating conditions for event {event_data.event_name}: {e}")
            return False
    
    def _is_claimed_event(self, event_data: EventData) -> bool:
        """
        Check if this is a claimed event that must generate a diary entry.
        
        Args:
            event_data: Event data to check
            
        Returns:
            True if this is a claimed event
        """
        for claimed in self.claimed_events:
            if (claimed.event_type == event_data.event_type and 
                claimed.event_name == event_data.event_name and 
                claimed.is_claimed):
                return True
        return False
    
    def _check_daily_quota(self, event_type: str) -> bool:
        """
        Check if daily quota allows for diary generation.
        
        Args:
            event_type: Type of event
            
        Returns:
            True if quota allows generation
        """
        if not self.daily_quota:
            return True  # No quota set, allow generation
        
        return self.daily_quota.can_generate_diary(event_type)
    
    def _evaluate_condition(self, condition: TriggerCondition, event_data: EventData) -> bool:
        """
        Evaluate a specific trigger condition.
        
        Args:
            condition: Condition to evaluate
            event_data: Event data
            
        Returns:
            True if condition is met
        """
        if not condition.is_active:
            return False
        
        # Check if event type matches
        if (condition.event_types != ["all"] and 
            event_data.event_type not in condition.event_types):
            return False
        
        # Evaluate based on condition type
        if condition.condition_type == ConditionType.EVENT_BASED:
            return self._evaluate_event_condition(condition, event_data)
        elif condition.condition_type == ConditionType.TIME_BASED:
            return self._evaluate_time_condition(condition, event_data)
        elif condition.condition_type == ConditionType.IMAGE_BASED:
            return self._evaluate_image_condition(condition, event_data)
        
        return False
    
    def _evaluate_event_condition(self, condition: TriggerCondition, event_data: EventData) -> bool:
        """
        Evaluate event-based condition.
        
        Args:
            condition: Event condition
            event_data: Event data
            
        Returns:
            True if condition is met
        """
        import random
        
        # Check probability
        if random.random() > condition.probability:
            self.logger.debug(f"Event condition failed probability check: {condition.probability}")
            return False
        
        # Additional event-specific logic can be added here
        return True
    
    def _evaluate_time_condition(self, condition: TriggerCondition, event_data: EventData) -> bool:
        """
        Evaluate time-based condition.
        
        Args:
            condition: Time condition
            event_data: Event data
            
        Returns:
            True if condition is met
        """
        if not condition.time_range:
            return True
        
        current_time = event_data.timestamp.time()
        start_time, end_time = condition.time_range
        
        # Handle time range that crosses midnight
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            return current_time >= start_time or current_time <= end_time
    
    def _evaluate_image_condition(self, condition: TriggerCondition, event_data: EventData) -> bool:
        """
        Evaluate image-based condition.
        
        Args:
            condition: Image condition
            event_data: Event data
            
        Returns:
            True if condition is met
        """
        # Check if event contains image data
        image_data = event_data.context_data.get('image_data')
        if not image_data:
            return False
        
        try:
            # Process image for event detection
            event_info = self.process_image_for_events(image_data)
            
            # Check if extracted events match condition requirements
            if event_info and event_info.get('detected_events'):
                detected_types = [evt.get('type') for evt in event_info['detected_events']]
                return any(evt_type in condition.event_types for evt_type in detected_types)
            
        except Exception as e:
            self.logger.error(f"Error processing image condition: {e}")
        
        return False
    
    def process_image_for_events(self, image_data: Any) -> Optional[Dict[str, Any]]:
        """
        Process image input to extract event information.
        
        Args:
            image_data: Image data (base64 string, bytes, or PIL Image)
            
        Returns:
            Dictionary containing extracted event information
        """
        try:
            # Convert image data to PIL Image
            image = self._convert_to_pil_image(image_data)
            if not image:
                return None
            
            # Basic image analysis for event detection
            # This is a simplified implementation - in practice, you might use
            # computer vision models or AI services for more sophisticated detection
            
            event_info = {
                'image_size': image.size,
                'image_mode': image.mode,
                'detected_events': [],
                'confidence': 0.0,
                'timestamp': datetime.now()
            }
            
            # Placeholder for actual image analysis logic
            # In a real implementation, this would use ML models to detect:
            # - Weather conditions from images
            # - Social interactions
            # - Objects and activities
            # - Emotional expressions
            
            # For now, return basic image metadata
            self.logger.info(f"Processed image: {image.size} pixels, mode: {image.mode}")
            
            return event_info
            
        except Exception as e:
            self.logger.error(f"Error processing image for events: {e}")
            return None
    
    def _convert_to_pil_image(self, image_data: Any) -> Optional[Image.Image]:
        """
        Convert various image data formats to PIL Image.
        
        Args:
            image_data: Image data in various formats
            
        Returns:
            PIL Image object or None if conversion fails
        """
        try:
            if isinstance(image_data, str):
                # Assume base64 encoded image
                image_bytes = base64.b64decode(image_data)
                return Image.open(io.BytesIO(image_bytes))
            elif isinstance(image_data, bytes):
                return Image.open(io.BytesIO(image_data))
            elif isinstance(image_data, Image.Image):
                return image_data
            else:
                self.logger.warning(f"Unsupported image data type: {type(image_data)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting image data: {e}")
            return None
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler for specific event types.
        
        Args:
            event_type: Type of event to handle
            handler: Callable to handle the event
        """
        self.event_handlers[event_type] = handler
        self.logger.info(f"Registered event handler for: {event_type}")
    
    def trigger_diary_generation(self, event_data: EventData) -> bool:
        """
        Trigger diary generation if conditions are met.
        
        Args:
            event_data: Event data to process
            
        Returns:
            True if diary generation was triggered
        """
        if self.evaluate_conditions(event_data):
            # Update daily quota if applicable
            if self.daily_quota and not self._is_claimed_event(event_data):
                self.daily_quota.add_diary_entry(event_data.event_type)
            
            # Call registered event handler if available
            handler = self.event_handlers.get(event_data.event_type)
            if handler:
                try:
                    handler(event_data)
                    self.logger.info(f"Triggered diary generation for: {event_data.event_name}")
                    return True
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_data.event_type}: {e}")
            else:
                self.logger.warning(f"No handler registered for event type: {event_data.event_type}")
            
            return True
        
        return False
    
    def get_active_conditions(self) -> List[TriggerCondition]:
        """
        Get list of currently active conditions.
        
        Returns:
            List of active trigger conditions
        """
        return [condition for condition in self.conditions if condition.is_active]
    
    def update_condition_status(self, condition_id: str, is_active: bool) -> bool:
        """
        Update the active status of a condition.
        
        Args:
            condition_id: ID of condition to update
            is_active: New active status
            
        Returns:
            True if condition was found and updated
        """
        for condition in self.conditions:
            if condition.condition_id == condition_id:
                condition.is_active = is_active
                self.logger.info(f"Updated condition {condition_id} active status to: {is_active}")
                return True
        
        self.logger.warning(f"Condition not found: {condition_id}")
        return False