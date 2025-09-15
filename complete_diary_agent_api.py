#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Diary Agent API
This API implements the entire diary agent workflow as specified in diary_agent_specifications_en.md
"""

import sys
import os
import json
import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual agents and configurations
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import PromptConfig, EventData, DiaryEntry, DataReader, DiaryContextData
from diary_agent.agents.interactive_agent import InteractiveAgent
from diary_agent.agents.dialogue_agent import DialogueAgent
from diary_agent.agents.neglect_agent import NeglectAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_diary_agent_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@dataclass
class APIResponse:
    """Standard API response format."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class DailyDiaryPlan:
    """Daily diary planning data."""
    date: str
    planned_count: int
    written_count: int
    remaining_count: int
    event_types_written: List[str]
    status: str  # "planning", "in_progress", "completed"

@dataclass
class EventTrigger:
    """Event trigger data."""
    event_type: str
    event_name: str
    event_details: Dict[str, Any]
    user_id: int
    timestamp: str
    should_write_diary: bool = False

class CompleteDataReader(DataReader):
    """Complete data reader that handles all event types."""
    
    def __init__(self, module_name: str = "complete_module"):
        super().__init__(module_name=module_name, read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """Read event context for any event type."""
        return DiaryContextData(
            user_profile={"name": "主人"},
            event_details=event_data.context_data,
            environmental_context=self._get_environmental_context(event_data),
            social_context=self._get_social_context(event_data),
            emotional_context=self._get_emotional_context(event_data),
            temporal_context={"timestamp": event_data.timestamp.isoformat()}
        )
    
    def _get_environmental_context(self, event_data: EventData) -> Dict:
        """Get environmental context based on event type."""
        if event_data.event_type in ["weather", "season"]:
            return {
                "weather_data": event_data.context_data.get("weather_data", {}),
                "season_data": event_data.context_data.get("season_data", {}),
                "location": event_data.context_data.get("location", {})
            }
        return {}
    
    def _get_social_context(self, event_data: EventData) -> Dict:
        """Get social context based on event type."""
        if event_data.event_type in ["remote_toy_interaction", "toy_close_friend", "human_machine_interaction"]:
            return {
                "interaction_partner": event_data.context_data.get("partner_info", {}),
                "relationship_type": event_data.context_data.get("relationship_type", "unknown")
            }
        return {}
    
    def _get_emotional_context(self, event_data: EventData) -> Dict:
        """Get emotional context based on event type."""
        return {
            "toy_emotion": event_data.context_data.get("toy_emotion", "neutral"),
            "owner_emotion": event_data.context_data.get("owner_emotion", "neutral"),
            "emotional_intensity": event_data.context_data.get("emotional_intensity", 0.5)
        }

class CompleteDiaryAgentManager:
    """Manages the complete diary agent workflow."""
    
    def __init__(self):
        self.llm_config_manager = LLMConfigManager()
        self.daily_plans = {}  # Store daily diary plans
        self.data_reader = CompleteDataReader()
        
        # Event type mappings (must be defined before initializing agents)
        self.event_type_mappings = {
            "weather": "weather_agent",
            "season": "season_agent", 
            "current_affairs": "current_affairs_agent",
            "holiday": "holiday_agent",
            "remote_toy_interaction": "remote_interaction_agent",
            "toy_close_friend": "close_friend_agent",
            "claim_event": "claim_agent",
            "human_machine_interaction": "interactive_agent",
            "human_machine_dialogue": "dialogue_agent",
            "interaction_reduction": "neglect_agent"
        }
        
        # Initialize prompt configurations for different event types
        self.prompt_configs = self._initialize_prompt_configs()
        
        # Initialize agents
        self.agents = self._initialize_agents()
    
    def _initialize_prompt_configs(self) -> Dict[str, PromptConfig]:
        """Initialize prompt configurations for all event types."""
        configs = {}
        
        # Base configuration
        base_config = {
            "agent_type": "diary_agent",
            "system_prompt": "你是一个可爱的玩具日记助手，请根据事件信息写一篇简短的日记。直接输出日记内容，不要包含任何思考过程或标签。",
            "output_format": {
                "title": "string",
                "content": "string", 
                "emotion": "string"
            },
            "validation_rules": {
                "title_max_length": 6,
                "content_max_length": 35,
                "required_fields": ["title", "content", "emotion"]
            }
        }
        
        # Weather category
        configs["weather"] = PromptConfig(
            **base_config,
            user_prompt_template="天气事件: {event_name}\n城市: {city}\n天气变化: {weather_changes}\n喜欢的天气: {liked_weather}\n不喜欢的天气: {disliked_weather}\n性格类型: {personality_type}\n\n请写一篇关于天气的日记。"
        )
        
        # Season category
        configs["season"] = PromptConfig(
            **base_config,
            user_prompt_template="季节事件: {event_name}\n城市: {city}\n季节: {season}\n温度: {temperature}\n喜欢的季节: {liked_season}\n不喜欢的季节: {disliked_season}\n性格类型: {personality_type}\n\n请写一篇关于季节的日记。"
        )
        
        # Current affairs
        configs["current_affairs"] = PromptConfig(
            **base_config,
            user_prompt_template="时事热点: {event_name}\n事件标签: {event_tags}\n事件类型: {event_type}\n\n请写一篇关于时事热点的日记。"
        )
        
        # Holiday category
        configs["holiday"] = PromptConfig(
            **base_config,
            user_prompt_template="节日事件: {event_name}\n时间: {time_description}\n节日名称: {holiday_name}\n\n请写一篇关于节日的日记。"
        )
        
        # Remote toy interaction
        configs["remote_toy_interaction"] = PromptConfig(
            **base_config,
            user_prompt_template="远程玩具互动: {event_name}\n好友昵称: {friend_nickname}\n好友主人昵称: {friend_owner_nickname}\n玩具偏好: {toy_preference}\n\n请写一篇关于远程互动的日记。"
        )
        
        # Toy close friend
        configs["toy_close_friend"] = PromptConfig(
            **base_config,
            user_prompt_template="玩具好友同频事件: {event_name}\n玩具主人昵称: {toy_owner_nickname}\n好友昵称: {friend_nickname}\n好友主人昵称: {friend_owner_nickname}\n\n请写一篇关于好友同频的日记。"
        )
        
        # Claim event
        configs["claim_event"] = PromptConfig(
            **base_config,
            user_prompt_template="绑定事件: {event_name}\n主人个人信息: {owner_info}\n\n请写一篇关于设备绑定的日记。"
        )
        
        # Human-machine interaction
        configs["human_machine_interaction"] = PromptConfig(
            **base_config,
            user_prompt_template="人机互动事件: {event_name}\n互动类型: {interaction_type}\n持续时间: {duration}\n用户反应: {user_response}\n玩具情感: {toy_emotion}\n\n请写一篇关于人机互动的日记。"
        )
        
        # Human-machine dialogue
        configs["human_machine_dialogue"] = PromptConfig(
            **base_config,
            user_prompt_template="人机对话事件: {event_name}\n事件摘要: {event_summary}\n事件标题: {event_title}\n内容主题: {content_theme}\n主人情感: {owner_emotion}\n\n请写一篇关于对话的日记。"
        )
        
        # Interaction reduction
        configs["interaction_reduction"] = PromptConfig(
            **base_config,
            user_prompt_template="互动减少事件: {event_name}\n断开类型: {disconnection_type}\n断开天数: {disconnection_days}\n\n请写一篇关于互动减少的日记。"
        )
        
        return configs
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize agents for all event types."""
        agents = {}
        
        for event_type, agent_type in self.event_type_mappings.items():
            prompt_config = self.prompt_configs.get(event_type, self.prompt_configs["human_machine_interaction"])
            
            if agent_type == "interactive_agent":
                agents[event_type] = InteractiveAgent(
                    agent_type=agent_type,
                    prompt_config=prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
            elif agent_type == "dialogue_agent":
                agents[event_type] = DialogueAgent(
                    agent_type=agent_type,
                    prompt_config=prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
            elif agent_type == "neglect_agent":
                agents[event_type] = NeglectAgent(
                    agent_type=agent_type,
                    prompt_config=prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
            else:
                # For other event types, use InteractiveAgent as base
                agents[event_type] = InteractiveAgent(
                    agent_type=agent_type,
                    prompt_config=prompt_config,
                    llm_manager=self.llm_config_manager,
                    data_reader=self.data_reader
                )
        
        return agents
    
    def determine_daily_diary_count(self, date: str = None) -> int:
        """At 00:00 daily, determine the number of diaries to write (0-5)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_count = random.randint(0, 5)
        
        # Store daily plan
        self.daily_plans[date] = DailyDiaryPlan(
            date=date,
            planned_count=daily_count,
            written_count=0,
            remaining_count=daily_count,
            event_types_written=[],
            status="planning"
        )
        
        logger.info(f"Daily diary plan for {date}: {daily_count} diaries")
        return daily_count
    
    def should_write_diary_for_event(self, event_type: str, date: str = None) -> bool:
        """Randomly determine if a diary should be written for this event."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Get daily plan
        daily_plan = self.daily_plans.get(date)
        if not daily_plan:
            # Create new daily plan if not exists
            self.determine_daily_diary_count(date)
            daily_plan = self.daily_plans[date]
        
        # Only one diary per event type per day
        if event_type in daily_plan.event_types_written:
            return False
        
        # If we've already written all required diaries, don't write more
        if daily_plan.written_count >= daily_plan.planned_count:
            return False
        
        # Randomly decide if we should write a diary for this event
        should_write = random.choice([True, False])
        
        if should_write:
            daily_plan.event_types_written.append(event_type)
            daily_plan.written_count += 1
            daily_plan.remaining_count = max(0, daily_plan.planned_count - daily_plan.written_count)
            
            if daily_plan.remaining_count == 0:
                daily_plan.status = "completed"
            else:
                daily_plan.status = "in_progress"
        
        return should_write
    
    def clean_llm_output(self, content: str) -> str:
        """Clean LLM output to remove thinking patterns and tags."""
        if not content:
            return ""
        
        # Remove thinking patterns
        thinking_patterns = [
            "<think>", "</think>", "首先", "用户要求", "关于持续忽", 
            "根据事件信息", "作为日记助手", "让我来写", "我来写",
            "思考过程", "分析", "理解", "总结"
        ]
        
        cleaned_content = content
        for pattern in thinking_patterns:
            cleaned_content = cleaned_content.replace(pattern, "")
        
        # Remove extra whitespace
        cleaned_content = " ".join(cleaned_content.split())
        
        # If content is too short after cleaning, try to extract meaningful content
        if len(cleaned_content) < 10:
            import re
            content_match = re.search(r'内容[：:]\s*(.+)', content)
            if content_match:
                cleaned_content = content_match.group(1).strip()
        
        return cleaned_content
    
    async def generate_diary_entry(self, event_trigger: EventTrigger) -> Optional[DiaryEntry]:
        """Generate a diary entry for the given event."""
        try:
            # Create event data
            event_data = EventData(
                event_id=f"complete_event_{uuid.uuid4()}",
                event_type=event_trigger.event_type,
                event_name=event_trigger.event_name,
                user_id=event_trigger.user_id,
                timestamp=datetime.fromisoformat(event_trigger.timestamp),
                context_data=event_trigger.event_details,
                metadata={"api_generated": True, "workflow": "complete"}
            )
            
            # Get the appropriate agent
            agent = self.agents.get(event_trigger.event_type)
            if not agent:
                logger.warning(f"No agent found for event type: {event_trigger.event_type}")
                return None
            
            # Generate diary entry
            diary_entry = await agent.process_event(event_data)
            
            if diary_entry:
                # Clean the content
                diary_entry.content = self.clean_llm_output(diary_entry.content)
                diary_entry.title = self.clean_llm_output(diary_entry.title)
                
            return diary_entry
            
        except Exception as e:
            logger.error(f"Error generating diary entry: {e}")
            return None
    
    def get_daily_plan(self, date: str = None) -> Optional[DailyDiaryPlan]:
        """Get daily diary plan."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.daily_plans.get(date)
    
    def get_all_daily_plans(self) -> Dict[str, DailyDiaryPlan]:
        """Get all daily diary plans."""
        return self.daily_plans

# Initialize the complete diary agent manager
diary_manager = CompleteDiaryAgentManager()

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify(APIResponse(
        success=True,
        message="Complete Diary Agent API is running",
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "type": "complete_diary_agent_api",
            "supported_event_types": list(diary_manager.event_type_mappings.keys())
        }
    ).__dict__)

