"""
Configuration Management System for Diary Agent

This module provides comprehensive configuration management including:
- LLM provider configuration loading and validation
- Agent prompt configuration management with hot-reloading
- Configuration file monitoring for dynamic updates
- Error handling and validation
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from threading import Thread, Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

from ..utils.data_models import LLMConfig, PromptConfig
from ..utils.validators import ConfigValidator

logger = logging.getLogger(__name__)


@dataclass
class ConfigChangeEvent:
    """Represents a configuration change event"""
    config_type: str  # 'llm' or 'prompt'
    file_path: str
    change_type: str  # 'modified', 'created', 'deleted'
    timestamp: float
    config_data: Optional[Dict[str, Any]] = None


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes"""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.config_manager._handle_file_change(event.src_path, 'modified')
            
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.config_manager._handle_file_change(event.src_path, 'created')
            
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.config_manager._handle_file_change(event.src_path, 'deleted')


class ConfigManager:
    """
    Comprehensive configuration management system with hot-reloading capabilities
    """
    
    def __init__(self, config_dir: str = "diary_agent/config"):
        self.config_dir = Path(config_dir)
        self.llm_config_file = Path("config") / "llm_configuration.json"
        self.prompts_dir = self.config_dir / "agent_prompts"
        
        # Configuration storage
        self._llm_configs: Dict[str, LLMConfig] = {}
        self._prompt_configs: Dict[str, PromptConfig] = {}
        
        # File monitoring
        self._observer: Optional[Observer] = None
        self._file_handler: Optional[ConfigFileHandler] = None
        self._monitoring_enabled = False
        
        # Change callbacks
        self._change_callbacks: List[Callable[[ConfigChangeEvent], None]] = []
        
        # Thread safety
        self._config_lock = Lock()
        
        # Validation
        self.validator = ConfigValidator()
        
        # Initialize configurations
        self._load_all_configurations()
        
    def start_monitoring(self) -> None:
        """Start file system monitoring for configuration changes"""
        if self._monitoring_enabled:
            logger.warning("Configuration monitoring is already enabled")
            return
            
        try:
            self._observer = Observer()
            self._file_handler = ConfigFileHandler(self)
            
            # Monitor config directory
            self._observer.schedule(
                self._file_handler,
                str(self.config_dir),
                recursive=True
            )
            
            self._observer.start()
            self._monitoring_enabled = True
            logger.info("Configuration file monitoring started")
            
        except Exception as e:
            logger.error(f"Failed to start configuration monitoring: {e}")
            raise
            
    def stop_monitoring(self) -> None:
        """Stop file system monitoring"""
        if not self._monitoring_enabled:
            return
            
        try:
            if self._observer:
                self._observer.stop()
                self._observer.join()
                self._observer = None
                
            self._file_handler = None
            self._monitoring_enabled = False
            logger.info("Configuration file monitoring stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop configuration monitoring: {e}")
            
    def add_change_callback(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """Add a callback function to be called when configuration changes"""
        self._change_callbacks.append(callback)
        
    def remove_change_callback(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """Remove a change callback"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            
    def _handle_file_change(self, file_path: str, change_type: str) -> None:
        """Handle configuration file changes"""
        try:
            file_path = Path(file_path)
            
            # Determine configuration type
            config_type = None
            if file_path.name == "llm_configuration.json":
                config_type = "llm"
            elif file_path.parent.name == "agent_prompts":
                config_type = "prompt"
            else:
                return  # Not a configuration file we care about
                
            # Create change event
            event = ConfigChangeEvent(
                config_type=config_type,
                file_path=str(file_path),
                change_type=change_type,
                timestamp=time.time()
            )
            
            # Reload configuration if modified or created
            if change_type in ['modified', 'created']:
                if config_type == "llm":
                    self._reload_llm_configuration()
                elif config_type == "prompt":
                    agent_name = file_path.stem
                    self._reload_prompt_configuration(agent_name)
                    
            # Handle deletion
            elif change_type == "deleted":
                if config_type == "prompt":
                    agent_name = file_path.stem
                    with self._config_lock:
                        if agent_name in self._prompt_configs:
                            del self._prompt_configs[agent_name]
                            
            # Notify callbacks
            for callback in self._change_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in configuration change callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling configuration file change: {e}")
            
    def _load_all_configurations(self) -> None:
        """Load all configuration files"""
        self._load_llm_configuration()
        self._load_prompt_configurations()
        
    def _load_llm_configuration(self) -> None:
        """Load LLM provider configurations"""
        try:
            if not self.llm_config_file.exists():
                logger.warning(f"LLM configuration file not found: {self.llm_config_file}")
                return
                
            with open(self.llm_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Validate configuration structure
            if not self.validator.validate_llm_config_structure(config_data):
                raise ValueError("Invalid LLM configuration structure")
                
            # Load provider configurations
            with self._config_lock:
                self._llm_configs.clear()
                
                for provider_name, provider_config in config_data.get('providers', {}).items():
                    try:
                        llm_config = LLMConfig(**provider_config)
                        
                        # Validate individual provider config
                        if self.validator.validate_llm_provider_config(llm_config):
                            self._llm_configs[provider_name] = llm_config
                        else:
                            logger.error(f"Invalid configuration for provider: {provider_name}")
                            
                    except Exception as e:
                        logger.error(f"Error loading LLM provider {provider_name}: {e}")
                        
            logger.info(f"Loaded {len(self._llm_configs)} LLM provider configurations")
            
        except Exception as e:
            logger.error(f"Error loading LLM configuration: {e}")
            raise
            
    def _reload_llm_configuration(self) -> None:
        """Reload LLM configuration from file"""
        logger.info("Reloading LLM configuration")
        self._load_llm_configuration()
        
    def _load_prompt_configurations(self) -> None:
        """Load all agent prompt configurations"""
        try:
            if not self.prompts_dir.exists():
                logger.warning(f"Prompts directory not found: {self.prompts_dir}")
                return
                
            with self._config_lock:
                self._prompt_configs.clear()
                
                for prompt_file in self.prompts_dir.glob("*.json"):
                    agent_name = prompt_file.stem
                    self._load_single_prompt_configuration(agent_name, prompt_file)
                    
            logger.info(f"Loaded {len(self._prompt_configs)} prompt configurations")
            
        except Exception as e:
            logger.error(f"Error loading prompt configurations: {e}")
            raise
            
    def _load_single_prompt_configuration(self, agent_name: str, file_path: Path) -> None:
        """Load a single prompt configuration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Validate prompt configuration
            if not self.validator.validate_prompt_config_structure(config_data):
                logger.error(f"Invalid prompt configuration structure: {agent_name}")
                return
                
            prompt_config = PromptConfig(**config_data)
            
            # Additional validation
            if self.validator.validate_prompt_config(prompt_config):
                self._prompt_configs[agent_name] = prompt_config
            else:
                logger.error(f"Invalid prompt configuration: {agent_name}")
                
        except Exception as e:
            logger.error(f"Error loading prompt configuration {agent_name}: {e}")
            
    def _reload_prompt_configuration(self, agent_name: str) -> None:
        """Reload a specific prompt configuration"""
        logger.info(f"Reloading prompt configuration for agent: {agent_name}")
        
        prompt_file = self.prompts_dir / f"{agent_name}.json"
        if prompt_file.exists():
            with self._config_lock:
                self._load_single_prompt_configuration(agent_name, prompt_file)
        else:
            logger.warning(f"Prompt configuration file not found: {prompt_file}")
            
    def get_llm_config(self, provider_name: str) -> Optional[LLMConfig]:
        """Get LLM configuration for a specific provider"""
        with self._config_lock:
            return self._llm_configs.get(provider_name)
            
    def get_all_llm_configs(self) -> Dict[str, LLMConfig]:
        """Get all LLM configurations"""
        with self._config_lock:
            return self._llm_configs.copy()
            
    def get_prompt_config(self, agent_name: str) -> Optional[PromptConfig]:
        """Get prompt configuration for a specific agent"""
        with self._config_lock:
            return self._prompt_configs.get(agent_name)
            
    def get_all_prompt_configs(self) -> Dict[str, PromptConfig]:
        """Get all prompt configurations"""
        with self._config_lock:
            return self._prompt_configs.copy()
            
    def update_llm_config(self, provider_name: str, config: LLMConfig) -> bool:
        """Update LLM configuration for a provider"""
        try:
            # Validate configuration
            if not self.validator.validate_llm_provider_config(config):
                logger.error(f"Invalid LLM configuration for provider: {provider_name}")
                return False
                
            with self._config_lock:
                self._llm_configs[provider_name] = config
                
            # Save to file
            self._save_llm_configuration()
            logger.info(f"Updated LLM configuration for provider: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating LLM configuration: {e}")
            return False
            
    def update_prompt_config(self, agent_name: str, config: PromptConfig) -> bool:
        """Update prompt configuration for an agent"""
        try:
            # Validate configuration
            if not self.validator.validate_prompt_config(config):
                logger.error(f"Invalid prompt configuration for agent: {agent_name}")
                return False
                
            with self._config_lock:
                self._prompt_configs[agent_name] = config
                
            # Save to file
            self._save_prompt_configuration(agent_name, config)
            logger.info(f"Updated prompt configuration for agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating prompt configuration: {e}")
            return False
            
    def _save_llm_configuration(self) -> None:
        """Save LLM configuration to file"""
        try:
            config_data = {
                "providers": {
                    name: asdict(config) for name, config in self._llm_configs.items()
                }
            }
            
            with open(self.llm_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving LLM configuration: {e}")
            raise
            
    def _save_prompt_configuration(self, agent_name: str, config: PromptConfig) -> None:
        """Save prompt configuration to file"""
        try:
            prompt_file = self.prompts_dir / f"{agent_name}.json"
            
            with open(prompt_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving prompt configuration: {e}")
            raise
            
    def validate_all_configurations(self) -> Dict[str, List[str]]:
        """Validate all configurations and return validation results"""
        results = {
            "llm_configs": [],
            "prompt_configs": []
        }
        
        # Validate LLM configurations
        for provider_name, config in self._llm_configs.items():
            if not self.validator.validate_llm_provider_config(config):
                results["llm_configs"].append(f"Invalid LLM config: {provider_name}")
                
        # Validate prompt configurations
        for agent_name, config in self._prompt_configs.items():
            if not self.validator.validate_prompt_config(config):
                results["prompt_configs"].append(f"Invalid prompt config: {agent_name}")
                
        return results
        
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get current configuration status"""
        return {
            "llm_providers": list(self._llm_configs.keys()),
            "prompt_agents": list(self._prompt_configs.keys()),
            "monitoring_enabled": self._monitoring_enabled,
            "config_directory": str(self.config_dir),
            "llm_config_file": str(self.llm_config_file),
            "prompts_directory": str(self.prompts_dir)
        }
        
    def __enter__(self):
        """Context manager entry"""
        self.start_monitoring()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()