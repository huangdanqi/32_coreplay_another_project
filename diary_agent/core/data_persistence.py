"""
Data persistence and retrieval system for diary entries.
Provides JSON-based storage compatible with existing system structure.
"""

import json
import os
import shutil
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid
import threading
from contextlib import contextmanager

from ..utils.data_models import DiaryEntry, EmotionalTag, DailyQuota
from ..utils.logger import get_component_logger
from ..utils.validators import DiaryEntryValidator


logger = get_component_logger("data_persistence")


class DiaryPersistenceManager:
    """Manages diary entry storage and retrieval with JSON format."""
    
    def __init__(self, data_directory: str = "diary_agent/data"):
        """
        Initialize the persistence manager.
        
        Args:
            data_directory: Base directory for storing diary data
        """
        self.data_directory = Path(data_directory)
        self.entries_directory = self.data_directory / "entries"
        self.backups_directory = self.data_directory / "backups"
        self.quota_directory = self.data_directory / "quotas"
        self._lock = threading.Lock()
        
        # Create directories if they don't exist
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Create necessary directories for data storage."""
        directories = [
            self.data_directory,
            self.entries_directory,
            self.backups_directory,
            self.quota_directory
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    @contextmanager
    def _file_lock(self):
        """Thread-safe file operations."""
        with self._lock:
            yield
    
    def save_diary_entry(self, entry: DiaryEntry) -> bool:
        """
        Save a diary entry to JSON storage.
        
        Args:
            entry: DiaryEntry object to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Validate entry before saving
            validator = DiaryEntryValidator()
            if not validator.validate_diary_entry(entry):
                logger.error(f"Invalid diary entry: {entry.entry_id}")
                return False
            
            # Convert entry to JSON-compatible format
            entry_data = self._entry_to_dict(entry)
            
            # Create file path based on date and user
            date_str = entry.timestamp.strftime("%Y-%m-%d")
            filename = f"{entry.user_id}_{date_str}_{entry.entry_id}.json"
            file_path = self.entries_directory / filename
            
            with self._file_lock():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(entry_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved diary entry: {entry.entry_id} to {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save diary entry {entry.entry_id}: {str(e)}")
            return False
    
    def get_diary_entry(self, entry_id: str) -> Optional[DiaryEntry]:
        """
        Retrieve a specific diary entry by ID.
        
        Args:
            entry_id: Unique identifier for the diary entry
            
        Returns:
            DiaryEntry object if found, None otherwise
        """
        try:
            # Search for the entry file
            for file_path in self.entries_directory.glob(f"*_{entry_id}.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    entry_data = json.load(f)
                    return self._dict_to_entry(entry_data)
            
            logger.warning(f"Diary entry not found: {entry_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve diary entry {entry_id}: {str(e)}")
            return None
    
    def get_entries_by_user(self, user_id: int, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> List[DiaryEntry]:
        """
        Retrieve diary entries for a specific user within date range.
        
        Args:
            user_id: User identifier
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            
        Returns:
            List of DiaryEntry objects
        """
        entries = []
        
        try:
            # Get all files for the user
            pattern = f"{user_id}_*.json"
            
            for file_path in self.entries_directory.glob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entry_data = json.load(f)
                        entry = self._dict_to_entry(entry_data)
                        
                        # Apply date filtering
                        entry_date = entry.timestamp.date()
                        if start_date and entry_date < start_date:
                            continue
                        if end_date and entry_date > end_date:
                            continue
                            
                        entries.append(entry)
                        
                except Exception as e:
                    logger.error(f"Failed to load entry from {file_path}: {str(e)}")
                    continue
            
            # Sort by timestamp
            entries.sort(key=lambda x: x.timestamp)
            logger.info(f"Retrieved {len(entries)} entries for user {user_id}")
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to retrieve entries for user {user_id}: {str(e)}")
            return []
    
    def get_entries_by_date(self, target_date: date, user_id: Optional[int] = None) -> List[DiaryEntry]:
        """
        Retrieve diary entries for a specific date.
        
        Args:
            target_date: Date to retrieve entries for
            user_id: Optional user filter
            
        Returns:
            List of DiaryEntry objects
        """
        entries = []
        date_str = target_date.strftime("%Y-%m-%d")
        
        try:
            if user_id:
                pattern = f"{user_id}_{date_str}_*.json"
            else:
                pattern = f"*_{date_str}_*.json"
            
            for file_path in self.entries_directory.glob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entry_data = json.load(f)
                        entry = self._dict_to_entry(entry_data)
                        entries.append(entry)
                        
                except Exception as e:
                    logger.error(f"Failed to load entry from {file_path}: {str(e)}")
                    continue
            
            entries.sort(key=lambda x: x.timestamp)
            logger.info(f"Retrieved {len(entries)} entries for date {target_date}")
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to retrieve entries for date {target_date}: {str(e)}")
            return []
    
    def delete_diary_entry(self, entry_id: str) -> bool:
        """
        Delete a diary entry.
        
        Args:
            entry_id: Unique identifier for the diary entry
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Find and delete the entry file
            for file_path in self.entries_directory.glob(f"*_{entry_id}.json"):
                with self._file_lock():
                    file_path.unlink()
                    logger.info(f"Deleted diary entry: {entry_id}")
                    return True
            
            logger.warning(f"Diary entry not found for deletion: {entry_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete diary entry {entry_id}: {str(e)}")
            return False
    
    def _entry_to_dict(self, entry: DiaryEntry) -> Dict[str, Any]:
        """Convert DiaryEntry to JSON-compatible dictionary."""
        return {
            "entry_id": entry.entry_id,
            "user_id": entry.user_id,
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "event_name": entry.event_name,
            "title": entry.title,
            "content": entry.content,
            "emotion_tags": [tag.value for tag in entry.emotion_tags],
            "agent_type": entry.agent_type,
            "llm_provider": entry.llm_provider
        }
    
    def _dict_to_entry(self, data: Dict[str, Any]) -> DiaryEntry:
        """Convert dictionary to DiaryEntry object."""
        return DiaryEntry(
            entry_id=data["entry_id"],
            user_id=data["user_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            event_name=data["event_name"],
            title=data["title"],
            content=data["content"],
            emotion_tags=[EmotionalTag(tag) for tag in data["emotion_tags"]],
            agent_type=data["agent_type"],
            llm_provider=data["llm_provider"]
        )
    
    def save_daily_quota(self, quota: DailyQuota) -> bool:
        """
        Save daily quota information.
        
        Args:
            quota: DailyQuota object to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            date_str = quota.date.strftime("%Y-%m-%d")
            filename = f"quota_{date_str}.json"
            file_path = self.quota_directory / filename
            
            quota_data = {
                "date": quota.date.isoformat(),
                "total_quota": quota.total_quota,
                "current_count": quota.current_count,
                "completed_event_types": quota.completed_event_types
            }
            
            with self._file_lock():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(quota_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved daily quota for {date_str}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save daily quota: {str(e)}")
            return False
    
    def get_daily_quota(self, target_date: date) -> Optional[DailyQuota]:
        """
        Retrieve daily quota for a specific date.
        
        Args:
            target_date: Date to retrieve quota for
            
        Returns:
            DailyQuota object if found, None otherwise
        """
        try:
            date_str = target_date.strftime("%Y-%m-%d")
            filename = f"quota_{date_str}.json"
            file_path = self.quota_directory / filename
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                quota_data = json.load(f)
                
                return DailyQuota(
                    date=datetime.fromisoformat(quota_data["date"]).date(),
                    total_quota=quota_data["total_quota"],
                    current_count=quota_data["current_count"],
                    completed_event_types=quota_data["completed_event_types"]
                )
                
        except Exception as e:
            logger.error(f"Failed to retrieve daily quota for {target_date}: {str(e)}")
            return None
    
    def create_backup(self, backup_name: Optional[str] = None) -> bool:
        """
        Create a backup of all diary data.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            bool: True if backup created successfully, False otherwise
        """
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
            
            backup_path = self.backups_directory / backup_name
            
            with self._file_lock():
                # Copy entries directory
                if self.entries_directory.exists():
                    shutil.copytree(self.entries_directory, backup_path / "entries")
                
                # Copy quotas directory
                if self.quota_directory.exists():
                    shutil.copytree(self.quota_directory, backup_path / "quotas")
                
                logger.info(f"Created backup: {backup_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return False
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore data from a backup.
        
        Args:
            backup_name: Name of the backup to restore
            
        Returns:
            bool: True if restored successfully, False otherwise
        """
        try:
            backup_path = self.backups_directory / backup_name
            
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_name}")
                return False
            
            with self._file_lock():
                # Create current backup before restore
                self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                # Remove current data
                if self.entries_directory.exists():
                    shutil.rmtree(self.entries_directory)
                if self.quota_directory.exists():
                    shutil.rmtree(self.quota_directory)
                
                # Restore from backup
                if (backup_path / "entries").exists():
                    shutil.copytree(backup_path / "entries", self.entries_directory)
                if (backup_path / "quotas").exists():
                    shutil.copytree(backup_path / "quotas", self.quota_directory)
                
                logger.info(f"Restored from backup: {backup_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_name}: {str(e)}")
            return False
    
    def list_backups(self) -> List[str]:
        """
        List available backups.
        
        Returns:
            List of backup names
        """
        try:
            backups = []
            for backup_path in self.backups_directory.iterdir():
                if backup_path.is_dir():
                    backups.append(backup_path.name)
            
            backups.sort(reverse=True)  # Most recent first
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage information
        """
        try:
            stats = {
                "total_entries": 0,
                "entries_by_user": {},
                "entries_by_date": {},
                "storage_size_mb": 0,
                "oldest_entry": None,
                "newest_entry": None
            }
            
            oldest_timestamp = None
            newest_timestamp = None
            total_size = 0
            
            # Count entries and calculate stats
            for file_path in self.entries_directory.glob("*.json"):
                try:
                    # Get file size
                    total_size += file_path.stat().st_size
                    
                    # Parse filename for user and date info
                    filename = file_path.stem
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        user_id = int(parts[0])
                        date_str = parts[1]
                        
                        # Count by user
                        stats["entries_by_user"][user_id] = stats["entries_by_user"].get(user_id, 0) + 1
                        
                        # Count by date
                        stats["entries_by_date"][date_str] = stats["entries_by_date"].get(date_str, 0) + 1
                        
                        # Track timestamps
                        with open(file_path, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            timestamp = datetime.fromisoformat(entry_data["timestamp"])
                            
                            if oldest_timestamp is None or timestamp < oldest_timestamp:
                                oldest_timestamp = timestamp
                            if newest_timestamp is None or timestamp > newest_timestamp:
                                newest_timestamp = timestamp
                    
                    stats["total_entries"] += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {str(e)}")
                    continue
            
            stats["storage_size_mb"] = round(total_size / (1024 * 1024), 2)
            stats["oldest_entry"] = oldest_timestamp.isoformat() if oldest_timestamp else None
            stats["newest_entry"] = newest_timestamp.isoformat() if newest_timestamp else None
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {}
    
    def cleanup_old_entries(self, days_to_keep: int = 365) -> int:
        """
        Clean up old diary entries beyond the retention period.
        
        Args:
            days_to_keep: Number of days to retain entries
            
        Returns:
            Number of entries deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            with self._file_lock():
                for file_path in self.entries_directory.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            timestamp = datetime.fromisoformat(entry_data["timestamp"])
                            
                            if timestamp < cutoff_date:
                                file_path.unlink()
                                deleted_count += 1
                                
                    except Exception as e:
                        logger.warning(f"Failed to process file {file_path} for cleanup: {str(e)}")
                        continue
            
            logger.info(f"Cleaned up {deleted_count} old entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old entries: {str(e)}")
            return 0


# Add missing import
from datetime import timedelta


class DiaryQueryManager:
    """Advanced querying capabilities for diary entries."""
    
    def __init__(self, persistence_manager: DiaryPersistenceManager):
        """
        Initialize query manager.
        
        Args:
            persistence_manager: DiaryPersistenceManager instance
        """
        self.persistence = persistence_manager
        self.logger = get_component_logger("data_query")
    
    def search_entries(self, query: str, user_id: Optional[int] = None, 
                      start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[DiaryEntry]:
        """
        Search diary entries by content.
        
        Args:
            query: Search query string
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of matching DiaryEntry objects
        """
        try:
            matching_entries = []
            query_lower = query.lower()
            
            # Get entries to search
            if user_id:
                entries = self.persistence.get_entries_by_user(user_id, start_date, end_date)
            else:
                # Search all entries within date range
                entries = []
                for file_path in self.persistence.entries_directory.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            entry = self.persistence._dict_to_entry(entry_data)
                            
                            # Apply date filtering
                            entry_date = entry.timestamp.date()
                            if start_date and entry_date < start_date:
                                continue
                            if end_date and entry_date > end_date:
                                continue
                                
                            entries.append(entry)
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to load entry from {file_path}: {str(e)}")
                        continue
            
            # Search in title and content
            for entry in entries:
                if (query_lower in entry.title.lower() or 
                    query_lower in entry.content.lower() or
                    query_lower in entry.event_name.lower()):
                    matching_entries.append(entry)
            
            self.logger.info(f"Found {len(matching_entries)} entries matching query: {query}")
            return matching_entries
            
        except Exception as e:
            self.logger.error(f"Failed to search entries: {str(e)}")
            return []
    
    def get_entries_by_emotion(self, emotion_tag: EmotionalTag, user_id: Optional[int] = None,
                              start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[DiaryEntry]:
        """
        Get entries filtered by emotional tag.
        
        Args:
            emotion_tag: EmotionalTag to filter by
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of matching DiaryEntry objects
        """
        try:
            matching_entries = []
            
            # Get entries to filter
            if user_id:
                entries = self.persistence.get_entries_by_user(user_id, start_date, end_date)
            else:
                # Get all entries within date range
                entries = []
                for file_path in self.persistence.entries_directory.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            entry = self.persistence._dict_to_entry(entry_data)
                            
                            # Apply date filtering
                            entry_date = entry.timestamp.date()
                            if start_date and entry_date < start_date:
                                continue
                            if end_date and entry_date > end_date:
                                continue
                                
                            entries.append(entry)
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to load entry from {file_path}: {str(e)}")
                        continue
            
            # Filter by emotion tag
            for entry in entries:
                if emotion_tag in entry.emotion_tags:
                    matching_entries.append(entry)
            
            self.logger.info(f"Found {len(matching_entries)} entries with emotion: {emotion_tag.value}")
            return matching_entries
            
        except Exception as e:
            self.logger.error(f"Failed to get entries by emotion: {str(e)}")
            return []
    
    def get_entries_by_event_type(self, event_type: str, user_id: Optional[int] = None,
                                 start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[DiaryEntry]:
        """
        Get entries filtered by event type.
        
        Args:
            event_type: Event type to filter by
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of matching DiaryEntry objects
        """
        try:
            matching_entries = []
            
            # Get entries to filter
            if user_id:
                entries = self.persistence.get_entries_by_user(user_id, start_date, end_date)
            else:
                # Get all entries within date range
                entries = []
                for file_path in self.persistence.entries_directory.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            entry = self.persistence._dict_to_entry(entry_data)
                            
                            # Apply date filtering
                            entry_date = entry.timestamp.date()
                            if start_date and entry_date < start_date:
                                continue
                            if end_date and entry_date > end_date:
                                continue
                                
                            entries.append(entry)
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to load entry from {file_path}: {str(e)}")
                        continue
            
            # Filter by event type
            for entry in entries:
                if entry.event_type == event_type:
                    matching_entries.append(entry)
            
            self.logger.info(f"Found {len(matching_entries)} entries for event type: {event_type}")
            return matching_entries
            
        except Exception as e:
            self.logger.error(f"Failed to get entries by event type: {str(e)}")
            return []
    
    def get_emotion_statistics(self, user_id: Optional[int] = None,
                              start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, int]:
        """
        Get statistics about emotional tags in diary entries.
        
        Args:
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary mapping emotion tags to counts
        """
        try:
            emotion_counts = {}
            
            # Get entries to analyze
            if user_id:
                entries = self.persistence.get_entries_by_user(user_id, start_date, end_date)
            else:
                # Get all entries within date range
                entries = []
                for file_path in self.persistence.entries_directory.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            entry = self.persistence._dict_to_entry(entry_data)
                            
                            # Apply date filtering
                            entry_date = entry.timestamp.date()
                            if start_date and entry_date < start_date:
                                continue
                            if end_date and entry_date > end_date:
                                continue
                                
                            entries.append(entry)
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to load entry from {file_path}: {str(e)}")
                        continue
            
            # Count emotions
            for entry in entries:
                for emotion_tag in entry.emotion_tags:
                    emotion_counts[emotion_tag.value] = emotion_counts.get(emotion_tag.value, 0) + 1
            
            self.logger.info(f"Generated emotion statistics for {len(entries)} entries")
            return emotion_counts
            
        except Exception as e:
            self.logger.error(f"Failed to get emotion statistics: {str(e)}")
            return {}