"""
Formatting utilities for diary entries.
"""

import random
import re
import unicodedata
from datetime import datetime
from typing import List, Dict, Any, Union
from .data_models import DiaryEntry, EmotionalTag


class DiaryEntryFormatter:
    """No-op formatter: keep exact LLM output (no truncation)."""
    
    def __init__(self):
        pass
    
    def format_diary_entry(self, entry: DiaryEntry) -> DiaryEntry:
        return entry
    
    def _format_title(self, title: str) -> str:
        return title or ""
    
    def _format_content(self, content: str) -> str:
        return content or ""
    
    def _format_emotional_tags(self, tags: List[EmotionalTag]) -> List[EmotionalTag]:
        """Format emotional tags list."""
        if not tags:
            return [EmotionalTag.CALM]  # Default to calm
        
        # Remove duplicates while preserving order
        seen = set()
        formatted_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                formatted_tags.append(tag)
        
        return formatted_tags
    
    def _get_display_width(self, text: str) -> int:
        """
        Get display width of text considering wide characters and emojis.
        
        Args:
            text: Text to measure
            
        Returns:
            Display width in character units
        """
        width = 0
        for char in text:
            # Check if character is wide (CJK characters, etc.)
            if unicodedata.east_asian_width(char) in ('F', 'W'):
                width += 2
            # Check if character is emoji (simplified check)
            elif ord(char) > 0x1F000:
                width += 2
            else:
                width += 1
        return width
    
    def _truncate_to_width(self, text: str, max_width: int) -> str:
        """
        Truncate text to specified display width.
        
        Args:
            text: Text to truncate
            max_width: Maximum display width
            
        Returns:
            Truncated text
        """
        current_width = 0
        result = ""
        
        for char in text:
            char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W') or ord(char) > 0x1F000 else 1
            
            if current_width + char_width > max_width:
                break
            
            result += char
            current_width += char_width
        
        return result


class DiaryFormatter:
    """Formatter for diary entries."""
    
    @classmethod
    def format_timestamp(cls, timestamp: datetime) -> str:
        """Format timestamp for diary entry."""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def generate_entry_id(cls, user_id: int, timestamp: datetime, event_type: str) -> str:
        """Generate unique entry ID."""
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")
        return f"diary_{user_id}_{date_str}_{time_str}_{event_type}"
    
    @classmethod
    def truncate_title(cls, title: str, max_length: int = 6) -> str:
        """Truncate title to maximum length."""
        if len(title) <= max_length:
            return title
        return title[:max_length-1] + "…"
    
    @classmethod
    def truncate_content(cls, content: str, max_length: int = 35) -> str:
        """Truncate content to maximum length."""
        if len(content) <= max_length:
            return content
        return content[:max_length-3] + "..."
    
    @classmethod
    def select_emotional_tags(cls, context: Dict[str, Any], event_type: str) -> List[EmotionalTag]:
        """Select appropriate emotional tags based on context."""
        # Default emotional tag mapping based on event types
        event_emotion_mapping = {
            "weather_events": {
                "favorite_weather": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM],
                "dislike_weather": [EmotionalTag.SAD_UPSET, EmotionalTag.WORRIED],
                "favorite_season": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.HAPPY_JOYFUL],
                "dislike_season": [EmotionalTag.ANXIOUS_MELANCHOLY, EmotionalTag.SAD_UPSET]
            },
            "trending_events": {
                "celebration": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.HAPPY_JOYFUL],
                "disaster": [EmotionalTag.WORRIED, EmotionalTag.SAD_UPSET]
            },
            "holiday_events": {
                "approaching_holiday": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.CURIOUS],
                "during_holiday": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED],
                "holiday_ends": [EmotionalTag.SAD_UPSET, EmotionalTag.CALM]
            },
            "friends_function": {
                "made_new_friend": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED],
                "friend_deleted": [EmotionalTag.SAD_UPSET, EmotionalTag.WORRIED],
                "liked_single": [EmotionalTag.HAPPY_JOYFUL],
                "disliked_single": [EmotionalTag.ANGRY_FURIOUS]
            },
            "same_frequency": {
                "close_friend_frequency": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.HAPPY_JOYFUL]
            },
            "adopted_function": {
                "toy_claimed": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.CURIOUS]
            },
            "human_toy_interactive_function": {
                "liked_interaction_once": [EmotionalTag.HAPPY_JOYFUL],
                "disliked_interaction_once": [EmotionalTag.ANGRY_FURIOUS],
                "neutral_interaction_over_5_times": [EmotionalTag.CALM]
            },
            "human_toy_talk": {
                "positive_emotional_dialogue": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED],
                "negative_emotional_dialogue": [EmotionalTag.WORRIED, EmotionalTag.SAD_UPSET]
            },
            "unkeep_interactive": {
                "neglect_1_day_no_dialogue": [EmotionalTag.SAD_UPSET],
                "neglect_7_days_no_interaction": [EmotionalTag.ANXIOUS_MELANCHOLY, EmotionalTag.WORRIED]
            }
        }
        
        # Get event name from context
        event_name = context.get("event_name", "")
        
        # Find appropriate emotions
        if event_type in event_emotion_mapping:
            type_emotions = event_emotion_mapping[event_type]
            if event_name in type_emotions:
                emotions = type_emotions[event_name]
                # Randomly select 1-2 emotions
                num_emotions = random.randint(1, min(2, len(emotions)))
                return random.sample(emotions, num_emotions)
        
        # Default fallback emotion
        return [EmotionalTag.CALM]
    
    @classmethod
    def format_diary_entry_for_storage(cls, entry: DiaryEntry) -> Dict[str, Any]:
        """Format diary entry for database storage."""
        return {
            "entry_id": entry.entry_id,
            "user_id": entry.user_id,
            "timestamp": cls.format_timestamp(entry.timestamp),
            "event_type": entry.event_type,
            "event_name": entry.event_name,
            "title": entry.title,
            "content": entry.content,
            "emotion_tags": [tag.value for tag in entry.emotion_tags],
            "agent_type": entry.agent_type,
            "llm_provider": entry.llm_provider
        }
    
    @classmethod
    def format_diary_entry_for_display(cls, entry: DiaryEntry) -> str:
        """Format diary entry for display."""
        timestamp_str = cls.format_timestamp(entry.timestamp)
        emotions_str = ", ".join([tag.value for tag in entry.emotion_tags])
        
        return f"""
📅 {timestamp_str}
😊 {emotions_str}
📝 {entry.title}
💭 {entry.content}
🤖 {entry.agent_type}
        """.strip()


