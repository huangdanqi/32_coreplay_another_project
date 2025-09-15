"""
Diary Agent for generating general diary entries.
Supports two modes: LLM-based generation and default content generation.
"""

import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

from agents.base_agent import BaseSubAgent
from utils.data_models import EventData, DiaryEntry, DiaryContextData, EmotionalTag
from utils.data_models import DataReader


class DiaryAgent(BaseSubAgent):
    """
    General diary agent for creating diary entries.
    Supports both LLM-based generation and default content generation.
    """
    
    def __init__(self, agent_type: str, prompt_config, llm_manager, data_reader: DataReader, use_llm: bool = True):
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.use_llm = use_llm
        self.supported_events = [
            "daily_reflection", "personal_milestone", "learning_experience",
            "social_interaction", "work_achievement", "hobby_activity",
            "health_wellness", "travel_experience", "family_event",
            "general_diary", "random_thought", "goal_progress"
        ]
        
        # Default content templates for non-LLM mode
        self.default_templates = {
            "daily_reflection": {
                "titles": ["今日感悟", "生活点滴", "日常记录", "今日心情"],
                "contents": [
                    "今天过得还不错，记录一下生活点滴 ✨",
                    "平凡的一天，但也有很多值得记住的瞬间 🌟",
                    "生活就是由这些小确幸组成的 💫",
                    "今天的心情很平静，适合记录 📝"
                ],
                "emotions": [EmotionalTag.CALM, EmotionalTag.HAPPY_JOYFUL]
            },
            "personal_milestone": {
                "titles": ["重要时刻", "里程碑", "突破", "成就"],
                "contents": [
                    "今天完成了一个重要目标，很开心 🎉",
                    "又向前迈进了一步，继续加油 💪",
                    "这个里程碑值得好好记录 📊",
                    "努力终有回报，感觉很棒 ⭐"
                ],
                "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED]
            },
            "learning_experience": {
                "titles": ["学习收获", "新知识", "成长", "进步"],
                "contents": [
                    "今天学到了新东西，很有收获 📚",
                    "知识就是力量，继续学习 💡",
                    "每一次学习都是成长的机会 🌱",
                    "保持好奇心，保持学习 📖"
                ],
                "emotions": [EmotionalTag.CURIOUS, EmotionalTag.HAPPY_JOYFUL]
            },
            "social_interaction": {
                "titles": ["社交时光", "朋友聚会", "人际交往", "社交"],
                "contents": [
                    "和朋友聊天很开心，社交很重要 👥",
                    "人际关系需要用心经营 💝",
                    "今天认识新朋友，很兴奋 🤝",
                    "社交让生活更丰富多彩 🌈"
                ],
                "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED]
            },
            "work_achievement": {
                "titles": ["工作成果", "职场进步", "职业发展", "工作"],
                "contents": [
                    "工作有进展，感觉很有成就感 💼",
                    "职场路上又前进了一步 📈",
                    "努力工作的感觉真好 ⚡",
                    "专业能力在不断提升 🔧"
                ],
                "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED]
            },
            "hobby_activity": {
                "titles": ["兴趣爱好", "休闲时光", "爱好", "娱乐"],
                "contents": [
                    "做喜欢的事情真的很开心 🎨",
                    "兴趣爱好让生活更有趣 🎵",
                    "休闲时光总是过得很快 ⏰",
                    "培养爱好是很好的投资 🌟"
                ],
                "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM]
            },
            "health_wellness": {
                "titles": ["健康生活", "身心状态", "养生", "健康"],
                "contents": [
                    "健康是最重要的财富 💪",
                    "身心状态很好，继续保持 🧘",
                    "养生之道，贵在坚持 🌿",
                    "健康的生活方式让人愉悦 😊"
                ],
                "emotions": [EmotionalTag.CALM, EmotionalTag.HAPPY_JOYFUL]
            },
            "travel_experience": {
                "titles": ["旅行见闻", "探索世界", "旅途", "旅行"],
                "contents": [
                    "旅行让人开阔眼界 🌍",
                    "探索新地方很有趣 🗺️",
                    "旅途中的风景很美 📸",
                    "旅行是人生的重要体验 ✈️"
                ],
                "emotions": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.CURIOUS]
            },
            "family_event": {
                "titles": ["家庭时光", "亲情", "家人", "家庭"],
                "contents": [
                    "和家人在一起的时光很珍贵 👨‍👩‍👧‍👦",
                    "亲情是最温暖的港湾 🏠",
                    "家庭是永远的依靠 💕",
                    "家人的爱是最无私的 ❤️"
                ],
                "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM]
            },
            "general_diary": {
                "titles": ["日记", "记录", "生活", "日常"],
                "contents": [
                    "记录生活的美好时刻 📝",
                    "每一天都值得被记住 ⭐",
                    "生活中有很多小确幸 🌸",
                    "保持记录的习惯很好 📖"
                ],
                "emotions": [EmotionalTag.CALM, EmotionalTag.HAPPY_JOYFUL]
            },
            "random_thought": {
                "titles": ["随想", "思考", "感悟", "想法"],
                "contents": [
                    "突然想到一些有趣的事情 💭",
                    "思考让人成长 🤔",
                    "有时候想法很奇妙 ✨",
                    "记录下此刻的想法 📝"
                ],
                "emotions": [EmotionalTag.CURIOUS, EmotionalTag.CALM]
            },
            "goal_progress": {
                "titles": ["目标进展", "计划执行", "目标", "计划"],
                "contents": [
                    "朝着目标又前进了一步 🎯",
                    "计划执行得很顺利 📋",
                    "目标让人更有动力 🚀",
                    "坚持就是胜利 💪"
                ],
                "emotions": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.HAPPY_JOYFUL]
            }
        }
    
    def get_supported_events(self) -> List[str]:
        """Get list of events this agent supports."""
        return self.supported_events.copy()
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process event and generate diary entry.
        
        Args:
            event_data: Event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        if event_data.event_name not in self.supported_events:
            raise ValueError(f"Unsupported event: {event_data.event_name}")
        
        # Read event context
        context_data = await self.read_event_context(event_data)
        
        # Generate diary content based on mode
        if self.use_llm:
            content_dict = await self.generate_diary_content(event_data, context_data)
        else:
            content_dict = self.generate_default_content(event_data, context_data)
        
        # Create diary entry
        diary_entry = await self._create_diary_entry(event_data, content_dict)
        
        # Validate and format output
        if not self.validate_output(diary_entry):
            # If validation fails, create a fallback entry
            diary_entry = self._create_fallback_entry(event_data, context_data)
        
        formatted_entry = self.format_output(diary_entry)
        
        return formatted_entry
    
    def generate_default_content(self, event_data: EventData, context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate default content without using LLM.
        
        Args:
            event_data: Event data
            context_data: Context data
            
        Returns:
            Generated content dictionary
        """
        self.logger.info(f"Generating default content for event: {event_data.event_name}")
        
        # Get template for this event type
        template = self.default_templates.get(event_data.event_name, self.default_templates["general_diary"])
        
        # Randomly select content
        title = random.choice(template["titles"])
        content = random.choice(template["contents"])
        emotion_tags = random.sample(template["emotions"], min(2, len(template["emotions"])))
        
        return {
            "title": title,
            "content": content,
            "emotion_tags": [emotion.value for emotion in emotion_tags],
            "source": "default_template"
        }
    

    
    async def generate_diary_content(self, event_data: EventData, context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate diary content using LLM with custom prompt.
        
        Args:
            event_data: Event data
            context_data: Context data
            
        Returns:
            Generated content dictionary
        """
        try:
            # Generate content using parent method (which uses LLM with our prompt config)
            content_dict = await super().generate_diary_content(event_data, context_data)
            
            # Add source information
            content_dict["source"] = "llm_diary_prompt"
            
            return content_dict
            
        except Exception as e:
            # Fallback to default content if LLM fails
            self.logger.warning(f"LLM generation failed, falling back to default: {str(e)}")
            return self.generate_default_content(event_data, context_data)
    

    
    async def _create_diary_entry(self, event_data: EventData, content_dict: Dict[str, Any]) -> DiaryEntry:
        """
        Create diary entry from generated content.
        
        Args:
            event_data: Event data
            content_dict: Generated content dictionary
            
        Returns:
            Diary entry
        """
        # Convert emotion tag strings to EmotionalTag enum
        emotion_tags = []
        for emotion_str in content_dict.get("emotion_tags", []):
            try:
                emotion_tags.append(EmotionalTag(emotion_str))
            except ValueError:
                # If emotion tag is invalid, use CALM as default
                emotion_tags.append(EmotionalTag.CALM)
        
        # If no emotion tags, add default
        if not emotion_tags:
            emotion_tags = [EmotionalTag.CALM]
        
        return DiaryEntry(
            entry_id=f"diary_{event_data.event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=event_data.user_id,
            timestamp=event_data.timestamp,
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title=content_dict.get("title", "记录"),
            content=content_dict.get("content", "今天发生了一些事情。"),
            emotion_tags=emotion_tags,
            agent_type=self.agent_type,
            llm_provider=content_dict.get("source", "default")
        )
    
    def _create_fallback_entry(self, event_data: EventData, context_data: DiaryContextData) -> DiaryEntry:
        """
        Create fallback diary entry when generation fails.
        
        Args:
            event_data: Event data
            context_data: Context data
            
        Returns:
            Fallback diary entry
        """
        self.logger.warning(f"Creating fallback entry for event: {event_data.event_name}")
        
        return DiaryEntry(
            entry_id=f"fallback_{event_data.event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=event_data.user_id,
            timestamp=event_data.timestamp,
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title="记录",
            content=f"今天发生了{event_data.event_name}相关的事情。",
            emotion_tags=[EmotionalTag.CALM],
            agent_type=self.agent_type,
            llm_provider="fallback"
        )
    
    def validate_output(self, diary_entry: DiaryEntry) -> bool:
        """
        Validate generated diary entry.
        
        Args:
            diary_entry: Diary entry to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check title length
            if len(diary_entry.title) > 6:
                return False
            
            # Check content length
            if len(diary_entry.content) > 35:
                return False
            
            # Check emotion tags
            if not diary_entry.emotion_tags:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False
    
    def format_output(self, diary_entry: DiaryEntry) -> DiaryEntry:
        """
        Format diary entry for output.
        
        Args:
            diary_entry: Diary entry to format
            
        Returns:
            Formatted diary entry
        """
        # Ensure title and content are within limits
        if len(diary_entry.title) > 6:
            diary_entry.title = diary_entry.title[:6]
        
        if len(diary_entry.content) > 35:
            diary_entry.content = diary_entry.content[:35]
        
        return diary_entry
    
    def set_llm_mode(self, use_llm: bool):
        """
        Set whether to use LLM or default content.
        
        Args:
            use_llm: True to use LLM, False to use default content
        """
        self.use_llm = use_llm
        self.logger.info(f"Diary agent LLM mode set to: {use_llm}")
    
    def get_llm_mode(self) -> bool:
        """
        Get current LLM mode.
        
        Returns:
            True if using LLM, False if using default content
        """
        return self.use_llm
