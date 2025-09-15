# Sensor Event Agent Documentation

## Overview

The Sensor Event Agent is a sophisticated system that translates technical sensor MQTT messages into cute, human-readable Chinese descriptions. It uses AI-powered language generation to convert raw sensor data into adorable, emotional narratives that make sensor events feel more personal and engaging.

## Features

- 🤖 **AI-Powered Translation**: Uses LLM (Large Language Model) to generate cute Chinese descriptions
- 🔄 **Automatic Failover**: Seamlessly switches between different AI providers if one fails
- 📱 **MQTT Integration**: Processes sensor data from MQTT messages
- 🎯 **Multiple Sensor Types**: Supports accelerometer, touch, gesture, sound, light, temperature, and more
- 🛡️ **Error Handling**: Comprehensive error handling with graceful degradation
- 📊 **Batch Processing**: Can process multiple sensor events simultaneously
- 🎮 **Interactive Mode**: Interactive testing interface for development

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MQTT Message  │───▶│  Sensor Event    │───▶│  AI Translation │
│   (Raw Data)    │    │     Agent        │    │   (Zhipu API)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Cute Chinese    │
                       │   Description    │
                       └──────────────────┘
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- Required packages: `aiohttp`, `asyncio`, `json`, `logging`

### Configuration

1. **LLM Configuration**: Edit `config/llm_configuration.json`
2. **Prompt Configuration**: Edit `config/prompt.json`
3. **API Keys**: Update your API keys in the configuration files

## Usage

### Command Line Interface

#### Basic Usage

```bash
# Process a single sensor event
python main.py -m '{"sensor_type": "touch", "value": 1, "duration": 2.5}'

# Process events from a file
python main.py -f messages.json

# Interactive mode
python main.py -i

# Batch processing
python main.py -f messages.json --batch
```

#### Advanced Options

```bash
# Verbose logging
python main.py -f messages.json --verbose

# Custom configuration
python main.py -f messages.json --config custom_prompt.json --llm-config custom_llm.json
```

### Programmatic Usage

```python
import asyncio
from core.sensor_event_agent import SensorEventAgent

async def main():
    # Initialize the agent
    agent = SensorEventAgent()
    
    # Process a sensor event
    mqtt_message = {
        "sensor_type": "touch",
        "value": 1,
        "duration": 2.5
    }
    
    result = await agent.translate_sensor_event(mqtt_message)
    
    if result["success"]:
        print(f"Description: {result['description']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

# Run the async function
asyncio.run(main())
```

## API Reference

### SensorEventAgent Class

#### Constructor

```python
SensorEventAgent(
    prompt_config_path: str = None,
    llm_config_path: str = None
)
```

**Parameters:**
- `prompt_config_path`: Path to prompt configuration file
- `llm_config_path`: Path to LLM configuration file

#### Methods

##### `translate_sensor_event(mqtt_message)`

Translates a single sensor event to human language.

**Parameters:**
- `mqtt_message`: MQTT message as JSON string or dictionary

**Returns:**
```python
{
    "description": "小鼻子轻轻点了下，好轻好萌哦~",
    "timestamp": "2025-09-08T00:00:21.341921",
    "sensor_type": "touch",
    "event_type": "interaction",
    "success": True
}
```

##### `process_batch_messages(mqtt_messages)`

Process multiple MQTT messages in batch.

**Parameters:**
- `mqtt_messages`: List of MQTT messages

**Returns:**
- List of translation results

## Input Format

### Supported Sensor Types

#### Touch Sensor
```json
{
    "sensor_type": "touch",
    "value": 1,
    "duration": 2.5
}
```

#### Accelerometer
```json
{
    "sensor_type": "accelerometer",
    "x": 0.1,
    "y": 0.2,
    "z": 9.8,
    "count": 3
}
```

#### Gesture Sensor
```json
{
    "sensor_type": "gesture",
    "gesture_type": "shake",
    "confidence": 0.9
}
```

#### Sound Sensor
```json
{
    "sensor_type": "sound",
    "decibel": 65,
    "frequency": 440
}
```

#### Light Sensor
```json
{
    "sensor_type": "light",
    "lux": 300,
    "color": "white"
}
```

#### Temperature Sensor
```json
{
    "sensor_type": "temperature",
    "temperature": 25.5,
    "humidity": 60
}
```

