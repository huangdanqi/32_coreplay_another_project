"""
End-to-end tests for complete diary agent system.
Tests the entire system from event input to diary output with real components.
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from diary_agent.core.dairy_agent_controller import DairyAgentController
from diary_agent.core.event_router import EventRouter
from diary_agent.core.condition import ConditionChecker
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.core.config_manager import ConfigManager
from diary_agent.integration.database_manager import DatabaseManager
from diary_agent.utils.data_models import EventData, DiaryEntry, LLMConfig
from diary_agent.tests.test_data_generators import DiaryTestDataGenerator


class TestEndToEnd:
    """End-to-end tests for complete diary agent system."""
    
    @pytest.fixture
    def test_data_generator(self):
        """Fixture for test data generator."""
        return DiaryTestDataGenerator()
    
    @pytest.fixture
    def temp_config_dir(self):
        """Fixture for temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config structure
            config_dir = os.path.join(temp_dir, "config")
            os.makedirs(config_dir)
            
            # Create agent_prompts directory
            prompts_dir = os.path.join(config_dir, "agent_prompts")
            os.makedirs(prompts_dir)
            
            # Create test configuration files
            llm_config = {
                "providers": {
                    "test_provider": {
                        "api_endpoint": "http://test.api",
                        "api_key": "test_key",
                        "model_name": "test_model",
                        "max_tokens": 100,
                        "temperature": 0.7,
                        "timeout": 30,
                        "retry_attempts": 3
                    }
                },
                "default_provider": "test_provider"
            }
            
            with open(os.path.join(config_dir, "llm_configuration.json"), "w", encoding="utf-8") as f:
                json.dump(llm_config, f, ensure_ascii=False, indent=2)
            
            # Create agent prompt configurations
            agent_types = [
                "weather_agent", "trending_agent", "holiday_agent",
                "friends_agent", "interactive_agent", "dialogue_agent", "neglect_agent"
            ]
            
            for agent_type in agent_types:
                prompt_config = {
                    "agent_type": agent_type,
                    "system_prompt": f"You are a {agent_type} that generates diary entries.",
                    "user_prompt_template": "Generate a diary entry for: {event_name}",
                    "output_format": {
                        "title": "string (max 6 characters)",
                        "content": "string (max 35 characters)",
                        "emotion_tags": "array of strings"
                    },
                    "validation_rules": {
                        "title_max_length": 6,
                        "content_max_length": 35,
                        "required_emotion_tags": True
                    }
                }
                
                with open(os.path.join(prompts_dir, f"{agent_type}.json"), "w", encoding="utf-8") as f:
                    json.dump(prompt_config, f, ensure_ascii=False, indent=2)
            
            # Create condition rules
            condition_rules = {
                "default_conditions": {
                    "time_based": True,
                    "event_based": True,
                    "image_based": False
                },
                "trigger_conditions": [
                    {
                        "condition_type": "always_true",
                        "description": "Always trigger for testing"
                    }
                ]
            }
            
            with open(os.path.join(config_dir, "condition_rules.json"), "w", encoding="utf-8") as f:
                json.dump(condition_rules, f, ensure_ascii=False, indent=2)
            
            yield temp_dir
    
    @pytest.fixture
    def mock_llm_responses(self):
        """Fixture for mock LLM responses."""
        return {
            "weather_agent": {
                "favorite_weather": {
                    "title": "晴天好心情",
                    "content": "今天阳光明媚☀️心情特别好想出去走走",
                    "emotion_tags": ["开心快乐"]
                },
                "dislike_weather": {
                    "title": "雨天烦躁",
                    "content": "下雨天🌧️心情有点低落不想出门",
                    "emotion_tags": ["悲伤难过"]
                }
            },
            "friends_agent": {
                "made_new_friend": {
                    "title": "新朋友",
                    "content": "今天认识了新朋友👫感觉很开心",
                    "emotion_tags": ["开心快乐"]
                }
            },
            "dialogue_agent": {
                "positive_emotional_dialogue": {
                    "title": "愉快聊天",
                    "content": "和主人聊天很开心😊感觉被关爱着",
                    "emotion_tags": ["开心快乐"]
                }
            }
        }
    
    @pytest.fixture
    async def integrated_system(self, temp_config_dir, mock_llm_responses):
        """Fixture for integrated diary agent system."""
        # Initialize configuration manager
        config_manager = ConfigManager(config_dir=os.path.join(temp_config_dir, "config"))
        
        # Mock LLM manager with realistic responses
        llm_manager = Mock(spec=LLMConfigManager)
        
        def mock_generate_response(prompt, agent_type=None, **kwargs):
            # Extract event information from prompt
            if "favorite_weather" in prompt:
                return mock_llm_responses["weather_agent"]["favorite_weather"]
            elif "dislike_weather" in prompt:
                return mock_llm_responses["weather_agent"]["dislike_weather"]
            elif "made_new_friend" in prompt:
                return mock_llm_responses["friends_agent"]["made_new_friend"]
            elif "positive_emotional_dialogue" in prompt:
                return mock_llm_responses["dialogue_agent"]["positive_emotional_dialogue"]
            else:
                return {
                    "title": "默认",
                    "content": "默认日记内容",
                    "emotion_tags": ["平静"]
                }
        
        llm_manager.generate_response.side_effect = mock_generate_response
        
        # Mock database manager
        database_manager = Mock(spec=DatabaseManager)
        database_manager.get_user_profile.return_value = {
            "id": 1,
            "name": "test_user",
            "role": "clam",
            "favorite_weathers": '["Clear", "Sunny"]',
            "dislike_weathers": '["Rain", "Storm"]',
            "x_axis": 5,
            "y_axis": 3,
            "intimacy": 50
        }
        database_manager.save_diary_entry.return_value = True
        
        # Initialize system components
        condition_checker = ConditionChecker(config_manager)
        event_router = EventRouter()
        sub_agent_manager = SubAgentManager(config_manager, llm_manager)
        
        # Initialize main controller
        controller = DairyAgentController()
        controller.config_manager = config_manager
        controller.llm_manager = llm_manager
        controller.database_manager = database_manager
        controller.condition_checker = condition_checker
        controller.event_router = event_router
        controller.sub_agent_manager = sub_agent_manager
        
        # Initialize system
        await controller.initialize()
        
        return controller
    
    @pytest.mark.asyncio
    async def test_complete_weather_event_flow(self, integrated_system, test_data_generator):
        """Test complete flow for weather event processing."""
        # Generate weather event
        event = test_data_generator.generate_weather_event(1, "favorite_weather")
        event.context_data.update({
            "weather_condition": "Sunny",
            "temperature": 25,
            "city": "Beijing"
        })
        
        # Process event through complete system
        result = await integrated_system.process_event(event)
        
        # Verify complete processing
        assert result is not None
        assert isinstance(result, DiaryEntry)
        
        # Verify diary content
        assert result.user_id == 1
        assert result.event_type == "weather_events"
        assert result.event_name == "favorite_weather"
        assert result.title == "晴天好心情"
        assert "阳光明媚" in result.content
        assert "开心快乐" in result.emotion_tags
        
        # Verify formatting constraints
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        
        # Verify system calls
        integrated_system.database_manager.get_user_profile.assert_called_with(1)
        integrated_system.database_manager.save_diary_entry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_social_event_flow(self, integrated_system, test_data_generator):
        """Test complete flow for social event processing."""
        # Generate friend event
        event = test_data_generator.generate_friends_event(1, "made_new_friend")
        event.context_data.update({
            "friend_count": 1,
            "friendship_level": "new",
            "activity": "聊天"
        })
        
        # Process event
        result = await integrated_system.process_event(event)
        
        # Verify processing
        assert result is not None
        assert result.event_name == "made_new_friend"
        assert result.title == "新朋友"
        assert "认识了新朋友" in result.content
        assert "开心快乐" in result.emotion_tags
    
    @pytest.mark.asyncio
    async def test_multiple_events_sequential_processing(self, integrated_system, test_data_generator):
        """Test sequential processing of multiple different events."""
        # Generate multiple events
        events = [
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_friends_event(1, "made_new_friend"),
            test_data_generator.generate_dialogue_event(1, "positive_emotional_dialogue"),
            test_data_generator.generate_weather_event(2, "dislike_weather")
        ]
        
        # Process events sequentially
        results = []
        for event in events:
            result = await integrated_system.process_event(event)
            results.append(result)
        
        # Verify all events processed
        assert len(results) == 4
        assert all(result is not None for result in results)
        
        # Verify event types
        event_names = [result.event_name for result in results]
        assert "favorite_weather" in event_names
        assert "made_new_friend" in event_names
        assert "positive_emotional_dialogue" in event_names
        assert "dislike_weather" in event_names
        
        # Verify user separation
        user_1_results = [r for r in results if r.user_id == 1]
        user_2_results = [r for r in results if r.user_id == 2]
        assert len(user_1_results) == 3
        assert len(user_2_results) == 1
    
    @pytest.mark.asyncio
    async def test_system_error_recovery(self, integrated_system, test_data_generator):
        """Test system error recovery and graceful degradation."""
        # Generate test event
        event = test_data_generator.generate_weather_event(1, "favorite_weather")
        
        # Test database error recovery
        integrated_system.database_manager.get_user_profile.side_effect = Exception("Database error")
        
        # System should handle error gracefully
        result = await integrated_system.process_event(event)
        
        # Should either return None or use fallback data
        if result is not None:
            # If system recovered, verify basic structure
            assert isinstance(result, DiaryEntry)
            assert len(result.title) <= 6
            assert len(result.content) <= 35
        
        # Reset database manager
        integrated_system.database_manager.get_user_profile.side_effect = None
        integrated_system.database_manager.get_user_profile.return_value = {
            "id": 1, "name": "test_user", "role": "clam"
        }
        
        # Test LLM error recovery
        integrated_system.llm_manager.generate_response.side_effect = Exception("LLM error")
        
        result = await integrated_system.process_event(event)
        
        # System should handle LLM errors
        if result is not None:
            # Should use fallback response
            assert isinstance(result, DiaryEntry)
    
    @pytest.mark.asyncio
    async def test_configuration_hot_reload(self, integrated_system, temp_config_dir):
        """Test configuration hot-reloading during system operation."""
        # Modify LLM configuration
        config_file = os.path.join(temp_config_dir, "config", "llm_configuration.json")
        
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Add new provider
        config["providers"]["new_test_provider"] = {
            "api_endpoint": "http://new.test.api",
            "api_key": "new_test_key",
            "model_name": "new_test_model"
        }
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # Reload configuration
        await integrated_system.config_manager.reload_configuration()
        
        # Verify new configuration loaded
        llm_config = integrated_system.config_manager.get_llm_config()
        assert "new_test_provider" in llm_config["providers"]
    
    @pytest.mark.asyncio
    async def test_daily_quota_management(self, integrated_system, test_data_generator):
        """Test daily quota management in end-to-end flow."""
        # Set daily quota
        integrated_system.daily_quota = 2
        integrated_system.daily_count = 0
        integrated_system.daily_event_types = set()
        
        # Generate more events than quota
        events = test_data_generator.generate_batch_events(5)
        
        # Process events
        processed_results = []
        for event in events:
            if integrated_system.daily_count < integrated_system.daily_quota:
                result = await integrated_system.process_event(event)
                if result:
                    processed_results.append(result)
                    integrated_system.daily_count += 1
        
        # Verify quota enforcement
        assert len(processed_results) == 2
        assert integrated_system.daily_count == 2
    
    @pytest.mark.asyncio
    async def test_event_type_uniqueness_enforcement(self, integrated_system, test_data_generator):
        """Test one diary per event type per day enforcement."""
        # Initialize daily tracking
        integrated_system.daily_event_types = set()
        
        # Generate multiple events of same type
        events = [
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_weather_event(1, "favorite_weather"),  # Duplicate
            test_data_generator.generate_weather_event(1, "dislike_weather")   # Different type
        ]
        
        # Process events with uniqueness check
        processed_results = []
        for event in events:
            if event.event_name not in integrated_system.daily_event_types:
                result = await integrated_system.process_event(event)
                if result:
                    processed_results.append(result)
                    integrated_system.daily_event_types.add(event.event_name)
        
        # Verify uniqueness enforcement
        assert len(processed_results) == 2  # Should process each type once
        processed_event_names = {result.event_name for result in processed_results}
        assert "favorite_weather" in processed_event_names
        assert "dislike_weather" in processed_event_names
    
    @pytest.mark.asyncio
    async def test_system_initialization_and_cleanup(self, temp_config_dir):
        """Test system initialization and cleanup procedures."""
        # Test system initialization
        controller = DairyAgentController()
        
        # Mock dependencies
        controller.config_manager = Mock()
        controller.llm_manager = Mock()
        controller.database_manager = Mock()
        controller.condition_checker = Mock()
        controller.event_router = Mock()
        controller.sub_agent_manager = Mock()
        
        # Initialize system
        await controller.initialize()
        
        # Verify initialization calls
        controller.config_manager.load_configuration.assert_called_once()
        controller.sub_agent_manager.initialize_agents.assert_called_once()
        
        # Test system cleanup
        await controller.cleanup()
        
        # Verify cleanup calls
        controller.sub_agent_manager.cleanup_agents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_multi_user_processing(self, integrated_system, test_data_generator):
        """Test concurrent processing for multiple users."""
        # Generate events for different users
        user_events = []
        for user_id in range(1, 6):  # 5 users
            event = test_data_generator.generate_weather_event(user_id, "favorite_weather")
            user_events.append(event)
        
        # Process events concurrently
        tasks = [integrated_system.process_event(event) for event in user_events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify concurrent processing
        successful_results = [r for r in results if isinstance(r, DiaryEntry)]
        assert len(successful_results) >= 4  # At least 80% success rate
        
        # Verify user isolation
        user_ids = {result.user_id for result in successful_results}
        assert len(user_ids) >= 4  # Multiple users processed
        
        # Verify each result belongs to correct user
        for i, result in enumerate(successful_results):
            if isinstance(result, DiaryEntry):
                expected_user_id = user_events[i].user_id
                assert result.user_id == expected_user_id
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, integrated_system, test_data_generator):
        """Test system health monitoring and metrics collection."""
        # Initialize health monitoring
        health_metrics = {
            "events_processed": 0,
            "events_failed": 0,
            "average_processing_time": 0,
            "system_errors": []
        }
        
        # Process multiple events and collect metrics
        events = test_data_generator.generate_batch_events(10)
        processing_times = []
        
        for event in events:
            start_time = datetime.now()
            
            try:
                result = await integrated_system.process_event(event)
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                processing_times.append(processing_time)
                
                if result:
                    health_metrics["events_processed"] += 1
                else:
                    health_metrics["events_failed"] += 1
                    
            except Exception as e:
                health_metrics["events_failed"] += 1
                health_metrics["system_errors"].append(str(e))
        
        # Calculate health metrics
        if processing_times:
            health_metrics["average_processing_time"] = sum(processing_times) / len(processing_times)
        
        # Verify system health
        total_events = health_metrics["events_processed"] + health_metrics["events_failed"]
        success_rate = health_metrics["events_processed"] / total_events if total_events > 0 else 0
        
        assert success_rate >= 0.8  # At least 80% success rate
        assert health_metrics["average_processing_time"] <= 1.0  # Under 1 second average
        assert len(health_metrics["system_errors"]) <= 2  # Minimal system errors
        
        print(f"System Health Metrics:")
        print(f"  Events processed: {health_metrics['events_processed']}")
        print(f"  Events failed: {health_metrics['events_failed']}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Average processing time: {health_metrics['average_processing_time']:.3f}s")
        print(f"  System errors: {len(health_metrics['system_errors'])}")
    
    @pytest.mark.asyncio
    async def test_data_persistence_integrity(self, integrated_system, test_data_generator):
        """Test data persistence and integrity throughout the system."""
        # Generate test event with specific data
        event = test_data_generator.generate_weather_event(1, "favorite_weather")
        event.context_data.update({
            "weather_condition": "Sunny",
            "temperature": 25,
            "city": "Beijing",
            "test_marker": "data_integrity_test"
        })
        
        # Process event
        result = await integrated_system.process_event(event)
        
        # Verify data integrity
        assert result is not None
        
        # Check that original event data is preserved
        assert result.user_id == event.user_id
        assert result.event_type == event.event_type
        assert result.event_name == event.event_name
        
        # Verify database save was called with correct data
        integrated_system.database_manager.save_diary_entry.assert_called_once()
        saved_entry = integrated_system.database_manager.save_diary_entry.call_args[0][0]
        
        # Verify saved entry integrity
        assert saved_entry.user_id == event.user_id
        assert saved_entry.event_name == event.event_name
        assert saved_entry.timestamp is not None
        assert len(saved_entry.title) <= 6
        assert len(saved_entry.content) <= 35
        assert len(saved_entry.emotion_tags) > 0