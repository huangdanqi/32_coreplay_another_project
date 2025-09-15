"""
Unit tests for SubAgentManager class.
Tests agent lifecycle management, initialization, configuration loading, and failure handling.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from diary_agent.core.sub_agent_manager import SubAgentManager, AgentFailureError
from diary_agent.core.llm_manager import LLMConfigManager, LLMProviderError
from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag, DataReader


class MockAgent(BaseSubAgent):
    """Mock agent for testing."""
    
    def __init__(self, agent_type: str, should_fail: bool = False, supported_events: list = None):
        self.agent_type = agent_type
        self.should_fail = should_fail
        self.process_count = 0
        self._supported_events = supported_events or [f"{self.agent_type}_event"]
    
    def get_agent_type(self) -> str:
        return self.agent_type
    
    def get_supported_events(self) -> list:
        return self._supported_events
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        self.process_count += 1
        
        if self.should_fail:
            raise LLMProviderError("Mock agent failure")
        
        return DiaryEntry(
            entry_id=f"test_{self.process_count}",
            user_id=event_data.user_id,
            timestamp=event_data.timestamp,
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title="测试",
            content="测试日记内容",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type=self.agent_type,
            llm_provider="test"
        )
    
    def get_data_reader(self) -> DataReader:
        return Mock(spec=DataReader)


class MockDataReader(DataReader):
    """Mock data reader for testing."""
    
    def __init__(self):
        super().__init__(module_name="test_module", read_only=True)
    
    def read_event_context(self, event_data):
        return Mock()
    
    def get_user_preferences(self, user_id):
        return {}


@pytest.fixture
def temp_config_dir():
    """Create temporary configuration directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_llm_manager():
    """Create mock LLM manager."""
    manager = Mock(spec=LLMConfigManager)
    manager.generate_text_with_failover = AsyncMock(return_value='{"title": "测试", "content": "测试内容", "emotion_tags": ["开心快乐"]}')
    manager.get_provider_status.return_value = {"providers": ["test"], "current_provider": "test"}
    return manager


@pytest.fixture
def sample_event_data():
    """Create sample event data for testing."""
    return EventData(
        event_id="test_event_1",
        event_type="weather",
        event_name="favorite_weather",
        timestamp=datetime.now(),
        user_id=1,
        context_data={},
        metadata={}
    )


