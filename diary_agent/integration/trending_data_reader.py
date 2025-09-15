"""
Trending data reader for integrating with existing douyin_news.py module.
Provides read-only access to trending news event data for diary generation context.
"""

import json
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the hewan_emotion_cursor_python directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hewan_emotion_cursor_python'))

try:
    from douyin_news import (
        load_douyin_hot_words, classify_douyin_news, 
        DISASTER_KEYWORDS, CELEBRATION_KEYWORDS, ROLE_WEIGHTS
    )
    from db_utils import get_emotion_data
except ImportError as e:
    print(f"Warning: Could not import douyin_news functions: {e}")
    # Define fallback functions for testing
    def load_douyin_hot_words(file_path=None, page_size=50): return []
    def classify_douyin_news(words): return None
    def get_emotion_data(): return []
    DISASTER_KEYWORDS = []
    CELEBRATION_KEYWORDS = []
    ROLE_WEIGHTS = {"disaster": {"lively": 1.5, "clam": 1.0}, "celebration": {"lively": 2.0, "clam": 1.5}}

from diary_agent.utils.data_models import EventData, DiaryContextData, DataReader


class TrendingDataReader(DataReader):
    """
    Data reader for trending events that interfaces with existing douyin_news.py.
    Provides read-only access to trending news data for diary generation context.
    """
    
    def __init__(self):
        super().__init__(module_name="douyin_news", read_only=True)
        self.supported_events = ["celebration", "disaster"]
        self.default_page_size = 50
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """
        Read trending event context from existing douyin_news.py module.
        
        Args:
            event_data: Event data containing user_id and event details
            
        Returns:
            DiaryContextData with trending context for diary generation
        """
        try:
            # Get user data from emotion database
            user_profile = self.get_user_preferences(event_data.user_id)
            if not user_profile:
                return self._create_minimal_context(event_data)
            
            # Get trending words from douyin file
            file_path = event_data.metadata.get("douyin_file_path")
            page_size = event_data.metadata.get("page_size", self.default_page_size)
            
            trending_words = load_douyin_hot_words(file_path=file_path, page_size=page_size)
            
            # Classify trending words
            event_classification = classify_douyin_news(trending_words)
            
            # Analyze event details
            event_details = self._analyze_trending_event(
                event_data.event_name, event_classification, trending_words, user_profile
            )
            
            # Build social context with trending information
            social_context = {
                "trending_words": trending_words[:10],  # Top 10 words for context
                "total_words_count": len(trending_words),
                "event_classification": event_classification,
                "matched_keywords": self._get_matched_keywords(trending_words, event_data.event_name),
                "trending_topics": self._extract_trending_topics(trending_words),
                "social_sentiment": self._analyze_social_sentiment(event_data.event_name, trending_words)
            }
            
            # Build emotional context
            emotional_context = {
                "event_emotional_impact": self._calculate_event_emotional_impact(
                    event_data.event_name, user_profile.get("role", "clam")
                ),
                "social_emotional_tone": self._determine_social_emotional_tone(event_data.event_name),
                "emotional_intensity": self._calculate_emotional_intensity(
                    user_profile.get("role", "clam"), event_data.event_name
                )
            }
            
            # Build environmental context (news environment)
            environmental_context = {
                "news_environment": "social_media",
                "information_source": "douyin_trending",
                "data_freshness": self._get_data_freshness(event_data.timestamp),
                "trending_context": event_classification or "neutral"
            }
            
            # Build temporal context
            temporal_context = {
                "timestamp": event_data.timestamp,
                "time_of_day": self._get_time_of_day(event_data.timestamp),
                "news_timing": self._analyze_news_timing(event_data.timestamp)
            }
            
            return DiaryContextData(
                user_profile=user_profile,
                event_details=event_details,
                environmental_context=environmental_context,
                social_context=social_context,
                emotional_context=emotional_context,
                temporal_context=temporal_context
            )
            
        except Exception as e:
            print(f"Error reading trending event context: {e}")
            return self._create_minimal_context(event_data)
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from emotion database.
        
        Args:
            user_id: User ID to get preferences for
            
        Returns:
            User profile dictionary or None if not found
        """
        try:
            all_emotion_data = get_emotion_data()
            user_data = next((item for item in all_emotion_data if item["id"] == user_id), None)
            return user_data
        except Exception as e:
            print(f"Error getting user preferences for user {user_id}: {e}")
            return None
    
    def _create_minimal_context(self, event_data: EventData) -> DiaryContextData:
        """Create minimal context when data reading fails."""
        return DiaryContextData(
            user_profile={"id": event_data.user_id, "role": "clam"},
            event_details={"event_name": event_data.event_name, "event_type": "trending"},
            environmental_context={"news_environment": "social_media"},
            social_context={"trending_words": [], "event_classification": event_data.event_name},
            emotional_context={"event_emotional_impact": "neutral"},
            temporal_context={"timestamp": event_data.timestamp}
        )
    
    def _analyze_trending_event(self, event_name: str, classification: Optional[str], 
                               trending_words: List[str], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze trending event to determine context details.
        
        Args:
            event_name: Name of the trending event
            classification: Classification result from douyin_news
            trending_words: List of trending words
            user_profile: User profile data
            
        Returns:
            Event details dictionary
        """
        event_details = {
            "event_name": event_name,
            "event_type": "trending",
            "classification": classification,
            "user_role": user_profile.get("role", "clam"),
            "classification_match": classification == event_name if classification else False
        }
        
        # Add keyword analysis
        if event_name == "disaster":
            matched_keywords = [kw for kw in DISASTER_KEYWORDS if any(kw in word for word in trending_words)]
            event_details["matched_keywords"] = matched_keywords
            event_details["keyword_strength"] = len(matched_keywords)
        elif event_name == "celebration":
            matched_keywords = [kw for kw in CELEBRATION_KEYWORDS if any(kw in word for word in trending_words)]
            event_details["matched_keywords"] = matched_keywords
            event_details["keyword_strength"] = len(matched_keywords)
        else:
            event_details["matched_keywords"] = []
            event_details["keyword_strength"] = 0
        
        # Add trending word analysis
        event_details["sample_trending_words"] = trending_words[:5]  # First 5 words for context
        event_details["total_trending_words"] = len(trending_words)
        
        return event_details
    
    def _get_matched_keywords(self, trending_words: List[str], event_name: str) -> List[str]:
        """Get keywords that match the event type from trending words."""
        matched = []
        keywords = DISASTER_KEYWORDS if event_name == "disaster" else CELEBRATION_KEYWORDS
        
        for word in trending_words:
            for keyword in keywords:
                if keyword in word:
                    matched.append(keyword)
        
        return list(set(matched))  # Remove duplicates
    
    def _extract_trending_topics(self, trending_words: List[str]) -> List[str]:
        """Extract main topics from trending words."""
        # Simple topic extraction - take first few words as main topics
        return trending_words[:5] if trending_words else []
    
    def _analyze_social_sentiment(self, event_name: str, trending_words: List[str]) -> str:
        """Analyze overall social sentiment from trending words."""
        if event_name == "disaster":
            return "negative"
        elif event_name == "celebration":
            return "positive"
        else:
            return "neutral"
    
    def _calculate_event_emotional_impact(self, event_name: str, role: str) -> str:
        """Calculate emotional impact based on event type and user role."""
        if event_name == "disaster":
            return "high_negative" if role == "lively" else "moderate_negative"
        elif event_name == "celebration":
            return "high_positive" if role == "lively" else "moderate_positive"
        else:
            return "neutral"
    
    def _determine_social_emotional_tone(self, event_name: str) -> str:
        """Determine the emotional tone of social context."""
        tone_mapping = {
            "disaster": "somber",
            "celebration": "joyful"
        }
        return tone_mapping.get(event_name, "neutral")
    
    def _calculate_emotional_intensity(self, role: str, event_name: str) -> float:
        """Calculate emotional intensity based on role and event type."""
        role = role.lower()
        if role not in ["lively", "clam"]:
            role = "clam"
        
        if event_name in ROLE_WEIGHTS:
            return ROLE_WEIGHTS[event_name][role]
        else:
            return 1.0
    
    def _get_data_freshness(self, timestamp: datetime) -> str:
        """Determine how fresh the trending data is."""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.total_seconds() < 3600:  # Less than 1 hour
            return "very_fresh"
        elif diff.total_seconds() < 86400:  # Less than 1 day
            return "fresh"
        else:
            return "older"
    
    def _get_time_of_day(self, timestamp: datetime) -> str:
        """Get time of day description."""
        hour = timestamp.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _analyze_news_timing(self, timestamp: datetime) -> str:
        """Analyze timing context for news events."""
        hour = timestamp.hour
        
        if 6 <= hour < 9:
            return "morning_news"
        elif 12 <= hour < 14:
            return "lunch_news"
        elif 18 <= hour < 22:
            return "evening_news"
        else:
            return "off_peak_news"
    
    def get_supported_events(self) -> List[str]:
        """Get list of supported trending events."""
        return self.supported_events.copy()