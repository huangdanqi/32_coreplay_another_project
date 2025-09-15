"""
Validation utilities for diary agent system.
"""

import re
from typing import List, Dict, Any
from .data_models import DiaryEntry, EventData, EmotionalTag, LLMConfig, PromptConfig


class DiaryEntryValidator:
    """Validator for diary entries (relaxed to preserve LLM output)."""
    
    MAX_TITLE_LENGTH = 1000
    MAX_CONTENT_LENGTH = 10000
    
    def validate_diary_entry(self, entry: DiaryEntry) -> bool:
        """Validate a diary entry and return True if valid (no strict length limits)."""
        errors = self.get_validation_errors(entry)
        return len(errors) == 0
    
    def get_validation_errors(self, entry: DiaryEntry) -> List[str]:
        """Validate a diary entry and return list of errors."""
        errors = []
        
        # Length checks disabled for API output; keep only presence checks
        if entry.title is None:
            errors.append("Title is required")
        if entry.content is None:
            errors.append("Content is required")
        
        # Validate emotional tags
        if not entry.emotion_tags:
            errors.append("At least one emotional tag is required")
        
        for tag in entry.emotion_tags:
            if not isinstance(tag, EmotionalTag):
                errors.append(f"Invalid emotional tag: {tag}")
        
        # Validate required fields
        if not entry.entry_id:
            errors.append("Entry ID is required")
        
        if not entry.user_id:
            errors.append("User ID is required")
        
        if not entry.event_type:
            errors.append("Event type is required")
        
        if not entry.agent_type:
            errors.append("Agent type is required")
        
        return errors
    
    @classmethod
    def is_valid_diary_entry(cls, entry: DiaryEntry) -> bool:
        """Check if diary entry is valid (class method for backward compatibility)."""
        validator = cls()
        return validator.validate_diary_entry(entry)


class EventDataValidator:
    """Validator for event data."""
    
    @classmethod
    def validate_event_data(cls, event_data: EventData) -> List[str]:
        """Validate event data and return list of errors."""
        errors = []
        
        if not event_data.event_id:
            errors.append("Event ID is required")
        
        if not event_data.event_type:
            errors.append("Event type is required")
        
        if not event_data.event_name:
            errors.append("Event name is required")
        
        if not event_data.user_id:
            errors.append("User ID is required")
        
        if not event_data.timestamp:
            errors.append("Timestamp is required")
        
        return errors
    
    @classmethod
    def is_valid_event_data(cls, event_data: EventData) -> bool:
        """Check if event data is valid."""
        return len(cls.validate_event_data(event_data)) == 0


