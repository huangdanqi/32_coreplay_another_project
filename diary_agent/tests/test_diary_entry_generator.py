"""
Unit tests for diary entry generation and formatting system.
"""

import pytest
import asyncio
import json
import tempfile
from datetime import datetime, date
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from diary_agent.core.diary_entry_generator import (
    DiaryEntryGenerator, EmotionalContextProcessor, ChineseTextProcessor
)
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, EmotionalTag, DailyQuota
)
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.agents.base_agent import AgentRegistry, BaseSubAgent


class TestDiaryEntryGenerator:
    """Test cases for DiaryEntryGenerator class."""
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Create mock LLM manager."""
        manager = Mock(spec=LLMConfigManager)
        manager.generate_text_with_failover = AsyncMock(return_value='{"title": "测试", "content": "今天天气很好", "emotion_tags": ["开心快乐"]}')
        return manager
    
    @pytest.fixture
    def mock_agent_registry(self):
        """Create mock agent registry."""
        registry = Mock(spec=AgentRegistry)
        
        # Create mock agent
        mock_agent = Mock(spec=BaseSubAgent)
        mock_agent.process_event = AsyncMock(return_value=DiaryEntry(
            entry_id="test_entry_1",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="favorite_weather",
            title="好天气",
            content="今天阳光明媚，心情很好",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        ))
        
        registry.get_agent_for_event.return_value = mock_agent
        return registry
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def diary_generator(self, mock_llm_manager, mock_agent_registry, temp_storage_path):
        """Create diary entry generator instance."""
        return DiaryEntryGenerator(
            llm_manager=mock_llm_manager,
            agent_registry=mock_agent_registry,
            storage_path=temp_storage_path
        )
    
    @pytest.fixture
    def sample_event_data(self):
        """Create sample event data."""
        return EventData(
            event_id="event_001",
            event_type="weather_events",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"weather": "sunny", "temperature": 25},
            metadata={"location": "Beijing"}
        )
    
    @pytest.mark.asyncio
    async def test_generate_diary_entry_success(self, diary_generator, sample_event_data):
        """Test successful diary entry generation."""
        # Set daily quota
        diary_generator.set_daily_quota(sample_event_data.timestamp, 3)
        
        # Generate diary entry
        result = await diary_generator.generate_diary_entry(sample_event_data)
        
        # Verify result
        assert result is not None
        assert isinstance(result, DiaryEntry)
        assert result.user_id == sample_event_data.user_id
        assert result.event_type == sample_event_data.event_type
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        assert len(result.emotion_tags) > 0
        
        # Verify statistics
        stats = diary_generator.get_generation_stats()
        assert stats["successful_generations"] == 1
        assert stats["total_generated"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_diary_entry_quota_exceeded(self, diary_generator, sample_event_data):
        """Test diary generation when daily quota is exceeded."""
        # Set quota to 0
        diary_generator.set_daily_quota(sample_event_data.timestamp, 0)
        
        # Try to generate diary entry
        result = await diary_generator.generate_diary_entry(sample_event_data)
        
        # Should return None due to quota
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_diary_entry_force_generation(self, diary_generator, sample_event_data):
        """Test forced diary generation bypassing quota."""
        # Set quota to 0
        diary_generator.set_daily_quota(sample_event_data.timestamp, 0)
        
        # Force generation
        result = await diary_generator.generate_diary_entry(sample_event_data, force_generation=True)
        
        # Should succeed despite quota
        assert result is not None
        assert isinstance(result, DiaryEntry)
    
    @pytest.mark.asyncio
    async def test_generate_diary_entry_no_agent(self, diary_generator, sample_event_data, mock_agent_registry):
        """Test diary generation when no agent is found."""
        # Mock registry to return None
        mock_agent_registry.get_agent_for_event.return_value = None
        
        # Set daily quota
        diary_generator.set_daily_quota(sample_event_data.timestamp, 3)
        
        # Try to generate diary entry
        with pytest.raises(ValueError, match="No agent found for event"):
            await diary_generator.generate_diary_entry(sample_event_data)
    
    @pytest.mark.asyncio
    async def test_generate_multiple_entries(self, diary_generator):
        """Test generating multiple diary entries concurrently."""
        # Create multiple events with different event types to avoid daily quota conflicts
        events = []
        event_types = ["weather_events", "trending_events", "holiday_events"]
        event_names = ["favorite_weather", "celebration", "approaching_holiday"]
        
        for i in range(3):
            event = EventData(
                event_id=f"event_{i:03d}",
                event_type=event_types[i],
                event_name=event_names[i],
                timestamp=datetime.now(),
                user_id=1,
                context_data={"weather": "sunny"},
                metadata={}
            )
            events.append(event)
        
        # Set daily quota
        diary_generator.set_daily_quota(datetime.now(), 5)
        
        # Generate multiple entries
        results = await diary_generator.generate_multiple_entries(events, max_concurrent=2)
        
        # Verify results
        assert len(results) == 3
        for result in results:
            assert isinstance(result, DiaryEntry)
    
    def test_format_title_within_limit(self, diary_generator):
        """Test title formatting within character limit."""
        title = "好天气"
        formatted = diary_generator._format_title(title)
        assert formatted == title
        assert len(formatted) <= 6
    
    def test_format_title_exceeds_limit(self, diary_generator):
        """Test title formatting when exceeding character limit."""
        title = "今天是一个非常美好的天气"
        formatted = diary_generator._format_title(title)
        assert len(formatted) <= 6
        assert formatted.endswith("…")
    
    def test_format_title_empty(self, diary_generator):
        """Test title formatting with empty input."""
        title = ""
        formatted = diary_generator._format_title(title)
        assert formatted == "日记"
    
    def test_format_content_within_limit(self, diary_generator):
        """Test content formatting within character limit."""
        content = "今天天气很好，心情愉快"
        formatted = diary_generator._format_content(content)
        assert formatted == content
        assert len(formatted) <= 35
    
    def test_format_content_exceeds_limit(self, diary_generator):
        """Test content formatting when exceeding character limit."""
        content = "今天是一个非常美好的天气，阳光明媚，微风徐徐，让人心情愉快，想要出去散步"
        formatted = diary_generator._format_content(content)
        assert len(formatted) <= 35
        assert formatted.endswith("...")
    
    def test_format_content_with_emoji(self, diary_generator):
        """Test content formatting with emojis."""
        content = "今天天气很好😊🌞，心情愉快😄"
        formatted = diary_generator._format_content(content)
        assert len(formatted) <= 35
        # Should preserve emojis if possible
        assert "😊" in formatted or "🌞" in formatted or "😄" in formatted
    
    def test_format_content_empty(self, diary_generator):
        """Test content formatting with empty input."""
        content = ""
        formatted = diary_generator._format_content(content)
        assert formatted == "今天发生了一些事情"
    
    def test_format_emotion_tags_valid(self, diary_generator):
        """Test emotion tags formatting with valid tags."""
        tags = [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED]
        formatted = diary_generator._format_emotion_tags(tags)
        assert formatted == tags
        assert len(formatted) <= 3
    
    def test_format_emotion_tags_empty(self, diary_generator):
        """Test emotion tags formatting with empty input."""
        tags = []
        formatted = diary_generator._format_emotion_tags(tags)
        assert formatted == [EmotionalTag.CALM]
    
    def test_format_emotion_tags_string_conversion(self, diary_generator):
        """Test emotion tags formatting with string inputs."""
        tags = ["开心快乐", "兴奋激动"]
        formatted = diary_generator._format_emotion_tags(tags)
        assert len(formatted) == 2
        assert EmotionalTag.HAPPY_JOYFUL in formatted
        assert EmotionalTag.EXCITED_THRILLED in formatted
    
    def test_format_emotion_tags_too_many(self, diary_generator):
        """Test emotion tags formatting with too many tags."""
        tags = [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED, 
                EmotionalTag.CURIOUS, EmotionalTag.CALM]
        formatted = diary_generator._format_emotion_tags(tags)
        assert len(formatted) <= 3
    
    def test_format_entry_id_existing(self, diary_generator):
        """Test entry ID formatting with existing ID."""
        entry = DiaryEntry(
            entry_id="existing_id",
            user_id=1,
            timestamp=datetime.now(),
            event_type="test",
            event_name="test",
            title="test",
            content="test",
            emotion_tags=[EmotionalTag.CALM],
            agent_type="test",
            llm_provider="test"
        )
        formatted_id = diary_generator._format_entry_id(entry)
        assert formatted_id == "existing_id"
    
    def test_format_entry_id_missing(self, diary_generator):
        """Test entry ID formatting with missing ID."""
        entry = DiaryEntry(
            entry_id="",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="test",
            title="test",
            content="test",
            emotion_tags=[EmotionalTag.CALM],
            agent_type="test",
            llm_provider="test"
        )
        formatted_id = diary_generator._format_entry_id(entry)
        assert formatted_id.startswith("diary_1_")
        assert "weather_events" in formatted_id
    
    def test_set_daily_quota(self, diary_generator):
        """Test setting daily quota."""
        test_date = datetime(2024, 1, 1)
        diary_generator.set_daily_quota(test_date, 3)
        
        quota = diary_generator.get_daily_quota(test_date)
        assert quota is not None
        assert quota.total_quota == 3
        assert quota.current_count == 0
    
    def test_set_daily_quota_bounds(self, diary_generator):
        """Test daily quota bounds enforcement."""
        test_date = datetime(2024, 1, 1)
        
        # Test upper bound
        diary_generator.set_daily_quota(test_date, 10)
        quota = diary_generator.get_daily_quota(test_date)
        assert quota.total_quota == 5
        
        # Test lower bound
        diary_generator.set_daily_quota(test_date, -1)
        quota = diary_generator.get_daily_quota(test_date)
        assert quota.total_quota == 0
    
    def test_can_generate_diary_with_quota(self, diary_generator, sample_event_data):
        """Test diary generation permission with available quota."""
        diary_generator.set_daily_quota(sample_event_data.timestamp, 3)
        
        can_generate = diary_generator._can_generate_diary(sample_event_data)
        assert can_generate is True
    
    def test_can_generate_diary_no_quota(self, diary_generator, sample_event_data):
        """Test diary generation permission with no quota."""
        diary_generator.set_daily_quota(sample_event_data.timestamp, 0)
        
        can_generate = diary_generator._can_generate_diary(sample_event_data)
        assert can_generate is False
    
    def test_update_daily_quota(self, diary_generator, sample_event_data):
        """Test updating daily quota after generation."""
        diary_generator.set_daily_quota(sample_event_data.timestamp, 3)
        
        # Update quota
        diary_generator._update_daily_quota(sample_event_data)
        
        # Check quota state
        quota = diary_generator.get_daily_quota(sample_event_data.timestamp)
        assert quota.current_count == 1
        assert sample_event_data.event_type in quota.completed_event_types
    
    @pytest.mark.asyncio
    async def test_store_diary_entry(self, diary_generator, temp_storage_path):
        """Test storing diary entry to file system."""
        entry = DiaryEntry(
            entry_id="test_entry",
            user_id=1,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="weather_events",
            event_name="favorite_weather",
            title="好天气",
            content="今天天气很好",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        await diary_generator._store_diary_entry(entry)
        
        # Verify file was created
        expected_path = Path(temp_storage_path) / "user_1" / "diary_2024-01-01.json"
        assert expected_path.exists()
        
        # Verify content
        with open(expected_path, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)
        
        assert len(stored_data) == 1
        assert stored_data[0]["entry_id"] == "test_entry"
        assert stored_data[0]["title"] == "好天气"
    
    @pytest.mark.asyncio
    async def test_load_diary_entries(self, diary_generator, temp_storage_path):
        """Test loading diary entries from file system."""
        # First store an entry
        entry = DiaryEntry(
            entry_id="test_entry",
            user_id=1,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="weather_events",
            event_name="favorite_weather",
            title="好天气",
            content="今天天气很好",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        await diary_generator._store_diary_entry(entry)
        
        # Load entries
        loaded_entries = await diary_generator.load_diary_entries(1, datetime(2024, 1, 1))
        
        assert len(loaded_entries) == 1
        loaded_entry = loaded_entries[0]
        assert loaded_entry.entry_id == "test_entry"
        assert loaded_entry.title == "好天气"
        assert loaded_entry.emotion_tags == [EmotionalTag.HAPPY_JOYFUL]
    
    def test_get_generation_stats(self, diary_generator):
        """Test getting generation statistics."""
        stats = diary_generator.get_generation_stats()
        
        expected_keys = [
            "total_generated", "successful_generations", "failed_generations",
            "validation_failures", "formatting_corrections"
        ]
        
        for key in expected_keys:
            assert key in stats
            assert isinstance(stats[key], int)
    
    def test_reset_generation_stats(self, diary_generator):
        """Test resetting generation statistics."""
        # Modify stats
        diary_generator.generation_stats["total_generated"] = 10
        
        # Reset
        diary_generator.reset_generation_stats()
        
        # Verify reset
        stats = diary_generator.get_generation_stats()
        assert stats["total_generated"] == 0


class TestEmotionalContextProcessor:
    """Test cases for EmotionalContextProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create emotional context processor instance."""
        return EmotionalContextProcessor()
    
    @pytest.fixture
    def sample_context_data(self):
        """Create sample context data."""
        return DiaryContextData(
            user_profile={"role": "clam", "name": "test_user"},
            event_details={"weather": "sunny", "temperature": 25},
            environmental_context={"location": "Beijing"},
            social_context={"friends_count": 5},
            emotional_context={"mood": "happy"},
            temporal_context={"season": "spring"}
        )
    
    def test_process_emotional_context_positive_weather(self, processor, sample_context_data):
        """Test emotional context processing for positive weather events."""
        event_data = EventData(
            event_id="test",
            event_type="weather_events",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        emotions = processor.process_emotional_context(sample_context_data, event_data)
        
        assert len(emotions) >= 1
        assert len(emotions) <= 2
        # Should contain positive emotions
        positive_emotions = [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM, EmotionalTag.EXCITED_THRILLED]
        assert any(emotion in positive_emotions for emotion in emotions)
    
    def test_process_emotional_context_negative_weather(self, processor, sample_context_data):
        """Test emotional context processing for negative weather events."""
        event_data = EventData(
            event_id="test",
            event_type="weather_events",
            event_name="dislike_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        emotions = processor.process_emotional_context(sample_context_data, event_data)
        
        assert len(emotions) >= 1
        assert len(emotions) <= 2
        # Should contain negative emotions
        negative_emotions = [EmotionalTag.SAD_UPSET, EmotionalTag.WORRIED, EmotionalTag.ANXIOUS_MELANCHOLY]
        assert any(emotion in negative_emotions for emotion in emotions)
    
    def test_process_emotional_context_celebration(self, processor, sample_context_data):
        """Test emotional context processing for celebration events."""
        event_data = EventData(
            event_id="test",
            event_type="trending_events",
            event_name="celebration",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        emotions = processor.process_emotional_context(sample_context_data, event_data)
        
        assert len(emotions) >= 1
        celebration_emotions = [EmotionalTag.EXCITED_THRILLED, EmotionalTag.HAPPY_JOYFUL]
        assert any(emotion in celebration_emotions for emotion in emotions)
    
    def test_process_emotional_context_disaster(self, processor, sample_context_data):
        """Test emotional context processing for disaster events."""
        event_data = EventData(
            event_id="test",
            event_type="trending_events",
            event_name="disaster",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        emotions = processor.process_emotional_context(sample_context_data, event_data)
        
        assert len(emotions) >= 1
        disaster_emotions = [EmotionalTag.WORRIED, EmotionalTag.SAD_UPSET]
        assert any(emotion in disaster_emotions for emotion in emotions)
    
    def test_process_emotional_context_neutral(self, processor, sample_context_data):
        """Test emotional context processing for neutral events."""
        event_data = EventData(
            event_id="test",
            event_type="unknown_events",
            event_name="unknown_event",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        emotions = processor.process_emotional_context(sample_context_data, event_data)
        
        assert len(emotions) >= 1
        # Should default to neutral emotions
        assert EmotionalTag.CALM in emotions or EmotionalTag.CURIOUS in emotions
    
    def test_validate_emotional_consistency_valid(self, processor):
        """Test emotional consistency validation with valid emotions."""
        emotions = [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED]
        is_consistent = processor.validate_emotional_consistency(emotions, "positive event")
        assert is_consistent is True
    
    def test_validate_emotional_consistency_conflicting(self, processor):
        """Test emotional consistency validation with conflicting emotions."""
        emotions = [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.SAD_UPSET]
        is_consistent = processor.validate_emotional_consistency(emotions, "mixed event")
        assert is_consistent is False
    
    def test_validate_emotional_consistency_single_emotion(self, processor):
        """Test emotional consistency validation with single emotion."""
        emotions = [EmotionalTag.CALM]
        is_consistent = processor.validate_emotional_consistency(emotions, "neutral event")
        assert is_consistent is True


class TestChineseTextProcessor:
    """Test cases for ChineseTextProcessor class."""
    
    def test_count_chinese_characters_chinese_only(self):
        """Test counting Chinese characters in Chinese-only text."""
        text = "今天天气很好"
        count = ChineseTextProcessor.count_chinese_characters(text)
        assert count == 6
    
    def test_count_chinese_characters_mixed(self):
        """Test counting Chinese characters in mixed text."""
        text = "今天temperature是25度"
        count = ChineseTextProcessor.count_chinese_characters(text)
        assert count == 4  # 今天度
    
    def test_count_chinese_characters_no_chinese(self):
        """Test counting Chinese characters in non-Chinese text."""
        text = "Hello World 123"
        count = ChineseTextProcessor.count_chinese_characters(text)
        assert count == 0
    
    def test_is_valid_chinese_diary_content_valid(self):
        """Test validation of valid Chinese diary content."""
        text = "今天天气很好，心情愉快"
        is_valid = ChineseTextProcessor.is_valid_chinese_diary_content(text)
        assert is_valid is True
    
    def test_is_valid_chinese_diary_content_no_chinese(self):
        """Test validation of content without Chinese characters."""
        text = "Hello World"
        is_valid = ChineseTextProcessor.is_valid_chinese_diary_content(text)
        assert is_valid is False
    
    def test_is_valid_chinese_diary_content_empty(self):
        """Test validation of empty content."""
        text = ""
        is_valid = ChineseTextProcessor.is_valid_chinese_diary_content(text)
        assert is_valid is False
    
    def test_format_chinese_diary_text_within_limit(self):
        """Test formatting Chinese text within length limit."""
        text = "今天天气很好"
        formatted = ChineseTextProcessor.format_chinese_diary_text(text, 10)
        assert formatted == text
        assert len(formatted) <= 10
    
    def test_format_chinese_diary_text_exceeds_limit(self):
        """Test formatting Chinese text exceeding length limit."""
        text = "今天天气非常好，阳光明媚，微风徐徐"
        formatted = ChineseTextProcessor.format_chinese_diary_text(text, 10)
        assert len(formatted) <= 10
        assert formatted.endswith("…")
    
    def test_format_chinese_diary_text_with_punctuation(self):
        """Test formatting Chinese text with natural break points."""
        text = "今天天气很好。心情愉快，想要出去散步"
        formatted = ChineseTextProcessor.format_chinese_diary_text(text, 8)
        assert len(formatted) <= 8
        # Should break at punctuation if possible
        assert formatted.endswith("。") or formatted.endswith("…")
    
    def test_format_chinese_diary_text_excessive_punctuation(self):
        """Test formatting Chinese text with excessive punctuation."""
        text = "今天天气很好！！！心情愉快？？？"
        formatted = ChineseTextProcessor.format_chinese_diary_text(text, 20)
        # Should clean up excessive punctuation
        assert "！！！" not in formatted
        assert "？？？" not in formatted


class TestDailyQuota:
    """Test cases for DailyQuota class."""
    
    def test_daily_quota_initialization(self):
        """Test daily quota initialization."""
        test_date = date(2024, 1, 1)
        quota = DailyQuota(date=test_date, total_quota=3)
        
        assert quota.date == test_date
        assert quota.total_quota == 3
        assert quota.current_count == 0
        assert quota.completed_event_types == []
    
    def test_can_generate_diary_available_quota(self):
        """Test diary generation permission with available quota."""
        quota = DailyQuota(date=date.today(), total_quota=3)
        
        can_generate = quota.can_generate_diary("weather_events")
        assert can_generate is True
    
    def test_can_generate_diary_quota_exceeded(self):
        """Test diary generation permission when quota is exceeded."""
        quota = DailyQuota(date=date.today(), total_quota=1, current_count=1)
        
        can_generate = quota.can_generate_diary("weather_events")
        assert can_generate is False
    
    def test_can_generate_diary_event_type_completed(self):
        """Test diary generation permission when event type already completed."""
        quota = DailyQuota(
            date=date.today(), 
            total_quota=3, 
            current_count=1,
            completed_event_types=["weather_events"]
        )
        
        can_generate = quota.can_generate_diary("weather_events")
        assert can_generate is False
    
    def test_add_diary_entry_new_event_type(self):
        """Test adding diary entry for new event type."""
        quota = DailyQuota(date=date.today(), total_quota=3)
        
        quota.add_diary_entry("weather_events")
        
        assert quota.current_count == 1
        assert "weather_events" in quota.completed_event_types
    
    def test_add_diary_entry_existing_event_type(self):
        """Test adding diary entry for existing event type."""
        quota = DailyQuota(
            date=date.today(), 
            total_quota=3,
            completed_event_types=["weather_events"]
        )
        
        initial_count = quota.current_count
        quota.add_diary_entry("weather_events")
        
        # Should not increment count for existing event type
        assert quota.current_count == initial_count
        assert quota.completed_event_types.count("weather_events") == 1


if __name__ == "__main__":
    pytest.main([__file__])