@app.route('/api/diary/daily-plan', methods=['POST'])
def create_daily_plan():
    """Create daily diary plan (00:00 daily task)."""
    try:
        request_data = request.get_json() or {}
        date = request_data.get('date', datetime.now().strftime("%Y-%m-%d"))
        
        daily_count = diary_manager.determine_daily_diary_count(date)
        daily_plan = diary_manager.get_daily_plan(date)
        
        return jsonify(APIResponse(
            success=True,
            message=f"Daily diary plan created for {date}",
            data={
                "date": date,
                "planned_count": daily_count,
                "written_count": daily_plan.written_count,
                "remaining_count": daily_plan.remaining_count,
                "status": daily_plan.status,
                "event_types_written": daily_plan.event_types_written
            }
        ).__dict__)
        
    except Exception as e:
        logger.error(f"Error creating daily plan: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to create daily plan",
            error=str(e)
        ).__dict__), 500

@app.route('/api/diary/generate', methods=['POST'])
async def generate_diary():
    """Generate a single diary entry with complete workflow."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify(APIResponse(
                success=False,
                message="No JSON data provided",
                error="Missing request body"
            ).__dict__), 400
        
        # Validate required fields
        required_fields = ['event_type', 'event_name', 'event_details']
        for field in required_fields:
            if field not in request_data:
                return jsonify(APIResponse(
                    success=False,
                    message=f"Missing required field: {field}",
                    error="Invalid request data"
                ).__dict__), 400
        
        # Validate event type
        valid_event_types = list(diary_manager.event_type_mappings.keys())
        if request_data['event_type'] not in valid_event_types:
            return jsonify(APIResponse(
                success=False,
                message=f"Invalid event_type. Must be one of: {valid_event_types}",
                error="Invalid event type"
            ).__dict__), 400
        
        # Create event trigger
        event_trigger = EventTrigger(
            event_type=request_data['event_type'],
            event_name=request_data['event_name'],
            event_details=request_data['event_details'],
            user_id=request_data.get('user_id', 1),
            timestamp=request_data.get('timestamp', datetime.now().isoformat())
        )
        
        # Check if should write diary for this event
        date = datetime.now().strftime("%Y-%m-%d")
        should_write = diary_manager.should_write_diary_for_event(event_trigger.event_type, date)
        event_trigger.should_write_diary = should_write
        
        if not should_write:
            return jsonify(APIResponse(
                success=True,
                message="No diary needed for this event",
                data={
                    "should_write": False,
                    "reason": "Daily quota reached or event type already written today"
                }
            ).__dict__)
        
        # Generate diary entry
        diary_entry = await diary_manager.generate_diary_entry(event_trigger)
        
        if diary_entry:
            # Convert to dictionary for JSON response
            diary_data = {
                "entry_id": diary_entry.entry_id,
                "event_type": diary_entry.event_type,
                "event_name": diary_entry.event_name,
                "title": diary_entry.title,
                "content": diary_entry.content,
                "emotion_tags": [tag.value for tag in diary_entry.emotion_tags] if diary_entry.emotion_tags else [],
                "timestamp": diary_entry.timestamp.isoformat(),
                "agent_type": diary_entry.agent_type,
                "llm_provider": diary_entry.llm_provider,
                "should_write": True
            }
            
            return jsonify(APIResponse(
                success=True,
                message="Diary entry generated successfully",
                data=diary_data
            ).__dict__)
        else:
            return jsonify(APIResponse(
                success=False,
                message="Failed to generate diary entry",
                error="Diary generation failed"
            ).__dict__), 500
            
    except Exception as e:
        logger.error(f"Error in generate_diary endpoint: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Internal server error",
            error=str(e)
        ).__dict__), 500

@app.route('/api/diary/batch', methods=['POST'])
async def generate_batch_diary():
    """Generate multiple diary entries with complete workflow."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify(APIResponse(
                success=False,
                message="No JSON data provided",
                error="Missing request body"
            ).__dict__), 400
        
        # Validate batch request
        if 'events' not in request_data:
            return jsonify(APIResponse(
                success=False,
                message="Missing events in request",
                error="events field is required"
            ).__dict__), 400
        
        if not isinstance(request_data['events'], list):
            return jsonify(APIResponse(
                success=False,
                message="Events must be a list",
                error="Invalid events format"
            ).__dict__), 400
        
        # Process each event
        diary_entries = []
        skipped_events = []
        
        for i, event_data in enumerate(request_data['events']):
            # Validate each event
            required_fields = ['event_type', 'event_name', 'event_details']
            for field in required_fields:
                if field not in event_data:
                    return jsonify(APIResponse(
                        success=False,
                        message=f"Missing required field '{field}' in event {i}",
                        error="Invalid event data"
                    ).__dict__), 400
            
            # Create event trigger
            event_trigger = EventTrigger(
                event_type=event_data['event_type'],
                event_name=event_data['event_name'],
                event_details=event_data['event_details'],
                user_id=event_data.get('user_id', 1),
                timestamp=event_data.get('timestamp', datetime.now().isoformat())
            )
            
            # Check if should write diary
            date = datetime.now().strftime("%Y-%m-%d")
            should_write = diary_manager.should_write_diary_for_event(event_trigger.event_type, date)
            
            if should_write:
                diary_entry = await diary_manager.generate_diary_entry(event_trigger)
                if diary_entry:
                    diary_entries.append(diary_entry)
            else:
                skipped_events.append({
                    "event_index": i,
                    "event_type": event_trigger.event_type,
                    "reason": "Daily quota reached or event type already written today"
                })
        
        # Convert to response format
        diary_data = []
        for diary_entry in diary_entries:
            diary_data.append({
                "entry_id": diary_entry.entry_id,
                "event_type": diary_entry.event_type,
                "event_name": diary_entry.event_name,
                "title": diary_entry.title,
                "content": diary_entry.content,
                "emotion_tags": [tag.value for tag in diary_entry.emotion_tags] if diary_entry.emotion_tags else [],
                "timestamp": diary_entry.timestamp.isoformat(),
                "agent_type": diary_entry.agent_type,
                "llm_provider": diary_entry.llm_provider
            })
        
        return jsonify(APIResponse(
            success=True,
            message=f"Processed {len(request_data['events'])} events, generated {len(diary_entries)} diary entries",
            data={
                "diary_entries": diary_data,
                "total_generated": len(diary_entries),
                "total_requested": len(request_data['events']),
                "skipped_events": skipped_events
            }
        ).__dict__)
        
    except Exception as e:
        logger.error(f"Error in generate_batch_diary endpoint: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Internal server error",
            error=str(e)
        ).__dict__), 500

