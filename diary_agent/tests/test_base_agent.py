"""
Unit tests for base agent architecture and interface.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from diary_agent.agents.base_agent import (
    BaseSubAgent, AgentRegistry, AgentFactory
)
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, 
    EmotionalTag, DataReader, LLMConfig
)
from diary_agent.core.llm_manager import LLMConfigManager, LLMProviderError


class MockSubAgent(BaseSubAgent):
    """Mock sub-agent for testing."""
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """Mock implementation of process_event."""
        context_data = await self.read_event_context(event_data)
        content_dict = await self.generate_diary_content(event_data, context_data)
        entry = await self._create_diary_entry(event_data, content_dict)
        return self.format_output(entry)
    
    def get_supported_events(self) -> list:
        """Mock implementation of get_supported_events."""
        return ["test_event", "mock_event"]


class MockDataReader(DataReader):
    """Mock data reader for testing."""
    
    def __init__(self):
        super().__init__("mock_module")
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """Mock implementation of read_event_context."""
        return DiaryContextData(
            user_profile={"role": "test_user", "name": "Test User"},
            event_details={"event_name": event_data.event_name},
            environmental_context={"weather": "sunny"},
            social_context={"friends": []},
            emotional_context={"mood": "happy"},
            temporal_context={"timestamp": event_data.timestamp}
        )
    
    def get_user_preferences(self, user_id: int) -> dict:
        """Mock implementation of get_user_preferences."""
        return {"favorite_weather": "sunny", "role": "test_user"}


@pytest.fixture
def mock_llm_manager():
    """Create mock LLM manager."""
    manager = Mock(spec=LLMConfigManager)
    manager.generate_text_with_failover = AsyncMock(return_value='{"title": "测试", "content": "这是一个测试日记", "emotion_tags": ["开心快乐"]}')
    manager.get_current_provider = Mock(return_value=Mock(provider_name="test_provider"))
    return manager


@pytest.fixture
def mock_prompt_config():
    """Create mock prompt configuration."""
    return PromptConfig(
        agent_type="test_agent",
        system_prompt="You are a test diary agent.",
        user_prompt_template="Write about {event_name} at {timestamp}",
        output_format={"title": "string", "content": "string", "emotion_tags": "list"},
        validation_rules={"title_max_length": 6, "content_max_length": 35}
    )


@pytest.fixture
def mock_data_reader():
    """Create mock data reader."""
    return MockDataReader()


@pytest.fixture
def sample_event_data():
    """Create sample event data."""
    return EventData(
        event_id="test_001",
        event_type="test_events",
        event_name="test_event",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={}
    )


@pytest.fixture
def mock_agent(mock_prompt_config, mock_llm_manager, mock_data_reader):
    """Create mock agent instance."""
    return MockSubAgent(
        agent_type="test_agent",
        prompt_config=mock_prompt_config,
        llm_manager=mock_llm_manager,
        data_reader=mock_data_reader
    )


class TestBaseSubAgent:
    """Test cases for BaseSubAgent class."""
    
    def test_init(self, mock_prompt_config, mock_llm_manager, mock_data_reader):
        """Test BaseSubAgent initialization."""
        agent = MockSubAgent(
            agent_type="test_agent",
            prompt_config=mock_prompt_config,
            llm_manager=mock_llm_manager,
            data_reader=mock_data_reader
        )
        
        assert agent.agent_type == "test_agent"
        assert agent.prompt_config == mock_prompt_config
        assert agent.llm_manager == mock_llm_manager
        assert agent.data_reader == mock_data_reader
        assert agent.validator is not None
        assert agent.formatter is not None
    
    def test_get_agent_type(self, mock_agent):
        """Test get_agent_type method."""
        assert mock_agent.get_agent_type() == "test_agent"
    
    def test_get_data_reader(self, mock_agent):
        """Test get_data_reader method."""
        data_reader = mock_agent.get_data_reader()
        assert isinstance(data_reader, MockDataReader)
        assert data_reader.module_name == "mock_module"
    
    @pytest.mark.asyncio
    async def test_read_event_context_success(self, mock_agent, sample_event_data):
        """Test successful event context reading."""
        context_data = await mock_agent.read_event_context(sample_event_data)
        
        assert isinstance(context_data, DiaryContextData)
        assert context_data.user_profile["role"] == "test_user"
        assert context_data.event_details["event_name"] == "test_event"
        assert context_data.environmental_context["weather"] == "sunny"
    
    @pytest.mark.asyncio
    async def test_read_event_context_failure(self, mock_agent, sample_event_data):
        """Test event context reading with failure."""
        # Mock data reader to raise exception
        mock_agent.data_reader.read_event_context = Mock(side_effect=Exception("Read error"))
        
        context_data = await mock_agent.read_event_context(sample_event_data)
        
        # Should return minimal context on failure
        assert isinstance(context_data, DiaryContextData)
        assert context_data.user_profile == {}
        assert context_data.event_details["event_name"] == "test_event"
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_success(self, mock_agent, sample_event_data):
        """Test successful diary content generation."""
        context_data = DiaryContextData(
            user_profile={"role": "test_user"},
            event_details={"event_name": "test_event"},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={}
        )
        
        content_dict = await mock_agent.generate_diary_content(sample_event_data, context_data)
        
        assert "title" in content_dict
        assert "content" in content_dict
        assert "emotion_tags" in content_dict
        assert content_dict["title"] == "测试"
        assert content_dict["content"] == "这是一个测试日记"
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_llm_failure(self, mock_agent, sample_event_data):
        """Test diary content generation with LLM failure."""
        # Mock LLM manager to raise exception
        mock_agent.llm_manager.generate_text_with_failover = AsyncMock(
            side_effect=LLMProviderError("LLM failed")
        )
        
        context_data = DiaryContextData(
            user_profile={},
            event_details={},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={}
        )
        
        with pytest.raises(LLMProviderError):
            await mock_agent.generate_diary_content(sample_event_data, context_data)
    
    def test_prepare_user_prompt(self, mock_agent, sample_event_data):
        """Test user prompt preparation."""
        context_data = DiaryContextData(
            user_profile={"role": "test_user"},
            event_details={"event_name": "test_event"},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={}
        )
        
        prompt = mock_agent._prepare_user_prompt(sample_event_data, context_data)
        
        assert "test_event" in prompt
        assert sample_event_data.timestamp.strftime("%Y-%m-%d %H:%M:%S") in prompt
    
    def test_parse_generated_content_json(self, mock_agent):
        """Test parsing valid JSON content."""
        json_content = '{"title": "测试", "content": "测试内容", "emotion_tags": ["开心快乐"]}'
        
        content_dict = mock_agent._parse_generated_content(json_content)
        
        assert content_dict["title"] == "测试"
        assert content_dict["content"] == "测试内容"
        assert content_dict["emotion_tags"] == ["开心快乐"]
    
    def test_parse_generated_content_fallback(self, mock_agent):
        """Test fallback parsing for non-JSON content."""
        text_content = "测试标题\n这是测试内容"
        
        content_dict = mock_agent._parse_generated_content(text_content)
        
        assert "title" in content_dict
        assert "content" in content_dict
        assert "emotion_tags" in content_dict
        assert len(content_dict["title"]) <= 6
        assert len(content_dict["content"]) <= 35
    
    def test_validate_output(self, mock_agent):
        """Test diary entry validation."""
        valid_entry = DiaryEntry(
            entry_id="test_001",
            user_id=1,
            timestamp=datetime.now(),
            event_type="test_events",
            event_name="test_event",
            title="测试",
            content="测试内容",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="test_agent",
            llm_provider="test_provider"
        )
        
        assert mock_agent.validate_output(valid_entry) is True
    
    def test_format_output(self, mock_agent):
        """Test diary entry formatting."""
        entry = DiaryEntry(
            entry_id="test_001",
            user_id=1,
            timestamp=datetime.now(),
            event_type="test_events",
            event_name="test_event",
            title="这是一个很长的标题",  # Too long
            content="这是一个很长的内容，超过了三十五个字符的限制，需要被截断处理",  # Too long
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="test_agent",
            llm_provider="test_provider"
        )
        
        formatted_entry = mock_agent.format_output(entry)
        
        assert len(formatted_entry.title) <= 6
        assert len(formatted_entry.content) <= 35
    
    @pytest.mark.asyncio
    async def test_create_diary_entry(self, mock_agent, sample_event_data):
        """Test diary entry creation."""
        content_dict = {
            "title": "测试",
            "content": "测试内容",
            "emotion_tags": ["开心快乐"]
        }
        
        entry = await mock_agent._create_diary_entry(sample_event_data, content_dict)
        
        assert isinstance(entry, DiaryEntry)
        assert entry.user_id == sample_event_data.user_id
        assert entry.event_type == sample_event_data.event_type
        assert entry.title == "测试"
        assert entry.content == "测试内容"
        assert EmotionalTag.HAPPY_JOYFUL in entry.emotion_tags
    
    @pytest.mark.asyncio
    async def test_process_event_end_to_end(self, mock_agent, sample_event_data):
        """Test complete event processing workflow."""
        entry = await mock_agent.process_event(sample_event_data)
        
        assert isinstance(entry, DiaryEntry)
        assert entry.user_id == sample_event_data.user_id
        assert entry.event_type == sample_event_data.event_type
        assert len(entry.title) <= 6
        assert len(entry.content) <= 35
        assert len(entry.emotion_tags) > 0


class TestAgentRegistry:
    """Test cases for AgentRegistry class."""
    
    def test_init(self):
        """Test AgentRegistry initialization."""
        registry = AgentRegistry()
        
        assert len(registry._agents) == 0
        assert len(registry._event_mappings) == 0
    
    def test_register_agent(self, mock_agent):
        """Test agent registration."""
        registry = AgentRegistry()
        registry.register_agent(mock_agent)
        
        assert "test_agent" in registry._agents
        assert registry._agents["test_agent"] == mock_agent
        assert "test_event" in registry._event_mappings
        assert "mock_event" in registry._event_mappings
        assert registry._event_mappings["test_event"] == "test_agent"
    
    def test_get_agent(self, mock_agent):
        """Test getting agent by type."""
        registry = AgentRegistry()
        registry.register_agent(mock_agent)
        
        retrieved_agent = registry.get_agent("test_agent")
        assert retrieved_agent == mock_agent
        
        non_existent = registry.get_agent("non_existent")
        assert non_existent is None
    
    def test_get_agent_for_event(self, mock_agent):
        """Test getting agent for specific event."""
        registry = AgentRegistry()
        registry.register_agent(mock_agent)
        
        agent = registry.get_agent_for_event("test_event")
        assert agent == mock_agent
        
        no_agent = registry.get_agent_for_event("unknown_event")
        assert no_agent is None
    
    def test_list_agents(self, mock_agent):
        """Test listing registered agents."""
        registry = AgentRegistry()
        registry.register_agent(mock_agent)
        
        agents = registry.list_agents()
        assert "test_agent" in agents
        assert len(agents) == 1
    
    def test_list_supported_events(self, mock_agent):
        """Test listing supported events."""
        registry = AgentRegistry()
        registry.register_agent(mock_agent)
        
        events = registry.list_supported_events()
        assert "test_event" in events
        assert "mock_event" in events
        assert len(events) == 2
    
    def test_get_event_mappings(self, mock_agent):
        """Test getting event mappings."""
        registry = AgentRegistry()
        registry.register_agent(mock_agent)
        
        mappings = registry.get_event_mappings()
        assert mappings["test_event"] == "test_agent"
        assert mappings["mock_event"] == "test_agent"


class TestAgentFactory:
    """Test cases for AgentFactory class."""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary config directory."""
        config_dir = tmp_path / "agent_prompts"
        config_dir.mkdir()
        return str(config_dir)
    
    def test_init(self, mock_llm_manager, temp_config_dir):
        """Test AgentFactory initialization."""
        factory = AgentFactory(mock_llm_manager, temp_config_dir)
        
        assert factory.llm_manager == mock_llm_manager
        assert factory.prompt_config_dir == Path(temp_config_dir)
    
    def test_load_prompt_configurations(self, mock_llm_manager, temp_config_dir):
        """Test loading prompt configurations."""
        # Create test config file
        config_file = Path(temp_config_dir) / "test_agent.json"
        config_data = {
            "agent_type": "test_agent",
            "system_prompt": "Test system prompt",
            "user_prompt_template": "Test template",
            "output_format": {},
            "validation_rules": {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        factory = AgentFactory(mock_llm_manager, temp_config_dir)
        
        assert "test_agent" in factory._prompt_configs
        config = factory._prompt_configs["test_agent"]
        assert config.agent_type == "test_agent"
        assert config.system_prompt == "Test system prompt"
    
    def test_get_prompt_config(self, mock_llm_manager, temp_config_dir):
        """Test getting prompt configuration."""
        factory = AgentFactory(mock_llm_manager, temp_config_dir)
        
        # Should have default configs
        config = factory.get_prompt_config("weather_agent")
        assert config is not None
        assert config.agent_type == "weather_agent"
        
        # Non-existent config
        no_config = factory.get_prompt_config("non_existent")
        assert no_config is None
    
    def test_create_agent_success(self, mock_llm_manager, temp_config_dir, mock_data_reader):
        """Test successful agent creation."""
        factory = AgentFactory(mock_llm_manager, temp_config_dir)
        
        agent = factory.create_agent("weather_agent", MockSubAgent, mock_data_reader)
        
        assert agent is not None
        assert isinstance(agent, MockSubAgent)
        assert agent.agent_type == "weather_agent"
    
    def test_create_agent_no_config(self, mock_llm_manager, temp_config_dir, mock_data_reader):
        """Test agent creation with missing config."""
        factory = AgentFactory(mock_llm_manager, temp_config_dir)
        
        agent = factory.create_agent("non_existent", MockSubAgent, mock_data_reader)
        
        assert agent is None
    
    def test_reload_prompt_configurations(self, mock_llm_manager, temp_config_dir):
        """Test reloading prompt configurations."""
        factory = AgentFactory(mock_llm_manager, temp_config_dir)
        initial_count = len(factory._prompt_configs)
        
        # Add new config file
        new_config_file = Path(temp_config_dir) / "new_agent.json"
        config_data = {
            "agent_type": "new_agent",
            "system_prompt": "New agent prompt",
            "user_prompt_template": "New template",
            "output_format": {},
            "validation_rules": {}
        }
        
        with open(new_config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        factory.reload_prompt_configurations()
        
        assert len(factory._prompt_configs) > initial_count
        assert "new_agent" in factory._prompt_configs
    
    def test_list_available_configs(self, mock_llm_manager, temp_config_dir):
        """Test listing available configurations."""
        factory = AgentFactory(mock_llm_manager, temp_config_dir)
        
        configs = factory.list_available_configs()
        
        assert isinstance(configs, list)
        assert len(configs) > 0
        assert "weather_agent" in configs
        assert "trending_agent" in configs


if __name__ == "__main__":
    pytest.main([__file__])