class EventValidator:
    """Validator for event routing and processing."""
    
    def __init__(self):
        self.event_data_validator = EventDataValidator()
    
    def validate_event_data(self, event_data: EventData) -> bool:
        """Validate event data for routing."""
        return self.event_data_validator.is_valid_event_data(event_data)
    
    def validate_event_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate event metadata."""
        errors = []
        
        # Check required metadata fields
        required_fields = ["timestamp", "user_id", "event_type", "event_name"]
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required metadata field: {field}")
        
        return errors
    
    def validate_routing_context(self, event_type: str, agent_type: str) -> bool:
        """Validate routing context."""
        return bool(event_type and agent_type)


class ContentValidator:
    """Validator for diary content formatting."""
    
    @classmethod
    def validate_chinese_text_length(cls, text: str, max_length: int) -> bool:
        """Validate Chinese text length considering character width."""
        # Count Chinese characters and emojis properly
        char_count = 0
        for char in text:
            # Chinese characters, emojis, and wide characters count as 1
            if ord(char) > 127:
                char_count += 1
            else:
                char_count += 1
        
        return char_count <= max_length
    
    @classmethod
    def contains_emoji(cls, text: str) -> bool:
        """Check if text contains emojis."""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return bool(emoji_pattern.search(text))
    
    @classmethod
    def sanitize_content(cls, content: str) -> str:
        """Sanitize content for diary entry."""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Ensure content doesn't exceed length limits
        if len(content) > 35:
            content = content[:32] + "..."
        
        return content


class ConfigValidator:
    """Validator for configuration files and structures"""
    
    # Valid emotional tags
    VALID_EMOTIONS = [
        "生气愤怒",    # Angry/Furious
        "悲伤难过",    # Sad/Upset  
        "担忧",        # Worried
        "焦虑忧愁",    # Anxious/Melancholy
        "惊讶震惊",    # Surprised/Shocked
        "好奇",        # Curious
        "羞愧",        # Confused/Ashamed
        "平静",        # Calm
        "开心快乐",    # Happy/Joyful
        "兴奋激动"     # Excited/Thrilled
    ]
    
    @staticmethod
    def validate_llm_config_structure(config_data: Dict[str, Any]) -> bool:
        """Validate LLM configuration file structure"""
        try:
            # Check top-level structure
            if not isinstance(config_data, dict):
                return False
                
            if "providers" not in config_data:
                return False
                
            providers = config_data["providers"]
            if not isinstance(providers, dict):
                return False
                
            # Validate each provider has required fields
            required_fields = [
                "provider_name", "api_endpoint", "api_key", "model_name",
                "max_tokens", "temperature", "timeout", "retry_attempts"
            ]
            
            for provider_name, provider_config in providers.items():
                if not isinstance(provider_config, dict):
                    return False
                    
                for field in required_fields:
                    if field not in provider_config:
                        return False
                        
            return True
            
        except Exception:
            return False
            
    @staticmethod
    def validate_llm_provider_config(config: LLMConfig) -> bool:
        """Validate individual LLM provider configuration"""
        try:
            # Check required fields
            if not all([config.provider_name, config.api_endpoint, 
                       config.model_name]):
                return False
                
            # Validate URL format
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                
            if not url_pattern.match(config.api_endpoint):
                return False
                
            # Validate numeric fields
            if config.max_tokens <= 0 or config.timeout <= 0 or config.retry_attempts < 0:
                return False
                
            # Validate temperature range
            if not (0.0 <= config.temperature <= 2.0):
                return False
                
            return True
            
        except Exception:
            return False
        
    @staticmethod
    def validate_prompt_config_structure(config_data: Dict[str, Any]) -> bool:
        """Validate prompt configuration file structure"""
        try:
            # Check top-level structure
            if not isinstance(config_data, dict):
                return False
                
            # Required top-level fields
            required_fields = [
                "agent_type", "system_prompt", "user_prompt_template",
                "output_format", "validation_rules"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    return False
                    
            # Validate output_format structure
            output_format = config_data["output_format"]
            if not isinstance(output_format, dict):
                return False
                
            required_output_fields = ["title", "content", "emotion_tags"]
            for field in required_output_fields:
                if field not in output_format:
                    return False
                    
            # Validate validation_rules structure
            validation_rules = config_data["validation_rules"]
            if not isinstance(validation_rules, dict):
                return False
                
            required_validation_fields = [
                "title_max_length", "content_max_length", 
                "required_fields", "emotion_tags_valid"
            ]
            
            for field in required_validation_fields:
                if field not in validation_rules:
                    return False
                    
            # Validate emotion tags
            emotion_tags = validation_rules.get("emotion_tags_valid", [])
            if not isinstance(emotion_tags, list):
                return False
                
            # Check if emotion tags match valid emotions
            for tag in emotion_tags:
                if tag not in ConfigValidator.VALID_EMOTIONS:
                    return False
                    
            return True
            
        except Exception:
            return False
            
    @staticmethod
    def validate_prompt_config(config: PromptConfig) -> bool:
        """Validate individual prompt configuration"""
        try:
            # Check required fields
            if not all([config.agent_type, config.system_prompt, 
                       config.user_prompt_template]):
                return False
                
            # Validate output format
            if not isinstance(config.output_format, dict):
                return False
                
            # Check for required output format fields
            required_output_fields = ["title", "content", "emotion_tags"]
            for field in required_output_fields:
                if field not in config.output_format:
                    return False
                    
            # Validate validation rules
            if not isinstance(config.validation_rules, dict):
                return False
                
            # Check for required validation rules
            required_validation_fields = ["title_max_length", "content_max_length", 
                                        "required_fields", "emotion_tags_valid"]
            for field in required_validation_fields:
                if field not in config.validation_rules:
                    return False
                    
            return True
            
        except Exception:
            return False
        
    @staticmethod
    def validate_condition_config_structure(config_data: Dict[str, Any]) -> bool:
        """Validate condition configuration file structure"""
        try:
            if not isinstance(config_data, dict):
                return False
                
            # Check for required sections
            required_sections = ["time_conditions", "event_conditions", "image_conditions"]
            for section in required_sections:
                if section not in config_data:
                    return False
                    
                if not isinstance(config_data[section], dict):
                    return False
                    
            return True
            
        except Exception:
            return False
            
    @staticmethod
    def validate_json_syntax(file_path: str) -> bool:
        """Validate JSON file syntax"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, FileNotFoundError, IOError):
            return False
            
    @staticmethod
    def validate_file_permissions(file_path: str) -> bool:
        """Validate file read/write permissions"""
        try:
            import os
            return os.access(file_path, os.R_OK | os.W_OK)
        except Exception:
            return False