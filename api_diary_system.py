#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API-based Diary System
This module provides REST API endpoints for the diary system with input validation and output generation.
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import uuid

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
        logging.FileHandler('api_diary_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
class DiaryRequest:
    """Request model for diary generation."""
    event_type: str
    event_name: str
    event_details: Dict[str, Any]
    user_id: Optional[int] = 1
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class BatchDiaryRequest:
    """Request model for batch diary generation."""
    events: List[DiaryRequest]
    daily_diary_count: Optional[int] = None
    user_id: Optional[int] = 1

class MockDataReader(DataReader):
    """Mock data reader for API testing."""
    
    def __init__(self, module_name: str = "api_module"):
        super().__init__(module_name=module_name, read_only=True)
    
    def read_event_context(self, event_data: EventData) -> DiaryContextData:
        """Mock event context reading."""
        return DiaryContextData(
            user_profile={"name": "主人"},
            event_details=event_data.context_data,
            environmental_context={},
            social_context={},
            emotional_context={},
            temporal_context={"timestamp": event_data.timestamp.isoformat()}
        )

class APIDiaryManager:
    """Manages diary operations through API."""
    
    def __init__(self):
        self.llm_config_manager = LLMConfigManager()
        
        # Initialize prompt configuration
        self.prompt_config = PromptConfig(
            agent_type="diary_agent",
            system_prompt="你是一个可爱的玩具日记助手，请根据事件信息写一篇简短的日记。直接输出日记内容，不要包含任何思考过程或标签。",
            user_prompt_template="事件类型: {event_type}\n事件名称: {event_name}\n事件详情: {event_details}\n\n请写一篇简短的日记，包含标题和内容。",
            output_format={
                "title": "string",
                "content": "string",
                "emotion": "string"
            },
            validation_rules={
                "title_max_length": 6,
                "content_max_length": 35,
                "required_fields": ["title", "content", "emotion"]
            }
        )
        
        # Initialize agents with mock data readers
        mock_interaction_reader = MockDataReader()
        mock_dialogue_reader = MockDataReader()
        mock_neglect_reader = MockDataReader()
        
        self.interactive_agent = InteractiveAgent(
            agent_type="interactive_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=mock_interaction_reader
        )
        self.dialogue_agent = DialogueAgent(
            agent_type="dialogue_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=mock_dialogue_reader
        )
        self.neglect_agent = NeglectAgent(
            agent_type="neglect_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=mock_neglect_reader
        )
    
    def validate_diary_request(self, request_data: Dict) -> tuple[bool, str]:
        """Validate diary request data."""
        required_fields = ['event_type', 'event_name', 'event_details']
        
        for field in required_fields:
            if field not in request_data:
                return False, f"Missing required field: {field}"
        
        valid_event_types = ['human_machine_interaction', 'dialogue', 'neglect']
        if request_data['event_type'] not in valid_event_types:
            return False, f"Invalid event_type. Must be one of: {valid_event_types}"
        
        if not isinstance(request_data['event_details'], dict):
            return False, "event_details must be a dictionary"
        
        return True, ""
    
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
    
    async def generate_diary_entry(self, diary_request: DiaryRequest) -> Optional[DiaryEntry]:
        """Generate a single diary entry."""
        try:
            # Create event data
            event_data = EventData(
                event_id=f"api_event_{uuid.uuid4()}",
                event_type=diary_request.event_type,
                event_name=diary_request.event_name,
                user_id=diary_request.user_id,
                timestamp=datetime.fromisoformat(diary_request.timestamp),
                context_data=diary_request.event_details,
                metadata={"api_generated": True}
            )
            
            # Select the appropriate agent
            if diary_request.event_type == "human_machine_interaction":
                agent = self.interactive_agent
            elif diary_request.event_type == "dialogue":
                agent = self.dialogue_agent
            elif diary_request.event_type == "neglect":
                agent = self.neglect_agent
            else:
                logger.warning(f"Unknown event type: {diary_request.event_type}")
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
    
    async def generate_batch_diary_entries(self, batch_request: BatchDiaryRequest) -> List[DiaryEntry]:
        """Generate multiple diary entries."""
        diary_entries = []
        
        for diary_request in batch_request.events:
            diary_entry = await self.generate_diary_entry(diary_request)
            if diary_entry:
                diary_entries.append(diary_entry)
        
        return diary_entries

# Initialize the diary manager
diary_manager = APIDiaryManager()

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify(APIResponse(
        success=True,
        message="API is running",
        data={"status": "healthy", "timestamp": datetime.now().isoformat()}
    ).__dict__)

@app.route('/api/diary/generate', methods=['POST'])
async def generate_diary():
    """Generate a single diary entry."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify(APIResponse(
                success=False,
                message="No JSON data provided",
                error="Missing request body"
            ).__dict__), 400
        
        # Validate request
        is_valid, error_message = diary_manager.validate_diary_request(request_data)
        if not is_valid:
            return jsonify(APIResponse(
                success=False,
                message="Invalid request data",
                error=error_message
            ).__dict__), 400
        
        # Create diary request
        diary_request = DiaryRequest(**request_data)
        
        # Generate diary entry
        diary_entry = await diary_manager.generate_diary_entry(diary_request)
        
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
                "llm_provider": diary_entry.llm_provider
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
    """Generate multiple diary entries."""
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
        
        # Validate each event
        for i, event_data in enumerate(request_data['events']):
            is_valid, error_message = diary_manager.validate_diary_request(event_data)
            if not is_valid:
                return jsonify(APIResponse(
                    success=False,
                    message=f"Invalid event data at index {i}",
                    error=error_message
                ).__dict__), 400
        
        # Create batch request
        batch_request = BatchDiaryRequest(**request_data)
        
        # Generate diary entries
        diary_entries = await diary_manager.generate_batch_diary_entries(batch_request)
        
        # Convert to dictionaries for JSON response
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
            message=f"Generated {len(diary_entries)} diary entries successfully",
            data={
                "diary_entries": diary_data,
                "total_generated": len(diary_entries),
                "total_requested": len(batch_request.events)
            }
        ).__dict__)
        
    except Exception as e:
        logger.error(f"Error in generate_batch_diary endpoint: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Internal server error",
            error=str(e)
        ).__dict__), 500

@app.route('/api/diary/templates', methods=['GET'])
def get_event_templates():
    """Get available event templates."""
    templates = {
        "human_machine_interaction": {
            "name": "人机互动事件",
            "examples": [
                {
                    "name": "liked_interaction_once",
                    "details": {
                        "interaction_type": "抚摸",
                        "duration": "5分钟",
                        "user_response": "positive",
                        "toy_emotion": "开心"
                    }
                },
                {
                    "name": "liked_interaction_3_to_5_times",
                    "details": {
                        "interaction_type": "摸摸头",
                        "count": 4,
                        "duration": "20分钟",
                        "user_response": "positive",
                        "toy_emotion": "平静"
                    }
                }
            ]
        },
        "dialogue": {
            "name": "对话事件",
            "examples": [
                {
                    "name": "positive_emotional_dialogue",
                    "details": {
                        "dialogue_type": "开心对话",
                        "content": "主人今天心情很好",
                        "duration": "10分钟",
                        "toy_emotion": "开心快乐"
                    }
                }
            ]
        },
        "neglect": {
            "name": "忽视事件",
            "examples": [
                {
                    "name": "neglect_1_day_no_dialogue",
                    "details": {
                        "neglect_duration": 1,
                        "neglect_type": "no_dialogue",
                        "disconnection_type": "无对话有互动",
                        "disconnection_days": 1,
                        "memory_status": "on",
                        "last_interaction_date": (datetime.now() - timedelta(days=1)).isoformat()
                    }
                }
            ]
        }
    }
    
    return jsonify(APIResponse(
        success=True,
        message="Event templates retrieved successfully",
        data=templates
    ).__dict__)

@app.route('/api/diary/test', methods=['POST'])
async def test_diary_system():
    """Test the diary system with sample data."""
    try:
        # Create sample test data
        test_events = [
            DiaryRequest(
                event_type="human_machine_interaction",
                event_name="test_interaction",
                event_details={
                    "interaction_type": "抚摸",
                    "duration": "5分钟",
                    "user_response": "positive",
                    "toy_emotion": "开心"
                }
            ),
            DiaryRequest(
                event_type="dialogue",
                event_name="test_dialogue",
                event_details={
                    "dialogue_type": "开心对话",
                    "content": "主人今天心情很好",
                    "duration": "10分钟",
                    "toy_emotion": "开心快乐"
                }
            )
        ]
        
        # Generate test diary entries
        diary_entries = []
        for test_event in test_events:
            diary_entry = await diary_manager.generate_diary_entry(test_event)
            if diary_entry:
                diary_entries.append(diary_entry)
        
        # Convert to response format
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
            message="Test completed successfully",
            data={
                "test_results": test_results,
                "total_generated": len(diary_entries),
                "test_timestamp": datetime.now().isoformat()
            }
        ).__dict__)
        
    except Exception as e:
        logger.error(f"Error in test_diary_system endpoint: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Test failed",
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

def run_api_server(host='0.0.0.0', port=5000, debug=False):
    """Run the API server."""
    print(f"🚀 Starting Diary System API Server")
    print(f"📍 Server running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("=" * 60)
    print("Available endpoints:")
    print("  GET  /api/health           - Health check")
    print("  POST /api/diary/generate   - Generate single diary entry")
    print("  POST /api/diary/batch      - Generate multiple diary entries")
    print("  GET  /api/diary/templates  - Get event templates")
    print("  POST /api/diary/test       - Test diary system")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Diary System API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_api_server(host=args.host, port=args.port, debug=args.debug)

