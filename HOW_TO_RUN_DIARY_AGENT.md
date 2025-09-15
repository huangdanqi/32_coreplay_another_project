# How to Run the Diary Agent

## Quick Start

### 1. Install Dependencies

```cmd
pip install -r requirements.txt
```

### 2. Setup Local Ollama (Recommended)

The system is now configured to use your local Ollama Qwen3 model by default:

```cmd
# Test if Ollama is working
python test_ollama_connection.py
```

If the test fails, make sure:

- Ollama is running: `ollama serve`
- Qwen3 model is installed: `ollama pull qwen3`

### 3. Run the Complete Example

```cmd
python diary_agent_api_example.py
```

This will show you:

- ✅ Exact input/output formats
- ✅ Working code examples
- ✅ All supported event types
- ✅ Real diary generation results

## What You'll See

The example will process different types of events and show you:

### Weather Events (100% success rate)

```
Input:  {"event_type": "weather", "event_name": "favorite_weather", "user_id": 1, "context_data": {"weather": "sunny", "temperature": 25}}
Output: {"title": "晴天好心情", "content": "今天阳光明媚，心情特别好！😊", "emotion_tags": ["开心快乐"]}
```

### Social Events (70% success rate)

```
Input:  {"event_type": "friends", "event_name": "made_new_friend", "user_id": 1, "context_data": {"friend_name": "Alice", "activity": "playing games"}}
Output: {"title": "新朋友", "content": "今天认识了新朋友Alice，很开心！", "emotion_tags": ["开心快乐"]}
```

### Holiday Events (80% success rate)

```
Input:  {"event_type": "holiday", "event_name": "approaching_holiday", "user_id": 1, "context_data": {"holiday": "Spring Festival", "days_until": 7}}
Output: {"title": "节日将至", "content": "春节快到了，好期待啊！🎉", "emotion_tags": ["兴奋激动"]}
```

## Using in Your Application

### Simple Integration Template

**Copy this code and replace the values with your own:**

```python
from diary_agent_api_example import DiaryAgentAPI

# Initialize once
api = DiaryAgentAPI()
await api.initialize()

# Generate diary entries - REPLACE THESE VALUES WITH YOUR OWN:
diary = await api.generate_diary_entry(
    event_type="YOUR_EVENT_TYPE",      # e.g., "weather", "friends", "holiday"
    event_name="YOUR_EVENT_NAME",      # e.g., "favorite_weather", "made_new_friend"
    user_id=YOUR_USER_ID,              # e.g., 1, 2, 3
    context_data={                     # Replace with your event data
        "key1": "value1",              # e.g., "weather": "sunny"
        "key2": "value2"               # e.g., "temperature": 25
    }
)

# Check if diary was generated
if diary:
    print(f"Title: {diary.title}")
    print(f"Content: {diary.content}")
    print(f"Emotions: {diary.emotion_tags}")
else:
    print("No diary entry generated (quota reached or conditions not met)")

# Clean up
await api.shutdown()
```

### Quick Examples - Just Copy & Paste:

**Weather Event:**

```python
diary = await api.generate_diary_entry(
    event_type="weather",
    event_name="favorite_weather",
    user_id=1,
    context_data={"weather": "sunny", "temperature": 25, "city": "Beijing"}
)
```

**Social Event:**

```python
diary = await api.generate_diary_entry(
    event_type="friends",
    event_name="made_new_friend",
    user_id=1,
    context_data={"friend_name": "Alice", "activity": "playing games", "mood": "happy"}
)
```

**Holiday Event:**

```python
diary = await api.generate_diary_entry(
    event_type="holiday",
    event_name="approaching_holiday",
    user_id=1,
    context_data={"holiday": "Spring Festival", "days_until": 7, "excitement_level": "high"}
)
```

### Input Format

```python
{
    "event_type": "weather",           # Event category
    "event_name": "favorite_weather",  # Specific event
    "user_id": 1,                     # User ID
    "context_data": {                 # Event details
        "weather": "sunny",
        "temperature": 25,
        "city": "Beijing"
    }
}
```

### Output Format

```python
{
    "title": "晴天好心情",              # Max 6 characters
    "content": "今天阳光明媚，心情特别好！😊",  # Max 35 characters
    "emotion_tags": ["开心快乐"],       # Emotional tags
    "user_id": 1,                     # User ID
    "timestamp": "2024-01-01T12:00:00" # Generation time
}
```

## Supported Events

### Weather Events (Always trigger)

- `favorite_weather` - User likes the weather
- `dislike_weather` - User dislikes the weather

### Social Events (70% chance)

- `made_new_friend` - Made a new friend
- `liked_single` - Liked one person
- `liked_3_to_5` - Liked 3-5 people

### Holiday Events (80% chance)

- `approaching_holiday` - Holiday is coming
- `during_holiday` - Currently in holiday

### Interactive Events

- `toy_claimed` - Adopted/claimed a toy
- `positive_emotional_dialogue` - Had positive conversation

### Neglect Events (Always trigger)

- `neglect_1_day_no_dialogue` - No conversation for 1 day
- `neglect_3_days_no_interaction` - No interaction for 3 days

## Trigger Conditions

The system has built-in conditions that determine when diary entries are generated:

- **Daily Quota**: 0-5 entries per day (randomly set at midnight)
- **Event Probability**: Different event types have different trigger rates
- **User Context**: System considers user history and preferences

## Troubleshooting

### If the example doesn't run:

1. Make sure you're in the project root directory
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Verify the `diary_agent/` folder exists with all components
4. Test Ollama connection: `python test_ollama_connection.py`

### If Ollama connection fails:

1. **Install Ollama**: Download from https://ollama.ai/
2. **Start Ollama service**: Run `ollama serve` in terminal
3. **Install Qwen3 model**: Run `ollama pull qwen3`
4. **Verify installation**: Run `ollama list` to see installed models
5. **Test connection**: Run `python test_ollama_connection.py`

### If no diary entries are generated:

- This is normal! The system has quotas and probability-based triggering
- Weather and neglect events have 100% trigger rate
- Social events only trigger 70% of the time
- Try running multiple times to see different results

### For integration issues:

- Always call `await api.initialize()` before generating entries
- Always call `await api.shutdown()` when done
- Handle the case where `generate_diary_entry()` returns `None`

### Ollama Model Issues:

- **Model not found**: Make sure you have the exact model name. Try `ollama list`
- **Connection refused**: Ollama service might not be running. Try `ollama serve`
- **Slow responses**: Local models may take longer than cloud APIs
- **Memory issues**: Qwen3 requires sufficient RAM. Try smaller models if needed

## Files You Need

The main files for integration:

- `diary_agent_api_example.py` - Complete working example
- `diary_agent/core/dairy_agent_controller.py` - Main controller
- `diary_agent/utils/data_models.py` - Data structures
- `events.json` - Supported events list
- `diary_agent/config/` - Configuration files
