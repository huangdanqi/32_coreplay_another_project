"""
Adoption Agent for diary generation.
Handles adoption events (toy_claimed) by integrating with adopted_function.py.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, PromptConfig
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.integration.adoption_data_reader import AdoptionDataReader


class AdoptionAgent(BaseSubAgent):
    """
    Specialized agent for handling adoption events.
    Integrates with adopted_function.py for event context.
    """
    
    def __init__(self, 
                 agent_type: str,
                 prompt_config: PromptConfig,
                 llm_manager: LLMConfigManager,
                 data_reader: AdoptionDataReader):
        """
        Initialize adoption agent.
        
        Args:
            agent_type: Agent type identifier
            prompt_config: Prompt configuration
            llm_manager: LLM configuration manager
            data_reader: Adoption data reader
        """
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.adoption_data_reader = data_reader
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process adoption event and generate diary entry.
        
        Args:
            event_data: Adoption event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        # Validate event type
        if event_data.event_name not in self.get_supported_events():
            raise ValueError(f"Unsupported adoption event: {event_data.event_name}")
        
        # Read event context from adoption module
        context_data = await self.read_event_context(event_data)
        
        # Generate diary content using LLM
        content_dict = await self.generate_diary_content(event_data, context_data)
        
        # Create diary entry
        diary_entry = await self._create_diary_entry(event_data, content_dict)
        
        # Validate and format output
        if not self.validate_output(diary_entry):
            # If validation fails, create a fallback entry
            diary_entry = self._create_fallback_entry(event_data, context_data)
        
        formatted_entry = self.format_output(diary_entry)
        
        return formatted_entry
    
    def get_supported_events(self) -> List[str]:
        """
        Get list of adoption events this agent supports.
        
        Returns:
            List of supported event names
        """
        return [
            "toy_claimed"
        ]
    
    def _create_fallback_entry(self, event_data: EventData, context_data) -> DiaryEntry:
        """
        Create a fallback diary entry when LLM generation fails.
        
        Args:
            event_data: Original event data
            context_data: Event context data
            
        Returns:
            Fallback diary entry
        """
        # Get user name from context
        user_name = context_data.user_profile.get("name", "主人")
        
        # Create simple adoption-themed content
        fallback_content = {
            "title": "被认领",
            "content": f"今天{user_name}认领了我！好开心！🎉",
            "emotion_tags": ["开心快乐", "兴奋激动"]
        }
        
        return self._create_diary_entry_sync(event_data, fallback_content)
    
    def _create_diary_entry_sync(self, event_data: EventData, content_dict: Dict[str, Any]) -> DiaryEntry:
        """
        Synchronous version of diary entry creation for fallback.
        
        Args:
            event_data: Original event data
            content_dict: Content dictionary
            
        Returns:
            DiaryEntry object
        """
        from diary_agent.utils.data_models import EmotionalTag
        
        # Convert emotion tag strings to EmotionalTag enums
        emotion_tags = []
        for tag_str in content_dict.get("emotion_tags", []):
            for tag in EmotionalTag:
                if tag.value == tag_str:
                    emotion_tags.append(tag)
                    break
        
        # Default to HAPPY if no valid tags found for adoption
        if not emotion_tags:
            emotion_tags = [EmotionalTag.HAPPY]
        
        # Get current provider name
        current_provider = self.llm_manager.get_current_provider()
        provider_name = current_provider.provider_name if current_provider else "fallback"
        
        # Create diary entry
        entry = DiaryEntry(
            entry_id=f"{event_data.user_id}_{event_data.event_id}_{int(event_data.timestamp.timestamp())}",
            user_id=event_data.user_id,
            timestamp=event_data.timestamp,
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title=content_dict["title"][:6],  # Ensure max 6 characters
            content=content_dict["content"][:35],  # Ensure max 35 characters
            emotion_tags=emotion_tags,
            agent_type=self.agent_type,
            llm_provider=provider_name
        )
        
        return entry
    
    def get_adoption_event_config(self, event_name: str) -> Dict[str, Any]:
        """
        Get adoption event configuration.
        
        Args:
            event_name: Name of the adoption event
            
        Returns:
            Event configuration dictionary
        """
        return self.adoption_data_reader.get_adoption_event_info(event_name)
    
    def get_user_adoption_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences for adoption events.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences dictionary
        """
        return self.adoption_data_reader.get_user_preferences(user_id)


# Factory function for creating adoption agent
def create_adoption_agent(llm_manager: LLMConfigManager, 
                         prompt_config: PromptConfig) -> AdoptionAgent:
    """
    Factory function to create an adoption agent instance.
    
    Args:
        llm_manager: LLM configuration manager
        prompt_config: Prompt configuration for the agent
        
    Returns:
        AdoptionAgent instance
    """
    data_reader = AdoptionDataReader()
    
    return AdoptionAgent(
        agent_type="adoption_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )