# Diary System API

A REST API for the Diary System that allows you to generate diary entries based on various event types.

## Features

- **Single Diary Generation**: Generate individual diary entries
- **Batch Diary Generation**: Generate multiple diary entries at once
- **Event Templates**: Get predefined event templates
- **Health Check**: Monitor API status
- **Error Handling**: Comprehensive error handling and validation
- **Interactive Mode**: Command-line interface for easy testing

## Installation

1. Install required dependencies:
```bash
pip install -r requirements_api.txt
```

2. Ensure the diary system modules are available in your Python path.

## Quick Start

### 1. Start the API Server

```bash
python api_diary_system.py
```

The server will start on `http://localhost:5000` by default.

### 2. Test the API

```bash
python api_usage_examples.py
```

## API Endpoints

### Health Check
```
GET /api/health
```
Returns the API status and health information.

### Generate Single Diary
```
POST /api/diary/generate
```

**Request Body:**
```json
{
    "event_type": "human_machine_interaction",
    "event_name": "liked_interaction_once",
    "event_details": {
        "interaction_type": "抚摸",
        "duration": "5分钟",
        "user_response": "positive",
        "toy_emotion": "开心"
    },
    "user_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "message": "Diary entry generated successfully",
    "data": {
        "entry_id": "uuid",
        "event_type": "human_machine_interaction",
        "event_name": "liked_interaction_once",
        "title": "日记标题",
        "content": "日记内容",
        "emotion_tags": ["开心"],
        "timestamp": "2024-01-01T12:00:00",
        "agent_type": "interactive_agent",
        "llm_provider": "provider_name"
    },
    "timestamp": "2024-01-01T12:00:00"
}
```

### Generate Batch Diary
```
POST /api/diary/batch
```

**Request Body:**
```json
{
    "events": [
        {
            "event_type": "human_machine_interaction",
            "event_name": "liked_interaction_once",
            "event_details": {
                "interaction_type": "抚摸",
                "duration": "5分钟",
                "user_response": "positive",
                "toy_emotion": "开心"
            }
        },
        {
            "event_type": "dialogue",
            "event_name": "positive_emotional_dialogue",
            "event_details": {
                "dialogue_type": "开心对话",
                "content": "主人今天心情很好",
                "duration": "10分钟",
                "toy_emotion": "开心快乐"
            }
        }
    ],
    "daily_diary_count": 2,
    "user_id": 1
}
```

### Get Event Templates
```
GET /api/diary/templates
```

Returns available event types and their example configurations.

### Test Diary System
```
POST /api/diary/test
```

Runs a test with sample data to verify the system is working correctly.

## Event Types

### 1. Human Machine Interaction (`human_machine_interaction`)
Events related to physical interaction between user and toy.

**Example:**
```json
{
    "event_type": "human_machine_interaction",
    "event_name": "liked_interaction_once",
    "event_details": {
        "interaction_type": "抚摸",
        "duration": "5分钟",
        "user_response": "positive",
        "toy_emotion": "开心"
    }
}
```

### 2. Dialogue (`dialogue`)
Events related to verbal communication.

**Example:**
```json
{
    "event_type": "dialogue",
    "event_name": "positive_emotional_dialogue",
    "event_details": {
        "dialogue_type": "开心对话",
        "content": "主人今天心情很好",
        "duration": "10分钟",
        "toy_emotion": "开心快乐"
    }
}
```

### 3. Neglect (`neglect`)
Events related to periods of no interaction or communication.

**Example:**
```json
{
    "event_type": "neglect",
    "event_name": "neglect_1_day_no_dialogue",
    "event_details": {
        "neglect_duration": 1,
        "neglect_type": "no_dialogue",
        "disconnection_type": "无对话有互动",
        "disconnection_days": 1,
        "memory_status": "on",
        "last_interaction_date": "2024-01-01T12:00:00"
    }
}
```

## Usage Examples

### Python Requests

```python
import requests
import json

# Generate single diary
response = requests.post(
    "http://localhost:5000/api/diary/generate",
    json={
        "event_type": "human_machine_interaction",
        "event_name": "test_interaction",
        "event_details": {
            "interaction_type": "抚摸",
            "duration": "5分钟",
            "toy_emotion": "开心"
        }
    }
)

result = response.json()
if result["success"]:
    print(f"Title: {result['data']['title']}")
    print(f"Content: {result['data']['content']}")
```

### cURL

```bash
# Health check
curl -X GET http://localhost:5000/api/health

# Generate single diary
curl -X POST http://localhost:5000/api/diary/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "human_machine_interaction",
    "event_name": "test_interaction",
    "event_details": {
      "interaction_type": "抚摸",
      "duration": "5分钟",
      "toy_emotion": "开心"
    }
  }'
```

## Error Handling

The API returns standardized error responses:

```json
{
    "success": false,
    "message": "Error description",
    "error": "Detailed error information",
    "timestamp": "2024-01-01T12:00:00"
}
```

### Common Error Codes

- `400`: Bad Request - Invalid input data
- `404`: Not Found - Endpoint does not exist
- `405`: Method Not Allowed - HTTP method not supported
- `500`: Internal Server Error - Server-side error

## Configuration

### Server Configuration

You can customize the server settings:

```bash
python api_diary_system.py --host 0.0.0.0 --port 8080 --debug
```

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode
- `FLASK_DEBUG`: Set to `True` to enable debug mode

## Interactive Mode

Run the interactive diary generator:

```bash
python api_usage_examples.py
```

This provides a command-line interface for:
- Generating single diary entries
- Batch diary generation
- Viewing event templates
- Testing the system

## Logging

The API logs all requests and errors to:
- Console output
- `api_diary_system.log` file

## Development

### Adding New Endpoints

1. Define the route in `api_diary_system.py`
2. Add validation logic
3. Update error handling
4. Add tests in `api_usage_examples.py`

### Testing

Run the test suite:
```bash
python api_usage_examples.py
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the API server is running
2. **Import Errors**: Check that all diary system modules are available
3. **JSON Errors**: Validate your request format
4. **Timeout Errors**: Check LLM configuration and network connectivity

### Debug Mode

Enable debug mode for detailed error information:
```bash
python api_diary_system.py --debug
```

## License

This API is part of the Diary System project.

