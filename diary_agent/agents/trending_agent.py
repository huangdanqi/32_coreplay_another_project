"""
Trending Agent for generating diary entries about trending news and social events.
Integrates with existing douyin_news.py module for trending data and classification.
"""

import json
from typing import List, Dict, Any
from datetime import datetime

from diary_agent.agents.base_agent import BaseSubAgent
from diary_agent.utils.data_models import EventData, DiaryEntry, DiaryContextData, EmotionalTag
from diary_agent.integration.trending_data_reader import TrendingDataReader


class TrendingAgent(BaseSubAgent):
    """
    Specialized agent for trending news and social event diary entries.
    Handles: celebration, disaster events from douyin trending topics.
    """
    
    def __init__(self, agent_type: str, prompt_config, llm_manager, data_reader: TrendingDataReader):
        super().__init__(agent_type, prompt_config, llm_manager, data_reader)
        self.supported_events = ["celebration", "disaster"]
    
    def get_supported_events(self) -> List[str]:
        """Get list of trending events this agent supports."""
        return self.supported_events.copy()
    
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process trending event and generate diary entry.
        
        Args:
            event_data: Trending event data
            
        Returns:
            Generated diary entry
            
        Raises:
            ValueError: If event is not supported
            LLMProviderError: If diary generation fails
        """
        if event_data.event_name not in self.supported_events:
            raise ValueError(f"Unsupported event: {event_data.event_name}")
        
        # Read trending context from existing module
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
        Generate trending-specific diary content using LLM.
        
        Args:
            event_data: Event data
            context_data: Trending context data
            
        Returns:
            Generated content dictionary
        """
        # Prepare trending-specific prompt
        trending_prompt = self._prepare_trending_prompt(event_data, context_data)
        
        try:
            # Generate content using parent method
            content_dict = await super().generate_diary_content(event_data, context_data)
            
            # Enhance with trending-specific emotion tags
            content_dict["emotion_tags"] = self._select_trending_emotion_tags(
                event_data.event_name, context_data
            )
            
            return content_dict
            
        except Exception as e:
            # Fallback to trending-specific generation
            return self._generate_trending_fallback_content(event_data, context_data)
    
    def _prepare_trending_prompt(self, event_data: EventData, context_data: DiaryContextData) -> str:
        """
        Prepare trending-specific prompt with rich context.
        
        Args:
            event_data: Event data
            context_data: Trending context data
            
        Returns:
            Formatted trending prompt
        """
        social_context = context_data.social_context
        event_details = context_data.event_details
        emotional_context = context_data.emotional_context
        
        # Build trending context string
        trending_words = social_context.get('trending_words', [])
        trending_topics = social_context.get('trending_topics', [])
        event_classification = social_context.get('event_classification', 'unknown')
        
        # Build social sentiment context
        social_sentiment = social_context.get('social_sentiment', 'neutral')
        emotional_impact = emotional_context.get('event_emotional_impact', 'neutral')
        
        # Build user context
        user_role = event_details.get("user_role", "clam")
        emotional_intensity = emotional_context.get("emotional_intensity", 1.0)
        
        # Create trending-specific prompt
        timestamp_str = event_data.timestamp.strftime('%Y-%m-%d %H:%M')
        trending_prompt = f"""
事件: {event_data.event_name}
时间: {timestamp_str}
热门话题: {', '.join(trending_topics[:3]) if trending_topics else '无'}
社会情绪: {social_sentiment}
事件分类: {event_classification}
用户性格: {user_role}
情感强度: {emotional_intensity}
情感影响: {emotional_impact}

当前热门词汇: {', '.join(trending_words[:5]) if trending_words else '无'}

请生成一篇关于当前热门话题的日记，要求：
1. 标题最多6个字符
2. 内容最多35个字符，可以包含表情符号
3. 选择合适的情感标签
4. 体现用户对当前社会事件的感受
5. 符合用户的性格特点
6. 反映社会情绪和热门话题的影响

输出格式为JSON:
{{"title": "标题", "content": "内容", "emotion_tags": ["情感标签"]}}
"""
        
        return trending_prompt.strip()
    
    def _select_trending_emotion_tags(self, event_name: str, context_data: DiaryContextData) -> List[str]:
        """
        Select appropriate emotion tags for trending events.
        
        Args:
            event_name: Trending event name
            context_data: Trending context data
            
        Returns:
            List of emotion tag strings
        """
        social_context = context_data.social_context
        emotional_context = context_data.emotional_context
        
        social_sentiment = social_context.get("social_sentiment", "neutral")
        emotional_intensity = emotional_context.get("emotional_intensity", 1.0)
        
        # Select emotion based on event type and social sentiment
        if event_name == "disaster":
            # Disaster events - negative emotions
            if emotional_intensity >= 1.5:
                return [EmotionalTag.ANGRY_FURIOUS.value]    # 生气愤怒
            elif social_sentiment == "negative":
                return [EmotionalTag.SAD_UPSET.value]        # 悲伤难过
            else:
                return [EmotionalTag.WORRIED.value]          # 担忧
                
        elif event_name == "celebration":
            # Celebration events - positive emotions
            if emotional_intensity >= 2.0:
                return [EmotionalTag.EXCITED_THRILLED.value] # 兴奋激动
            elif social_sentiment == "positive":
                return [EmotionalTag.HAPPY_JOYFUL.value]     # 开心快乐
            else:
                return [EmotionalTag.CURIOUS.value]          # 好奇
                
        else:
            # Default case
            return [EmotionalTag.CALM.value]                 # 平静
    
    def _generate_trending_fallback_content(self, event_data: EventData, 
                                          context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate fallback trending content when LLM fails.
        
        Args:
            event_data: Event data
            context_data: Trending context data
            
        Returns:
            Fallback content dictionary
        """
        import random
        
        social_context = context_data.social_context
        trending_topics = social_context.get('trending_topics', [])
        trending_words = social_context.get('trending_words', [])
        
        # Use all available trending words, not just topics
        all_trending = trending_words if trending_words else trending_topics
        
        # Generate varied trending-based content
        if event_data.event_name == "disaster":
            titles = ["担心", "忧虑", "难过", "震惊", "沉重"]
            title = random.choice(titles)
            
            if all_trending:
                # Randomly select from available trending words
                selected_topic = random.choice(all_trending[:10])  # Use top 10 for variety
                content_templates = [
                    f"看到{selected_topic}的新闻，有点担心😟",
                    f"关于{selected_topic}的消息让人忧虑😔",
                    f"{selected_topic}的事情真让人难过😢",
                    f"听到{selected_topic}的报道，心情沉重😞"
                ]
                content = random.choice(content_templates)
            else:
                content_options = [
                    "看到一些不好的新闻，心情沉重😔",
                    "今天的新闻让人担忧😟",
                    "社会上发生的事情让人难过😢"
                ]
                content = random.choice(content_options)
                
        elif event_data.event_name == "celebration":
            titles = ["开心", "兴奋", "高兴", "愉快", "欣喜"]
            title = random.choice(titles)
            
            if all_trending:
                # Randomly select from available trending words
                selected_topic = random.choice(all_trending[:10])  # Use top 10 for variety
                content_templates = [
                    f"看到{selected_topic}的消息，很开心😊",
                    f"关于{selected_topic}的好消息真棒😄",
                    f"{selected_topic}让人感到兴奋🎉",
                    f"听到{selected_topic}的报道，心情愉快😃"
                ]
                content = random.choice(content_templates)
            else:
                content_options = [
                    "看到一些好消息，心情不错😄",
                    "今天有让人开心的事情😊",
                    "社会上的正能量让人高兴🎉"
                ]
                content = random.choice(content_options)
        else:
            titles = ["热点", "关注", "话题", "新闻", "动态"]
            title = random.choice(titles)
            
            if all_trending:
                selected_topic = random.choice(all_trending[:10])
                content_templates = [
                    f"今天{selected_topic}很热门🤔",
                    f"关注{selected_topic}的动态📱",
                    f"{selected_topic}成为话题了💭"
                ]
                content = random.choice(content_templates)
            else:
                content = "今天的热门话题挺有意思的🤔"
        
        # Select emotion tags
        emotion_tags = self._select_trending_emotion_tags(event_data.event_name, context_data)
        
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
            context_data: Trending context data
            
        Returns:
            Fallback diary entry
        """
        fallback_content = self._generate_trending_fallback_content(event_data, context_data)
        
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