class TestSubAgentManager:
    """Test cases for SubAgentManager."""
    
    def test_init(self, mock_llm_manager, temp_config_dir):
        """Test SubAgentManager initialization."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        assert manager.llm_manager == mock_llm_manager
        assert manager.config_dir == Path(temp_config_dir)
        assert manager.max_retry_attempts == 3
        assert manager.retry_delay == 1.0
        assert isinstance(manager.agents, dict)
        assert isinstance(manager.data_readers, dict)
        assert isinstance(manager.agent_health, dict)
    
    def test_create_default_agent_configuration(self, mock_llm_manager, temp_config_dir):
        """Test creation of default agent configuration."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        config_file = Path(temp_config_dir) / "agent_configuration.json"
        assert config_file.exists()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        assert "agents" in config
        assert "weather_agent" in config["agents"]
        assert "trending_agent" in config["agents"]
        assert config["agents"]["weather_agent"]["enabled"] is True
    
    @patch('diary_agent.core.sub_agent_manager.WeatherDataReader')
    @patch('diary_agent.core.sub_agent_manager.TrendingDataReader')
    def test_initialize_data_readers(self, mock_trending_reader, mock_weather_reader, 
                                   mock_llm_manager, temp_config_dir):
        """Test data reader initialization."""
        mock_weather_reader.return_value = MockDataReader()
        mock_trending_reader.return_value = MockDataReader()
        
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        assert "weather_data_reader" in manager.data_readers
        assert "trending_data_reader" in manager.data_readers
    
    @pytest.mark.asyncio
    @patch('importlib.import_module')
    async def test_initialize_single_agent_success(self, mock_import, mock_llm_manager, temp_config_dir):
        """Test successful single agent initialization."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        # Add mock data reader
        manager.data_readers["test_reader"] = MockDataReader()
        
        # Mock the import and class
        mock_module = Mock()
        mock_module.TestAgent = MockAgent
        mock_import.return_value = mock_module
        
        # Mock factory to return test agent
        manager.factory.create_agent = Mock(return_value=MockAgent("test_agent"))
        
        config = {
            "class_name": "TestAgent",
            "module_path": "test.module",
            "data_reader": "test_reader",
            "enabled": True
        }
        
        success = await manager._initialize_single_agent("test_agent", config)
        
        assert success is True
        assert "test_agent" in manager.agents
        assert "test_agent" in manager.agent_health
        assert manager.agent_health["test_agent"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_initialize_single_agent_failure(self, mock_llm_manager, temp_config_dir):
        """Test failed single agent initialization."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        # Mock factory to return None (failure)
        manager.factory.create_agent = Mock(return_value=None)
        
        config = {
            "class_name": "TestAgent",
            "module_path": "test.module", 
            "data_reader": "nonexistent_reader",
            "enabled": True
        }
        
        success = await manager._initialize_single_agent("test_agent", config)
        
        assert success is False
        assert "test_agent" not in manager.agents
    
    @pytest.mark.asyncio
    async def test_process_event_with_retry_success(self, mock_llm_manager, temp_config_dir, sample_event_data):
        """Test successful event processing."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        # Create and register mock agent
        mock_agent = MockAgent("weather_agent", supported_events=["favorite_weather"])
        manager.agents["weather_agent"] = mock_agent
        manager.registry.register_agent(mock_agent)
        manager.agent_health["weather_agent"] = {
            "status": "healthy",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        manager.failure_counts["weather_agent"] = 0
        
        # Process event
        result = await manager.process_event_with_retry(sample_event_data)
        
        assert result is not None
        assert isinstance(result, DiaryEntry)
        assert result.agent_type == "weather_agent"
        assert manager.agent_health["weather_agent"]["successful_requests"] == 1
        assert manager.agent_health["weather_agent"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_process_event_with_retry_failure(self, mock_llm_manager, temp_config_dir, sample_event_data):
        """Test event processing with retry after failures."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir,
            max_retry_attempts=2,
            retry_delay=0.1  # Fast retry for testing
        )
        
        # Create and register failing mock agent
        mock_agent = MockAgent("weather_agent", should_fail=True, supported_events=["favorite_weather"])
        manager.agents["weather_agent"] = mock_agent
        manager.registry.register_agent(mock_agent)
        manager.agent_health["weather_agent"] = {
            "status": "healthy",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        manager.failure_counts["weather_agent"] = 0
        
        # Process event (should fail after retries)
        result = await manager.process_event_with_retry(sample_event_data)
        
        assert result is None
        assert manager.agent_health["weather_agent"]["failed_requests"] == 2
        assert manager.agent_health["weather_agent"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_process_event_no_agent(self, mock_llm_manager, temp_config_dir):
        """Test event processing when no agent is found."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        event_data = EventData(
            event_id="test",
            event_type="unknown",
            event_name="unknown_event",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        result = await manager.process_event_with_retry(event_data)
        assert result is None
    
    def test_get_agent(self, mock_llm_manager, temp_config_dir):
        """Test getting agent by type."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        mock_agent = MockAgent("test_agent")
        manager.agents["test_agent"] = mock_agent
        
        result = manager.get_agent("test_agent")
        assert result == mock_agent
        
        result = manager.get_agent("nonexistent")
        assert result is None
    
    def test_get_agent_for_event(self, mock_llm_manager, temp_config_dir):
        """Test getting agent for specific event."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        mock_agent = MockAgent("test_agent")
        manager.agents["test_agent"] = mock_agent
        manager.registry.register_agent(mock_agent)
        
        result = manager.get_agent_for_event("test_agent_event")
        assert result == mock_agent
        
        result = manager.get_agent_for_event("unknown_event")
        assert result is None
    
    def test_list_agents(self, mock_llm_manager, temp_config_dir):
        """Test listing all agents."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        manager.agents["agent1"] = MockAgent("agent1")
        manager.agents["agent2"] = MockAgent("agent2")
        
        result = manager.list_agents()
        assert set(result) == {"agent1", "agent2"}
    
    def test_list_supported_events(self, mock_llm_manager, temp_config_dir):
        """Test listing supported events."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        manager.registry.register_agent(agent1)
        manager.registry.register_agent(agent2)
        
        result = manager.list_supported_events()
        assert set(result) == {"agent1_event", "agent2_event"}
    
    def test_get_agent_health(self, mock_llm_manager, temp_config_dir):
        """Test getting agent health status."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        manager.agent_health["test_agent"] = {
            "status": "healthy",
            "total_requests": 10,
            "successful_requests": 8
        }
        
        # Get specific agent health
        result = manager.get_agent_health("test_agent")
        assert result["status"] == "healthy"
        assert result["total_requests"] == 10
        
        # Get all agent health
        result = manager.get_agent_health()
        assert "test_agent" in result
    
    def test_get_system_status(self, mock_llm_manager, temp_config_dir):
        """Test getting system status."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        manager.agents["agent1"] = MockAgent("agent1")
        manager.agents["agent2"] = MockAgent("agent2")
        manager.agent_health["agent1"] = {
            "status": "healthy",
            "total_requests": 10,
            "successful_requests": 8
        }
        manager.agent_health["agent2"] = {
            "status": "unhealthy",
            "total_requests": 5,
            "successful_requests": 2
        }
        
        result = manager.get_system_status()
        
        assert result["total_agents"] == 2
        assert result["healthy_agents"] == 1
        assert result["unhealthy_agents"] == 1
        assert result["total_requests"] == 15
        assert result["successful_requests"] == 10
        assert result["success_rate"] == 66.67
    
    @pytest.mark.asyncio
    @patch('importlib.import_module')
    async def test_restart_agent_success(self, mock_import, mock_llm_manager, temp_config_dir):
        """Test successful agent restart."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        # Add agent configuration
        manager.agent_configurations["test_agent"] = {
            "class_name": "TestAgent",
            "module_path": "test.module",
            "data_reader": "test_reader",
            "enabled": True
        }
        
        # Add mock data reader
        manager.data_readers["test_reader"] = MockDataReader()
        
        # Mock the import and class
        mock_module = Mock()
        mock_module.TestAgent = MockAgent
        mock_import.return_value = mock_module
        
        # Mock factory
        manager.factory.create_agent = Mock(return_value=MockAgent("test_agent"))
        
        # Add existing agent
        manager.agents["test_agent"] = MockAgent("test_agent")
        
        success = await manager.restart_agent("test_agent")
        
        assert success is True
        assert "test_agent" in manager.agents
    
    @pytest.mark.asyncio
    async def test_restart_agent_no_config(self, mock_llm_manager, temp_config_dir):
        """Test agent restart with no configuration."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        success = await manager.restart_agent("nonexistent_agent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_restart_unhealthy_agents(self, mock_llm_manager, temp_config_dir):
        """Test restarting unhealthy agents."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        # Add agent configurations
        manager.agent_configurations["agent1"] = {
            "class_name": "TestAgent",
            "module_path": "test.module",
            "data_reader": "test_reader",
            "enabled": True
        }
        
        # Add mock data reader
        manager.data_readers["test_reader"] = MockDataReader()
        
        # Mock factory
        manager.factory.create_agent = Mock(return_value=MockAgent("agent1"))
        
        # Set up unhealthy agent
        manager.agent_health["agent1"] = {"status": "unhealthy"}
        manager.agent_health["agent2"] = {"status": "healthy"}
        
        results = await manager.restart_unhealthy_agents()
        
        assert "agent1" in results
        assert "agent2" not in results
    
    def test_reload_configurations(self, mock_llm_manager, temp_config_dir):
        """Test configuration reloading."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        # Mock methods
        manager.factory.reload_prompt_configurations = Mock()
        
        manager.reload_configurations()
        
        # Verify methods were called
        mock_llm_manager.reload_configuration.assert_called_once()
        manager.factory.reload_prompt_configurations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown(self, mock_llm_manager, temp_config_dir):
        """Test graceful shutdown."""
        manager = SubAgentManager(
            llm_manager=mock_llm_manager,
            config_dir=temp_config_dir
        )
        
        # Add some data
        manager.agents["test"] = MockAgent("test")
        manager.agent_health["test"] = {"status": "healthy"}
        manager.failure_counts["test"] = 0
        
        await manager.shutdown()
        
        assert len(manager.agents) == 0
        assert len(manager.agent_health) == 0
        assert len(manager.failure_counts) == 0


if __name__ == "__main__":
    pytest.main([__file__])