"""
Unit tests for data persistence and retrieval system.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import uuid

from diary_agent.core.data_persistence import DiaryPersistenceManager, DiaryQueryManager
from diary_agent.utils.data_models import DiaryEntry, EmotionalTag, DailyQuota


class TestDiaryPersistenceManager:
    """Test cases for DiaryPersistenceManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def persistence_manager(self, temp_dir):
        """Create DiaryPersistenceManager instance for testing."""
        return DiaryPersistenceManager(data_directory=temp_dir)
    
    @pytest.fixture
    def sample_diary_entry(self):
        """Create sample diary entry for testing."""
        return DiaryEntry(
            entry_id=str(uuid.uuid4()),
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="favorite_weather",
            title="晴天",
            content="今天天气很好，心情愉快😊",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL, EmotionalTag.CALM],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
    
    @pytest.fixture
    def sample_daily_quota(self):
        """Create sample daily quota for testing."""
        return DailyQuota(
            date=date.today(),
            total_quota=3,
            current_count=1,
            completed_event_types=["weather_events"]
        )
    
    def test_initialization(self, temp_dir):
        """Test DiaryPersistenceManager initialization."""
        manager = DiaryPersistenceManager(data_directory=temp_dir)
        
        # Check that directories are created
        assert Path(temp_dir).exists()
        assert (Path(temp_dir) / "entries").exists()
        assert (Path(temp_dir) / "backups").exists()
        assert (Path(temp_dir) / "quotas").exists()
    
    def test_save_diary_entry(self, persistence_manager, sample_diary_entry):
        """Test saving diary entry."""
        result = persistence_manager.save_diary_entry(sample_diary_entry)
        
        assert result is True
        
        # Check that file was created
        date_str = sample_diary_entry.timestamp.strftime("%Y-%m-%d")
        expected_filename = f"{sample_diary_entry.user_id}_{date_str}_{sample_diary_entry.entry_id}.json"
        expected_path = persistence_manager.entries_directory / expected_filename
        
        assert expected_path.exists()
        
        # Verify file content
        with open(expected_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        assert saved_data["entry_id"] == sample_diary_entry.entry_id
        assert saved_data["user_id"] == sample_diary_entry.user_id
        assert saved_data["title"] == sample_diary_entry.title
        assert saved_data["content"] == sample_diary_entry.content
        assert len(saved_data["emotion_tags"]) == 2
    
    def test_get_diary_entry(self, persistence_manager, sample_diary_entry):
        """Test retrieving diary entry by ID."""
        # Save entry first
        persistence_manager.save_diary_entry(sample_diary_entry)
        
        # Retrieve entry
        retrieved_entry = persistence_manager.get_diary_entry(sample_diary_entry.entry_id)
        
        assert retrieved_entry is not None
        assert retrieved_entry.entry_id == sample_diary_entry.entry_id
        assert retrieved_entry.user_id == sample_diary_entry.user_id
        assert retrieved_entry.title == sample_diary_entry.title
        assert retrieved_entry.content == sample_diary_entry.content
        assert len(retrieved_entry.emotion_tags) == 2
    
    def test_get_diary_entry_not_found(self, persistence_manager):
        """Test retrieving non-existent diary entry."""
        result = persistence_manager.get_diary_entry("non-existent-id")
        assert result is None
    
    def test_get_entries_by_user(self, persistence_manager):
        """Test retrieving entries by user ID."""
        # Create multiple entries for different users
        entries = []
        for i in range(3):
            entry = DiaryEntry(
                entry_id=str(uuid.uuid4()),
                user_id=1,
                timestamp=datetime.now() - timedelta(days=i),
                event_type="weather_events",
                event_name="favorite_weather",
                title=f"标题{i}",
                content=f"内容{i}",
                emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
                agent_type="weather_agent",
                llm_provider="qwen"
            )
            entries.append(entry)
            persistence_manager.save_diary_entry(entry)
        
        # Create entry for different user
        other_entry = DiaryEntry(
            entry_id=str(uuid.uuid4()),
            user_id=2,
            timestamp=datetime.now(),
            event_type="weather_events",
            event_name="favorite_weather",
            title="其他",
            content="其他用户",
            emotion_tags=[EmotionalTag.CALM],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        persistence_manager.save_diary_entry(other_entry)
        
        # Retrieve entries for user 1
        user_entries = persistence_manager.get_entries_by_user(1)
        
        assert len(user_entries) == 3
        for entry in user_entries:
            assert entry.user_id == 1
        
        # Check sorting by timestamp (oldest first)
        timestamps = [entry.timestamp for entry in user_entries]
        assert timestamps == sorted(timestamps)
    
    def test_get_entries_by_user_with_date_filter(self, persistence_manager):
        """Test retrieving entries by user with date filtering."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        
        # Create entries on different dates
        entries_data = [
            (two_days_ago, "旧条目"),
            (yesterday, "昨天条目"),
            (today, "今天条目")
        ]
        
        for entry_date, title in entries_data:
            entry = DiaryEntry(
                entry_id=str(uuid.uuid4()),
                user_id=1,
                timestamp=datetime.combine(entry_date, datetime.min.time()),
                event_type="weather_events",
                event_name="favorite_weather",
                title=title,
                content=f"内容 {title}",
                emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
                agent_type="weather_agent",
                llm_provider="qwen"
            )
            persistence_manager.save_diary_entry(entry)
        
        # Test date filtering
        filtered_entries = persistence_manager.get_entries_by_user(1, start_date=yesterday, end_date=today)
        
        assert len(filtered_entries) == 2
        for entry in filtered_entries:
            assert entry.timestamp.date() >= yesterday
            assert entry.timestamp.date() <= today
    
    def test_get_entries_by_date(self, persistence_manager):
        """Test retrieving entries by specific date."""
        target_date = date.today()
        
        # Create entries for target date
        for i in range(2):
            entry = DiaryEntry(
                entry_id=str(uuid.uuid4()),
                user_id=i + 1,
                timestamp=datetime.combine(target_date, datetime.min.time()) + timedelta(hours=i),
                event_type="weather_events",
                event_name="favorite_weather",
                title=f"标题{i}",
                content=f"内容{i}",
                emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
                agent_type="weather_agent",
                llm_provider="qwen"
            )
            persistence_manager.save_diary_entry(entry)
        
        # Create entry for different date
        other_entry = DiaryEntry(
            entry_id=str(uuid.uuid4()),
            user_id=1,
            timestamp=datetime.combine(target_date - timedelta(days=1), datetime.min.time()),
            event_type="weather_events",
            event_name="favorite_weather",
            title="其他日期",
            content="其他日期内容",
            emotion_tags=[EmotionalTag.CALM],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        persistence_manager.save_diary_entry(other_entry)
        
        # Retrieve entries for target date
        date_entries = persistence_manager.get_entries_by_date(target_date)
        
        assert len(date_entries) == 2
        for entry in date_entries:
            assert entry.timestamp.date() == target_date
    
    def test_delete_diary_entry(self, persistence_manager, sample_diary_entry):
        """Test deleting diary entry."""
        # Save entry first
        persistence_manager.save_diary_entry(sample_diary_entry)
        
        # Verify entry exists
        retrieved_entry = persistence_manager.get_diary_entry(sample_diary_entry.entry_id)
        assert retrieved_entry is not None
        
        # Delete entry
        result = persistence_manager.delete_diary_entry(sample_diary_entry.entry_id)
        assert result is True
        
        # Verify entry is deleted
        deleted_entry = persistence_manager.get_diary_entry(sample_diary_entry.entry_id)
        assert deleted_entry is None
    
    def test_delete_diary_entry_not_found(self, persistence_manager):
        """Test deleting non-existent diary entry."""
        result = persistence_manager.delete_diary_entry("non-existent-id")
        assert result is False
    
    def test_save_daily_quota(self, persistence_manager, sample_daily_quota):
        """Test saving daily quota."""
        result = persistence_manager.save_daily_quota(sample_daily_quota)
        
        assert result is True
        
        # Check that file was created
        date_str = sample_daily_quota.date.strftime("%Y-%m-%d")
        expected_filename = f"quota_{date_str}.json"
        expected_path = persistence_manager.quota_directory / expected_filename
        
        assert expected_path.exists()
        
        # Verify file content
        with open(expected_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        assert saved_data["total_quota"] == sample_daily_quota.total_quota
        assert saved_data["current_count"] == sample_daily_quota.current_count
        assert saved_data["completed_event_types"] == sample_daily_quota.completed_event_types
    
    def test_get_daily_quota(self, persistence_manager, sample_daily_quota):
        """Test retrieving daily quota."""
        # Save quota first
        persistence_manager.save_daily_quota(sample_daily_quota)
        
        # Retrieve quota
        retrieved_quota = persistence_manager.get_daily_quota(sample_daily_quota.date)
        
        assert retrieved_quota is not None
        assert retrieved_quota.date == sample_daily_quota.date
        assert retrieved_quota.total_quota == sample_daily_quota.total_quota
        assert retrieved_quota.current_count == sample_daily_quota.current_count
        assert retrieved_quota.completed_event_types == sample_daily_quota.completed_event_types
    
    def test_get_daily_quota_not_found(self, persistence_manager):
        """Test retrieving non-existent daily quota."""
        result = persistence_manager.get_daily_quota(date.today() - timedelta(days=30))
        assert result is None
    
    def test_create_backup(self, persistence_manager, sample_diary_entry, sample_daily_quota):
        """Test creating backup."""
        # Save some data first
        persistence_manager.save_diary_entry(sample_diary_entry)
        persistence_manager.save_daily_quota(sample_daily_quota)
        
        # Create backup
        result = persistence_manager.create_backup("test_backup")
        
        assert result is True
        
        # Check backup directory exists
        backup_path = persistence_manager.backups_directory / "test_backup"
        assert backup_path.exists()
        assert (backup_path / "entries").exists()
        assert (backup_path / "quotas").exists()
        
        # Check backup contains data
        entries_backup = backup_path / "entries"
        quotas_backup = backup_path / "quotas"
        
        assert len(list(entries_backup.glob("*.json"))) > 0
        assert len(list(quotas_backup.glob("*.json"))) > 0
    
    def test_restore_backup(self, persistence_manager, sample_diary_entry):
        """Test restoring from backup."""
        # Save original data and create backup
        persistence_manager.save_diary_entry(sample_diary_entry)
        persistence_manager.create_backup("restore_test")
        
        # Delete original data
        persistence_manager.delete_diary_entry(sample_diary_entry.entry_id)
        assert persistence_manager.get_diary_entry(sample_diary_entry.entry_id) is None
        
        # Restore from backup
        result = persistence_manager.restore_backup("restore_test")
        
        assert result is True
        
        # Verify data is restored
        restored_entry = persistence_manager.get_diary_entry(sample_diary_entry.entry_id)
        assert restored_entry is not None
        assert restored_entry.entry_id == sample_diary_entry.entry_id
    
    def test_list_backups(self, persistence_manager):
        """Test listing backups."""
        # Create multiple backups
        backup_names = ["backup1", "backup2", "backup3"]
        for name in backup_names:
            persistence_manager.create_backup(name)
        
        # List backups
        backups = persistence_manager.list_backups()
        
        assert len(backups) >= 3
        for name in backup_names:
            assert name in backups
    
    def test_get_storage_stats(self, persistence_manager):
        """Test getting storage statistics."""
        # Create some test data
        for i in range(3):
            entry = DiaryEntry(
                entry_id=str(uuid.uuid4()),
                user_id=1,
                timestamp=datetime.now() - timedelta(days=i),
                event_type="weather_events",
                event_name="favorite_weather",
                title=f"标题{i}",
                content=f"内容{i}",
                emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
                agent_type="weather_agent",
                llm_provider="qwen"
            )
            persistence_manager.save_diary_entry(entry)
        
        # Get stats
        stats = persistence_manager.get_storage_stats()
        
        assert "total_entries" in stats
        assert "entries_by_user" in stats
        assert "entries_by_date" in stats
        assert "storage_size_mb" in stats
        assert "oldest_entry" in stats
        assert "newest_entry" in stats
        
        assert stats["total_entries"] == 3
        assert stats["entries_by_user"][1] == 3
        assert stats["storage_size_mb"] >= 0
    
    def test_cleanup_old_entries(self, persistence_manager):
        """Test cleaning up old entries."""
        # Create old and new entries
        old_entry = DiaryEntry(
            entry_id=str(uuid.uuid4()),
            user_id=1,
            timestamp=datetime.now() - timedelta(days=400),  # Very old
            event_type="weather_events",
            event_name="favorite_weather",
            title="旧条目",
            content="很旧的条目",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        new_entry = DiaryEntry(
            entry_id=str(uuid.uuid4()),
            user_id=1,
            timestamp=datetime.now(),  # Recent
            event_type="weather_events",
            event_name="favorite_weather",
            title="新条目",
            content="新的条目",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        persistence_manager.save_diary_entry(old_entry)
        persistence_manager.save_diary_entry(new_entry)
        
        # Cleanup entries older than 365 days
        deleted_count = persistence_manager.cleanup_old_entries(days_to_keep=365)
        
        assert deleted_count == 1
        
        # Verify old entry is deleted, new entry remains
        assert persistence_manager.get_diary_entry(old_entry.entry_id) is None
        assert persistence_manager.get_diary_entry(new_entry.entry_id) is not None


class TestDiaryQueryManager:
    """Test cases for DiaryQueryManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def persistence_manager(self, temp_dir):
        """Create DiaryPersistenceManager instance for testing."""
        return DiaryPersistenceManager(data_directory=temp_dir)
    
    @pytest.fixture
    def query_manager(self, persistence_manager):
        """Create DiaryQueryManager instance for testing."""
        return DiaryQueryManager(persistence_manager)
    
    @pytest.fixture
    def sample_entries(self, persistence_manager):
        """Create sample entries for testing."""
        entries = []
        
        # Create entries with different content and emotions
        entries_data = [
            ("晴天", "今天天气很好", [EmotionalTag.HAPPY_JOYFUL], "weather_events", "favorite_weather"),
            ("雨天", "下雨了很烦躁", [EmotionalTag.ANGRY_FURIOUS], "weather_events", "dislike_weather"),
            ("朋友", "和朋友聊天很开心", [EmotionalTag.HAPPY_JOYFUL, EmotionalTag.EXCITED_THRILLED], "friends_function", "made_new_friend"),
            ("孤独", "今天没人陪我", [EmotionalTag.SAD_UPSET], "unkeep_interactive", "neglect_1_day_no_dialogue")
        ]
        
        for i, (title, content, emotions, event_type, event_name) in enumerate(entries_data):
            entry = DiaryEntry(
                entry_id=str(uuid.uuid4()),
                user_id=1,
                timestamp=datetime.now() - timedelta(days=i),
                event_type=event_type,
                event_name=event_name,
                title=title,
                content=content,
                emotion_tags=emotions,
                agent_type="test_agent",
                llm_provider="qwen"
            )
            entries.append(entry)
            persistence_manager.save_diary_entry(entry)
        
        return entries
    
    def test_search_entries(self, query_manager, sample_entries):
        """Test searching entries by content."""
        # Search for weather-related entries
        weather_entries = query_manager.search_entries("天气")
        assert len(weather_entries) == 1
        assert "天气" in weather_entries[0].content
        
        # Search for friend-related entries
        friend_entries = query_manager.search_entries("朋友")
        assert len(friend_entries) == 1
        assert "朋友" in friend_entries[0].content
        
        # Search in title
        sunny_entries = query_manager.search_entries("晴天")
        assert len(sunny_entries) == 1
        assert sunny_entries[0].title == "晴天"
    
    def test_get_entries_by_emotion(self, query_manager, sample_entries):
        """Test filtering entries by emotion."""
        # Get happy entries
        happy_entries = query_manager.get_entries_by_emotion(EmotionalTag.HAPPY_JOYFUL)
        assert len(happy_entries) == 2
        
        for entry in happy_entries:
            assert EmotionalTag.HAPPY_JOYFUL in entry.emotion_tags
        
        # Get sad entries
        sad_entries = query_manager.get_entries_by_emotion(EmotionalTag.SAD_UPSET)
        assert len(sad_entries) == 1
        assert EmotionalTag.SAD_UPSET in sad_entries[0].emotion_tags
    
    def test_get_entries_by_event_type(self, query_manager, sample_entries):
        """Test filtering entries by event type."""
        # Get weather events
        weather_entries = query_manager.get_entries_by_event_type("weather_events")
        assert len(weather_entries) == 2
        
        for entry in weather_entries:
            assert entry.event_type == "weather_events"
        
        # Get friend events
        friend_entries = query_manager.get_entries_by_event_type("friends_function")
        assert len(friend_entries) == 1
        assert friend_entries[0].event_type == "friends_function"
    
    def test_get_emotion_statistics(self, query_manager, sample_entries):
        """Test getting emotion statistics."""
        stats = query_manager.get_emotion_statistics()
        
        assert EmotionalTag.HAPPY_JOYFUL.value in stats
        assert stats[EmotionalTag.HAPPY_JOYFUL.value] == 2
        
        assert EmotionalTag.ANGRY_FURIOUS.value in stats
        assert stats[EmotionalTag.ANGRY_FURIOUS.value] == 1
        
        assert EmotionalTag.SAD_UPSET.value in stats
        assert stats[EmotionalTag.SAD_UPSET.value] == 1
        
        assert EmotionalTag.EXCITED_THRILLED.value in stats
        assert stats[EmotionalTag.EXCITED_THRILLED.value] == 1


if __name__ == "__main__":
    pytest.main([__file__])