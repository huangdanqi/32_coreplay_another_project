"""
Core data models for the diary agent system.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from enum import Enum


class EmotionalTag(Enum):
    """Predefined emotional tags for diary entries."""
    ANGRY_FURIOUS = "生气愤怒"      # Angry/Furious
    SAD_UPSET = "悲伤难过"          # Sad/Upset  
    WORRIED = "担忧"               # Worried
    ANXIOUS_MELANCHOLY = "焦虑忧愁"  # Anxious/Melancholy
    SURPRISED_SHOCKED = "惊讶震惊"   # Surprised/Shocked
    CURIOUS = "好奇"               # Curious
    CONFUSED_ASHAMED = "羞愧"       # Confused/Ashamed
    CALM = "平静"                  # Calm
    HAPPY_JOYFUL = "开心快乐"       # Happy/Joyful
    EXCITED_THRILLED = "兴奋激动"    # Excited/Thrilled


@dataclass
class EventData:
    """Event data structure for diary generation."""
    event_id: str
    event_type: str  # Maps to sub-agent types from events.json
    event_name: str  # Specific event name (e.g., "favorite_weather", "made_new_friend")
    timestamp: datetime
    user_id: int  # User associated with the event
    context_data: Dict[str, Any]  # Event context read from existing modules
    metadata: Dict[str, Any]  # Additional diary generation context


@dataclass
class DiaryContextData:
    """Context data read from existing modules for diary generation."""
    user_profile: Dict[str, Any]  # User preferences, role, etc.
    event_details: Dict[str, Any]  # Specific event information
    environmental_context: Dict[str, Any]  # Weather, time, location context
    social_context: Dict[str, Any]  # Friend interactions, relationships
    emotional_context: Dict[str, Any]  # Current emotional state indicators
    temporal_context: Dict[str, Any]  # Time-based information (holidays, seasons, etc.)


@dataclass
class DiaryEntry:
    """Diary entry structure."""
    entry_id: str
    user_id: int
    timestamp: datetime
    event_type: str
    event_name: str
    title: str  # Diary entry title
    content: str  # Diary entry content, emoji allowed
    emotion_tags: List[EmotionalTag]  # Selected from predefined emotions
    agent_type: str
    llm_provider: str


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider_name: str  # "qwen", "deepseek", "ollama_qwen3", etc.
    api_endpoint: str
    api_key: str
    model_name: str
    max_tokens: int = 150
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    provider_type: str = "cloud"  # "cloud", "ollama", "local"
    enabled: bool = True
    priority: int = 999
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["general"]


@dataclass
class PromptConfig:
    """Prompt configuration for sub-agents."""
    agent_type: str
    system_prompt: str
    user_prompt_template: str
    output_format: Dict[str, Any]
    validation_rules: Dict[str, Any]


@dataclass
class DatabaseConfig:
    """Database configuration matching existing system."""
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = "h05010501"
    database: str = "page_test"


class DataReader:
    """Base interface for reading data from existing modules."""
    
    def __init__(self, module_name: str, read_only: bool = True):
        self.module_name = module_name
        self.read_only = read_only
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """Read event context from existing modules."""
        raise NotImplementedError("Subclasses must implement read_event_context")
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences for diary context."""
        raise NotImplementedError("Subclasses must implement get_user_preferences")


@dataclass
class DailyQuota:
    """Daily diary generation quota."""
    date: date
    total_quota: int  # 0-5 randomly determined at 00:00
    current_count: int = 0
    completed_event_types: List[str] = None
    
    def __post_init__(self):
        if self.completed_event_types is None:
            self.completed_event_types = []
    
    def can_generate_diary(self, event_type: str) -> bool:
        """Check if diary can be generated for this event type."""
        return (self.current_count < self.total_quota and 
                event_type not in self.completed_event_types)
    
    def add_diary_entry(self, event_type: str):
        """Record a diary entry generation."""
        if event_type not in self.completed_event_types:
            self.completed_event_types.append(event_type)
            self.current_count += 1


@dataclass
class ClaimedEvent:
    """Events that must always result in diary entries."""
    event_type: str
    event_name: str
    is_claimed: bool = True