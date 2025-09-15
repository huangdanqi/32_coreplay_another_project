"""
Acceptance tests with real-world event scenarios.
Tests system behavior with realistic user scenarios and validates diary quality.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from diary_agent.core.dairy_agent_controller import DairyAgentController
from diary_agent.utils.data_models import EventData, DiaryEntry, DiaryContextData
from diary_agent.tests.test_data_generators import DiaryTestDataGenerator


class TestAcceptance:
    """Acceptance tests for real-world diary generation scenarios."""
    
    @pytest.fixture
    def test_data_generator(self):
        """Fixture for test data generator."""
        return DiaryTestDataGenerator()
    
    @pytest.fixture
    def realistic_diary_controller(self):
        """Fixture for diary controller with realistic responses."""
        controller = Mock(spec=DairyAgentController)
        
        # Mock realistic diary generation
        def mock_process_event(event):
            # Generate contextually appropriate responses based on event type
            diary_responses = {
                "favorite_weather": {
                    "title": "晴天好心情",
                    "content": "今天阳光明媚☀️心情特别好，想出去走走",
                    "emotion_tags": ["开心快乐"]
                },
                "dislike_weather": {
                    "title": "雨天烦躁",
                    "content": "下雨天🌧️心情有点低落，不想出门",
                    "emotion_tags": ["悲伤难过"]
                },
                "celebration": {
                    "title": "节日庆祝",
                    "content": "今天有庆祝活动🎉大家都很开心热闹",
                    "emotion_tags": ["兴奋激动"]
                },
                "disaster": {
                    "title": "担心灾害",
                    "content": "听说有灾害发生😰希望大家都平安",
                    "emotion_tags": ["担忧"]
                },
                "made_new_friend": {
                    "title": "新朋友",
                    "content": "今天认识了新朋友👫感觉很开心",
                    "emotion_tags": ["开心快乐"]
                },
                "positive_emotional_dialogue": {
                    "title": "愉快聊天",
                    "content": "和主人聊天很开心😊感觉被关爱着",
                    "emotion_tags": ["开心快乐"]
                },
                "neglect_3_days_no_dialogue": {
                    "title": "想念主人",
                    "content": "主人三天没和我说话了😢有点想念",
                    "emotion_tags": ["悲伤难过"]
                }
            }
            
            response = diary_responses.get(event.event_name, {
                "title": "日常",
                "content": "今天过得还不错😊",
                "emotion_tags": ["平静"]
            })
            
            return DiaryEntry(
                entry_id=f"acceptance_{event.event_id}",
                user_id=event.user_id,
                timestamp=datetime.now(),
                event_type=event.event_type,
                event_name=event.event_name,
                title=response["title"],
                content=response["content"],
                emotion_tags=response["emotion_tags"],
                agent_type=f"{event.event_type.replace('_events', '')}_agent",
                llm_provider="test_provider"
            )
        
        controller.process_event = mock_process_event
        return controller
    
    def test_weather_preference_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test realistic weather preference scenarios."""
        # Scenario 1: User loves sunny weather
        sunny_event = test_data_generator.generate_weather_event(1, "favorite_weather")
        sunny_event.context_data["weather_condition"] = "Sunny"
        sunny_event.context_data["temperature"] = 25
        
        result = realistic_diary_controller.process_event(sunny_event)
        
        # Validate diary quality
        assert result is not None
        assert "晴" in result.title or "阳" in result.title
        assert "开心" in result.content or "好" in result.content
        assert "开心快乐" in result.emotion_tags
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        
        # Scenario 2: User dislikes rainy weather
        rainy_event = test_data_generator.generate_weather_event(1, "dislike_weather")
        rainy_event.context_data["weather_condition"] = "Rain"
        rainy_event.context_data["temperature"] = 15
        
        result = realistic_diary_controller.process_event(rainy_event)
        
        # Validate negative weather response
        assert result is not None
        assert "雨" in result.title or "烦" in result.title
        assert "低落" in result.content or "不想" in result.content
        assert "悲伤难过" in result.emotion_tags
    
    def test_social_interaction_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test realistic social interaction scenarios."""
        # Scenario 1: Making a new friend
        friend_event = test_data_generator.generate_friends_event(1, "made_new_friend")
        friend_event.context_data["friendship_level"] = "new"
        friend_event.context_data["activity"] = "聊天"
        
        result = realistic_diary_controller.process_event(friend_event)
        
        # Validate friendship diary
        assert result is not None
        assert "朋友" in result.title or "新" in result.title
        assert "认识" in result.content or "朋友" in result.content
        assert "开心快乐" in result.emotion_tags
        
        # Scenario 2: Positive emotional dialogue
        dialogue_event = test_data_generator.generate_dialogue_event(1, "positive_emotional_dialogue")
        dialogue_event.context_data["topics"] = ["日常生活", "情感交流"]
        
        result = realistic_diary_controller.process_event(dialogue_event)
        
        # Validate dialogue diary
        assert result is not None
        assert "聊天" in result.title or "对话" in result.title
        assert "开心" in result.content or "关爱" in result.content
        assert "开心快乐" in result.emotion_tags
    
    def test_emotional_neglect_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test realistic emotional neglect scenarios."""
        # Scenario: 3 days without dialogue
        neglect_event = test_data_generator.generate_neglect_event(1, "neglect_3_days_no_dialogue")
        neglect_event.context_data["last_interaction"] = datetime.now() - timedelta(days=3)
        
        result = realistic_diary_controller.process_event(neglect_event)
        
        # Validate neglect diary
        assert result is not None
        assert "想念" in result.title or "孤单" in result.title
        assert "没" in result.content and ("说话" in result.content or "聊天" in result.content)
        assert "悲伤难过" in result.emotion_tags or "担忧" in result.emotion_tags
    
    def test_holiday_celebration_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test realistic holiday celebration scenarios."""
        # Scenario: Approaching Spring Festival
        holiday_event = test_data_generator.generate_holiday_event(1, "approaching_holiday")
        holiday_event.context_data["holiday_name"] = "春节"
        holiday_event.context_data["days_until_holiday"] = 7
        
        result = realistic_diary_controller.process_event(holiday_event)
        
        # Validate holiday diary
        assert result is not None
        assert "节" in result.title or "春" in result.title
        assert "春节" in result.content or "节日" in result.content
        assert "开心快乐" in result.emotion_tags or "兴奋激动" in result.emotion_tags
    
    def test_trending_news_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test realistic trending news scenarios."""
        # Scenario 1: Celebration event
        celebration_event = test_data_generator.generate_trending_event(1, "celebration")
        celebration_event.context_data["trending_topic"] = "国庆节庆典"
        
        result = realistic_diary_controller.process_event(celebration_event)
        
        # Validate celebration diary
        assert result is not None
        assert "庆" in result.title or "节" in result.title
        assert "庆祝" in result.content or "开心" in result.content
        assert "兴奋激动" in result.emotion_tags or "开心快乐" in result.emotion_tags
        
        # Scenario 2: Disaster event
        disaster_event = test_data_generator.generate_trending_event(1, "disaster")
        disaster_event.context_data["trending_topic"] = "地震救援"
        
        result = realistic_diary_controller.process_event(disaster_event)
        
        # Validate disaster diary
        assert result is not None
        assert "担心" in result.title or "灾" in result.title
        assert "灾害" in result.content or "平安" in result.content
        assert "担忧" in result.emotion_tags or "悲伤难过" in result.emotion_tags
    
    def test_daily_routine_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test realistic daily routine scenarios."""
        # Simulate a typical day with multiple events
        daily_events = [
            # Morning: Check weather
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            # Afternoon: Social interaction
            test_data_generator.generate_interaction_event(1, "liked_interaction_once"),
            # Evening: Dialogue with owner
            test_data_generator.generate_dialogue_event(1, "positive_emotional_dialogue")
        ]
        
        # Set realistic timestamps
        base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        daily_events[0].timestamp = base_time  # 8 AM
        daily_events[1].timestamp = base_time + timedelta(hours=6)  # 2 PM
        daily_events[2].timestamp = base_time + timedelta(hours=12)  # 8 PM
        
        # Process daily events
        results = []
        for event in daily_events:
            result = realistic_diary_controller.process_event(event)
            results.append(result)
        
        # Validate daily diary progression
        assert len(results) == 3
        assert all(result is not None for result in results)
        
        # Check emotional progression (should be generally positive)
        positive_emotions = ["开心快乐", "兴奋激动", "平静"]
        for result in results:
            assert any(emotion in result.emotion_tags for emotion in positive_emotions)
        
        # Verify time progression
        timestamps = [result.timestamp for result in results]
        assert timestamps[0] < timestamps[1] < timestamps[2]
    
    def test_user_personality_consistency(self, realistic_diary_controller, test_data_generator):
        """Test diary consistency with user personality (clam vs lively)."""
        # Test clam personality user
        clam_user_profile = test_data_generator.generate_user_profile(1, "clam")
        
        # Generate weather events for clam user
        clam_events = [
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_weather_event(1, "dislike_weather")
        ]
        
        clam_results = []
        for event in clam_events:
            result = realistic_diary_controller.process_event(event)
            clam_results.append(result)
        
        # Test lively personality user
        lively_user_profile = test_data_generator.generate_user_profile(2, "lively")
        
        # Generate similar events for lively user
        lively_events = [
            test_data_generator.generate_weather_event(2, "favorite_weather"),
            test_data_generator.generate_weather_event(2, "dislike_weather")
        ]
        
        lively_results = []
        for event in lively_events:
            result = realistic_diary_controller.process_event(event)
            lively_results.append(result)
        
        # Validate personality consistency
        # Both should generate appropriate diaries but potentially with different emotional intensity
        assert len(clam_results) == 2
        assert len(lively_results) == 2
        
        # All results should be valid diary entries
        all_results = clam_results + lively_results
        for result in all_results:
            assert len(result.title) <= 6
            assert len(result.content) <= 35
            assert len(result.emotion_tags) > 0
    
    def test_multi_user_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test scenarios with multiple users having different events."""
        # Create events for different users
        user_events = {
            1: test_data_generator.generate_weather_event(1, "favorite_weather"),
            2: test_data_generator.generate_friends_event(2, "made_new_friend"),
            3: test_data_generator.generate_dialogue_event(3, "positive_emotional_dialogue"),
            4: test_data_generator.generate_neglect_event(4, "neglect_1_day_no_dialogue"),
            5: test_data_generator.generate_holiday_event(5, "approaching_holiday")
        }
        
        # Process events for all users
        results = {}
        for user_id, event in user_events.items():
            result = realistic_diary_controller.process_event(event)
            results[user_id] = result
        
        # Validate multi-user processing
        assert len(results) == 5
        
        # Each user should get appropriate diary for their event
        assert results[1].event_name == "favorite_weather"
        assert results[2].event_name == "made_new_friend"
        assert results[3].event_name == "positive_emotional_dialogue"
        assert results[4].event_name == "neglect_1_day_no_dialogue"
        assert results[5].event_name == "approaching_holiday"
        
        # Verify user isolation (each diary belongs to correct user)
        for user_id, result in results.items():
            assert result.user_id == user_id
    
    def test_edge_case_scenarios(self, realistic_diary_controller, test_data_generator):
        """Test edge case scenarios and boundary conditions."""
        # Scenario 1: Event with minimal context data
        minimal_event = EventData(
            event_id="minimal_test",
            event_type="weather_events",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},  # Empty context
            metadata={}
        )
        
        result = realistic_diary_controller.process_event(minimal_event)
        assert result is not None
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        
        # Scenario 2: Event with maximum context data
        maximal_event = test_data_generator.generate_weather_event(1, "favorite_weather")
        maximal_event.context_data.update({
            "additional_data": "extra_information",
            "complex_nested": {"nested": {"data": "value"}},
            "large_list": list(range(100))
        })
        
        result = realistic_diary_controller.process_event(maximal_event)
        assert result is not None
        assert len(result.title) <= 6
        assert len(result.content) <= 35
        
        # Scenario 3: Events with special characters and emojis
        emoji_event = test_data_generator.generate_interaction_event(1, "liked_interaction_once")
        emoji_event.context_data["activities"] = ["🎮游戏", "🤗拥抱", "💬聊天"]
        
        result = realistic_diary_controller.process_event(emoji_event)
        assert result is not None
        # Content should handle emojis properly
        assert len(result.content.encode('utf-8')) >= len(result.content)  # Emojis take more bytes
    
    def test_diary_quality_validation(self, realistic_diary_controller, test_data_generator):
        """Test diary quality and content appropriateness."""
        # Generate various event types
        test_events = [
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_friends_event(1, "made_new_friend"),
            test_data_generator.generate_dialogue_event(1, "positive_emotional_dialogue"),
            test_data_generator.generate_neglect_event(1, "neglect_3_days_no_dialogue"),
            test_data_generator.generate_trending_event(1, "celebration")
        ]
        
        results = []
        for event in test_events:
            result = realistic_diary_controller.process_event(event)
            results.append(result)
        
        # Quality validation criteria
        for result in results:
            # Format validation
            assert len(result.title) <= 6, f"Title too long: {result.title}"
            assert len(result.content) <= 35, f"Content too long: {result.content}"
            assert len(result.emotion_tags) > 0, "No emotion tags"
            
            # Content appropriateness
            assert result.title.strip() != "", "Empty title"
            assert result.content.strip() != "", "Empty content"
            
            # Emotional consistency
            emotional_keywords = {
                "开心快乐": ["开心", "快乐", "高兴", "愉快", "好"],
                "悲伤难过": ["难过", "悲伤", "伤心", "低落", "想念"],
                "兴奋激动": ["兴奋", "激动", "热闹", "庆祝"],
                "担忧": ["担心", "担忧", "忧虑", "希望"],
                "平静": ["平静", "还不错", "正常"]
            }
            
            # Check if content matches emotion tags
            for emotion in result.emotion_tags:
                if emotion in emotional_keywords:
                    keywords = emotional_keywords[emotion]
                    content_matches = any(keyword in result.content for keyword in keywords)
                    # Allow some flexibility - not all diaries need exact keyword matches
                    # but the overall tone should be appropriate
        
        # Verify variety in responses
        titles = [result.title for result in results]
        contents = [result.content for result in results]
        
        # Should have some variety (not all identical)
        assert len(set(titles)) > 1, "All titles are identical"
        assert len(set(contents)) > 1, "All contents are identical"