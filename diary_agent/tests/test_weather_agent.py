"""
Unit tests for WeatherAgent and SeasonalAgent.
Tests integration with weather_function.py and diary generation.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from diary_agent.agents.weather_agent import WeatherAgent, SeasonalAgent
from diary_agent.integration.weather_data_reader import WeatherDataReader
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, EmotionalTag
)
from diary_agent.core.llm_manager import LLMConfigManager


class TestWeatherDataReader:
    """Test WeatherDataReader functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reader = WeatherDataReader()
        self.sample_event_data = EventData(
            event_id="test_001",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={"user_ip": "8.8.8.8"}
        )
    
    @patch('diary_agent.integration.weather_data_reader.get_emotion_data')
    @patch('diary_agent.integration.weather_data_reader.get_ip_city')
    @patch('diary_agent.integration.weather_data_reader.get_weather_data')
    @patch('diary_agent.integration.weather_data_reader.get_current_season')
    @patch('diary_agent.integration.weather_data_reader.calculate_emotion_changes')
    def test_read_event_context_success(self, mock_calc_emotion, mock_season, 
                                       mock_weather, mock_city, mock_emotion_data):
        """Test successful event context reading."""
        # Mock return values
        mock_emotion_data.return_value = [{
            "id": 1,
            "name": "test_user",
            "role": "clam",
            "favorite_weathers": "[\"Clear\", \"Sunny\"]",
            "dislike_weathers": "[\"Rain\"]",
            "favorite_seasons": "[\"Spring\"]",
            "dislike_seasons": "[\"Winter\"]"
        }]
        mock_city.return_value = "Beijing"
        mock_weather.return_value = "Clear"
        mock_season.return_value = "Spring"
        mock_calc_emotion.return_value = (1, 1, 0)
        
        # Test context reading
        context = self.reader.read_event_context(self.sample_event_data)
        
        # Verify context structure
        assert isinstance(context, DiaryContextData)
        assert context.user_profile["id"] == 1
        assert context.user_profile["role"] == "clam"
        assert context.environmental_context["city"] == "Beijing"
        assert context.environmental_context["current_weather"] == "Clear"
        assert context.environmental_context["current_season"] == "Spring"
        assert context.event_details["preference_match"] is True
    
    @patch('diary_agent.integration.weather_data_reader.get_emotion_data')
    def test_read_event_context_user_not_found(self, mock_emotion_data):
        """Test context reading when user is not found."""
        mock_emotion_data.return_value = []
        
        context = self.reader.read_event_context(self.sample_event_data)
        
        # Should return minimal context
        assert isinstance(context, DiaryContextData)
        assert context.user_profile["id"] == 1
        assert context.user_profile["role"] == "clam"
    
    def test_get_supported_events(self):
        """Test supported events list."""
        events = self.reader.get_supported_events()
        expected_events = ["favorite_weather", "dislike_weather", "favorite_season", "dislike_season"]
        assert events == expected_events
    
    def test_analyze_weather_event_favorite_match(self):
        """Test weather event analysis for favorite weather match."""
        user_profile = {
            "role": "lively",
            "favorite_weathers": "[\"Clear\", \"Sunny\"]",
            "dislike_weathers": "[\"Rain\"]"
        }
        
        event_details = self.reader._analyze_weather_event(
            "favorite_weather", user_profile, "Clear", "Spring"
        )
        
        assert event_details["event_name"] == "favorite_weather"
        assert event_details["event_type"] == "weather"
        assert event_details["preference_match"] is True
        assert event_details["user_role"] == "lively"
    
    def test_analyze_season_event_dislike_match(self):
        """Test season event analysis for dislike season match."""
        user_profile = {
            "role": "clam",
            "favorite_seasons": "[\"Spring\"]",
            "dislike_seasons": "[\"Winter\"]"
        }
        
        event_details = self.reader._analyze_weather_event(
            "dislike_season", user_profile, "Clear", "Winter"
        )
        
        assert event_details["event_name"] == "dislike_season"
        assert event_details["event_type"] == "season"
        assert event_details["preference_match"] is True
        assert event_details["user_role"] == "clam"
    
    def test_calculate_emotional_intensity(self):
        """Test emotional intensity calculation."""
        # Test clam role
        intensity = self.reader._calculate_emotional_intensity("clam", "favorite_weather")
        assert intensity == 1.0
        
        intensity = self.reader._calculate_emotional_intensity("clam", "dislike_weather")
        assert intensity == 0.5
        
        # Test lively role
        intensity = self.reader._calculate_emotional_intensity("lively", "favorite_season")
        assert intensity == 1.5
        
        intensity = self.reader._calculate_emotional_intensity("lively", "dislike_season")
        assert intensity == 1.0