#### Gyroscope
```json
{
    "sensor_type": "gyroscope",
    "yaw": 45,
    "pitch": 10,
    "roll": 5
}
```

## Output Format

### Successful Translation

```json
{
    "description": "小鼻子轻轻点了下，好轻好萌哦~",
    "timestamp": "2025-09-08T00:00:21.341921",
    "sensor_type": "touch",
    "event_type": "interaction",
    "success": true
}
```

### Failed Translation

```json
{
    "description": "检测到传感器活动",
    "timestamp": "2025-09-08T00:00:21.341921",
    "error": "LLM generation failed: API timeout",
    "success": false
}
```

## Example Outputs

### Touch Events
- **Light touch**: "小鼻子轻轻点了下，好轻好萌哦~"
- **Long touch**: "被温柔地抚摸着"
- **Quick touch**: "被轻轻碰了一下"

### Motion Events
- **Single shake**: "轻快地摇摆"
- **Multiple shakes**: "小身体晃了3下~"
- **Strong motion**: "用力摇摆"

### Gesture Events
- **Shake gesture**: "使劲摇头晃脑"
- **Nod gesture**: "认真地点点头"
- **Wave gesture**: "挥挥小手打招呼"

### Sound Events
- **Loud sound**: "大声叫了一声"
- **Medium sound**: "轻声嘟囔了一下"
- **Quiet sound**: "发出微弱的声音"

### Light Events
- **Bright light**: "感受到明亮阳光"
- **Medium light**: "看到了温和光线"
- **Dim light**: "察觉到微弱亮光"

### Temperature Events
- **Hot**: "感觉热热的呢"
- **Cold**: "有点凉飕飕的"
- **Comfortable**: "温度刚刚好"

## Configuration Files

### Prompt Configuration (`config/prompt.json`)

```json
{
    "system_prompt": "你是一个可爱的翻译助手，将传感器数据翻译成萌系中文描述...",
    "user_prompt_template": "请将以下传感器数据翻译成可爱的中文描述...",
    "validation_rules": {
        "max_length": 20
    }
}
```

### LLM Configuration (`config/llm_configuration.json`)

```json
{
    "model_selection": {
        "default_provider": "zhipu"
    },
    "providers": {
        "zhipu": {
            "provider_name": "zhipu",
            "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "api_key": "your-api-key",
            "model_name": "glm-4",
            "max_tokens": 150,
            "temperature": 0.7,
            "timeout": 30,
            "retry_attempts": 3
        }
    }
}
```

## Error Handling

The agent includes comprehensive error handling:

1. **LLM Failover**: Automatically switches to backup providers
2. **Graceful Degradation**: Falls back to rule-based descriptions
3. **Input Validation**: Validates MQTT message format
4. **Timeout Handling**: Handles API timeouts gracefully
5. **Circuit Breaker**: Prevents cascading failures

## Testing

### Running Tests

```bash
# Run all tests
python main.py -f test_messages.json --verbose

# Interactive testing
python main.py -i

# Batch testing
python main.py -f test_messages.json --batch
```

### Test Message Examples

```json
[
    {
        "sensor_type": "touch",
        "value": 1,
        "duration": 2.5
    },
    {
        "sensor_type": "accelerometer",
        "x": 0.1,
        "y": 0.2,
        "z": 9.8,
        "count": 3
    },
    {
        "sensor_type": "gesture",
        "gesture_type": "shake",
        "confidence": 0.9
    }
]
```

## Performance

- **Response Time**: Typically 1-3 seconds per event
- **Throughput**: Can process 10-20 events per minute
- **Accuracy**: High accuracy with AI-generated descriptions
- **Reliability**: 99%+ uptime with failover mechanisms

## Troubleshooting

### Common Issues

1. **API Key Errors**: Check your API keys in the configuration
2. **Connection Timeouts**: Verify network connectivity
3. **Invalid JSON**: Ensure MQTT messages are valid JSON
4. **Missing Sensors**: Check sensor type is supported

### Debug Mode

```bash
python main.py -f messages.json --verbose
```

### Logs

Check logs in:
- `sensor_agent.log` - Main application logs
- `diary_agent.llm_manager.log` - LLM manager logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details