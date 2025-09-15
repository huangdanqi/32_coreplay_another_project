"""
Same Frequency Agent for generating diary entries about synchronization events.
Integrates with existing same_frequency.py module for frequency synchronization data.
"""

import json
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, DiaryContextData, EmotionalTag
from diary_agent.integration.frequency_data_reader import FrequencyDataReader


class SameFrequencyAgent(BaseSubAgent):
    """
    Specialized agent for same frequency synchronization diary entries.
    Handles: close_friend_frequency events.
    """
    
    def __init__(self, agent_type: str, prompt_config, llm_manager, data_reader: FrequencyDataReader):
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.supported_events = ["close_friend_frequency"]
    
    def get_supported_events(self) -> List[str]:
        """Get list of frequency events this agent supports."""
        return self.supported_events.copy()
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process frequency event and generate diary entry.
        
        Args:
            event_data: Frequency event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        if event_data.event_name not in self.supported_events:
            raise ValueError(f"Unsupported event: {event_data.event_name}")
        
        # Read frequency context from existing module
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
    
    async def generate_diary_content(self, event_data: EventData, context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate frequency-specific diary content using LLM.
        
        Args:
            event_data: Event data
            context_data: Frequency context data
            
        Returns:
            Generated content dictionary
        """
        try:
            # Generate content using parent method
            content_dict = await super().generate_diary_content(event_data, context_data)
            
            # Enhance with frequency-specific emotion tags
            content_dict["emotion_tags"] = self._select_frequency_emotion_tags(
                event_data.event_name, context_data
            )
            
            return content_dict
            
        except Exception as e:
            # Fallback to frequency-specific generation
            return self._generate_frequency_fallback_content(event_data, context_data)
    
    def _select_frequency_emotion_tags(self, event_name: str, context_data: DiaryContextData) -> List[str]:
        """
        Select appropriate emotion tags for frequency events.
        
        Args:
            event_name: Frequency event name
            context_data: Frequency context data
            
        Returns:
            List of emotion tag strings
        """
        emotional_context = context_data.emotional_context
        synchronization_strength = emotional_context.get("synchronization_strength", "unknown")
        emotional_intensity = emotional_context.get("emotional_intensity", 1.0)
        
        # Frequency events are generally positive and exciting due to synchronization
        if synchronization_strength == "perfect":
            # Perfect synchronization is very exciting
            return [EmotionalTag.EXCITED_THRILLED.value]  # 兴奋激动
        elif synchronization_strength == "excellent":
            # Excellent synchronization is surprising
            return [EmotionalTag.SURPRISED_SHOCKED.value]  # 惊讶震惊
        elif synchronization_strength == "good":
            # Good synchronization is surprising and happy
            return [EmotionalTag.SURPRISED_SHOCKED.value]  # 惊讶震惊
        elif synchronization_strength == "acceptable":
            # Acceptable synchronization is still happy
            return [EmotionalTag.HAPPY_JOYFUL.value]      # 开心快乐
        else:
            # Default for unknown or poor synchronization
            return [EmotionalTag.CURIOUS.value]           # 好奇
    
    def _generate_frequency_fallback_content(self, event_data: EventData, 
                                           context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate fallback frequency content when LLM fails.
        
        Args:
            event_data: Event data
            context_data: Frequency context data
            
        Returns:
            Fallback content dictionary
        """
        event_details = context_data.event_details
        social_context = context_data.social_context
        temporal_context = context_data.temporal_context
        
        synchronized_interaction = event_details.get("synchronized_interaction", "互动")
        time_difference = temporal_context.get("time_difference_seconds", 0)
        synchronization_quality = event_details.get("synchronization_quality", "unknown")
        user_role = social_context.get("user_role", "clam")
        
        # Generate content based on synchronization quality
        if synchronization_quality == "perfect":
            title = "完美同步"
            if user_role == "lively":
                content = f"和朋友同时{synchronized_interaction}！太神奇了✨"
            else:
                content = f"居然和朋友同步了，很奇妙"
                
        elif synchronization_quality == "excellent":
            title = "同频了"
            if user_role == "lively":
                content = f"和朋友几乎同时{synchronized_interaction}😲"
            else:
                content = f"和朋友同频{synchronized_interaction}，很巧"
                
        elif synchronization_quality == "good":
            title = "巧合"
            content = f"和朋友差不多同时{synchronized_interaction}了"
            
        elif synchronization_quality == "acceptable":
            title = "同步"
            content = f"和朋友在{time_difference:.1f}秒内都{synchronized_interaction}"
            
        else:
            title = "同频"
            content = f"和朋友有同频{synchronized_interaction}体验"
        
        # Select emotion tags
        emotion_tags = self._select_frequency_emotion_tags(event_data.event_name, context_data)
        
        return {
            "title": title[:6],  # Ensure max 6 characters
            "content": content[:35],  # Ensure max 35 characters
            "emotion_tags": emotion_tags
        }
    
    def _create_fallback_entry(self, event_data: EventData, context_data: DiaryContextData) -> DiaryEntry:
        """
        Create fallback diary entry when validation fails.
        
        Args:
            event_data: Event data
            context_data: Frequency context data
            
        Returns:
            Fallback diary entry
        """
        fallback_content = self._generate_frequency_fallback_content(event_data, context_data)
        
        # Convert emotion tag strings to EmotionalTag enums
        emotion_tags = []
        for tag_str in fallback_content["emotion_tags"]:
            for tag in EmotionalTag:
                if tag.value == tag_str:
                    emotion_tags.append(tag)
                    break
        
        if not emotion_tags:
            emotion_tags = [EmotionalTag.SURPRISED_SHOCKED]  # Default for frequency events
        
        return DiaryEntry(
            entry_id=f"{event_data.user_id}_{event_data.event_id}_{int(event_data.timestamp.timestamp())}",
            user_id=event_data.user_id,
            timestamp=event_data.timestamp,
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title=fallback_content["title"],
            content=fallback_content["content"],
            emotion_tags=emotion_tags,
            agent_type=self.agent_type,
            llm_provider="fallback"
        )