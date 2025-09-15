"""
Unit tests for AdoptionAgent.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from diary_agent.agents.adoption_agent import AdoptionAgent, create_adoption_agent
from diary_agent.utils.data_models import EventData, DiaryEntry, PromptConfig, EmotionalTag
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.integration.adoption_data_reader import AdoptionDataReader


class TestAdoptionAgent:
    """Test cases for AdoptionAgent."""
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Create mock LLM manager."""
        manager = Mock(spec=LLMConfigManager)
        manager.generate_text_with_failover = AsyncMock()
        manager.get_current_provider = Mock()
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.provider_name = "test_provider"
        manager.get_current_provider.return_value = mock_provider
        
        return manager
    
    @pytest.fixture
    def mock_data_reader(self):
        """Create mock adoption data reader."""
        reader = Mock(spec=AdoptionDataReader)
        reader.read_event_context = AsyncMock()
        reader.get_user_preferences = Mock()
        reader.get_adoption_event_info = Mock()
        reader.get_supported_events = Mock(return_value=["toy_claimed"])
        return reader
    
    @pytest.fixture
    def prompt_config(self):
        """Create test prompt configuration."""
        return PromptConfig(
            agent_type="adoption_agent",
            system_prompt="Test system prompt for adoption events",
            user_prompt_template="Test user prompt: {event_name} at {timestamp}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
    
    @pytest.fixture
    def adoption_agent(self, prompt_config, mock_llm_manager, mock_data_reader):
        """Create AdoptionAgent instance for testing."""
        return AdoptionAgent(
            agent_type="adoption_agent",
            prompt_config=prompt_config,
            llm_manager=mock_llm_manager,
            data_reader=mock_data_reader
        )
    
    @pytest.fixture
    def sample_event_data(self):
        """Create sample event data for testing."""
        return EventData(
            event_id="test_adoption_001",
            event_type="adoption_event",
            event_name="toy_claimed",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
    
    def test_initialization(self, adoption_agent, mock_data_reader):
        """Test agent initialization."""
        assert adoption_agent.agent_type == "adoption_agent"
        assert adoption_agent.adoption_data_reader == mock_data_reader
        assert isinstance(adoption_agent.adoption_data_reader, Mock)
    
    def test_get_supported_events(self, adoption_agent):
        """Test getting supported events."""
        events = adoption_agent.get_supported_events()
        assert "toy_claimed" in events
        assert len(events) == 1
    
    @pytest.mark.asyncio
    async def test_process_event_success(self, adoption_agent, sample_event_data, mock_llm_manager, mock_data_reader):
        """Test successful event processing."""
        # Mock context data
        from diary_agent.utils.data_models import DiaryContextData
        mock_context = DiaryContextData(
            user_profile={"user_id": 1, "name": "TestUser", "role": "lively"},
            event_details={"event_name": "toy_claimed"},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": sample_event_data.timestamp}
        )
        mock_data_reader.read_event_context.return_value = mock_context
        
        # Mock LLM response
        mock_llm_response = '{"title": "被认领", "content": "今天被主人认领了！好开心！🎉", "emotion_tags": ["开心快乐", "兴奋激动"]}'
        mock_llm_manager.generate_text_with_failover.return_value = mock_llm_response
        
        # Process event
        result = await adoption_agent.process_event(sample_event_data)
        
        # Verify result
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "toy_claimed"
        assert result.user_id == 1
        assert result.agent_type == "adoption_agent"
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        
        # Verify LLM was called
        mock_llm_manager.generate_text_with_failover.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_event_unsupported(self, adoption_agent, sample_event_data):
        """Test processing unsupported event."""
        sample_event_data.event_name = "unsupported_event"
        
        with pytest.raises(ValueError, match="Unsupported adoption event"):
            await adoption_agent.process_event(sample_event_data)
    
    @pytest.mark.asyncio
    async def test_process_event_llm_failure_fallback(self, adoption_agent, sample_event_data, mock_llm_manager, mock_data_reader):
        """Test fallback when LLM generation fails."""
        # Mock context data
        from diary_agent.utils.data_models import DiaryContextData
        mock_context = DiaryContextData(
            user_profile={"user_id": 1, "name": "TestUser", "role": "lively"},
            event_details={"event_name": "toy_claimed"},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": sample_event_data.timestamp}
        )
        mock_data_reader.read_event_context.return_value = mock_context
        
        # Mock LLM failure (invalid JSON)
        mock_llm_manager.generate_text_with_failover.return_value = "Invalid JSON response"
        
        # Mock validation failure to trigger fallback
        with patch.object(adoption_agent, 'validate_output', return_value=False):
            result = await adoption_agent.process_event(sample_event_data)
        
        # Verify fallback entry was created
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "toy_claimed"
        assert "被认领" in result.title or "认领" in result.content
    
    def test_create_fallback_entry(self, adoption_agent, sample_event_data):
        """Test fallback entry creation."""
        from diary_agent.utils.data_models import DiaryContextData
        
        mock_context = DiaryContextData(
            user_profile={"name": "TestUser"},
            event_details={},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={}
        )
        
        result = adoption_agent._create_fallback_entry(sample_event_data, mock_context)
        
        assert isinstance(result, DiaryEntry)
        assert result.title == "被认领"
        assert "TestUser" in result.content
        assert "认领" in result.content
        assert EmotionalTag.HAPPY in result.emotion_tags
    
    def test_get_adoption_event_config(self, adoption_agent, mock_data_reader):
        """Test getting adoption event configuration."""
        mock_config = {"probability": 1.0, "x_change": 2}
        mock_data_reader.get_adoption_event_info.return_value = mock_config
        
        result = adoption_agent.get_adoption_event_config("toy_claimed")
        
        assert result == mock_config
        mock_data_reader.get_adoption_event_info.assert_called_once_with("toy_claimed")
    
    def test_get_user_adoption_preferences(self, adoption_agent, mock_data_reader):
        """Test getting user adoption preferences."""
        mock_preferences = {"role": "lively", "emotional_baseline": {"x": 0, "y": 0}}
        mock_data_reader.get_user_preferences.return_value = mock_preferences
        
        result = adoption_agent.get_user_adoption_preferences(1)
        
        assert result == mock_preferences
        mock_data_reader.get_user_preferences.assert_called_once_with(1)


class TestCreateAdoptionAgent:
    """Test cases for adoption agent factory function."""
    
    def test_create_adoption_agent(self):
        """Test creating adoption agent via factory function."""
        mock_llm_manager = Mock(spec=LLMConfigManager)
        prompt_config = PromptConfig(
            agent_type="adoption_agent",
            system_prompt="Test prompt",
            user_prompt_template="Test template",
            output_format={},
            validation_rules={}
        )
        
        agent = create_adoption_agent(mock_llm_manager, prompt_config)
        
        assert isinstance(agent, AdoptionAgent)
        assert agent.agent_type == "adoption_agent"
        assert agent.llm_manager == mock_llm_manager
        assert isinstance(agent.adoption_data_reader, AdoptionDataReader)


if __name__ == "__main__":
    pytest.main([__file__])