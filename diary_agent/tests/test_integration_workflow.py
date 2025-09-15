"""
Integration tests for complete event processing workflow.
Tests the end-to-end flow from event detection to diary entry generation.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from diary_agent.core.dairy_agent_controller import DairyAgentController
from diary_agent.core.event_router import EventRouter
from diary_agent.core.condition import ConditionChecker
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.core.diary_entry_generator import DiaryEntryGenerator
from diary_agent.integration.database_manager import DatabaseManager
from diary_agent.utils.data_models import EventData, DiaryEntry, LLMConfig
from diary_agent.tests.test_data_generators import DiaryTestDataGenerator, DiaryPerformanceTestDataGenerator


class TestIntegrationWorkflow:
    """Integration tests for complete diary agent workflow."""
    
    @pytest.fixture
    def test_data_generator(self):
        """Fixture for test data generator."""
        return DiaryTestDataGenerator()
    
    @pytest.fixture
    def performance_generator(self):
        """Fixture for performance test data generator."""
        return DiaryPerformanceTestDataGenerator()
    
    @pytest.fixture
    def mock_llm_config(self):
        """Fixture for mock LLM configuration."""
        return LLMConfig(
            provider_name="test_provider",
            api_endpoint="http://test.api",
            api_key="test_key",
            model_name="test_model",
            max_tokens=100,
            temperature=0.7,
            timeout=30,
            retry_attempts=3
        )
    
    @pytest.fixture
    def mock_database_manager(self):
        """Fixture for mock database manager."""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.get_user_profile.return_value = {
            "id": 1,
            "name": "test_user",
            "role": "clam",
            "favorite_weathers": '["Clear", "Sunny"]',
            "dislike_weathers": '["Rain", "Storm"]',
            "x_axis": 5,
            "y_axis": 3,
            "intimacy": 50
        }
        db_manager.save_diary_entry.return_value = True
        return db_manager
    
    @pytest.fixture
    def mock_llm_manager(self, mock_llm_config):
        """Fixture for mock LLM manager."""
        llm_manager = Mock(spec=LLMConfigManager)
        llm_manager.generate_response.return_value = {
            "title": "晴天好心情",
            "content": "今天天气很好，心情特别愉快😊阳光明媚让人开心",
            "emotion_tags": ["开心快乐"]
        }
        return llm_manager
    
    @pytest.fixture
    async def diary_controller(self, mock_database_manager, mock_llm_manager):
        """Fixture for diary agent controller with mocked dependencies."""
        controller = DairyAgentController()
        controller.database_manager = mock_database_manager
        controller.llm_manager = mock_llm_manager
        
        # Mock other components
        controller.event_router = Mock(spec=EventRouter)
        controller.condition_checker = Mock(spec=ConditionChecker)
        controller.sub_agent_manager = Mock(spec=SubAgentManager)
        controller.diary_generator = Mock(spec=DiaryEntryGenerator)
        
        return controller
    
    @pytest.mark.asyncio
    async def test_single_event_processing_workflow(self, diary_controller, test_data_generator):
        """Test complete workflow for processing a single event."""
        # Generate test event
        event = test_data_generator.generate_weather_event(user_id=1, event_name="favorite_weather")
        
        # Mock condition checker to return True
        diary_controller.condition_checker.evaluate_conditions.return_value = True
        
        # Mock event router to return weather agent type
        diary_controller.event_router.route_event.return_value = "weather_agent"
        
        # Mock sub-agent manager to return processed diary entry
        expected_diary = DiaryEntry(
            entry_id="test_entry_1",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="favorite_weather",
            title="晴天好心情",
            content="今天天气很好，心情特别愉快😊阳光明媚让人开心",
            emotion_tags=["开心快乐"],
            agent_type="weather_agent",
            llm_provider="test_provider"
        )
        diary_controller.sub_agent_manager.process_event.return_value = expected_diary
        
        # Process the event
        result = await diary_controller.process_event(event)
        
        # Verify workflow execution
        assert result is not None
        assert result.event_name == "favorite_weather"
        assert result.title == "晴天好心情"
        assert len(result.content) <= 35
        assert len(result.title) <= 6
        assert "开心快乐" in result.emotion_tags
        
        # Verify method calls
        diary_controller.condition_checker.evaluate_conditions.assert_called_once()
        diary_controller.event_router.route_event.assert_called_once_with(event)
        diary_controller.sub_agent_manager.process_event.assert_called_once()
        diary_controller.database_manager.save_diary_entry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_event_types_workflow(self, diary_controller, test_data_generator):
        """Test workflow with multiple different event types."""
        # Generate different event types
        events = [
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_trending_event(1, "celebration"),
            test_data_generator.generate_holiday_event(1, "approaching_holiday"),
            test_data_generator.generate_friends_event(1, "made_new_friend"),
            test_data_generator.generate_interaction_event(1, "liked_interaction_once")
        ]
        
        # Mock responses for different agent types
        agent_responses = {
            "weather_agent": DiaryEntry(
                entry_id="weather_1", user_id=1, timestamp=datetime.now(),
                event_type="weather_events", event_name="favorite_weather",
                title="晴天", content="今天天气很好😊", emotion_tags=["开心快乐"],
                agent_type="weather_agent", llm_provider="test_provider"
            ),
            "trending_agent": DiaryEntry(
                entry_id="trending_1", user_id=1, timestamp=datetime.now(),
                event_type="trending_events", event_name="celebration",
                title="庆祝", content="今天有庆祝活动🎉", emotion_tags=["兴奋激动"],
                agent_type="trending_agent", llm_provider="test_provider"
            ),
            "holiday_agent": DiaryEntry(
                entry_id="holiday_1", user_id=1, timestamp=datetime.now(),
                event_type="holiday_events", event_name="approaching_holiday",
                title="节日", content="节日快到了，很期待🎊", emotion_tags=["开心快乐"],
                agent_type="holiday_agent", llm_provider="test_provider"
            ),
            "friends_agent": DiaryEntry(
                entry_id="friends_1", user_id=1, timestamp=datetime.now(),
                event_type="friends_events", event_name="made_new_friend",
                title="新朋友", content="今天认识了新朋友👫", emotion_tags=["开心快乐"],
                agent_type="friends_agent", llm_provider="test_provider"
            ),
            "interactive_agent": DiaryEntry(
                entry_id="interactive_1", user_id=1, timestamp=datetime.now(),
                event_type="interaction_events", event_name="liked_interaction_once",
                title="互动", content="和主人互动很开心😄", emotion_tags=["开心快乐"],
                agent_type="interactive_agent", llm_provider="test_provider"
            )
        }
        
        # Configure mocks
        diary_controller.condition_checker.evaluate_conditions.return_value = True
        
        def mock_route_event(event):
            if event.event_type == "weather_events":
                return "weather_agent"
            elif event.event_type == "trending_events":
                return "trending_agent"
            elif event.event_type == "holiday_events":
                return "holiday_agent"
            elif event.event_type == "friends_events":
                return "friends_agent"
            elif event.event_type == "interaction_events":
                return "interactive_agent"
        
        diary_controller.event_router.route_event.side_effect = mock_route_event
        
        def mock_process_event(event, agent_type):
            return agent_responses.get(agent_type)
        
        diary_controller.sub_agent_manager.process_event.side_effect = mock_process_event
        
        # Process all events
        results = []
        for event in events:
            result = await diary_controller.process_event(event)
            results.append(result)
        
        # Verify results
        assert len(results) == 5
        assert all(result is not None for result in results)
        
        # Verify each event type was processed correctly
        event_types = [result.event_type for result in results]
        assert "weather_events" in event_types
        assert "trending_events" in event_types
        assert "holiday_events" in event_types
        assert "friends_events" in event_types
        assert "interaction_events" in event_types
        
        # Verify formatting constraints
        for result in results:
            assert len(result.title) <= 6
            assert len(result.content) <= 35
            assert len(result.emotion_tags) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, diary_controller, test_data_generator):
        """Test workflow error handling and recovery."""
        event = test_data_generator.generate_weather_event(1, "favorite_weather")
        
        # Test condition checker failure
        diary_controller.condition_checker.evaluate_conditions.side_effect = Exception("Condition check failed")
        
        result = await diary_controller.process_event(event)
        assert result is None  # Should handle gracefully
        
        # Reset and test event router failure
        diary_controller.condition_checker.evaluate_conditions.side_effect = None
        diary_controller.condition_checker.evaluate_conditions.return_value = True
        diary_controller.event_router.route_event.side_effect = Exception("Routing failed")
        
        result = await diary_controller.process_event(event)
        assert result is None  # Should handle gracefully
        
        # Reset and test sub-agent failure with fallback
        diary_controller.event_router.route_event.side_effect = None
        diary_controller.event_router.route_event.return_value = "weather_agent"
        diary_controller.sub_agent_manager.process_event.side_effect = Exception("Agent failed")
        
        # Mock fallback behavior
        fallback_diary = DiaryEntry(
            entry_id="fallback_1", user_id=1, timestamp=datetime.now(),
            event_type="weather_events", event_name="favorite_weather",
            title="默认", content="处理失败，使用默认内容", emotion_tags=["平静"],
            agent_type="fallback_agent", llm_provider="fallback"
        )
        diary_controller.sub_agent_manager.get_fallback_response.return_value = fallback_diary
        
        result = await diary_controller.process_event(event)
        assert result is not None
        assert result.agent_type == "fallback_agent"
    
    @pytest.mark.asyncio
    async def test_daily_quota_workflow(self, diary_controller, test_data_generator):
        """Test daily diary quota management workflow."""
        # Mock daily quota of 3 entries
        diary_controller.daily_quota = 3
        diary_controller.daily_count = 0
        
        # Generate 5 events (more than quota)
        events = test_data_generator.generate_batch_events(5)
        
        # Configure mocks
        diary_controller.condition_checker.evaluate_conditions.return_value = True
        diary_controller.event_router.route_event.return_value = "weather_agent"
        
        mock_diary = DiaryEntry(
            entry_id="test", user_id=1, timestamp=datetime.now(),
            event_type="weather_events", event_name="favorite_weather",
            title="测试", content="测试内容", emotion_tags=["平静"],
            agent_type="weather_agent", llm_provider="test"
        )
        diary_controller.sub_agent_manager.process_event.return_value = mock_diary
        
        # Process events and track quota
        processed_count = 0
        for event in events:
            if diary_controller.daily_count < diary_controller.daily_quota:
                result = await diary_controller.process_event(event)
                if result:
                    processed_count += 1
                    diary_controller.daily_count += 1
        
        # Verify quota enforcement
        assert processed_count == 3  # Should only process 3 due to quota
        assert diary_controller.daily_count == 3
    
    @pytest.mark.asyncio
    async def test_event_type_uniqueness_workflow(self, diary_controller, test_data_generator):
        """Test one diary per event type per day constraint."""
        # Generate multiple events of same type
        events = [
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_weather_event(1, "dislike_weather")
        ]
        
        # Track processed event types
        diary_controller.daily_event_types = set()
        
        # Configure mocks
        diary_controller.condition_checker.evaluate_conditions.return_value = True
        diary_controller.event_router.route_event.return_value = "weather_agent"
        
        mock_diary = DiaryEntry(
            entry_id="test", user_id=1, timestamp=datetime.now(),
            event_type="weather_events", event_name="favorite_weather",
            title="测试", content="测试内容", emotion_tags=["平静"],
            agent_type="weather_agent", llm_provider="test"
        )
        diary_controller.sub_agent_manager.process_event.return_value = mock_diary
        
        # Process events
        results = []
        for event in events:
            # Check if event type already processed today
            if event.event_name not in diary_controller.daily_event_types:
                result = await diary_controller.process_event(event)
                if result:
                    diary_controller.daily_event_types.add(event.event_name)
                    results.append(result)
        
        # Verify uniqueness constraint
        assert len(results) == 2  # Should process favorite_weather once and dislike_weather once
        processed_event_names = {result.event_name for result in results}
        assert "favorite_weather" in processed_event_names
        assert "dislike_weather" in processed_event_names
    
    @pytest.mark.asyncio
    async def test_claimed_events_workflow(self, diary_controller, test_data_generator):
        """Test claimed events always generate diary entries."""
        # Define claimed events (events that must result in diary entries)
        claimed_events = ["toy_claimed", "positive_emotional_dialogue", "made_new_friend"]
        
        # Generate claimed and non-claimed events
        events = [
            test_data_generator.generate_friends_event(1, "made_new_friend"),  # Claimed
            test_data_generator.generate_dialogue_event(1, "positive_emotional_dialogue"),  # Claimed
            test_data_generator.generate_weather_event(1, "favorite_weather")  # Not claimed
        ]
        
        # Mock daily quota reached
        diary_controller.daily_quota = 1
        diary_controller.daily_count = 1
        
        # Configure mocks
        diary_controller.condition_checker.evaluate_conditions.return_value = True
        
        def mock_route_event(event):
            if event.event_type == "friends_events":
                return "friends_agent"
            elif event.event_type == "dialogue_events":
                return "dialogue_agent"
            else:
                return "weather_agent"
        
        diary_controller.event_router.route_event.side_effect = mock_route_event
        
        mock_diary = DiaryEntry(
            entry_id="test", user_id=1, timestamp=datetime.now(),
            event_type="test", event_name="test",
            title="测试", content="测试内容", emotion_tags=["平静"],
            agent_type="test", llm_provider="test"
        )
        diary_controller.sub_agent_manager.process_event.return_value = mock_diary
        
        # Process events with claimed event logic
        results = []
        for event in events:
            # Claimed events bypass quota
            if event.event_name in claimed_events or diary_controller.daily_count < diary_controller.daily_quota:
                result = await diary_controller.process_event(event)
                if result:
                    results.append(result)
                    if event.event_name not in claimed_events:
                        diary_controller.daily_count += 1
        
        # Verify claimed events were processed despite quota
        assert len(results) == 2  # Should process both claimed events
    
    @pytest.mark.asyncio
    async def test_database_integration_workflow(self, test_data_generator):
        """Test integration with database operations."""
        # Create real database manager for integration test
        db_manager = DatabaseManager()
        
        # Mock database operations
        with patch.object(db_manager, 'get_user_profile') as mock_get_user, \
             patch.object(db_manager, 'save_diary_entry') as mock_save_diary:
            
            mock_get_user.return_value = test_data_generator.generate_user_profile(1)
            mock_save_diary.return_value = True
            
            # Create controller with real database manager
            controller = DairyAgentController()
            controller.database_manager = db_manager
            
            # Generate test event
            event = test_data_generator.generate_weather_event(1, "favorite_weather")
            
            # Mock other components
            controller.condition_checker = Mock()
            controller.condition_checker.evaluate_conditions.return_value = True
            
            controller.event_router = Mock()
            controller.event_router.route_event.return_value = "weather_agent"
            
            controller.sub_agent_manager = Mock()
            mock_diary = DiaryEntry(
                entry_id="db_test", user_id=1, timestamp=datetime.now(),
                event_type="weather_events", event_name="favorite_weather",
                title="数据库测试", content="测试数据库集成", emotion_tags=["平静"],
                agent_type="weather_agent", llm_provider="test"
            )
            controller.sub_agent_manager.process_event.return_value = mock_diary
            
            # Process event
            result = await controller.process_event(event)
            
            # Verify database operations
            assert result is not None
            mock_get_user.assert_called_once_with(1)
            mock_save_diary.assert_called_once()
            
            # Verify saved diary entry structure
            saved_entry = mock_save_diary.call_args[0][0]
            assert saved_entry.user_id == 1
            assert saved_entry.event_name == "favorite_weather"
            assert len(saved_entry.title) <= 6
            assert len(saved_entry.content) <= 35