"""
Database connection manager and compatibility layer for diary agent system.
Provides read-only access to existing database structures while maintaining
compatibility with the existing emotion calculation system.
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Any
import json
import logging
from contextlib import contextmanager
from dataclasses import asdict

from ..utils.data_models import DatabaseConfig, DiaryEntry, EmotionalTag


class DatabaseManager:
    """
    Database connection manager using existing DB_CONFIG settings.
    Provides read-only access to necessary data sources without interfering
    with existing emotion calculations.
    """
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database manager with configuration."""
        self.config = config or DatabaseConfig()
        self.logger = logging.getLogger(__name__)
        
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            conn = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database
            )
            yield conn
        except Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Error as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


class EmotionDatabaseAdapter:
    """
    Adapter for reading from the existing emotion database.
    Provides read-only access to user data needed for diary generation context.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user data from emotion table for diary context.
        Returns user preferences, role, and current emotional state.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id, name, role, update_x_value, update_y_value, intimacy_value,
                           favorite_weathers, dislike_weathers, favorite_seasons, dislike_seasons,
                           favorite_action, annoying_action
                    FROM emotion 
                    WHERE id = %s
                """, (user_id,))
                
                user_data = cursor.fetchone()
                if user_data:
                    # Parse JSON fields safely
                    user_data = self._parse_json_fields(user_data)
                    return user_data
                else:
                    self.logger.warning(f"User {user_id} not found in emotion table")
                    return None
                    
        except Error as e:
            self.logger.error(f"Error fetching user data for user {user_id}: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from emotion table."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id, name, role, update_x_value, update_y_value, intimacy_value,
                           favorite_weathers, dislike_weathers, favorite_seasons, dislike_seasons,
                           favorite_action, annoying_action
                    FROM emotion
                """)
                
                users = cursor.fetchall()
                return [self._parse_json_fields(user) for user in users]
                
        except Error as e:
            self.logger.error(f"Error fetching all users: {e}")
            return []
    
    def _parse_json_fields(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON string fields in user data."""
        json_fields = [
            'favorite_weathers', 'dislike_weathers', 
            'favorite_seasons', 'dislike_seasons',
            'favorite_action', 'annoying_action'
        ]
        
        for field in json_fields:
            if field in user_data and user_data[field]:
                try:
                    if isinstance(user_data[field], str):
                        user_data[field] = json.loads(user_data[field])
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON field {field} for user {user_data.get('id')}: {e}")
                    user_data[field] = []
        
        return user_data


class InteractionDatabaseAdapter:
    """
    Adapter for reading from toy interaction events table.
    Provides access to interaction history for diary context.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_recent_interactions(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent interactions for a user within specified days."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM toy_interaction_events 
                    WHERE user_id = %s 
                    AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    ORDER BY timestamp DESC
                """, (user_id, days))
                
                return cursor.fetchall()
                
        except Error as e:
            self.logger.error(f"Error fetching interactions for user {user_id}: {e}")
            return []
    
    def get_interaction_count(self, user_id: int, interaction_type: str = None, days: int = 1) -> int:
        """Get count of interactions for a user within specified days."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if interaction_type:
                    cursor.execute("""
                        SELECT COUNT(*) FROM toy_interaction_events 
                        WHERE user_id = %s AND interaction_type = %s
                        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    """, (user_id, interaction_type, days))
                else:
                    cursor.execute("""
                        SELECT COUNT(*) FROM toy_interaction_events 
                        WHERE user_id = %s 
                        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    """, (user_id, days))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Error as e:
            self.logger.error(f"Error counting interactions for user {user_id}: {e}")
            return 0


class FriendshipDatabaseAdapter:
    """
    Adapter for reading from toy friendships table.
    Provides access to friendship data for diary context.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_user_friends(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all friends for a user."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM toy_friendships 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                
                return cursor.fetchall()
                
        except Error as e:
            self.logger.error(f"Error fetching friends for user {user_id}: {e}")
            return []
    
    def get_friendship_count(self, user_id: int) -> int:
        """Get total number of friends for a user."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM toy_friendships 
                    WHERE user_id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Error as e:
            self.logger.error(f"Error counting friends for user {user_id}: {e}")
            return 0


class DiaryStorageAdapter:
    """
    Adapter for storing diary entries.
    Creates and manages diary entry storage separate from emotion calculations.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._ensure_diary_table()
    
    def _ensure_diary_table(self):
        """Ensure diary entries table exists."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS diary_entries (
                        id VARCHAR(255) PRIMARY KEY,
                        user_id INT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        event_name VARCHAR(100) NOT NULL,
                        title VARCHAR(6) NOT NULL,
                        content VARCHAR(35) NOT NULL,
                        emotion_tags JSON,
                        agent_type VARCHAR(50) NOT NULL,
                        llm_provider VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_user_id (user_id),
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_event_type (event_type)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                conn.commit()
                
        except Error as e:
            self.logger.error(f"Error creating diary entries table: {e}")
            raise
    
    def store_diary_entry(self, diary_entry: DiaryEntry) -> bool:
        """Store a diary entry in the database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert emotion tags to JSON
                emotion_tags_json = json.dumps([tag.value for tag in diary_entry.emotion_tags])
                
                cursor.execute("""
                    INSERT INTO diary_entries 
                    (id, user_id, timestamp, event_type, event_name, title, content, 
                     emotion_tags, agent_type, llm_provider)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    diary_entry.entry_id,
                    diary_entry.user_id,
                    diary_entry.timestamp,
                    diary_entry.event_type,
                    diary_entry.event_name,
                    diary_entry.title,
                    diary_entry.content,
                    emotion_tags_json,
                    diary_entry.agent_type,
                    diary_entry.llm_provider
                ))
                
                conn.commit()
                return True
                
        except Error as e:
            self.logger.error(f"Error storing diary entry {diary_entry.entry_id}: {e}")
            return False
    
    def get_diary_entries(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get diary entries for a user."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM diary_entries 
                    WHERE user_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (user_id, limit))
                
                entries = cursor.fetchall()
                
                # Parse emotion tags JSON
                for entry in entries:
                    if entry['emotion_tags']:
                        try:
                            entry['emotion_tags'] = json.loads(entry['emotion_tags'])
                        except json.JSONDecodeError:
                            entry['emotion_tags'] = []
                
                return entries
                
        except Error as e:
            self.logger.error(f"Error fetching diary entries for user {user_id}: {e}")
            return []


class DataValidator:
    """
    Validates data formats for existing JSON field formats and diary entries.
    """
    
    @staticmethod
    def validate_json_field(field_value: Any, field_name: str) -> bool:
        """Validate JSON field format."""
        if field_value is None:
            return True
        
        if isinstance(field_value, str):
            try:
                json.loads(field_value)
                return True
            except json.JSONDecodeError:
                return False
        elif isinstance(field_value, (list, dict)):
            return True
        
        return False
    
    @staticmethod
    def validate_diary_entry(diary_entry: DiaryEntry) -> List[str]:
        """Validate diary entry format and return list of errors."""
        errors = []
        
        # Validate title length (max 6 characters)
        if len(diary_entry.title) > 6:
            errors.append(f"Title too long: {len(diary_entry.title)} characters (max 6)")
        
        # Validate content length (max 35 characters)
        if len(diary_entry.content) > 35:
            errors.append(f"Content too long: {len(diary_entry.content)} characters (max 35)")
        
        # Validate emotion tags
        if not diary_entry.emotion_tags:
            errors.append("At least one emotion tag is required")
        
        for tag in diary_entry.emotion_tags:
            if not isinstance(tag, EmotionalTag):
                errors.append(f"Invalid emotion tag: {tag}")
        
        # Validate required fields
        required_fields = ['entry_id', 'user_id', 'event_type', 'event_name', 'agent_type']
        for field in required_fields:
            if not getattr(diary_entry, field):
                errors.append(f"Required field missing: {field}")
        
        return errors
    
    @staticmethod
    def validate_user_data(user_data: Dict[str, Any]) -> List[str]:
        """Validate user data format."""
        errors = []
        
        # Check required fields
        required_fields = ['id', 'name', 'role']
        for field in required_fields:
            if field not in user_data:
                errors.append(f"Required field missing: {field}")
        
        # Validate JSON fields
        json_fields = [
            'favorite_weathers', 'dislike_weathers',
            'favorite_seasons', 'dislike_seasons',
            'favorite_action', 'annoying_action'
        ]
        
        for field in json_fields:
            if field in user_data and not DataValidator.validate_json_field(user_data[field], field):
                errors.append(f"Invalid JSON format in field: {field}")
        
        return errors  
  
    async def initialize(self):
        """Initialize the database manager (async compatibility)."""
        # Test connection to ensure database is accessible
        return self.test_connection()
    
    def close(self):
        """Close database connections (sync compatibility)."""
        # No persistent connections to close in this implementation
        pass
    
    async def async_close(self):
        """Close database connections (async compatibility)."""
        # No persistent connections to close in this implementation
        pass
    
    def is_connected(self) -> bool:
        """Check if database is accessible."""
        return self.test_connection()
    
    async def health_check(self) -> bool:
        """Perform health check on database connection."""
        return self.test_connection()