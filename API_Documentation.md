# Sensor Event Agent API Documentation

## Overview

The Sensor Event Agent API provides a comprehensive testing and integration interface for the sensor event translation system. This API allows you to test sensor event processing, generate cute Chinese descriptions, and integrate sensor data processing into your applications.

## Quick Start (Using the API)

1) Start the API server

```powershell
python simple_diary_api.py --port 5003 --debug
```

2) Verify the server is running

```powershell
curl http://localhost:5003/api/health
```

3) Run the test client (includes Sensor Event tests)

```powershell
python test_simple_api.py
```

- Choose 1 to run all API tests
- Choose 2 for interactive API tests
- Choose 3 for 传感器事件测试 (Sensor Event tests in the same client)

4) Call endpoints directly (Windows PowerShell examples)

- Health

```powershell
curl http://localhost:5003/api/health
```

- Get events

```powershell
curl http://localhost:5003/api/events
```

- BaZi/WuXing calculation

```powershell
curl -X POST http://localhost:5003/api/bazi_wuxing/calc -H "Content-Type: application/json" -d '{"birth_year":1990,"birth_month":5,"birth_day":20,"birth_hour":14,"birthplace":"北京"}'
```

- Process single event

```powershell
curl -X POST http://localhost:5003/api/diary/process -H "Content-Type: application/json" -d '{"event_category":"human_toy_interactive_function","event_name":"liked_interaction_once"}'
```

- Batch process events

```powershell
curl -X POST http://localhost:5003/api/diary/batch-process -H "Content-Type: application/json" -d '{"events":[{"event_category":"human_toy_interactive_function","event_name":"liked_interaction_3_to_5_times"},{"event_category":"human_toy_talk","event_name":"positive_emotional_dialogue"}]}'
```

5) Non-interactive test client runs

```powershell
# Run all API tests automatically
echo 1 | python test_simple_api.py

# Jump straight to Sensor Event test menu
echo 3 | python test_simple_api.py
```

## API Endpoints

### Base URL
```
http://localhost:5003/api
```

### Event Agents (Extraction / Update / Pipeline)

#### 1) POST /event/extract
Request body
```json
{
  "chat_uuid": "cu-1",
  "chat_event_uuid": "evt-1",
  "memory_uuid": "mem-1",
  "dialogue": "上一段完整对话..."
}
```
Response body
```json
{
  "success": true,
  "message": "Extraction completed",
  "data": {
    "chat_uuid": "cu-1",
    "chat_event_uuid": "evt-1",
    "memory_uuid": "mem-1",
    "topic": "考试",
    "title": "考试压力缓解",
    "summary": "不超过50字",
    "emotion": ["担忧","平静"],
    "type": "new",
    "created_at": "2025-09-08T00:00:00"
  }
}
```

### BaZi/WuXing Calculation

#### 1) POST /bazi_wuxing/calc
Calculate BaZi (八字，年柱/月柱/日柱/时柱) and aggregate WuXing (五行) from birth info.

Request body
```json
{
  "birth_year": 1990,
  "birth_month": 5,
  "birth_day": 20,
  "birth_hour": 14,
  "birthplace": "北京",
  "force_llm": false,
  "provider": "qwen"
}
```

Notes
- `force_llm` (optional): when true, disables local fallback; returns only what the LLM outputs. Use this to verify LLM responses.
- `provider` (optional): sets the default provider for this call (must exist in `config/llm_configuration.json`).

Response body
```json
{
  "success": true,
  "message": "BaZi/WuXing calculated",
  "data": {
    "bazi": ["庚","午","辛","午","乙","亥","癸","未"],
    "wuxing": ["金","水","火","木","土"]
  },
  "timestamp": "2025-09-08T00:00:00"
}
```

Constraints enforced by extractor
- topic: one of [个人信息, 爱情, 亲情, 友情, 工作, 考试, 健康/疾病, 生活琐事, 思想思考, 时事评论]
- summary: <= 50 chars
- emotion: 0-3 items from [生气愤怒, 悲伤难过, 担忧, 焦虑忐忑, 惊讶震惊, 好奇, 宽解, 平静, 开心快乐, 兴奋激动]

#### 2) POST /event/update
Request body
```json
{
  "extraction_result": { /* output from /event/extract */ },
  "related_events": [ { /* past event */ } ]
}
```
Response body
```json
{
  "success": true,
  "message": "Update completed",
  "data": {
    "merged": true,
    "merge_reason": "heuristic_merge",
    "new_event": null,
    "updated_event": {
      "topic": "考试",
      "title": "考试担忧",
      "summary": "旧摘要 | 新摘要(截断至200)",
      "emotion": ["担忧","平静"],
      "type": "update",
      "updated_at": "2025-09-08T00:00:00"
    },
    "update_info": {"updated_by": "event_update_agent", "updated_at": "2025-09-08T00:00:00"}
  }
}
```

