"""
Diary entry generation and formatting system.
Handles the complete workflow of generating, validating, and formatting diary entries.
"""

import json
import uuid
import asyncio
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, EmotionalTag, DailyQuota
)
from diary_agent.utils.validators import DiaryEntryValidator, ContentValidator
from diary_agent.utils.formatters import DiaryFormatter
from diary_agent.core.llm_manager import LLMConfigManager, LLMProviderError
from diary_agent.agents.base_agent import BaseSubAgent, AgentRegistry


class DiaryEntryGenerator:
    """
    Main diary entry generation system that orchestrates the complete workflow
    of generating, validating, and formatting diary entries.
    """
    
    def __init__(self, 
                 llm_manager: LLMConfigManager,
                 agent_registry: AgentRegistry,
                 storage_path: str = "diary_agent/data/diary_entries"):
        """
        Initialize diary entry generator.
        
        Args:
            llm_manager: LLM configuration manager
            agent_registry: Registry of available sub-agents
            storage_path: Path for storing diary entries
        """
        self.llm_manager = llm_manager
        self.agent_registry = agent_registry
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize validators and formatters
        self.entry_validator = DiaryEntryValidator()
        self.content_validator = ContentValidator()
        self.formatter = DiaryFormatter()
        
        # Daily quota tracking
        self.daily_quotas: Dict[str, DailyQuota] = {}  # date_str -> DailyQuota
        
        # Statistics tracking
        self.generation_stats = {
            "total_generated": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "validation_failures": 0,
            "formatting_corrections": 0
        }
    
    async def generate_diary_entry(self, 
                                 event_data: EventData,
                                 force_generation: bool = False) -> Optional[DiaryEntry]:
        """
        Generate a diary entry for the given event.
        
        Args:
            event_data: Event data to generate diary for
            force_generation: If True, bypass daily quota checks
            
        Returns:
            Generated diary entry or None if generation fails/skipped
            
        Raises:
            LLMProviderError: If LLM generation fails
            ValidationError: If generated entry cannot be validated
        """
        try:
            # Check daily quota unless forced
            if not force_generation and not self._can_generate_diary(event_data):
                return None
            
            # Get appropriate agent for this event
            agent = self.agent_registry.get_agent_for_event(event_data.event_name)
            if not agent:
                raise ValueError(f"No agent found for event: {event_data.event_name}")
            
            # Generate diary entry using the agent
            diary_entry = await agent.process_event(event_data)
            
            # Validate and format the entry
            validated_entry = await self._validate_and_format_entry(diary_entry)
            
            # Update daily quota
            if not force_generation:
                self._update_daily_quota(event_data)
            
            # Store the entry
            await self._store_diary_entry(validated_entry)
            
            # Update statistics
            self.generation_stats["total_generated"] += 1
            self.generation_stats["successful_generations"] += 1
            
            return validated_entry
            
        except Exception as e:
            self.generation_stats["total_generated"] += 1
            self.generation_stats["failed_generations"] += 1
            raise e
    
    async def generate_multiple_entries(self, 
                                      event_list: List[EventData],
                                      max_concurrent: int = 3) -> List[DiaryEntry]:
        """
        Generate multiple diary entries concurrently.
        
        Args:
            event_list: List of events to generate diaries for
            max_concurrent: Maximum concurrent generations
            
        Returns:
            List of successfully generated diary entries
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(event_data: EventData) -> Optional[DiaryEntry]:
            async with semaphore:
                try:
                    return await self.generate_diary_entry(event_data)
                except Exception as e:
                    print(f"Failed to generate diary for event {event_data.event_id}: {str(e)}")
                    return None
        
        # Generate entries concurrently
        tasks = [generate_with_semaphore(event) for event in event_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_entries = [
            result for result in results 
            if isinstance(result, DiaryEntry)
        ]
        
        return successful_entries
    
    async def _validate_and_format_entry(self, entry: DiaryEntry) -> DiaryEntry:
        """
        Validate and format a diary entry according to specifications.
        
        Args:
            entry: Raw diary entry from agent
            
        Returns:
            Validated and formatted diary entry
            
        Raises:
            ValidationError: If entry cannot be validated
        """
        # First pass validation
        validation_errors = self.entry_validator.get_validation_errors(entry)
        
        # Apply formatting corrections
        formatted_entry = self._apply_formatting_corrections(entry)
        
        # Second pass validation after formatting
        final_validation_errors = self.entry_validator.get_validation_errors(formatted_entry)
        
        if final_validation_errors:
            self.generation_stats["validation_failures"] += 1
            raise ValueError(f"Diary entry validation failed: {final_validation_errors}")
        
        # Track if formatting corrections were applied
        if validation_errors:
            self.generation_stats["formatting_corrections"] += 1
        
        return formatted_entry
    
    def _apply_formatting_corrections(self, entry: DiaryEntry) -> DiaryEntry:
        """
        Apply formatting corrections to ensure compliance with specifications.
        
        Args:
            entry: Original diary entry
            
        Returns:
            Corrected diary entry
        """
        # Format title (max 6 characters)
        formatted_title = self._format_title(entry.title)
        
        # Format content (max 35 characters, emoji support)
        formatted_content = self._format_content(entry.content)
        
        # Validate and format emotional tags
        formatted_emotion_tags = self._format_emotion_tags(entry.emotion_tags)
        
        # Generate proper entry ID if missing or invalid
        formatted_entry_id = self._format_entry_id(entry)
        
        # Create corrected entry
        corrected_entry = DiaryEntry(
            entry_id=formatted_entry_id,
            user_id=entry.user_id,
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            event_name=entry.event_name,
            title=formatted_title,
            content=formatted_content,
            emotion_tags=formatted_emotion_tags,
            agent_type=entry.agent_type,
            llm_provider=entry.llm_provider
        )
        
        return corrected_entry
    
    def _format_title(self, title: str) -> str:
        """
        Format title to comply with 6-character limit.
        
        Args:
            title: Original title
            
        Returns:
            Formatted title (max 6 characters)
        """
        if not title:
            return "日记"
        
        # Handle Chinese characters and emojis properly
        formatted_title = title.strip()
        
        # Truncate to 6 characters, considering Chinese characters
        if len(formatted_title) <= 6:
            return formatted_title
        
        # Smart truncation - try to keep meaningful content
        if len(formatted_title) > 6:
            # If it's mostly Chinese, truncate at 5 chars and add ellipsis
            return formatted_title[:5] + "…"
        
        return formatted_title[:6]
    
    def _format_content(self, content: str) -> str:
        """
        Format content to comply with 35-character limit and emoji support.
        
        Args:
            content: Original content
            
        Returns:
            Formatted content (max 35 characters, emoji allowed)
        """
        if not content:
            return "今天发生了一些事情"
        
        # Clean up content
        formatted_content = content.strip()
        formatted_content = self.content_validator.sanitize_content(formatted_content)
        
        # Ensure length compliance
        if len(formatted_content) <= 35:
            return formatted_content
        
        # Smart truncation preserving emojis and meaning
        if self.content_validator.contains_emoji(formatted_content):
            # Try to preserve emojis at the end
            truncated = formatted_content[:32]
            if formatted_content[32:35]:
                # Check if there are emojis in the remaining part
                remaining = formatted_content[32:35]
                if self.content_validator.contains_emoji(remaining):
                    return truncated + remaining
            return truncated + "..."
        else:
            return formatted_content[:32] + "..."
    
    def _format_emotion_tags(self, emotion_tags: List[EmotionalTag]) -> List[EmotionalTag]:
        """
        Format and validate emotional tags.
        
        Args:
            emotion_tags: Original emotion tags
            
        Returns:
            Validated emotion tags (at least one tag)
        """
        if not emotion_tags:
            return [EmotionalTag.CALM]
        
        # Ensure all tags are valid EmotionalTag enums
        valid_tags = []
        for tag in emotion_tags:
            if isinstance(tag, EmotionalTag):
                valid_tags.append(tag)
            elif isinstance(tag, str):
                # Try to convert string to EmotionalTag
                for enum_tag in EmotionalTag:
                    if enum_tag.value == tag:
                        valid_tags.append(enum_tag)
                        break
        
        # Ensure at least one valid tag
        if not valid_tags:
            valid_tags = [EmotionalTag.CALM]
        
        # Limit to maximum 3 tags for clarity
        return valid_tags[:3]
    
    def _format_entry_id(self, entry: DiaryEntry) -> str:
        """
        Generate or format entry ID.
        
        Args:
            entry: Diary entry
            
        Returns:
            Formatted entry ID
        """
        if entry.entry_id and len(entry.entry_id) > 0:
            return entry.entry_id
        
        # Generate new entry ID
        timestamp_str = entry.timestamp.strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"diary_{entry.user_id}_{timestamp_str}_{entry.event_type}_{unique_id}"
    
    def _can_generate_diary(self, event_data: EventData) -> bool:
        """
        Check if diary can be generated based on daily quota and rules.
        
        Args:
            event_data: Event data
            
        Returns:
            True if diary can be generated
        """
        date_str = event_data.timestamp.strftime("%Y-%m-%d")
        
        # Get or create daily quota for this date
        if date_str not in self.daily_quotas:
            # This should be set by daily scheduler, but create default if missing
            self.daily_quotas[date_str] = DailyQuota(
                date=event_data.timestamp.date(),
                total_quota=3  # Default quota
            )
        
        daily_quota = self.daily_quotas[date_str]
        
        # Check if we can generate diary for this event type
        return daily_quota.can_generate_diary(event_data.event_type)
    
    def _update_daily_quota(self, event_data: EventData):
        """
        Update daily quota after generating a diary entry.
        
        Args:
            event_data: Event data for the generated diary
        """
        date_str = event_data.timestamp.strftime("%Y-%m-%d")
        if date_str in self.daily_quotas:
            self.daily_quotas[date_str].add_diary_entry(event_data.event_type)
    
    async def _store_diary_entry(self, entry: DiaryEntry):
        """
        Store diary entry to file system.
        
        Args:
            entry: Diary entry to store
        """
        try:
            # Create user directory
            user_dir = self.storage_path / f"user_{entry.user_id}"
            user_dir.mkdir(exist_ok=True)
            
            # Create date-based file
            date_str = entry.timestamp.strftime("%Y-%m-%d")
            file_path = user_dir / f"diary_{date_str}.json"
            
            # Load existing entries for the day
            entries = []
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
            
            # Add new entry
            entry_dict = self.formatter.format_diary_entry_for_storage(entry)
            entries.append(entry_dict)
            
            # Save updated entries
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to store diary entry {entry.entry_id}: {str(e)}")
    
    def set_daily_quota(self, date_param: datetime, quota: int):
        """
        Set daily diary generation quota.
        
        Args:
            date_param: Date for the quota
            quota: Number of diary entries allowed (0-5)
        """
        date_str = date_param.strftime("%Y-%m-%d")
        self.daily_quotas[date_str] = DailyQuota(
            date=date_param.date() if hasattr(date_param, 'hour') else date_param,
            total_quota=max(0, min(5, quota))  # Ensure quota is between 0-5
        )
    
    def get_daily_quota(self, date: datetime) -> Optional[DailyQuota]:
        """
        Get daily quota for a specific date.
        
        Args:
            date: Date to check
            
        Returns:
            DailyQuota or None if not set
        """
        date_str = date.strftime("%Y-%m-%d")
        return self.daily_quotas.get(date_str)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get diary generation statistics.
        
        Returns:
            Dictionary with generation statistics
        """
        return self.generation_stats.copy()
    
    def reset_generation_stats(self):
        """Reset generation statistics."""
        self.generation_stats = {
            "total_generated": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "validation_failures": 0,
            "formatting_corrections": 0
        }
    
    async def load_diary_entries(self, 
                               user_id: int, 
                               date: Optional[datetime] = None) -> List[DiaryEntry]:
        """
        Load diary entries for a user and date.
        
        Args:
            user_id: User ID
            date: Specific date (if None, loads all entries)
            
        Returns:
            List of diary entries
        """
        entries = []
        user_dir = self.storage_path / f"user_{user_id}"
        
        if not user_dir.exists():
            return entries
        
        if date:
            # Load entries for specific date
            date_str = date.strftime("%Y-%m-%d")
            file_path = user_dir / f"diary_{date_str}.json"
            if file_path.exists():
                entries.extend(self._load_entries_from_file(file_path))
        else:
            # Load all entries
            for file_path in user_dir.glob("diary_*.json"):
                entries.extend(self._load_entries_from_file(file_path))
        
        return entries
    
    def _load_entries_from_file(self, file_path: Path) -> List[DiaryEntry]:
        """
        Load diary entries from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of diary entries
        """
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                entries_data = json.load(f)
            
            for entry_dict in entries_data:
                # Convert back to DiaryEntry object
                emotion_tags = []
                for tag_str in entry_dict.get("emotion_tags", []):
                    for tag in EmotionalTag:
                        if tag.value == tag_str:
                            emotion_tags.append(tag)
                            break
                
                entry = DiaryEntry(
                    entry_id=entry_dict["entry_id"],
                    user_id=entry_dict["user_id"],
                    timestamp=datetime.fromisoformat(entry_dict["timestamp"]),
                    event_type=entry_dict["event_type"],
                    event_name=entry_dict["event_name"],
                    title=entry_dict["title"],
                    content=entry_dict["content"],
                    emotion_tags=emotion_tags,
                    agent_type=entry_dict["agent_type"],
                    llm_provider=entry_dict["llm_provider"]
                )
                entries.append(entry)
                
        except Exception as e:
            print(f"Failed to load entries from {file_path}: {str(e)}")
        
        return entries


