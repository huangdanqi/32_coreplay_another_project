# Configuration Management System

The Configuration Management System provides comprehensive configuration loading, validation, and hot-reloading capabilities for the Diary Agent system.

## Features

- **LLM Provider Configuration**: Manage multiple LLM providers (Qwen, DeepSeek, etc.)
- **Agent Prompt Configuration**: Manage specialized prompts for each sub-agent
- **Hot-Reloading**: Automatic configuration updates when files change
- **Validation**: Comprehensive validation for all configuration types
- **File Monitoring**: Real-time monitoring of configuration file changes
- **Error Handling**: Robust error handling and recovery mechanisms
- **Thread Safety**: Safe concurrent access to configurations

## Architecture

```
ConfigManager
├── LLM Configuration Management
│   ├── Provider loading and validation
│   ├── Failover configuration
│   └── API endpoint management
├── Prompt Configuration Management
│   ├── Agent-specific prompts
│   ├── Template validation
│   └── Output format rules
├── File System Monitoring
│   ├── Real-time change detection
│   ├── Automatic reloading
│   └── Change event callbacks
└── Validation System
    ├── Structure validation
    ├── Content validation
    └── Syntax checking
```

## Configuration Files

### LLM Configuration (`llm_configuration.json`)

```json
{
  "providers": {
    "qwen": {
      "provider_name": "qwen",
      "api_endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
      "api_key": "your-qwen-api-key",
      "model_name": "qwen-turbo",
      "max_tokens": 150,
      "temperature": 0.7,
      "timeout": 30,
      "retry_attempts": 3
    },
    "deepseek": {
      "provider_name": "deepseek",
      "api_endpoint": "https://api.deepseek.com/v1/chat/completions",
      "api_key": "your-deepseek-api-key",
      "model_name": "deepseek-chat",
      "max_tokens": 150,
      "temperature": 0.7,
      "timeout": 30,
      "retry_attempts": 3
    }
  }
}
```

### Agent Prompt Configuration (`agent_prompts/{agent_name}.json`)

```json
{
  "agent_type": "weather_agent",
  "system_prompt": "你是一个专门写天气相关日记的AI助手...",
  "user_prompt_template": "请为以下天气事件生成一篇日记：\n\n事件类型：{event_name}...",
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
```

## Usage Examples

### Basic Usage

```python
from diary_agent.core.config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager("diary_agent/config")

# Get LLM configuration
qwen_config = config_manager.get_llm_config("qwen")
if qwen_config:
    print(f"Qwen endpoint: {qwen_config.api_endpoint}")

# Get prompt configuration
weather_config = config_manager.get_prompt_config("weather_agent")
if weather_config:
    print(f"Weather agent prompt: {weather_config.system_prompt}")
```

### Hot-Reloading with Callbacks

```python
def on_config_change(event):
    print(f"Configuration changed: {event.config_type} - {event.change_type}")

# Set up monitoring
config_manager.add_change_callback(on_config_change)
config_manager.start_monitoring()

# Configurations will automatically reload when files change
# Callbacks will be triggered for each change
```

### Context Manager Usage

```python
# Automatic monitoring setup and cleanup
with ConfigManager("diary_agent/config") as cm:
    # Monitoring is automatically started
    configs = cm.get_all_llm_configs()
    # Process configurations...
# Monitoring is automatically stopped when exiting
```

### Configuration Updates

```python
from diary_agent.utils.data_models import LLMConfig

# Create new LLM configuration
new_config = LLMConfig(
    provider_name="claude",
    api_endpoint="https://api.anthropic.com/v1/messages",
    api_key="your-claude-key",
    model_name="claude-3-sonnet",
    max_tokens=200,
    temperature=0.6,
    timeout=45,
    retry_attempts=2
)

# Update configuration (validates and saves to file)
success = config_manager.update_llm_config("claude", new_config)
if success:
    print("Configuration updated successfully")
```

### Validation

```python
# Validate all configurations
results = config_manager.validate_all_configurations()

if not results["llm_configs"] and not results["prompt_configs"]:
    print("All configurations are valid")
else:
    print("Validation errors found:")
    for error in results["llm_configs"]:
        print(f"LLM: {error}")
    for error in results["prompt_configs"]:
        print(f"Prompt: {error}")
```