@app.route('/api/diary/daily-status', methods=['GET'])
def get_daily_status():
    """Get current daily diary status."""
    try:
        date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
        daily_plan = diary_manager.get_daily_plan(date)
        
        if not daily_plan:
            return jsonify(APIResponse(
                success=False,
                message=f"No daily plan found for {date}",
                error="Daily plan not created"
            ).__dict__), 404
        
        return jsonify(APIResponse(
            success=True,
            message=f"Daily status retrieved for {date}",
            data=asdict(daily_plan)
        ).__dict__)
        
    except Exception as e:
        logger.error(f"Error getting daily status: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to get daily status",
            error=str(e)
        ).__dict__), 500

@app.route('/api/diary/event-types', methods=['GET'])
def get_event_types():
    """Get all supported event types."""
    return jsonify(APIResponse(
        success=True,
        message="Event types retrieved successfully",
        data={
            "event_types": list(diary_manager.event_type_mappings.keys()),
            "event_type_mappings": diary_manager.event_type_mappings,
            "total_types": len(diary_manager.event_type_mappings)
        }
    ).__dict__)

@app.route('/api/diary/workflow-test', methods=['POST'])
async def test_complete_workflow():
    """Test the complete diary workflow with sample events."""
    try:
        # Create daily plan first
        date = datetime.now().strftime("%Y-%m-%d")
        daily_count = diary_manager.determine_daily_diary_count(date)
        
        # Sample events for testing
        test_events = [
            {
                "event_type": "weather",
                "event_name": "sunny_day",
                "event_details": {
                    "city": "北京",
                    "weather_changes": "晴天转多云",
                    "liked_weather": "晴天",
                    "disliked_weather": "雨天",
                    "personality_type": "开朗"
                }
            },
            {
                "event_type": "human_machine_interaction",
                "event_name": "petting_session",
                "event_details": {
                    "interaction_type": "抚摸",
                    "duration": "10分钟",
                    "user_response": "positive",
                    "toy_emotion": "开心"
                }
            },
            {
                "event_type": "holiday",
                "event_name": "spring_festival",
                "event_details": {
                    "time_description": "春节第2天",
                    "holiday_name": "春节",
                    "festivity_level": "high"
                }
            }
        ]
        
        # Process events
        diary_entries = []
        for event_data in test_events:
            event_trigger = EventTrigger(
                event_type=event_data['event_type'],
                event_name=event_data['event_name'],
                event_details=event_data['event_details'],
                user_id=1,
                timestamp=datetime.now().isoformat()
            )
            
            should_write = diary_manager.should_write_diary_for_event(event_trigger.event_type, date)
            if should_write:
                diary_entry = await diary_manager.generate_diary_entry(event_trigger)
                if diary_entry:
                    diary_entries.append(diary_entry)
        
        # Get final daily status
        final_plan = diary_manager.get_daily_plan(date)
        
        # Convert results
        test_results = []
        for diary_entry in diary_entries:
            test_results.append({
                "entry_id": diary_entry.entry_id,
                "event_type": diary_entry.event_type,
                "event_name": diary_entry.event_name,
                "title": diary_entry.title,
                "content": diary_entry.content,
                "emotion_tags": [tag.value for tag in diary_entry.emotion_tags] if diary_entry.emotion_tags else [],
                "timestamp": diary_entry.timestamp.isoformat(),
                "agent_type": diary_entry.agent_type,
                "llm_provider": diary_entry.llm_provider
            })
        
        return jsonify(APIResponse(
            success=True,
            message="Complete workflow test completed successfully",
            data={
                "test_results": test_results,
                "daily_plan": asdict(final_plan),
                "total_generated": len(diary_entries),
                "test_timestamp": datetime.now().isoformat()
            }
        ).__dict__)
        
    except Exception as e:
        logger.error(f"Error in workflow test: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Workflow test failed",
            error=str(e)
        ).__dict__), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify(APIResponse(
        success=False,
        message="Endpoint not found",
        error="The requested endpoint does not exist"
    ).__dict__), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify(APIResponse(
        success=False,
        message="Method not allowed",
        error="The HTTP method is not allowed for this endpoint"
    ).__dict__), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify(APIResponse(
        success=False,
        message="Internal server error",
        error="An unexpected error occurred"
    ).__dict__), 500

def run_complete_api_server(host='0.0.0.0', port=5002, debug=False):
    """Run the complete diary agent API server."""
    print(f"🚀 Starting Complete Diary Agent API Server")
    print(f"📍 Server running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("=" * 60)
    print("Available Complete Workflow Endpoints:")
    print("  GET  /api/health                    - Health check")
    print("  POST /api/diary/daily-plan          - Create daily diary plan (00:00 task)")
    print("  POST /api/diary/generate             - Generate single diary entry")
    print("  POST /api/diary/batch               - Generate multiple diary entries")
    print("  GET  /api/diary/daily-status        - Get daily diary status")
    print("  GET  /api/diary/event-types         - Get supported event types")
    print("  POST /api/diary/workflow-test       - Test complete workflow")
    print("=" * 60)
    print("🎯 Complete Diary Agent Workflow Implementation!")
    print("📋 Supports all 10 event types from specifications")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete Diary Agent API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5002, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_complete_api_server(host=args.host, port=args.port, debug=args.debug)
