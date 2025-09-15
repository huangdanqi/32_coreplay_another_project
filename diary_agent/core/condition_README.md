# ConditionChecker Implementation

## Overview

The `ConditionChecker` class is a core component of the diary agent system that evaluates trigger conditions for diary generation. It determines when diary entries should be created based on various types of conditions including event-based, time-based, and image-based triggers.

## Features

### 1. Multiple Condition Types
- **Event-based**: Triggers based on specific event types and names
- **Time-based**: Triggers at specific times or time ranges
- **Image-based**: Triggers based on image analysis and event detection
- **Claimed Events**: Events that must always result in diary entries

### 2. Daily Quota Management
- Supports daily diary generation quotas (0-5 entries per day)
- Tracks completed event types to prevent duplicates
- Enforces one diary entry per event type per day

### 3. Probability-based Triggering
- Each condition can have a probability (0.0-1.0) for triggering
- Allows for random diary generation based on configured probabilities

### 4. Configuration Management
- Loads conditions from JSON configuration files
- Supports hot-reloading of condition configurations
- Provides default conditions if no configuration is provided

### 5. Image Processing
- Basic image processing capabilities for event detection
- Supports multiple image formats (base64, bytes, PIL Image)
- Extensible for integration with computer vision models

## Usage

### Basic Initialization

```python
from diary_agent.core.condition import ConditionChecker

# Initialize with default conditions
checker = ConditionChecker()

# Initialize with configuration file
checker = ConditionChecker("config/condition_rules.json")
```

### Setting Daily Quota

```python
from diary_agent.utils.data_models import DailyQuota
from datetime import datetime

quota = DailyQuota(
    date=datetime.now(),
    total_quota=3,  # Allow 3 diary entries today
    current_count=0
)
checker.set_daily_quota(quota)
```

### Registering Event Handlers

```python
def weather_handler(event_data):
    print(f"Processing weather event: {event_data.event_name}")

checker.register_event_handler("weather", weather_handler)
```

### Evaluating Conditions

```python
from diary_agent.utils.data_models import EventData
from datetime import datetime

event = EventData(
    event_id="weather_001",
    event_type="weather",
    event_name="favorite_weather",
    timestamp=datetime.now(),
    user_id=1,
    context_data={"temperature": 25, "condition": "sunny"},
    metadata={"source": "weather_api"}
)

# Check if conditions are met
if checker.evaluate_conditions(event):
    # Trigger diary generation
    checker.trigger_diary_generation(event)
```

## Configuration Format

The condition configuration file uses JSON format:

```json
{
  "trigger_conditions": [
    {
      "condition_id": "weather_events",
      "condition_type": "event_based",
      "event_types": ["weather", "seasonal"],
      "probability": 1.0,
      "is_active": true,
      "metadata": {
        "description": "Always trigger for weather events",
        "priority": "high"
      }
    }
  ],
  "claimed_events": [
    {
      "event_type": "weather",
      "event_name": "favorite_weather",
      "is_claimed": true
    }
  ]
}
```

## Condition Types

### Event-based Conditions
- Trigger when specific event types occur
- Support probability-based random triggering
- Can match multiple event types

### Time-based Conditions
- Trigger at specific times or time ranges
- Support time ranges that cross midnight
- Useful for daily quota resets and scheduled operations

### Image-based Conditions
- Process images to detect events
- Extract event information from visual data
- Extensible for computer vision integration

### Claimed Events
- Events that must always generate diary entries
- Bypass probability and quota restrictions
- Ensure important events are never missed

## Requirements Satisfied

This implementation satisfies the following requirements:

- **5.1**: ✅ Activates appropriate sub-agents when trigger conditions are met
- **5.2**: ✅ Begins event processing when condition.py evaluates to true
- **5.3**: ✅ Remains in monitoring mode when trigger conditions are not met
- **5.4**: ✅ Extracts relevant event information from image inputs for diary generation

## Testing

The implementation includes comprehensive unit tests covering:

- Condition initialization and configuration loading
- Daily quota management and checking
- Event-based, time-based, and image-based condition evaluation
- Claimed event detection
- Event handler registration and triggering
- Condition status management
- Image processing capabilities

Run tests with:
```bash
python -m pytest diary_agent/tests/test_condition_checker.py -v
```

## Integration

The ConditionChecker integrates with other diary agent components:

- **Event Router**: Receives events for condition evaluation
- **Sub-Agent Manager**: Triggers appropriate agents when conditions are met
- **Daily Scheduler**: Manages daily quotas and resets
- **LLM Manager**: Coordinates with AI providers for diary generation

## Future Enhancements

Potential improvements for the ConditionChecker:

1. **Advanced Image Processing**: Integration with computer vision models for better event detection
2. **Machine Learning**: Use ML models to learn optimal trigger probabilities
3. **Real-time Monitoring**: Continuous monitoring of system events and conditions
4. **Performance Optimization**: Caching and optimization for high-frequency event processing
5. **Advanced Scheduling**: More sophisticated time-based condition patterns