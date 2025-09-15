"""
Dialogue Agent for diary generation.
Handles human-toy dialogue events by integrating with human_toy_talk.py.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, PromptConfig
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.integration.dialogue_data_reader import DialogueDataReader


class DialogueAgent(BaseSubAgent):
    """
    Specialized agent for handling human-toy dialogue events.
    Integrates with human_toy_talk.py for event context.
    """
    
    def __init__(self, 
                 agent_type: str,
                 prompt_config: PromptConfig,
                 llm_manager: LLMConfigManager,
                 data_reader: DialogueDataReader):
        """
        Initialize dialogue agent.
        
        Args:
            agent_type: Agent type identifier
            prompt_config: Prompt configuration
            llm_manager: LLM configuration manager
            data_reader: Dialogue data reader
        """
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.dialogue_data_reader = data_reader
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process dialogue event and generate diary entry.
        
        Args:
            event_data: Dialogue event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        # Validate event type
        if event_data.event_name not in self.get_supported_events():
            raise ValueError(f"Unsupported dialogue event: {event_data.event_name}")
        
        # Read event context from dialogue module
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
        Get list of dialogue events this agent supports.
        
        Returns:
            List of supported event names
        """
        return [
            "positive_emotional_dialogue",
            "negative_emotional_dialogue"
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
        
        # Create content based on dialogue type
        if event_data.event_name == "positive_emotional_dialogue":
            title = "开心聊天"
            content = f"和{user_name}开心地聊天了！😊"
            emotions = ["开心快乐", "兴奋激动"]
        elif event_data.event_name == "negative_emotional_dialogue":
            title = "关心主人"
            content = f"{user_name}心情不好，我想安慰他😔"
            emotions = ["担忧", "悲伤难过"]
        else:
            title = "聊天"
            content = f"和{user_name}聊天了"
            emotions = ["平静"]
        
        fallback_content = {
            "title": title,
            "content": content,
            "emotion_tags": emotions
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
        
        # Default to CALM if no valid tags found
        if not emotion_tags:
            emotion_tags = [EmotionalTag.CALM]
        
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
    
    def get_dialogue_event_config(self, event_name: str) -> Dict[str, Any]:
        """
        Get dialogue event configuration.
        
        Args:
            event_name: Name of the dialogue event
            
        Returns:
            Event configuration dictionary
        """
        return self.dialogue_data_reader.get_dialogue_event_info(event_name)
    
    def get_user_dialogue_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences for dialogue events.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences dictionary
        """
        return self.dialogue_data_reader.get_user_preferences(user_id)


# Factory function for creating dialogue agent
def create_dialogue_agent(llm_manager: LLMConfigManager, 
                         prompt_config: PromptConfig) -> DialogueAgent:
    """
    Factory function to create a dialogue agent instance.
    
    Args:
        llm_manager: LLM configuration manager
        prompt_config: Prompt configuration for the agent
        
    Returns:
        DialogueAgent instance
    """
    data_reader = DialogueDataReader()
    
    return DialogueAgent(
        agent_type="dialogue_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )