"""
Interactive Agent for diary generation.
Handles human-toy interaction events by integrating with human_toy_interactive_function.py.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, PromptConfig
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.integration.interaction_data_reader import InteractionDataReader


class InteractiveAgent(BaseSubAgent):
    """
    Specialized agent for handling human-toy interaction events.
    Integrates with human_toy_interactive_function.py for event context.
    """
    
    def __init__(self, 
                 agent_type: str,
                 prompt_config: PromptConfig,
                 llm_manager: LLMConfigManager,
                 data_reader: InteractionDataReader):
        """
        Initialize interactive agent.
        
        Args:
            agent_type: Agent type identifier
            prompt_config: Prompt configuration
            llm_manager: LLM configuration manager
            data_reader: Interaction data reader
        """
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.interaction_data_reader = data_reader
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process interaction event and generate diary entry.
        
        Args:
            event_data: Interaction event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        # Validate event type
        if event_data.event_name not in self.get_supported_events():
            raise ValueError(f"Unsupported interaction event: {event_data.event_name}")
        
        # Read event context from interaction module
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
        Get list of interaction events this agent supports.
        
        Returns:
            List of supported event names
        """
        return [
            "liked_interaction_once",
            "liked_interaction_3_to_5_times", 
            "liked_interaction_over_5_times",
            "disliked_interaction_once",
            "disliked_interaction_3_to_5_times",
            "neutral_interaction_over_5_times"
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
        # Get interaction preference and frequency from context
        preference = context_data.event_details.get("interaction_preference", "neutral")
        interaction_type = context_data.event_details.get("interaction_type", "互动")
        
        # Create content based on preference and frequency
        if "liked" in event_data.event_name:
            if "over_5" in event_data.event_name:
                title = "好开心"
                content = f"主人一直{interaction_type}我！太幸福了！😊"
                emotions = ["开心快乐", "兴奋激动"]
            elif "3_to_5" in event_data.event_name:
                title = "很高兴"
                content = f"主人多次{interaction_type}我，好开心！😄"
                emotions = ["开心快乐"]
            else:
                title = "开心"
                content = f"主人{interaction_type}了我，很开心！😊"
                emotions = ["开心快乐"]
        elif "disliked" in event_data.event_name:
            if "over_5" in event_data.event_name:
                title = "很难受"
                content = f"主人一直做我不喜欢的事😢"
                emotions = ["悲伤难过", "生气愤怒"]
            elif "3_to_5" in event_data.event_name:
                title = "不开心"
                content = f"主人做了我不喜欢的事😔"
                emotions = ["悲伤难过"]
            else:
                title = "有点难受"
                content = f"主人做了我不太喜欢的事😕"
                emotions = ["担忧"]
        else:  # neutral
            title = "还好"
            content = f"主人和我互动了很多次😐"
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
    
    def get_interaction_event_config(self, event_name: str) -> Dict[str, Any]:
        """
        Get interaction event configuration.
        
        Args:
            event_name: Name of the interaction event
            
        Returns:
            Event configuration dictionary
        """
        return self.interaction_data_reader.get_interaction_event_info(event_name)
    
    def get_user_interaction_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences for interaction events.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences dictionary
        """
        return self.interaction_data_reader.get_user_preferences(user_id)


# Factory function for creating interactive agent
def create_interactive_agent(llm_manager: LLMConfigManager, 
                           prompt_config: PromptConfig) -> InteractiveAgent:
    """
    Factory function to create an interactive agent instance.
    
    Args:
        llm_manager: LLM configuration manager
        prompt_config: Prompt configuration for the agent
        
    Returns:
        InteractiveAgent instance
    """
    data_reader = InteractionDataReader()
    
    return InteractiveAgent(
        agent_type="interactive_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )