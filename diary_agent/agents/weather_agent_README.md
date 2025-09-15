# Weather Agent Implementation

## Overview

The Weather Agent is a specialized sub-agent that generates diary entries for weather and seasonal events. It integrates with the existing `weather_function.py` module to read weather data, user preferences, and emotion calculations while maintaining complete separation from the emotion calculation system.

## Components

### WeatherAgent

Handles weather-related diary entries for events:
- `favorite_weather`: When user's preferred weather conditions occur
- `dislike_weather`: When user's disliked weather conditions occur
- `favorite_season`: When user's preferred season arrives
- `dislike_season`: When user's disliked season arrives

### SeasonalAgent

Specialized agent for seasonal events, inheriting from WeatherAgent:
- `favorite_season`: User's favorite season events
- `dislike_season`: User's disliked season events

### WeatherDataReader

Read-only data adapter that interfaces with existing `weather_function.py`:
- Reads user preferences from emotion database
- Gets current weather from WeatherAPI.com
- Determines current season based on month
- Calculates emotional context without modifying emotion database
- Provides weather descriptions in Chinese

## Integration with Existing System

### Data Flow
```
Event Occurs → WeatherDataReader → weather_function.py → Weather Data
                     ↓
            WeatherAgent → LLM → Diary Entry
```

### Preserved Functionality
- **WeatherAPI.com Integration**: Uses existing API key and endpoints
- **Role-based Weights**: Maintains "clam" and "lively" personality calculations
- **IP Geolocation**: Uses existing `ip_lookup.py` for city determination
- **Database Schema**: Compatible with existing emotion database structure
- **Emotion Calculations**: Reads but doesn't modify existing emotion logic

### Separation of Concerns
- **Emotion System**: Continues to operate independently, handling all emotion calculations and database updates
- **Diary System**: Focuses solely on reading event data and generating diary entries
- **No Interference**: Diary generation doesn't affect existing emotion calculation workflows

## Configuration

### Prompt Configuration
Located in `diary_agent/config/agent_prompts/weather_agent.json`:
- Chinese language prompts for authentic diary generation
- Specific formatting requirements (6-char titles, 35-char content)
- Emotion tag selection from predefined Chinese emotions
- Weather-specific context integration

### Emotional Tag Mapping
Based on event type and preference matching:
- **Favorite + Match**: 兴奋激动 (Excited) or 开心快乐 (Happy)
- **Favorite + No Match**: 平静 (Calm)
- **Dislike + Match**: 生气愤怒 (Angry) or 悲伤难过 (Sad)
- **Dislike + No Match**: 平静 (Calm)

Intensity determined by user role:
- **Clam**: Lower emotional intensity (weights: favorite 1.0, dislike 0.5)
- **Lively**: Higher emotional intensity (weights: favorite 1.5, dislike 1.0)

## Usage Example

```python
from diary_agent.agents.weather_agent import WeatherAgent
from diary_agent.integration.weather_data_reader import WeatherDataReader
from diary_agent.utils.data_models import EventData

# Initialize components
data_reader = WeatherDataReader()
weather_agent = WeatherAgent(
    agent_type="weather_agent",
    prompt_config=prompt_config,
    llm_manager=llm_manager,
    data_reader=data_reader
)

# Create weather event
event_data = EventData(
    event_id="weather_001",
    event_type="weather",
    event_name="favorite_weather",
    timestamp=datetime.now(),
    user_id=1,
    context_data={},
    metadata={"user_ip": "8.8.8.8"}
)

# Generate diary entry
diary_entry = await weather_agent.process_event(event_data)
```

## Testing

Comprehensive test suite in `diary_agent/tests/test_weather_agent.py`:
- **WeatherDataReader Tests**: Context reading, user preferences, event analysis
- **WeatherAgent Tests**: Event processing, emotion tag selection, fallback content
- **SeasonalAgent Tests**: Inheritance verification, supported events
- **Integration Tests**: End-to-end workflow with mocked dependencies

Run tests:
```bash
python -m pytest diary_agent/tests/test_weather_agent.py -v
```

## Error Handling

### Graceful Degradation
- **Weather API Failure**: Uses fallback weather data
- **User Not Found**: Creates minimal context with defaults
- **LLM Failure**: Generates fallback content using templates
- **Validation Failure**: Creates simple, compliant diary entries

### Fallback Content
When LLM generation fails, the agent generates simple weather-based content:
- Weather events: "今天是{weather}，心情很好😊" or "今天{weather}，有点不开心😔"
- Season events: "{season}来了，很喜欢这个季节🌸" or "{season}又来了，不太喜欢😞"

## File Structure

```
diary_agent/
├── agents/
│   ├── weather_agent.py          # WeatherAgent and SeasonalAgent classes
│   └── weather_agent_README.md   # This documentation
├── integration/
│   └── weather_data_reader.py    # Data reader for weather_function.py
├── config/agent_prompts/
│   ├── weather_agent.json        # Weather agent prompt configuration
│   └── seasonal_agent.json       # Seasonal agent prompt configuration
├── tests/
│   └── test_weather_agent.py     # Comprehensive test suite
└── examples/
    └── weather_agent_example.py  # Usage demonstration
```

## Requirements Fulfilled

This implementation satisfies the following requirements from the specification:

- **3.1, 3.2**: Weather and seasonal sub-agents with specialized processing
- **7.1-7.8**: Weather agent handles specific weather preference events with proper emotion calculation integration
- **Integration**: Preserves existing WeatherAPI.com integration, IP geolocation, and role-based weight calculations
- **Diary Generation**: Uses existing emotion calculation results for context without modifying the emotion system
- **Prompt Templates**: Weather-specific prompts incorporating weather data, city information, and emotional context
- **Testing**: Comprehensive unit tests for weather agent integration and diary generation