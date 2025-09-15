"""
Unit tests for SameFrequencyAgent.
Tests same frequency synchronization diary generation functionality.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from diary_agent.agents.same_frequency_agent import SameFrequencyAgent
from diary_agent.integration.frequency_data_reader import FrequencyDataReader
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, EmotionalTag
)
from diary_agent.core.llm_manager import LLMConfigManager


class TestSameFrequencyAgent:
    """Test cases for SameFrequencyAgent."""
    
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
        """Create mock frequency data reader."""
        reader = Mock(spec=FrequencyDataReader)
        reader.read_event_context = AsyncMock()
        return reader
    
    @pytest.fixture
    def prompt_config(self):
        """Create test prompt configuration."""
        return PromptConfig(
            agent_type="same_frequency_agent",
            system_prompt="Test system prompt for same frequency",
            user_prompt_template="Test prompt: {event_name} at {timestamp}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
    
    @pytest.fixture
    def frequency_agent(self, prompt_config, mock_llm_manager, mock_data_reader):
        """Create SameFrequencyAgent instance for testing."""
        agent = SameFrequencyAgent(
            agent_type="same_frequency_agent",
            prompt_config=prompt_config,
            llm_manager=mock_llm_manager,
            data_reader=mock_data_reader
        )
        # Override the read_event_context method to return the mock data directly
        agent.read_event_context = AsyncMock()
        return agent
    
    @pytest.fixture
    def sample_event_data(self):
        """Create sample event data for testing."""
        return EventData(
            event_id="test_freq_123",
            event_type="frequency",
            event_name="close_friend_frequency",
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
            user_id=1,
            context_data={},
            metadata={
                "friend_id": 2,
                "interaction_type": "摸摸脸",
                "time_difference_seconds": 1.5
            }
        )
    
    @pytest.fixture
    def sample_context_data(self):
        """Create sample context data for testing."""
        return DiaryContextData(
            user_profile={
                "id": 1,
                "name": "TestUser",
                "role": "lively",
                "update_x_value": 2,
                "update_y_value": 1,
                "intimacy_value": 5
            },
            event_details={
                "event_name": "close_friend_frequency",
                "event_type": "synchronization",
                "chinese_name": "玩具同频事件",
                "english_name": "Toy Frequency Event",
                "synchronization_window": "5 seconds",
                "friend_id": 2,
                "synchronized_interaction": "摸摸脸",
                "time_difference_seconds": 1.5,
                "synchronization_quality": "excellent",
                "frequency_event_detected": True,
                "emotion_impact": {
                    "x_change": 3,
                    "y_change_logic": {"x_greater_equal_0": 3},
                    "weights": {"lively": 1, "clam": 1}
                }
            },
            environmental_context={},
            social_context={
                "user_role": "lively",
                "close_friends_count": 3,
                "close_friends_list": [2, 3, 4],
                "synchronization_partner": {
                    "friend_id": 2,
                    "is_close_friend": True,
                    "synchronized_interaction": "摸摸脸"
                },
                "recent_interactions": {
                    "total_interactions": 2,
                    "interaction_types": {"摸摸脸": 2}
                }
            },
            emotional_context={
                "current_x": 2,
                "current_y": 1,
                "emotional_tone": "positive",
                "synchronization_impact": "bonding",
                "emotional_intensity": 1.0,
                "synchronization_strength": "excellent"
            },
            temporal_context={
                "timestamp": datetime(2024, 1, 15, 14, 30, 0),
                "time_of_day": "afternoon",
                "synchronization_window": "5 seconds",
                "time_difference_seconds": 1.5,
                "synchronization_precision": "1.5s",
                "within_window": True
            }
        )
    
    def test_get_supported_events(self, frequency_agent):
        """Test that agent returns correct supported events."""
        expected_events = ["close_friend_frequency"]
        assert frequency_agent.get_supported_events() == expected_events
    
    def test_get_agent_type(self, frequency_agent):
        """Test that agent returns correct type."""
        assert frequency_agent.get_agent_type() == "same_frequency_agent"
    
    @pytest.mark.asyncio
    async def test_process_event_success(self, frequency_agent, sample_event_data, 
                                       sample_context_data, mock_llm_manager, mock_data_reader):
        """Test successful event processing."""
        # Setup mocks
        frequency_agent.read_event_context.return_value = sample_context_data
        mock_llm_manager.generate_text_with_failover.return_value = '''
        {
            "title": "同频了",
            "content": "和朋友同时摸摸脸，太神奇了✨",
            "emotion_tags": ["惊讶震惊"]
        }
        '''
        
        # Process event
        result = await frequency_agent.process_event(sample_event_data)
        
        # Verify result
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "close_friend_frequency"
        assert result.user_id == 1
        assert result.title == "同频了"
        assert "同时" in result.content or "同频" in result.content
        assert EmotionalTag.SURPRISED_SHOCKED in result.emotion_tags
        assert result.agent_type == "same_frequency_agent"
    
    @pytest.mark.asyncio
    async def test_process_unsupported_event(self, frequency_agent, sample_event_data):
        """Test processing unsupported event raises ValueError."""
        sample_event_data.event_name = "unsupported_event"
        
        with pytest.raises(ValueError, match="Unsupported event"):
            await frequency_agent.process_event(sample_event_data)
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_llm_success(self, frequency_agent, sample_event_data,
                                                    sample_context_data, mock_llm_manager):
        """Test successful LLM diary content generation."""
        mock_llm_manager.generate_text_with_failover.return_value = '''
        {
            "title": "完美同步",
            "content": "和朋友完美同步摸摸脸！",
            "emotion_tags": ["兴奋激动"]
        }
        '''
        
        result = await frequency_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "完美同步"
        assert result["content"] == "和朋友完美同步摸摸脸！"
        # The emotion tags are enhanced by the agent based on synchronization strength
        # With "excellent" synchronization, it should return "惊讶震惊"
        assert "惊讶震惊" in result["emotion_tags"] or "兴奋激动" in result["emotion_tags"]
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_llm_failure_fallback(self, frequency_agent, 
                                                             sample_event_data, sample_context_data,
                                                             mock_llm_manager):
        """Test fallback when LLM generation fails."""
        mock_llm_manager.generate_text_with_failover.side_effect = Exception("LLM failed")
        
        result = await frequency_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        assert "title" in result
        assert "content" in result
        assert "emotion_tags" in result
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_select_frequency_emotion_tags_perfect_sync(self, frequency_agent, sample_context_data):
        """Test emotion tag selection for perfect synchronization."""
        sample_context_data.emotional_context["synchronization_strength"] = "perfect"
        tags = frequency_agent._select_frequency_emotion_tags("close_friend_frequency", sample_context_data)
        assert EmotionalTag.EXCITED_THRILLED.value in tags
    
    def test_select_frequency_emotion_tags_excellent_sync(self, frequency_agent, sample_context_data):
        """Test emotion tag selection for excellent synchronization."""
        sample_context_data.emotional_context["synchronization_strength"] = "excellent"
        tags = frequency_agent._select_frequency_emotion_tags("close_friend_frequency", sample_context_data)
        assert EmotionalTag.SURPRISED_SHOCKED.value in tags
    
    def test_select_frequency_emotion_tags_good_sync(self, frequency_agent, sample_context_data):
        """Test emotion tag selection for good synchronization."""
        sample_context_data.emotional_context["synchronization_strength"] = "good"
        tags = frequency_agent._select_frequency_emotion_tags("close_friend_frequency", sample_context_data)
        assert EmotionalTag.SURPRISED_SHOCKED.value in tags
    
    def test_select_frequency_emotion_tags_acceptable_sync(self, frequency_agent, sample_context_data):
        """Test emotion tag selection for acceptable synchronization."""
        sample_context_data.emotional_context["synchronization_strength"] = "acceptable"
        tags = frequency_agent._select_frequency_emotion_tags("close_friend_frequency", sample_context_data)
        assert EmotionalTag.HAPPY_JOYFUL.value in tags
    
    def test_select_frequency_emotion_tags_unknown_sync(self, frequency_agent, sample_context_data):
        """Test emotion tag selection for unknown synchronization."""
        sample_context_data.emotional_context["synchronization_strength"] = "unknown"
        tags = frequency_agent._select_frequency_emotion_tags("close_friend_frequency", sample_context_data)
        assert EmotionalTag.CURIOUS.value in tags
    
    def test_generate_frequency_fallback_content_perfect_sync(self, frequency_agent, 
                                                            sample_event_data, sample_context_data):
        """Test fallback content generation for perfect synchronization."""
        sample_context_data.event_details["synchronization_quality"] = "perfect"
        sample_context_data.social_context["user_role"] = "lively"
        
        result = frequency_agent._generate_frequency_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "完美同步"
        assert "同时" in result["content"] and "摸摸脸" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
        assert len(result["emotion_tags"]) > 0
    
    def test_generate_frequency_fallback_content_excellent_sync(self, frequency_agent, 
                                                              sample_event_data, sample_context_data):
        """Test fallback content generation for excellent synchronization."""
        sample_context_data.event_details["synchronization_quality"] = "excellent"
        sample_context_data.social_context["user_role"] = "clam"
        
        result = frequency_agent._generate_frequency_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "同频了"
        assert "朋友" in result["content"] and "摸摸脸" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_generate_frequency_fallback_content_good_sync(self, frequency_agent, 
                                                         sample_event_data, sample_context_data):
        """Test fallback content generation for good synchronization."""
        sample_context_data.event_details["synchronization_quality"] = "good"
        
        result = frequency_agent._generate_frequency_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "巧合"
        assert "朋友" in result["content"] and "摸摸脸" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_generate_frequency_fallback_content_acceptable_sync(self, frequency_agent, 
                                                               sample_event_data, sample_context_data):
        """Test fallback content generation for acceptable synchronization."""
        sample_context_data.event_details["synchronization_quality"] = "acceptable"
        sample_context_data.temporal_context["time_difference_seconds"] = 3.2
        
        result = frequency_agent._generate_frequency_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "同步"
        assert "3.2秒" in result["content"] and "摸摸脸" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_generate_frequency_fallback_content_unknown_sync(self, frequency_agent, 
                                                            sample_event_data, sample_context_data):
        """Test fallback content generation for unknown synchronization."""
        sample_context_data.event_details["synchronization_quality"] = "unknown"
        
        result = frequency_agent._generate_frequency_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "同频"
        assert "同频" in result["content"] and "摸摸脸" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_create_fallback_entry(self, frequency_agent, sample_event_data, sample_context_data):
        """Test creation of fallback diary entry."""
        # Modify context to have "excellent" synchronization which should return SURPRISED_SHOCKED
        sample_context_data.emotional_context["synchronization_strength"] = "excellent"
        
        entry = frequency_agent._create_fallback_entry(sample_event_data, sample_context_data)
        
        assert isinstance(entry, DiaryEntry)
        assert entry.user_id == sample_event_data.user_id
        assert entry.event_name == sample_event_data.event_name
        assert entry.agent_type == "same_frequency_agent"
        assert entry.llm_provider == "fallback"
        assert len(entry.title) <= 6
        assert len(entry.content) <= 35
        assert len(entry.emotion_tags) > 0
        # With excellent synchronization, should return SURPRISED_SHOCKED
        assert EmotionalTag.SURPRISED_SHOCKED in entry.emotion_tags


if __name__ == "__main__":
    pytest.main([__file__])