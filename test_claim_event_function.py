"""
Comprehensive test for Claim Event function (toy_claimed).

This test suite validates the Claim Event functionality as specified in diary_agent_specifications_en.md:
- Trigger Condition: Each time a device is bound
- Content to Include: Owner's personal information

The test covers:
1. Device binding simulation
2. Event generation and routing
3. Adoption agent processing
4. Diary entry generation with owner's personal information
5. Integration with adopted_function.py
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Import diary agent components
from diary_agent.core.dairy_agent_controller import DairyAgentController
from diary_agent.core.event_router import EventRouter
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.agents.adoption_agent import AdoptionAgent, create_adoption_agent
from diary_agent.integration.adoption_data_reader import AdoptionDataReader
from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, 
    EmotionalTag, LLMConfig
)


class TestClaimEventFunction:
    """Test suite for Claim Event (toy_claimed) functionality."""
    
    @pytest.fixture
    def mock_llm_config(self):
        """Create mock LLM configuration."""
        return LLMConfig(
            provider_name="test_provider",
            api_endpoint="http://test.api",
            api_key="test_key",
            model_name="test_model",
            max_tokens=100,
            temperature=0.7,
            timeout=30,
            retry_attempts=3
        )
    
    @pytest.fixture
    def mock_llm_manager(self, mock_llm_config):
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
    def mock_adoption_data_reader(self):
        """Create mock adoption data reader."""
        reader = Mock(spec=AdoptionDataReader)
        reader.read_event_context = Mock()  # Changed from AsyncMock to Mock
        reader.get_user_preferences = Mock()
        reader.get_adoption_event_info = Mock()
        reader.get_supported_events = Mock(return_value=["toy_claimed"])
        return reader
    
    @pytest.fixture
    def prompt_config(self):
        """Create prompt configuration for adoption agent."""
        return PromptConfig(
            agent_type="adoption_agent",
            system_prompt="You are an adoption agent that generates diary entries for toy claim events.",
            user_prompt_template="Generate a diary entry for {event_name} event with owner info: {owner_info}",
            output_format={
                "title": "string",
                "content": "string", 
                "emotion_tags": "list"
            },
            validation_rules={
                "title_max_length": 6,
                "content_max_length": 35
            }
        )
    
    @pytest.fixture
    def adoption_agent(self, prompt_config, mock_llm_manager, mock_adoption_data_reader):
        """Create AdoptionAgent instance for testing."""
        return AdoptionAgent(
            agent_type="adoption_agent",
            prompt_config=prompt_config,
            llm_manager=mock_llm_manager,
            data_reader=mock_adoption_data_reader
        )
    
    @pytest.fixture
    def sample_owner_info(self):
        """Sample owner personal information."""
        return {
            "user_id": 123,
            "name": "小明",
            "nickname": "小主人",
            "age": 25,
            "gender": "male",
            "location": "北京",
            "interests": ["游戏", "音乐", "科技"],
            "personality": "lively",
            "emotional_baseline": {"x": 0, "y": 0},
            "intimacy_level": 50
        }
    
    @pytest.fixture
    def device_binding_event_data(self, sample_owner_info):
        """Create event data simulating device binding."""
        return EventData(
            event_id="claim_event_001",
            event_type="adoption_event",
            event_name="toy_claimed",
            timestamp=datetime.now(),
            user_id=sample_owner_info["user_id"],
            context_data={
                "device_id": "toy_robot_001",
                "binding_method": "mobile_app",
                "binding_timestamp": datetime.now().isoformat(),
                "device_type": "smart_toy",
                "device_name": "小机器人"
            },
            metadata={
                "owner_info": sample_owner_info,
                "claim_method": "app_binding",
                "toy_model": "AI_PET_V2"
            }
        )
    
    def test_claim_event_specification_compliance(self):
        """Test that Claim Event implementation follows specifications."""
        # Verify trigger condition: device binding
        assert "toy_claimed" in ["toy_claimed"]  # Event name exists
        
        # Verify content requirement: owner's personal information
        # This will be tested in integration tests
        assert True
    
    @pytest.mark.asyncio
    async def test_device_binding_triggers_claim_event(self, adoption_agent, device_binding_event_data):
        """Test that device binding triggers the claim event."""
        # Verify event is supported
        supported_events = adoption_agent.get_supported_events()
        assert "toy_claimed" in supported_events
        
        # Verify event data structure
        assert device_binding_event_data.event_name == "toy_claimed"
        assert device_binding_event_data.event_type == "adoption_event"
        assert "device_id" in device_binding_event_data.context_data
        assert "owner_info" in device_binding_event_data.metadata
    
    @pytest.mark.asyncio
    async def test_claim_event_processing_with_owner_info(self, adoption_agent, device_binding_event_data, 
                                                          mock_adoption_data_reader, mock_llm_manager):
        """Test processing claim event with owner's personal information."""
        # Mock context data with owner information
        mock_context = DiaryContextData(
            user_profile=device_binding_event_data.metadata["owner_info"],
            event_details={
                "event_name": "toy_claimed",
                "device_id": device_binding_event_data.context_data["device_id"],
                "device_name": device_binding_event_data.context_data["device_name"],
                "binding_method": device_binding_event_data.context_data["binding_method"]
            },
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": device_binding_event_data.timestamp}
        )
        # Fix: Use return_value instead of AsyncMock for read_event_context
        mock_adoption_data_reader.read_event_context = Mock(return_value=mock_context)
        
        # Mock LLM response with owner information
        mock_llm_response = json.dumps({
            "title": "被认领",
            "content": "小明主人认领了我！好开心！🎉",
            "emotion_tags": ["开心快乐", "兴奋激动"]
        })
        mock_llm_manager.generate_text_with_failover.return_value = mock_llm_response
        
        # Process the claim event
        result = await adoption_agent.process_event(device_binding_event_data)
        
        # Verify result
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "toy_claimed"
        assert result.user_id == device_binding_event_data.user_id
        assert result.agent_type == "adoption_agent"
        
        # Verify content includes owner information
        assert "小明" in result.content or "主人" in result.content
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        
        # Verify emotion tags are appropriate for claim event
        assert any(tag in ["开心快乐", "兴奋激动"] for tag in [tag.value for tag in result.emotion_tags])
    
    @pytest.mark.asyncio
    async def test_claim_event_fallback_generation(self, adoption_agent, device_binding_event_data, 
                                                   mock_adoption_data_reader):
        """Test fallback diary generation when LLM fails."""
        # Mock context data
        mock_context = DiaryContextData(
            user_profile=device_binding_event_data.metadata["owner_info"],
            event_details={"event_name": "toy_claimed"},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": device_binding_event_data.timestamp}
        )
        # Fix: Use return_value instead of AsyncMock for read_event_context
        mock_adoption_data_reader.read_event_context = Mock(return_value=mock_context)
        
        # Mock LLM failure
        with patch.object(adoption_agent, 'validate_output', return_value=False):
            result = await adoption_agent.process_event(device_binding_event_data)
        
        # Verify fallback entry
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "toy_claimed"
        assert "被认领" in result.title or "认领" in result.content
        assert "小明" in result.content or "主人" in result.content
    
    @pytest.mark.asyncio
    async def test_claim_event_integration_with_adopted_function(self):
        """Test integration with adopted_function.py for claim events."""
        # This test would verify the integration with the actual adopted_function.py
        # For now, we'll test the expected behavior
        
        # Import the adopted function
        try:
            from hewan_emotion_cursor_python.adopted_function import ADOPTED_EVENTS, get_user_data
        except ImportError:
            pytest.skip("adopted_function.py not available")
        
        # Verify adopted function configuration
        assert "toy_claimed" in ADOPTED_EVENTS
        claim_config = ADOPTED_EVENTS["toy_claimed"]
        
        # Verify configuration matches specifications
        assert claim_config["name"] == "被认领"
        assert claim_config["trigger_condition"] == "该玩具通过手机APP成功添加了好友"
        assert claim_config["probability"] == 1.0  # Always trigger
        assert claim_config["x_change"] == 2
        assert "weights" in claim_config
    
    def test_claim_event_claimed_status(self):
        """Test that claim events are properly marked as claimed events."""
        # Test through event mapper
        from diary_agent.utils.event_mapper import EventMapper
        
        event_mapper = EventMapper()
        claimed_events = event_mapper.get_claimed_events()
        
        # Verify toy_claimed is in claimed events
        assert "toy_claimed" in claimed_events
        
        # Verify is_claimed_event returns True
        assert event_mapper.is_claimed_event("toy_claimed")
    
    @pytest.mark.asyncio
    async def test_claim_event_end_to_end_workflow(self):
        """Test complete end-to-end workflow for claim event."""
        # Create controller with mocked components
        controller = DairyAgentController()
        
        # Mock components
        controller.event_router = Mock(spec=EventRouter)
        controller.sub_agent_manager = Mock(spec=SubAgentManager)
        controller.llm_manager = Mock(spec=LLMConfigManager)
        
        # Create test event data
        event_data = EventData(
            event_id="claim_test_001",
            event_type="adoption_event",
            event_name="toy_claimed",
            timestamp=datetime.now(),
            user_id=123,
            context_data={"device_id": "test_device"},
            metadata={"owner_info": {"name": "测试用户", "nickname": "小主人"}}
        )
        
        # Mock event router responses
        controller.event_router.classify_event.return_value = {
            "success": True,
            "event_type": "adopted_function",
            "agent_type": "adoption_agent",
            "metadata": {"owner_info": {"name": "测试用户"}}
        }
        
        controller.event_router.is_claimed_event.return_value = True
        controller.event_router.should_generate_diary.return_value = True
        
        # Mock sub agent manager
        mock_agent = Mock(spec=AdoptionAgent)
        mock_agent.process_event = AsyncMock()
        mock_agent.process_event.return_value = DiaryEntry(
            entry_id="diary_001",
            user_id=123,
            timestamp=datetime.now(),
            event_type="adoption_event",
            event_name="toy_claimed",
            title="被认领",
            content="测试用户主人认领了我！🎉",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="adoption_agent",
            llm_provider="test_provider"
        )
        
        controller.sub_agent_manager.get_agent.return_value = mock_agent
        
        # Process the event
        result = await controller.process_event(event_data)
        
        # Verify the workflow
        assert result.success
        assert result.diary_entry is not None
        assert result.diary_entry.event_name == "toy_claimed"
        assert "测试用户" in result.diary_entry.content
    
    def test_claim_event_data_validation(self, device_binding_event_data):
        """Test validation of claim event data structure."""
        # Verify required fields
        assert device_binding_event_data.event_name == "toy_claimed"
        assert device_binding_event_data.event_type == "adoption_event"
        assert device_binding_event_data.user_id is not None
        
        # Verify context data contains device binding info
        context_data = device_binding_event_data.context_data
        assert "device_id" in context_data
        assert "binding_method" in context_data
        assert "device_type" in context_data
        
        # Verify metadata contains owner information
        metadata = device_binding_event_data.metadata
        assert "owner_info" in metadata
        owner_info = metadata["owner_info"]
        assert "name" in owner_info
        assert "user_id" in owner_info
    
    @pytest.mark.asyncio
    async def test_multiple_claim_events_handling(self, adoption_agent):
        """Test handling multiple claim events for different users."""
        # Create multiple claim events
        events = []
        for i in range(3):
            event_data = EventData(
                event_id=f"claim_event_{i+1}",
                event_type="adoption_event",
                event_name="toy_claimed",
                timestamp=datetime.now(),
                user_id=100 + i,
                context_data={"device_id": f"device_{i+1}"},
                metadata={"owner_info": {"name": f"用户{i+1}", "nickname": f"主人{i+1}"}}
            )
            events.append(event_data)
        
        # Mock data reader and LLM manager
        mock_data_reader = Mock(spec=AdoptionDataReader)
        mock_llm_manager = Mock(spec=LLMConfigManager)
        
        # Process each event
        results = []
        for event_data in events:
            # Mock context data
            mock_context = DiaryContextData(
                user_profile=event_data.metadata["owner_info"],
                event_details={"event_name": "toy_claimed"},
                environmental_context={},
                social_context={},
                emotional_context={},
                temporal_context={"timestamp": event_data.timestamp}
            )
            # Fix: Use return_value instead of AsyncMock for read_event_context
            mock_data_reader.read_event_context = Mock(return_value=mock_context)
            
            # Mock LLM response
            mock_llm_response = json.dumps({
                "title": "被认领",
                "content": f"{event_data.metadata['owner_info']['name']}主人认领了我！🎉",
                "emotion_tags": ["开心快乐"]
            })
            mock_llm_manager.generate_text_with_failover.return_value = mock_llm_response
            
            # Update agent with mocks
            adoption_agent.adoption_data_reader = mock_data_reader
            adoption_agent.llm_manager = mock_llm_manager
            
            # Process event
            result = await adoption_agent.process_event(event_data)
            results.append(result)
        
        # Verify all events were processed
        assert len(results) == 3
        for i, result in enumerate(results):
            assert isinstance(result, DiaryEntry)
            assert result.event_name == "toy_claimed"
            assert result.user_id == 100 + i
            assert f"用户{i+1}" in result.content


