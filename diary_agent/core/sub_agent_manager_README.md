# SubAgentManager

The SubAgentManager is the central component responsible for managing the lifecycle of all diary generation sub-agents in the system. It handles agent initialization, configuration loading, failure handling, and retry logic.

## Features

- **Agent Lifecycle Management**: Initialize, restart, and shutdown agents
- **Configuration Management**: Load and reload agent configurations dynamically
- **Failure Handling**: Automatic retry with exponential backoff
- **Health Monitoring**: Track agent health and performance metrics
- **Event Routing**: Route events to appropriate agents
- **Data Reader Integration**: Manage data readers for existing module integration

## Architecture

```
SubAgentManager
├── AgentRegistry (manages agent instances)
├── AgentFactory (creates agent instances)
├── Data Readers (integration with existing modules)
├── Health Monitoring (tracks agent status)
└── Configuration Management (loads/reloads configs)
```

## Usage

### Basic Initialization

```python
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.llm_manager import LLMConfigManager

# Initialize LLM manager
llm_manager = LLMConfigManager("config/llm_configuration.json")

# Initialize SubAgentManager
manager = SubAgentManager(
    llm_manager=llm_manager,
    config_dir="diary_agent/config",
    max_retry_attempts=3,
    retry_delay=1.0
)

# Initialize all agents
success = await manager.initialize_agents()
```

### Event Processing

```python
from diary_agent.utils.data_models import EventData
from datetime import datetime

# Create event data
event = EventData(
    event_id="weather_001",
    event_type="weather", 
    event_name="favorite_weather",
    timestamp=datetime.now(),
    user_id=1,
    context_data={"weather": "sunny"},
    metadata={}
)

# Process event with automatic retry
diary_entry = await manager.process_event_with_retry(event)
```

### Health Monitoring

```python
# Get system status
status = manager.get_system_status()
print(f"Healthy agents: {status['healthy_agents']}/{status['total_agents']}")
print(f"Success rate: {status['success_rate']}%")

# Get specific agent health
health = manager.get_agent_health("weather_agent")
print(f"Status: {health['status']}")
print(f"Requests: {health['total_requests']}")
```

### Agent Management

```python
# List all agents
agents = manager.list_agents()
print(f"Active agents: {agents}")

# List supported events
events = manager.list_supported_events()
print(f"Supported events: {events}")

# Restart specific agent
success = await manager.restart_agent("weather_agent")

# Restart all unhealthy agents
results = await manager.restart_unhealthy_agents()
```

### Configuration Management

```python
# Reload all configurations
manager.reload_configurations()

# Get agent for specific event
agent = manager.get_agent_for_event("favorite_weather")
if agent:
    print(f"Handler: {agent.get_agent_type()}")
```

## Configuration Files

### Agent Configuration (`agent_configuration.json`)

```json
{
  "agents": {
    "weather_agent": {
      "class_name": "WeatherAgent",
      "module_path": "diary_agent.agents.weather_agent",
      "data_reader": "weather_data_reader",
      "enabled": true,
      "priority": 1
    },
    "trending_agent": {
      "class_name": "TrendingAgent",
      "module_path": "diary_agent.agents.trending_agent", 
      "data_reader": "trending_data_reader",
      "enabled": true,
      "priority": 2
    }
  }
}
```

### LLM Configuration (`llm_configuration.json`)

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

## Agent Types and Data Readers

| Agent Type | Data Reader | Supported Events |
|------------|-------------|------------------|
| weather_agent | weather_data_reader | favorite_weather, dislike_weather, favorite_season, dislike_season |
| trending_agent | trending_data_reader | celebration, disaster |
| holiday_agent | holiday_data_reader | approaching_holiday, during_holiday, holiday_ends |
| friends_agent | friends_data_reader | made_new_friend, friend_deleted, liked_single, etc. |
| same_frequency_agent | frequency_data_reader | close_friend_frequency |
| adoption_agent | adoption_data_reader | toy_claimed |
| interactive_agent | interaction_data_reader | liked_interaction_once, etc. |
| dialogue_agent | dialogue_data_reader | positive_emotional_dialogue, negative_emotional_dialogue |
| neglect_agent | neglect_data_reader | neglect_1_day_no_dialogue, etc. |

## Error Handling

The SubAgentManager implements comprehensive error handling:

- **Retry Logic**: Exponential backoff for failed operations
- **Failover**: Automatic switching between LLM providers
- **Health Tracking**: Monitor agent status and performance
- **Graceful Degradation**: Continue operating with reduced functionality
- **Recovery**: Automatic restart of failed agents

## Health Metrics

Each agent tracks the following health metrics:

- `status`: "healthy" or "unhealthy"
- `total_requests`: Total number of requests processed
- `successful_requests`: Number of successful requests
- `failed_requests`: Number of failed requests
- `last_success`: Timestamp of last successful operation
- `last_failure`: Timestamp of last failure

## Best Practices

1. **Initialize Early**: Initialize the SubAgentManager during system startup
2. **Monitor Health**: Regularly check agent health status
3. **Handle Failures**: Implement proper error handling for event processing
4. **Configuration Management**: Use configuration files for easy updates
5. **Graceful Shutdown**: Always call shutdown() during system termination

## Example

See `diary_agent/examples/sub_agent_manager_example.py` for a complete usage example.

## Requirements

The SubAgentManager requires the following components:

- Requirements 4.1: Agent initialization and configuration loading
- Requirements 4.2: Agent failure handling and retry logic  
- Requirements 4.3: Sub-agent management scenarios

## Testing

Run the test suite:

```bash
python -m pytest diary_agent/tests/test_sub_agent_manager.py -v
```

The test suite covers:

- Agent initialization and configuration
- Event processing with retry logic
- Health monitoring and status tracking
- Agent restart and recovery
- Configuration management
- Error handling scenarios