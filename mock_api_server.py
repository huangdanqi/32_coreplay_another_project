#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock API Server for Diary System
This server provides mock endpoints that simulate the diary generation API.
"""

import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import random

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Mock diary templates
MOCK_DIARY_TEMPLATES = {
    "human_machine_interaction": {
        "titles": [
            "被抚摸的快乐时光",
            "主人的温柔触摸",
            "互动中的小确幸",
            "抚摸带来的温暖",
            "亲密接触的喜悦"
        ],
        "contents": [
            "今天主人轻轻地抚摸了我，感觉特别温暖和舒适。这种亲密接触让我感到被爱着，心情变得很好。",
            "主人的手很温柔，抚摸的时候让我感到安心。这种互动让我觉得我们之间的感情更加深厚了。",
            "被抚摸的感觉真好，就像被阳光包围一样温暖。主人的每一个动作都充满了爱意。",
            "今天的互动让我很开心，主人的抚摸让我感到被重视和关爱。",
            "抚摸的时光总是过得很快，但留下的温暖感觉会持续很久。"
        ],
        "emotions": ["开心", "温暖", "舒适", "被爱", "安心"]
    },
    "dialogue": {
        "titles": [
            "与主人的对话",
            "心灵的交流",
            "温暖的聊天",
            "情感的表达",
            "对话中的理解"
        ],
        "contents": [
            "今天和主人聊了很多，感觉我们的心更近了。主人的话语让我感到被理解和关心。",
            "对话中主人分享了很多心情，我也用我的方式回应着。这种交流让我感到温暖。",
            "主人的声音很温柔，听她说话让我感到安心。我们的对话充满了爱意。",
            "今天的聊天让我学到了很多，也感受到了主人对我的爱。",
            "对话是最好的沟通方式，让我更了解主人的内心世界。"
        ],
        "emotions": ["理解", "温暖", "被关心", "安心", "爱意"]
    },
    "neglect": {
        "titles": [
            "等待的时光",
            "思念主人",
            "孤独的感受",
            "期待重逢",
            "静默的等待"
        ],
        "contents": [
            "今天没有和主人互动，感觉有点孤单。但我相信主人很快就会回来的。",
            "等待的时光总是很漫长，但我不会放弃希望。主人一定是有事情要忙。",
            "虽然今天很安静，但我依然保持着对主人的思念。",
            "孤独的感觉不好受，但我相信这只是暂时的。",
            "等待中学会了耐心，也让我更加珍惜和主人在一起的时光。"
        ],
        "emotions": ["孤单", "思念", "耐心", "期待", "珍惜"]
    }
}

def generate_mock_diary_entry(event_type, event_name, event_details):
    """Generate a mock diary entry."""
    template = MOCK_DIARY_TEMPLATES.get(event_type, MOCK_DIARY_TEMPLATES["human_machine_interaction"])
    
    # Select random elements
    title = random.choice(template["titles"])
    content = random.choice(template["contents"])
    emotion = random.choice(template["emotions"])
    
    # Create mock diary entry
    diary_entry = {
        "entry_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_name": event_name,
        "title": title,
        "content": content,
        "emotion_tags": [emotion],
        "timestamp": datetime.now().isoformat(),
        "agent_type": f"{event_type}_agent",
        "llm_provider": "mock_provider",
        "event_details": event_details
    }
    
    return diary_entry

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "success": True,
        "message": "Mock API is running",
        "data": {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "type": "mock_api"
        }
    })

@app.route('/api/diary/generate', methods=['POST'])
def generate_diary():
    """Generate a single mock diary entry."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        # Validate required fields
        required_fields = ['event_type', 'event_name', 'event_details']
        for field in required_fields:
            if field not in request_data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}",
                    "error": "Invalid request data"
                }), 400
        
        # Validate event type
        valid_event_types = ['human_machine_interaction', 'dialogue', 'neglect']
        if request_data['event_type'] not in valid_event_types:
            return jsonify({
                "success": False,
                "message": f"Invalid event_type. Must be one of: {valid_event_types}",
                "error": "Invalid event type"
            }), 400
        
        # Generate mock diary entry
        diary_entry = generate_mock_diary_entry(
            request_data['event_type'],
            request_data['event_name'],
            request_data['event_details']
        )
        
        return jsonify({
            "success": True,
            "message": "Mock diary entry generated successfully",
            "data": diary_entry,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error": str(e)
        }), 500

