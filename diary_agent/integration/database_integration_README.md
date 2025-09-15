# Database Integration and Compatibility Layer

This module provides a comprehensive database integration layer for the diary agent system, maintaining compatibility with the existing emotion calculation system while providing read-only access to necessary data sources.

## Overview

The database integration layer consists of several components:

- **DatabaseManager**: Core connection management with existing DB_CONFIG settings
- **Database Adapters**: Specialized adapters for different table types
- **DatabaseReader**: Unified interface for all database operations
- **DataValidator**: Validation utilities for existing JSON field formats
- **DiaryStorageAdapter**: Separate storage for diary entries

## Architecture

```
DatabaseReader
├── DatabaseManager (Connection Management)
├── EmotionDatabaseAdapter (User profiles & preferences)
├── InteractionDatabaseAdapter (Interaction history)
├── FriendshipDatabaseAdapter (Social relationships)
├── DiaryStorageAdapter (Diary entry storage)
└── DataValidator (Data format validation)
```

## Key Features

### 1. Read-Only Access
- **Non-intrusive**: Does not modify existing emotion calculation logic
- **Compatible**: Works with existing database schema and JSON field formats
- **Safe**: Provides read-only access to prevent interference with emotion system

### 2. Existing Schema Support
- **emotion table**: User profiles, preferences, emotional state
- **toy_interaction_events table**: Interaction history and patterns
- **toy_friendships table**: Social relationships and friend data
- **JSON fields**: Validates and parses existing JSON string formats

### 3. Diary Entry Management
- **Separate storage**: Creates dedicated diary_entries table
- **Format validation**: Enforces 6-character titles, 35-character content
- **Emotion tagging**: Supports predefined emotional tags
- **Metadata tracking**: Stores agent type, LLM provider, timestamps

## Usage Examples

### Basic Database Reader Usage

```python
from diary_agent.integration.database_reader import DatabaseReader
from diary_agent.utils.data_models import DatabaseConfig

# Initialize with default configuration
config = DatabaseConfig()
db_reader = DatabaseReader(config)

# Test connection
if db_reader.test_connection():
    print("Database connected successfully")

# Get user profile for diary context
user_profile = db_reader.get_user_profile(user_id=1)
if user_profile:
    print(f"User: {user_profile['basic_info']['name']}")
    print(f"Role: {user_profile['basic_info']['role']}")
    print(f"Preferences: {user_profile['preferences']}")
```

### Getting Diary Generation Context

```python
from diary_agent.utils.data_models import EventData
from datetime import datetime

# Create event data
event_data = EventData(
    event_id="weather_event_123",
    event_type="weather",
    event_name="favorite_weather",
    timestamp=datetime.now(),
    user_id=1,
    context_data={'weather': 'Sunny', 'temperature': 25},
    metadata={}
)

# Get complete diary context
diary_context = db_reader.get_diary_context(event_data)

# Access different context types
user_info = diary_context.user_profile
event_details = diary_context.event_details
social_context = diary_context.social_context
emotional_state = diary_context.emotional_context
```

### Storing Diary Entries

```python
from diary_agent.utils.data_models import DiaryEntry, EmotionalTag
import uuid

# Create diary entry
diary_entry = DiaryEntry(
    entry_id=str(uuid.uuid4()),
    user_id=1,
    timestamp=datetime.now(),
    event_type="weather",
    event_name="favorite_weather",
    title="晴天",
    content="今天天气很好，心情愉快😊",
    emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
    agent_type="weather_agent",
    llm_provider="qwen"
)

# Validate and store
if db_reader.store_diary_entry(diary_entry):
    print("Diary entry stored successfully")
```

## Database Configuration

### Default Configuration
The system uses the existing database configuration from the hewan_emotion_cursor_python modules:

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "h05010501",
    "database": "page_test"
}
```

### Custom Configuration
You can provide custom configuration:

```python
from diary_agent.utils.data_models import DatabaseConfig

config = DatabaseConfig(
    host="your_host",
    port=3306,
    user="your_user",
    password="your_password",
    database="your_database"
)

