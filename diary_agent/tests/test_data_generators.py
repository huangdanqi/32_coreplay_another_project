"""
Test data generators for various event types and scenarios.
Provides realistic test data for integration and end-to-end testing.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from diary_agent.utils.data_models import EventData, DiaryContextData


class DiaryTestDataGenerator:
    """Generates test data for various event types and scenarios."""
    
    def __init__(self):
        self.emotional_tags = [
            "生气愤怒", "悲伤难过", "担忧", "焦虑忧愁", "惊讶震惊",
            "好奇", "羞愧", "平静", "开心快乐", "兴奋激动"
        ]
        
        self.weather_conditions = ["Clear", "Sunny", "Cloudy", "Rain", "Storm", "Snow"]
        self.seasons = ["Spring", "Summer", "Autumn", "Winter"]
        self.cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou"]
        
    def generate_weather_event(self, user_id: int = 1, event_name: str = "favorite_weather") -> EventData:
        """Generate weather event test data."""
        return EventData(
            event_id=f"weather_{random.randint(1000, 9999)}",
            event_type="weather_events",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={
                "weather_condition": random.choice(self.weather_conditions),
                "temperature": random.randint(-10, 35),
                "city": random.choice(self.cities),
                "season": random.choice(self.seasons)
            },
            metadata={"source": "test_generator"}
        )
    
    def generate_trending_event(self, user_id: int = 1, event_name: str = "celebration") -> EventData:
        """Generate trending event test data."""
        trending_topics = [
            "春节庆祝活动", "国庆节庆典", "中秋节团圆", "元宵节灯会",
            "地震救援", "洪水灾害", "台风预警", "火灾事故"
        ]
        
        return EventData(
            event_id=f"trending_{random.randint(1000, 9999)}",
            event_type="trending_events", 
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={
                "trending_topic": random.choice(trending_topics),
                "keyword_classification": "celebration" if event_name == "celebration" else "disaster",
                "probability_score": random.uniform(0.6, 0.9)
            },
            metadata={"source": "douyin_news"}
        )
    
    def generate_holiday_event(self, user_id: int = 1, event_name: str = "approaching_holiday") -> EventData:
        """Generate holiday event test data."""
        holidays = ["春节", "清明节", "劳动节", "端午节", "中秋节", "国庆节"]
        
        return EventData(
            event_id=f"holiday_{random.randint(1000, 9999)}",
            event_type="holiday_events",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={
                "holiday_name": random.choice(holidays),
                "days_until_holiday": random.randint(1, 30) if "approaching" in event_name else 0,
                "holiday_type": "traditional",
                "celebration_activities": ["团圆饭", "放烟花", "赏月", "踏青"]
            },
            metadata={"source": "chinese_calendar"}
        )
    
    def generate_friends_event(self, user_id: int = 1, event_name: str = "made_new_friend") -> EventData:
        """Generate friends event test data."""
        return EventData(
            event_id=f"friends_{random.randint(1000, 9999)}",
            event_type="friends_events",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={
                "friend_count": random.randint(1, 10),
                "interaction_type": "positive" if "liked" in event_name else "negative",
                "friendship_level": random.choice(["new", "close", "best"]),
                "activity": random.choice(["聊天", "游戏", "学习", "运动"])
            },
            metadata={"source": "friends_function"}
        )
    
    def generate_interaction_event(self, user_id: int = 1, event_name: str = "liked_interaction_once") -> EventData:
        """Generate human-toy interaction event test data."""
        return EventData(
            event_id=f"interaction_{random.randint(1000, 9999)}",
            event_type="interaction_events",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={
                "interaction_count": 1 if "once" in event_name else random.randint(3, 10),
                "interaction_type": "positive" if "liked" in event_name else "negative",
                "duration_minutes": random.randint(5, 60),
                "activities": ["抚摸", "对话", "游戏", "拥抱"]
            },
            metadata={"source": "human_toy_interactive"}
        )
    
    def generate_dialogue_event(self, user_id: int = 1, event_name: str = "positive_emotional_dialogue") -> EventData:
        """Generate dialogue event test data."""
        return EventData(
            event_id=f"dialogue_{random.randint(1000, 9999)}",
            event_type="dialogue_events",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={
                "dialogue_type": "positive" if "positive" in event_name else "negative",
                "conversation_length": random.randint(5, 30),
                "emotional_intensity": random.uniform(0.3, 0.9),
                "topics": ["日常生活", "学习工作", "情感交流", "未来计划"]
            },
            metadata={"source": "human_toy_talk"}
        )
    
    def generate_neglect_event(self, user_id: int = 1, event_name: str = "neglect_1_day_no_dialogue") -> EventData:
        """Generate neglect event test data."""
        days_neglected = 1
        if "3_days" in event_name:
            days_neglected = 3
        elif "7_days" in event_name:
            days_neglected = 7
        elif "15_days" in event_name:
            days_neglected = 15
        elif "30_days" in event_name:
            days_neglected = 30
            
        return EventData(
            event_id=f"neglect_{random.randint(1000, 9999)}",
            event_type="neglect_events",
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={
                "days_neglected": days_neglected,
                "neglect_type": "dialogue" if "dialogue" in event_name else "interaction",
                "last_interaction": datetime.now() - timedelta(days=days_neglected),
                "emotional_impact": "high" if days_neglected >= 7 else "medium"
            },
            metadata={"source": "unkeep_interactive"}
        )
    
    def generate_user_profile(self, user_id: int = 1, role: str = "clam") -> Dict[str, Any]:
        """Generate user profile test data."""
        return {
            "id": user_id,
            "name": f"test_user_{user_id}",
            "role": role,
            "favorite_weathers": json.dumps(random.sample(self.weather_conditions, 2)),
            "dislike_weathers": json.dumps(random.sample(self.weather_conditions, 2)),
            "favorite_seasons": json.dumps(random.sample(self.seasons, 2)),
            "dislike_seasons": json.dumps(random.sample(self.seasons, 1)),
            "x_axis": random.randint(-10, 10),
            "y_axis": random.randint(-10, 10),
            "intimacy": random.randint(0, 100)
        }
    
    def generate_diary_context_data(self, event_data: EventData) -> DiaryContextData:
        """Generate diary context data for testing."""
        return DiaryContextData(
            user_profile=self.generate_user_profile(event_data.user_id),
            event_details=event_data.context_data,
            environmental_context={
                "weather": random.choice(self.weather_conditions),
                "temperature": random.randint(-10, 35),
                "time_of_day": random.choice(["morning", "afternoon", "evening", "night"])
            },
            social_context={
                "friend_count": random.randint(0, 10),
                "recent_interactions": random.randint(0, 5)
            },
            emotional_context={
                "current_emotion": random.choice(self.emotional_tags),
                "emotion_intensity": random.uniform(0.1, 1.0)
            },
            temporal_context={
                "season": random.choice(self.seasons),
                "is_holiday": random.choice([True, False]),
                "day_of_week": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            }
        )
    
    def generate_batch_events(self, count: int = 10, event_types: List[str] = None) -> List[EventData]:
        """Generate a batch of mixed event types for testing."""
        if event_types is None:
            event_types = [
                "favorite_weather", "celebration", "approaching_holiday",
                "made_new_friend", "liked_interaction_once", "positive_emotional_dialogue"
            ]
        
        events = []
        for i in range(count):
            event_type = random.choice(event_types)
            user_id = random.randint(1, 5)
            
            if "weather" in event_type:
                events.append(self.generate_weather_event(user_id, event_type))
            elif event_type in ["celebration", "disaster"]:
                events.append(self.generate_trending_event(user_id, event_type))
            elif "holiday" in event_type:
                events.append(self.generate_holiday_event(user_id, event_type))
            elif "friend" in event_type:
                events.append(self.generate_friends_event(user_id, event_type))
            elif "interaction" in event_type:
                events.append(self.generate_interaction_event(user_id, event_type))
            elif "dialogue" in event_type:
                events.append(self.generate_dialogue_event(user_id, event_type))
            elif "neglect" in event_type:
                events.append(self.generate_neglect_event(user_id, event_type))
        
        return events


class DiaryPerformanceTestDataGenerator:
    """Generates large datasets for performance testing."""
    
    def __init__(self):
        self.base_generator = DiaryTestDataGenerator()
    
    def generate_concurrent_events(self, event_count: int = 100, user_count: int = 10) -> List[EventData]:
        """Generate events for concurrent processing tests."""
        events = []
        event_types = [
            "favorite_weather", "dislike_weather", "celebration", "disaster",
            "approaching_holiday", "made_new_friend", "liked_interaction_once",
            "positive_emotional_dialogue", "neglect_1_day_no_dialogue"
        ]
        
        for i in range(event_count):
            user_id = (i % user_count) + 1
            event_type = event_types[i % len(event_types)]
            
            # Add timestamp variation for realistic concurrent scenarios
            timestamp_offset = random.randint(0, 3600)  # Within 1 hour
            
            if "weather" in event_type:
                event = self.base_generator.generate_weather_event(user_id, event_type)
            elif event_type in ["celebration", "disaster"]:
                event = self.base_generator.generate_trending_event(user_id, event_type)
            elif "holiday" in event_type:
                event = self.base_generator.generate_holiday_event(user_id, event_type)
            elif "friend" in event_type:
                event = self.base_generator.generate_friends_event(user_id, event_type)
            elif "interaction" in event_type:
                event = self.base_generator.generate_interaction_event(user_id, event_type)
            elif "dialogue" in event_type:
                event = self.base_generator.generate_dialogue_event(user_id, event_type)
            elif "neglect" in event_type:
                event = self.base_generator.generate_neglect_event(user_id, event_type)
            
            event.timestamp = datetime.now() + timedelta(seconds=timestamp_offset)
            events.append(event)
        
        return events
    
    def generate_stress_test_scenario(self) -> Dict[str, Any]:
        """Generate data for stress testing scenarios."""
        return {
            "events": self.generate_concurrent_events(1000, 50),
            "users": [self.base_generator.generate_user_profile(i) for i in range(1, 51)],
            "expected_diary_count": random.randint(800, 1000),
            "max_processing_time": 300,  # 5 minutes
            "concurrent_agents": 10
        }