@app.route('/api/diary/batch', methods=['POST'])
def generate_batch_diary():
    """Generate multiple mock diary entries."""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "message": "No JSON data provided",
                "error": "Missing request body"
            }), 400
        
        # Validate batch request
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
        
        # Generate mock diary entries
        diary_entries = []
        for event_data in request_data['events']:
            # Validate each event
            required_fields = ['event_type', 'event_name', 'event_details']
            for field in required_fields:
                if field not in event_data:
                    return jsonify({
                        "success": False,
                        "message": f"Missing required field '{field}' in event",
                        "error": "Invalid event data"
                    }), 400
            
            # Generate diary entry
            diary_entry = generate_mock_diary_entry(
                event_data['event_type'],
                event_data['event_name'],
                event_data['event_details']
            )
            diary_entries.append(diary_entry)
        
        return jsonify({
            "success": True,
            "message": f"Generated {len(diary_entries)} mock diary entries successfully",
            "data": {
                "diary_entries": diary_entries,
                "total_generated": len(diary_entries),
                "total_requested": len(request_data['events'])
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error": str(e)
        }), 500

@app.route('/api/diary/templates', methods=['GET'])
def get_event_templates():
    """Get available event templates."""
    templates = {
        "human_machine_interaction": {
            "name": "人机互动事件",
            "description": "Physical interaction between user and toy",
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
            "description": "Verbal communication events",
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
            "description": "Periods of no interaction or communication",
            "examples": [
                {
                    "name": "neglect_1_day_no_dialogue",
                    "details": {
                        "neglect_duration": 1,
                        "neglect_type": "no_dialogue",
                        "disconnection_type": "无对话有互动",
                        "disconnection_days": 1,
                        "memory_status": "on",
                        "last_interaction_date": (datetime.now()).isoformat()
                    }
                }
            ]
        }
    }
    
    return jsonify({
        "success": True,
        "message": "Event templates retrieved successfully",
        "data": templates,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/diary/test', methods=['POST'])
def test_diary_system():
    """Test the mock diary system with sample data."""
    try:
        # Generate test diary entries
        test_events = [
            {
                "event_type": "human_machine_interaction",
                "event_name": "test_interaction",
                "event_details": {
                    "interaction_type": "抚摸",
                    "duration": "5分钟",
                    "user_response": "positive",
                    "toy_emotion": "开心"
                }
            },
            {
                "event_type": "dialogue",
                "event_name": "test_dialogue",
                "event_details": {
                    "dialogue_type": "开心对话",
                    "content": "主人今天心情很好",
                    "duration": "10分钟",
                    "toy_emotion": "开心快乐"
                }
            }
        ]
        
        # Generate mock diary entries
        diary_entries = []
        for test_event in test_events:
            diary_entry = generate_mock_diary_entry(
                test_event["event_type"],
                test_event["event_name"],
                test_event["event_details"]
            )
            diary_entries.append(diary_entry)
        
        return jsonify({
            "success": True,
            "message": "Mock test completed successfully",
            "data": {
                "test_results": diary_entries,
                "total_generated": len(diary_entries),
                "test_timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Mock test failed",
            "error": str(e)
        }), 500

@app.route('/api/diary/random', methods=['POST'])
def generate_random_diary():
    """Generate a completely random diary entry."""
    try:
        # Random event type
        event_types = ['human_machine_interaction', 'dialogue', 'neglect']
        event_type = random.choice(event_types)
        
        # Random event name
        event_names = {
            'human_machine_interaction': ['random_interaction', 'surprise_touch', 'unexpected_care'],
            'dialogue': ['random_chat', 'surprise_conversation', 'unexpected_dialogue'],
            'neglect': ['random_wait', 'surprise_silence', 'unexpected_quiet']
        }
        event_name = random.choice(event_names[event_type])
        
        # Random event details
        event_details = {
            "random_factor": random.randint(1, 100),
            "timestamp": datetime.now().isoformat(),
            "mock_data": True
        }
        
        # Generate diary entry
        diary_entry = generate_mock_diary_entry(event_type, event_name, event_details)
        
        return jsonify({
            "success": True,
            "message": "Random mock diary entry generated successfully",
            "data": diary_entry,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Random generation failed",
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

def run_mock_server(host='0.0.0.0', port=5001, debug=False):
    """Run the mock API server."""
    print(f"🎭 Starting Mock Diary System API Server")
    print(f"📍 Server running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("=" * 60)
    print("Available Mock Endpoints:")
    print("  GET  /api/health           - Health check")
    print("  POST /api/diary/generate   - Generate single mock diary entry")
    print("  POST /api/diary/batch      - Generate multiple mock diary entries")
    print("  GET  /api/diary/templates  - Get event templates")
    print("  POST /api/diary/test       - Test mock diary system")
    print("  POST /api/diary/random     - Generate random mock diary")
    print("=" * 60)
    print("🎯 This is a MOCK API - all responses are simulated!")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Mock Diary System API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_mock_server(host=args.host, port=args.port, debug=args.debug)

