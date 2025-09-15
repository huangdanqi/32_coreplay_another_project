"""
Simple validation test to verify test infrastructure is working.
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from diary_agent.utils.data_models import EventData, DiaryEntry
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestSimpleValidation:
    """Simple validation tests for test infrastructure."""
    
    def test_basic_functionality(self):
        """Test basic Python functionality."""
        assert 1 + 1 == 2
        assert "test" == "test"
        assert len([1, 2, 3]) == 3
    
    def test_datetime_functionality(self):
        """Test datetime functionality."""
        now = datetime.now()
        assert isinstance(now, datetime)
        assert now.year >= 2024
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="diary_agent imports not available")
    def test_data_models_import(self):
        """Test that data models can be imported."""
        # Test EventData creation
        event = EventData(
            event_id="test_1",
            event_type="test_events",
            event_name="test_event",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"test": "data"},
            metadata={"source": "test"}
        )
        
        assert event.event_id == "test_1"
        assert event.user_id == 1
        assert event.context_data["test"] == "data"
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="diary_agent imports not available")
    def test_diary_entry_creation(self):
        """Test diary entry creation."""
        diary = DiaryEntry(
            entry_id="diary_1",
            user_id=1,
            timestamp=datetime.now(),
            event_type="test_events",
            event_name="test_event",
            title="测试",
            content="这是一个测试日记",
            emotion_tags=["平静"],
            agent_type="test_agent",
            llm_provider="test_provider"
        )
        
        assert diary.entry_id == "diary_1"
        assert diary.title == "测试"
        assert len(diary.title) <= 6
        assert len(diary.content) <= 35
        assert "平静" in diary.emotion_tags
    
    def test_chinese_text_handling(self):
        """Test Chinese text handling."""
        chinese_text = "今天天气很好"
        assert len(chinese_text) == 6
        assert "天气" in chinese_text
        
        # Test emoji handling
        emoji_text = "开心😊"
        assert "😊" in emoji_text
    
    def test_formatting_constraints(self):
        """Test diary formatting constraints."""
        # Test title length constraint
        title = "测试标题"
        assert len(title) <= 6
        
        # Test content length constraint  
        content = "今天是一个很好的日子，心情特别愉快"
        assert len(content) <= 35
        
        # Test with emojis
        emoji_content = "今天心情很好😊阳光明媚🌞"
        # Note: emojis count as characters but may take more bytes
        char_count = len(emoji_content)
        assert char_count <= 35
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality works."""
        import asyncio
        
        async def async_operation():
            await asyncio.sleep(0.01)  # 10ms delay
            return "async_result"
        
        result = await async_operation()
        assert result == "async_result"
    
    def test_emotional_tags_validation(self):
        """Test emotional tags validation."""
        valid_emotions = [
            "生气愤怒", "悲伤难过", "担忧", "焦虑忧愁", "惊讶震惊",
            "好奇", "羞愧", "平静", "开心快乐", "兴奋激动"
        ]
        
        # Test all emotions are strings
        for emotion in valid_emotions:
            assert isinstance(emotion, str)
            assert len(emotion) > 0
        
        # Test specific emotions
        assert "开心快乐" in valid_emotions
        assert "悲伤难过" in valid_emotions
        assert "平静" in valid_emotions