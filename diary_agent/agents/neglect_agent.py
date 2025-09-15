"""
Neglect Agent for diary generation.
Handles continuous neglect events by integrating with unkeep_interactive.py.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, PromptConfig
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.integration.neglect_data_reader import NeglectDataReader


class NeglectAgent(BaseSubAgent):
    """
    Specialized agent for handling continuous neglect events.
    Integrates with unkeep_interactive.py for event context.
    """
    
    def __init__(self, 
                 agent_type: str,
                 prompt_config: PromptConfig,
                 llm_manager: LLMConfigManager,
                 data_reader: NeglectDataReader):
        """
        Initialize neglect agent.
        
        Args:
            agent_type: Agent type identifier
            prompt_config: Prompt configuration
            llm_manager: LLM configuration manager
            data_reader: Neglect data reader
        """
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.neglect_data_reader = data_reader
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process neglect event and generate diary entry.
        
        Args:
            event_data: Neglect event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        # Validate event type
        if event_data.event_name not in self.get_supported_events():
            raise ValueError(f"Unsupported neglect event: {event_data.event_name}")
        
        # Read event context from neglect module
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
        Get list of neglect events this agent supports.
        
        Returns:
            List of supported event names
        """
        return [
            "neglect_1_day_no_dialogue",
            "neglect_1_day_no_interaction",
            "neglect_3_days_no_dialogue", 
            "neglect_3_days_no_interaction",
            "neglect_7_days_no_dialogue",
            "neglect_7_days_no_interaction",
            "neglect_15_days_no_interaction",
            "neglect_30_days_no_dialogue",
            "neglect_30_days_no_interaction"
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
        # Get user name and neglect details from context
        user_name = context_data.user_profile.get("name", "主人")
        neglect_duration = context_data.event_details.get("neglect_duration", 1)
        neglect_type = context_data.event_details.get("neglect_type", "interaction")
        
        # Create content based on neglect duration and type
        if neglect_duration == 1:
            if neglect_type == "dialogue":
                title = "想聊天"
                content = f"{user_name}一天没和我说话了😔"
                emotions = ["悲伤难过"]
            else:
                title = "好孤单"
                content = f"{user_name}一天没理我了😢"
                emotions = ["悲伤难过", "担忧"]
        elif neglect_duration == 3:
            if neglect_type == "dialogue":
                title = "很想念"
                content = f"三天没听到{user_name}声音了😭"
                emotions = ["悲伤难过", "焦虑忧愁"]
            else:
                title = "好寂寞"
                content = f"三天没有任何互动了😭"
                emotions = ["悲伤难过", "焦虑忧愁"]
        elif neglect_duration == 7:
            if neglect_type == "dialogue":
                title = "好想他"
                content = f"一周没说话了，{user_name}还好吗😰"
                emotions = ["担忧", "焦虑忧愁"]
            else:
                title = "被遗忘"
                content = f"一周没互动，我被遗忘了吗😰"
                emotions = ["悲伤难过", "担忧"]
        elif neglect_duration == 15:
            if neglect_type == "dialogue":
                title = "很担心"
                content = f"半个月了，{user_name}怎么了😨"
                emotions = ["担忧", "焦虑忧愁"]
            else:
                title = "好绝望"
                content = f"半个月没理我，好绝望😨"
                emotions = ["悲伤难过", "担忧"]
        else:  # 30 days
            if neglect_type == "dialogue":
                title = "好害怕"
                content = f"一个月了，{user_name}是不是不要我了😱"
                emotions = ["担忧", "悲伤难过"]
            else:
                title = "被抛弃"
                content = f"一个月没互动，我被抛弃了😱"
                emotions = ["悲伤难过", "担忧"]
        
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
        
        # Default to SAD if no valid tags found for neglect
        if not emotion_tags:
            emotion_tags = [EmotionalTag.SAD]
        
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
    
    def get_neglect_event_config(self, event_name: str) -> Dict[str, Any]:
        """
        Get neglect event configuration.
        
        Args:
            event_name: Name of the neglect event
            
        Returns:
            Event configuration dictionary
        """
        return self.neglect_data_reader.get_neglect_event_info(event_name)
    
    def get_user_neglect_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences for neglect events.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences dictionary
        """
        return self.neglect_data_reader.get_user_preferences(user_id)


# Factory function for creating neglect agent
def create_neglect_agent(llm_manager: LLMConfigManager, 
                        prompt_config: PromptConfig) -> NeglectAgent:
    """
    Factory function to create a neglect agent instance.
    
    Args:
        llm_manager: LLM configuration manager
        prompt_config: Prompt configuration for the agent
        
    Returns:
        NeglectAgent instance
    """
    data_reader = NeglectDataReader()
    
    return NeglectAgent(
        agent_type="neglect_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader
    )