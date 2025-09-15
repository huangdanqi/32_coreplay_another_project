"""
Unit tests for FriendsAgent.
Tests friend-related diary generation functionality.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from diary_agent.agents.friends_agent import FriendsAgent
from diary_agent.integration.friends_data_reader import FriendsDataReader
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, EmotionalTag
)
from diary_agent.core.llm_manager import LLMConfigManager


class TestFriendsAgent:
    """Test cases for FriendsAgent."""
    
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
        """Create mock friends data reader."""
        reader = Mock(spec=FriendsDataReader)
        reader.read_event_context = AsyncMock()
        return reader
    
    @pytest.fixture
    def prompt_config(self):
        """Create test prompt configuration."""
        return PromptConfig(
            agent_type="friends_agent",
            system_prompt="Test system prompt for friends",
            user_prompt_template="Test prompt: {event_name} at {timestamp}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
    
    @pytest.fixture
    def friends_agent(self, prompt_config, mock_llm_manager, mock_data_reader):
        """Create FriendsAgent instance for testing."""
        agent = FriendsAgent(
            agent_type="friends_agent",
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
            event_id="test_event_123",
            event_type="friend",
            event_name="made_new_friend",
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
            user_id=1,
            context_data={},
            metadata={"friend_id": 2}
        )
    
    @pytest.fixture
    def sample_context_data(self):
        """Create sample context data for testing."""
        return DiaryContextData(
            user_profile={
                "id": 1,
                "name": "TestUser",
                "role": "lively",
                "friend_count": 3,
                "favorite_action": '["摸摸脸", "拍拍头"]',
                "annoying_action": '["捏一下"]'
            },
            event_details={
                "event_name": "made_new_friend",
                "event_type": "friendship_change",
                "chinese_name": "交到新朋友",
                "user_role": "lively",
                "emotion_impact": {"x_change": 2, "y_change_logic": {"x_greater_equal_0": 2}}
            },
            environmental_context={},
            social_context={
                "current_friend_count": 3,
                "user_role": "lively",
                "favorite_interactions": ["摸摸脸", "拍拍头"],
                "disliked_interactions": ["捏一下"],
                "friend_id": 2
            },
            emotional_context={
                "current_x": 1,
                "current_y": 0,
                "emotional_tone": "positive",
                "social_impact": "expansion",
                "emotional_intensity": 1.5
            },
            temporal_context={
                "timestamp": datetime(2024, 1, 15, 14, 30, 0),
                "time_of_day": "afternoon"
            }
        )
    
    def test_get_supported_events(self, friends_agent):
        """Test that agent returns correct supported events."""
        expected_events = [
            "made_new_friend", "friend_deleted",
            "liked_single", "liked_3_to_5", "liked_5_plus",
            "disliked_single", "disliked_3_to_5", "disliked_5_plus"
        ]
        assert friends_agent.get_supported_events() == expected_events
    
    def test_get_agent_type(self, friends_agent):
        """Test that agent returns correct type."""
        assert friends_agent.get_agent_type() == "friends_agent"
    
    @pytest.mark.asyncio
    async def test_process_event_success(self, friends_agent, sample_event_data, 
                                       sample_context_data, mock_llm_manager, mock_data_reader):
        """Test successful event processing."""
        # Setup mocks
        friends_agent.read_event_context.return_value = sample_context_data
        mock_llm_manager.generate_text_with_failover.return_value = '''
        {
            "title": "新朋友",
            "content": "今天交到新朋友了，很开心😊",
            "emotion_tags": ["开心快乐"]
        }
        '''
        
        # Process event
        result = await friends_agent.process_event(sample_event_data)
        
        # Verify result
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "made_new_friend"
        assert result.user_id == 1
        assert result.title == "新朋友"
        assert "开心" in result.content
        # With emotional_intensity of 1.5, it should select EXCITED_THRILLED
        assert EmotionalTag.EXCITED_THRILLED in result.emotion_tags
        assert result.agent_type == "friends_agent"
    
    @pytest.mark.asyncio
    async def test_process_unsupported_event(self, friends_agent, sample_event_data):
        """Test processing unsupported event raises ValueError."""
        sample_event_data.event_name = "unsupported_event"
        
        with pytest.raises(ValueError, match="Unsupported event"):
            await friends_agent.process_event(sample_event_data)
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_llm_success(self, friends_agent, sample_event_data,
                                                    sample_context_data, mock_llm_manager):
        """Test successful LLM diary content generation."""
        mock_llm_manager.generate_text_with_failover.return_value = '''
        {
            "title": "新朋友",
            "content": "交到新朋友了，心情很好",
            "emotion_tags": ["开心快乐"]
        }
        '''
        
        result = await friends_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "新朋友"
        assert result["content"] == "交到新朋友了，心情很好"
        # The emotion tags are enhanced by the agent, so check for the enhanced tags
        assert "兴奋激动" in result["emotion_tags"] or "开心快乐" in result["emotion_tags"]
    
    @pytest.mark.asyncio
    async def test_generate_diary_content_llm_failure_fallback(self, friends_agent, 
                                                             sample_event_data, sample_context_data,
                                                             mock_llm_manager):
        """Test fallback when LLM generation fails."""
        mock_llm_manager.generate_text_with_failover.side_effect = Exception("LLM failed")
        
        result = await friends_agent.generate_diary_content(sample_event_data, sample_context_data)
        
        assert "title" in result
        assert "content" in result
        assert "emotion_tags" in result
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_select_friend_emotion_tags_made_new_friend(self, friends_agent, sample_context_data):
        """Test emotion tag selection for made_new_friend event."""
        # High intensity
        sample_context_data.emotional_context["emotional_intensity"] = 1.5
        tags = friends_agent._select_friend_emotion_tags("made_new_friend", sample_context_data)
        assert EmotionalTag.EXCITED_THRILLED.value in tags
        
        # Normal intensity
        sample_context_data.emotional_context["emotional_intensity"] = 1.0
        tags = friends_agent._select_friend_emotion_tags("made_new_friend", sample_context_data)
        assert EmotionalTag.HAPPY_JOYFUL.value in tags
    
    def test_select_friend_emotion_tags_friend_deleted(self, friends_agent, sample_context_data):
        """Test emotion tag selection for friend_deleted event."""
        # High intensity
        sample_context_data.emotional_context["emotional_intensity"] = 1.0
        tags = friends_agent._select_friend_emotion_tags("friend_deleted", sample_context_data)
        assert EmotionalTag.SAD_UPSET.value in tags
        
        # Lower intensity
        sample_context_data.emotional_context["emotional_intensity"] = 0.5
        tags = friends_agent._select_friend_emotion_tags("friend_deleted", sample_context_data)
        assert EmotionalTag.WORRIED.value in tags
    
    def test_select_friend_emotion_tags_liked_interactions(self, friends_agent, sample_context_data):
        """Test emotion tag selection for liked interaction events."""
        # 5+ interactions
        tags = friends_agent._select_friend_emotion_tags("liked_5_plus", sample_context_data)
        assert EmotionalTag.EXCITED_THRILLED.value in tags
        
        # 3-5 interactions
        tags = friends_agent._select_friend_emotion_tags("liked_3_to_5", sample_context_data)
        assert EmotionalTag.HAPPY_JOYFUL.value in tags
        
        # Single interaction
        tags = friends_agent._select_friend_emotion_tags("liked_single", sample_context_data)
        assert EmotionalTag.HAPPY_JOYFUL.value in tags
    
    def test_select_friend_emotion_tags_disliked_interactions(self, friends_agent):
        """Test emotion tag selection for disliked interaction events."""
        # Create context data specifically for disliked interactions
        disliked_context_data = DiaryContextData(
            user_profile={"id": 1, "role": "lively"},
            event_details={"event_name": "disliked_5_plus"},
            environmental_context={},
            social_context={},
            emotional_context={
                "emotional_tone": "negative",
                "emotional_intensity": 1.0
            },
            temporal_context={}
        )
        
        # 5+ interactions
        tags = friends_agent._select_friend_emotion_tags("disliked_5_plus", disliked_context_data)
        assert EmotionalTag.ANGRY_FURIOUS.value in tags
        
        # 3-5 interactions
        tags = friends_agent._select_friend_emotion_tags("disliked_3_to_5", disliked_context_data)
        assert EmotionalTag.SAD_UPSET.value in tags
        
        # Single interaction
        tags = friends_agent._select_friend_emotion_tags("disliked_single", disliked_context_data)
        assert EmotionalTag.ANXIOUS_MELANCHOLY.value in tags
    
    def test_generate_friend_fallback_content_made_new_friend(self, friends_agent, 
                                                            sample_event_data, sample_context_data):
        """Test fallback content generation for made_new_friend."""
        result = friends_agent._generate_friend_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "新朋友"
        assert "朋友" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
        assert len(result["emotion_tags"]) > 0
    
    def test_generate_friend_fallback_content_friend_deleted(self, friends_agent, 
                                                           sample_event_data, sample_context_data):
        """Test fallback content generation for friend_deleted."""
        sample_event_data.event_name = "friend_deleted"
        sample_context_data.event_details["event_name"] = "friend_deleted"
        
        result = friends_agent._generate_friend_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "失去朋友"
        assert "朋友" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_generate_friend_fallback_content_liked_interaction(self, friends_agent, 
                                                              sample_event_data, sample_context_data):
        """Test fallback content generation for liked interactions."""
        sample_event_data.event_name = "liked_5_plus"
        sample_context_data.event_details.update({
            "event_name": "liked_5_plus",
            "interaction_type": "摸摸脸",
            "interaction_frequency": "5+ times"
        })
        
        result = friends_agent._generate_friend_fallback_content(sample_event_data, sample_context_data)
        
        assert result["title"] == "超开心"
        assert "摸摸脸" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_generate_friend_fallback_content_disliked_interaction(self, friends_agent):
        """Test fallback content generation for disliked interactions."""
        # Create event data for disliked interaction
        disliked_event_data = EventData(
            event_id="test_disliked",
            event_type="friend",
            event_name="disliked_3_to_5",
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
            user_id=1,
            context_data={},
            metadata={"friend_id": 2}
        )
        
        # Create context data for disliked interaction
        disliked_context_data = DiaryContextData(
            user_profile={"id": 1, "role": "lively"},
            event_details={
                "event_name": "disliked_3_to_5",
                "interaction_type": "捏一下",
                "interaction_frequency": "3-5 times"
            },
            environmental_context={},
            social_context={"user_role": "lively"},
            emotional_context={"emotional_tone": "negative"},
            temporal_context={}
        )
        
        result = friends_agent._generate_friend_fallback_content(disliked_event_data, disliked_context_data)
        
        assert result["title"] == "不开心"
        assert "捏一下" in result["content"]
        assert len(result["title"]) <= 6
        assert len(result["content"]) <= 35
    
    def test_create_fallback_entry(self, friends_agent, sample_event_data, sample_context_data):
        """Test creation of fallback diary entry."""
        entry = friends_agent._create_fallback_entry(sample_event_data, sample_context_data)
        
        assert isinstance(entry, DiaryEntry)
        assert entry.user_id == sample_event_data.user_id
        assert entry.event_name == sample_event_data.event_name
        assert entry.agent_type == "friends_agent"
        assert entry.llm_provider == "fallback"
        assert len(entry.title) <= 6
        assert len(entry.content) <= 35
        assert len(entry.emotion_tags) > 0


if __name__ == "__main__":
    pytest.main([__file__])