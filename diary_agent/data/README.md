# Diary Agent Data Directory

This directory contains the persistent storage for the diary agent system.

## Directory Structure

```
diary_agent/data/
├── entries/           # Individual diary entry JSON files
├── backups/          # Backup directories with timestamped snapshots
├── quotas/           # Daily quota tracking files
└── README.md         # This file
```

## File Naming Conventions

### Diary Entries
- Format: `{user_id}_{date}_{entry_id}.json`
- Example: `1_2025-09-01_ba533c0a-7b26-485b-8419-9a6b29cd47e3.json`

### Daily Quotas
- Format: `quota_{date}.json`
- Example: `quota_2025-09-01.json`

### Backups
- Format: `backup_{timestamp}/` or custom names
- Example: `backup_20250901_143022/`

## Data Persistence Features

- **JSON-based Storage**: Human-readable format compatible with existing system
- **Thread-safe Operations**: Concurrent access protection with file locking
- **Automatic Backup**: Comprehensive backup and restore functionality
- **Daily Quota Tracking**: Manages daily diary generation limits
- **Advanced Querying**: Search by content, emotion, event type, and date ranges
- **Storage Statistics**: Detailed usage and performance metrics
- **Data Cleanup**: Automatic cleanup of old entries beyond retention period

## Usage

The data persistence system is automatically initialized when the diary agent starts. Data is stored and retrieved transparently through the `DiaryPersistenceManager` and `DiaryQueryManager` classes.

For manual data management, see the examples in `diary_agent/examples/data_persistence_example.py`.