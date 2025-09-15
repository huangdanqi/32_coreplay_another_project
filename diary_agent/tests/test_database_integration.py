"""
Unit tests for database integration and compatibility layer.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
import mysql.connector

from diary_agent.integration.database_manager import (
    DatabaseManager, EmotionDatabaseAdapter, InteractionDatabaseAdapter,
    FriendshipDatabaseAdapter, DiaryStorageAdapter, DataValidator
)
from diary_agent.integration.database_reader import DatabaseReader
from diary_agent.utils.data_models import (
    DatabaseConfig, DiaryEntry, EmotionalTag, EventData, DiaryContextData
)


class TestDatabaseManager(unittest.TestCase):
    """Test database connection manager."""
    
    def setUp(self):
        self.config = DatabaseConfig(
            host="test_host",
            port=3306,
            user="test_user",
            password="test_pass",
            database="test_db"
        )
        self.db_manager = DatabaseManager(self.config)
    
    @patch('mysql.connector.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with self.db_manager.get_connection() as conn:
            self.assertEqual(conn, mock_conn)
        
        mock_connect.assert_called_once_with(
            host="test_host",
            port=3306,
            user="test_user",
            password="test_pass",
            database="test_db"
        )
    
    @patch('mysql.connector.connect')
    def test_get_connection_error(self, mock_connect):
        """Test database connection error handling."""
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        with self.assertRaises(mysql.connector.Error):
            with self.db_manager.get_connection() as conn:
                pass
    
    @patch('mysql.connector.connect')
    def test_test_connection_success(self, mock_connect):
        """Test connection test success."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = self.db_manager.test_connection()
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_cursor.fetchone.assert_called_once()
    
    @patch('mysql.connector.connect')
    def test_test_connection_failure(self, mock_connect):
        """Test connection test failure."""
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        result = self.db_manager.test_connection()
        
        self.assertFalse(result)


class TestEmotionDatabaseAdapter(unittest.TestCase):
    """Test emotion database adapter."""
    
    def setUp(self):
        self.db_manager = Mock()
        self.adapter = EmotionDatabaseAdapter(self.db_manager)
    
    def test_get_user_data_success(self):
        """Test successful user data retrieval."""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Mock user data with JSON fields
        user_data = {
            'id': 1,
            'name': 'test_user',
            'role': 'clam',
            'update_x_value': 5,
            'update_y_value': -2,
            'intimacy_value': 10,
            'favorite_weathers': '["Sunny", "Clear"]',
            'dislike_weathers': '["Rain", "Storm"]',
            'favorite_seasons': '["Spring", "Summer"]',
            'dislike_seasons': '["Winter"]',
            'favorite_action': '["play", "talk"]',
            'annoying_action': '["ignore"]'
        }
        
        mock_cursor.fetchone.return_value = user_data
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        result = self.adapter.get_user_data(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], 'test_user')
        self.assertEqual(result['favorite_weathers'], ["Sunny", "Clear"])
        self.assertEqual(result['dislike_weathers'], ["Rain", "Storm"])
    
    def test_get_user_data_not_found(self):
        """Test user data retrieval when user not found."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        result = self.adapter.get_user_data(999)
        
        self.assertIsNone(result)
    
    def test_parse_json_fields_valid(self):
        """Test parsing valid JSON fields."""
        user_data = {
            'id': 1,
            'favorite_weathers': '["Sunny", "Clear"]',
            'dislike_weathers': '["Rain"]'
        }
        
        result = self.adapter._parse_json_fields(user_data)
        
        self.assertEqual(result['favorite_weathers'], ["Sunny", "Clear"])
        self.assertEqual(result['dislike_weathers'], ["Rain"])
    
    def test_parse_json_fields_invalid(self):
        """Test parsing invalid JSON fields."""
        user_data = {
            'id': 1,
            'favorite_weathers': 'invalid_json',
            'dislike_weathers': '["Rain"]'
        }
        
        result = self.adapter._parse_json_fields(user_data)
        
        self.assertEqual(result['favorite_weathers'], [])  # Should default to empty list
        self.assertEqual(result['dislike_weathers'], ["Rain"])


class TestInteractionDatabaseAdapter(unittest.TestCase):
    """Test interaction database adapter."""
    
    def setUp(self):
        self.db_manager = Mock()
        self.adapter = InteractionDatabaseAdapter(self.db_manager)
    
    def test_get_recent_interactions(self):
        """Test getting recent interactions."""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        interactions = [
            {'id': 1, 'user_id': 1, 'interaction_type': 'play', 'timestamp': datetime.now()},
            {'id': 2, 'user_id': 1, 'interaction_type': 'talk', 'timestamp': datetime.now()}
        ]
        
        mock_cursor.fetchall.return_value = interactions
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        result = self.adapter.get_recent_interactions(1, 7)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['interaction_type'], 'play')
    
    def test_get_interaction_count(self):
        """Test getting interaction count."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (5,)
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        result = self.adapter.get_interaction_count(1, 'play', 1)
        
        self.assertEqual(result, 5)


