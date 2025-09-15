# Daily Diary Generation Scheduler

The Daily Scheduler is the core component that implements the daily diary generation process as specified in `diary_agent_specifications_en.md`. It manages the complete workflow from daily quota determination to diary entry generation and storage.

## Overview

The scheduler implements the following key processes:

1. **Daily Quota Determination**: At 00:00 each day, randomly determines 0-5 diary entries to generate
2. **Event-Driven Generation**: When events occur, randomly determines if diary should be written
3. **Claimed Events Processing**: Certain events always result in diary entries
4. **Query Function System**: Calls corresponding query functions for event context
5. **Agent Routing**: Routes events to appropriate sub-agents for diary generation
6. **Daily Completion Tracking**: Tracks progress until daily quota is met
7. **One-Diary-Per-Type Constraint**: Ensures only one diary per event type per day

## Key Components

### DailyScheduler

Main scheduler class that orchestrates the entire diary generation workflow.

```python
from diary_agent.core.daily_scheduler import DailyScheduler, DailyScheduleConfig

# Configure scheduler
config = DailyScheduleConfig(
    schedule_time=time(0, 0),  # Reset at 00:00
    min_quota=0,
    max_quota=5,
    claimed_events_always_generate=True,
    random_selection_probability=0.6,
    alternative_approach_enabled=True
)

# Create scheduler
scheduler = DailyScheduler(
    event_router=event_router,
    sub_agent_manager=sub_agent_manager,
    diary_generator=diary_generator,
    data_persistence=data_persistence,
    config=config
)
```

### DailyScheduleConfig

Configuration class for scheduler behavior:

- `schedule_time`: Time to reset daily quota (default: 00:00)
- `min_quota`/`max_quota`: Range for random quota generation (0-5)
- `claimed_events_always_generate`: Whether claimed events bypass quota
- `random_selection_probability`: Probability for non-claimed events
- `alternative_approach_enabled`: Enable pre-selection of event types
- `storage_enabled`: Whether to store generated diary entries

### DiaryGenerationResult

Result object containing diary generation outcome:

```python
@dataclass
class DiaryGenerationResult:
    success: bool
    diary_entry: Optional[DiaryEntry] = None
    error_message: Optional[str] = None
    agent_type: Optional[str] = None
    event_type: Optional[str] = None
    generation_time: Optional[datetime] = None
```

## Usage

### Basic Setup

```python
import asyncio
from diary_agent.core.daily_scheduler import DailyScheduler

async def setup_scheduler():
    # Initialize components
    event_router = EventRouter("diary_agent/events.json")
    sub_agent_manager = SubAgentManager(llm_manager)
    diary_generator = DiaryEntryGenerator(llm_manager)
    data_persistence = DataPersistence()
    
    # Create scheduler
    scheduler = DailyScheduler(
        event_router=event_router,
        sub_agent_manager=sub_agent_manager,
        diary_generator=diary_generator,
        data_persistence=data_persistence
    )
    
    return scheduler
```

### Register Query Functions

Query functions provide event context for diary generation:

```python
async def weather_query_function(event_data: EventData) -> DiaryContextData:
    """Query weather data for diary context."""
    # Call weather_function.py to get weather context
    weather_data = weather_function.process_weather_event(
        event_data.user_id, 
        user_ip_address
    )
    
    return DiaryContextData(
        user_profile=weather_data["user_profile"],
        environmental_context=weather_data["weather_context"],
        # ... other context data
    )

# Register the function
scheduler.register_query_function("weather_events", weather_query_function)
```

### Process Events

```python
async def process_event(scheduler, event_data):
    # Process event and potentially generate diary
    result = await scheduler.process_event(event_data)
    
    if result.success and result.diary_entry:
        print(f"Generated diary: {result.diary_entry.title}")
        print(f"Content: {result.diary_entry.content}")
    else:
        print(f"Event skipped or failed: {result.error_message}")
```

### Start/Stop Scheduler

```python
async def run_scheduler():
    scheduler = await setup_scheduler()
    
    # Start continuous scheduling
    await scheduler.start_scheduler()
    
    try:
        # Process events as they occur
        while True:
            # Your event detection logic here
            await asyncio.sleep(60)  # Check every minute
    finally:
        # Stop scheduler
        await scheduler.stop_scheduler()
```

## Daily Process Flow

### 1. Daily Quota Reset (00:00)

```python
# Automatically triggered at 00:00
await scheduler._reset_daily_quota()

# Manual reset for testing
await scheduler._reset_daily_quota()
print(f"New quota: {scheduler.current_quota.total_quota}")
```

### 2. Event Processing

When an event occurs:

