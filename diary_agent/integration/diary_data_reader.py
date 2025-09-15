"""
Data reader for diary agent.
Provides context data for diary generation.
"""

from typing import Dict, Any
from utils.data_models import EventData, DiaryContextData


class DiaryDataReader:
    """
    Data reader for diary agent context.
    Provides basic context data for diary generation.
    """
    
    def __init__(self):
        """Initialize diary data reader."""
        pass
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read event context for diary generation.
        
        Args:
            event_data: Event data to read context for
            
        Returns:
            Context data for diary generation
        """
        # Extract context from event data
        context_data = event_data.context_data if hasattr(event_data, 'context_data') else {}
        
        # Build context data structure
        return DiaryContextData(
            user_profile=context_data.get('user_profile', {}),
            event_details=context_data.get('event_details', {'event_name': event_data.event_name}),
            environmental_context=context_data.get('environmental_context', {}),
            social_context=context_data.get('social_context', {}),
            emotional_context=context_data.get('emotional_context', {}),
            temporal_context=context_data.get('temporal_context', {'timestamp': event_data.timestamp})
        )
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Get user profile information.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile dictionary
        """
        # Default user profile - can be extended with database integration
        return {
            'user_id': user_id,
            'personality': 'calm',  # Default personality
            'preferences': {},
            'interests': []
        }
    
    def get_environmental_context(self, timestamp) -> Dict[str, Any]:
        """
        Get environmental context for a timestamp.
        
        Args:
            timestamp: Timestamp to get context for
            
        Returns:
            Environmental context dictionary
        """
        # Default environmental context
        return {
            'season': self._get_season(timestamp),
            'time_of_day': self._get_time_of_day(timestamp),
            'weather': 'unknown'
        }
    
    def _get_season(self, timestamp) -> str:
        """Get season from timestamp."""
        month = timestamp.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    def _get_time_of_day(self, timestamp) -> str:
        """Get time of day from timestamp."""
        hour = timestamp.hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
