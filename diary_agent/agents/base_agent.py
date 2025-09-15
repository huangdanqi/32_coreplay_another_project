"""
Base agent architecture for diary generation sub-agents.
Provides common interface and functionality for all specialized sub-agents.
Enhanced with comprehensive error handling and logging.
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from diary_agent.utils.data_models import (
    EventData, DiaryEntry, DiaryContextData, PromptConfig, 
    EmotionalTag, DataReader
)
from diary_agent.core.llm_manager import LLMConfigManager, LLMProviderError
from diary_agent.utils.validators import DiaryEntryValidator
from diary_agent.utils.formatters import DiaryEntryFormatter
from diary_agent.utils.error_handler import (
    ErrorHandler, ErrorCategory, ErrorContext, with_error_handling, global_error_handler
)
from diary_agent.utils.logger import get_component_logger, diary_logger
from diary_agent.utils.graceful_degradation import with_graceful_degradation


class BaseSubAgent(ABC):
    """
    Abstract base class for all diary generation sub-agents.
    Provides common interface and functionality.
    """
    
    def __init__(self, 
                 agent_type: str,
                 prompt_config: PromptConfig,
                 llm_manager: LLMConfigManager,
                 data_reader: DataReader):
        """
        Initialize base sub-agent.
        
        Args:
            agent_type: Type identifier for this agent
            prompt_config: Prompt configuration for this agent
            llm_manager: LLM configuration manager
            data_reader: Data reader for accessing existing modules
        """
        self.agent_type = agent_type
        self.prompt_config = prompt_config
        self.llm_manager = llm_manager
        self.data_reader = data_reader
        self.validator = DiaryEntryValidator()
        self.formatter = DiaryEntryFormatter()
        self.logger = get_component_logger(f"agent_{agent_type}")
        self.error_handler = global_error_handler
    
    @abstractmethod
    async def process_event(self, event_data: EventData) -> DiaryEntry:
        """
        Process an event and generate a diary entry.
        
        Args:
            event_data: Event data to process
            
        Returns:
            Generated diary entry
            
        Raises:
            LLMProviderError: If LLM generation fails
            ValidationError: If generated entry is invalid
        """
        pass
    
    @abstractmethod
    def get_supported_events(self) -> List[str]:
        """
        Get list of event names this agent supports.
        
        Returns:
            List of supported event names
        """
        pass    
    
    def get_agent_type(self) -> str:
        """Get the agent type identifier."""
        return self.agent_type
    
    def get_data_reader(self) -> DataReader:
        """Get the data reader instance."""
        return self.data_reader
    
    async def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read event context from existing modules via data reader.
        
        Args:
            event_data: Event data to read context for
            
        Returns:
            Context data for diary generation
        """
        try:
            return self.data_reader.read_event_context(event_data)
        except Exception as e:
            # Return minimal context if reading fails
            return DiaryContextData(
                user_profile={},
                event_details={"event_name": event_data.event_name},
                environmental_context={},
                social_context={},
                emotional_context={},
                temporal_context={"timestamp": event_data.timestamp}
            )
    
    @with_graceful_degradation("sub_agent")
    async def generate_diary_content(self, 
                                   event_data: EventData, 
                                   context_data: DiaryContextData) -> Dict[str, Any]:
        """
        Generate diary content using LLM.
        
        Args:
            event_data: Event data
            context_data: Context data from existing modules
            
        Returns:
            Generated content dictionary with title, content, and emotion_tags
            
        Raises:
            LLMProviderError: If LLM generation fails
        """
        start_time = datetime.now()
        
        self.logger.info(f"Starting diary content generation for event: {event_data.event_name}")
        
        # Prepare prompt with context
        user_prompt = self._prepare_user_prompt(event_data, context_data)
        
        # Use custom system prompt if available, otherwise use default (no auto appends)
        system_prompt = self.prompt_config.system_prompt
        
        try:
            # Generate content using LLM with failover
            generated_text = await self.llm_manager.generate_text_with_failover(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            # Debug: Log the generated text
            self.logger.info(f"LLM generated text: {generated_text[:200]}...")
            
            # Parse generated content
            content_dict = await self._parse_generated_content(generated_text)
            
            # Debug: Log the parsed content
            self.logger.info(f"Parsed content: {content_dict}")
            
            # Log successful generation
            duration = (datetime.now() - start_time).total_seconds()
            diary_logger.log_performance_metrics(
                component=f"agent_{self.agent_type}",
                operation="generate_diary_content",
                duration=duration,
                metadata={
                    "event_name": event_data.event_name,
                    "content_length": len(content_dict.get("content", "")),
                    "title_length": len(content_dict.get("title", ""))
                }
            )
            
            self.logger.info(f"Successfully generated diary content for {event_data.event_name}")
            return content_dict
            
        except Exception as e:
            # Handle error with error handler
            error_context = ErrorContext(
                error_category=ErrorCategory.SUB_AGENT_FAILURE,
                error_message=str(e),
                component_name=f"agent_{self.agent_type}",
                timestamp=datetime.now(),
                metadata={
                    "event_name": event_data.event_name,
                    "event_type": event_data.event_type,
                    "user_id": event_data.user_id
                }
            )
            
            recovery_result = self.error_handler.handle_error(e, error_context)
            
            if recovery_result.get("fallback_agent"):
                self.logger.warning(f"Using fallback for {self.agent_type} due to error: {str(e)}")
                # Return a simple fallback diary entry
                return {
                    "title": "记录",
                    "content": f"今天发生了{event_data.event_name}相关的事情。",
                    "emotion_tags": ["平静"],
                    "source": "fallback"
                }
            
            raise LLMProviderError(f"Failed to generate diary content for {self.agent_type}: {str(e)}")
    
    def _prepare_user_prompt(self, event_data: EventData, context_data: DiaryContextData) -> str:
        """
        Prepare user prompt by filling template with event and context data.
        
        Args:
            event_data: Event data
            context_data: Context data
            
        Returns:
            Formatted user prompt
        """
        template_vars = {
            "event_name": event_data.event_name,
            "event_type": event_data.event_type,
            "timestamp": event_data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": event_data.user_id,
            "user_profile": context_data.user_profile,
            "event_details": context_data.event_details,
            "environmental_context": context_data.environmental_context,
            "social_context": context_data.social_context,
            "emotional_context": context_data.emotional_context,
            "temporal_context": context_data.temporal_context
        }
        
        try:
            # Provide richer template variables to encourage specificity
            enriched_vars = {
                **template_vars,
                "now_date": datetime.now().strftime("%Y年%m月%d日"),
                "now_time": datetime.now().strftime("%H:%M"),
            }
            return self.prompt_config.user_prompt_template.format(**enriched_vars)
        except KeyError as e:
            # If template variable is missing, use a simpler format
            return f"Generate a diary entry for event: {event_data.event_name} at {event_data.timestamp}"    
    
    async def _parse_generated_content(self, generated_text: str) -> Dict[str, Any]:
        """
        Parse generated content from LLM response.
        
        Args:
            generated_text: Raw text from LLM
            
        Returns:
            Parsed content dictionary
        """
        try:
            # Try to parse as JSON first
            content_dict = json.loads(generated_text)
            
            # Validate required fields
            if not all(key in content_dict for key in ["title", "content", "emotion_tags"]):
                raise ValueError("Missing required fields in generated content")
            
            return content_dict
            
        except (json.JSONDecodeError, ValueError):
            # Fallback: extract content using simple parsing
            return await self._fallback_parse_content(generated_text)
    
    async def _fallback_parse_content(self, generated_text: str) -> Dict[str, Any]:
        """
        Fallback parsing when JSON parsing fails.
        
        Args:
            generated_text: Raw text from LLM
            
        Returns:
            Parsed content dictionary
        """
        # Clean the text first
        cleaned_text = generated_text.strip()
        
        # Try to extract JSON-like structure
        if '"title"' in cleaned_text and '"content"' in cleaned_text:
            try:
                # Extract JSON part if it exists
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_part = cleaned_text[start_idx:end_idx]
                    return json.loads(json_part)
            except:
                pass
        
        # Fallback to line-based parsing
        lines = cleaned_text.split('\n')
        
        # Extract title: prefer a line starting with "标题" or the first short non-empty line
        title = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('标题'):
                # Accept formats like "标题：xxxx" or "标题: xxxx"
                sep_idx = max(line.find('：'), line.find(':'))
                title = line[sep_idx+1:].strip() if sep_idx != -1 else line.replace('标题', '').strip()
                break
            if len(line) < 50 and not line.startswith('日记') and not line.startswith('今天') and not line.startswith('与'):
                title = line
                break
        
        # If no title found, use LLM to generate a title from content
        if not title:
            try:
                # Use LLM to generate a title from the content
                title_prompt = f"请为以下日记内容生成一个简洁的标题（不超过10个字）：\n{cleaned_text[:200]}..."
                title_response = await self.llm_manager.generate_text_with_failover(
                    prompt=title_prompt,
                    system_prompt="你是一个专业的标题生成助手。请根据日记内容生成简洁、有吸引力的中文标题。"
                )
                # Clean the title response
                title = title_response.strip().replace('"', '').replace("'", '').replace('\n', ' ').strip()
                # Limit title length
                if len(title) > 15:
                    title = title[:15] + "..."
                if not title:
                    title = "美好时光"
            except Exception as e:
                self.logger.warning(f"Failed to generate title with LLM: {e}")
                title = "美好时光"
        
        # Extract content (all text, but clean it up)
        content = cleaned_text
        
        # Try to extract emotion tags from content
        emotion_tags = []
        
        # Look for Chinese emotion words in the content
        chinese_emotions = {
            '开心': EmotionalTag.HAPPY_JOYFUL.value,
            '快乐': EmotionalTag.HAPPY_JOYFUL.value,
            '兴奋': EmotionalTag.EXCITED_THRILLED.value,
            '激动': EmotionalTag.EXCITED_THRILLED.value,
            '满足': EmotionalTag.HAPPY_JOYFUL.value,
            '平静': EmotionalTag.CALM.value,
            '温馨': EmotionalTag.CALM.value,
            '美好': EmotionalTag.HAPPY_JOYFUL.value,
            '幸福': EmotionalTag.HAPPY_JOYFUL.value,
            '愉快': EmotionalTag.HAPPY_JOYFUL.value
        }
        
        for emotion_word, emotion_tag in chinese_emotions.items():
            if emotion_word in content:
                emotion_tags.append(emotion_tag)
                break
        
        # Default to Chinese emotion tag if none found
        if not emotion_tags:
            emotion_tags = [EmotionalTag.HAPPY_JOYFUL.value]  # Use Chinese "开心快乐"
        
        return {
            "title": title,
            "content": content,
            "emotion_tags": emotion_tags
        }
    
    def validate_output(self, entry: DiaryEntry) -> bool:
        """
        Validate generated diary entry.
        
        Args:
            entry: Diary entry to validate
            
        Returns:
            True if valid, False otherwise
        """
        return self.validator.validate_diary_entry(entry)
    
    def format_output(self, entry: DiaryEntry) -> DiaryEntry:
        """
        Return entry as-is to preserve exact LLM output for title/content.
        """
        return entry
    
    async def _create_diary_entry(self, 
                                event_data: EventData, 
                                content_dict: Dict[str, Any]) -> DiaryEntry:
        """
        Create DiaryEntry object from generated content.
        
        Args:
            event_data: Original event data
            content_dict: Generated content dictionary
            
        Returns:
            DiaryEntry object
        """
        # Convert emotion tag strings to EmotionalTag enums
        emotion_tags = []
        for tag_str in content_dict.get("emotion_tags", []):
            for tag in EmotionalTag:
                if tag.value == tag_str:
                    emotion_tags.append(tag)
                    break
        
        # Default to CALM if no valid tags found
        if not emotion_tags:
            emotion_tags = [EmotionalTag.CALM]
        
        # Get current provider name
        current_provider = self.llm_manager.get_current_provider()
        provider_name = current_provider.provider_name if current_provider else "unknown"
        
        # Create diary entry
        entry = DiaryEntry(
            entry_id=f"{event_data.user_id}_{event_data.event_id}_{int(event_data.timestamp.timestamp())}",
            user_id=event_data.user_id,
            timestamp=event_data.timestamp,
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            title=content_dict["title"],  # Use full title from LLM
            content=content_dict["content"],  # Use full content from LLM
            emotion_tags=emotion_tags,
            agent_type=self.agent_type,
            llm_provider=provider_name
        )
        
        return entry


class AgentRegistry:
    """Registry for managing sub-agent instances."""
    
    def __init__(self):
        self._agents: Dict[str, BaseSubAgent] = {}
        self._event_mappings: Dict[str, str] = {}  # event_name -> agent_type
    
    def register_agent(self, agent: BaseSubAgent):
        """
        Register a sub-agent.
        
        Args:
            agent: Sub-agent instance to register
        """
        agent_type = agent.get_agent_type()
        self._agents[agent_type] = agent
        
        # Register event mappings
        for event_name in agent.get_supported_events():
            self._event_mappings[event_name] = agent_type
    
    def get_agent(self, agent_type: str) -> Optional[BaseSubAgent]:
        """
        Get agent by type.
        
        Args:
            agent_type: Agent type identifier
            
        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_type)
    
    def get_agent_for_event(self, event_name: str) -> Optional[BaseSubAgent]:
        """
        Get agent that handles a specific event.
        
        Args:
            event_name: Event name
            
        Returns:
            Agent instance or None if no agent handles this event
        """
        agent_type = self._event_mappings.get(event_name)
        if agent_type:
            return self._agents.get(agent_type)
        return None
    
    def list_agents(self) -> List[str]:
        """Get list of registered agent types."""
        return list(self._agents.keys())
    
    def list_supported_events(self) -> List[str]:
        """Get list of all supported event names."""
        return list(self._event_mappings.keys())
    
    def get_event_mappings(self) -> Dict[str, str]:
        """Get event name to agent type mappings."""
        return self._event_mappings.copy()

class AgentFactory:
    """Factory for creating sub-agent instances."""
    
    def __init__(self, 
                 llm_manager: LLMConfigManager,
                 prompt_config_dir: str = "diary_agent/config/agent_prompts"):
        self.llm_manager = llm_manager
        self.prompt_config_dir = Path(prompt_config_dir)
        self._prompt_configs: Dict[str, PromptConfig] = {}
        self._load_prompt_configurations()
    
    def _load_prompt_configurations(self):
        """Load prompt configurations for all agent types."""
        if not self.prompt_config_dir.exists():
            self.prompt_config_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_prompt_configs()
        
        # Load existing prompt configurations
        for config_file in self.prompt_config_dir.glob("*.json"):
            agent_type = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                prompt_config = PromptConfig(**config_data)
                self._prompt_configs[agent_type] = prompt_config
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to load prompt config for {agent_type}: {str(e)}")
    
    def _create_default_prompt_configs(self):
        """Create default prompt configuration files."""
        default_configs = {
            "weather_agent": {
                "agent_type": "weather_agent",
                "system_prompt": "You are a diary writing assistant specializing in weather-related entries. Generate authentic, emotional diary entries about weather experiences.",
                "user_prompt_template": "Write a diary entry about {event_name} on {timestamp}. User profile: {user_profile}. Weather context: {environmental_context}. Format as JSON with title, content, and emotion_tags. Make the content natural and complete.",
                "output_format": {"title": "string", "content": "string", "emotion_tags": "list"},
                "validation_rules": {}
            },
            "trending_agent": {
                "agent_type": "trending_agent",
                "system_prompt": "You are a diary writing assistant specializing in trending news and social events. Generate relevant diary entries about current events.",
                "user_prompt_template": "Write a diary entry about {event_name} on {timestamp}. User profile: {user_profile}. Social context: {social_context}. Format as JSON with title, content, and emotion_tags. Make the content natural and complete.",
                "output_format": {"title": "string", "content": "string", "emotion_tags": "list"},
                "validation_rules": {}
            }
        }
        
        for agent_type, config_data in default_configs.items():
            config_file = self.prompt_config_dir / f"{agent_type}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def get_prompt_config(self, agent_type: str) -> Optional[PromptConfig]:
        """
        Get prompt configuration for an agent type.
        
        Args:
            agent_type: Agent type identifier
            
        Returns:
            PromptConfig or None if not found
        """
        return self._prompt_configs.get(agent_type)
    
    def create_agent(self, 
                    agent_type: str, 
                    agent_class: type, 
                    data_reader: DataReader) -> Optional[BaseSubAgent]:
        """
        Create a sub-agent instance.
        
        Args:
            agent_type: Agent type identifier
            agent_class: Agent class to instantiate
            data_reader: Data reader for the agent
            
        Returns:
            Agent instance or None if creation fails
        """
        prompt_config = self.get_prompt_config(agent_type)
        if not prompt_config:
            print(f"No prompt configuration found for agent type: {agent_type}")
            return None
        
        try:
            agent = agent_class(
                agent_type=agent_type,
                prompt_config=prompt_config,
                llm_manager=self.llm_manager,
                data_reader=data_reader
            )
            return agent
            
        except Exception as e:
            print(f"Failed to create agent {agent_type}: {str(e)}")
            return None
    
    def reload_prompt_configurations(self):
        """Reload prompt configurations from files."""
        self._prompt_configs.clear()
        self._load_prompt_configurations()
        print("Prompt configurations reloaded")
    
    def list_available_configs(self) -> List[str]:
        """Get list of available prompt configurations."""
        return list(self._prompt_configs.keys())