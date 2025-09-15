# 🎯 Simple Diary API - User Guide

## 📋 Overview

The Simple Diary API is a streamlined REST API that processes events from `diary_agent/events.json` and generates diary entries when conditions are met. It requires only **event category** and **event name** - no complex event details needed!

## 🚀 Quick Start

### 1. Start the API Server

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Start the server
python simple_diary_api.py --port 5003
```

### 2. Test the API

```bash
# Run the test client
python test_simple_api.py
```

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/events` | Get all events from events.json |
| `POST` | `/api/diary/process` | Process single event |
| `POST` | `/api/diary/batch-process` | Process multiple events |
| `POST` | `/api/diary/test` | Test with sample events |

## 📝 Input Format

### Single Event Processing

**Endpoint:** `POST /api/diary/process`

**Input (Simplified):**
```json
{
  "event_category": "human_toy_interactive_function",
  "event_name": "liked_interaction_once"
}
```

**Required Fields:**
- `event_category`: Event category from events.json
- `event_name`: Specific event name from events.json

**No `event_details` required!** The API auto-generates appropriate details.

### Batch Event Processing

**Endpoint:** `POST /api/diary/batch-process`

**Input:**
```json
{
  "events": [
    {
      "event_category": "human_toy_interactive_function",
      "event_name": "liked_interaction_once"
    },
    {
      "event_category": "human_toy_talk",
      "event_name": "positive_emotional_dialogue"
    },
    {
      "event_category": "weather_events",
      "event_name": "favorite_weather"
    }
  ]
}
```

## 📤 Output Format

### Successful Diary Generation

```json
{
  "success": true,
  "message": "Diary generated successfully",
  "data": {
    "event_category": "human_toy_interactive_function",
    "event_name": "liked_interaction_once",
    "diary_generated": true,
    "diary_entry": {
      "title": "被抚摸的快乐",
      "content": "今天主人轻轻地抚摸了我，感觉特别温暖和舒适...",
      "emotion_tags": ["开心", "温暖"],
      "timestamp": "2025-09-04T19:38:07.921834",
      "entry_id": "1_simple_event_a5fd1572-7f7d-47f8-8d0b-4f6168441356_1757039887",
      "agent_type": "interactive_agent",
      "llm_provider": "ollama_qwen3"
    }
  },
  "timestamp": "2025-09-04T19:39:06.367488"
}
```

### Event Processed (No Diary Generated)

```json
{
  "success": true,
  "message": "Event processed but no diary generated",
  "data": {
    "event_category": "human_toy_talk",
    "event_name": "positive_emotional_dialogue",
    "diary_generated": false,
    "reason": "Random condition not met"
  },
  "timestamp": "2025-09-04T19:39:08.407585"
}
```

### Error Response

```json
{
  "success": false,
  "message": "Event not found in events.json",
  "error": "Invalid event data",
  "timestamp": "2025-09-04T19:39:08.407585"
}
```

## 📚 Available Event Categories

The API supports **10 event categories** from `events.json`:

### 1. **human_toy_interactive_function** (6 events)
- `liked_interaction_once`
- `liked_interaction_3_to_5_times`
- `liked_interaction_over_5_times`
- `disliked_interaction_once`
- `disliked_interaction_3_to_5_times`
- `neutral_interaction_over_5_times`

### 2. **human_toy_talk** (2 events)
- `positive_emotional_dialogue`
- `negative_emotional_dialogue`

### 3. **unkeep_interactive** (9 events)
- `neglect_1_day_no_dialogue`
- `neglect_1_day_no_interaction`
- `neglect_3_days_no_dialogue`
- `neglect_3_days_no_interaction`
- `neglect_7_days_no_dialogue`
- `neglect_7_days_no_interaction`
- `neglect_15_days_no_interaction`
- `neglect_30_days_no_dialogue`
- `neglect_30_days_no_interaction`

### 4. **weather_events** (4 events)
- `favorite_weather`
- `dislike_weather`
- `favorite_season`
- `dislike_season`

### 5. **seasonal_events** (2 events)
- `favorite_season`
- `dislike_season`

### 6. **trending_events** (2 events)
- `celebration`
- `disaster`

### 7. **holiday_events** (3 events)
- `approaching_holiday`
- `during_holiday`
- `holiday_ends`

