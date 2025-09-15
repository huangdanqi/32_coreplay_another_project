"""
Holiday Agent for generating diary entries about holiday and festival events.
Integrates with existing holiday_function.py module for Chinese calendar and holiday data.
"""

import json
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, DiaryContextData, EmotionalTag
from diary_agent.integration.holiday_data_reader import HolidayDataReader


class HolidayAgent(BaseSubAgent):
    """
    Specialized agent for holiday and festival diary entries.
    Handles: approaching_holiday, during_holiday, holiday_ends events.
    """
    
    def __init__(self, agent_type: str, prompt_config, llm_manager, data_reader: HolidayDataReader):
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.supported_events = ["approaching_holiday", "during_holiday", "holiday_ends"]
    
    def get_supported_events(self) -> List[str]:
        """Get list of holiday events this agent supports."""
        return self.supported_events.copy()
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process holiday event and generate diary entry.
        
        Args:
            event_data: Holiday event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        if event_data.event_name not in self.supported_events:
            raise ValueError(f"Unsupported event: {event_data.event_name}")
        
        # Read holiday context from existing module
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
        Generate holiday-specific diary content using LLM.
        
        Args:
            event_data: Event data
            context_data: Holiday context data
            
        Returns:
            Generated content dictionary
        """
        # Prepare holiday-specific prompt
        holiday_prompt = self._prepare_holiday_prompt(event_data, context_data)
        
        try:
            # Generate content using parent method
            content_dict = await super().generate_diary_content(event_data, context_data)
            
            # Enhance with holiday-specific emotion tags
            content_dict["emotion_tags"] = self._select_holiday_emotion_tags(
                event_data.event_name, context_data
            )
            
            return content_dict
            
        except Exception as e:
            # Fallback to holiday-specific generation
            return self._generate_holiday_fallback_content(event_data, context_data)
    
    def _prepare_holiday_prompt(self, event_data: EventData, context_data: DiaryContextData) -> str:
        """
        Prepare holiday-specific prompt with rich context.
        
        Args:
            event_data: Event data
            context_data: Holiday context data
            
        Returns:
            Formatted holiday prompt
        """
        temporal_context = context_data.temporal_context
        social_context = context_data.social_context
        emotional_context = context_data.emotional_context
        event_details = context_data.event_details
        
        # Build holiday context string
        holiday_name = event_details.get('holiday_name', 'Unknown')
        holiday_timing = temporal_context.get('holiday_timing', 'unknown')
        days_to_holiday = temporal_context.get('days_to_holiday', 0)
        
        # Build cultural context
        cultural_significance = social_context.get('cultural_significance', 'moderate')
        typical_activities = social_context.get('typical_activities', [])
        
        # Build emotional context
        holiday_emotional_tone = emotional_context.get('holiday_emotional_tone', 'neutral')
        anticipation_level = emotional_context.get('anticipation_level', 'low')
        
        # Build user context
        user_role = event_details.get("user_role", "clam")
        emotional_intensity = emotional_context.get("emotional_intensity", 1.0)
        
        # Create holiday-specific prompt
        timestamp_str = event_data.timestamp.strftime('%Y-%m-%d %H:%M')
        
        # Format days information
        if days_to_holiday > 0:
            days_info = f"还有{days_to_holiday}天"
        elif days_to_holiday == 0:
            days_info = "今天就是"
        else:
            days_info = f"已经过去{abs(days_to_holiday)}天"
        
        holiday_prompt = f"""
事件: {event_data.event_name}
时间: {timestamp_str}
节假日: {holiday_name}
节假日时间: {days_info}
文化意义: {cultural_significance}
情感基调: {holiday_emotional_tone}
期待程度: {anticipation_level}
用户性格: {user_role}
情感强度: {emotional_intensity}

传统活动: {', '.join(typical_activities[:3]) if typical_activities else '休息庆祝'}

