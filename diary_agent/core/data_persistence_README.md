# Data Persistence and Retrieval System

## Overview

The data persistence system provides comprehensive storage and retrieval capabilities for diary entries in the diary agent system. It uses JSON-based file storage that is compatible with the existing system structure and provides robust backup and recovery mechanisms.

## Components

### DiaryPersistenceManager

The main class responsible for managing diary entry storage and retrieval.

#### Key Features

- **JSON-based Storage**: Stores diary entries as JSON files with structured naming
- **Thread-safe Operations**: Uses file locking for concurrent access
- **Date-based Organization**: Organizes entries by date for efficient retrieval
- **Backup and Recovery**: Comprehensive backup and restore functionality
- **Daily Quota Management**: Tracks daily diary generation quotas
- **Storage Statistics**: Provides detailed storage usage information

#### Directory Structure

```
diary_agent/data/
├── entries/           # Individual diary entry JSON files
├── backups/          # Backup directories
└── quotas/           # Daily quota tracking files
```

#### File Naming Convention

- **Diary Entries**: `{user_id}_{date}_{entry_id}.json`
- **Daily Quotas**: `quota_{date}.json`
- **Backups**: `backup_{timestamp}/` or custom names

### DiaryQueryManager

Advanced querying capabilities for diary entries.

#### Query Types

- **Content Search**: Search by title, content, or event name
- **Emotion Filtering**: Filter entries by emotional tags
- **Event Type Filtering**: Filter by event type categories
- **Date Range Filtering**: Filter by date ranges
- **User Filtering**: Filter by specific users

#### Statistics

- **Emotion Statistics**: Count distribution of emotional tags
- **Storage Statistics**: File counts, sizes, and date ranges
- **User Statistics**: Entry counts per user

## Usage Examples

### Basic Operations

```python
from diary_agent.core.data_persistence import DiaryPersistenceManager, DiaryQueryManager
from diary_agent.utils.data_models import DiaryEntry, EmotionalTag

# Initialize managers
persistence = DiaryPersistenceManager("diary_agent/data")
query_manager = DiaryQueryManager(persistence)

# Save diary entry
entry = DiaryEntry(
    entry_id="unique-id",
    user_id=1,
    timestamp=datetime.now(),
    event_type="weather_events",
    event_name="favorite_weather",
    title="晴天",
    content="今天天气很好😊",
    emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
    agent_type="weather_agent",
    llm_provider="qwen"
)

success = persistence.save_diary_entry(entry)
```

### Retrieval Operations

```python
# Get entry by ID
entry = persistence.get_diary_entry("entry-id")

# Get entries by user
user_entries = persistence.get_entries_by_user(user_id=1)

# Get entries by date
today_entries = persistence.get_entries_by_date(date.today())

# Get entries with date range
filtered_entries = persistence.get_entries_by_user(
    user_id=1, 
    start_date=date.today() - timedelta(days=7),
    end_date=date.today()
)
```

### Advanced Queries

```python
# Search by content
weather_entries = query_manager.search_entries("天气")

# Filter by emotion
happy_entries = query_manager.get_entries_by_emotion(EmotionalTag.HAPPY_JOYFUL)

# Filter by event type
weather_events = query_manager.get_entries_by_event_type("weather_events")

# Get emotion statistics
emotion_stats = query_manager.get_emotion_statistics()
```

### Daily Quota Management

```python
from diary_agent.utils.data_models import DailyQuota

# Create daily quota
quota = DailyQuota(
    date=date.today(),
    total_quota=3,
    current_count=1,
    completed_event_types=["weather_events"]
)

# Save quota
persistence.save_daily_quota(quota)

# Retrieve quota
daily_quota = persistence.get_daily_quota(date.today())

# Check if can generate diary
can_generate = daily_quota.can_generate_diary("friends_function")
```

### Backup and Recovery

```python
# Create backup
success = persistence.create_backup("my_backup")

# List available backups
backups = persistence.list_backups()

# Restore from backup
success = persistence.restore_backup("my_backup")
```

### Storage Management

```python
# Get storage statistics
stats = persistence.get_storage_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Storage size: {stats['storage_size_mb']} MB")

# Cleanup old entries (older than 365 days)
deleted_count = persistence.cleanup_old_entries(days_to_keep=365)
```

## JSON File Format

### Diary Entry Format

```json
{
  "entry_id": "unique-identifier",
  "user_id": 1,
  "timestamp": "2024-01-15T10:30:00",
  "event_type": "weather_events",
  "event_name": "favorite_weather",
  "title": "晴天",
  "content": "今天天气很好，心情愉快😊",
  "emotion_tags": ["开心快乐", "平静"],
  "agent_type": "weather_agent",
  "llm_provider": "qwen"
}
```

### Daily Quota Format

```json
{
  "date": "2024-01-15",
  "total_quota": 3,
  "current_count": 1,
  "completed_event_types": ["weather_events"]
}
```

## Error Handling

The system includes comprehensive error handling:

- **File I/O Errors**: Graceful handling of file system issues
- **JSON Parsing Errors**: Validation and error recovery for corrupted files
- **Concurrent Access**: Thread-safe operations with file locking
- **Validation Errors**: Entry validation before saving
- **Backup Failures**: Automatic pre-restore backups

## Performance Considerations

- **File-based Storage**: Suitable for moderate volumes (thousands of entries)
- **Date-based Organization**: Efficient retrieval by date ranges
- **Lazy Loading**: Entries loaded only when needed
- **Concurrent Access**: Thread-safe with minimal locking overhead
- **Memory Usage**: Minimal memory footprint for large datasets

## Integration with Existing System

The persistence system is designed to be compatible with the existing diary agent architecture:

- **Data Models**: Uses existing `DiaryEntry` and related models
- **Validation**: Integrates with existing validation utilities
- **Logging**: Uses the centralized logging system
- **Configuration**: Configurable data directory location
- **Independence**: Operates independently from emotion calculation system

## Testing

Comprehensive test coverage includes:

- **Unit Tests**: All core functionality tested
- **Integration Tests**: End-to-end workflow testing
- **Error Scenarios**: Failure condition testing
- **Performance Tests**: Load and stress testing
- **Data Integrity**: Backup and recovery testing

Run tests with:

```bash
cd diary_agent/tests
python -m pytest test_data_persistence.py -v
```

## Future Enhancements

Potential improvements for the persistence system:

- **Database Backend**: Optional SQL database support for larger scales
- **Compression**: File compression for storage efficiency
- **Encryption**: Data encryption for sensitive information
- **Replication**: Multi-location backup replication
- **Indexing**: Advanced indexing for faster queries
- **Caching**: In-memory caching for frequently accessed data