### 8. **friends_function** (8 events)
- `made_new_friend`
- `friend_deleted`
- `liked_single`
- `liked_3_to_5`
- `liked_5_plus`
- `disliked_single`
- `disliked_3_to_5`
- `disliked_5_plus`

### 9. **same_frequency** (1 event)
- `close_friend_frequency`

### 10. **adopted_function** (1 event)
- `toy_claimed`

## 🔧 Usage Examples

### Example 1: Single Event (PowerShell)

```powershell
$body = '{"event_category": "human_toy_interactive_function", "event_name": "liked_interaction_once"}'
Invoke-WebRequest -Uri "http://localhost:5003/api/diary/process" -Method POST -Body $body -ContentType "application/json"
```

### Example 2: Single Event (Python)

```python
import requests

payload = {
    "event_category": "human_toy_interactive_function",
    "event_name": "liked_interaction_once"
}

response = requests.post("http://localhost:5003/api/diary/process", json=payload)
print(response.json())
```

### Example 3: Batch Processing (Python)

```python
import requests

payload = {
    "events": [
        {
            "event_category": "weather_events",
            "event_name": "favorite_weather"
        },
        {
            "event_category": "unkeep_interactive",
            "event_name": "neglect_1_day_no_dialogue"
        }
    ]
}

response = requests.post("http://localhost:5003/api/diary/batch-process", json=payload)
print(response.json())
```

### Example 4: Get All Events

```python
import requests

response = requests.get("http://localhost:5003/api/events")
events = response.json()
print(f"Found {len(events['data'])} event categories")
```

## 🎯 Key Features

### ✅ **Simplified Input**
- Only requires `event_category` and `event_name`
- No complex `event_details` needed
- Auto-generates appropriate event details

### ✅ **Conditional Processing**
- Randomly decides if diary should be generated (50% chance)
- Only returns diary when conditions are met
- Provides reason when no diary is generated

### ✅ **Event Validation**
- Validates events against `events.json`
- Returns error for invalid events
- Supports all 10 event categories

### ✅ **Auto-Generated Details**
- Creates appropriate event details based on event name
- Includes timestamps, emotions, and context
- Tailored details for each event type

### ✅ **Multiple Output Formats**
- Single event processing
- Batch event processing
- Health check and event listing

## 🚨 Error Handling

### Common Error Responses

**1. Missing Required Fields:**
```json
{
  "success": false,
  "message": "Missing required field: event_category",
  "error": "Invalid request data"
}
```

**2. Invalid Event:**
```json
{
  "success": false,
  "message": "Event not found in events.json",
  "error": "Invalid event data"
}
```

**3. No JSON Data:**
```json
{
  "success": false,
  "message": "No JSON data provided",
  "error": "Missing request body"
}
```

## 🌐 Server Configuration

### Default Settings
- **Host:** `0.0.0.0` (all interfaces)
- **Port:** `5003`
- **Debug Mode:** `False`
- **CORS:** Enabled for all origins

### Change Port
```bash
python simple_diary_api.py --port 8080
```

### Production Deployment
For production, replace the Flask development server with a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5003 simple_diary_api:app
```

## 📊 Performance

### Response Times
- **Health Check:** ~10ms
- **Get Events:** ~50ms
- **Single Event Processing:** ~1-2 seconds (includes LLM generation)
- **Batch Processing:** ~1-2 seconds per event

### LLM Provider
- **Default:** `ollama_qwen3`
- **Fallback:** `llm_qwen`, `llm_deepseek`
- **Circuit Breaker:** Automatic failover

## 🔄 Migration to Cloud Server

To deploy to a cloud server, simply change the base URL:

```python
# Local development
base_url = "http://localhost:5003"

# Cloud server
base_url = "https://your-cloud-server.com/api"
```

## 📞 Support

### Health Check
```bash
curl http://localhost:5003/api/health
```

### Test Endpoint
```bash
curl -X POST http://localhost:5003/api/diary/test
```

### Logs
Check the terminal output for detailed logs including:
- Event processing status
- LLM generation progress
- Error details
- Performance metrics

---

## 🎉 Ready to Use!

The Simple Diary API is now ready for production use. It provides a clean, simple interface for processing events and generating diary entries based on your `events.json` configuration.

**Happy diary generation!** 📖✨