请生成一篇关于节假日的日记，要求：
1. 标题最多6个字符
2. 内容最多35个字符，可以包含表情符号
3. 选择合适的情感标签
4. 体现用户对节假日的真实感受
5. 符合节假日的文化背景和传统
6. 体现节假日不同阶段的情感变化
7. 符合用户的性格特点

输出格式为JSON:
{{"title": "标题", "content": "内容", "emotion_tags": ["情感标签"]}}
"""
        
        return holiday_prompt.strip()
    
    def _select_holiday_emotion_tags(self, event_name: str, context_data: DiaryContextData) -> List[str]:
        """
        Select appropriate emotion tags for holiday events.
        
        Args:
            event_name: Holiday event name
            context_data: Holiday context data
            
        Returns:
            List of emotion tag strings
        """
        emotional_context = context_data.emotional_context
        temporal_context = context_data.temporal_context
        
        anticipation_level = emotional_context.get("anticipation_level", "low")
        emotional_intensity = emotional_context.get("emotional_intensity", 1.0)
        holiday_name = context_data.event_details.get('holiday_name', '')
        
        # Select emotion based on event type and holiday context
        if event_name == "approaching_holiday":
            # Approaching holiday - anticipation and excitement
            if anticipation_level == "very_high" or "春节" in holiday_name:
                return [EmotionalTag.EXCITED_THRILLED.value]  # 兴奋激动
            elif anticipation_level == "high":
                return [EmotionalTag.HAPPY_JOYFUL.value]      # 开心快乐
            else:
                return [EmotionalTag.CURIOUS.value]           # 好奇
                
        elif event_name == "during_holiday":
            # During holiday - joy and celebration
            if emotional_intensity >= 2.0:
                return [EmotionalTag.EXCITED_THRILLED.value]  # 兴奋激动
            else:
                return [EmotionalTag.HAPPY_JOYFUL.value]      # 开心快乐
                
        elif event_name == "holiday_ends":
            # Holiday ending - nostalgia and sadness
            if emotional_intensity >= 1.5:
                return [EmotionalTag.SAD_UPSET.value]         # 悲伤难过
            else:
                return [EmotionalTag.CALM.value]              # 平静
                
        else:
            # Default case
            return [EmotionalTag.CALM.value]                  # 平静
    
    def _generate_holiday_fallback_content(self, event_data: EventData, 
                                         context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate fallback holiday content when LLM fails.
        
        Args:
            event_data: Event data
            context_data: Holiday context data
            
        Returns:
            Fallback content dictionary
        """
        event_details = context_data.event_details
        temporal_context = context_data.temporal_context
        
        holiday_name = event_details.get('holiday_name', '节假日')
        days_to_holiday = temporal_context.get('days_to_holiday', 0)
        
        # Generate simple holiday-based content
        if event_data.event_name == "approaching_holiday":
            title = "期待"
            if days_to_holiday > 0:
                content = f"{holiday_name}快到了，还有{days_to_holiday}天😊"
            else:
                content = f"{holiday_name}快到了，很期待🎉"
                
        elif event_data.event_name == "during_holiday":
            title = "假期"
            content = f"今天是{holiday_name}，很开心😄"
            
        elif event_data.event_name == "holiday_ends":
            title = "结束"
            content = f"{holiday_name}结束了，有点不舍😔"
            
        else:
            title = "节日"
            content = f"今天和{holiday_name}有关的日子"
        
        # Ensure character limits
        title = title[:6]
        content = content[:35]
        
        # Select emotion tags
        emotion_tags = self._select_holiday_emotion_tags(event_data.event_name, context_data)
        
        return {
            "title": title,
            "content": content,
            "emotion_tags": emotion_tags
        }
    
    def _create_fallback_entry(self, event_data: EventData, context_data: DiaryContextData) -> DiaryEntry:
        """
        Create fallback diary entry when validation fails.
        
        Args:
            event_data: Event data
            context_data: Holiday context data
            
        Returns:
            Fallback diary entry
        """
        fallback_content = self._generate_holiday_fallback_content(event_data, context_data)
        
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