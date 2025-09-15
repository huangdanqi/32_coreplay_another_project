"""
Unified database reader for diary agent system.
Provides read-only access to all necessary database tables for diary generation context.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

from .database_manager import (
    DatabaseManager, EmotionDatabaseAdapter, 
    InteractionDatabaseAdapter, FriendshipDatabaseAdapter,
    DiaryStorageAdapter, DataValidator
)
from ..utils.data_models import (
    EventData, DiaryContextData, DatabaseConfig, DiaryEntry
)


class DatabaseReader:
    """
    Unified database reader that provides read-only access to existing database structures.
    Maintains compatibility with existing emotion table schema and supports diary generation context.
    """
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database reader with configuration."""
        self.config = config or DatabaseConfig()
        self.db_manager = DatabaseManager(self.config)
        
        # Initialize adapters
        self.emotion_adapter = EmotionDatabaseAdapter(self.db_manager)
        self.interaction_adapter = InteractionDatabaseAdapter(self.db_manager)
        self.friendship_adapter = FriendshipDatabaseAdapter(self.db_manager)
        self.diary_adapter = DiaryStorageAdapter(self.db_manager)
        
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """Test database connection."""
        return self.db_manager.test_connection()
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile for diary generation context.
        Returns user preferences, role, emotional state, and validation status.
        """
        user_data = self.emotion_adapter.get_user_data(user_id)
        if not user_data:
            return None
        
        # Validate user data
        validation_errors = DataValidator.validate_user_data(user_data)
        if validation_errors:
            self.logger.warning(f"User data validation errors for user {user_id}: {validation_errors}")
        
        # Enrich with additional context
        user_profile = {
            'basic_info': {
                'id': user_data.get('id'),
                'name': user_data.get('name'),
                'role': user_data.get('role')
            },
            'emotional_state': {
                'x_value': user_data.get('update_x_value', 0),
                'y_value': user_data.get('update_y_value', 0),
                'intimacy_value': user_data.get('intimacy_value', 0)
            },
            'preferences': {
                'favorite_weathers': user_data.get('favorite_weathers', []),
                'dislike_weathers': user_data.get('dislike_weathers', []),
                'favorite_seasons': user_data.get('favorite_seasons', []),
                'dislike_seasons': user_data.get('dislike_seasons', []),
                'favorite_action': user_data.get('favorite_action', []),
                'annoying_action': user_data.get('annoying_action', [])
            },
            'social_context': {
                'friend_count': self.friendship_adapter.get_friendship_count(user_id),
                'recent_interactions': len(self.interaction_adapter.get_recent_interactions(user_id, 1))
            },
            'validation_status': {
                'is_valid': len(validation_errors) == 0,
                'errors': validation_errors
            }
        }
        
        return user_profile
    
    def get_interaction_context(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Get interaction context for diary generation.
        Returns recent interactions, patterns, and statistics.
        """
        recent_interactions = self.interaction_adapter.get_recent_interactions(user_id, days)
        
        # Analyze interaction patterns
        interaction_stats = {
            'total_interactions': len(recent_interactions),
            'daily_average': len(recent_interactions) / days if days > 0 else 0,
            'interaction_types': {},
            'recent_activity': []
        }
        
        # Count interaction types
        for interaction in recent_interactions:
            interaction_type = interaction.get('interaction_type', 'unknown')
            interaction_stats['interaction_types'][interaction_type] = \
                interaction_stats['interaction_types'].get(interaction_type, 0) + 1
        
        # Get recent activity (last 3 days)
        for interaction in recent_interactions[:10]:  # Limit to last 10 interactions
            interaction_stats['recent_activity'].append({
                'type': interaction.get('interaction_type'),
                'timestamp': interaction.get('timestamp'),
                'details': interaction.get('details', {})
            })
        
        return {
            'interactions': recent_interactions,
            'statistics': interaction_stats,
            'neglect_indicators': self._analyze_neglect_patterns(user_id, recent_interactions)
        }
    
    def get_social_context(self, user_id: int) -> Dict[str, Any]:
        """
        Get social context for diary generation.
        Returns friendship data and social interaction patterns.
        """
        friends = self.friendship_adapter.get_user_friends(user_id)
        friend_count = self.friendship_adapter.get_friendship_count(user_id)
        
        # Analyze friendship patterns
        social_stats = {
            'total_friends': friend_count,
            'recent_friendships': 0,
            'friend_categories': {},
            'social_activity_level': 'low'  # low, medium, high
        }
        
        # Count recent friendships (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        for friend in friends:
            created_at = friend.get('created_at')
            if created_at and created_at >= thirty_days_ago:
                social_stats['recent_friendships'] += 1
        
        # Determine social activity level
        if friend_count >= 10:
            social_stats['social_activity_level'] = 'high'
        elif friend_count >= 3:
            social_stats['social_activity_level'] = 'medium'
        
        return {
            'friends': friends,
            'statistics': social_stats,
            'friendship_trends': self._analyze_friendship_trends(friends)
        }
    
    def get_diary_context(self, event_data: EventData) -> DiaryContextData:
        """
        Get complete diary generation context for an event.
        Combines user profile, interaction context, and social context.
        """
        user_profile = self.get_user_profile(event_data.user_id)
        if not user_profile:
            raise ValueError(f"User {event_data.user_id} not found")
        
        interaction_context = self.get_interaction_context(event_data.user_id)
        social_context = self.get_social_context(event_data.user_id)
        
        # Build environmental context based on event type
        environmental_context = self._build_environmental_context(event_data)
        
        # Build temporal context
        temporal_context = {
            'current_time': datetime.now(),
            'event_time': event_data.timestamp,
            'time_of_day': self._get_time_of_day(event_data.timestamp),
            'day_of_week': event_data.timestamp.strftime('%A'),
            'season': self._get_current_season()
        }
        
        return DiaryContextData(
            user_profile=user_profile,
            event_details=event_data.context_data,
            environmental_context=environmental_context,
            social_context=social_context,
            emotional_context=user_profile['emotional_state'],
            temporal_context=temporal_context
        )
    
    def store_diary_entry(self, diary_entry: DiaryEntry) -> bool:
        """Store a diary entry with validation."""
        # Validate diary entry
        validation_errors = DataValidator.validate_diary_entry(diary_entry)
        if validation_errors:
            self.logger.error(f"Diary entry validation failed: {validation_errors}")
            return False
        
        return self.diary_adapter.store_diary_entry(diary_entry)
    
    def get_user_diary_entries(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get diary entries for a user."""
        return self.diary_adapter.get_diary_entries(user_id, limit)
    
    def _analyze_neglect_patterns(self, user_id: int, recent_interactions: List[Dict]) -> Dict[str, Any]:
        """Analyze neglect patterns from interaction history."""
        now = datetime.now()
        
        # Check for different neglect periods
        neglect_indicators = {
            'no_interaction_1_day': False,
            'no_interaction_3_days': False,
            'no_interaction_7_days': False,
            'no_interaction_15_days': False,
            'no_interaction_30_days': False,
            'last_interaction': None,
            'days_since_last_interaction': 0
        }
        
        if recent_interactions:
            last_interaction = recent_interactions[0]  # Most recent
            last_interaction_time = last_interaction.get('timestamp')
            
            if last_interaction_time:
                neglect_indicators['last_interaction'] = last_interaction_time
                days_since = (now - last_interaction_time).days
                neglect_indicators['days_since_last_interaction'] = days_since
                
                # Set neglect flags
                neglect_indicators['no_interaction_1_day'] = days_since >= 1
                neglect_indicators['no_interaction_3_days'] = days_since >= 3
                neglect_indicators['no_interaction_7_days'] = days_since >= 7
                neglect_indicators['no_interaction_15_days'] = days_since >= 15
                neglect_indicators['no_interaction_30_days'] = days_since >= 30
        else:
            # No interactions found
            neglect_indicators.update({
                'no_interaction_1_day': True,
                'no_interaction_3_days': True,
                'no_interaction_7_days': True,
                'no_interaction_15_days': True,
                'no_interaction_30_days': True,
                'days_since_last_interaction': 999  # Unknown, assume very long
            })
        
        return neglect_indicators
    
    def _analyze_friendship_trends(self, friends: List[Dict]) -> Dict[str, Any]:
        """Analyze friendship trends and patterns."""
        if not friends:
            return {'trend': 'no_friends', 'recent_changes': 0}
        
        # Analyze recent friendship changes
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_friends = [f for f in friends if f.get('created_at', datetime.min) >= thirty_days_ago]
        
        return {
            'trend': 'growing' if len(recent_friends) > 0 else 'stable',
            'recent_changes': len(recent_friends),
            'total_friends': len(friends),
            'oldest_friendship': min(friends, key=lambda f: f.get('created_at', datetime.max)) if friends else None
        }
    
    def _build_environmental_context(self, event_data: EventData) -> Dict[str, Any]:
        """Build environmental context based on event type."""
        context = {
            'event_type': event_data.event_type,
            'event_name': event_data.event_name,
            'timestamp': event_data.timestamp
        }
        
        # Add event-specific context from metadata
        if event_data.context_data:
            context.update(event_data.context_data)
        
        return context
    
    def _get_time_of_day(self, timestamp: datetime) -> str:
        """Get time of day category."""
        hour = timestamp.hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _get_current_season(self) -> str:
        """Get current season based on month."""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Autumn'