class TestWeatherAgent:
    """Test WeatherAgent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_manager = Mock(spec=LLMConfigManager)
        self.mock_data_reader = Mock(spec=WeatherDataReader)
        
        self.prompt_config = PromptConfig(
            agent_type="weather_agent",
            system_prompt="Test system prompt",
            user_prompt_template="Test template: {event_name}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
        
        self.agent = WeatherAgent(
            agent_type="weather_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.mock_llm_manager,
            data_reader=self.mock_data_reader
        )
        
        self.sample_event_data = EventData(
            event_id="test_001",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={"user_ip": "8.8.8.8"}
        )
    
    def test_get_supported_events(self):
        """Test supported events list."""
        events = self.agent.get_supported_events()
        expected_events = ["favorite_weather", "dislike_weather", "favorite_season", "dislike_season"]
        assert events == expected_events
    
    @pytest.mark.asyncio
    async def test_process_event_success(self):
        """Test successful event processing."""
        # Mock context data
        mock_context = DiaryContextData(
            user_profile={"id": 1, "role": "clam"},
            event_details={"event_name": "favorite_weather", "preference_match": True},
            environmental_context={"current_weather": "Clear", "city": "Beijing"},
            social_context={},
            emotional_context={"emotional_intensity": 1.0},
            temporal_context={"timestamp": datetime.now()}
        )
        
        # Mock LLM response
        mock_llm_response = json.dumps({
            "title": "好天气",
            "content": "今天天气很好，心情愉快😊",
            "emotion_tags": ["开心快乐"]
        })
        
        # Set up mocks
        self.mock_data_reader.read_event_context = AsyncMock(return_value=mock_context)
        self.mock_llm_manager.generate_text_with_failover = AsyncMock(return_value=mock_llm_response)
        self.mock_llm_manager.get_current_provider = Mock(return_value=Mock(provider_name="qwen"))
        
        # Mock validation and formatting
        with patch.object(self.agent, 'validate_output', return_value=True), \
             patch.object(self.agent, 'format_output', side_effect=lambda x: x), \
             patch.object(self.agent, 'read_event_context', return_value=mock_context):
            
            result = await self.agent.process_event(self.sample_event_data)
        
        # Verify result
        assert isinstance(result, DiaryEntry)
        assert result.title == "好天气"
        assert result.content == "今天天气很好，心情愉快😊"
        assert result.agent_type == "weather_agent"
        assert result.user_id == 1
    
    @pytest.mark.asyncio
    async def test_process_event_unsupported(self):
        """Test processing unsupported event."""
        unsupported_event = EventData(
            event_id="test_002",
            event_type="social",
            event_name="made_new_friend",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
        
        with pytest.raises(ValueError, match="Unsupported event"):
            await self.agent.process_event(unsupported_event)
    
    def test_select_weather_emotion_tags_favorite_match(self):
        """Test emotion tag selection for favorite weather match."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={"preference_match": True},
            environmental_context={},
            social_context={},
            emotional_context={"emotional_intensity": 1.5},
            temporal_context={}
        )
        
        tags = self.agent._select_weather_emotion_tags("favorite_weather", context_data)
        assert tags == [EmotionalTag.EXCITED_THRILLED.value]
    
    def test_select_weather_emotion_tags_dislike_match(self):
        """Test emotion tag selection for dislike weather match."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={"preference_match": True},
            environmental_context={},
            social_context={},
            emotional_context={"emotional_intensity": 1.0},
            temporal_context={}
        )
        
        tags = self.agent._select_weather_emotion_tags("dislike_weather", context_data)
        assert tags == [EmotionalTag.ANGRY_FURIOUS.value]
    
    def test_generate_weather_fallback_content(self):
        """Test fallback content generation."""
        context_data = DiaryContextData(
            user_profile={},
            event_details={"preference_match": True},
            environmental_context={"current_weather": "Clear", "current_season": "Spring"},
            social_context={},
            emotional_context={},
            temporal_context={}
        )
        
        content = self.agent._generate_weather_fallback_content(self.sample_event_data, context_data)
        
        assert "title" in content
        assert "content" in content
        assert "emotion_tags" in content
        assert len(content["title"]) <= 6
        assert len(content["content"]) <= 35
    
    @pytest.mark.asyncio
    async def test_process_event_with_validation_failure(self):
        """Test event processing when validation fails."""
        # Mock context data
        mock_context = DiaryContextData(
            user_profile={"id": 1, "role": "clam"},
            event_details={"event_name": "favorite_weather", "preference_match": True},
            environmental_context={"current_weather": "Clear"},
            social_context={},
            emotional_context={"emotional_intensity": 1.0},
            temporal_context={"timestamp": datetime.now()}
        )
        
        # Mock LLM response
        mock_llm_response = json.dumps({
            "title": "好天气",
            "content": "今天天气很好",
            "emotion_tags": ["开心快乐"]
        })
        
        # Set up mocks
        self.mock_data_reader.read_event_context = AsyncMock(return_value=mock_context)
        self.mock_llm_manager.generate_text_with_failover = AsyncMock(return_value=mock_llm_response)
        self.mock_llm_manager.get_current_provider = Mock(return_value=Mock(provider_name="qwen"))
        
        # Mock validation failure and formatting
        with patch.object(self.agent, 'validate_output', return_value=False), \
             patch.object(self.agent, 'format_output', side_effect=lambda x: x), \
             patch.object(self.agent, 'read_event_context', return_value=mock_context):
            
            result = await self.agent.process_event(self.sample_event_data)
        
        # Should return fallback entry
        assert isinstance(result, DiaryEntry)
        assert result.llm_provider == "fallback"


class TestSeasonalAgent:
    """Test SeasonalAgent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_manager = Mock(spec=LLMConfigManager)
        self.mock_data_reader = Mock(spec=WeatherDataReader)
        
        self.prompt_config = PromptConfig(
            agent_type="seasonal_agent",
            system_prompt="Test seasonal prompt",
            user_prompt_template="Test template: {event_name}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
        
        self.agent = SeasonalAgent(
            agent_type="seasonal_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.mock_llm_manager,
            data_reader=self.mock_data_reader
        )
    
    def test_get_supported_events(self):
        """Test seasonal agent supported events."""
        events = self.agent.get_supported_events()
        expected_events = ["favorite_season", "dislike_season"]
        assert events == expected_events
    
    @pytest.mark.asyncio
    async def test_seasonal_agent_inherits_weather_functionality(self):
        """Test that seasonal agent inherits weather agent functionality."""
        # Seasonal agent should have access to weather agent methods
        assert hasattr(self.agent, '_select_weather_emotion_tags')
        assert hasattr(self.agent, '_generate_weather_fallback_content')
        assert hasattr(self.agent, 'process_event')


if __name__ == "__main__":
    pytest.main([__file__])