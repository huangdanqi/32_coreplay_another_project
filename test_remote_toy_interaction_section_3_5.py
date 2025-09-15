#!/usr/bin/env python3
"""
Remote Toy Interaction Section 3.5 Test
Tests Section 3.5 requirements for remote toy interaction events:
- Trigger: Each time like/dislike remote interaction is triggered
- Content: Event name, friend nickname, friend owner nickname, toy's preference for action
- Uses local Ollama model for diary generation
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'diary_agent'))

from diary_agent.agents.friends_agent import FriendsAgent
from diary_agent.integration.friends_data_reader import FriendsDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, EmotionalTag


class RemoteToyInteractionTester:
    """Remote toy interaction Section 3.5 tester"""
    
    def __init__(self):
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment using main LLM configuration"""
        # Use the main LLM configuration file
        self.llm_manager = LLMConfigManager("config/llm_configuration.json")
        self.data_reader = FriendsDataReader()
        
        # Load friends agent prompt configuration
        prompt_config_path = "diary_agent/config/agent_prompts/friends_agent.json"
        with open(prompt_config_path, 'r', encoding='utf-8') as f:
            self.prompt_config = json.load(f)
        
        # Initialize friends agent
        self.friends_agent = FriendsAgent(
            agent_type="friends_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_manager,
            data_reader=self.data_reader
        )
        
        print("✓ Test environment setup complete")
        print(f"✓ Using LLM Manager: {type(self.llm_manager).__name__}")
        print(f"✓ Using LLM Provider: {self.llm_manager.get_default_provider()}")
        print(f"✓ Using Data Reader: {type(self.data_reader).__name__}")
        print(f"✓ Using Friends Agent: {type(self.friends_agent).__name__}")
    
    def create_remote_interaction_scenarios(self) -> List[Dict[str, Any]]:
        """Create remote toy interaction test scenarios for Section 3.5"""
        
        scenarios = [
            # Scenario 1: Made new friend (positive)
            {
                "event_name": "made_new_friend",
                "event_type": "friend",
                "friend_nickname": "小猫咪",
                "friend_owner_nickname": "小明",
                "interaction_type": "打招呼",
                "toy_preference": "喜欢",
                "description": "新朋友小猫咪(主人:小明)打招呼，玩具很喜欢"
            },
            
            # Scenario 2: Friend deleted (negative)
            {
                "event_name": "friend_deleted", 
                "event_type": "friend",
                "friend_nickname": "小狗",
                "friend_owner_nickname": "小红",
                "interaction_type": "删除好友",
                "toy_preference": "不喜欢",
                "description": "朋友小狗(主人:小红)删除了好友，玩具很失落"
            },
            
            # Scenario 3: Liked single interaction
            {
                "event_name": "liked_single",
                "event_type": "friend", 
                "friend_nickname": "小兔子",
                "friend_owner_nickname": "小李",
                "interaction_type": "摸头",
                "toy_preference": "喜欢",
                "description": "朋友小兔子(主人:小李)摸头1次，玩具很喜欢"
            },
            
            # Scenario 4: Liked multiple interactions (3-5)
            {
                "event_name": "liked_3_to_5",
                "event_type": "friend",
                "friend_nickname": "小熊",
                "friend_owner_nickname": "小王", 
                "interaction_type": "拥抱",
                "toy_preference": "喜欢",
                "description": "朋友小熊(主人:小王)拥抱3次，玩具很喜欢"
            },
            
            # Scenario 5: Liked many interactions (5+)
            {
                "event_name": "liked_5_plus",
                "event_type": "friend",
                "friend_nickname": "小鸭子",
                "friend_owner_nickname": "小张",
                "interaction_type": "亲吻",
                "toy_preference": "喜欢", 
                "description": "朋友小鸭子(主人:小张)亲吻6次，玩具超喜欢"
            },
            
            # Scenario 6: Disliked single interaction
            {
                "event_name": "disliked_single",
                "event_type": "friend",
                "friend_nickname": "小老虎",
                "friend_owner_nickname": "小陈",
                "interaction_type": "拍打",
                "toy_preference": "不喜欢",
                "description": "朋友小老虎(主人:小陈)拍打1次，玩具不喜欢"
            },
            
            # Scenario 7: Disliked multiple interactions (3-5)
            {
                "event_name": "disliked_3_to_5",
                "event_type": "friend",
                "friend_nickname": "小狮子",
                "friend_owner_nickname": "小刘",
                "interaction_type": "摇晃",
                "toy_preference": "不喜欢",
                "description": "朋友小狮子(主人:小刘)摇晃4次，玩具不喜欢"
            },
            
            # Scenario 8: Disliked many interactions (5+)
            {
                "event_name": "disliked_5_plus",
                "event_type": "friend",
                "friend_nickname": "小鳄鱼",
                "friend_owner_nickname": "小赵",
                "interaction_type": "拉扯",
                "toy_preference": "不喜欢",
                "description": "朋友小鳄鱼(主人:小赵)拉扯7次，玩具很生气"
            }
        ]
        
        return scenarios
    
    async def test_ollama_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags") as response:
                    if response.status == 200:
                        models = await response.json()
                        print(f"✓ Ollama is running with {len(models.get('models', []))} models")
                        
                        # Check if qwen3:4b is available
                        model_names = [model['name'] for model in models.get('models', [])]
                        if 'qwen3:4b' in model_names:
                            print("✓ qwen3:4b model is available")
                            return True
                        else:
                            print(f"⚠ qwen3:4b not found. Available models: {model_names}")
                            return False
                    else:
                        print(f"✗ Ollama responded with status {response.status}")
                        return False
        except Exception as e:
            print(f"✗ Cannot connect to Ollama: {e}")
            print("Please ensure Ollama is running with: ollama serve")
            print("And qwen3:4b model is installed with: ollama pull qwen3:4b")
            return False
    
    async def test_single_remote_interaction_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single remote interaction scenario with real API calls"""
        print(f"\n{'='*50}")
        print(f"TESTING REMOTE TOY INTERACTION SCENARIO")
        print(f"{'='*50}")
        print(f"Event: {scenario['event_name']}")
        print(f"Friend: {scenario['friend_nickname']} (Owner: {scenario['friend_owner_nickname']})")
        print(f"Interaction: {scenario['interaction_type']}")
        print(f"Preference: {scenario['toy_preference']}")
        print(f"Description: {scenario['description']}")
        
        # Create event data with remote interaction information
        event_data = EventData(
            event_id=f"test_remote_interaction_{scenario['event_name']}_{int(datetime.now().timestamp())}",
            event_type=scenario['event_type'],
            event_name=scenario['event_name'],
            timestamp=datetime.now(),
            user_id=1,
            context_data={
                "friend_info": {
                    "friend_nickname": scenario['friend_nickname'],
                    "friend_owner_nickname": scenario['friend_owner_nickname']
                },
                "interaction_info": {
                    "interaction_type": scenario['interaction_type'],
                    "toy_preference": scenario['toy_preference']
                }
            },
            metadata={
                "friend_nickname": scenario['friend_nickname'],
                "friend_owner_nickname": scenario['friend_owner_nickname'],
                "interaction_type": scenario['interaction_type'],
                "toy_preference": scenario['toy_preference']
            }
        )
        
        try:
            print(f"\n--- Step 1: Reading Remote Interaction Context from Real API ---")
            # Use real friends data reader with API
            context_data = self.data_reader.read_event_context(event_data)
            print(f"✓ Context extracted from friends_data_reader.py API")
            print(f"  Event name: {context_data.event_details.get('event_name', 'N/A')}")
            print(f"  Friend count: {context_data.social_context.get('current_friend_count', 'N/A')}")
            print(f"  User role: {context_data.social_context.get('user_role', 'N/A')}")
            print(f"  Emotional tone: {context_data.emotional_context.get('emotional_tone', 'N/A')}")
            print(f"  Emotional intensity: {context_data.emotional_context.get('emotional_intensity', 'N/A')}")
            
            print(f"\n--- Step 2: Generating Remote Interaction Diary with Ollama ---")
            # Use real friends agent with Ollama API
            diary_entry = await self.friends_agent.process_event(event_data)
            print(f"✓ Remote interaction diary generated using Ollama API")
            print(f"  Title: '{diary_entry.title}'")
            print(f"  Content: '{diary_entry.content}'")
            print(f"  Emotion Tags: {[tag.value if hasattr(tag, 'value') else str(tag) for tag in diary_entry.emotion_tags]}")
            print(f"  LLM Provider: {diary_entry.llm_provider}")
            
            print(f"\n--- Step 3: Validating Section 3.5 Requirements ---")
            # Validate results against Section 3.5 requirements
            validation_results = self.validate_section_3_5_requirements(
                diary_entry, scenario, context_data
            )
            
            # Print validation results
            for check, passed in validation_results.items():
                if check != "overall_pass":
                    status = "✓ PASS" if passed else "✗ FAIL"
                    print(f"  {check}: {status}")
            
            overall_status = "✓ OVERALL PASS" if validation_results["overall_pass"] else "✗ OVERALL FAIL"
            print(f"\n{overall_status}")
            
            result = {
                "scenario": scenario,
                "diary_entry": {
                    "title": diary_entry.title,
                    "content": diary_entry.content,
                    "emotion_tags": [tag.value if hasattr(tag, 'value') else str(tag) for tag in diary_entry.emotion_tags],
                    "timestamp": diary_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "llm_provider": diary_entry.llm_provider
                },
                "context_data": {
                    "event_name": context_data.event_details.get('event_name'),
                    "friend_count": context_data.social_context.get('current_friend_count'),
                    "user_role": context_data.social_context.get('user_role'),
                    "emotional_tone": context_data.emotional_context.get('emotional_tone'),
                    "emotional_intensity": context_data.emotional_context.get('emotional_intensity')
                },
                "validation": validation_results,
                "success": validation_results["overall_pass"]
            }
            
            return result
            
        except Exception as e:
            print(f"✗ Error testing remote interaction scenario: {e}")
            import traceback
            traceback.print_exc()
            return {
                "scenario": scenario,
                "error": str(e),
                "success": False
            }
    
    def validate_section_3_5_requirements(self, diary_entry, scenario: Dict[str, Any], 
                                        context_data) -> Dict[str, bool]:
        """
        Validate Section 3.5 requirements specifically for remote toy interactions:
        - Content includes friend nickname and owner nickname
        - Content reflects toy's preference for the action
        - Appropriate emotional context for interaction type
        - Proper formatting (6-char title, 35-char content)
        """
        validation = {}
        
        # Check title length (max 6 characters)
        validation["title_length_valid"] = len(diary_entry.title) <= 6
        
        # Check content length (max 35 characters)
        validation["content_length_valid"] = len(diary_entry.content) <= 35
        
        # Check friend nickname is included in content or title
        friend_nickname = scenario['friend_nickname']
        validation["friend_nickname_included"] = (
            friend_nickname in diary_entry.content or 
            friend_nickname in diary_entry.title
        )
        
        # Check friend owner nickname is included (if space allows)
        friend_owner_nickname = scenario['friend_owner_nickname']
        validation["friend_owner_nickname_included"] = (
            friend_owner_nickname in diary_entry.content or 
            friend_owner_nickname in diary_entry.title
        )
        
        # Check interaction type is contextually appropriate
        interaction_type = scenario['interaction_type']
        toy_preference = scenario['toy_preference']
        content_and_title = diary_entry.content + diary_entry.title
        
        if toy_preference == "喜欢":
            # Should indicate positive feelings
            validation["preference_context_appropriate"] = any(word in content_and_title for word in 
                ["喜欢", "开心", "高兴", "好", "棒", "😊", "😄", "🎉", "开心", "快乐", "兴奋"])
        else:
            # Should indicate negative feelings
            validation["preference_context_appropriate"] = any(word in content_and_title for word in 
                ["不喜欢", "讨厌", "烦", "生气", "难过", "😢", "😠", "😞", "不开心", "失落"])
        
        # Check emotional tags are appropriate for interaction type
        emotion_tag_values = [tag.value if hasattr(tag, 'value') else str(tag) for tag in diary_entry.emotion_tags]
        
        if "liked" in scenario['event_name']:
            # Positive interaction events
            validation["emotion_appropriate"] = any(emotion in emotion_tag_values for emotion in 
                ["开心快乐", "兴奋激动", "好奇"])
        elif "disliked" in scenario['event_name']:
            # Negative interaction events
            validation["emotion_appropriate"] = any(emotion in emotion_tag_values for emotion in 
                ["生气愤怒", "悲伤难过", "焦虑忧愁", "担忧"])
        elif scenario['event_name'] == "made_new_friend":
            # New friend event
            validation["emotion_appropriate"] = any(emotion in emotion_tag_values for emotion in 
                ["开心快乐", "兴奋激动", "好奇"])
        elif scenario['event_name'] == "friend_deleted":
            # Friend deleted event
            validation["emotion_appropriate"] = any(emotion in emotion_tag_values for emotion in 
                ["悲伤难过", "担忧", "焦虑忧愁"])
        else:
            validation["emotion_appropriate"] = True
        
        # Check that emotion tags are from valid set
        valid_emotions = {tag.value for tag in EmotionalTag}
        validation["emotion_tags_valid"] = all(emotion in valid_emotions for emotion in emotion_tag_values)
        
        # Check that diary entry has required fields
        validation["required_fields_present"] = all([
            diary_entry.title,
            diary_entry.content,
            diary_entry.emotion_tags
        ])
        
        # Overall pass - all individual checks must pass
        validation["overall_pass"] = all(validation.values())
        
        return validation
    
    async def run_remote_interaction_test(self):
        """Run comprehensive remote toy interaction Section 3.5 test"""
        print("=" * 60)
        print("REMOTE TOY INTERACTION SECTION 3.5 - REAL API TEST")
        print("=" * 60)
        print("Testing requirements:")
        print("- Using real friends_data_reader.py with API access")
        print("- Using local Ollama model for diary generation")
        print("- Focus: Remote toy interactions only")
        print("- Trigger: Each like/dislike remote interaction")
        print("- Content: Event name, friend nickname, friend owner nickname, toy preference")
        print("=" * 60)
        
        # Test Ollama connection first
        print("\n--- Testing Ollama Connection ---")
        ollama_available = await self.test_ollama_connection()
        if not ollama_available:
            print("Cannot proceed without Ollama. Please start Ollama and install qwen3:4b model.")
            return []
        
        scenarios = self.create_remote_interaction_scenarios()
        results = []
        
        print(f"\nGenerated {len(scenarios)} remote interaction scenarios")
        print(f"Testing all scenarios with real API calls...")
        
        for i, scenario in enumerate(scenarios):
            print(f"\n{'='*60}")
            print(f"REMOTE INTERACTION SCENARIO {i+1}/{len(scenarios)}")
            print(f"{'='*60}")
            
            result = await self.test_single_remote_interaction_scenario(scenario)
            results.append(result)
            
            # Small delay between API calls
            await asyncio.sleep(1)
        
        # Generate summary report
        self.generate_remote_interaction_summary(results)
        
        return results
    
    def generate_remote_interaction_summary(self, results: List[Dict[str, Any]]):
        """Generate remote interaction specific summary report"""
        print("\n" + "=" * 60)
        print("REMOTE TOY INTERACTION SECTION 3.5 SUMMARY REPORT")
        print("=" * 60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get('success', False))
        
        print(f"Total Remote Interaction Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Failed Tests: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Breakdown by event type
        event_type_stats = {}
        for result in results:
            if 'scenario' in result:
                event_name = result['scenario']['event_name']
                if event_name not in event_type_stats:
                    event_type_stats[event_name] = {'total': 0, 'success': 0}
                event_type_stats[event_name]['total'] += 1
                if result.get('success', False):
                    event_type_stats[event_name]['success'] += 1
        
        print(f"\nBreakdown by Remote Interaction Event Type:")
        for event_type, stats in event_type_stats.items():
            success_rate = (stats['success']/stats['total'])*100 if stats['total'] > 0 else 0
            print(f"  {event_type}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Validation breakdown
        if results:
            validation_stats = {}
            for result in results:
                if 'validation' in result:
                    for check, passed in result['validation'].items():
                        if check != 'overall_pass':
                            if check not in validation_stats:
                                validation_stats[check] = {'total': 0, 'passed': 0}
                            validation_stats[check]['total'] += 1
                            if passed:
                                validation_stats[check]['passed'] += 1
            
            print(f"\nValidation Breakdown:")
            for check, stats in validation_stats.items():
                pass_rate = (stats['passed']/stats['total'])*100 if stats['total'] > 0 else 0
                print(f"  {check}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
        
        # Sample successful remote interaction entries
        successful_results = [r for r in results if r.get('success', False)]
        if successful_results:
            print(f"\nSample Successful Remote Interaction Diary Entries:")
            for i, result in enumerate(successful_results[:3]):
                diary = result['diary_entry']
                scenario = result['scenario']
                print(f"  {i+1}. {scenario['event_name']} - {scenario['friend_nickname']} ({scenario['friend_owner_nickname']})")
                print(f"     Title: {diary['title']}")
                print(f"     Content: {diary['content']}")
                print(f"     Emotions: {', '.join(diary['emotion_tags'])}")
                print(f"     LLM Provider: {diary['llm_provider']}")
        
        print("=" * 60)
    
    def cleanup(self):
        """Clean up test files"""
        print("✓ No cleanup needed - using main configuration")


async def main():
    """Main test function for Remote Toy Interaction Section 3.5"""
    tester = RemoteToyInteractionTester()
    
    try:
        results = await tester.run_remote_interaction_test()
        
        # Save results to file
        with open('remote_toy_interaction_section_3_5_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nDetailed remote interaction results saved to: remote_toy_interaction_section_3_5_results.json")
        
    except Exception as e:
        print(f"Remote interaction test execution failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