db_reader = DatabaseReader(config)
```

## Data Models and Validation

### Supported JSON Field Formats
The system validates and parses existing JSON string fields:

- `favorite_weathers`: `'["Sunny", "Clear"]'`
- `dislike_weathers`: `'["Rain", "Storm"]'`
- `favorite_seasons`: `'["Spring", "Summer"]'`
- `dislike_seasons`: `'["Winter"]'`
- `favorite_action`: `'["play", "talk"]'`
- `annoying_action`: `'["ignore"]'`

### Diary Entry Validation
Automatic validation ensures:

- **Title**: Maximum 6 characters
- **Content**: Maximum 35 characters (emoji allowed)
- **Emotion Tags**: Must be from predefined EmotionalTag enum
- **Required Fields**: entry_id, user_id, event_type, event_name, agent_type

### User Data Validation
Validates user profile data:

- **Required Fields**: id, name, role
- **JSON Fields**: Proper format for preference arrays
- **Data Types**: Correct types for all fields

## Error Handling

### Connection Errors
```python
try:
    user_profile = db_reader.get_user_profile(1)
except mysql.connector.Error as e:
    print(f"Database error: {e}")
```

### Validation Errors
```python
from diary_agent.integration.database_manager import DataValidator

errors = DataValidator.validate_diary_entry(diary_entry)
if errors:
    print(f"Validation failed: {errors}")
```

### Graceful Degradation
- Returns None/empty lists for missing data
- Logs warnings for validation issues
- Continues operation with available data

## Integration with Existing Modules

### Weather Function Integration
```python
# Read weather preferences for diary context
user_profile = db_reader.get_user_profile(user_id)
favorite_weathers = user_profile['preferences']['favorite_weathers']
current_role = user_profile['basic_info']['role']

# Use in weather agent for diary generation
weather_context = {
    'user_preferences': favorite_weathers,
    'personality_type': current_role,
    'emotional_state': user_profile['emotional_state']
}
```

### Interaction Analysis
```python
# Get interaction patterns for diary context
interaction_context = db_reader.get_interaction_context(user_id, days=7)
neglect_indicators = interaction_context['neglect_indicators']

# Check for neglect events
if neglect_indicators['no_interaction_3_days']:
    # Generate neglect-themed diary entry
    pass
```

### Social Context
```python
# Get friendship data for social diary entries
social_context = db_reader.get_social_context(user_id)
friend_count = social_context['statistics']['total_friends']
social_activity = social_context['statistics']['social_activity_level']

# Use in friends agent
if social_activity == 'high':
    # Generate social-themed diary content
    pass
```

## Testing

### Unit Tests
Run the comprehensive test suite:

```bash
python -m pytest diary_agent/tests/test_database_integration.py -v
```

### Example Usage
Run the example script:

```bash
python diary_agent/examples/database_integration_example.py
```

### Manual Testing
```python
# Test individual components
from diary_agent.integration.database_manager import DatabaseManager

db_manager = DatabaseManager()
if db_manager.test_connection():
    print("Database connection working")
```

## Performance Considerations

### Connection Management
- Uses context managers for automatic connection cleanup
- Implements connection pooling through mysql.connector
- Handles connection timeouts and retries

### Query Optimization
- Indexes on frequently queried fields (user_id, timestamp, event_type)
- Limits result sets with configurable limits
- Efficient JSON field parsing

### Memory Usage
- Streams large result sets
- Lazy loading of related data
- Garbage collection of connection objects

## Security

### Read-Only Access
- No modification of existing emotion calculations
- Separate diary storage prevents data corruption
- Input validation prevents SQL injection

### Data Privacy
- Logs exclude sensitive information
- Connection credentials managed securely
- User data access logged for audit

## Troubleshooting

### Common Issues

1. **Connection Failed**
   ```
   Error: Database connection error: Access denied
   ```
   - Check database credentials in DatabaseConfig
   - Verify database server is running
   - Confirm network connectivity

2. **Table Not Found**
   ```
   Error: Table 'emotion' doesn't exist
   ```
   - Ensure database schema is set up
   - Check database name in configuration
   - Verify table permissions

3. **JSON Parse Error**
   ```
   Warning: Failed to parse JSON field favorite_weathers
   ```
   - Check JSON field format in database
   - Verify data integrity
   - Review field validation logic

### Debug Mode
Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

db_reader = DatabaseReader()
# Detailed logs will show all database operations
```

## Future Enhancements

### Planned Features
- Connection pooling for high-concurrency scenarios
- Caching layer for frequently accessed user profiles
- Async database operations for better performance
- Database migration utilities for schema updates

### Extensibility
- Plugin architecture for custom data adapters
- Configurable validation rules
- Custom field parsers for new JSON formats
- Integration with other database systems (PostgreSQL, MongoDB)