# Diary Agent

A flexible diary generation agent that supports two modes:
1. **LLM-based generation** - Uses AI language models to generate personalized diary entries
2. **Default content generation** - Uses predefined templates for consistent, reliable output

## Features

- **Dual Mode Support**: Switch between LLM and default content generation
- **Multiple Event Types**: Supports 12 different diary event types
- **Emotion Tagging**: Automatically assigns appropriate emotional tags
- **Validation**: Ensures content meets length and format requirements
- **Fallback Handling**: Graceful degradation when generation fails
- **Context Awareness**: Considers user profile, environment, and social context

## Supported Event Types

- `daily_reflection` - Daily thoughts and reflections
- `personal_milestone` - Personal achievements and milestones
- `learning_experience` - Educational and learning moments
- `social_interaction` - Social events and interactions
- `work_achievement` - Professional accomplishments
- `hobby_activity` - Recreational and hobby activities
- `health_wellness` - Health and wellness related events
- `travel_experience` - Travel and exploration experiences
- `family_event` - Family-related events and moments
- `general_diary` - General diary entries
- `random_thought` - Random thoughts and ideas
- `goal_progress` - Progress towards personal goals

## Installation

The diary agent is part of the diary_agent system. Ensure you have the required dependencies:

```bash
# Install required packages
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
import asyncio
from diary_agent.agents.diary_agent import DiaryAgent
from diary_agent.integration.diary_data_reader import DiaryDataReader
from diary_agent.utils.data_models import EventData, PromptConfig
from diary_agent.core.llm_manager import LLMConfigManager

async def create_diary_entry():
    # Initialize components
    llm_manager = LLMConfigManager()
    data_reader = DiaryDataReader()
    
    # Load prompt configuration
    with open("diary_agent/config/agent_prompts/diary_agent.json", 'r') as f:
        prompt_data = json.load(f)
    
    prompt_config = PromptConfig(**prompt_data)
    
    # Create diary agent (LLM mode)
    diary_agent = DiaryAgent(
        agent_type="diary_agent",
        prompt_config=prompt_config,
        llm_manager=llm_manager,
        data_reader=data_reader,
        use_llm=True  # Set to False for default content mode
    )
    
    # Create event data
    event_data = EventData(
        event_id="event_001",
        event_type="diary",
        event_name="daily_reflection",
        timestamp=datetime.now(),
        user_id=1,
        context_data={
            "user_profile": {"personality": "calm"},
            "event_details": {"description": "A peaceful day"},
            "environmental_context": {"weather": "sunny"},
            "social_context": {"interactions": "minimal"},
            "emotional_context": {"mood": "content"},
            "temporal_context": {"time_of_day": "afternoon"}
        },
        metadata={}
    )
    
    # Generate diary entry
    diary_entry = await diary_agent.process_event(event_data)
    
    print(f"Title: {diary_entry.title}")
    print(f"Content: {diary_entry.content}")
    print(f"Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")

# Run the example
asyncio.run(create_diary_entry())
```

### Switching Between Modes

```python
# Create agent with default content mode
diary_agent = DiaryAgent(
    agent_type="diary_agent",
    prompt_config=prompt_config,
    llm_manager=llm_manager,
    data_reader=data_reader,
    use_llm=False  # Start with default content
)

# Switch to LLM mode
diary_agent.set_llm_mode(True)

# Switch back to default content mode
diary_agent.set_llm_mode(False)

# Check current mode
current_mode = diary_agent.get_llm_mode()  # True for LLM, False for default
```

### Testing

Run the test script to see both modes in action:

```bash
python diary_agent/test_diary_agent.py
```

## Configuration

### Prompt Configuration

The diary agent uses a JSON configuration file for prompts:

```json
{
  "agent_type": "diary_agent",
  "system_prompt": "You are a diary writing AI assistant...",
  "user_prompt_template": "Please generate a diary entry for...",
  "output_format": {
    "title": "string (max 6 characters)",
    "content": "string (max 35 characters)",
    "emotion_tags": "array of strings"
  },
  "validation_rules": {
    "title_max_length": 6,
    "content_max_length": 35,
    "required_fields": ["title", "content", "emotion_tags"],
    "emotion_tags_valid": ["生气愤怒", "悲伤难过", "担忧", "焦虑忧愁", "惊讶震惊", "好奇", "羞愧", "平静", "开心快乐", "兴奋激动"]
  }
}
```

### LLM Configuration

Configure your LLM providers in `config/llm_configuration.json`:

```json
{
  "providers": [
    {
      "provider_name": "qwen",
      "api_endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
      "api_key": "your_api_key",
      "model_name": "qwen-turbo",
      "max_tokens": 150,
      "temperature": 0.7,
      "enabled": true,
      "priority": 1
    }
  ]
}
```

## Output Format

Diary entries follow this structure:

```python
@dataclass
class DiaryEntry:
    entry_id: str          # Unique identifier
    user_id: int          # User ID
    timestamp: datetime   # Entry timestamp
    event_type: str       # Event type
    event_name: str       # Specific event name
    title: str           # Entry title (max 6 characters)
    content: str         # Entry content (max 35 characters)
    emotion_tags: List[EmotionalTag]  # Emotional tags
    agent_type: str      # Agent type
    llm_provider: str    # LLM provider or "default"/"fallback"
```

## Error Handling

The diary agent includes comprehensive error handling:

- **LLM Failures**: Falls back to default content or simple fallback entries
- **Validation Errors**: Ensures content meets length and format requirements
- **Context Errors**: Provides minimal context when data reading fails
- **Graceful Degradation**: Continues operation even when components fail

## Customization

### Adding New Event Types

1. Add the event type to the `supported_events` list
2. Create default templates in `default_templates`
3. Update the prompt template if needed

### Custom Default Templates

```python
# Add custom templates
diary_agent.default_templates["custom_event"] = {
    "titles": ["自定义标题"],
    "contents": ["自定义内容 ✨"],
    "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM]
}
```

### Extending Data Reader

Create a custom data reader to integrate with your data sources:

```python
class CustomDataReader(DiaryDataReader):
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        # Custom context reading logic
        return DiaryContextData(...)
```

## Integration

The diary agent integrates with the existing diary_agent system:

- **Base Agent**: Inherits from `BaseSubAgent` for consistency
- **Data Models**: Uses standard `EventData` and `DiaryEntry` structures
- **LLM Manager**: Integrates with the centralized LLM management system
- **Validation**: Uses standard validation and formatting utilities
- **Logging**: Integrates with the system-wide logging framework

## Performance

- **Default Mode**: Fast, reliable, no external dependencies
- **LLM Mode**: Variable performance based on LLM provider and network
- **Caching**: LLM responses can be cached for improved performance
- **Async**: Full async support for non-blocking operation

## Troubleshooting

### Common Issues

1. **LLM Connection Errors**: Check API keys and network connectivity
2. **Validation Failures**: Ensure content meets length requirements
3. **Import Errors**: Verify all dependencies are installed
4. **Context Errors**: Check data reader configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is part of the diary_agent system.