1. **Event Validation**: Validate event data structure
2. **Quota Check**: Check if diary can be generated (quota remaining, event type not processed)
3. **Claimed Event Check**: Always generate for claimed events
4. **Random Selection**: For non-claimed events, randomly decide based on probability
5. **Query Function Call**: Get event context using registered query function
6. **Agent Routing**: Route to appropriate sub-agent for diary generation
7. **Validation & Formatting**: Ensure 6-char title, 35-char content
8. **Storage**: Store diary entry if enabled
9. **Quota Update**: Update daily quota and completed event types

### 3. Alternative Approach

When enabled, pre-selects event types at quota reset:

```python
# Get available event types for today
available_types = scheduler.event_router.get_available_event_types_for_today()

# Randomly select types up to quota
selected_types = scheduler.event_router.select_random_event_types_for_today()
```

## Monitoring and Status

### Daily Status

```python
status = scheduler.get_daily_status()
print(f"Quota: {status['quota']['current']}/{status['quota']['total']}")
print(f"Completed types: {status['completed_event_types']}")
print(f"Is complete: {status['is_complete']}")
```

### Generation History

```python
history = scheduler.get_generation_history(limit=10)
for entry in history:
    print(f"Agent: {entry['agent_type']}, Success: {entry['success']}")
```

### Statistics

```python
stats = scheduler.daily_stats
print(f"Total events: {stats['total_events_processed']}")
print(f"Diaries generated: {stats['diaries_generated']}")
print(f"Failed generations: {stats['failed_generations']}")
```

## Diary Entry Formatting

The scheduler ensures all diary entries meet the specifications:

- **Title**: Maximum 6 characters (considering Unicode width)
- **Content**: Maximum 35 characters (emoji support)
- **Emotional Tags**: Selected from predefined 10 emotions
- **Timestamp**: Event occurrence time
- **Agent Type**: Sub-agent that generated the entry

```python
# Example formatted diary entry
DiaryEntry(
    entry_id="diary_001",
    user_id=1,
    timestamp=datetime.now(),
    event_type="weather_events",
    event_name="favorite_weather",
    title="晴天",  # 6 chars max
    content="今天天气很好，心情愉快😊",  # 35 chars max
    emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
    agent_type="weather_agent",
    llm_provider="qwen"
)
```

## Error Handling

The scheduler includes comprehensive error handling:

- **Event Validation Errors**: Invalid event data structure
- **Routing Failures**: No agent available for event type
- **Generation Failures**: LLM or agent processing errors
- **Storage Failures**: Database or file system errors
- **Quota Exceeded**: Daily limit reached

```python
result = await scheduler.process_event(event_data)
if not result.success:
    logger.error(f"Event processing failed: {result.error_message}")
    # Handle error appropriately
```

## Testing

Run the comprehensive test suite:

```bash
python -m pytest diary_agent/tests/test_daily_scheduler.py -v
```

Key test scenarios:
- Daily quota reset and determination
- Event processing with various conditions
- Claimed vs non-claimed event handling
- Query function registration and calling
- Diary entry formatting and validation
- Error handling and recovery
- Alternative approach event type selection

## Integration

The scheduler integrates with existing hewan_emotion_cursor_python modules:

- **weather_function.py**: Weather and seasonal events
- **douyin_news.py**: Trending and news events
- **holiday_function.py**: Holiday-related events
- **friends_function.py**: Friend interaction events
- **same_frequency.py**: Synchronization events
- **adopted_function.py**: Claiming/adoption events
- **human_toy_interactive_function.py**: Human-toy interactions
- **human_toy_talk.py**: Dialogue events
- **unkeep_interactive.py**: Neglect tracking events

Each integration uses read-only data access to maintain separation from the existing emotion calculation system.

## Configuration Files

The scheduler uses several configuration files:

- `config/llm_configuration.json`: LLM provider settings
- `diary_agent/config/agent_prompts/*.json`: Agent-specific prompts
- `diary_agent/events.json`: Event type mappings
- `diary_agent/config/condition_rules.json`: Trigger conditions

## Performance Considerations

- **Async Processing**: All operations are asynchronous for better performance
- **Batch Processing**: Can handle multiple events efficiently
- **Memory Management**: Clears daily results at quota reset
- **Error Recovery**: Continues processing other events on individual failures
- **Configurable Retries**: Adjustable retry attempts for failed operations

## Logging

The scheduler provides detailed logging for monitoring and debugging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Scheduler logs include:
# - Daily quota resets
# - Event processing results
# - Query function calls
# - Agent routing decisions
# - Diary generation outcomes
# - Error conditions and recovery
```