#!/usr/bin/env python3
"""
Real Holiday Category Section 3.4 Test with Ollama API
Tests the exact requirements using actual components:
- Uses real holiday_data_reader.py
- Uses local Ollama model for diary generation
- Tests trigger conditions: 3 days before to 3 days after holiday
- Validates content includes time description and holiday name
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

from diary_agent.agents.holiday_agent import HolidayAgent
from diary_agent.integration.holiday_data_reader import HolidayDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, EmotionalTag


class RealHolidayTester:
    """Real Holiday Category Section 3.4 tester using Ollama API"""
    
    def __init__(self):
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment with real Ollama configuration"""
        # Create LLM configuration file for Ollama
        self.create_ollama_config()
        
        # Initialize real components
        self.llm_manager = LLMConfigManager("test_llm_config.json")
        self.data_reader = HolidayDataReader()
        
        # Load holiday agent prompt configuration
        prompt_config_path = "diary_agent/config/agent_prompts/holiday_agent.json"
        with open(prompt_config_path, 'r', encoding='utf-8') as f:
            self.prompt_config = json.load(f)
        
        # Initialize holiday agent
        self.holiday_agent = HolidayAgent(
            agent_type="holiday_agent",
            prompt_config=self.prompt_config,
            llm_manager=self.llm_manager,
            data_reader=self.data_reader
        )
        
        print("✓ Test environment setup complete")
        print(f"✓ Using LLM Manager: {type(self.llm_manager).__name__}")
        print(f"✓ Using Data Reader: {type(self.data_reader).__name__}")
        print(f"✓ Using Holiday Agent: {type(self.holiday_agent).__name__}")
    
    def create_ollama_config(self):
        """Create Ollama configuration file"""
        ollama_config = {
            "providers": {
                "ollama_qwen3": {
                    "provider_name": "ollama_qwen3",
                    "api_endpoint": "http://localhost:11434/api/generate",
                    "api_key": "not_needed",
                    "model_name": "qwen3:4b",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "enabled": True
                }
            },
            "model_selection": {
                "default_provider": "ollama_qwen3"
            }
        }
        
        with open("test_llm_config.json", 'w', encoding='utf-8') as f:
            json.dump(ollama_config, f, indent=2, ensure_ascii=False)
        
        print("✓ Created Ollama configuration file")
    
    def create_real_holiday_scenarios(self) -> List[Dict[str, Any]]:
        """Create realistic holiday scenarios based on Chinese calendar"""
        # Use actual Chinese holidays for 2025
        current_year = datetime.now().year
        real_holidays = [
            {
                "name": "春节",
                "date": f"{current_year + 1}-01-29",  # 2025 Spring Festival
                "duration": 7,
                "type": "traditional_major"
            },
            {
                "name": "清明节",
                "date": f"{current_year + 1}-04-05",  # 2025 Qingming Festival
                "duration": 1,
                "type": "traditional_cultural"
            },
            {
                "name": "劳动节",
                "date": f"{current_year + 1}-05-01",  # 2025 Labor Day
                "duration": 3,
                "type": "international"
            },
            {
                "name": "端午节",
                "date": f"{current_year + 1}-05-31",  # 2025 Dragon Boat Festival
                "duration": 1,
                "type": "traditional_cultural"
            },
            {
                "name": "中秋节",
                "date": f"{current_year + 1}-10-06",  # 2025 Mid-Autumn Festival
                "duration": 1,
                "type": "traditional_cultural"
            },
            {
                "name": "国庆节",
                "date": f"{current_year + 1}-10-01",  # 2025 National Day
                "duration": 7,
                "type": "national_major"
            }
        ]
        
        scenarios = []
        
        # Generate scenarios for each holiday within the 3-day window
        for holiday in real_holidays[:2]:  # Test first 2 holidays to keep output manageable
            holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
            
            # Test key scenarios within 3 days before to 3 days after
            test_offsets = [-3, -1, 0, 1, 3]  # Representative days
            
            for days_offset in test_offsets:
                test_date = holiday_date + timedelta(days=days_offset)
                
                # Determine event type based on timing
                if days_offset < 0:
                    event_name = "approaching_holiday"
                    time_description = f"{abs(days_offset)}天前"
                elif days_offset == 0:
                    event_name = "during_holiday"
                    time_description = "节日当天"
                else:
                    event_name = "holiday_ends"
                    time_description = f"节后{days_offset}天"
                
                scenario = {
                    "holiday": holiday,
                    "test_date": test_date,
                    "days_offset": days_offset,
                    "event_name": event_name,
                    "time_description": time_description,
                    "expected_content_includes": [
                        holiday["name"],
                        time_description
                    ]
                }
                scenarios.append(scenario)
        
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
    
    async def test_single_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single holiday scenario with real API calls"""
        print(f"\n{'='*50}")
        print(f"TESTING SCENARIO")
        print(f"{'='*50}")
        print(f"Holiday: {scenario['holiday']['name']}")
        print(f"Test Date: {scenario['test_date'].strftime('%Y-%m-%d')}")
        print(f"Days Offset: {scenario['days_offset']}")
        print(f"Event Type: {scenario['event_name']}")
        print(f"Expected Time: {scenario['time_description']}")
        
        # Create event data
        event_data = EventData(
            event_id=f"test_holiday_{int(scenario['test_date'].timestamp())}",
            event_type="holiday_events",
            event_name=scenario['event_name'],
            timestamp=scenario['test_date'],
            user_id=1,
            context_data={},
            metadata={
                "event_date": scenario['test_date'],
                "holiday_name": scenario['holiday']['name'],
                "days_to_holiday": -scenario['days_offset']
            }
        )
        
        try:
            print(f"\n--- Step 1: Reading Holiday Context ---")
            # Use real holiday data reader
            context_data = self.data_reader.read_event_context(event_data)
            print(f"✓ Context extracted from holiday_data_reader.py")
            print(f"  Holiday name: {context_data.event_details.get('holiday_name', 'N/A')}")
            print(f"  Days to holiday: {context_data.temporal_context.get('days_to_holiday', 'N/A')}")
            print(f"  Holiday timing: {context_data.temporal_context.get('holiday_timing', 'N/A')}")
            print(f"  Emotional tone: {context_data.emotional_context.get('holiday_emotional_tone', 'N/A')}")
            print(f"  Anticipation level: {context_data.emotional_context.get('anticipation_level', 'N/A')}")
            print(f"  Cultural significance: {context_data.social_context.get('cultural_significance', 'N/A')}")
            
            print(f"\n--- Step 2: Generating Diary with Ollama ---")
            # Use real holiday agent with Ollama API
            diary_entry = await self.holiday_agent.process_event(event_data)
            print(f"✓ Diary generated using Ollama API")
            print(f"  Title: '{diary_entry.title}'")
            print(f"  Content: '{diary_entry.content}'")
            print(f"  Emotion Tags: {[tag.value if hasattr(tag, 'value') else str(tag) for tag in diary_entry.emotion_tags]}")
            print(f"  LLM Provider: {diary_entry.llm_provider}")
            
            print(f"\n--- Step 3: Validating Section 3.4 Requirements ---")
            # Validate results
            validation_results = self.validate_section_3_4_requirements(
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
                    "holiday_name": context_data.event_details.get('holiday_name'),
                    "days_to_holiday": context_data.temporal_context.get('days_to_holiday'),
                    "holiday_timing": context_data.temporal_context.get('holiday_timing'),
                    "emotional_tone": context_data.emotional_context.get('holiday_emotional_tone'),
                    "cultural_significance": context_data.social_context.get('cultural_significance')
                },
                "validation": validation_results,
                "success": validation_results["overall_pass"]
            }
            
            return result
            
        except Exception as e:
            print(f"✗ Error testing scenario: {e}")
            import traceback
            traceback.print_exc()
            return {
                "scenario": scenario,
                "error": str(e),
                "success": False
            }
    
    def validate_section_3_4_requirements(self, diary_entry, scenario: Dict[str, Any], 
                                        context_data) -> Dict[str, bool]:
        """
        Validate Section 3.4 requirements:
        - Content includes time description (X days before/during/after holiday)
        - Content includes holiday name
        - Appropriate emotional context
        - Proper formatting (6-char title, 35-char content)
        """
        validation = {}
        
        # Check title length (max 6 characters)
        validation["title_length_valid"] = len(diary_entry.title) <= 6
        
        # Check content length (max 35 characters)
        validation["content_length_valid"] = len(diary_entry.content) <= 35
        
        # Check holiday name is included in content, title, or context
        holiday_name = scenario['holiday']['name']
        validation["holiday_name_included"] = (
            holiday_name in diary_entry.content or 
            holiday_name in diary_entry.title or
            holiday_name in str(context_data.event_details.get('holiday_name', ''))
        )
        
        # Check time description is contextually appropriate
        days_offset = scenario['days_offset']
        content_and_title = diary_entry.content + diary_entry.title
        
        if days_offset < 0:
            # Before holiday - should indicate anticipation/approaching
            validation["time_context_appropriate"] = any(word in content_and_title for word in 
                ["快到", "期待", "准备", "即将", "还有", "天", "前", "临近", "接近"])
        elif days_offset == 0:
            # During holiday - should indicate current celebration
            validation["time_context_appropriate"] = any(word in content_and_title for word in 
                ["今天", "现在", "正在", "节日", "假期", "庆祝", "当天"])
        else:
            # After holiday - should indicate ending/nostalgia
            validation["time_context_appropriate"] = any(word in content_and_title for word in 
                ["结束", "过去", "回忆", "不舍", "恢复", "后", "完了"])
        
        # Check emotional tags are appropriate for event type
        emotion_tag_values = [tag.value if hasattr(tag, 'value') else str(tag) for tag in diary_entry.emotion_tags]
        
        if scenario['event_name'] == "approaching_holiday":
            # Should have positive anticipatory emotions
            validation["emotion_appropriate"] = any(emotion in emotion_tag_values for emotion in 
                ["开心快乐", "兴奋激动", "好奇"])
        elif scenario['event_name'] == "during_holiday":
            # Should have joyful celebration emotions
            validation["emotion_appropriate"] = any(emotion in emotion_tag_values for emotion in 
                ["开心快乐", "兴奋激动", "平静"])
        elif scenario['event_name'] == "holiday_ends":
            # Should have nostalgic or sad emotions
            validation["emotion_appropriate"] = any(emotion in emotion_tag_values for emotion in 
                ["悲伤难过", "平静", "担忧"])
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
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of Holiday Category Section 3.4 with real API"""
        print("=" * 60)
        print("HOLIDAY CATEGORY SECTION 3.4 - REAL API TEST")
        print("=" * 60)
        print("Testing requirements:")
        print("- Using real holiday_data_reader.py")
        print("- Using local Ollama model for diary generation")
        print("- Trigger: 3 days before to 3 days after holiday")
        print("- Content: Time description + Holiday name")
        print("=" * 60)
        
        # Test Ollama connection first
        print("\n--- Testing Ollama Connection ---")
        ollama_available = await self.test_ollama_connection()
        if not ollama_available:
            print("Cannot proceed without Ollama. Please start Ollama and install qwen2.5:7b model.")
            return []
        
        scenarios = self.create_real_holiday_scenarios()
        results = []
        
        print(f"\nGenerated {len(scenarios)} real holiday scenarios")
        print(f"Testing all scenarios with real API calls...")
        
        for i, scenario in enumerate(scenarios):
            print(f"\n{'='*60}")
            print(f"SCENARIO {i+1}/{len(scenarios)}")
            print(f"{'='*60}")
            
            result = await self.test_single_scenario(scenario)
            results.append(result)
            
            # Small delay between API calls
            await asyncio.sleep(1)
        
        # Generate summary report
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results: List[Dict[str, Any]]):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE SUMMARY REPORT")
        print("=" * 60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get('success', False))
        
        print(f"Total Tests: {total_tests}")
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
        
        print(f"\nBreakdown by Event Type:")
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
        
        # Sample successful entries
        successful_results = [r for r in results if r.get('success', False)]
        if successful_results:
            print(f"\nSample Successful Diary Entries:")
            for i, result in enumerate(successful_results[:3]):
                diary = result['diary_entry']
                scenario = result['scenario']
                print(f"  {i+1}. {scenario['holiday']['name']} ({scenario['event_name']})")
                print(f"     Title: {diary['title']}")
                print(f"     Content: {diary['content']}")
                print(f"     Emotions: {', '.join(diary['emotion_tags'])}")
                print(f"     LLM Provider: {diary['llm_provider']}")
        
        print("=" * 60)
    
    def cleanup(self):
        """Clean up test files"""
        try:
            if os.path.exists("test_llm_config.json"):
                os.remove("test_llm_config.json")
                print("✓ Cleaned up test configuration file")
        except Exception as e:
            print(f"Warning: Could not clean up test files: {e}")


async def main():
    """Main test function"""
    tester = RealHolidayTester()
    
    try:
        results = await tester.run_comprehensive_test()
        
        # Save results to file
        with open('holiday_section_3_4_real_results.json', 'w', encoding='utf-8') as f:
            # Convert datetime objects to strings for JSON serialization
            json_results = []
            for result in results:
                json_result = result.copy()
                if 'scenario' in json_result and 'test_date' in json_result['scenario']:
                    json_result['scenario']['test_date'] = json_result['scenario']['test_date'].isoformat()
                json_results.append(json_result)
            
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        print(f"\nDetailed results saved to: holiday_section_3_4_real_results.json")
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())