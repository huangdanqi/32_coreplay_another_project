"""
Unit tests for the ConditionChecker class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time, date
import json
import tempfile
import os
from PIL import Image
import io
import base64

from diary_agent.core.condition import (
    ConditionChecker, 
    ConditionType, 
    TriggerCondition
)
from diary_agent.utils.data_models import (
    EventData, 
    DailyQuota, 
    ClaimedEvent
)


class TestConditionChecker(unittest.TestCase):
    """Test cases for ConditionChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.condition_checker = ConditionChecker()
        
        # Sample event data
        self.sample_event = EventData(
            event_id="test_001",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"temperature": 25, "condition": "sunny"},
            metadata={"source": "weather_api"}
        )
        
        # Sample daily quota
        self.daily_quota = DailyQuota(
            date=datetime.now(),
            total_quota=3,
            current_count=0
        )
    
    def test_initialization_default(self):
        """Test ConditionChecker initialization with default conditions."""
        checker = ConditionChecker()
        
        # Should have default conditions loaded
        self.assertGreater(len(checker.conditions), 0)
        self.assertGreater(len(checker.claimed_events), 0)
        
        # Check for expected default conditions
        condition_ids = [c.condition_id for c in checker.conditions]
        self.assertIn("weather_events", condition_ids)
        self.assertIn("social_events", condition_ids)
    
    def test_initialization_with_config(self):
        """Test ConditionChecker initialization with configuration file."""
        # Create temporary config file
        config_data = {
            "trigger_conditions": [
                {
                    "condition_id": "test_condition",
                    "condition_type": "event_based",
                    "event_types": ["test"],
                    "probability": 0.8,
                    "is_active": True,
                    "metadata": {"test": True}
                }
            ],
            "claimed_events": [
                {
                    "event_type": "test",
                    "event_name": "test_event",
                    "is_claimed": True
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            checker = ConditionChecker(config_path)
            
            # Should have loaded the test condition
            condition_ids = [c.condition_id for c in checker.conditions]
            self.assertIn("test_condition", condition_ids)
            
            # Should have loaded the claimed event
            claimed_events = [(c.event_type, c.event_name) for c in checker.claimed_events]
            self.assertIn(("test", "test_event"), claimed_events)
            
        finally:
            os.unlink(config_path)
    
    def test_set_daily_quota(self):
        """Test setting daily quota."""
        self.condition_checker.set_daily_quota(self.daily_quota)
        
        self.assertEqual(self.condition_checker.daily_quota, self.daily_quota)
    
    def test_is_claimed_event(self):
        """Test claimed event detection."""
        # Test with a claimed event
        claimed_event = EventData(
            event_id="claimed_001",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = self.condition_checker._is_claimed_event(claimed_event)
        self.assertTrue(result)
        
        # Test with a non-claimed event
        non_claimed_event = EventData(
            event_id="non_claimed_001",
            event_type="test",
            event_name="test_event",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = self.condition_checker._is_claimed_event(non_claimed_event)
        self.assertFalse(result)
    
    def test_check_daily_quota(self):
        """Test daily quota checking."""
        # Test without quota set
        result = self.condition_checker._check_daily_quota("weather")
        self.assertTrue(result)
        
        # Test with quota set
        self.condition_checker.set_daily_quota(self.daily_quota)
        
        # Should allow generation when quota not exceeded
        result = self.condition_checker._check_daily_quota("weather")
        self.assertTrue(result)
        
        # Simulate quota exceeded
        self.daily_quota.current_count = 3
        result = self.condition_checker._check_daily_quota("weather")
        self.assertFalse(result)
        
        # Test event type already completed
        self.daily_quota.current_count = 1
        self.daily_quota.completed_event_types = ["weather"]
        result = self.condition_checker._check_daily_quota("weather")
        self.assertFalse(result)
    
    def test_evaluate_event_condition(self):
        """Test event-based condition evaluation."""
        condition = TriggerCondition(
            condition_id="test_event",
            condition_type=ConditionType.EVENT_BASED,
            event_types=["weather"],
            probability=1.0
        )
        
        # Should pass with matching event type and 100% probability
        result = self.condition_checker._evaluate_event_condition(condition, self.sample_event)
        self.assertTrue(result)
        
        # Test with low probability (mock random to return high value)
        condition.probability = 0.1
        with patch('random.random', return_value=0.9):
            result = self.condition_checker._evaluate_event_condition(condition, self.sample_event)
            self.assertFalse(result)
    
    def test_evaluate_time_condition(self):
        """Test time-based condition evaluation."""
        # Test condition that should match current time
        current_time = datetime.now().time()
        condition = TriggerCondition(
            condition_id="test_time",
            condition_type=ConditionType.TIME_BASED,
            event_types=["all"],
            time_range=(time(0, 0), time(23, 59))  # All day
        )
        
        result = self.condition_checker._evaluate_time_condition(condition, self.sample_event)
        self.assertTrue(result)
        
        # Test condition that should not match
        condition.time_range = (time(1, 0), time(2, 0))  # 1-2 AM only
        event_at_noon = EventData(
            event_id="noon_event",
            event_type="test",
            event_name="test",
            timestamp=datetime.now().replace(hour=12, minute=0),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = self.condition_checker._evaluate_time_condition(condition, event_at_noon)
        self.assertFalse(result)
    
    def test_evaluate_time_condition_cross_midnight(self):
        """Test time condition that crosses midnight."""
        condition = TriggerCondition(
            condition_id="cross_midnight",
            condition_type=ConditionType.TIME_BASED,
            event_types=["all"],
            time_range=(time(23, 0), time(1, 0))  # 11 PM to 1 AM
        )
        
        # Test at 11:30 PM
        late_event = EventData(
            event_id="late_event",
            event_type="test",
            event_name="test",
            timestamp=datetime.now().replace(hour=23, minute=30),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = self.condition_checker._evaluate_time_condition(condition, late_event)
        self.assertTrue(result)
        
        # Test at 12:30 AM
        early_event = EventData(
            event_id="early_event",
            event_type="test",
            event_name="test",
            timestamp=datetime.now().replace(hour=0, minute=30),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = self.condition_checker._evaluate_time_condition(condition, early_event)
        self.assertTrue(result)
    
    def test_evaluate_image_condition(self):
        """Test image-based condition evaluation."""
        condition = TriggerCondition(
            condition_id="test_image",
            condition_type=ConditionType.IMAGE_BASED,
            event_types=["weather"],
            probability=1.0
        )
        
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Event with image data
        image_event = EventData(
            event_id="image_event",
            event_type="weather",
            event_name="test_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"image_data": img_data},
            metadata={}
        )
        
        # Mock the process_image_for_events method to return detected events
        with patch.object(self.condition_checker, 'process_image_for_events') as mock_process:
            mock_process.return_value = {
                'detected_events': [{'type': 'weather', 'confidence': 0.8}]
            }
            
            result = self.condition_checker._evaluate_image_condition(condition, image_event)
            self.assertTrue(result)
        
        # Test with no image data
        result = self.condition_checker._evaluate_image_condition(condition, self.sample_event)
        self.assertFalse(result)
    
    def test_process_image_for_events(self):
        """Test image processing for event detection."""
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='blue')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        
        result = self.condition_checker.process_image_for_events(img_data)
        
        self.assertIsNotNone(result)
        self.assertIn('image_size', result)
        self.assertIn('image_mode', result)
        self.assertIn('detected_events', result)
        self.assertEqual(result['image_size'], (100, 100))
        self.assertEqual(result['image_mode'], 'RGB')
    
    def test_convert_to_pil_image(self):
        """Test image conversion to PIL format."""
        # Test with base64 string
        test_image = Image.new('RGB', (50, 50), color='green')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        
        result = self.condition_checker._convert_to_pil_image(img_data)
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (50, 50))
        
        # Test with bytes
        img_buffer.seek(0)
        img_bytes = img_buffer.getvalue()
        result = self.condition_checker._convert_to_pil_image(img_bytes)
        self.assertIsInstance(result, Image.Image)
        
        # Test with PIL Image
        result = self.condition_checker._convert_to_pil_image(test_image)
        self.assertEqual(result, test_image)
        
        # Test with invalid data
        result = self.condition_checker._convert_to_pil_image("invalid_data")
        self.assertIsNone(result)
    
    def test_evaluate_conditions_claimed_event(self):
        """Test condition evaluation for claimed events."""
        # Claimed events should always return True
        result = self.condition_checker.evaluate_conditions(self.sample_event)
        self.assertTrue(result)
    
    def test_evaluate_conditions_quota_exceeded(self):
        """Test condition evaluation when quota is exceeded."""
        # Set up quota that's exceeded
        quota = DailyQuota(
            date=datetime.now(),
            total_quota=1,
            current_count=1,
            completed_event_types=["weather"]
        )
        self.condition_checker.set_daily_quota(quota)
        
        # Non-claimed event should fail when quota exceeded
        non_claimed_event = EventData(
            event_id="non_claimed",
            event_type="friends",
            event_name="made_new_friend",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = self.condition_checker.evaluate_conditions(non_claimed_event)
        self.assertFalse(result)
    
    def test_register_event_handler(self):
        """Test event handler registration."""
        mock_handler = Mock()
        
        self.condition_checker.register_event_handler("weather", mock_handler)
        
        self.assertIn("weather", self.condition_checker.event_handlers)
        self.assertEqual(self.condition_checker.event_handlers["weather"], mock_handler)
    
    def test_trigger_diary_generation(self):
        """Test diary generation triggering."""
        mock_handler = Mock()
        self.condition_checker.register_event_handler("weather", mock_handler)
        self.condition_checker.set_daily_quota(self.daily_quota)
        
        # Should trigger for claimed event
        result = self.condition_checker.trigger_diary_generation(self.sample_event)
        self.assertTrue(result)
        mock_handler.assert_called_once_with(self.sample_event)
        
        # Should not update quota for claimed events
        self.assertEqual(self.daily_quota.current_count, 0)
    
    def test_trigger_diary_generation_non_claimed(self):
        """Test diary generation for non-claimed events."""
        mock_handler = Mock()
        self.condition_checker.register_event_handler("friends", mock_handler)
        self.condition_checker.set_daily_quota(self.daily_quota)
        
        non_claimed_event = EventData(
            event_id="friend_event",
            event_type="friends",
            event_name="made_new_friend",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        # Mock condition evaluation to return True
        with patch.object(self.condition_checker, 'evaluate_conditions', return_value=True):
            result = self.condition_checker.trigger_diary_generation(non_claimed_event)
            self.assertTrue(result)
            mock_handler.assert_called_once_with(non_claimed_event)
            
            # Should update quota for non-claimed events
            self.assertEqual(self.daily_quota.current_count, 1)
            self.assertIn("friends", self.daily_quota.completed_event_types)
    
    def test_get_active_conditions(self):
        """Test getting active conditions."""
        # Add an inactive condition
        inactive_condition = TriggerCondition(
            condition_id="inactive_test",
            condition_type=ConditionType.EVENT_BASED,
            event_types=["test"],
            is_active=False
        )
        self.condition_checker.conditions.append(inactive_condition)
        
        active_conditions = self.condition_checker.get_active_conditions()
        
        # Should not include inactive condition
        active_ids = [c.condition_id for c in active_conditions]
        self.assertNotIn("inactive_test", active_ids)
        
        # Should include active conditions
        self.assertIn("weather_events", active_ids)
    
    def test_update_condition_status(self):
        """Test updating condition status."""
        # Update existing condition
        result = self.condition_checker.update_condition_status("weather_events", False)
        self.assertTrue(result)
        
        # Check that condition is now inactive
        weather_condition = next(
            (c for c in self.condition_checker.conditions if c.condition_id == "weather_events"),
            None
        )
        self.assertIsNotNone(weather_condition)
        self.assertFalse(weather_condition.is_active)
        
        # Try to update non-existent condition
        result = self.condition_checker.update_condition_status("non_existent", True)
        self.assertFalse(result)
    
    def test_evaluate_condition_inactive(self):
        """Test that inactive conditions are not evaluated."""
        inactive_condition = TriggerCondition(
            condition_id="inactive",
            condition_type=ConditionType.EVENT_BASED,
            event_types=["weather"],
            is_active=False
        )
        
        result = self.condition_checker._evaluate_condition(inactive_condition, self.sample_event)
        self.assertFalse(result)
    
    def test_evaluate_condition_wrong_event_type(self):
        """Test condition evaluation with wrong event type."""
        condition = TriggerCondition(
            condition_id="wrong_type",
            condition_type=ConditionType.EVENT_BASED,
            event_types=["friends"],  # Different from sample_event type
            is_active=True
        )
        
        result = self.condition_checker._evaluate_condition(condition, self.sample_event)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()