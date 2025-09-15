# EventRouter Documentation

## Overview

The `EventRouter` is a central component of the diary agent system that handles event routing and classification. It routes incoming events to appropriate sub-agents based on event type classification from `events.json`, manages daily diary generation quotas, and implements the query function calling system.

## Key Features

### 1. Event Type Classification
- Automatically classifies events based on `events.json` configuration
- Maps events to appropriate sub-agent types
- Validates event data structure and metadata

### 2. Query Function Calling System
- Calls corresponding query functions as input parameters per specifications
- Retrieves event context from existing modules (weather_function.py, douyin_news.py, etc.)
- Provides standardized context data for diary generation

### 3. Claimed Events Identification
- Identifies events that must always result in diary entries
- Processes claimed events regardless of daily quota constraints
- Currently includes: `toy_claimed` (adoption events)

### 4. Random Diary Selection Logic
- Implements probability-based selection for non-claimed events
- Respects daily quota limits (0-5 diary entries per day)
- Ensures only one diary entry per event type per day

### 5. Agent Routing
- Routes events to registered sub-agents for processing
- Handles agent failures and provides error recovery
- Updates daily quota when diary entries are generated

## Architecture

```
Event → EventRouter → Classification → Query Function → Sub-Agent → Diary Entry
                   ↓
              Daily Quota Check
                   ↓
              Claimed Event Check
                   ↓
              Random Selection
```

## Usage

### Basic Setup

```python
from diary_agent.core.event_router import EventRouter
from diary_agent.utils.data_models import EventData, DailyQuota

# Initialize router with events.json
router = EventRouter("diary_agent/events.json")

# Set daily quota (0-5 entries per day)
daily_quota = DailyQuota(
    date=date.today(),
    total_quota=3,
    current_count=0
)
router.update_daily_quota(daily_quota)
```

### Register Agents and Query Functions

```python
# Register sub-agents
router.register_agent("weather_agent", weather_agent_instance)
router.register_agent("friends_agent", friends_agent_instance)

# Register query functions for event context
router.register_query_function("weather_events", weather_query_function)
router.register_query_function("friends_function", friends_query_function)
```

### Process Events

```python
# Create event data
event_data = EventData(
    event_id="event_001",
    event_type="weather_events",
    event_name="favorite_weather",
    timestamp=datetime.now(),
    user_id=1,
    context_data={"weather_type": "sunny"},
    metadata={"source": "weather_sensor"}
)

# Route event for processing
result = router.route_event(event_data)

if result["success"]:
    if result.get("diary_generated"):
        diary_entry = result["diary_entry"]
        print(f"Generated: {diary_entry.title} - {diary_entry.content}")
    else:
        print(f"Event skipped: {result.get('reason', 'Unknown')}")
else:
    print(f"Error: {result['error']}")
```

## Event Processing Workflow

### 1. Event Validation
- Validates event data structure using `EventValidator`
- Checks required fields: event_id, event_type, event_name, user_id, timestamp

### 2. Event Classification
- Determines event type from `events.json` mapping
- Maps to appropriate sub-agent type
- Parses and validates event metadata

### 3. Diary Generation Decision
- **Claimed Events**: Always generate diary entries
- **Non-Claimed Events**: Check daily quota and use probability-based selection
- **Quota Constraints**: Respect daily limits and one-per-event-type rule

### 4. Query Function Call
- Calls registered query function for event type
- Retrieves context data from existing modules
- Provides standardized `DiaryContextData` format

### 5. Agent Routing
- Routes to appropriate registered sub-agent
- Passes event data and context data to agent
- Handles agent processing errors

### 6. Quota Management
- Updates daily quota when diary is generated
- Tracks completed event types
- Prevents duplicate diary entries for same event type

## Event Type Mappings

Based on `events.json`, the following mappings are supported:

