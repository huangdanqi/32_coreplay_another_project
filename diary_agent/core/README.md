# LLM Configuration Manager

The LLM Configuration Manager provides a robust system for managing multiple LLM providers with automatic failover, retry mechanisms, and configuration management.

## Features

- **Multiple Provider Support**: Currently supports Qwen and DeepSeek APIs
- **Automatic Failover**: Seamlessly switches between providers when one fails
- **Retry Mechanism**: Exponential backoff retry with configurable attempts
- **Configuration Management**: JSON-based configuration with hot-reloading
- **Error Handling**: Comprehensive error handling and logging
- **Async Support**: Fully asynchronous API for better performance

## Quick Start

```python
import asyncio
from diary_agent.core.llm_manager import LLMConfigManager

async def main():
    # Initialize the manager
    manager = LLMConfigManager()
    
    # Generate text with automatic failover
    try:
        result = await manager.generate_text_with_failover(
            prompt="Write a short diary entry about today's weather",
            system_prompt="You are a helpful diary writing assistant"
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
```

## Configuration

The LLM manager uses a JSON configuration file located at `config/llm_configuration.json`:

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

### Configuration Parameters

- `provider_name`: Unique identifier for the provider
- `api_endpoint`: API endpoint URL
- `api_key`: Authentication key for the API
- `model_name`: Model to use for text generation
- `max_tokens`: Maximum tokens to generate (default: 150)
- `temperature`: Sampling temperature (default: 0.7)
- `timeout`: Request timeout in seconds (default: 30)
- `retry_attempts`: Number of retry attempts (default: 3)

## API Reference

### LLMConfigManager

#### Methods

- `__init__(config_path: str)`: Initialize with configuration file path
- `get_provider_config(provider_name: str) -> Optional[LLMConfig]`: Get specific provider configuration
- `get_current_provider() -> Optional[LLMConfig]`: Get current active provider
- `generate_text_with_failover(prompt: str, system_prompt: str = "") -> str`: Generate text with failover
- `reload_configuration()`: Reload configuration from file
- `get_provider_status() -> Dict[str, Any]`: Get provider status information

### Error Classes

- `LLMProviderError`: Raised when LLM provider operations fail
- `LLMConfigurationError`: Raised when configuration is invalid

## Failover Mechanism

The manager automatically handles provider failures:

1. **Primary Provider**: Starts with the first configured provider
2. **Retry Logic**: Retries failed requests with exponential backoff
3. **Provider Switching**: Switches to next provider if all retries fail
4. **Circular Failover**: Cycles through all providers before giving up

## Retry Strategy

- **Exponential Backoff**: Delay increases exponentially (2^attempt + jitter)
- **Jitter**: Random delay component to prevent thundering herd
- **Configurable Attempts**: Set retry attempts per provider
- **Per-Provider Retries**: Each provider gets its own retry attempts

## Error Handling

The system provides comprehensive error handling:

- **Network Errors**: Handles connection timeouts and network issues
- **API Errors**: Processes HTTP error responses from providers
- **Configuration Errors**: Validates configuration on startup
- **Format Errors**: Handles malformed API responses

## Testing

Run the test suite:

```bash
python -m pytest diary_agent/tests/test_llm_manager.py -v
```

Or run the simple verification script:

```bash
python test_llm_implementation.py
```

## Examples

See `diary_agent/examples/llm_manager_example.py` for comprehensive usage examples including:

- Basic usage
- Failover simulation
- Configuration management
- API client creation
- Error handling

## Integration with Diary Agent

The LLM manager integrates seamlessly with the diary agent system:

1. **Sub-Agent Integration**: Each sub-agent uses the manager for text generation
2. **Prompt Processing**: Handles system and user prompts for diary generation
3. **Error Recovery**: Provides graceful degradation when providers fail
4. **Performance**: Async operations for concurrent diary generation

## Requirements

- Python 3.7+
- aiohttp >= 3.8.0
- pytest >= 7.0.0 (for testing)
- pytest-asyncio >= 0.21.0 (for testing)

## Security Considerations

- **API Keys**: Store API keys securely, never commit to version control
- **Rate Limiting**: Respect provider rate limits and implement backoff
- **Timeout Handling**: Set appropriate timeouts to prevent hanging requests
- **Error Logging**: Log errors without exposing sensitive information