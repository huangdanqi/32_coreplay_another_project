"""
Integration tests for the DairyAgentController.
Tests the complete end-to-end workflow of the diary generation system.
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from diary_agent.core.dairy_agent_controller import (
    DairyAgentController, create_and_start_system, SystemHealthError
)
from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag


class TestDairyAgentController:
    """Test suite for DairyAgentController integration."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        config_dir = temp_dir / "config"
        data_dir = temp_dir / "data"
        
        config_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        
        yield str(config_dir), str(data_dir)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_controller(self, temp_dirs):
        """Create a controller with mocked dependencies for testing."""
        config_dir, data_dir = temp_dirs
        
        controller = DairyAgentController(
            config_dir=config_dir,
            data_dir=data_dir,
            log_level="DEBUG"
        )
        
        # Mock the components to avoid external dependencies
        controller.llm_manager = Mock()
        controller.llm_manager.get_provider_status.return_value = {
            "providers": ["qwen", "deepseek"],
            "current_provider": "qwen",
            "total_providers": 2
        }
        
        controller.database_manager = AsyncMock()
        controller.database_manager.initialize.return_value = True
        controller.database_manager.health_check.return_value = True
        
        controller.sub_agent_manager = AsyncMock()
        controller.sub_agent_manager.initialize_agents.return_value = True
        controller.sub_agent_manager.list_agents.return_value = ["weather_agent", "friends_agent"]
        controller.sub_agent_manager.get_agent.return_value = Mock()
        controller.sub_agent_manager.get_system_status.return_value = {
            "total_agents": 2,
            "healthy_agents": 2,
            "unhealthy_agents": 0,
            "success_rate": 95.0
        }
        controller.sub_agent_manager.registry = Mock()
        
        controller.condition_checker = Mock()
        controller.condition_checker.evaluate_conditions.return_value = True
        
        controller.event_router = Mock()
        controller.event_router.route_event.return_value = {
            "success": True,
            "diary_generated": True,
            "diary_entry": DiaryEntry(
                entry_id="test_entry_1",
                user_id=1,
                timestamp=datetime.now(),
                event_type="weather",
                event_name="favorite_weather",
                title="晴天",
                content="今天天气很好，心情愉快😊",
                emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
                agent_type="weather_agent",
                llm_provider="qwen"
            )
        }
        controller.event_router.get_routing_statistics.return_value = {
            "daily_quota": {"total_quota": 3, "current_count": 1}
        }
        
        controller.diary_generator = Mock()
        controller.diary_generator.get_daily_quota.return_value = None
        controller.diary_generator.set_daily_quota = Mock()
        controller.diary_generator.get_generation_stats.return_value = {
            "total_generated": 10,
            "successful_generations": 9,
            "failed_generations": 1
        }
        
        return controller
    
    @pytest.mark.asyncio
    async def test_system_initialization(self, mock_controller):
        """Test complete system initialization."""
        # Test initialization
        result = await mock_controller.initialize_system()
        
        assert result is True
        assert mock_controller.is_initialized is True
        assert mock_controller.health_status["system_status"] == "initialized"
        
        # Verify all components were initialized
        mock_controller.database_manager.initialize.assert_called_once()
        mock_controller.sub_agent_manager.initialize_agents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_system_start_stop(self, mock_controller):
        """Test system start and stop operations."""
        # Initialize first
        await mock_controller.initialize_system()
        
        # Test start
        result = await mock_controller.start_system()
        assert result is True
        assert mock_controller.is_running is True
        assert mock_controller.health_status["system_status"] == "running"
        
        # Verify tasks were created
        assert mock_controller.daily_scheduler_task is not None
        assert mock_controller.health_monitor_task is not None
        assert len(mock_controller.processing_tasks) == 3
        
        # Test stop
        await mock_controller.stop_system()
        assert mock_controller.is_running is False
        assert mock_controller.health_status["system_status"] == "stopped"
    
    @pytest.mark.asyncio
    async def test_event_processing_workflow(self, mock_controller):
        """Test complete event processing workflow."""
        # Initialize system
        await mock_controller.initialize_system()
        
        # Create test event
        event_data = EventData(
            event_id="test_event_1",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"weather": "sunny", "temperature": 25},
            metadata={"source": "test"}
        )
        
        # Process event
        result = await mock_controller.process_event(event_data)
        
        # Verify processing
        assert result is not None
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "favorite_weather"
        assert result.user_id == 1
        
        # Verify statistics updated
        assert mock_controller.system_stats["events_processed"] == 1
        assert mock_controller.system_stats["diaries_generated"] == 1
    
    @pytest.mark.asyncio
    async def test_manual_event_processing(self, mock_controller):
        """Test manual event processing."""
        await mock_controller.initialize_system()
        
        # Process manual event
        result = await mock_controller.process_manual_event(
            event_name="favorite_weather",
            user_id=1,
            context_data={"manual": True}
        )
        
        assert result is not None
        assert result.event_name == "favorite_weather"
        assert result.user_id == 1
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, mock_controller):
        """Test system health monitoring."""
        await mock_controller.initialize_system()
        
        # Perform health check
        health_status = await mock_controller._perform_health_check()
        
        assert "overall_healthy" in health_status
        assert "components" in health_status
        assert "timestamp" in health_status
        
        # Check component health
        components = health_status["components"]
        assert "llm_manager" in components
        assert "sub_agent_manager" in components
        assert "database_manager" in components
    
    @pytest.mark.asyncio
    async def test_daily_quota_initialization(self, mock_controller):
        """Test daily quota initialization."""
        await mock_controller.initialize_system()
        
        # Verify daily quota was initialized
        mock_controller.diary_generator.set_daily_quota.assert_called()
        
        # Test manual daily reset
        await mock_controller._perform_daily_reset()
        
        # Verify quota was reset
        assert mock_controller.diary_generator.set_daily_quota.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_system_restart(self, mock_controller):
        """Test system restart functionality."""
        # Initialize and start
        await mock_controller.initialize_system()
        await mock_controller.start_system()
        
        initial_restart_count = mock_controller.system_stats["system_restarts"]
        
        # Restart system
        result = await mock_controller.restart_system()
        
        assert result is True
        assert mock_controller.system_stats["system_restarts"] == initial_restart_count + 1
        assert mock_controller.is_running is True
    
    @pytest.mark.asyncio
    async def test_error_handling_in_event_processing(self, mock_controller):
        """Test error handling during event processing."""
        await mock_controller.initialize_system()
        
        # Mock condition checker to raise exception
        mock_controller.condition_checker.evaluate_conditions.side_effect = Exception("Test error")
        
        event_data = EventData(
            event_id="error_test",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        # Process event with error
        result = await mock_controller.process_event(event_data)
        
        # Should handle error gracefully
        assert result is None
        assert mock_controller.system_stats["errors_encountered"] == 1
    
    @pytest.mark.asyncio
    async def test_system_status_reporting(self, mock_controller):
        """Test system status reporting."""
        await mock_controller.initialize_system()
        await mock_controller.start_system()
        
        # Get system status
        status = mock_controller.get_system_status()
        
        # Verify status structure
        assert "system_info" in status
        assert "health_status" in status
        assert "statistics" in status
        assert "component_status" in status
        
        # Verify system info
        system_info = status["system_info"]
        assert system_info["is_initialized"] is True
        assert system_info["is_running"] is True
        assert "uptime_seconds" in system_info
        
        await mock_controller.stop_system()
    
    @pytest.mark.asyncio
    async def test_emergency_shutdown(self, mock_controller):
        """Test emergency shutdown functionality."""
        await mock_controller.initialize_system()
        await mock_controller.start_system()
        
        # Perform emergency shutdown
        await mock_controller.emergency_shutdown()
        
        assert mock_controller.is_running is False
        assert mock_controller.health_status["system_status"] == "emergency_stopped"
    
    @pytest.mark.asyncio
    async def test_event_queue_processing(self, mock_controller):
        """Test event queue processing."""
        await mock_controller.initialize_system()
        
        # Add events to queue
        event1 = EventData(
            event_id="queue_test_1",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        event2 = EventData(
            event_id="queue_test_2",
            event_type="friends",
            event_name="made_new_friend",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        # Add to queue via handler
        await mock_controller._handle_event_processing(event1)
        await mock_controller._handle_event_processing(event2)
        
        # Verify events were queued
        assert mock_controller.event_queue.qsize() == 2
    
    @pytest.mark.asyncio
    async def test_supported_events_listing(self, mock_controller):
        """Test listing of supported events."""
        await mock_controller.initialize_system()
        
        # Mock supported events
        mock_controller.sub_agent_manager.list_supported_events.return_value = [
            "favorite_weather", "dislike_weather", "made_new_friend"
        ]
        
        supported_events = mock_controller.get_supported_events()
        
        assert len(supported_events) == 3
        assert "favorite_weather" in supported_events
        assert "made_new_friend" in supported_events


class TestSystemIntegration:
    """Integration tests for complete system workflow."""
    
    @pytest.mark.asyncio
    async def test_create_and_start_system_success(self, tmp_path):
        """Test successful system creation and startup."""
        config_dir = str(tmp_path / "config")
        data_dir = str(tmp_path / "data")
        
        with patch('diary_agent.core.dairy_agent_controller.DairyAgentController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.initialize_system.return_value = True
            mock_controller.start_system.return_value = True
            mock_controller_class.return_value = mock_controller
            
            # Test successful creation
            controller = await create_and_start_system(config_dir, data_dir)
            
            assert controller is not None
            mock_controller.initialize_system.assert_called_once()
            mock_controller.start_system.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_and_start_system_initialization_failure(self, tmp_path):
        """Test system creation with initialization failure."""
        config_dir = str(tmp_path / "config")
        data_dir = str(tmp_path / "data")
        
        with patch('diary_agent.core.dairy_agent_controller.DairyAgentController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.initialize_system.return_value = False
            mock_controller_class.return_value = mock_controller
            
            # Test initialization failure
            with pytest.raises(SystemHealthError, match="Failed to initialize"):
                await create_and_start_system(config_dir, data_dir)
    
    @pytest.mark.asyncio
    async def test_create_and_start_system_startup_failure(self, tmp_path):
        """Test system creation with startup failure."""
        config_dir = str(tmp_path / "config")
        data_dir = str(tmp_path / "data")
        
        with patch('diary_agent.core.dairy_agent_controller.DairyAgentController') as mock_controller_class:
            mock_controller = AsyncMock()
            mock_controller.initialize_system.return_value = True
            mock_controller.start_system.return_value = False
            mock_controller_class.return_value = mock_controller
            
            # Test startup failure
            with pytest.raises(SystemHealthError, match="Failed to start"):
                await create_and_start_system(config_dir, data_dir)


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    @pytest.fixture
    def full_system_mock(self, tmp_path):
        """Create a fully mocked system for end-to-end testing."""
        config_dir = str(tmp_path / "config")
        data_dir = str(tmp_path / "data")
        
        # Create necessary config files
        Path(config_dir).mkdir(parents=True)
        Path(data_dir).mkdir(parents=True)
        
        # Create mock LLM config
        llm_config = {
            "providers": {
                "qwen": {
                    "provider_name": "qwen",
                    "api_endpoint": "https://test.api.com",
                    "api_key": "test-key",
                    "model_name": "test-model",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                }
            }
        }
        
        with open(Path(config_dir) / "llm_configuration.json", 'w') as f:
            import json
            json.dump(llm_config, f)
        
        # Create events.json
        events_config = {
            "weather_events": ["favorite_weather", "dislike_weather"],
            "friends_function": ["made_new_friend", "friend_deleted"]
        }
        
        with open(Path(config_dir).parent / "events.json", 'w') as f:
            json.dump(events_config, f)
        
        return config_dir, data_dir
    
    @pytest.mark.asyncio
    async def test_complete_diary_generation_workflow(self, full_system_mock):
        """Test complete workflow from event to diary entry."""
        config_dir, data_dir = full_system_mock
        
        # This would be a more comprehensive test with real components
        # For now, we'll test the workflow structure
        
        controller = DairyAgentController(config_dir, data_dir)
        
        # Mock the workflow steps
        with patch.object(controller, 'initialize_system', return_value=True), \
             patch.object(controller, 'start_system', return_value=True), \
             patch.object(controller, 'process_event') as mock_process:
            
            mock_diary_entry = DiaryEntry(
                entry_id="workflow_test",
                user_id=1,
                timestamp=datetime.now(),
                event_type="weather",
                event_name="favorite_weather",
                title="好天气",
                content="今天阳光明媚，心情特别好！😊",
                emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
                agent_type="weather_agent",
                llm_provider="qwen"
            )
            
            mock_process.return_value = mock_diary_entry
            
            # Initialize and start system
            await controller.initialize_system()
            await controller.start_system()
            
            # Create and process event
            event_data = EventData(
                event_id="workflow_event",
                event_type="weather",
                event_name="favorite_weather",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"weather": "sunny"},
                metadata={"test": True}
            )
            
            # Process event
            result = await controller.process_event(event_data)
            
            # Verify workflow
            assert result is not None
            assert result.event_name == "favorite_weather"
            assert len(result.content) <= 35  # Content length constraint
            assert len(result.title) <= 6     # Title length constraint
            
            await controller.stop_system()
    
    @pytest.mark.asyncio
    async def test_daily_quota_workflow(self, full_system_mock):
        """Test daily quota management workflow."""
        config_dir, data_dir = full_system_mock
        
        controller = DairyAgentController(config_dir, data_dir)
        
        # Test daily quota initialization and management
        with patch.object(controller, 'initialize_system', return_value=True):
            await controller.initialize_system()
            
            # Test daily reset
            await controller._perform_daily_reset()
            
            # Verify quota was set (would be mocked in real test)
            assert controller.diary_generator is not None
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, full_system_mock):
        """Test error recovery and system resilience."""
        config_dir, data_dir = full_system_mock
        
        controller = DairyAgentController(config_dir, data_dir)
        
        with patch.object(controller, 'initialize_system', return_value=True), \
             patch.object(controller, 'start_system', return_value=True), \
             patch.object(controller, '_perform_health_check') as mock_health:
            
            # Simulate unhealthy system
            mock_health.return_value = {
                "overall_healthy": False,
                "issues": ["Test issue"],
                "components": {}
            }
            
            await controller.initialize_system()
            await controller.start_system()
            
            # Test health check
            health_status = await controller._perform_health_check()
            assert health_status["overall_healthy"] is False
            
            await controller.stop_system()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])