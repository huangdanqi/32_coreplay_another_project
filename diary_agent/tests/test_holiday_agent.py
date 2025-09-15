"""
Unit tests for HolidayAgent.
Tests holiday event processing and diary generation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from diary_agent.agents.holiday_agent import HolidayAgent
from diary_agent.integration.holiday_data_reader import HolidayDataReader
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, EmotionalTag
)
from diary_agent.core.llm_manager import LLMConfigManager


class TestHolidayAgent:
    """Test cases for HolidayAgent."""
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Create mock LLM manager."""
        manager = Mock(spec=LLMConfigManager)
        manager.generate_text_with_failover = AsyncMock()
        manager.get_current_provider = Mock()
        manager.get_current_provider.return_value = Mock(provider_name="test_provider")
        return manager
    
    @pytest.fixture
    def mock_data_reader(self):
        """Create mock holiday data reader."""
        reader = Mock(spec=HolidayDataReader)
        reader.read_event_context = Mock()
        return reader
    
    @pytest.fixture
    def prompt_config(self):
        """Create test prompt configuration."""
        return PromptConfig(
            agent_type="holiday_agent",
            system_prompt="Test system prompt for holiday events",
            user_prompt_template="Test template: {event_name} at {timestamp}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
    
    @pytest.fixture
    def holiday_agent(self, prompt_config, mock_llm_manager, mock_data_reader):
        """Create HolidayAgent instance for testing."""
        return HolidayAgent(
            agent_type="holiday_agent",
            prompt_config=prompt_config,
            llm_manager=mock_llm_manager,
            data_reader=mock_data_reader
        )
    
    @pytest.fixture
    def sample_event_data(self):
        """Create sample event data for testing."""
        return EventData(
            event_id="test_holiday_123",
            event_type="holiday",
            event_name="approaching_holiday",
            timestamp=datetime(2024, 1, 28, 10, 0),  # 3 days before Spring Festival
            user_id=1,
            context_data={},
            metadata={"event_date": "2024-01-28"}
        )
    
    @pytest.fixture
    def sample_context_data(self):
        """Create sample context data for testing."""
        return DiaryContextData(
            user_profile={"id": 1, "name": "test_user", "role": "lively"},
            event_details={
                "event_name": "approaching_holiday",
                "event_type": "holiday",
                "holiday_name": "春节",
                "holiday_date": "2024-02-01",
                "holiday_duration": 7,
                "user_role": "lively",
                "is_major_holiday": True,
                "emotion_impact": {"x_change": 2, "y_change": 2, "intimacy_change": 0}
            },
            environmental_context={
                "holiday_atmosphere": "anticipatory_festive",
                "seasonal_context": "winter",
                "cultural_environment": "chinese_traditional",
                "celebration_scale": "national_major"
            },
            social_context={
                "holiday_type": "traditional_major",
                "cultural_significance": "highest",
                "typical_activities": ["团圆", "拜年", "放鞭炮", "吃年夜饭"],
                "social_expectations": "preparation_excitement",
                "family_context": "anticipation_planning"
            },
            emotional_context={
                "holiday_emotional_tone": "anticipation_excitement",
                "anticipation_level": "very_high",
                "emotional_intensity": 2.0,
                "holiday_stress_level": "moderate"
            },
            temporal_context={
                "timestamp": datetime(2024, 1, 28, 10, 0),
                "event_date": datetime(2024, 1, 28),
                "holiday_year": 2024,
                "related_holiday": {"name": "春节", "date": "2024-02-01"},
                "days_to_holiday": 4,
                "holiday_season": "winter_spring",
                "time_of_day": "morning"
            }
        )
    
    def test_initialization(self, holiday_agent):
        """Test HolidayAgent initialization."""
        assert holiday_agent.agent_type == "holiday_agent"
        assert holiday_agent.get_supported_events() == ["approaching_holiday", "during_holiday", "holiday_ends"]
    
    def test_get_supported_events(self, holiday_agent):
        """Test getting supported events."""
        events = holiday_agent.get_supported_events()
        assert isinstance(events, list)
        assert "approaching_holiday" in events
        assert "during_holiday" in events
        assert "holiday_ends" in events
        assert len(events) == 3
    
    @pytest.mark.asyncio
    async def test_process_event_success(self, holiday_agent, sample_event_data, sample_context_data):
        """Test successful event processing."""
        # Mock the data reader
        holiday_agent.data_reader.read_event_context.return_value = sample_context_data
        
        # Mock LLM response
        llm_response = '{"title": "春节快到", "content": "还有4天就是春节了，好期待啊🎉", "emotion_tags": ["兴奋激动"]}'
        holiday_agent.llm_manager.generate_text_with_failover.return_value = llm_response
        
        # Process event
        result = await holiday_agent.process_event(sample_event_data)
        
        # Verify result
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "approaching_holiday"
        assert result.agent_type == "holiday_agent"
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        assert len(result.emotion_tags) > 0
    
    @pytest.mark.asyncio
    async def test_process_unsupported_event(self, holiday_agent, sample_event_data):
        """Test processing unsupported event."""
        sample_event_data.event_name = "unsupported_event"
        
        with pytest.raises(ValueError, match="Unsupported event"):
            await holiday_agent.process_event(sample_event_data)
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_success(self, holiday_agent, sample_event_data, sample_context_data):
        """Test successful diary content generation."""
        # Mock LLM response
        llm_response = '{"title": "期待", "content": "春节快到了，准备回家过年😊", "emotion_tags": ["开心快乐"]}'
        holiday_agent.llm_manager.generate_text_with_failover.return_value = llm_response
        
        # Generate content
        result = await holiday_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        # Verify result
        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        assert "emotion_tags" in result
        assert result["emotion_tags"] == ["兴奋激动"]  # Should be enhanced by agent
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_fallback(self, holiday_agent, sample_event_data, sample_context_data):
        """Test diary content generation with fallback."""
        # Mock LLM failure
        holiday_agent.llm_manager.generate_text_with_failover.side_effect = Exception("LLM failed")
        
        # Generate content (should use fallback)
        result = await holiday_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        # Verify fallback result
        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        assert "emotion_tags" in result
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_select_holiday_emotion_tags_approaching(self, holiday_agent):
        """Test emotion tag selection for approaching holiday events."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={"holiday_name": "春节"},
            environmental_context={},
            social_context={},
            emotional_context={"anticipation_level": "very_high", "emotional_intensity": 2.0},
            temporal_context={}
        )
        
        tags = holiday_agent._select_holiday_emotion_tags("approaching_holiday", context_data)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert tags[0] == EmotionalTag.EXCITED_THRILLED.value
    
    def test_select_holiday_emotion_tags_during(self, holiday_agent):
        """Test emotion tag selection for during holiday events."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={},
            environmental_context={},
            social_context={},
            emotional_context={"emotional_intensity": 2.0},
            temporal_context={}
        )
        
        tags = holiday_agent._select_holiday_emotion_tags("during_holiday", context_data)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert tags[0] == EmotionalTag.EXCITED_THRILLED.value
    
    def test_select_holiday_emotion_tags_ends(self, holiday_agent):
        """Test emotion tag selection for holiday ending events."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={},
            environmental_context={},
            social_context={},
            emotional_context={"emotional_intensity": 1.5},
            temporal_context={}
        )
        
        tags = holiday_agent._select_holiday_emotion_tags("holiday_ends", context_data)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert tags[0] == EmotionalTag.SAD_UPSET.value
    
    def test_generate_holiday_fallback_content_approaching(self, holiday_agent, sample_event_data, sample_context_data):
        """Test fallback content generation for approaching holiday events."""
        result = holiday_agent._generate_holiday_fallback_content(sample_event_data, sample_context_data)
        
        assert isinstance(result, dict)
        assert result["title"] == "期待"
        assert "春节" in result["content"]
        assert "4天" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
        assert isinstance(result["emotion_tags"], list)
    
    def test_generate_holiday_fallback_content_during(self, holiday_agent, sample_context_data):
        """Test fallback content generation for during holiday events."""
        during_event = EventData(
            event_id="during_123",
            event_type="holiday",
            event_name="during_holiday",
            timestamp=datetime(2024, 2, 1, 12, 0),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = holiday_agent._generate_holiday_fallback_content(during_event, sample_context_data)
        
        assert isinstance(result, dict)
        assert result["title"] == "假期"
        assert "春节" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
        assert isinstance(result["emotion_tags"], list)
    
    def test_generate_holiday_fallback_content_ends(self, holiday_agent, sample_context_data):
        """Test fallback content generation for holiday ending events."""
        ends_event = EventData(
            event_id="ends_123",
            event_type="holiday",
            event_name="holiday_ends",
            timestamp=datetime(2024, 2, 8, 18, 0),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = holiday_agent._generate_holiday_fallback_content(ends_event, sample_context_data)
        
        assert isinstance(result, dict)
        assert result["title"] == "结束"
        assert "春节" in result["content"]
        assert "结束" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
        assert isinstance(result["emotion_tags"], list)
    
    def test_prepare_holiday_prompt(self, holiday_agent, sample_event_data, sample_context_data):
        """Test holiday prompt preparation."""
        prompt = holiday_agent._prepare_holiday_prompt(sample_event_data, sample_context_data)
        
        assert isinstance(prompt, str)
        assert "approaching_holiday" in prompt
        assert "春节" in prompt
        assert "2024-01-28 10:00" in prompt
        assert "lively" in prompt
        assert "还有4天" in prompt
        assert "团圆" in prompt
    
    def test_create_fallback_entry(self, holiday_agent, sample_event_data, sample_context_data):
        """Test fallback diary entry creation."""
        entry = holiday_agent._create_fallback_entry(sample_event_data, sample_context_data)
        
        assert isinstance(entry, DiaryEntry)
        assert entry.event_name == "approaching_holiday"
        assert entry.agent_type == "holiday_agent"
        assert entry.llm_provider == "fallback"
        assert len(entry.title) <= 6
        assert len(entry.content) <= 35
        assert len(entry.emotion_tags) > 0


@pytest.mark.asyncio
async def test_holiday_agent_integration():
    """Integration test for HolidayAgent with real components."""
    # This test would require actual LLM and data reader setup
    # For now, we'll test the basic integration flow
    
    # Mock components
    llm_manager = Mock(spec=LLMConfigManager)
    llm_manager.generate_text_with_failover = AsyncMock()
    llm_manager.get_current_provider = Mock()
    llm_manager.get_current_provider.return_value = Mock(provider_name="test")
    
    data_reader = Mock(spec=HolidayDataReader)
    
    prompt_config = PromptConfig(
        agent_type="holiday_agent",
        system_prompt="Test prompt",
        user_prompt_template="Test: {event_name}",
        output_format={},
        validation_rules={}
    )
    
    # Create agent
    agent = HolidayAgent("holiday_agent", prompt_config, llm_manager, data_reader)
    
    # Verify initialization
    assert agent.agent_type == "holiday_agent"
    assert "approaching_holiday" in agent.get_supported_events()
    assert "during_holiday" in agent.get_supported_events()
    assert "holiday_ends" in agent.get_supported_events()


if __name__ == "__main__":
    pytest.main([__file__])