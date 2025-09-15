"""
Example usage of the Configuration Management System

This example demonstrates:
1. Loading and managing LLM provider configurations
2. Managing agent prompt configurations with hot-reloading
3. Configuration validation and error handling
4. File monitoring for dynamic updates
5. Configuration change callbacks
"""

import json
import time
from pathlib import Path
from diary_agent.core.config_manager import ConfigManager, ConfigChangeEvent
from diary_agent.utils.data_models import LLMConfig, PromptConfig


def configuration_change_handler(event: ConfigChangeEvent):
    """Handle configuration change events"""
    print(f"Configuration changed:")
    print(f"  Type: {event.config_type}")
    print(f"  File: {event.file_path}")
    print(f"  Change: {event.change_type}")
    print(f"  Time: {time.ctime(event.timestamp)}")
    print()


def main():
    """Demonstrate configuration management system usage"""
    
    print("=== Diary Agent Configuration Management Example ===\n")
    
    # Initialize configuration manager
    config_manager = ConfigManager("diary_agent/config")
    
    # 1. Display current configuration status
    print("1. Current Configuration Status:")
    status = config_manager.get_configuration_status()
    print(f"   LLM Providers: {status['llm_providers']}")
    print(f"   Prompt Agents: {status['prompt_agents']}")
    print(f"   Monitoring: {status['monitoring_enabled']}")
    print()
    
    # 2. Load and display LLM configurations
    print("2. LLM Provider Configurations:")
    llm_configs = config_manager.get_all_llm_configs()
    for provider_name, config in llm_configs.items():
        print(f"   {provider_name}:")
        print(f"     Model: {config.model_name}")
        print(f"     Endpoint: {config.api_endpoint}")
        print(f"     Max Tokens: {config.max_tokens}")
        print(f"     Temperature: {config.temperature}")
    print()
    
    # 3. Load and display prompt configurations
    print("3. Agent Prompt Configurations:")
    prompt_configs = config_manager.get_all_prompt_configs()
    for agent_name, config in prompt_configs.items():
        print(f"   {agent_name}:")
        print(f"     Type: {config.agent_type}")
        print(f"     System Prompt: {config.system_prompt[:50]}...")
        print(f"     Title Max Length: {config.validation_rules.get('title_max_length', 'N/A')}")
        print(f"     Content Max Length: {config.validation_rules.get('content_max_length', 'N/A')}")
    print()
    
    # 4. Add a new LLM provider configuration
    print("4. Adding New LLM Provider:")
    new_llm_config = LLMConfig(
        provider_name="claude",
        api_endpoint="https://api.anthropic.com/v1/messages",
        api_key="your-claude-api-key",
        model_name="claude-3-sonnet",
        max_tokens=200,
        temperature=0.6,
        timeout=45,
        retry_attempts=2
    )
    
    success = config_manager.update_llm_config("claude", new_llm_config)
    if success:
        print("   ✓ Successfully added Claude provider")
    else:
        print("   ✗ Failed to add Claude provider")
    print()
    
    # 5. Add a new prompt configuration
    print("5. Adding New Prompt Configuration:")
    new_prompt_config = PromptConfig(
        agent_type="example_agent",
        system_prompt="你是一个示例日记代理，专门处理示例事件。",
        user_prompt_template="请为以下示例事件生成日记：\n事件：{event_name}\n时间：{timestamp}\n用户：{user_profile}\n\n要求：标题6字符内，内容35字符内，包含合适的情感标签。",
        output_format={
            "title": "string (max 6 characters)",
            "content": "string (max 35 characters)",
            "emotion_tags": "array of strings"
        },
        validation_rules={
            "title_max_length": 6,
            "content_max_length": 35,
            "required_fields": ["title", "content", "emotion_tags"],
            "emotion_tags_valid": ["生气愤怒", "悲伤难过", "担忧", "焦虑忧愁", "惊讶震惊", "好奇", "羞愧", "平静", "开心快乐", "兴奋激动"]
        }
    )
    
    success = config_manager.update_prompt_config("example_agent", new_prompt_config)
    if success:
        print("   ✓ Successfully added example agent prompt")
    else:
        print("   ✗ Failed to add example agent prompt")
    print()
    
    # 6. Validate all configurations
    print("6. Configuration Validation:")
    validation_results = config_manager.validate_all_configurations()
    
    if not validation_results["llm_configs"] and not validation_results["prompt_configs"]:
        print("   ✓ All configurations are valid")
    else:
        print("   ✗ Configuration validation errors found:")
        for error in validation_results["llm_configs"]:
            print(f"     LLM: {error}")
        for error in validation_results["prompt_configs"]:
            print(f"     Prompt: {error}")
    print()
    
    # 7. Set up file monitoring with callbacks
    print("7. Setting up File Monitoring:")
    config_manager.add_change_callback(configuration_change_handler)
    config_manager.start_monitoring()
    print("   ✓ File monitoring started")
    print("   ✓ Change callback registered")
    print("   → Try modifying configuration files to see real-time updates")
    print()
    
    # 8. Demonstrate configuration retrieval
    print("8. Configuration Retrieval Examples:")
    
    # Get specific LLM config
    qwen_config = config_manager.get_llm_config("qwen")
    if qwen_config:
        print(f"   Qwen Config: {qwen_config.model_name} @ {qwen_config.api_endpoint}")
    
    # Get specific prompt config
    weather_config = config_manager.get_prompt_config("weather_agent")
    if weather_config:
        print(f"   Weather Agent: {weather_config.agent_type}")
        
    # Try to get non-existent config
    missing_config = config_manager.get_llm_config("nonexistent")
    print(f"   Missing Config: {missing_config}")
    print()
    
    # 9. Context manager usage
    print("9. Context Manager Usage:")
    print("   Using ConfigManager as context manager for automatic cleanup...")
    
    with ConfigManager("diary_agent/config") as cm:
        print(f"   Monitoring enabled: {cm._monitoring_enabled}")
        configs = cm.get_all_llm_configs()
        print(f"   Loaded {len(configs)} LLM configurations")
    
    print("   Context manager exited, monitoring stopped automatically")
    print()
    
    # 10. Error handling demonstration
    print("10. Error Handling:")
    
    # Try to add invalid configuration
    invalid_config = LLMConfig(
        provider_name="",  # Invalid empty name
        api_endpoint="not-a-url",  # Invalid URL
        api_key="test",
        model_name="test",
        max_tokens=-1,  # Invalid negative value
        temperature=5.0,  # Out of range
        timeout=0,  # Invalid zero timeout
        retry_attempts=-1  # Invalid negative retries
    )
    
    success = config_manager.update_llm_config("invalid", invalid_config)
    if not success:
        print("   ✓ Invalid configuration correctly rejected")
    else:
        print("   ✗ Invalid configuration was incorrectly accepted")
    print()
    
    # Clean up
    print("Cleaning up...")
    config_manager.stop_monitoring()
    print("✓ Configuration management example completed")


if __name__ == "__main__":
    main()