Update decision logic
1) Heuristic merge (fast, deterministic)
   - Match if memory_uuid equals OR topic equals (trimmed). If none match, pick first related event as fallback candidate.
   - Build updated_event:
     - title: keep candidate; if empty, use extraction title
     - summary: concat candidate.summary + " | " + extraction.summary; dedup and trim to 200
     - emotion: union(cand.emotion, extr.emotion) preserving order
     - type="update"; updated_at=now(ISO8601)
   - Return merged=true, merge_reason=heuristic_merge
2) LLM fallback
   - If heuristic fails, ask LLM to return JSON {merged, merge_reason, new_event|null, updated_event|null}

#### 3) POST /event/pipeline
Runs extract → update in one call
Request body
```json
{
  "dialogue_payload": {
    "chat_uuid": "cu-1",
    "chat_event_uuid": "evt-1",
    "memory_uuid": "mem-1",
    "dialogue": "上一段完整对话..."
  },
  "related_events": []
}
```
Response body
```json
{
  "success": true,
  "message": "Pipeline completed",
  "data": { "extraction": { ... }, "update": { ... } }
}
```

### Health Check
**GET** `/health`

Check if the API server is running and healthy.

**Response:**
```json
{
    "success": true,
    "status": "healthy",
    "timestamp": "2025-09-08T00:00:00.000000",
    "version": "1.0.0"
}
```

### Get Events
**GET** `/events`

Retrieve all available events from the events.json configuration.

**Response:**
```json
{
    "success": true,
    "data": {
        "events": [
            {
                "event_category": "human_toy_interactive_function",
                "event_name": "liked_interaction_once",
                "description": "User liked interaction once"
            }
        ]
    }
}
```

### Process Single Event
**POST** `/diary/process`

Process a single event and generate diary entry if conditions are met.

**Request Body:**
```json
{
    "event_category": "human_toy_interactive_function",
    "event_name": "liked_interaction_once"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "diary_generated": true,
        "diary_entry": {
            "title": "被喜欢的小互动",
            "content": "今天主人和我玩了一次，感觉很开心呢~",
            "emotion_tags": ["开心", "满足"],
            "timestamp": "2025-09-08T00:00:00.000000"
        }
    }
}
```

### Process Batch Events
**POST** `/diary/batch-process`

Process multiple events in batch.

**Request Body:**
```json
{
    "events": [
        {
            "event_category": "human_toy_interactive_function",
            "event_name": "liked_interaction_3_to_5_times"
        },
        {
            "event_category": "human_toy_talk",
            "event_name": "positive_emotional_dialogue"
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "total_events": 2,
        "diaries_generated": 1,
        "results": [
            {
                "status": "diary_generated",
                "event_name": "liked_interaction_3_to_5_times",
                "diary_entry": {
                    "title": "多次互动",
                    "content": "今天主人和我玩了好几次，真是太开心了！",
                    "emotion_tags": ["兴奋", "满足"]
                }
            },
            {
                "status": "no_diary",
                "event_name": "positive_emotional_dialogue",
                "reason": "Condition not met"
            }
        ]
    }
}
```

### Test Diary Generation
**POST** `/diary/test`

Test diary generation with sample events.

**Request Body:**
```json
{}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "total_generated": 3,
        "test_results": [
            {
                "event_name": "liked_interaction_once",
                "diary_entry": {
                    "title": "被喜欢的小互动",
                    "content": "今天主人和我玩了一次，感觉很开心呢~",
                    "emotion_tags": ["开心", "满足"]
                }
            }
        ]
    }
}
```

## Sensor Event Agent Integration

### Direct Integration

The Sensor Event Agent can be integrated directly into your Python applications:

```python
import asyncio
from sensor_event_agent.core.sensor_event_agent import SensorEventAgent

async def process_sensor_data():
    # Initialize the agent
    agent = SensorEventAgent()
    
    # Process sensor event
    mqtt_message = {
        "sensor_type": "touch",
        "value": 1,
        "duration": 2.5
    }
    
    result = await agent.translate_sensor_event(mqtt_message)
    
    if result["success"]:
        print(f"Description: {result['description']}")
        return result['description']
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return None

# Run the function
description = asyncio.run(process_sensor_data())
```

### Batch Processing

```python
async def process_multiple_sensors():
    agent = SensorEventAgent()
    
    sensor_events = [
        {"sensor_type": "touch", "value": 1, "duration": 2.5},
        {"sensor_type": "accelerometer", "x": 0.1, "y": 0.2, "z": 9.8, "count": 3},
        {"sensor_type": "gesture", "gesture_type": "shake", "confidence": 0.9}
    ]
    
    results = agent.process_batch_messages(sensor_events)
    
    for i, result in enumerate(results):
        if result["success"]:
            print(f"Event {i+1}: {result['description']}")
        else:
            print(f"Event {i+1}: Failed - {result.get('error', 'Unknown error')}")
```

## Input Formats

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

#### Proximity Sensor
```json
{
    "sensor_type": "proximity",
    "distance": 10,
    "detected": true
}
```

