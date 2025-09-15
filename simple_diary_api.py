#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Diary API
This API reads events from diary_agent/events.json and processes them based on actual event data.
Returns results only when conditions are met.
"""

import sys
import os
import json
import asyncio
import logging
import random
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Authentication configuration
AUTH_CONFIG_FILE = "auth_config.json"
DEFAULT_PASSWORD = "GOODluck!328"  # Default password for first-time setup

def load_auth_config():
    """Load authentication configuration from file."""
    if os.path.exists(AUTH_CONFIG_FILE):
        try:
            with open(AUTH_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading auth config: {e}")
    
    # Create default config if file doesn't exist
    default_config = {
        "username": "admin",
        "password_hash": hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest(),
        "created_at": datetime.now().isoformat()
    }
    save_auth_config(default_config)
    return default_config

def save_auth_config(config):
    """Save authentication configuration to file."""
    try:
        with open(AUTH_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving auth config: {e}")
        return False

def verify_password(password, password_hash):
    """Verify password against hash."""
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

def hash_password(password):
    """Hash password for storage."""
    return hashlib.sha256(password.encode()).hexdigest()

# Load auth config
auth_config = load_auth_config()

# Import the actual agents and configurations
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import PromptConfig, EventData, DiaryEntry, DataReader, DiaryContextData
from diary_agent.agents.interactive_agent import InteractiveAgent
from diary_agent.agents.dialogue_agent import DialogueAgent
from diary_agent.agents.neglect_agent import NeglectAgent
from diary_agent.agents.weather_agent import WeatherAgent, SeasonalAgent
from diary_agent.agents.trending_agent import TrendingAgent
from diary_agent.agents.holiday_agent import HolidayAgent
from diary_agent.agents.friends_agent import FriendsAgent
from diary_agent.agents.same_frequency_agent import SameFrequencyAgent
from diary_agent.agents.adoption_agent import AdoptionAgent
from event_agents.extraction.agent import EventExtractionAgent
from event_agents.update.agent import EventUpdateAgent
from bazi_wuxing_agent import BaziWuxingAgent
from sensor_event_agent.core.sensor_event_agent import SensorEventAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_diary_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

class SimpleDataReader(DataReader):
    """Simple data reader for event processing."""
    
    def __init__(self, module_name: str = "simple_module"):
        super().__init__(module_name=module_name, read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """Read event context."""
        return DiaryContextData(
            user_profile={"name": "主人"},
            event_details=event_data.context_data,
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": event_data.timestamp.isoformat()}
        )

class SimpleDiaryManager:
    """Simple diary manager that processes events from events.json."""
    
    def __init__(self):
        self.llm_config_manager = LLMConfigManager()
        self.data_reader = SimpleDataReader()
        self.events_config = self._load_events_config()
        
        # Initialize prompt configuration
        self.prompt_config = PromptConfig(
            agent_type="diary_agent",
            system_prompt="你是一个可爱的玩具日记助手。请根据事件信息写一篇生动有趣的日记，用第一人称（我）的语气，表达玩具的真实感受和想法。日记要温馨可爱，充满童趣。请严格按照JSON格式输出。",
            user_prompt_template="事件类型: {event_type}\n事件名称: {event_name}\n事件详情: {event_details}\n\n请严格按照以下JSON格式输出日记：\n{{\n  \"title\": \"简洁有趣的标题（不超过15字）\",\n  \"content\": \"详细的日记内容（不少于50字）\",\n  \"emotion_tags\": [\"情感标签\"]\n}}",
            output_format={
                "title": "string",
                "content": "string",
                "emotion": "string"
            },
            validation_rules={
                "title_max_length": 15,
                "content_max_length": 200,
                "required_fields": ["title", "content", "emotion"]
            }
        )
        
        # Initialize agents
        self.interactive_agent = InteractiveAgent(
            agent_type="interactive_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.dialogue_agent = DialogueAgent(
            agent_type="dialogue_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.neglect_agent = NeglectAgent(
            agent_type="neglect_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        # Additional sub-agents
        self.weather_agent = WeatherAgent(
            agent_type="weather_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.season_agent = SeasonalAgent(
            agent_type="season_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.trending_agent = TrendingAgent(
            agent_type="trending_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.holiday_agent = HolidayAgent(
            agent_type="holiday_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.friends_agent = FriendsAgent(
            agent_type="friends_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.frequency_agent = SameFrequencyAgent(
            agent_type="frequency_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        self.adopted_agent = AdoptionAgent(
            agent_type="adoption_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.data_reader
        )
        
        # Event type mappings based on events.json
        self.event_type_mappings = {
            "weather_events": "weather_agent",
            "seasonal_events": "season_agent",
            "trending_events": "trending_agent",
            "holiday_events": "holiday_agent",
            "friends_function": "friends_agent",
            "same_frequency": "frequency_agent",
            "adopted_function": "adopted_agent",
            "human_toy_interactive_function": "interactive_agent",
            "human_toy_talk": "dialogue_agent",
            "unkeep_interactive": "neglect_agent"
        }
    
    def _load_events_config(self) -> Dict:
        """Load events configuration from events.json."""
        try:
            events_file = os.path.join(os.path.dirname(__file__), "diary_agent", "events.json")
            with open(events_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading events config: {e}")
            return {}
    
    def get_available_events(self) -> Dict[str, List[str]]:
        """Get all available events from events.json."""
        return self.events_config
    
    def validate_event(self, event_category: str, event_name: str) -> bool:
        """Validate if event exists in events.json."""
        if event_category not in self.events_config:
            return False
        
        return event_name in self.events_config[event_category]
    
    def should_generate_diary(self, event_category: str, event_name: str) -> bool:
        """Determine if diary should be generated for this event."""
        # Always generate diary for testing purposes
        return True
    
    def generate_event_details(self, event_category: str, event_name: str) -> Dict[str, Any]:
        """Auto-generate event details based on event category and name."""
        base_details = {
            "event_category": event_category,
            "event_name": event_name,
            "timestamp": datetime.now().isoformat(),
            "auto_generated": True
        }
        
        # Add specific details based on event category
        if event_category == "human_toy_interactive_function":
            if "liked_interaction_once" in event_name:
                base_details.update({
                    "interaction_type": "抚摸",
                    "duration": "5分钟",
                    "user_response": "positive",
                    "toy_emotion": "开心",
                    "location": "客厅"
                })
            elif "liked_interaction_3_to_5_times" in event_name:
                base_details.update({
                    "interaction_type": "摸摸头",
                    "count": 4,
                    "duration": "20分钟",
                    "user_response": "positive",
                    "toy_emotion": "平静"
                })
            elif "liked_interaction_over_5_times" in event_name:
                base_details.update({
                    "interaction_type": "喂食",
                    "count": 7,
                    "duration": "30分钟",
                    "user_response": "positive",
                    "toy_emotion": "开心快乐"
                })
            elif "disliked_interaction" in event_name:
                base_details.update({
                    "interaction_type": "拍打",
                    "duration": "2分钟",
                    "user_response": "negative",
                    "toy_emotion": "害怕"
                })
            elif "neutral_interaction" in event_name:
                base_details.update({
                    "interaction_type": "触摸",
                    "duration": "10分钟",
                    "user_response": "neutral",
                    "toy_emotion": "平静"
                })
        
        elif event_category == "human_toy_talk":
            if "positive_emotional_dialogue" in event_name:
                base_details.update({
                    "dialogue_type": "开心对话",
                    "content": "主人今天心情很好",
                    "duration": "10分钟",
                    "toy_emotion": "开心快乐"
                })
            elif "negative_emotional_dialogue" in event_name:
                base_details.update({
                    "dialogue_type": "安慰对话",
                    "content": "主人需要安慰",
                    "duration": "15分钟",
                    "toy_emotion": "平静"
                })
        
        elif event_category == "unkeep_interactive":
            if "neglect_1_day_no_dialogue" in event_name:
                base_details.update({
                    "neglect_duration": 1,
                    "neglect_type": "no_dialogue",
                    "disconnection_type": "无对话有互动",
                    "disconnection_days": 1,
                    "memory_status": "on"
                })
            elif "neglect_1_day_no_interaction" in event_name:
                base_details.update({
                    "neglect_duration": 1,
                    "neglect_type": "no_interaction",
                    "disconnection_type": "完全无互动",
                    "disconnection_days": 1,
                    "memory_status": "on"
                })
            elif "neglect_3_days" in event_name:
                base_details.update({
                    "neglect_duration": 3,
                    "neglect_type": "no_interaction",
                    "disconnection_type": "完全无互动",
                    "disconnection_days": 3,
                    "memory_status": "on"
                })
            elif "neglect_7_days" in event_name:
                base_details.update({
                    "neglect_duration": 7,
                    "neglect_type": "no_dialogue",
                    "disconnection_type": "无对话有互动",
                    "disconnection_days": 7,
                    "memory_status": "on"
                })
            elif "neglect_15_days" in event_name:
                base_details.update({
                    "neglect_duration": 15,
                    "neglect_type": "no_interaction",
                    "disconnection_type": "完全无互动",
                    "disconnection_days": 15,
                    "memory_status": "on"
                })
            elif "neglect_30_days" in event_name:
                base_details.update({
                    "neglect_duration": 30,
                    "neglect_type": "no_interaction",
                    "disconnection_type": "完全无互动",
                    "disconnection_days": 30,
                    "memory_status": "on"
                })
        
        elif event_category == "weather_events":
            if "favorite_weather" in event_name:
                base_details.update({
                    "city": "北京",
                    "weather_type": "晴天",
                    "temperature": "22°C",
                    "user_preference": "喜欢",
                    "toy_emotion": "开心"
                })
            elif "dislike_weather" in event_name:
                base_details.update({
                    "city": "北京",
                    "weather_type": "雨天",
                    "temperature": "18°C",
                    "user_preference": "不喜欢",
                    "toy_emotion": "平静"
                })
        
        elif event_category == "seasonal_events":
            if "favorite_season" in event_name:
                base_details.update({
                    "city": "北京",
                    "season": "春季",
                    "temperature": "20°C",
                    "user_preference": "喜欢",
                    "toy_emotion": "开心"
                })
            elif "dislike_season" in event_name:
                base_details.update({
                    "city": "北京",
                    "season": "冬季",
                    "temperature": "-5°C",
                    "user_preference": "不喜欢",
                    "toy_emotion": "平静"
                })
        
        elif event_category == "trending_events":
            if "celebration" in event_name:
                base_details.update({
                    "event_type": "庆祝事件",
                    "impact_level": "positive",
                    "toy_emotion": "开心",
                    "description": "重大庆祝活动"
                })
            elif "disaster" in event_name:
                base_details.update({
                    "event_type": "灾难事件",
                    "impact_level": "negative",
                    "toy_emotion": "担心",
                    "description": "重大灾难事件"
                })
        
        elif event_category == "holiday_events":
            if "approaching_holiday" in event_name:
                base_details.update({
                    "holiday_name": "春节",
                    "time_description": "春节前3天",
                    "festivity_level": "high",
                    "toy_emotion": "期待"
                })
            elif "during_holiday" in event_name:
                base_details.update({
                    "holiday_name": "春节",
                    "time_description": "春节第2天",
                    "festivity_level": "high",
                    "toy_emotion": "开心"
                })
            elif "holiday_ends" in event_name:
                base_details.update({
                    "holiday_name": "春节",
                    "time_description": "春节后1天",
                    "festivity_level": "medium",
                    "toy_emotion": "平静"
                })
        
        elif event_category == "friends_function":
            if "made_new_friend" in event_name:
                base_details.update({
                    "friend_action": "新朋友",
                    "relationship_type": "new",
                    "toy_emotion": "开心",
                    "interaction_level": "high"
                })
            elif "friend_deleted" in event_name:
                base_details.update({
                    "friend_action": "删除朋友",
                    "relationship_type": "deleted",
                    "toy_emotion": "难过",
                    "interaction_level": "none"
                })
            elif "liked_single" in event_name:
                base_details.update({
                    "friend_action": "单次点赞",
                    "interaction_count": 1,
                    "toy_emotion": "开心",
                    "interaction_type": "like"
                })
            elif "liked_3_to_5" in event_name:
                base_details.update({
                    "friend_action": "多次点赞",
                    "interaction_count": 4,
                    "toy_emotion": "开心",
                    "interaction_type": "like"
                })
            elif "liked_5_plus" in event_name:
                base_details.update({
                    "friend_action": "大量点赞",
                    "interaction_count": 7,
                    "toy_emotion": "开心快乐",
                    "interaction_type": "like"
                })
            elif "disliked" in event_name:
                base_details.update({
                    "friend_action": "不喜欢",
                    "interaction_type": "dislike",
                    "toy_emotion": "难过",
                    "interaction_count": 1
                })
        
        elif event_category == "same_frequency":
            if "close_friend_frequency" in event_name:
                base_details.update({
                    "frequency_type": "同频",
                    "friend_name": "好友",
                    "interaction_level": "high",
                    "toy_emotion": "开心"
                })
        
        elif event_category == "adopted_function":
            if "toy_claimed" in event_name:
                base_details.update({
                    "claim_type": "绑定",
                    "owner_info": "新主人",
                    "toy_emotion": "开心",
                    "relationship_status": "claimed"
                })
        
        return base_details
    
    def clean_llm_output(self, content: str) -> str:
        """Clean LLM output - minimal cleaning to preserve diary content."""
        if not content:
            return ""
        
        # Only remove obvious meta-commentary patterns, not diary content
        meta_patterns = [
            "<think>", "</think>", "思考过程", "分析", "理解", "总结"
        ]
        
        cleaned_content = content
        for pattern in meta_patterns:
            cleaned_content = cleaned_content.replace(pattern, "")
        
        # Remove extra whitespace but preserve line breaks for diary formatting
        cleaned_content = cleaned_content.strip()
        
        return cleaned_content
    
    async def generate_diary_for_event(self, event_category: str, event_name: str, event_details: Dict) -> Optional[DiaryEntry]:
        """Generate diary entry for a specific event."""
        try:
            # Create event data
            event_data = EventData(
                event_id=f"simple_event_{uuid.uuid4()}",
                event_type=event_category,
                event_name=event_name,
                user_id=1,
                timestamp=datetime.now(),
                context_data=event_details,
                metadata={"api_generated": True, "source": "events.json"}
            )
            
            # Select appropriate agent based on event category
            agent_type = self.event_type_mappings.get(event_category, "interactive_agent")
            
            if agent_type == "interactive_agent":
                agent = self.interactive_agent
            elif agent_type == "dialogue_agent":
                agent = self.dialogue_agent
            elif agent_type == "neglect_agent":
                agent = self.neglect_agent
            elif agent_type == "weather_agent":
                agent = self.weather_agent
            elif agent_type == "season_agent":
                agent = self.season_agent
            elif agent_type == "trending_agent":
                agent = self.trending_agent
            elif agent_type == "holiday_agent":
                agent = self.holiday_agent
            elif agent_type == "friends_agent":
                agent = self.friends_agent
            elif agent_type == "frequency_agent":
                agent = self.frequency_agent
            elif agent_type == "adopted_agent":
                agent = self.adopted_agent
            else:
                # Use interactive agent as default
                agent = self.interactive_agent
            
            # Generate diary entry
            diary_entry = await agent.process_event(event_data)
            
            if diary_entry:
                # Clean the content
                diary_entry.content = self.clean_llm_output(diary_entry.content)
                diary_entry.title = self.clean_llm_output(diary_entry.title)
                
            return diary_entry
            
        except Exception as e:
            logger.error(f"Error generating diary for event {event_name}: {e}")
            return None

    async def generate_diary_with_custom_prompt(self, event_category: str, event_name: str, event_details: Dict, custom_prompt: Dict, sub_agent: str = "interactive", additional_data: Dict = None) -> Dict:
        """Generate diary entry with custom prompt configuration."""
        try:
            # Create event data
            event_data = EventData(
                event_id=f"custom_event_{uuid.uuid4()}",
                event_type=event_category,
                event_name=event_name,
                user_id=1,
                timestamp=datetime.now(),
                context_data=event_details,
                metadata={"api_generated": True, "source": "custom_prompt", "custom_prompt": True}
            )
            
            # Create custom prompt configuration
            custom_prompt_config = PromptConfig(
                agent_type="diary_agent",
                system_prompt=custom_prompt.get('system_prompt', ''),
                user_prompt_template=custom_prompt.get('user_prompt_template', ''),
                output_format=custom_prompt.get('output_format', {}),
                validation_rules=custom_prompt.get('validation_rules', {})
            )
            
            # Debug: Log the custom prompt being used
            logger.info(f"Using custom prompt - System: {custom_prompt_config.system_prompt[:100]}...")
            logger.info(f"Using custom prompt - User template: {custom_prompt_config.user_prompt_template[:100]}...")
            
            # Create agent with custom prompt
            if sub_agent == "interactive":
                agent = InteractiveAgent(
                    agent_type="interactive_agent",
                    prompt_config=custom_prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
            elif sub_agent == "dialogue":
                agent = DialogueAgent(
                    agent_type="dialogue_agent",
                    prompt_config=custom_prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
            elif sub_agent == "neglect":
                agent = NeglectAgent(
                    agent_type="neglect_agent",
                    prompt_config=custom_prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
            else:
                # Use interactive agent as default
                agent = InteractiveAgent(
                    agent_type="interactive_agent",
                    prompt_config=custom_prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
            
            # Generate diary entry with custom prompt
            diary_entry = await agent.process_event(event_data)
            
            if diary_entry:
                # Clean the content
                diary_entry.content = self.clean_llm_output(diary_entry.content)
                diary_entry.title = self.clean_llm_output(diary_entry.title)
                
                return {
                    "success": True,
                    "data": {
                        "diary_entry": {
                            "agent_type": sub_agent,
                            "title": diary_entry.title,
                            "content": diary_entry.content,
                            "emotion_tags": [tag.value if hasattr(tag, 'value') else str(tag) for tag in diary_entry.emotion_tags],
                            "entry_id": diary_entry.entry_id,
                            "timestamp": diary_entry.timestamp.isoformat(),
                            "llm_provider": getattr(diary_entry, 'llm_provider', 'unknown')
                        },
                        "diary_generated": True,
                        "event_category": event_category,
                        "event_name": event_name
                    },
                    "provider": getattr(diary_entry, 'llm_provider', 'unknown'),
                    "response_time": getattr(diary_entry, 'metadata', {}).get('response_time', 0)
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to generate diary entry",
                    "error": "Agent returned None",
                    "data": {}
                }
                
        except Exception as e:
            logger.error(f"Error generating diary with custom prompt for event {event_name}: {e}")
            return {
                "success": False,
                "message": f"Error generating diary: {str(e)}",
                "error": str(e),
                "data": {}
            }

# Initialize the simple diary manager
diary_manager = SimpleDiaryManager()
extraction_agent = EventExtractionAgent()
update_agent = EventUpdateAgent()
bazi_agent = BaziWuxingAgent()
sensor_agent = SensorEventAgent()

# API Routes

# ===== Authentication Endpoints =====

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Login endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required",
                "error": "Missing credentials"
            }), 400
        
        # Verify credentials
        if username == auth_config['username'] and verify_password(password, auth_config['password_hash']):
            token = secrets.token_urlsafe(32)
            return jsonify({
                "success": True,
                "message": "Login successful",
                "token": token,
                "role": "admin",
                "username": username
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid username or password",
                "error": "Authentication failed"
            }), 401
            
    except Exception as e:
        logger.error(f"Error in auth_login: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """Logout endpoint."""
    return jsonify({
        "success": True,
        "message": "Logout successful"
    })

@app.route('/api/auth/verify', methods=['POST'])
def auth_verify():
    """Verify password endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        password = data.get('password')
        if not password:
            return jsonify({
                "success": False,
                "message": "Password is required",
                "error": "Missing password"
            }), 400
        
        if verify_password(password, auth_config['password_hash']):
            return jsonify({
                "success": True,
                "message": "Password verified"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid password",
                "error": "Authentication failed"
            }), 401
            
    except Exception as e:
        logger.error(f"Error in auth_verify: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/auth/change-password', methods=['POST'])
def auth_change_password():
    """Change password endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({
                "success": False,
                "message": "Old password and new password are required",
                "error": "Missing passwords"
            }), 400
        
        # Verify old password
        if not verify_password(old_password, auth_config['password_hash']):
            return jsonify({
                "success": False,
                "message": "Invalid old password",
                "error": "Authentication failed"
            }), 401
        
        # Update password
        auth_config['password_hash'] = hash_password(new_password)
        auth_config['updated_at'] = datetime.now().isoformat()
        
        if save_auth_config(auth_config):
            return jsonify({
                "success": True,
                "message": "Password changed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to save new password",
                "error": "File write error"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in auth_change_password: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

# ===== Prompt Management Endpoints =====

@app.route('/api/prompts/save', methods=['POST'])
def prompts_save():
    """Save prompt configuration to backend files."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        agent_type = data.get('agent_type')
        if not agent_type:
            return jsonify({
                "success": False,
                "message": "Agent type is required",
                "error": "Missing agent_type"
            }), 400
        
        # Determine the config file path based on agent type
        config_paths = {
            'diary': 'diary_agent/config/prompt_configuration.json',
            'sensor': 'sensor_event_agent/config/prompt.json',
            'bazi': 'bazi_wuxing_agent/prompt.json'
        }
        
        config_path = config_paths.get(agent_type)
        if not config_path:
            return jsonify({
                "success": False,
                "message": f"Unknown agent type: {agent_type}",
                "error": "Invalid agent type"
            }), 400
        
        # Prepare prompt configuration
        prompt_config = {
            "system_prompt": data.get('system_prompt', ''),
            "user_prompt_template": data.get('user_prompt_template', ''),
            "output_format": data.get('output_format', {}),
            "validation_rules": data.get('validation_rules', {}),
            "updated_at": datetime.now().isoformat(),
            "updated_by": "admin"
        }
        
        # Save to file
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(prompt_config, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                "success": True,
                "message": f"Prompt configuration saved for {agent_type}",
                "config_path": config_path
            })
        except Exception as e:
            logger.error(f"Error saving prompt config to {config_path}: {e}")
            return jsonify({
                "success": False,
                "message": f"Failed to save prompt configuration",
                "error": str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Error in prompts_save: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/prompts/templates', methods=['GET'])
def prompts_templates():
    """Get available prompt templates."""
    try:
        templates = []
        
        # Load templates from various config files
        config_files = [
            ('diary', 'diary_agent/config/prompt_configuration.json'),
            ('sensor', 'sensor_event_agent/config/prompt.json'),
            ('bazi', 'bazi_wuxing_agent/prompt.json')
        ]
        
        for agent_type, config_path in config_files:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        templates.append({
                            "agent_type": agent_type,
                            "system_prompt": config.get('system_prompt', ''),
                            "user_prompt_template": config.get('user_prompt_template', ''),
                            "output_format": config.get('output_format', {}),
                            "validation_rules": config.get('validation_rules', {}),
                            "version": "1.0",
                            "last_updated": config.get('updated_at', 'Unknown')
                        })
                except Exception as e:
                    logger.error(f"Error loading template from {config_path}: {e}")
        
        return jsonify({
            "success": True,
            "data": templates,
            "message": f"Loaded {len(templates)} templates"
        })
        
    except Exception as e:
        logger.error(f"Error in prompts_templates: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

# ===== LLM Configuration Endpoints =====

@app.route('/api/llm-config', methods=['GET'])
def llm_config_get():
    """Get LLM configuration."""
    try:
        config_path = 'config/llm_configuration.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return jsonify({
                "success": True,
                "data": config,
                "message": "LLM configuration loaded"
            })
        else:
            return jsonify({
                "success": False,
                "message": "LLM configuration file not found",
                "error": "FILE_NOT_FOUND"
            }), 404
            
    except Exception as e:
        logger.error(f"Error in llm_config_get: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/llm-config', methods=['POST'])
def llm_config_save():
    """Save LLM configuration."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        config_path = 'config/llm_configuration.json'
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Add metadata
        config_data = {
            **data,
            "updated_at": datetime.now().isoformat(),
            "updated_by": "admin"
        }
        
        # Save to file
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "message": "LLM configuration saved successfully",
            "config_path": config_path
        })
        
    except Exception as e:
        logger.error(f"Error in llm_config_save: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/llm-config/test', methods=['POST'])
def llm_config_test():
    """Test LLM configuration."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        provider_name = data.get('provider_name')
        if not provider_name:
            return jsonify({
                "success": False,
                "message": "Provider name is required",
                "error": "Missing provider_name"
            }), 400
        
        # Test the provider
        try:
            # Import LLM manager for testing
            from diary_agent.core.llm_manager.llm_manager import LLMManager
            test_manager = LLMManager('config/llm_configuration.json')
            
            # Test with a simple prompt
            test_prompt = "Hello, this is a test message. Please respond with 'Test successful'."
            response = test_manager.generate_text_with_failover(
                prompt=test_prompt,
                system_prompt="You are a helpful assistant.",
                provider_name=provider_name
            )
            
            return jsonify({
                "success": True,
                "message": f"Provider {provider_name} test successful",
                "response": response[:100] + "..." if len(response) > 100 else response
            })
            
        except Exception as test_error:
            return jsonify({
                "success": False,
                "message": f"Provider {provider_name} test failed: {str(test_error)}",
                "error": "TEST_FAILED"
            }), 400
            
    except Exception as e:
        logger.error(f"Error in llm_config_test: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/llm-config/check-local', methods=['POST'])
def llm_config_check_local():
    """Check if local Ollama model is running."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        model_name = data.get('model_name')
        if not model_name:
            return jsonify({
                "success": False,
                "message": "Model name is required",
                "error": "Missing model_name"
            }), 400
        
        # Check if Ollama is running and model is available
        try:
            import requests
            ollama_url = "http://localhost:11434"
            
            # Check if Ollama is running
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if model_name in model_names:
                    return jsonify({
                        "success": True,
                        "message": f"Model {model_name} is available",
                        "running": True,
                        "available_models": model_names
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": f"Model {model_name} not found. Available models: {', '.join(model_names)}",
                        "running": False,
                        "available_models": model_names
                    })
            else:
                return jsonify({
                    "success": False,
                    "message": "Ollama server is not responding",
                    "running": False
                })
                
        except requests.exceptions.RequestException:
            return jsonify({
                "success": False,
                "message": "Ollama server is not running or not accessible",
                "running": False
            })
            
    except Exception as e:
        logger.error(f"Error in llm_config_check_local: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "success": True,
        "message": "Simple Diary API is running",
        "data": {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "type": "simple_diary_api",
            "events_loaded": len(diary_manager.events_config) > 0
        }
    })

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all available events from events.json."""
    return jsonify({
        "success": True,
        "message": "Events retrieved successfully",
        "data": diary_manager.get_available_events(),
        "timestamp": datetime.now().isoformat()
    })

# ===== Event Agents (Extraction / Update) =====

@app.route('/api/event/extract', methods=['POST'])
def event_extract():
    try:
        payload = request.get_json() or {}
        required = ["chat_uuid", "chat_event_uuid", "memory_uuid", "dialogue"]
        missing = [k for k in required if k not in payload]
        if missing:
            return jsonify({
                "success": False,
                "message": f"Missing required fields: {', '.join(missing)}",
                "error": "Invalid request"
            }), 400

        result = asyncio.run(extraction_agent.run(payload))
        return jsonify({
            "success": True,
            "message": "Extraction completed",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in event_extract: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500


@app.route('/api/event/update', methods=['POST'])
def event_update():
    try:
        body = request.get_json() or {}
        extraction_result = body.get("extraction_result")
        related_events = body.get("related_events", [])
        if not isinstance(related_events, list):
            return jsonify({"success": False, "message": "related_events must be a list"}), 400
        if not isinstance(extraction_result, dict):
            return jsonify({"success": False, "message": "extraction_result must be an object"}), 400

        result = asyncio.run(update_agent.run(extraction_result, related_events))
        return jsonify({
            "success": True,
            "message": "Update completed",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in event_update: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500


@app.route('/api/bazi_wuxing/calc', methods=['POST'])
def bazi_wuxing_calc():
    """Calculate BaZi and WuXing from birth info using BaziWuxingAgent."""
    try:
        body = request.get_json() or {}
        required = ["birth_year", "birth_month", "birth_day", "birth_hour", "birthplace"]
        missing = [k for k in required if k not in body]
        if missing:
            return jsonify({
                "success": False,
                "message": f"Missing required fields: {', '.join(missing)}",
                "error": "Invalid request"
            }), 400

        result = asyncio.run(bazi_agent.run(body))
        return jsonify({
            "success": True,
            "message": "BaZi/WuXing calculated",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in bazi_wuxing_calc: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500


@app.route('/api/sensor/translate', methods=['POST'])
def translate_sensor_event():
    """Translate sensor event to human-readable description."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        # Validate required fields
        if 'sensor_type' not in request_data:
            return jsonify({
                "success": False,
                "message": "Missing required field: sensor_type",
                "error": "Invalid request data"
            }), 400
        
        # Create MQTT-like message for sensor agent
        sensor_type = request_data['sensor_type']
        sensor_data = {k: v for k, v in request_data.items() if k != 'sensor_type'}
        
        # Structure the message so the sensor agent can extract the sensor_type
        mqtt_message = {
            "sensor_type": sensor_type,
            "topic": f"sensor/{sensor_type}",
            "timestamp": datetime.now().isoformat(),
            **sensor_data  # Include all sensor data directly in the message
        }
        
        # Translate sensor event
        result = asyncio.run(sensor_agent.translate_sensor_event(mqtt_message))
        
        return jsonify({
            "success": True,
            "message": "Sensor event translated successfully",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error translating sensor event: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to translate sensor event",
            "error": str(e)
        }), 500


@app.route('/api/event/pipeline', methods=['POST'])
def event_pipeline():
    try:
        body = request.get_json() or {}
        dialogue_payload = body.get("dialogue_payload") or {}
        related_events = body.get("related_events", [])
        required = ["chat_uuid", "chat_event_uuid", "memory_uuid", "dialogue"]
        missing = [k for k in required if k not in dialogue_payload]
        if missing:
            return jsonify({
                "success": False,
                "message": f"Missing required fields in dialogue_payload: {', '.join(missing)}"
            }), 400
        if not isinstance(related_events, list):
            return jsonify({"success": False, "message": "related_events must be a list"}), 400

        extraction = asyncio.run(extraction_agent.run(dialogue_payload))
        update = asyncio.run(update_agent.run(extraction, related_events))
        return jsonify({
            "success": True,
            "message": "Pipeline completed",
            "data": {"extraction": extraction, "update": update},
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in event_pipeline: {e}")
        return jsonify({"success": False, "message": "Internal server error", "error": str(e)}), 500

@app.route('/api/diary/process', methods=['POST'])
async def process_event():
    """Process a single event and generate diary if conditions are met."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        # Validate required fields (only event_category and event_name needed)
        required_fields = ['event_category', 'event_name']
        for field in required_fields:
            if field not in request_data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}",
                    "error": "Invalid request data"
                }), 400
        
        event_category = request_data['event_category']
        event_name = request_data['event_name']
        
        # Auto-generate event details based on event name
        event_details = diary_manager.generate_event_details(event_category, event_name)
        
        # Validate event exists in events.json
        if not diary_manager.validate_event(event_category, event_name):
            return jsonify({
                "success": False,
                "message": f"Event '{event_name}' not found in category '{event_category}'",
                "error": "Invalid event",
                "data": {
                    "available_events": diary_manager.get_available_events()
                }
            }), 400
        
        # Check if diary should be generated
        should_generate = diary_manager.should_generate_diary(event_category, event_name)
        
        if not should_generate:
            return jsonify({
                "success": True,
                "message": "Event processed but no diary generated",
                "data": {
                    "event_category": event_category,
                    "event_name": event_name,
                    "diary_generated": False,
                    "reason": "Random condition not met"
                },
                "timestamp": datetime.now().isoformat()
            })
        
        # Generate diary entry
        diary_entry = await diary_manager.generate_diary_for_event(
            event_category, event_name, event_details
        )
        
        if diary_entry:
            return jsonify({
                "success": True,
                "message": "Diary generated successfully",
                "data": {
                    "event_category": event_category,
                    "event_name": event_name,
                    "diary_generated": True,
                    "diary_entry": {
                        "entry_id": diary_entry.entry_id,
                        "title": diary_entry.title,
                        "content": diary_entry.content,
                        "emotion_tags": [tag.value for tag in diary_entry.emotion_tags] if diary_entry.emotion_tags else [],
                        "timestamp": diary_entry.timestamp.isoformat(),
                        "agent_type": diary_entry.agent_type,
                        "llm_provider": diary_entry.llm_provider
                    }
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to generate diary entry",
                "error": "Diary generation failed"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in process_event endpoint: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error": str(e)
        }), 500

@app.route('/api/diary/process-custom', methods=['POST'])
async def process_event_with_custom_prompt():
    """Process a single event with custom prompt configuration."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        # Validate required fields
        required_fields = ['event_category', 'event_name', 'custom_prompt']
        for field in required_fields:
            if field not in request_data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}",
                    "error": "Invalid request data"
                }), 400
        
        event_category = request_data['event_category']
        event_name = request_data['event_name']
        custom_prompt = request_data['custom_prompt']
        
        # Validate custom prompt structure
        if not isinstance(custom_prompt, dict) or 'system_prompt' not in custom_prompt:
            return jsonify({
                "success": False,
                "message": "Invalid custom prompt format",
                "error": "Custom prompt must contain system_prompt"
            }), 400
        
        # Auto-generate event details based on event name
        event_details = diary_manager.generate_event_details(event_category, event_name)
        
        # Validate event exists in events.json
        if not diary_manager.validate_event(event_category, event_name):
            return jsonify({
                "success": False,
                "message": f"Event '{event_name}' not found in category '{event_category}'",
                "error": "Invalid event",
                "data": {
                    "available_events": diary_manager.get_available_events()
                }
            }), 400
        
        # Check if diary should be generated
        should_generate = diary_manager.should_generate_diary(event_category, event_name)
        
        if not should_generate:
            return jsonify({
                "success": True,
                "message": "Event processed but no diary generated",
                "data": {
                    "event_category": event_category,
                    "event_name": event_name,
                    "event_details": event_details,
                    "diary_generated": False,
                    "reason": "Event does not meet diary generation conditions"
                }
            })
        
        # Generate diary with custom prompt
        diary_result = await diary_manager.generate_diary_with_custom_prompt(
            event_category=event_category,
            event_name=event_name,
            event_details=event_details,
            custom_prompt=custom_prompt,
            sub_agent=request_data.get('sub_agent', 'interactive'),
            additional_data=request_data
        )
        
        if diary_result['success']:
            return jsonify({
                "success": True,
                "message": "Diary generated successfully",
                "data": diary_result['data'],
                "timestamp": datetime.now().isoformat(),
                "provider": diary_result.get('provider', 'unknown'),
                "responseTime": diary_result.get('response_time', 0)
            })
        else:
            return jsonify({
                "success": False,
                "message": diary_result.get('message', 'Failed to generate diary'),
                "error": diary_result.get('error', 'Unknown error'),
                "data": diary_result.get('data', {})
            }), 500
            
    except Exception as e:
        logger.error(f"Error in process_event_with_custom_prompt: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error": str(e)
        }), 500

@app.route('/api/diary/batch-process', methods=['POST'])
async def batch_process_events():
    """Process multiple events and generate diaries for those that meet conditions."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        # Validate required fields
        if 'events' not in request_data:
            return jsonify({
                "success": False,
                "message": "Missing events in request",
                "error": "events field is required"
            }), 400
        
        if not isinstance(request_data['events'], list):
            return jsonify({
                "success": False,
                "message": "Events must be a list",
                "error": "Invalid events format"
            }), 400
        
        # Process each event
        results = []
        generated_diaries = []
        
        for i, event_data in enumerate(request_data['events']):
            # Validate each event (only event_category and event_name needed)
            required_fields = ['event_category', 'event_name']
            for field in required_fields:
                if field not in event_data:
                    return jsonify({
                        "success": False,
                        "message": f"Missing required field '{field}' in event {i}",
                        "error": "Invalid event data"
                    }), 400
            
            event_category = event_data['event_category']
            event_name = event_data['event_name']
            
            # Auto-generate event details
            event_details = diary_manager.generate_event_details(event_category, event_name)
            
            # Validate event exists
            if not diary_manager.validate_event(event_category, event_name):
                results.append({
                    "event_index": i,
                    "event_category": event_category,
                    "event_name": event_name,
                    "status": "invalid",
                    "reason": f"Event '{event_name}' not found in category '{event_category}'"
                })
                continue
            
            # Check if diary should be generated
            should_generate = diary_manager.should_generate_diary(event_category, event_name)
            
            if should_generate:
                # Generate diary entry
                diary_entry = await diary_manager.generate_diary_for_event(
                    event_category, event_name, event_details
                )
                
                if diary_entry:
                    diary_data = {
                        "entry_id": diary_entry.entry_id,
                        "title": diary_entry.title,
                        "content": diary_entry.content,
                        "emotion_tags": [tag.value for tag in diary_entry.emotion_tags] if diary_entry.emotion_tags else [],
                        "timestamp": diary_entry.timestamp.isoformat(),
                        "agent_type": diary_entry.agent_type,
                        "llm_provider": diary_entry.llm_provider
                    }
                    
                    generated_diaries.append(diary_data)
                    results.append({
                        "event_index": i,
                        "event_category": event_category,
                        "event_name": event_name,
                        "status": "diary_generated",
                        "diary_entry": diary_data
                    })
                else:
                    results.append({
                        "event_index": i,
                        "event_category": event_category,
                        "event_name": event_name,
                        "status": "generation_failed",
                        "reason": "Diary generation failed"
                    })
            else:
                results.append({
                    "event_index": i,
                    "event_category": event_category,
                    "event_name": event_name,
                    "status": "no_diary",
                    "reason": "Random condition not met"
                })
        
        return jsonify({
            "success": True,
            "message": f"Processed {len(request_data['events'])} events",
            "data": {
                "total_events": len(request_data['events']),
                "diaries_generated": len(generated_diaries),
                "results": results,
                "generated_diaries": generated_diaries
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in batch_process_events endpoint: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error": str(e)
        }), 500

@app.route('/api/diary/test', methods=['POST'])
async def test_diary_generation():
    """Test diary generation with sample events from events.json."""
    try:
        # Get available events
        available_events = diary_manager.get_available_events()
        
        # Select a random event for testing
        test_results = []
        
        for category, events in available_events.items():
            if events:  # If category has events
                # Pick first event from each category for testing
                test_event = events[0]
                
                # Generate diary for this event
                diary_entry = await diary_manager.generate_diary_for_event(
                    category, test_event, {"test": True, "category": category}
                )
                
                if diary_entry:
                    test_results.append({
                        "event_category": category,
                        "event_name": test_event,
                        "diary_entry": {
                            "entry_id": diary_entry.entry_id,
                            "title": diary_entry.title,
                            "content": diary_entry.content,
                            "emotion_tags": [tag.value for tag in diary_entry.emotion_tags] if diary_entry.emotion_tags else [],
                            "timestamp": diary_entry.timestamp.isoformat(),
                            "agent_type": diary_entry.agent_type,
                            "llm_provider": diary_entry.llm_provider
                        }
                    })
        
        return jsonify({
            "success": True,
            "message": "Test completed successfully",
            "data": {
                "test_results": test_results,
                "total_generated": len(test_results),
                "available_events": available_events
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in test_diary_generation endpoint: {e}")
        return jsonify({
            "success": False,
            "message": "Test failed",
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "message": "Endpoint not found",
        "error": "The requested endpoint does not exist",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        "success": False,
        "message": "Method not allowed",
        "error": "The HTTP method is not allowed for this endpoint",
        "timestamp": datetime.now().isoformat()
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "success": False,
        "message": "Internal server error",
        "error": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }), 500

def run_simple_api_server(host='0.0.0.0', port=5003, debug=False):
    """Run the simple diary API server."""
    print(f"🚀 Starting Simple Diary API Server")
    print(f"📍 Server running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("=" * 60)
    print("Available Simple API Endpoints:")
    print("  GET  /api/health              - Health check")
    print("  GET  /api/events              - Get all events from events.json")
    print("  POST /api/diary/process        - Process single event")
    print("  POST /api/diary/batch-process  - Process multiple events")
    print("  POST /api/diary/test          - Test with sample events")
    print("  POST /api/bazi_wuxing/calc    - Calculate BaZi and WuXing")
    print("=" * 60)
    print("🎯 Simple API - Based on events.json!")
    print("📋 Processes events only if conditions are met!")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Diary API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5003, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_simple_api_server(host=args.host, port=args.port, debug=args.debug)
