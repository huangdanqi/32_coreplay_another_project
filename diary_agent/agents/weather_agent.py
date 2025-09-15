"""
Weather Agent for generating diary entries about weather and seasonal events.
Integrates with existing weather_function.py module for weather data and preferences.
"""

import json
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, DiaryContextData, EmotionalTag
from diary_agent.integration.weather_data_reader import WeatherDataReader


class WeatherAgent(BaseSubAgent):
    """
    Specialized agent for weather and seasonal diary entries.
    Handles: favorite_weather, dislike_weather, favorite_season, dislike_season events.
    """
    
    def __init__(self, agent_type: str, prompt_config, llm_manager, data_reader: WeatherDataReader):
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.supported_events = [
            "favorite_weather", "dislike_weather", 
            "favorite_season", "dislike_season"
        ]
    
    def get_supported_events(self) -> List[str]:
        """Get list of weather events this agent supports."""
        return self.supported_events.copy()
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process weather event and generate diary entry.
        
        Args:
            event_data: Weather event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        if event_data.event_name not in self.supported_events:
            raise ValueError(f"Unsupported event: {event_data.event_name}")
        
        # Read weather context from existing module
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
        Generate weather-specific diary content using LLM.
        
        Args:
            event_data: Event data
            context_data: Weather context data
            
        Returns:
            Generated content dictionary
        """
        # Prepare weather-specific prompt
        weather_prompt = self._prepare_weather_prompt(event_data, context_data)
        
        try:
            # Generate content using parent method
            content_dict = await super().generate_diary_content(event_data, context_data)
            
            # Enhance with weather-specific emotion tags
            content_dict["emotion_tags"] = self._select_weather_emotion_tags(
                event_data.event_name, context_data
            )
            
            return content_dict
            
        except Exception as e:
            # Fallback to weather-specific generation
            return self._generate_weather_fallback_content(event_data, context_data)
    
    def _prepare_weather_prompt(self, event_data: EventData, context_data: DiaryContextData) -> str:
        """
        Prepare weather-specific prompt with rich context.
        
        Args:
            event_data: Event data
            context_data: Weather context data
            
        Returns:
            Formatted weather prompt
        """
        env_context = context_data.environmental_context
        event_details = context_data.event_details
        emotional_context = context_data.emotional_context
        
        # Build weather context string
        weather_info = f"当前天气: {env_context.get('current_weather', 'Unknown')}"
        season_info = f"当前季节: {env_context.get('current_season', 'Unknown')}"
        city_info = f"城市: {env_context.get('city', 'Unknown')}"
        
        # Build preference context
        preference_match = event_details.get("preference_match", False)
        user_role = event_details.get("user_role", "clam")
        
        # Build emotional context
        emotion_impact = env_context.get("emotion_impact", {})
        emotional_intensity = emotional_context.get("emotional_intensity", 1.0)
        
        # Create weather-specific prompt
        timestamp_str = event_data.timestamp.strftime('%Y-%m-%d %H:%M')
        weather_prompt = f"""
事件: {event_data.event_name}
时间: {timestamp_str}
{weather_info}
{season_info}
{city_info}
用户性格: {user_role}
偏好匹配: {'是' if preference_match else '否'}
情感强度: {emotional_intensity}
情感影响: 快乐度{emotion_impact.get('x_change', 0):+d}, 活跃度{emotion_impact.get('y_change', 0):+d}

请生成一篇关于天气或季节的日记，要求：
1. 标题最多6个字符
2. 内容最多35个字符，可以包含表情符号
3. 选择合适的情感标签
4. 体现用户对当前天气/季节的感受
5. 符合用户的性格特点

输出格式为JSON:
{{"title": "标题", "content": "内容", "emotion_tags": ["情感标签"]}}
"""
        
        return weather_prompt.strip()
    
    def _select_weather_emotion_tags(self, event_name: str, context_data: DiaryContextData) -> List[str]:
        """
        Select appropriate emotion tags for weather events.
        
        Args:
            event_name: Weather event name
            context_data: Weather context data
            
        Returns:
            List of emotion tag strings
        """
        event_details = context_data.event_details
        preference_match = event_details.get("preference_match", False)
        emotional_intensity = context_data.emotional_context.get("emotional_intensity", 1.0)
        
        # Select emotion based on event type and preference match
        if "favorite" in event_name and preference_match:
            # Favorite weather/season and it matches current condition
            if emotional_intensity >= 1.5:
                return [EmotionalTag.EXCITED_THRILLED.value]  # 兴奋激动
            else:
                return [EmotionalTag.HAPPY_JOYFUL.value]    # 开心快乐
                
        elif "favorite" in event_name and not preference_match:
            # Favorite weather/season but current condition doesn't match
            return [EmotionalTag.CALM.value]         # 平静
            
        elif "dislike" in event_name and preference_match:
            # Dislike weather/season and it matches current condition (bad weather)
            if emotional_intensity >= 1.0:
                return [EmotionalTag.ANGRY_FURIOUS.value]    # 生气愤怒
            else:
                return [EmotionalTag.SAD_UPSET.value]      # 悲伤难过
                
        elif "dislike" in event_name and not preference_match:
            # Dislike weather/season but current condition is not the disliked one
            return [EmotionalTag.CALM.value]         # 平静
            
        else:
            # Default case
            return [EmotionalTag.CALM.value]         # 平静
    
    def _generate_weather_fallback_content(self, event_data: EventData, 
                                         context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate fallback weather content when LLM fails.
        
        Args:
            event_data: Event data
            context_data: Weather context data
            
        Returns:
            Fallback content dictionary
        """
        env_context = context_data.environmental_context
        event_details = context_data.event_details
        
        current_weather = env_context.get("current_weather", "晴天")
        current_season = env_context.get("current_season", "春天")
        preference_match = event_details.get("preference_match", False)
        
        # Generate simple weather-based content
        if "weather" in event_data.event_name:
            if "favorite" in event_data.event_name and preference_match:
                title = "好天气"
                content = f"今天是{current_weather}，心情很好😊"
            elif "dislike" in event_data.event_name and preference_match:
                title = "坏天气"
                content = f"今天{current_weather}，有点不开心😔"
            else:
                title = "天气"
                content = f"今天天气{current_weather}，还好吧"
        else:  # season event
            if "favorite" in event_data.event_name and preference_match:
                title = "好季节"
                content = f"{current_season}来了，很喜欢这个季节🌸"
            elif "dislike" in event_data.event_name and preference_match:
                title = "讨厌"
                content = f"{current_season}又来了，不太喜欢😞"
            else:
                title = "季节"
                content = f"现在是{current_season}，时间过得真快"
        
        # Select emotion tags
        emotion_tags = self._select_weather_emotion_tags(event_data.event_name, context_data)
        
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
            context_data: Weather context data
            
        Returns:
            Fallback diary entry
        """
        fallback_content = self._generate_weather_fallback_content(event_data, context_data)
        
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


class SeasonalAgent(WeatherAgent):
    """
    Specialized agent for seasonal diary entries.
    Inherits from WeatherAgent since both use weather_function.py.
    """
    
    def __init__(self, agent_type: str, prompt_config, llm_manager, data_reader: WeatherDataReader):
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.supported_events = ["favorite_season", "dislike_season"]
    
    def get_supported_events(self) -> List[str]:
        """Get list of seasonal events this agent supports."""
        return self.supported_events.copy()