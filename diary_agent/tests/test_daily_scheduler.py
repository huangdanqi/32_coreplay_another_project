"""
Unit tests for the daily diary generation scheduler.
"""

import pytest
import asyncio
from datetime import datetime, time, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from diary_agent.core.daily_scheduler import DailyScheduler, DailyScheduleConfig, DiaryGenerationResult
from diary_agent.core.event_router import EventRouter
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.diary_entry_generator import DiaryEntryGenerator
from diary_agent.core.data_persistence import DiaryPersistenceManager
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DailyQuota, EmotionalTag, DiaryContextData
)


class TestDailyScheduler:
    """Test cases for DailyScheduler."""
    
    @pytest.fixture
    def mock_event_router(self):
        """Mock event router."""
        router = Mock(spec=EventRouter)
        router.route_event = Mock(return_value={
            "success": True,
            "agent_type": "weather_agent",
            "event_type": "weather_events"
        })
        router.is_claimed_event = Mock(return_value=False)
        router.event_mapper = Mock()
        router.event_mapper.get_event_type_for_event = Mock(return_value="weather_events")
        router.update_daily_quota = Mock()
        router.get_available_event_types_for_today = Mock(return_value=["weather_events", "friends_function"])
        return router
    
    @pytest.fixture
    def mock_sub_agent_manager(self):
        """Mock sub-agent manager."""
        manager = Mock(spec=SubAgentManager)
        mock_agent = Mock()
        mock_agent.process_event = AsyncMock(return_value=self.create_sample_diary_entry())
        manager.get_agent = Mock(return_value=mock_agent)
        return manager
    
    @pytest.fixture
    def mock_diary_generator(self):
        """Mock diary generator."""
        return Mock(spec=DiaryEntryGenerator)
    
    @pytest.fixture
    def mock_data_persistence(self):
        """Mock data persistence."""
        persistence = Mock(spec=DiaryPersistenceManager)
        persistence.save_diary_entry = Mock(return_value=True)
        return persistence
    
    @pytest.fixture
    def scheduler_config(self):
        """Default scheduler configuration."""
        return DailyScheduleConfig(
            schedule_time=time(0, 0),
            min_quota=0,
            max_quota=5,
            claimed_events_always_generate=True,
            random_selection_probability=0.6,
            alternative_approach_enabled=True,
            max_retries_per_event=3,
            storage_enabled=True
        )
    
    @pytest.fixture
    def daily_scheduler(self, mock_event_router, mock_sub_agent_manager, 
                       mock_diary_generator, mock_data_persistence, scheduler_config):
        """Create DailyScheduler instance."""
        return DailyScheduler(
            event_router=mock_event_router,
            sub_agent_manager=mock_sub_agent_manager,
            diary_generator=mock_diary_generator,
            data_persistence=mock_data_persistence,
            config=scheduler_config
        )
    
    def create_sample_event_data(self) -> EventData:
        """Create sample event data for testing."""
        return EventData(
            event_id="test_event_001",
            event_type="weather_events",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"weather": "sunny", "temperature": 25},
            metadata={"source": "test"}
        )
    
    def create_sample_diary_entry(self) -> DiaryEntry:
        """Create sample diary entry for testing."""
        return DiaryEntry(
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
    
    @pytest.mark.asyncio
    async def test_scheduler_initialization(self, daily_scheduler):
        """Test scheduler initialization."""
        assert daily_scheduler.config.max_quota == 5
        assert daily_scheduler.config.min_quota == 0
        assert daily_scheduler.current_quota is None
        assert not daily_scheduler.is_running
        assert len(daily_scheduler.daily_generation_results) == 0
    
    @pytest.mark.asyncio
    async def test_daily_quota_reset(self, daily_scheduler):
        """Test daily quota reset functionality."""
        # Test quota reset
        await daily_scheduler._reset_daily_quota()
        
        assert daily_scheduler.current_quota is not None
        assert 0 <= daily_scheduler.current_quota.total_quota <= 5
        assert daily_scheduler.current_quota.current_count == 0
        assert len(daily_scheduler.current_quota.completed_event_types) == 0
        assert daily_scheduler.current_quota.date == datetime.now().date()
    
    @pytest.mark.asyncio
    async def test_should_generate_diary_for_claimed_event(self, daily_scheduler, mock_event_router):
        """Test diary generation decision for claimed events."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 3
        
        event_data = self.create_sample_event_data()
        mock_event_router.is_claimed_event.return_value = True
        
        # Test
        should_generate = await daily_scheduler._should_generate_diary_for_event(event_data)
        
        assert should_generate is True
        mock_event_router.is_claimed_event.assert_called_once_with(event_data.event_name)
    
    @pytest.mark.asyncio
    async def test_should_generate_diary_quota_exceeded(self, daily_scheduler):
        """Test diary generation when quota is exceeded."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 2
        daily_scheduler.current_quota.current_count = 2
        
        event_data = self.create_sample_event_data()
        
        # Test
        should_generate = await daily_scheduler._should_generate_diary_for_event(event_data)
        
        assert should_generate is False
    
    @pytest.mark.asyncio
    async def test_should_generate_diary_event_type_already_processed(self, daily_scheduler, mock_event_router):
        """Test diary generation when event type already processed."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 3
        daily_scheduler.current_quota.completed_event_types = ["weather_events"]
        
        event_data = self.create_sample_event_data()
        mock_event_router.is_claimed_event.return_value = False
        
        # Test
        should_generate = await daily_scheduler._should_generate_diary_for_event(event_data)
        
        assert should_generate is False
    
    @pytest.mark.asyncio
    async def test_process_event_successful(self, daily_scheduler, mock_event_router, mock_sub_agent_manager):
        """Test successful event processing."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 3
        
        event_data = self.create_sample_event_data()
        mock_event_router.is_claimed_event.return_value = True
        
        # Test
        result = await daily_scheduler.process_event(event_data)
        
        assert result.success is True
        assert result.diary_entry is not None
        assert result.agent_type == "weather_agent"
        assert result.event_type == "weather_events"
        assert daily_scheduler.current_quota.current_count == 1
        assert "weather_events" in daily_scheduler.current_quota.completed_event_types
    
    @pytest.mark.asyncio
    async def test_process_event_skipped(self, daily_scheduler, mock_event_router):
        """Test event processing when skipped."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 0  # No quota
        
        event_data = self.create_sample_event_data()
        mock_event_router.is_claimed_event.return_value = False
        
        # Test
        result = await daily_scheduler.process_event(event_data)
        
        assert result.success is True
        assert result.diary_entry is None
        assert "skipped" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_process_event_routing_failure(self, daily_scheduler, mock_event_router):
        """Test event processing when routing fails."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 3
        
        event_data = self.create_sample_event_data()
        mock_event_router.is_claimed_event.return_value = True
        mock_event_router.route_event.return_value = {
            "success": False,
            "error": "Routing failed"
        }
        
        # Test
        result = await daily_scheduler.process_event(event_data)
        
        assert result.success is False
        assert "Routing failed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_call_query_function_with_registered_function(self, daily_scheduler):
        """Test calling registered query function."""
        # Setup
        async def mock_query_func(event_data):
            return DiaryContextData(
                user_profile={"user_id": event_data.user_id},
                event_details={"event_name": event_data.event_name},
                environmental_context={"weather": "sunny"},
                social_context={},
                emotional_context={},
                temporal_context={"timestamp": event_data.timestamp}
            )
        
        daily_scheduler.register_query_function("weather_events", mock_query_func)
        event_data = self.create_sample_event_data()
        
        # Test
        context_data = await daily_scheduler._call_query_function(event_data)
        
        assert isinstance(context_data, DiaryContextData)
        assert context_data.user_profile["user_id"] == event_data.user_id
        assert context_data.environmental_context["weather"] == "sunny"
    
    @pytest.mark.asyncio
    async def test_call_query_function_without_registered_function(self, daily_scheduler, mock_event_router):
        """Test calling query function when none is registered."""
        # Setup
        event_data = self.create_sample_event_data()
        
        # Test
        context_data = await daily_scheduler._call_query_function(event_data)
        
        assert isinstance(context_data, DiaryContextData)
        assert context_data.user_profile["user_id"] == event_data.user_id
        assert context_data.event_details["event_name"] == event_data.event_name
    
    @pytest.mark.asyncio
    async def test_force_generate_diary(self, daily_scheduler, mock_event_router):
        """Test force diary generation bypassing quota."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 0  # No quota
        
        event_data = self.create_sample_event_data()
        mock_event_router.is_claimed_event.return_value = False
        
        # Test
        result = await daily_scheduler.force_generate_diary(event_data)
        
        assert result.success is True
        assert result.diary_entry is not None
    
    def test_get_daily_status_no_quota(self, daily_scheduler):
        """Test getting daily status when no quota is set."""
        status = daily_scheduler.get_daily_status()
        
        assert status["status"] == "no_quota_set"
        assert "not yet determined" in status["message"]
    
    @pytest.mark.asyncio
    async def test_get_daily_status_with_quota(self, daily_scheduler):
        """Test getting daily status with quota set."""
        # Setup
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 3
        daily_scheduler.current_quota.current_count = 1
        daily_scheduler.current_quota.completed_event_types = ["weather_events"]
        
        # Test
        status = daily_scheduler.get_daily_status()
        
        assert status["quota"]["total"] == 3
        assert status["quota"]["current"] == 1
        assert status["quota"]["remaining"] == 2
        assert "weather_events" in status["completed_event_types"]
        assert status["is_complete"] is False
    
    def test_get_generation_history(self, daily_scheduler):
        """Test getting generation history."""
        # Setup
        result1 = DiaryGenerationResult(
            success=True,
            diary_entry=self.create_sample_diary_entry(),
            agent_type="weather_agent",
            event_type="weather_events",
            generation_time=datetime.now()
        )
        result2 = DiaryGenerationResult(
            success=False,
            error_message="Test error",
            agent_type="friends_agent",
            event_type="friends_function"
        )
        
        daily_scheduler.daily_generation_results = [result1, result2]
        
        # Test
        history = daily_scheduler.get_generation_history()
        
        assert len(history) == 2
        assert history[0]["success"] is True
        assert history[0]["agent_type"] == "weather_agent"
        assert history[1]["success"] is False
        assert history[1]["error_message"] == "Test error"
    
    def test_get_generation_history_with_limit(self, daily_scheduler):
        """Test getting generation history with limit."""
        # Setup
        results = [
            DiaryGenerationResult(success=True, agent_type=f"agent_{i}")
            for i in range(5)
        ]
        daily_scheduler.daily_generation_results = results
        
        # Test
        history = daily_scheduler.get_generation_history(limit=3)
        
        assert len(history) == 3
        assert history[0]["agent_type"] == "agent_2"  # Last 3 results
        assert history[2]["agent_type"] == "agent_4"
    
    def test_get_available_emotional_tags(self, daily_scheduler):
        """Test getting available emotional tags."""
        tags = daily_scheduler.get_available_emotional_tags()
        
        assert len(tags) == 10  # All EmotionalTag values
        assert "生气愤怒" in tags
        assert "开心快乐" in tags
        assert "平静" in tags
    
    def test_select_random_emotional_tags(self, daily_scheduler):
        """Test selecting random emotional tags."""
        # Test single tag selection
        tags = daily_scheduler.select_random_emotional_tags(count=1)
        assert len(tags) == 1
        assert isinstance(tags[0], EmotionalTag)
        
        # Test multiple tag selection
        tags = daily_scheduler.select_random_emotional_tags(count=3)
        assert len(tags) == 3
        assert len(set(tags)) == 3  # All unique
        
        # Test count exceeding available tags
        tags = daily_scheduler.select_random_emotional_tags(count=20)
        assert len(tags) == 10  # Maximum available
    
    def test_register_query_function(self, daily_scheduler):
        """Test registering query function."""
        async def test_func(event_data):
            return {"test": "data"}
        
        daily_scheduler.register_query_function("test_events", test_func)
        
        assert "test_events" in daily_scheduler.query_functions
        assert daily_scheduler.query_functions["test_events"] == test_func
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, daily_scheduler):
        """Test scheduler start and stop functionality."""
        # Test start
        await daily_scheduler.start_scheduler()
        assert daily_scheduler.is_running is True
        assert daily_scheduler.scheduler_task is not None
        
        # Test stop
        await daily_scheduler.stop_scheduler()
        assert daily_scheduler.is_running is False
    
    @pytest.mark.asyncio
    async def test_should_reset_daily_quota_new_day(self, daily_scheduler):
        """Test quota reset detection for new day."""
        # Setup current quota for yesterday
        yesterday = datetime.now() - timedelta(days=1)
        daily_scheduler.current_quota = DailyQuota(
            date=yesterday.date(),
            total_quota=3
        )
        
        # Test
        current_time = datetime.now().replace(hour=0, minute=5)  # 00:05 today
        should_reset = daily_scheduler._should_reset_daily_quota(current_time)
        
        assert should_reset is True
    
    @pytest.mark.asyncio
    async def test_should_reset_daily_quota_same_day_before_schedule(self, daily_scheduler):
        """Test quota reset detection for same day before schedule time."""
        # Setup current quota for today
        today = datetime.now()
        daily_scheduler.current_quota = DailyQuota(
            date=today.date(),
            total_quota=3
        )
        
        # Test with time before schedule (23:59)
        current_time = datetime.now().replace(hour=23, minute=59)
        should_reset = daily_scheduler._should_reset_daily_quota(current_time)
        
        assert should_reset is False
    
    @pytest.mark.asyncio
    async def test_alternative_approach_event_type_selection(self, daily_scheduler, mock_event_router):
        """Test alternative approach for selecting event types."""
        # Setup
        mock_event_router.get_available_event_types_for_today.return_value = [
            "weather_events", "friends_function", "holiday_events"
        ]
        
        await daily_scheduler._reset_daily_quota()
        daily_scheduler.current_quota.total_quota = 2
        
        # Test
        await daily_scheduler._select_event_types_for_today()
        
        # Verify pre-selected types are stored
        assert "pre_selected_types" in daily_scheduler.current_quota.metadata
        selected_types = daily_scheduler.current_quota.metadata["pre_selected_types"]
        assert len(selected_types) == 2
        assert all(t in ["weather_events", "friends_function", "holiday_events"] for t in selected_types)


class TestDailyScheduleConfig:
    """Test cases for DailyScheduleConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DailyScheduleConfig()
        
        assert config.schedule_time == time(0, 0)
        assert config.min_quota == 0
        assert config.max_quota == 5
        assert config.claimed_events_always_generate is True
        assert config.random_selection_probability == 0.6
        assert config.alternative_approach_enabled is True
        assert config.max_retries_per_event == 3
        assert config.storage_enabled is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = DailyScheduleConfig(
            schedule_time=time(1, 30),
            min_quota=1,
            max_quota=3,
            claimed_events_always_generate=False,
            random_selection_probability=0.8,
            alternative_approach_enabled=False,
            max_retries_per_event=5,
            storage_enabled=False
        )
        
        assert config.schedule_time == time(1, 30)
        assert config.min_quota == 1
        assert config.max_quota == 3
        assert config.claimed_events_always_generate is False
        assert config.random_selection_probability == 0.8
        assert config.alternative_approach_enabled is False
        assert config.max_retries_per_event == 5
        assert config.storage_enabled is False


class TestDiaryGenerationResult:
    """Test cases for DiaryGenerationResult."""
    
    def test_successful_result(self):
        """Test successful diary generation result."""
        diary_entry = DiaryEntry(
            entry_id="test_001",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="favorite_weather",
            title="晴天",
            content="今天天气很好",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        result = DiaryGenerationResult(
            success=True,
            diary_entry=diary_entry,
            agent_type="weather_agent",
            event_type="weather_events",
            generation_time=datetime.now()
        )
        
        assert result.success is True
        assert result.diary_entry == diary_entry
        assert result.agent_type == "weather_agent"
        assert result.event_type == "weather_events"
        assert result.error_message is None
        assert result.generation_time is not None
    
    def test_failed_result(self):
        """Test failed diary generation result."""
        result = DiaryGenerationResult(
            success=False,
            error_message="Generation failed",
            agent_type="weather_agent",
            event_type="weather_events"
        )
        
        assert result.success is False
        assert result.diary_entry is None
        assert result.error_message == "Generation failed"
        assert result.agent_type == "weather_agent"
        assert result.event_type == "weather_events"
        assert result.generation_time is None


if __name__ == "__main__":
    pytest.main([__file__])