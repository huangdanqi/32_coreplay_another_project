"""
Simple test to verify daily scheduler basic functionality.
"""

import asyncio
from unittest.mock import Mock
from datetime import datetime

from diary_agent.core.daily_scheduler import DailyScheduler, DailyScheduleConfig
from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag


def test_scheduler_creation():
    """Test that scheduler can be created with mocked dependencies."""
    # Create mock dependencies
    mock_event_router = Mock()
    mock_sub_agent_manager = Mock()
    mock_diary_generator = Mock()
    mock_data_persistence = Mock()
    
    # Create scheduler
    scheduler = DailyScheduler(
        event_router=mock_event_router,
        sub_agent_manager=mock_sub_agent_manager,
        diary_generator=mock_diary_generator,
        data_persistence=mock_data_persistence
    )
    
    assert scheduler is not None
    assert scheduler.config.max_quota == 5
    assert scheduler.config.min_quota == 0
    print("✓ Scheduler creation test passed")


async def test_quota_reset():
    """Test daily quota reset functionality."""
    # Create mock dependencies
    mock_event_router = Mock()
    mock_event_router.update_daily_quota = Mock()
    mock_event_router.get_available_event_types_for_today = Mock(return_value=["weather_events"])
    
    mock_sub_agent_manager = Mock()
    mock_diary_generator = Mock()
    mock_data_persistence = Mock()
    
    # Create scheduler
    scheduler = DailyScheduler(
        event_router=mock_event_router,
        sub_agent_manager=mock_sub_agent_manager,
        diary_generator=mock_diary_generator,
        data_persistence=mock_data_persistence
    )
    
    # Test quota reset
    await scheduler._reset_daily_quota()
    
    assert scheduler.current_quota is not None
    assert 0 <= scheduler.current_quota.total_quota <= 5
    assert scheduler.current_quota.current_count == 0
    print("✓ Quota reset test passed")


def test_emotional_tags():
    """Test emotional tag functionality."""
    # Create mock dependencies
    mock_event_router = Mock()
    mock_sub_agent_manager = Mock()
    mock_diary_generator = Mock()
    mock_data_persistence = Mock()
    
    # Create scheduler
    scheduler = DailyScheduler(
        event_router=mock_event_router,
        sub_agent_manager=mock_sub_agent_manager,
        diary_generator=mock_diary_generator,
        data_persistence=mock_data_persistence
    )
    
    # Test emotional tags
    tags = scheduler.get_available_emotional_tags()
    assert len(tags) == 10
    assert "生气愤怒" in tags
    assert "开心快乐" in tags
    
    # Test random selection
    random_tags = scheduler.select_random_emotional_tags(count=2)
    assert len(random_tags) == 2
    assert all(isinstance(tag, EmotionalTag) for tag in random_tags)
    
    print("✓ Emotional tags test passed")


def test_query_function_registration():
    """Test query function registration."""
    # Create mock dependencies
    mock_event_router = Mock()
    mock_sub_agent_manager = Mock()
    mock_diary_generator = Mock()
    mock_data_persistence = Mock()
    
    # Create scheduler
    scheduler = DailyScheduler(
        event_router=mock_event_router,
        sub_agent_manager=mock_sub_agent_manager,
        diary_generator=mock_diary_generator,
        data_persistence=mock_data_persistence
    )
    
    # Test query function registration
    async def test_query_func(event_data):
        return {"test": "data"}
    
    scheduler.register_query_function("test_events", test_query_func)
    
    assert "test_events" in scheduler.query_functions
    assert scheduler.query_functions["test_events"] == test_query_func
    
    print("✓ Query function registration test passed")


async def main():
    """Run all tests."""
    print("Running Daily Scheduler Simple Tests...")
    
    test_scheduler_creation()
    await test_quota_reset()
    test_emotional_tags()
    test_query_function_registration()
    
    print("✓ All simple tests passed!")


if __name__ == "__main__":
    asyncio.run(main())