| Event Type | Agent Type | Source Module |
|------------|------------|---------------|
| weather_events | weather_agent | weather_function.py |
| seasonal_events | weather_agent | weather_function.py |
| trending_events | trending_agent | douyin_news.py |
| holiday_events | holiday_agent | holiday_function.py |
| friends_function | friends_agent | friends_function.py |
| same_frequency | same_frequency_agent | same_frequency.py |
| adopted_function | adoption_agent | adopted_function.py |
| human_toy_interactive_function | interactive_agent | human_toy_interactive_function.py |
| human_toy_talk | dialogue_agent | human_toy_talk.py |
| unkeep_interactive | neglect_agent | unkeep_interactive.py |

## Daily Quota Management

### Quota Rules
- **Daily Initialization**: Randomly determine 0-5 diary entries at 00:00
- **Claimed Events**: Always processed regardless of quota
- **Event Type Limit**: Only one diary per event type per day
- **Random Selection**: Probability-based selection for non-claimed events

### Quota Operations

```python
# Reset daily quota (typically at 00:00)
router.reset_daily_quota()  # Random 0-5
router.reset_daily_quota(3)  # Specific quota

# Check available event types
available_types = router.get_available_event_types_for_today()

# Alternative approach: randomly select event types
selected_types = router.select_random_event_types_for_today()

# Get quota statistics
stats = router.get_routing_statistics()
print(f"Quota: {stats['daily_quota']['current_count']}/{stats['daily_quota']['total_quota']}")
```

## Error Handling

### Event Validation Errors
- Invalid event data structure
- Missing required fields
- Unknown event names

### Routing Errors
- Unregistered agents
- Agent processing failures
- Query function errors

### Quota Errors
- Daily quota exceeded
- Event type already processed

### Error Response Format

```python
{
    "success": False,
    "error": "Error description",
    "event_id": "event_001"
}
```

## Monitoring and Statistics

### Routing Statistics

```python
stats = router.get_routing_statistics()
# Returns:
{
    "daily_quota": {
        "date": "2024-01-01",
        "total_quota": 3,
        "current_count": 1,
        "completed_event_types": ["weather_events"]
    },
    "registered_agents": ["weather_agent", "friends_agent"],
    "registered_query_functions": ["weather_events", "friends_function"],
    "available_event_types": [...],
    "claimed_events": ["toy_claimed"]
}
```

## Integration with Existing Modules

The EventRouter integrates with existing `hewan_emotion_cursor_python` modules through:

### Query Functions
- **Read-only access** to existing module outputs
- **No modification** of emotion calculation logic
- **Context extraction** for diary generation

### Data Flow
```
Existing Module → Query Function → EventRouter → Sub-Agent → Diary Entry
     ↓                                ↑
Emotion Calculation          Context Data Only
(Independent)               (Read-only)
```

## Testing

Comprehensive unit tests are available in `diary_agent/tests/test_event_router.py`:

```bash
# Run all EventRouter tests
python -m pytest diary_agent/tests/test_event_router.py -v

# Run specific test categories
python -m pytest diary_agent/tests/test_event_router.py::TestEventRouter::test_route_event_full_workflow_success -v
```

## Example Usage

See `diary_agent/examples/event_router_example.py` for complete usage examples including:
- Setting up EventRouter with agents and query functions
- Processing different event types
- Handling claimed vs non-claimed events
- Managing daily quotas
- Error handling scenarios

## Configuration

### Events Configuration
The EventRouter uses `diary_agent/events.json` for event type mappings. This file defines:
- Event type categories
- Event names within each category
- Mapping to source modules

### Agent Registration
Sub-agents must be registered with their corresponding agent type:
```python
router.register_agent("weather_agent", WeatherAgent())
```

### Query Function Registration
Query functions must be registered for each event type:
```python
router.register_query_function("weather_events", weather_query_function)
```

## Best Practices

1. **Always validate events** before routing
2. **Handle agent failures** gracefully
3. **Monitor daily quotas** to prevent overgeneration
4. **Use claimed events** for critical diary entries
5. **Implement proper error logging** for debugging
6. **Test with various event scenarios** to ensure robustness

## Future Enhancements

- Dynamic agent loading and unloading
- Advanced probability algorithms for event selection
- Event priority system
- Batch event processing
- Real-time quota adjustment based on user activity