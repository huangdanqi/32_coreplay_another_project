"""
Unit tests for configuration management system
"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from threading import Event

from diary_agent.core.config_manager import ConfigManager, ConfigChangeEvent
from diary_agent.utils.data_models import LLMConfig, PromptConfig
from diary_agent.utils.validators import ConfigValidator


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test configurations
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Create prompts directory
        self.prompts_dir = self.config_dir / "agent_prompts"
        self.prompts_dir.mkdir(exist_ok=True)
        
        # Sample LLM configuration
        self.sample_llm_config = {
            "providers": {
                "qwen": {
                    "provider_name": "qwen",
                    "api_endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    "api_key": "test-qwen-key",
                    "model_name": "qwen-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                },
                "deepseek": {
                    "provider_name": "deepseek",
                    "api_endpoint": "https://api.deepseek.com/v1/chat/completions",
                    "api_key": "test-deepseek-key",
                    "model_name": "deepseek-chat",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                }
            }
        }
        
        # Sample prompt configuration
        self.sample_prompt_config = {
            "agent_type": "test_agent",
            "system_prompt": "You are a test agent",
            "user_prompt_template": "Process this event: {event_data}",
            "output_format": {
                "title": "string (max 6 characters)",
                "content": "string (max 35 characters)",
                "emotion_tags": "array of strings"
            },
            "validation_rules": {
                "title_max_length": 6,
                "content_max_length": 35,
                "required_fields": ["title", "content", "emotion_tags"],
                "emotion_tags_valid": ["生气愤怒", "悲伤难过", "担忧", "焦虑忧愁", "惊讶震惊", "好奇", "羞愧", "平静", "开心快乐", "兴奋激动"]
            }
        }
        
        # Create configuration files
        self.llm_config_file = self.config_dir / "llm_configuration.json"
        with open(self.llm_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_llm_config, f, indent=2)
            
        self.prompt_config_file = self.prompts_dir / "test_agent.json"
        with open(self.prompt_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_prompt_config, f, indent=2)
            
        # Initialize config manager
        self.config_manager = ConfigManager(str(self.config_dir))
        
    def tearDown(self):
        """Clean up test environment"""
        # Stop monitoring if running
        if hasattr(self.config_manager, '_monitoring_enabled') and self.config_manager._monitoring_enabled:
            self.config_manager.stop_monitoring()
            
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """Test ConfigManager initialization"""
        self.assertIsInstance(self.config_manager, ConfigManager)
        self.assertEqual(self.config_manager.config_dir, self.config_dir)
        self.assertFalse(self.config_manager._monitoring_enabled)
        
    def test_load_llm_configuration(self):
        """Test loading LLM configuration"""
        # Check that configurations were loaded
        llm_configs = self.config_manager.get_all_llm_configs()
        self.assertEqual(len(llm_configs), 2)
        self.assertIn("qwen", llm_configs)
        self.assertIn("deepseek", llm_configs)
        
        # Check individual configuration
        qwen_config = self.config_manager.get_llm_config("qwen")
        self.assertIsInstance(qwen_config, LLMConfig)
        self.assertEqual(qwen_config.provider_name, "qwen")
        self.assertEqual(qwen_config.model_name, "qwen-turbo")
        
    def test_load_prompt_configuration(self):
        """Test loading prompt configuration"""
        # Check that configurations were loaded
        prompt_configs = self.config_manager.get_all_prompt_configs()
        self.assertEqual(len(prompt_configs), 1)
        self.assertIn("test_agent", prompt_configs)
        
        # Check individual configuration
        test_config = self.config_manager.get_prompt_config("test_agent")
        self.assertIsInstance(test_config, PromptConfig)
        self.assertEqual(test_config.agent_type, "test_agent")
        self.assertEqual(test_config.system_prompt, "You are a test agent")
        
    def test_get_nonexistent_config(self):
        """Test getting non-existent configuration"""
        self.assertIsNone(self.config_manager.get_llm_config("nonexistent"))
        self.assertIsNone(self.config_manager.get_prompt_config("nonexistent"))
        
    def test_update_llm_config(self):
        """Test updating LLM configuration"""
        new_config = LLMConfig(
            provider_name="test_provider",
            api_endpoint="https://test.example.com/api",
            api_key="test-key",
            model_name="test-model",
            max_tokens=200,
            temperature=0.8,
            timeout=60,
            retry_attempts=5
        )
        
        # Update configuration
        result = self.config_manager.update_llm_config("test_provider", new_config)
        self.assertTrue(result)
        
        # Verify update
        updated_config = self.config_manager.get_llm_config("test_provider")
        self.assertEqual(updated_config.provider_name, "test_provider")
        self.assertEqual(updated_config.max_tokens, 200)
        
    def test_update_prompt_config(self):
        """Test updating prompt configuration"""
        new_config = PromptConfig(
            agent_type="new_agent",
            system_prompt="You are a new agent",
            user_prompt_template="New template: {data}",
            output_format={"title": "string", "content": "string", "emotion_tags": "array"},
            validation_rules={
                "title_max_length": 6,
                "content_max_length": 35,
                "required_fields": ["title", "content", "emotion_tags"],
                "emotion_tags_valid": ["平静", "开心快乐"]
            }
        )
        
        # Update configuration
        result = self.config_manager.update_prompt_config("new_agent", new_config)
        self.assertTrue(result)
        
        # Verify update
        updated_config = self.config_manager.get_prompt_config("new_agent")
        self.assertEqual(updated_config.agent_type, "new_agent")
        self.assertEqual(updated_config.system_prompt, "You are a new agent")
        
    def test_invalid_config_update(self):
        """Test updating with invalid configuration"""
        # Invalid LLM config (missing required fields)
        invalid_llm_config = LLMConfig(
            provider_name="",  # Empty name
            api_endpoint="invalid-url",  # Invalid URL
            api_key="test-key",
            model_name="test-model",
            max_tokens=-1,  # Invalid value
            temperature=3.0,  # Out of range
            timeout=0,  # Invalid value
            retry_attempts=-1  # Invalid value
        )
        
        result = self.config_manager.update_llm_config("invalid", invalid_llm_config)
        self.assertFalse(result)
        
    def test_validate_all_configurations(self):
        """Test configuration validation"""
        results = self.config_manager.validate_all_configurations()
        
        # Should have no errors for valid configurations
        self.assertEqual(len(results["llm_configs"]), 0)
        self.assertEqual(len(results["prompt_configs"]), 0)
        
    def test_configuration_status(self):
        """Test getting configuration status"""
        status = self.config_manager.get_configuration_status()
        
        self.assertIn("llm_providers", status)
        self.assertIn("prompt_agents", status)
        self.assertIn("monitoring_enabled", status)
        self.assertEqual(len(status["llm_providers"]), 2)
        self.assertEqual(len(status["prompt_agents"]), 1)
        self.assertFalse(status["monitoring_enabled"])
        
    def test_start_stop_monitoring(self):
        """Test starting and stopping file monitoring"""
        # Start monitoring
        self.config_manager.start_monitoring()
        self.assertTrue(self.config_manager._monitoring_enabled)
        
        # Stop monitoring
        self.config_manager.stop_monitoring()
        self.assertFalse(self.config_manager._monitoring_enabled)
        
    def test_change_callbacks(self):
        """Test configuration change callbacks"""
        callback_called = Event()
        received_event = None
        
        def test_callback(event: ConfigChangeEvent):
            nonlocal received_event
            received_event = event
            callback_called.set()
            
        # Add callback
        self.config_manager.add_change_callback(test_callback)
        
        # Simulate file change
        test_event = ConfigChangeEvent(
            config_type="llm",
            file_path=str(self.llm_config_file),
            change_type="modified",
            timestamp=time.time()
        )
        
        # Trigger callback manually (since we're not testing actual file monitoring)
        for callback in self.config_manager._change_callbacks:
            callback(test_event)
            
        # Verify callback was called
        self.assertTrue(callback_called.wait(timeout=1))
        self.assertIsNotNone(received_event)
        self.assertEqual(received_event.config_type, "llm")
        
        # Remove callback
        self.config_manager.remove_change_callback(test_callback)
        self.assertEqual(len(self.config_manager._change_callbacks), 0)
        
    def test_context_manager(self):
        """Test ConfigManager as context manager"""
        with ConfigManager(str(self.config_dir)) as cm:
            self.assertTrue(cm._monitoring_enabled)
            
        # Should be stopped after exiting context
        self.assertFalse(cm._monitoring_enabled)
        
    def test_missing_config_files(self):
        """Test handling missing configuration files"""
        # Create config manager with non-existent directory
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir(exist_ok=True)
        
        empty_config_manager = ConfigManager(str(empty_dir))
        
        # Should handle missing files gracefully
        self.assertEqual(len(empty_config_manager.get_all_llm_configs()), 0)
        self.assertEqual(len(empty_config_manager.get_all_prompt_configs()), 0)
        
    def test_corrupted_config_files(self):
        """Test handling corrupted configuration files"""
        # Create corrupted JSON file
        corrupted_file = self.config_dir / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write("{ invalid json }")
            
        # Should handle corrupted files gracefully
        validator = ConfigValidator()
        self.assertFalse(validator.validate_json_syntax(str(corrupted_file)))


class TestConfigValidator(unittest.TestCase):
    """Test cases for ConfigValidator"""
    
    def test_validate_llm_config_structure(self):
        """Test LLM configuration structure validation"""
        # Valid structure
        valid_config = {
            "providers": {
                "test": {
                    "provider_name": "test",
                    "api_endpoint": "https://test.com",
                    "api_key": "key",
                    "model_name": "model",
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                }
            }
        }
        
        self.assertTrue(ConfigValidator.validate_llm_config_structure(valid_config))
        
        # Invalid structure - missing providers
        invalid_config = {"settings": {}}
        self.assertFalse(ConfigValidator.validate_llm_config_structure(invalid_config))
        
        # Invalid structure - missing required field
        invalid_config2 = {
            "providers": {
                "test": {
                    "provider_name": "test",
                    # Missing api_endpoint
                    "api_key": "key",
                    "model_name": "model",
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                }
            }
        }
        self.assertFalse(ConfigValidator.validate_llm_config_structure(invalid_config2))
        
    def test_validate_llm_provider_config(self):
        """Test individual LLM provider configuration validation"""
        # Valid configuration
        valid_config = LLMConfig(
            provider_name="test",
            api_endpoint="https://test.com/api",
            api_key="test-key",
            model_name="test-model",
            max_tokens=100,
            temperature=0.7,
            timeout=30,
            retry_attempts=3
        )
        
        self.assertTrue(ConfigValidator.validate_llm_provider_config(valid_config))
        
        # Invalid configuration - bad URL
        invalid_config = LLMConfig(
            provider_name="test",
            api_endpoint="not-a-url",
            api_key="test-key",
            model_name="test-model",
            max_tokens=100,
            temperature=0.7,
            timeout=30,
            retry_attempts=3
        )
        
        self.assertFalse(ConfigValidator.validate_llm_provider_config(invalid_config))
        
    def test_validate_prompt_config_structure(self):
        """Test prompt configuration structure validation"""
        # Valid structure
        valid_config = {
            "agent_type": "test",
            "system_prompt": "Test prompt",
            "user_prompt_template": "Template",
            "output_format": {
                "title": "string",
                "content": "string",
                "emotion_tags": "array"
            },
            "validation_rules": {
                "title_max_length": 6,
                "content_max_length": 35,
                "required_fields": ["title", "content", "emotion_tags"],
                "emotion_tags_valid": ["平静", "开心快乐"]
            }
        }
        
        self.assertTrue(ConfigValidator.validate_prompt_config_structure(valid_config))
        
        # Invalid structure - missing required field
        invalid_config = {
            "agent_type": "test",
            # Missing system_prompt
            "user_prompt_template": "Template",
            "output_format": {},
            "validation_rules": {}
        }
        
        self.assertFalse(ConfigValidator.validate_prompt_config_structure(invalid_config))
        
    def test_validate_json_syntax(self):
        """Test JSON syntax validation"""
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"valid": "json"}, f)
            valid_file = f.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            invalid_file = f.name
            
        try:
            self.assertTrue(ConfigValidator.validate_json_syntax(valid_file))
            self.assertFalse(ConfigValidator.validate_json_syntax(invalid_file))
            self.assertFalse(ConfigValidator.validate_json_syntax("nonexistent.json"))
        finally:
            os.unlink(valid_file)
            os.unlink(invalid_file)


if __name__ == '__main__':
    unittest.main()