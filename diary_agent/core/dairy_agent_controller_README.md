# Dairy Agent Controller

The `DairyAgentController` is the central orchestrator for the diary generation system. It manages system initialization, component coordination, event processing workflow, health monitoring, and error recovery.

## Overview

The controller serves as the main entry point for the diary agent system, coordinating all components to provide a complete end-to-end diary generation workflow. It implements the requirements specified in tasks 1.1, 1.2, 1.3, and 5.1.

## Key Features

### System Initialization and Component Coordination
- Initializes all system components in the correct order
- Manages dependencies between components
- Handles configuration loading and validation
- Sets up inter-component connections

### End-to-End Event Processing Workflow
- Receives and validates event data
- Routes events through condition checking
- Coordinates with sub-agents for diary generation
- Manages daily quota and event type constraints
- Handles event queuing and concurrent processing

### System Health Monitoring
- Continuous health monitoring of all components
- Component-level health status tracking
- Performance metrics collection
- Automatic detection of system issues

### Error Recovery
- Graceful error handling throughout the system
- Automatic retry mechanisms with exponential backoff
- Component restart capabilities
- System-wide restart functionality
- Emergency shutdown procedures

## Architecture

```
DairyAgentController
├── LLMConfigManager          # LLM provider management
├── SubAgentManager          # Sub-agent lifecycle management
├── EventRouter              # Event routing and classification
├── ConditionChecker         # Trigger condition evaluation
├── DiaryEntryGenerator      # Diary generation and formatting
└── DatabaseManager          # Database integration
```

## Usage

### Basic Usage

```python
from diary_agent.core.dairy_agent_controller import DairyAgentController

# Create controller
controller = DairyAgentController(
    config_dir="diary_agent/config",
    data_dir="diary_agent/data",
    log_level="INFO"
)

# Initialize and start system
await controller.initialize_system()
await controller.start_system()

# Process events
diary_entry = await controller.process_manual_event(
    event_name="favorite_weather",
    user_id=1,
    context_data={"weather": "sunny"}
)

# Stop system
await controller.stop_system()
```

### Convenience Functions

```python
from diary_agent.core.dairy_agent_controller import create_and_start_system

# Create and start system in one call
controller = await create_and_start_system(
    config_dir="diary_agent/config",
    data_dir="diary_agent/data"
)
```

### System Monitoring

```python
# Get system status
status = controller.get_system_status()
print(f"System health: {status['health_status']['system_status']}")

# Perform health check
health = await controller._perform_health_check()
print(f"Overall healthy: {health['overall_healthy']}")

# Get statistics
stats = controller.get_generation_stats()
print(f"Events processed: {stats['events_processed']}")
```

## Configuration

The controller requires several configuration files:

### Directory Structure
```
diary_agent/
├── config/
│   ├── llm_configuration.json      # LLM provider settings
│   ├── condition_rules.json        # Trigger conditions
│   └── agent_prompts/              # Agent prompt configurations
├── data/
│   └── diary_entries/              # Generated diary storage
└── events.json                     # Event type mappings
```

### LLM Configuration
```json
{
  "providers": {
    "qwen": {
      "provider_name": "qwen",
      "api_endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
      "api_key": "your-api-key",
      "model_name": "qwen-turbo",
      "max_tokens": 150,
      "temperature": 0.7,
      "timeout": 30,
      "retry_attempts": 3
    }
  }
}
```

## Event Processing Workflow

1. **Event Reception**: Events are received via `process_event()` or `process_manual_event()`
2. **Validation**: Event data is validated using `EventValidator`
3. **Condition Checking**: `ConditionChecker` evaluates if diary should be generated
4. **Event Routing**: `EventRouter` routes event to appropriate sub-agent
5. **Diary Generation**: Sub-agent generates diary entry using LLM
6. **Validation & Formatting**: Entry is validated and formatted according to specifications
7. **Storage**: Diary entry is stored to file system

## Daily Quota Management

The system implements daily quota management as specified in the requirements:

- **Daily Reset**: At 00:00, randomly determines 0-5 diary entries for the day
- **Claimed Events**: Certain events always generate diary entries
- **Random Selection**: For non-claimed events, randomly determines if diary should be written
- **Event Type Limits**: Only one diary entry per event type per day
- **No Make-up**: If insufficient events occur, no make-up writing required

## Health Monitoring

The controller continuously monitors system health:

### Component Health Checks
- **LLM Manager**: Provider availability and configuration
- **Sub-Agent Manager**: Agent health and success rates
- **Database Manager**: Connection status and query performance
- **Event Router**: Routing statistics and quota status
- **Diary Generator**: Generation success rates and error counts