class EmotionalContextProcessor:
    """
    Processor for handling emotional context in diary generation.
    """
    
    def __init__(self):
        self.emotion_mappings = self._initialize_emotion_mappings()
    
    def _initialize_emotion_mappings(self) -> Dict[str, List[EmotionalTag]]:
        """
        Initialize emotion mappings for different event types and contexts.
        
        Returns:
            Dictionary mapping contexts to appropriate emotions
        """
        return {
            "positive_weather": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM, EmotionalTag.EXCITED_THRILLED],
            "negative_weather": [EmotionalTag.SAD_UPSET, EmotionalTag.WORRIED, EmotionalTag.ANXIOUS_MELANCHOLY],
            "social_positive": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED, EmotionalTag.CURIOUS],
            "social_negative": [EmotionalTag.SAD_UPSET, EmotionalTag.ANGRY_FURIOUS, EmotionalTag.WORRIED],
            "celebration": [EmotionalTag.EXCITED_THRILLED, EmotionalTag.HAPPY_JOYFUL],
            "disaster": [EmotionalTag.WORRIED, EmotionalTag.SAD_UPSET, EmotionalTag.SURPRISED_SHOCKED],
            "interaction_positive": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED],
            "interaction_negative": [EmotionalTag.ANGRY_FURIOUS, EmotionalTag.SAD_UPSET],
            "neglect": [EmotionalTag.SAD_UPSET, EmotionalTag.ANXIOUS_MELANCHOLY, EmotionalTag.WORRIED],
            "neutral": [EmotionalTag.CALM, EmotionalTag.CURIOUS]
        }
    
    def process_emotional_context(self, 
                                context_data: DiaryContextData, 
                                event_data: EventData) -> List[EmotionalTag]:
        """
        Process emotional context and suggest appropriate emotional tags.
        
        Args:
            context_data: Context data from existing modules
            event_data: Event data
            
        Returns:
            List of suggested emotional tags
        """
        # Analyze event type and context to suggest emotions
        event_name = event_data.event_name
        
        # Map event names to emotional contexts
        if "favorite" in event_name or "liked" in event_name:
            context_key = "positive_weather" if "weather" in event_name or "season" in event_name else "social_positive"
        elif "dislike" in event_name or "disliked" in event_name:
            context_key = "negative_weather" if "weather" in event_name or "season" in event_name else "social_negative"
        elif "celebration" in event_name:
            context_key = "celebration"
        elif "disaster" in event_name:
            context_key = "disaster"
        elif "neglect" in event_name:
            context_key = "neglect"
        elif "interaction" in event_name:
            context_key = "interaction_positive" if "liked" in event_name else "interaction_negative"
        else:
            context_key = "neutral"
        
        # Get suggested emotions
        suggested_emotions = self.emotion_mappings.get(context_key, [EmotionalTag.CALM])
        
        # Return 1-2 random emotions from suggestions
        import random
        num_emotions = random.randint(1, min(2, len(suggested_emotions)))
        return random.sample(suggested_emotions, num_emotions)
    
    def validate_emotional_consistency(self, 
                                     emotion_tags: List[EmotionalTag], 
                                     event_context: str) -> bool:
        """
        Validate that emotional tags are consistent with event context.
        
        Args:
            emotion_tags: Selected emotional tags
            event_context: Event context description
            
        Returns:
            True if emotions are consistent with context
        """
        # Define conflicting emotion pairs
        conflicting_pairs = [
            (EmotionalTag.HAPPY_JOYFUL, EmotionalTag.SAD_UPSET),
            (EmotionalTag.EXCITED_THRILLED, EmotionalTag.ANXIOUS_MELANCHOLY),
            (EmotionalTag.CALM, EmotionalTag.ANGRY_FURIOUS),
            (EmotionalTag.CURIOUS, EmotionalTag.CONFUSED_ASHAMED)
        ]
        
        # Check for conflicting emotions
        for tag1, tag2 in conflicting_pairs:
            if tag1 in emotion_tags and tag2 in emotion_tags:
                return False
        
        return True