class TestFriendshipDatabaseAdapter(unittest.TestCase):
    """Test friendship database adapter."""
    
    def setUp(self):
        self.db_manager = Mock()
        self.adapter = FriendshipDatabaseAdapter(self.db_manager)
    
    def test_get_user_friends(self):
        """Test getting user friends."""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        friends = [
            {'id': 1, 'user_id': 1, 'friend_name': 'Alice', 'created_at': datetime.now()},
            {'id': 2, 'user_id': 1, 'friend_name': 'Bob', 'created_at': datetime.now()}
        ]
        
        mock_cursor.fetchall.return_value = friends
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        result = self.adapter.get_user_friends(1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['friend_name'], 'Alice')
    
    def test_get_friendship_count(self):
        """Test getting friendship count."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (3,)
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        result = self.adapter.get_friendship_count(1)
        
        self.assertEqual(result, 3)


class TestDiaryStorageAdapter(unittest.TestCase):
    """Test diary storage adapter."""
    
    def setUp(self):
        self.db_manager = Mock()
        
        # Mock context manager for _ensure_diary_table
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=Mock())
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        self.adapter = DiaryStorageAdapter(self.db_manager)
    
    def test_store_diary_entry(self):
        """Test storing diary entry."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        diary_entry = DiaryEntry(
            entry_id="test_123",
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
        
        result = self.adapter.store_diary_entry(diary_entry)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_get_diary_entries(self):
        """Test getting diary entries."""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        entries = [
            {
                'id': 'test_123',
                'user_id': 1,
                'title': '晴天',
                'content': '今天天气很好',
                'emotion_tags': '["开心快乐"]',
                'timestamp': datetime.now()
            }
        ]
        
        mock_cursor.fetchall.return_value = entries
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=None)
        self.db_manager.get_connection.return_value = mock_context
        
        result = self.adapter.get_diary_entries(1, 10)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], '晴天')
        self.assertEqual(result[0]['emotion_tags'], ["开心快乐"])