## Configuration Validation Rules

### LLM Configuration Validation

- **provider_name**: Non-empty string
- **api_endpoint**: Valid HTTP/HTTPS URL
- **api_key**: Non-empty string
- **model_name**: Non-empty string
- **max_tokens**: Positive integer
- **temperature**: Float between 0.0 and 2.0
- **timeout**: Positive integer (seconds)
- **retry_attempts**: Non-negative integer

### Prompt Configuration Validation

- **agent_type**: Non-empty string
- **system_prompt**: Non-empty string
- **user_prompt_template**: Non-empty string
- **output_format**: Dictionary with required fields (title, content, emotion_tags)
- **validation_rules**: Dictionary with validation parameters
- **emotion_tags_valid**: List of valid emotional tags

## File Monitoring

The system uses the `watchdog` library to monitor configuration files for changes:

- **Supported Events**: File creation, modification, deletion
- **File Types**: JSON configuration files
- **Automatic Reloading**: Configurations are automatically reloaded when files change
- **Error Handling**: Invalid configurations are logged but don't crash the system
- **Callbacks**: Custom callbacks can be registered for change notifications

## Error Handling

### Configuration Loading Errors

- Missing configuration files are logged as warnings
- Corrupted JSON files are logged as errors
- Invalid configurations are rejected with detailed error messages
- System continues operating with existing valid configurations

### File Monitoring Errors

- File system errors are logged but don't stop monitoring
- Invalid file changes are logged and ignored
- Monitoring can be restarted if it fails

### Validation Errors

- Configuration structure validation
- Individual field validation
- JSON syntax validation
- File permission validation

## Thread Safety

The ConfigManager is designed for concurrent access:

- **Read Operations**: Thread-safe access to configurations
- **Write Operations**: Protected by locks during updates
- **File Monitoring**: Runs in separate thread
- **Callbacks**: Executed safely with error isolation

## Performance Considerations

- **Lazy Loading**: Configurations are loaded on demand
- **Caching**: Loaded configurations are cached in memory
- **Efficient Monitoring**: Only monitors relevant file changes
- **Minimal Overhead**: File monitoring has minimal performance impact

## Integration with Other Components

### LLM Manager Integration

```python
# ConfigManager provides configurations to LLMManager
llm_configs = config_manager.get_all_llm_configs()
llm_manager = LLMManager(llm_configs)
```

### Agent Integration

```python
# Agents get their prompt configurations from ConfigManager
prompt_config = config_manager.get_prompt_config("weather_agent")
weather_agent = WeatherAgent(prompt_config)
```

### Dynamic Reconfiguration

```python
# Agents can be notified of configuration changes
def on_prompt_change(event):
    if event.config_type == "prompt":
        agent_name = Path(event.file_path).stem
        new_config = config_manager.get_prompt_config(agent_name)
        agent_manager.update_agent_config(agent_name, new_config)

config_manager.add_change_callback(on_prompt_change)
```

## Best Practices

1. **Configuration Validation**: Always validate configurations before use
2. **Error Handling**: Handle missing or invalid configurations gracefully
3. **Monitoring Setup**: Use context managers for automatic cleanup
4. **Change Callbacks**: Register callbacks for dynamic reconfiguration
5. **File Permissions**: Ensure configuration files have proper read/write permissions
6. **Backup Configurations**: Keep backup copies of working configurations
7. **Version Control**: Track configuration changes in version control
8. **Security**: Protect API keys and sensitive configuration data

## Troubleshooting

### Common Issues

1. **Configuration Not Loading**
   - Check file paths and permissions
   - Validate JSON syntax
   - Check configuration structure

2. **Monitoring Not Working**
   - Verify watchdog installation
   - Check file system permissions
   - Ensure configuration directory exists

3. **Validation Failures**
   - Review validation error messages
   - Check required fields
   - Verify data types and ranges

4. **Performance Issues**
   - Monitor file system activity
   - Check for excessive file changes
   - Review callback efficiency

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config_manager = ConfigManager("diary_agent/config")
```

## Dependencies

- **watchdog**: File system monitoring
- **pathlib**: Path handling
- **json**: Configuration file parsing
- **threading**: Thread safety and monitoring
- **dataclasses**: Configuration data models