class ChineseTextProcessor:
    """
    Processor for handling Chinese text formatting and validation.
    """
    
    @staticmethod
    def count_chinese_characters(text: str) -> int:
        """
        Count Chinese characters in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Number of Chinese characters
        """
        chinese_count = 0
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # Chinese character range
                chinese_count += 1
        return chinese_count
    
    @staticmethod
    def is_valid_chinese_diary_content(text: str) -> bool:
        """
        Validate if text is appropriate for Chinese diary content.
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid Chinese diary content
        """
        # Check if text contains Chinese characters
        chinese_count = ChineseTextProcessor.count_chinese_characters(text)
        
        # Should have at least some Chinese characters for diary content
        return chinese_count > 0 and len(text.strip()) > 0
    
    @staticmethod
    def format_chinese_diary_text(text: str, max_length: int) -> str:
        """
        Format Chinese text for diary entries.
        
        Args:
            text: Text to format
            max_length: Maximum length allowed
            
        Returns:
            Formatted text
        """
        # Clean up text
        formatted_text = text.strip()
        
        # Remove excessive punctuation
        import re
        formatted_text = re.sub(r'[。！？]{2,}', '。', formatted_text)
        formatted_text = re.sub(r'[，、]{2,}', '，', formatted_text)
        
        # Ensure proper length
        if len(formatted_text) <= max_length:
            return formatted_text
        
        # Text exceeds limit, need to truncate
        # Smart truncation for Chinese text
        truncated = formatted_text[:max_length-1]
        
        # Try to end at a natural break point
        for i in range(len(truncated)-1, max(0, len(truncated)-5), -1):
            if truncated[i] in '。！？，、':
                # Found natural break point, but still add ellipsis since original was longer
                natural_break = truncated[:i+1]
                if len(natural_break) + 1 <= max_length:
                    return natural_break + "…"
                else:
                    return natural_break
        
        # If no natural break point, add ellipsis
        return truncated + "…"