class TestDataValidator(unittest.TestCase):
    """Test data validation utilities."""
    
    def test_validate_json_field_valid_string(self):
        """Test validating valid JSON string."""
        result = DataValidator.validate_json_field('["item1", "item2"]', 'test_field')
        self.assertTrue(result)
    
    def test_validate_json_field_invalid_string(self):
        """Test validating invalid JSON string."""
        result = DataValidator.validate_json_field('invalid_json', 'test_field')
        self.assertFalse(result)
    
    def test_validate_json_field_list(self):
        """Test validating list object."""
        result = DataValidator.validate_json_field(['item1', 'item2'], 'test_field')
        self.assertTrue(result)
    
    def test_validate_json_field_none(self):
        """Test validating None value."""
        result = DataValidator.validate_json_field(None, 'test_field')
        self.assertTrue(result)
    
    def test_validate_diary_entry_valid(self):
        """Test validating valid diary entry."""
        diary_entry = DiaryEntry(
            entry_id="test_123",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather",
            event_name="favorite_weather",
            title="晴天",
            content="今天天气很好😊",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        errors = DataValidator.validate_diary_entry(diary_entry)
        self.assertEqual(len(errors), 0)
    
    def test_validate_diary_entry_title_too_long(self):
        """Test validating diary entry with title too long."""
        diary_entry = DiaryEntry(
            entry_id="test_123",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather",
            event_name="favorite_weather",
            title="这个标题太长了",  # 7 characters, exceeds limit
            content="内容",
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        errors = DataValidator.validate_diary_entry(diary_entry)
        self.assertTrue(any("Title too long" in error for error in errors))
    
    def test_validate_diary_entry_content_too_long(self):
        """Test validating diary entry with content too long."""
        diary_entry = DiaryEntry(
            entry_id="test_123",
            user_id=1,
            timestamp=datetime.now(),
            event_type="weather",
            event_name="favorite_weather",
            title="晴天",
            content="这是一个非常非常非常非常非常非常非常非常非常非常长的内容，超过了35个字符的限制",  # Too long
            emotion_tags=[EmotionalTag.HAPPY_JOYFUL],
            agent_type="weather_agent",
            llm_provider="qwen"
        )
        
        errors = DataValidator.validate_diary_entry(diary_entry)
        self.assertTrue(any("Content too long" in error for error in errors))
    
    def test_validate_user_data_valid(self):
        """Test validating valid user data."""
        user_data = {
            'id': 1,
            'name': 'test_user',
            'role': 'clam',
            'favorite_weathers': ["Sunny"],
            'dislike_weathers': ["Rain"]
        }
        
        errors = DataValidator.validate_user_data(user_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_user_data_missing_fields(self):
        """Test validating user data with missing required fields."""
        user_data = {
            'id': 1
            # Missing 'name' and 'role'
        }
        
        errors = DataValidator.validate_user_data(user_data)
        self.assertTrue(any("name" in error for error in errors))
        self.assertTrue(any("role" in error for error in errors))


class TestDatabaseReader(unittest.TestCase):
    """Test unified database reader."""
    
    def setUp(self):
        self.config = DatabaseConfig()
        
        # Mock all adapters
        with patch('diary_agent.integration.database_reader.DatabaseManager'), \
             patch('diary_agent.integration.database_reader.EmotionDatabaseAdapter'), \
             patch('diary_agent.integration.database_reader.InteractionDatabaseAdapter'), \
             patch('diary_agent.integration.database_reader.FriendshipDatabaseAdapter'), \
             patch('diary_agent.integration.database_reader.DiaryStorageAdapter'):
            
            self.reader = DatabaseReader(self.config)
    
    def test_get_user_profile_success(self):
        """Test getting user profile successfully."""
        # Mock user data
        user_data = {
            'id': 1,
            'name': 'test_user',
            'role': 'clam',
            'update_x_value': 5,
            'update_y_value': -2,
            'intimacy_value': 10,
            'favorite_weathers': ["Sunny"],
            'dislike_weathers': ["Rain"],
            'favorite_seasons': ["Spring"],
            'dislike_seasons': ["Winter"],
            'favorite_action': ["play"],
            'annoying_action': ["ignore"]
        }
        
        self.reader.emotion_adapter.get_user_data.return_value = user_data
        self.reader.friendship_adapter.get_friendship_count.return_value = 3
        self.reader.interaction_adapter.get_recent_interactions.return_value = [{'id': 1}]
        
        result = self.reader.get_user_profile(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['basic_info']['id'], 1)
        self.assertEqual(result['basic_info']['name'], 'test_user')
        self.assertEqual(result['emotional_state']['x_value'], 5)
        self.assertEqual(result['preferences']['favorite_weathers'], ["Sunny"])
        self.assertEqual(result['social_context']['friend_count'], 3)
    
    def test_get_user_profile_not_found(self):
        """Test getting user profile when user not found."""
        self.reader.emotion_adapter.get_user_data.return_value = None
        
        result = self.reader.get_user_profile(999)
        
        self.assertIsNone(result)
    
    def test_get_diary_context(self):
        """Test getting complete diary context."""
        # Mock event data
        event_data = EventData(
            event_id="test_event",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={'weather': 'Sunny', 'temperature': 25},
            metadata={}
        )
        
        # Mock user profile
        user_profile = {
            'basic_info': {'id': 1, 'name': 'test_user', 'role': 'clam'},
            'emotional_state': {'x_value': 5, 'y_value': -2, 'intimacy_value': 10},
            'preferences': {'favorite_weathers': ["Sunny"]},
            'social_context': {'friend_count': 3},
            'validation_status': {'is_valid': True, 'errors': []}
        }
        
        self.reader.get_user_profile = Mock(return_value=user_profile)
        self.reader.get_interaction_context = Mock(return_value={'interactions': [], 'statistics': {}})
        self.reader.get_social_context = Mock(return_value={'friends': [], 'statistics': {}})
        
        result = self.reader.get_diary_context(event_data)
        
        self.assertIsInstance(result, DiaryContextData)
        self.assertEqual(result.user_profile, user_profile)
        self.assertEqual(result.event_details, {'weather': 'Sunny', 'temperature': 25})


if __name__ == '__main__':
    unittest.main()