### Recovery Mechanisms
- **Agent Restart**: Restart individual unhealthy agents
- **System Restart**: Full system restart if multiple components fail
- **Emergency Shutdown**: Immediate shutdown in critical situations

## Error Handling

### Error Categories
1. **Initialization Errors**: Component setup failures
2. **Processing Errors**: Event processing failures
3. **LLM Errors**: API failures and timeouts
4. **Database Errors**: Connection and query failures
5. **Validation Errors**: Data format and constraint violations

### Recovery Strategies
- **Retry with Backoff**: Exponential backoff for transient failures
- **Failover**: Switch to alternative providers/components
- **Graceful Degradation**: Continue with reduced functionality
- **Circuit Breaker**: Prevent cascade failures

## API Reference

### Core Methods

#### `initialize_system() -> bool`
Initialize all system components and establish connections.

#### `start_system() -> bool`
Start the diary generation system with all background tasks.

#### `stop_system()`
Gracefully stop the system and cleanup resources.

#### `process_event(event_data: EventData) -> Optional[DiaryEntry]`
Process a single event through the complete workflow.

#### `process_manual_event(event_name: str, user_id: int, context_data: dict) -> Optional[DiaryEntry]`
Process a manually triggered event.

### Monitoring Methods

#### `get_system_status() -> Dict[str, Any]`
Get comprehensive system status and statistics.

#### `get_supported_events() -> List[str]`
Get list of all supported event names.

#### `get_diary_entries(user_id: int, date: Optional[datetime]) -> List[DiaryEntry]`
Retrieve diary entries for a user.

### Management Methods

#### `restart_system() -> bool`
Restart the entire system.

#### `force_daily_reset()`
Force a daily quota reset (for testing/manual intervention).

#### `emergency_shutdown()`
Emergency shutdown of the system.

## Testing

The controller includes comprehensive integration tests:

```python
# Run tests
python -m pytest diary_agent/tests/test_dairy_agent_controller.py -v
```

### Test Coverage
- System initialization and startup
- Event processing workflow
- Health monitoring and recovery
- Daily quota management
- Error handling and resilience
- Component integration

## Examples

See `diary_agent/examples/dairy_agent_controller_example.py` for comprehensive usage examples including:

- Basic controller usage
- Event processing
- Health monitoring
- Daily quota management
- Error handling
- System monitoring with recovery

## Requirements Compliance

This implementation satisfies the following requirements:

### Requirement 1.1, 1.2, 1.3
- **Event Detection and Processing**: Automatically detects and processes different types of life events
- **Event Routing**: Routes events to appropriate sub-agents based on events.json mapping
- **Multiple Event Handling**: Processes multiple simultaneous events with specialized agents
- **Error Logging**: Logs unhandled events and continues processing

### Requirement 5.1
- **Trigger Conditions**: Activates appropriate sub-agents when trigger conditions are met
- **Condition Evaluation**: Uses ConditionChecker to evaluate trigger conditions
- **Monitoring Mode**: Remains in monitoring mode when conditions are not met
- **Image Processing**: Supports image input processing for event information extraction

## Performance Considerations

- **Concurrent Processing**: Supports multiple concurrent event processors
- **Async Operations**: All I/O operations are asynchronous
- **Resource Management**: Proper cleanup and resource management
- **Memory Efficiency**: Efficient memory usage for long-running processes
- **Scalability**: Designed to handle increasing event volumes

## Security Considerations

- **API Key Management**: Secure handling of LLM provider API keys
- **Input Validation**: Comprehensive validation of all input data
- **Error Information**: Careful handling of error information to prevent data leaks
- **Access Control**: Proper access control for system management functions

## Troubleshooting

### Common Issues

1. **Initialization Failures**
   - Check configuration file paths and formats
   - Verify LLM provider API keys and endpoints
   - Ensure database connectivity

2. **Event Processing Failures**
   - Check event data format and validation
   - Verify agent configurations and prompt files
   - Monitor LLM provider status

3. **Health Check Issues**
   - Review component logs for specific errors
   - Check system resource availability
   - Verify network connectivity for external services

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
controller = DairyAgentController(log_level="DEBUG")
```

## Future Enhancements

- **Metrics Dashboard**: Web-based monitoring dashboard
- **Configuration Hot-reload**: Dynamic configuration updates
- **Advanced Recovery**: Machine learning-based failure prediction
- **Performance Optimization**: Caching and optimization strategies
- **Distributed Processing**: Multi-node deployment support