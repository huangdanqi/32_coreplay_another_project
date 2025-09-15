"""
Example usage of the data persistence and retrieval system.
Demonstrates how to save, retrieve, and manage diary entries.
"""

import uuid
from datetime import datetime, date, timedelta
from pathlib import Path

from diary_agent.core.data_persistence import DiaryPersistenceManager, DiaryQueryManager
from diary_agent.utils.data_models import DiaryEntry, EmotionalTag, DailyQuota


def main():
    """Demonstrate data persistence functionality."""
    
    # Initialize persistence manager
    data_dir = "diary_agent/data"
    persistence = DiaryPersistenceManager(data_directory=data_dir)
    query_manager = DiaryQueryManager(persistence)
    
    print("=== Diary Data Persistence Example ===\n")
    
    # 1. Create and save sample diary entries
    print("1. Creating and saving diary entries...")
    
    sample_entries = [
        {
            "title": "晴天",
            "content": "今天天气很好，心情愉快😊",
            "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM],
            "event_type": "weather_events",
            "event_name": "favorite_weather",
            "agent_type": "weather_agent"
        },
        {
            "title": "雨天",
            "content": "下雨了，有点烦躁😤",
            "emotions": [EmotionalTag.ANGRY_FURIOUS],
            "event_type": "weather_events", 
            "event_name": "dislike_weather",
            "agent_type": "weather_agent"
        },
        {
            "title": "新朋友",
            "content": "今天认识了新朋友，很开心🎉",
            "emotions": [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED],
            "event_type": "friends_function",
            "event_name": "made_new_friend",
            "agent_type": "friends_agent"
        },
        {
            "title": "孤独",
            "content": "今天没人陪我，感觉很孤单😢",
            "emotions": [EmotionalTag.SAD_UPSET],
            "event_type": "unkeep_interactive",
            "event_name": "neglect_1_day_no_dialogue",
            "agent_type": "neglect_agent"
        }
    ]
    
    saved_entries = []
    for i, entry_data in enumerate(sample_entries):
        entry = DiaryEntry(
            entry_id=str(uuid.uuid4()),
            user_id=1,
            timestamp=datetime.now() - timedelta(hours=i),
            event_type=entry_data["event_type"],
            event_name=entry_data["event_name"],
            title=entry_data["title"],
            content=entry_data["content"],
            emotion_tags=entry_data["emotions"],
            agent_type=entry_data["agent_type"],
            llm_provider="qwen"
        )
        
        success = persistence.save_diary_entry(entry)
        if success:
            saved_entries.append(entry)
            print(f"   ✓ Saved: {entry.title} - {entry.content}")
        else:
            print(f"   ✗ Failed to save: {entry.title}")
    
    print(f"\nSaved {len(saved_entries)} diary entries.\n")
    
    # 2. Retrieve entries by user
    print("2. Retrieving entries by user...")
    user_entries = persistence.get_entries_by_user(user_id=1)
    print(f"Found {len(user_entries)} entries for user 1:")
    for entry in user_entries:
        emotions_str = ", ".join([tag.value for tag in entry.emotion_tags])
        print(f"   - {entry.timestamp.strftime('%H:%M')} | {entry.title}: {entry.content} [{emotions_str}]")
    print()
    
    # 3. Retrieve entries by date
    print("3. Retrieving entries by date...")
    today_entries = persistence.get_entries_by_date(date.today())
    print(f"Found {len(today_entries)} entries for today:")
    for entry in today_entries:
        print(f"   - {entry.title}: {entry.content}")
    print()
    
    # 4. Search entries by content
    print("4. Searching entries...")
    weather_entries = query_manager.search_entries("天气")
    print(f"Found {len(weather_entries)} entries containing '天气':")
    for entry in weather_entries:
        print(f"   - {entry.title}: {entry.content}")
    
    friend_entries = query_manager.search_entries("朋友")
    print(f"Found {len(friend_entries)} entries containing '朋友':")
    for entry in friend_entries:
        print(f"   - {entry.title}: {entry.content}")
    print()
    
    # 5. Filter by emotion
    print("5. Filtering by emotion...")
    happy_entries = query_manager.get_entries_by_emotion(EmotionalTag.HAPPY_JOYFUL)
    print(f"Found {len(happy_entries)} happy entries:")
    for entry in happy_entries:
        print(f"   - {entry.title}: {entry.content}")
    
    sad_entries = query_manager.get_entries_by_emotion(EmotionalTag.SAD_UPSET)
    print(f"Found {len(sad_entries)} sad entries:")
    for entry in sad_entries:
        print(f"   - {entry.title}: {entry.content}")
    print()
    
    # 6. Filter by event type
    print("6. Filtering by event type...")
    weather_events = query_manager.get_entries_by_event_type("weather_events")
    print(f"Found {len(weather_events)} weather-related entries:")
    for entry in weather_events:
        print(f"   - {entry.title}: {entry.content}")
    print()
    
    # 7. Get emotion statistics
    print("7. Emotion statistics...")
    emotion_stats = query_manager.get_emotion_statistics()
    print("Emotion distribution:")
    for emotion, count in emotion_stats.items():
        print(f"   - {emotion}: {count}")
    print()
    
    # 8. Daily quota management
    print("8. Daily quota management...")
    daily_quota = DailyQuota(
        date=date.today(),
        total_quota=5,
        current_count=2,
        completed_event_types=["weather_events", "friends_function"]
    )
    
    success = persistence.save_daily_quota(daily_quota)
    if success:
        print("   ✓ Saved daily quota")
        
        # Retrieve quota
        retrieved_quota = persistence.get_daily_quota(date.today())
        if retrieved_quota:
            print(f"   - Total quota: {retrieved_quota.total_quota}")
            print(f"   - Current count: {retrieved_quota.current_count}")
            print(f"   - Completed types: {retrieved_quota.completed_event_types}")
            print(f"   - Can generate weather diary: {retrieved_quota.can_generate_diary('weather_events')}")
            print(f"   - Can generate holiday diary: {retrieved_quota.can_generate_diary('holiday_events')}")
    print()
    
    # 9. Backup and restore
    print("9. Backup and restore...")
    backup_name = f"example_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    success = persistence.create_backup(backup_name)
    if success:
        print(f"   ✓ Created backup: {backup_name}")
        
        # List backups
        backups = persistence.list_backups()
        print(f"   Available backups: {len(backups)}")
        for backup in backups[:3]:  # Show first 3
            print(f"     - {backup}")
    print()
    
    # 10. Storage statistics
    print("10. Storage statistics...")
    stats = persistence.get_storage_stats()
    print(f"   - Total entries: {stats.get('total_entries', 0)}")
    print(f"   - Storage size: {stats.get('storage_size_mb', 0)} MB")
    print(f"   - Users with entries: {len(stats.get('entries_by_user', {}))}")
    print(f"   - Dates with entries: {len(stats.get('entries_by_date', {}))}")
    if stats.get('oldest_entry'):
        oldest = datetime.fromisoformat(stats['oldest_entry'])
        print(f"   - Oldest entry: {oldest.strftime('%Y-%m-%d %H:%M')}")
    if stats.get('newest_entry'):
        newest = datetime.fromisoformat(stats['newest_entry'])
        print(f"   - Newest entry: {newest.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # 11. Demonstrate retrieval by ID
    print("11. Retrieving specific entry...")
    if saved_entries:
        first_entry = saved_entries[0]
        retrieved = persistence.get_diary_entry(first_entry.entry_id)
        if retrieved:
            print(f"   ✓ Retrieved entry: {retrieved.title} - {retrieved.content}")
            print(f"   - Event: {retrieved.event_type} / {retrieved.event_name}")
            print(f"   - Agent: {retrieved.agent_type}")
            print(f"   - LLM: {retrieved.llm_provider}")
            emotions_str = ", ".join([tag.value for tag in retrieved.emotion_tags])
            print(f"   - Emotions: {emotions_str}")
        else:
            print("   ✗ Failed to retrieve entry")
    print()
    
    print("=== Data Persistence Example Complete ===")


if __name__ == "__main__":
    main()