#### Vibration Sensor
```json
{
    "sensor_type": "vibration",
    "intensity": 0.7,
    "frequency": 50
}
```

#### Pressure Sensor
```json
{
    "sensor_type": "pressure",
    "pressure": 1013.25,
    "unit": "hPa"
}
```

#### Humidity Sensor
```json
{
    "sensor_type": "humidity",
    "humidity": 60,
    "temperature": 25
}
```

## Output Formats

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

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request format
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
    "success": false,
    "error": "Error message",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-09-08T00:00:00.000000"
}
```

### Common Error Codes

- `INVALID_EVENT_FORMAT`: Event data format is invalid
- `LLM_GENERATION_FAILED`: AI text generation failed
- `CONFIGURATION_ERROR`: Configuration file error
- `API_TIMEOUT`: API request timeout
- `PROVIDER_UNAVAILABLE`: LLM provider unavailable

## Testing

### Using the Test Client

The `test_simple_api.py` file provides comprehensive testing capabilities:

```bash
# Run all tests
python test_simple_api.py

# Choose mode:
# 1. Run all tests
# 2. Interactive testing
# 3. Sensor event testing
```

### Test Modes

#### 1. All Tests Mode
Runs all available tests including:
- Health check
- Event retrieval
- Single event processing
- Batch event processing
- Invalid event handling
- Diary generation
- Sensor event translation (if available)

#### 2. Interactive Mode
Allows you to run individual tests:
- Health Check
- Get Events
- Single Event Processing
- Batch Event Processing
- Invalid Event Test
- Diary Generation Test
- Single Sensor Event Test
- Batch Sensor Event Test
- Interactive Sensor Test

#### 3. Sensor Event Testing Mode
Dedicated sensor event testing:
- Single sensor event test
- Batch sensor event test
- Interactive sensor testing
- All sensor tests

### Example Test Commands

```bash
# Test single sensor event
python test_simple_api.py
# Choose mode 3, then option 1

# Test batch sensor events
python test_simple_api.py
# Choose mode 3, then option 2

# Interactive sensor testing
python test_simple_api.py
# Choose mode 3, then option 3
```

## Configuration

### LLM Configuration

The agent uses the LLM configuration from `config/llm_configuration.json`:

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

### Prompt Configuration

Sensor event prompts are configured in `sensor_event_agent/config/prompt.json`:

```json
{
    "system_prompt": "你是一个可爱的翻译助手，将传感器数据翻译成萌系中文描述...",
    "user_prompt_template": "请将以下传感器数据翻译成可爱的中文描述...",
    "validation_rules": {
        "max_length": 20
    }
}
```

## Performance

### Response Times
- **Single Event**: 1-3 seconds
- **Batch Events**: 2-5 seconds per event
- **Sensor Translation**: 1-2 seconds

### Throughput
- **Single Processing**: 20-30 events per minute
- **Batch Processing**: 10-20 events per minute
- **Sensor Events**: 30-40 events per minute

### Reliability
- **Uptime**: 99%+ with failover mechanisms
- **Error Rate**: <1% with proper configuration
- **Fallback**: Automatic fallback to rule-based descriptions

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Check your API keys in the configuration
   - Verify API key permissions

2. **Connection Timeouts**
   - Check network connectivity
   - Increase timeout values in configuration

3. **Invalid JSON Format**
   - Ensure MQTT messages are valid JSON
   - Check sensor data structure

4. **Missing Sensor Types**
   - Verify sensor type is supported
   - Check sensor data format

### Debug Mode

Enable verbose logging:

```bash
python test_simple_api.py --verbose
```

### Log Files

Check logs in:
- `sensor_agent.log` - Main application logs
- `diary_agent.llm_manager.log` - LLM manager logs
- `diary_agent.errors.log` - Error logs

## Integration Examples

### Web Application Integration

```python
from flask import Flask, request, jsonify
import asyncio
from sensor_event_agent.core.sensor_event_agent import SensorEventAgent

app = Flask(__name__)
agent = SensorEventAgent()

@app.route('/api/sensor/translate', methods=['POST'])
def translate_sensor():
    try:
        sensor_data = request.json
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(agent.translate_sensor_event(sensor_data))
        loop.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
```

### MQTT Integration

```python
import paho.mqtt.client as mqtt
import asyncio
from sensor_event_agent.core.sensor_event_agent import SensorEventAgent

agent = SensorEventAgent()

def on_message(client, userdata, message):
    try:
        sensor_data = json.loads(message.payload.decode())
        
        # Process sensor event
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(agent.translate_sensor_event(sensor_data))
        loop.close()
        
        if result["success"]:
            print(f"Sensor translation: {result['description']}")
        else:
            print(f"Translation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT client setup
client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.subscribe("sensors/#")
client.loop_forever()
```

## Support

For issues and questions:
- Check the troubleshooting section
- Review log files for error details
- Create an issue in the repository
- Check configuration files for errors

## License

This project is licensed under the MIT License.
