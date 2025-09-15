"""
Unit tests for TrendingAgent.
Tests trending news event processing and diary generation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from diary_agent.agents.trending_agent import TrendingAgent
from diary_agent.integration.trending_data_reader import TrendingDataReader
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, EmotionalTag
)
from diary_agent.core.llm_manager import LLMConfigManager


class TestTrendingAgent:
    """Test cases for TrendingAgent."""
    
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
        """Create mock trending data reader."""
        reader = Mock(spec=TrendingDataReader)
        reader.read_event_context = Mock()
        return reader
    
    @pytest.fixture
    def prompt_config(self):
        """Create test prompt configuration."""
        return PromptConfig(
            agent_type="trending_agent",
            system_prompt="Test system prompt for trending events",
            user_prompt_template="Test template: {event_name} at {timestamp}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
    
    @pytest.fixture
    def trending_agent(self, prompt_config, mock_llm_manager, mock_data_reader):
        """Create TrendingAgent instance for testing."""
        return TrendingAgent(
            agent_type="trending_agent",
            prompt_config=prompt_config,
            llm_manager=mock_llm_manager,
            data_reader=mock_data_reader
        )
    
    @pytest.fixture
    def sample_event_data(self):
        """Create sample event data for testing."""
        return EventData(
            event_id="test_event_123",
            event_type="trending",
            event_name="celebration",
            timestamp=datetime(2024, 1, 15, 14, 30),
            user_id=1,
            context_data={},
            metadata={"douyin_file_path": "test_file.json", "page_size": 50}
        )
    
    @pytest.fixture
    def sample_context_data(self):
        """Create sample context data for testing."""
        return DiaryContextData(
            user_profile={"id": 1, "name": "test_user", "role": "lively"},
            event_details={
                "event_name": "celebration",
                "event_type": "trending",
                "classification": "celebration",
                "user_role": "lively",
                "matched_keywords": ["演唱会", "明星"],
                "sample_trending_words": ["演唱会", "明星", "可爱", "挑战", "加油"]
            },
            environmental_context={
                "news_environment": "social_media",
                "information_source": "douyin_trending",
                "trending_context": "celebration"
            },
            social_context={
                "trending_words": ["演唱会", "明星", "可爱", "挑战", "加油"],
                "event_classification": "celebration",
                "social_sentiment": "positive",
                "trending_topics": ["演唱会", "明星见面会"]
            },
            emotional_context={
                "event_emotional_impact": "high_positive",
                "social_emotional_tone": "joyful",
                "emotional_intensity": 2.0
            },
            temporal_context={
                "timestamp": datetime(2024, 1, 15, 14, 30),
                "time_of_day": "afternoon"
            }
        )
    
    def test_initialization(self, trending_agent):
        """Test TrendingAgent initialization."""
        assert trending_agent.agent_type == "trending_agent"
        assert trending_agent.get_supported_events() == ["celebration", "disaster"]
    
    def test_get_supported_events(self, trending_agent):
        """Test getting supported events."""
        events = trending_agent.get_supported_events()
        assert isinstance(events, list)
        assert "celebration" in events
        assert "disaster" in events
        assert len(events) == 2
    
    @pytest.mark.asyncio
    async def test_process_event_success(self, trending_agent, sample_event_data, sample_context_data):
        """Test successful event processing."""
        # Mock the data reader
        trending_agent.data_reader.read_event_context.return_value = sample_context_data
        
        # Mock LLM response
        llm_response = '{"title": "演唱会", "content": "今天看到明星演唱会的消息，很兴奋😊", "emotion_tags": ["兴奋激动"]}'
        trending_agent.llm_manager.generate_text_with_failover.return_value = llm_response
        
        # Process event
        result = await trending_agent.process_event(sample_event_data)
        
        # Verify result
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "celebration"
        assert result.agent_type == "trending_agent"
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        assert len(result.emotion_tags) > 0
    
    @pytest.mark.asyncio
    async def test_process_unsupported_event(self, trending_agent, sample_event_data):
        """Test processing unsupported event."""
        sample_event_data.event_name = "unsupported_event"
        
        with pytest.raises(ValueError, match="Unsupported event"):
            await trending_agent.process_event(sample_event_data)
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_success(self, trending_agent, sample_event_data, sample_context_data):
        """Test successful diary content generation."""
        # Mock LLM response
        llm_response = '{"title": "好消息", "content": "看到演唱会的消息，心情很好😄", "emotion_tags": ["开心快乐"]}'
        trending_agent.llm_manager.generate_text_with_failover.return_value = llm_response
        
        # Generate content
        result = await trending_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        # Verify result
        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        assert "emotion_tags" in result
        assert result["emotion_tags"] == ["兴奋激动"]  # Should be enhanced by agent
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_fallback(self, trending_agent, sample_event_data, sample_context_data):
        """Test diary content generation with fallback."""
        # Mock LLM failure
        trending_agent.llm_manager.generate_text_with_failover.side_effect = Exception("LLM failed")
        
        # Generate content (should use fallback)
        result = await trending_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        # Verify fallback result
        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        assert "emotion_tags" in result
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_select_trending_emotion_tags_celebration(self, trending_agent):
        """Test emotion tag selection for celebration events."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={},
            environmental_context={},
            social_context={"social_sentiment": "positive"},
            emotional_context={"emotional_intensity": 2.0},
            temporal_context={}
        )
        
        tags = trending_agent._select_trending_emotion_tags("celebration", context_data)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert tags[0] == EmotionalTag.EXCITED_THRILLED.value
    
    def test_select_trending_emotion_tags_disaster(self, trending_agent):
        """Test emotion tag selection for disaster events."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={},
            environmental_context={},
            social_context={"social_sentiment": "negative"},
            emotional_context={"emotional_intensity": 1.5},
            temporal_context={}
        )
        
        tags = trending_agent._select_trending_emotion_tags("disaster", context_data)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert tags[0] == EmotionalTag.ANGRY_FURIOUS.value
    
    def test_generate_trending_fallback_content_celebration(self, trending_agent, sample_event_data, sample_context_data):
        """Test fallback content generation for celebration events."""
        result = trending_agent._generate_trending_fallback_content(sample_event_data, sample_context_data)
        
        assert isinstance(result, dict)
        assert result["title"] == "开心"
        assert "演唱会" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
        assert isinstance(result["emotion_tags"], list)
    
    def test_generate_trending_fallback_content_disaster(self, trending_agent, sample_context_data):
        """Test fallback content generation for disaster events."""
        disaster_event = EventData(
            event_id="disaster_123",
            event_type="trending",
            event_name="disaster",
            timestamp=datetime(2024, 1, 15, 14, 30),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        # Update context for disaster
        sample_context_data.social_context["trending_topics"] = ["地震", "灾难"]
        
        result = trending_agent._generate_trending_fallback_content(disaster_event, sample_context_data)
        
        assert isinstance(result, dict)
        assert result["title"] == "担心"
        assert "地震" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
        assert isinstance(result["emotion_tags"], list)
    
    def test_prepare_trending_prompt(self, trending_agent, sample_event_data, sample_context_data):
        """Test trending prompt preparation."""
        prompt = trending_agent._prepare_trending_prompt(sample_event_data, sample_context_data)
        
        assert isinstance(prompt, str)
        assert "celebration" in prompt
        assert "演唱会" in prompt
        assert "2024-01-15 14:30" in prompt
        assert "lively" in prompt
        assert "positive" in prompt
    
    def test_create_fallback_entry(self, trending_agent, sample_event_data, sample_context_data):
        """Test fallback diary entry creation."""
        entry = trending_agent._create_fallback_entry(sample_event_data, sample_context_data)
        
        assert isinstance(entry, DiaryEntry)
        assert entry.event_name == "celebration"
        assert entry.agent_type == "trending_agent"
        assert entry.llm_provider == "fallback"
        assert len(entry.title) <= 6
        assert len(entry.content) <= 35
        assert len(entry.emotion_tags) > 0


@pytest.mark.asyncio
async def test_trending_agent_integration():
    """Integration test for TrendingAgent with real components."""
    # This test would require actual LLM and data reader setup
    # For now, we'll test the basic integration flow
    
    # Mock components
    llm_manager = Mock(spec=LLMConfigManager)
    llm_manager.generate_text_with_failover = AsyncMock()
    llm_manager.get_current_provider = Mock()
    llm_manager.get_current_provider.return_value = Mock(provider_name="test")
    
    data_reader = Mock(spec=TrendingDataReader)
    
    prompt_config = PromptConfig(
        agent_type="trending_agent",
        system_prompt="Test prompt",
        user_prompt_template="Test: {event_name}",
        output_format={},
        validation_rules={}
    )
    
    # Create agent
    agent = TrendingAgent("trending_agent", prompt_config, llm_manager, data_reader)
    
    # Verify initialization
    assert agent.agent_type == "trending_agent"
    assert "celebration" in agent.get_supported_events()
    assert "disaster" in agent.get_supported_events()


if __name__ == "__main__":
    pytest.main([__file__])