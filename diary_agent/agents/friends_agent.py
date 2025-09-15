"""
Friends Agent for generating diary entries about friend-related events.
Integrates with existing friends_function.py module for friend data and interactions.
"""

import json
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, DiaryContextData, EmotionalTag
from diary_agent.integration.friends_data_reader import FriendsDataReader


class FriendsAgent(BaseSubAgent):
    """
    Specialized agent for friend-related diary entries.
    Handles: made_new_friend, friend_deleted, liked_single, liked_3_to_5, liked_5_plus,
             disliked_single, disliked_3_to_5, disliked_5_plus events.
    """
    
    def __init__(self, agent_type: str, prompt_config, llm_manager, data_reader: FriendsDataReader):
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.supported_events = [
            "made_new_friend", "friend_deleted",
            "liked_single", "liked_3_to_5", "liked_5_plus",
            "disliked_single", "disliked_3_to_5", "disliked_5_plus"
        ]
    
    def get_supported_events(self) -> List[str]:
        """Get list of friend events this agent supports."""
        return self.supported_events.copy()
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process friend event and generate diary entry.
        
        Args:
            event_data: Friend event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        if event_data.event_name not in self.supported_events:
            raise ValueError(f"Unsupported event: {event_data.event_name}")
        
        # Read friend context from existing module
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
        Generate friend-specific diary content using LLM.
        
        Args:
            event_data: Event data
            context_data: Friend context data
            
        Returns:
            Generated content dictionary
        """
        try:
            # Generate content using parent method
            content_dict = await super().generate_diary_content(event_data, context_data)
            
            # Enhance with friend-specific emotion tags
            content_dict["emotion_tags"] = self._select_friend_emotion_tags(
                event_data.event_name, context_data
            )
            
            return content_dict
            
        except Exception as e:
            # Fallback to friend-specific generation
            return self._generate_friend_fallback_content(event_data, context_data)
    
    def _select_friend_emotion_tags(self, event_name: str, context_data: DiaryContextData) -> List[str]:
        """
        Select appropriate emotion tags for friend events.
        
        Args:
            event_name: Friend event name
            context_data: Friend context data
            
        Returns:
            List of emotion tag strings
        """
        emotional_context = context_data.emotional_context
        emotional_tone = emotional_context.get("emotional_tone", "neutral")
        emotional_intensity = emotional_context.get("emotional_intensity", 1.0)
        
        # Select emotion based on event type and emotional context
        if event_name == "made_new_friend":
            if emotional_intensity >= 1.5:
                return [EmotionalTag.EXCITED_THRILLED.value]  # 兴奋激动
            else:
                return [EmotionalTag.HAPPY_JOYFUL.value]    # 开心快乐
                
        elif event_name == "friend_deleted":
            if emotional_intensity >= 1.0:
                return [EmotionalTag.SAD_UPSET.value]       # 悲伤难过
            else:
                return [EmotionalTag.WORRIED.value]         # 担忧
                
        elif "disliked" in event_name:
            # Negative interaction events
            if "5_plus" in event_name:
                return [EmotionalTag.ANGRY_FURIOUS.value]   # 生气愤怒
            elif "3_to_5" in event_name:
                return [EmotionalTag.SAD_UPSET.value]       # 悲伤难过
            else:  # single
                return [EmotionalTag.ANXIOUS_MELANCHOLY.value]  # 焦虑忧愁
                
        elif "liked" in event_name:
            # Positive interaction events
            if "5_plus" in event_name:
                return [EmotionalTag.EXCITED_THRILLED.value]  # 兴奋激动
            elif "3_to_5" in event_name:
                return [EmotionalTag.HAPPY_JOYFUL.value]    # 开心快乐
            else:  # single
                return [EmotionalTag.HAPPY_JOYFUL.value]    # 开心快乐
                
        else:
            # Default case
            return [EmotionalTag.CALM.value]                # 平静
    
    def _generate_friend_fallback_content(self, event_data: EventData, 
                                        context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate fallback friend content when LLM fails.
        
        Args:
            event_data: Event data
            context_data: Friend context data
            
        Returns:
            Fallback content dictionary
        """
        event_name = event_data.event_name
        social_context = context_data.social_context
        event_details = context_data.event_details
        
        current_friend_count = social_context.get("current_friend_count", 0)
        user_role = social_context.get("user_role", "clam")
        
        # Generate content based on event type
        if event_name == "made_new_friend":
            title = "新朋友"
            if user_role == "lively":
                content = f"交到新朋友了！现在有{current_friend_count}个朋友😊"
            else:
                content = f"今天认识了新朋友，很开心"
                
        elif event_name == "friend_deleted":
            title = "失去朋友"
            if user_role == "lively":
                content = f"被朋友删除了😢有点难过"
            else:
                content = f"朋友关系结束了，有些失落"
                
        elif "disliked" in event_name:
            interaction_type = event_details.get("interaction_type", "互动")
            
            if "5_plus" in event_name:
                title = "很生气"
                content = f"朋友一直{interaction_type}，很烦😠"
            elif "3_to_5" in event_name:
                title = "不开心"
                content = f"朋友{interaction_type}太多次了😞"
            else:  # single
                title = "有点烦"
                content = f"朋友{interaction_type}了，不太喜欢"
                
        elif "liked" in event_name:
            interaction_type = event_details.get("interaction_type", "互动")
            frequency = event_details.get("interaction_frequency", "")
            
            if "5_plus" in event_name:
                title = "超开心"
                content = f"朋友{interaction_type}了好多次！太开心了🎉"
            elif "3_to_5" in event_name:
                title = "很开心"
                content = f"朋友连续{interaction_type}，心情很好😄"
            else:  # single
                title = "开心"
                content = f"朋友{interaction_type}了我，很开心😊"
                
        else:
            title = "朋友"
            content = f"今天和朋友有互动"
        
        # Select emotion tags
        emotion_tags = self._select_friend_emotion_tags(event_data.event_name, context_data)
        
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
            context_data: Friend context data
            
        Returns:
            Fallback diary entry
        """
        fallback_content = self._generate_friend_fallback_content(event_data, context_data)
        
        # Convert emotion tag strings to EmotionalTag enums
        emotion_tags = []
        for tag_str in fallback_content["emotion_tags"]:
            for tag in EmotionalTag:
                if tag.value == tag_str:
                    emotion_tags.append(tag)
                    break
        
        if not emotion_tags:
            emotion_tags = [EmotionalTag.CALM]
        
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