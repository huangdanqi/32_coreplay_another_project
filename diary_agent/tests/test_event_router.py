"""
Unit tests for the EventRouter class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import json
import tempfile
import os

from diary_agent.core.event_router import EventRouter
from diary_agent.utils.data_models import EventData, DiaryContextData, DailyQuota, DiaryEntry, EmotionalTag
from diary_agent.utils.event_mapper import EventMapper


class TestEventRouter(unittest.TestCase):
    """Test cases for EventRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary events.json for testing
        self.test_events = {
            "weather_events": ["favorite_weather", "dislike_weather"],
            "friends_function": ["made_new_friend", "friend_deleted"],
            "adopted_function": ["toy_claimed"]
        }
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_events, self.temp_file)
        self.temp_file.close()
        
        # Create test daily quota
        self.test_quota = DailyQuota(
            date=date.today(),
            total_quota=3,
            current_count=0
        )
        
        # Initialize router
        self.router = EventRouter(
            events_json_path=self.temp_file.name,
            daily_quota=self.test_quota
        )
        
        # Create mock agents
        self.mock_weather_agent = Mock()
        self.mock_friends_agent = Mock()
        self.mock_adoption_agent = Mock()
        
        # Register mock agents
        self.router.register_agent("weather_agent", self.mock_weather_agent)
        self.router.register_agent("friends_agent", self.mock_friends_agent)
        self.router.register_agent("adoption_agent", self.mock_adoption_agent)
        
        # Create mock query functions
        self.mock_weather_query = Mock()
        self.mock_friends_query = Mock()
        
        # Register mock query functions
        self.router.register_query_function("weather_events", self.mock_weather_query)
        self.router.register_query_function("friends_function", self.mock_friends_query)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_file.name)
    
    def create_test_event_data(self, event_name: str = "favorite_weather", 
                              user_id: int = 1) -> EventData:
        """Create test event data."""
        return EventData(
            event_id="test_event_001",
            event_type="weather_events",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={"test": "data"},
            metadata={"source": "test"}
        )
    
    def create_test_context_data(self) -> DiaryContextData:
        """Create test context data."""
        return DiaryContextData(
            user_profile={"role": "clam", "name": "test_user"},
            event_details={"weather": "sunny"},
            environmental_context={"temperature": 25},
            social_context={},
            emotional_context={"mood": "happy"},
            temporal_context={"time": "morning"}
        )
    
    def test_event_classification_success(self):
        """Test successful event classification."""
        event_data = self.create_test_event_data("favorite_weather")
        
        result = self.router.classify_event(event_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["event_type"], "weather_events")
        self.assertEqual(result["agent_type"], "weather_agent")
        self.assertIn("metadata", result)
    
    def test_event_classification_unknown_event(self):
        """Test event classification with unknown event name."""
        event_data = self.create_test_event_data("unknown_event")
        
        result = self.router.classify_event(event_data)
        
        self.assertFalse(result["success"])
        self.assertIn("Unknown event name", result["error"])
    
    def test_should_generate_diary_claimed_event(self):
        """Test diary generation decision for claimed events."""
        # Mock claimed event
        with patch.object(self.router, 'is_claimed_event', return_value=True):
            event_data = self.create_test_event_data("toy_claimed")
            
            should_generate = self.router.should_generate_diary(event_data, "adopted_function")
            
            self.assertTrue(should_generate)
    
    def test_should_generate_diary_quota_exceeded(self):
        """Test diary generation decision when quota is exceeded."""
        # Set quota to full
        self.router.daily_quota.current_count = 3
        self.router.daily_quota.total_quota = 3
        
        event_data = self.create_test_event_data("favorite_weather")
        
        should_generate = self.router.should_generate_diary(event_data, "weather_events")
        
        self.assertFalse(should_generate)
    
    def test_should_generate_diary_event_type_already_processed(self):
        """Test diary generation decision when event type already processed."""
        # Mark event type as completed
        self.router.daily_quota.completed_event_types.append("weather_events")
        
        event_data = self.create_test_event_data("favorite_weather")
        
        should_generate = self.router.should_generate_diary(event_data, "weather_events")
        
        self.assertFalse(should_generate)
    
    def test_call_query_function_success(self):
        """Test successful query function call."""
        event_data = self.create_test_event_data("favorite_weather")
        expected_context = self.create_test_context_data()
        
        self.mock_weather_query.return_value = expected_context
        
        result = self.router.call_query_function("weather_events", event_data)
        
        self.assertIsInstance(result, DiaryContextData)
        self.mock_weather_query.assert_called_once_with(event_data)
    
    def test_call_query_function_dict_return(self):
        """Test query function call with dictionary return."""
        event_data = self.create_test_event_data("favorite_weather")
        
        # Mock query function returning dict
        self.mock_weather_query.return_value = {
            "user_profile": {"role": "clam"},
            "event_details": {"weather": "sunny"}
        }
        
        result = self.router.call_query_function("weather_events", event_data)
        
        self.assertIsInstance(result, DiaryContextData)
        self.assertEqual(result.user_profile["role"], "clam")
    
    def test_call_query_function_no_function_registered(self):
        """Test query function call when no function is registered."""
        event_data = self.create_test_event_data("favorite_weather")
        
        result = self.router.call_query_function("unregistered_type", event_data)
        
        self.assertIsInstance(result, DiaryContextData)
        self.assertEqual(result.event_details["event_name"], "favorite_weather")
    
    def test_call_query_function_exception(self):
        """Test query function call with exception."""
        event_data = self.create_test_event_data("favorite_weather")
        
        self.mock_weather_query.side_effect = Exception("Query failed")
        
        result = self.router.call_query_function("weather_events", event_data)
        
        self.assertIsNone(result)
    
    def test_route_to_agent_success(self):
        """Test successful routing to agent."""
        event_data = self.create_test_event_data("favorite_weather")
        context_data = self.create_test_context_data()
        
        # Mock successful diary entry generation
        mock_diary_entry = DiaryEntry(
            entry_id="diary_001",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="favorite_weather",
            title="晴天",
            content="今天天气很好，心情愉快😊",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        self.mock_weather_agent.process_event.return_value = mock_diary_entry
        
        result = self.router.route_to_agent("weather_agent", event_data, context_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["agent_type"], "weather_agent")
        self.assertTrue(result["diary_generated"])
        self.assertEqual(result["diary_entry"], mock_diary_entry)
    
    def test_route_to_agent_not_registered(self):
        """Test routing to unregistered agent."""
        event_data = self.create_test_event_data("favorite_weather")
        context_data = self.create_test_context_data()
        
        result = self.router.route_to_agent("unregistered_agent", event_data, context_data)
        
        self.assertFalse(result["success"])
        self.assertIn("Agent not registered", result["error"])
    
    def test_route_to_agent_processing_exception(self):
        """Test routing to agent with processing exception."""
        event_data = self.create_test_event_data("favorite_weather")
        context_data = self.create_test_context_data()
        
        self.mock_weather_agent.process_event.side_effect = Exception("Processing failed")
        
        result = self.router.route_to_agent("weather_agent", event_data, context_data)
        
        self.assertFalse(result["success"])
        self.assertIn("Agent processing failed", result["error"])
    
    def test_route_event_full_workflow_success(self):
        """Test complete event routing workflow."""
        event_data = self.create_test_event_data("favorite_weather")
        context_data = self.create_test_context_data()
        
        # Mock query function
        self.mock_weather_query.return_value = context_data
        
        # Mock agent processing
        mock_diary_entry = DiaryEntry(
            entry_id="diary_001",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="favorite_weather",
            title="晴天",
            content="今天天气很好，心情愉快😊",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        self.mock_weather_agent.process_event.return_value = mock_diary_entry
        
        # Mock should_generate_diary to return True
        with patch.object(self.router, 'should_generate_diary', return_value=True):
            result = self.router.route_event(event_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["diary_entry"], mock_diary_entry)
        
        # Check that daily quota was updated
        self.assertEqual(self.router.daily_quota.current_count, 1)
        self.assertIn("weather_events", self.router.daily_quota.completed_event_types)
    
    def test_route_event_skipped_due_to_quota(self):
        """Test event routing skipped due to quota constraints."""
        event_data = self.create_test_event_data("favorite_weather")
        
        # Mock should_generate_diary to return False
        with patch.object(self.router, 'should_generate_diary', return_value=False):
            result = self.router.route_event(event_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "skipped")
    
    def test_route_event_validation_failure(self):
        """Test event routing with validation failure."""
        # Create invalid event data
        event_data = EventData(
            event_id="",  # Invalid empty ID
            event_type="weather_events",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = self.router.route_event(event_data)
        
        self.assertFalse(result["success"])
        self.assertIn("validation failed", result["error"])
    
    def test_parse_event_metadata(self):
        """Test event metadata parsing."""
        event_data = self.create_test_event_data("toy_claimed")
        
        # Mock is_claimed_event
        with patch.object(self.router, 'is_claimed_event', return_value=True):
            metadata = self.router.parse_event_metadata(event_data)
        
        self.assertEqual(metadata["user_id"], 1)
        self.assertEqual(metadata["event_name"], "toy_claimed")
        self.assertTrue(metadata["is_claimed"])
        self.assertIn("source_module", metadata)
    
    def test_is_claimed_event(self):
        """Test claimed event identification."""
        # Mock event mapper
        with patch.object(self.router.event_mapper, 'is_claimed_event') as mock_is_claimed:
            mock_is_claimed.return_value = True
            
            result = self.router.is_claimed_event("toy_claimed")
            
            self.assertTrue(result)
            mock_is_claimed.assert_called_once_with("toy_claimed")
    
    def test_get_claimed_events(self):
        """Test getting list of claimed events."""
        expected_claimed = ["toy_claimed"]
        
        with patch.object(self.router.event_mapper, 'get_claimed_events') as mock_get_claimed:
            mock_get_claimed.return_value = expected_claimed
            
            result = self.router.get_claimed_events()
            
            self.assertEqual(result, expected_claimed)
    
    def test_update_daily_quota(self):
        """Test updating daily quota."""
        new_quota = DailyQuota(
            date=date.today(),
            total_quota=5,
            current_count=2
        )
        
        self.router.update_daily_quota(new_quota)
        
        self.assertEqual(self.router.daily_quota.total_quota, 5)
        self.assertEqual(self.router.daily_quota.current_count, 2)
    
    def test_reset_daily_quota(self):
        """Test resetting daily quota."""
        # Set some initial state
        self.router.daily_quota.current_count = 3
        self.router.daily_quota.completed_event_types = ["weather_events"]
        
        self.router.reset_daily_quota(4)
        
        self.assertEqual(self.router.daily_quota.total_quota, 4)
        self.assertEqual(self.router.daily_quota.current_count, 0)
        self.assertEqual(self.router.daily_quota.completed_event_types, [])
    
    def test_reset_daily_quota_random(self):
        """Test resetting daily quota with random value."""
        self.router.reset_daily_quota()
        
        # Should be between 0 and 5
        self.assertGreaterEqual(self.router.daily_quota.total_quota, 0)
        self.assertLessEqual(self.router.daily_quota.total_quota, 5)
        self.assertEqual(self.router.daily_quota.current_count, 0)
    
    def test_get_routing_statistics(self):
        """Test getting routing statistics."""
        stats = self.router.get_routing_statistics()
        
        self.assertIn("daily_quota", stats)
        self.assertIn("registered_agents", stats)
        self.assertIn("registered_query_functions", stats)
        self.assertIn("available_event_types", stats)
        self.assertIn("claimed_events", stats)
        
        # Check specific values
        self.assertIn("weather_agent", stats["registered_agents"])
        self.assertIn("weather_events", stats["registered_query_functions"])
    
    def test_get_available_event_types_for_today(self):
        """Test getting available event types for today."""
        # Mark one event type as completed
        self.router.daily_quota.completed_event_types = ["weather_events"]
        
        available_types = self.router.get_available_event_types_for_today()
        
        self.assertNotIn("weather_events", available_types)
        self.assertIn("friends_function", available_types)
        self.assertIn("adopted_function", available_types)
    
    def test_select_random_event_types_for_today(self):
        """Test selecting random event types for today."""
        # Set quota to 2 with 0 current count
        self.router.daily_quota.total_quota = 2
        self.router.daily_quota.current_count = 0
        
        selected_types = self.router.select_random_event_types_for_today()
        
        self.assertLessEqual(len(selected_types), 2)
        
        # All selected types should be valid
        all_types = self.router.event_mapper.get_all_event_types()
        for selected_type in selected_types:
            self.assertIn(selected_type, all_types)
    
    def test_select_random_event_types_no_quota(self):
        """Test selecting random event types when no quota remaining."""
        # Set quota to full
        self.router.daily_quota.total_quota = 3
        self.router.daily_quota.current_count = 3
        
        selected_types = self.router.select_random_event_types_for_today()
        
        self.assertEqual(len(selected_types), 0)


class TestEventRouterIntegration(unittest.TestCase):
    """Integration tests for EventRouter with real components."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Use real events.json file
        self.router = EventRouter("diary_agent/events.json")
    
    def test_real_events_json_loading(self):
        """Test loading real events.json file."""
        # Should load without errors
        self.assertIsNotNone(self.router.event_mapper)
        
        # Should have expected event types
        event_types = self.router.event_mapper.get_all_event_types()
        expected_types = [
            "weather_events", "seasonal_events", "trending_events",
            "holiday_events", "friends_function", "same_frequency",
            "adopted_function", "human_toy_interactive_function",
            "human_toy_talk", "unkeep_interactive"
        ]
        
        for expected_type in expected_types:
            self.assertIn(expected_type, event_types)
    
    def test_real_event_classification(self):
        """Test event classification with real events."""
        test_cases = [
            ("favorite_weather", "weather_events", "weather_agent"),
            ("made_new_friend", "friends_function", "friends_agent"),
            ("toy_claimed", "adopted_function", "adoption_agent"),
            ("positive_emotional_dialogue", "human_toy_talk", "dialogue_agent")
        ]
        
        for event_name, expected_event_type, expected_agent_type in test_cases:
            event_data = EventData(
                event_id=f"test_{event_name}",
                event_type=expected_event_type,
                event_name=event_name,
                timestamp=datetime.now(),
                user_id=1,
                context_data={},
                metadata={}
            )
            
            result = self.router.classify_event(event_data)
            
            self.assertTrue(result["success"], f"Failed for event: {event_name}")
            self.assertEqual(result["event_type"], expected_event_type)
            self.assertEqual(result["agent_type"], expected_agent_type)


if __name__ == '__main__':
    unittest.main()