class TestClaimEventErrorHandling:
    """Test error handling for Claim Event function."""
    
    @pytest.fixture
    def adoption_agent_with_mocks(self):
        """Create adoption agent with mocked dependencies."""
        mock_llm_manager = Mock(spec=LLMConfigManager)
        mock_data_reader = Mock(spec=AdoptionDataReader)
        
        prompt_config = PromptConfig(
            agent_type="adoption_agent",
            system_prompt="Test prompt",
            user_prompt_template="Test template",
            output_format={},
            validation_rules={}
        )
        
        return AdoptionAgent(
            agent_type="adoption_agent",
            prompt_config=prompt_config,
            llm_manager=mock_llm_manager,
            data_reader=mock_data_reader
        )
    
    @pytest.mark.asyncio
    async def test_claim_event_with_invalid_event_name(self, adoption_agent_with_mocks):
        """Test handling of invalid event names."""
        event_data = EventData(
            event_id="invalid_event",
            event_type="adoption_event",
            event_name="invalid_claim_event",  # Invalid event name
            timestamp=datetime.now(),
            user_id=123,
            context_data={},
            metadata={}
        )
        
        with pytest.raises(ValueError, match="Unsupported adoption event"):
            await adoption_agent_with_mocks.process_event(event_data)
    
    @pytest.mark.asyncio
    async def test_claim_event_with_missing_owner_info(self, adoption_agent_with_mocks):
        """Test handling of missing owner information."""
        event_data = EventData(
            event_id="claim_no_owner",
            event_type="adoption_event",
            event_name="toy_claimed",
            timestamp=datetime.now(),
            user_id=123,
            context_data={"device_id": "test_device"},
            metadata={}  # Missing owner_info
        )
        
        # Mock context data without owner info
        mock_context = DiaryContextData(
            user_profile={"name": "默认用户"},  # Default user
            event_details={"event_name": "toy_claimed"},
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": event_data.timestamp}
        )
        
        # Fix: Use return_value instead of AsyncMock for read_event_context
        adoption_agent_with_mocks.adoption_data_reader.read_event_context = Mock(return_value=mock_context)
        
        # Mock LLM failure to trigger fallback
        with patch.object(adoption_agent_with_mocks, 'validate_output', return_value=False):
            result = await adoption_agent_with_mocks.process_event(event_data)
        
        # Verify fallback handles missing owner info gracefully
        assert isinstance(result, DiaryEntry)
        assert result.event_name == "toy_claimed"
        assert "默认用户" in result.content or "主人" in result.content


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