class LLMResponseFormatter:
    """Formats LLM responses for consistency."""
    
    def format_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Format LLM response into structured diary entry data.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured diary entry data
        """
        # Parse JSON response if possible
        import json
        try:
            parsed = json.loads(response.strip())
            if isinstance(parsed, dict):
                return self._format_parsed_response(parsed)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Parse text response
        return self._parse_text_response(response)
    
    def _format_parsed_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Format parsed JSON response."""
        formatted = {
            'title': parsed.get('title', parsed.get('标题', '')),
            'content': parsed.get('content', parsed.get('内容', '')),
            'emotion_tags': parsed.get('emotion_tags', parsed.get('情感标签', []))
        }
        
        # Ensure emotion_tags is a list
        if isinstance(formatted['emotion_tags'], str):
            formatted['emotion_tags'] = [tag.strip() for tag in formatted['emotion_tags'].split(',')]
        
        return formatted
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Parse text-based LLM response."""
        lines = response.strip().split('\n')
        
        formatted = {
            'title': '',
            'content': '',
            'emotion_tags': []
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse title
            if any(line.startswith(prefix) for prefix in ['标题:', 'Title:', '题目:', 'title:']):
                formatted['title'] = self._extract_value_after_colon(line)
            
            # Parse content
            elif any(line.startswith(prefix) for prefix in ['内容:', 'Content:', '正文:', 'content:']):
                formatted['content'] = self._extract_value_after_colon(line)
            
            # Parse emotions
            elif any(line.startswith(prefix) for prefix in ['情感:', 'Emotion:', '情感标签:', 'emotion:', 'emotions:']):
                emotions = self._extract_value_after_colon(line)
                formatted['emotion_tags'] = [e.strip() for e in emotions.split(',') if e.strip()]
        
        # If no structured format found, try to extract from free text
        if not formatted['title'] and not formatted['content']:
            formatted = self._extract_from_free_text(response)
        
        return formatted
    
    def _extract_value_after_colon(self, line: str) -> str:
        """Extract value after colon in a line."""
        parts = line.split(':', 1)
        return parts[1].strip() if len(parts) > 1 else ''
    
    def _extract_from_free_text(self, text: str) -> Dict[str, Any]:
        """Extract diary components from free text."""
        # Simple heuristic: first line as title, rest as content
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        
        if not lines:
            return {'title': '', 'content': '', 'emotion_tags': []}
        
        title = lines[0]
        content = ' '.join(lines[1:]) if len(lines) > 1 else lines[0]
        
        return {
            'title': title,
            'content': content,
            'emotion_tags': []
        }