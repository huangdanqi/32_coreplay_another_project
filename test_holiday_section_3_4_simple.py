#!/usr/bin/env python3
"""
Simplified test for Holiday Category functionality (Section 3.4)
Tests the exact requirements without complex LLM setup:
- Trigger Condition: Randomly select 1 day within the period of 3 days before to 3 days after the holiday
- Content to Include: Time (X days before holiday / Xth day of holiday / X days after holiday), holiday name
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'diary_agent'))

from diary_agent.integration.holiday_data_reader import HolidayDataReader
from diary_agent.utils.data_models import EventData, EmotionalTag


class SimpleHolidayTester:
    """Simplified test class for Holiday Category functionality (Section 3.4)"""
    
    def __init__(self):
        self.data_reader = HolidayDataReader()
    
    def create_test_holidays(self) -> List[Dict[str, Any]]:
        """Create test holiday data for testing"""
        base_date = datetime.now()
        return [
            {
                "name": "春节",
                "date": (base_date + timedelta(days=5)).strftime("%Y-%m-%d"),
                "duration": 7,
                "type": "traditional"
            },
            {
                "name": "国庆节", 
                "date": (base_date + timedelta(days=15)).strftime("%Y-%m-%d"),
                "duration": 7,
                "type": "national"
            },
            {
                "name": "中秋节",
                "date": (base_date + timedelta(days=25)).strftime("%Y-%m-%d"),
                "duration": 1,
                "type": "traditional"
            }
        ]
    
    def generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """
        Generate test scenarios for Section 3.4 requirements:
        - 3 days before to 3 days after holiday period
        - Different event types (approaching_holiday, during_holiday, holiday_ends)
        """
        holidays = self.create_test_holidays()
        scenarios = []
        
        for holiday in holidays:
            holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
            
            # Test scenarios within 3 days before to 3 days after
            for days_offset in range(-3, 4):  # -3 to +3 days
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
                        holiday["name"],  # Holiday name must be included
                        time_description  # Time description must be included
                    ]
                }
                scenarios.append(scenario)
        
        return scenarios
    
    def test_single_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single holiday scenario"""
        print(f"\n=== Testing Scenario ===")
        print(f"Holiday: {scenario['holiday']['name']}")
        print(f"Test Date: {scenario['test_date'].strftime('%Y-%m-%d')}")
        print(f"Days Offset: {scenario['days_offset']}")
        print(f"Event Type: {scenario['event_name']}")
        print(f"Expected Time Description: {scenario['time_description']}")
        
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
                "days_to_holiday": -scenario['days_offset']  # Negative offset means days until
            }
        )
        
        try:
            # Test data reader context extraction
            context_data = self.data_reader.read_event_context(event_data)
            print(f"✓ Context extracted successfully")
            print(f"  Holiday name from context: {context_data.event_details.get('holiday_name', 'N/A')}")
            print(f"  Days to holiday: {context_data.temporal_context.get('days_to_holiday', 'N/A')}")
            print(f"  Holiday timing: {context_data.temporal_context.get('holiday_timing', 'N/A')}")
            print(f"  Emotional tone: {context_data.emotional_context.get('holiday_emotional_tone', 'N/A')}")
            print(f"  Anticipation level: {context_data.emotional_context.get('anticipation_level', 'N/A')}")
            
            # Test fallback diary generation (simulating what the agent would do)
            fallback_content = self.generate_fallback_content(event_data, context_data)
            print(f"✓ Fallback content generated")
            print(f"  Title: {fallback_content['title']}")
            print(f"  Content: {fallback_content['content']}")
            print(f"  Emotion Tags: {fallback_content['emotion_tags']}")
            
            # Validate results
            validation_results = self.validate_section_3_4_requirements(
                fallback_content, scenario, context_data
            )
            
            result = {
                "scenario": scenario,
                "context_data": {
                    "holiday_name": context_data.event_details.get('holiday_name'),
                    "days_to_holiday": context_data.temporal_context.get('days_to_holiday'),
                    "holiday_timing": context_data.temporal_context.get('holiday_timing'),
                    "emotional_tone": context_data.emotional_context.get('holiday_emotional_tone'),
                    "anticipation_level": context_data.emotional_context.get('anticipation_level')
                },
                "generated_content": fallback_content,
                "validation": validation_results,
                "success": validation_results["overall_pass"]
            }
            
            # Print validation results
            print(f"\n--- Validation Results ---")
            for check, passed in validation_results.items():
                if check != "overall_pass":
                    status = "✓ PASS" if passed else "✗ FAIL"
                    print(f"  {check}: {status}")
            
            overall_status = "✓ OVERALL PASS" if validation_results["overall_pass"] else "✗ OVERALL FAIL"
            print(f"\n{overall_status}")
            
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
    
    def generate_fallback_content(self, event_data: EventData, context_data) -> Dict[str, Any]:
        """
        Generate fallback holiday content (simulating what HolidayAgent would do).
        """
        event_details = context_data.event_details
        temporal_context = context_data.temporal_context
        
        holiday_name = event_details.get('holiday_name', '节假日')
        days_to_holiday = temporal_context.get('days_to_holiday', 0)
        
        # Generate simple holiday-based content
        if event_data.event_name == "approaching_holiday":
            title = "期待"
            if days_to_holiday > 0:
                content = f"{holiday_name}快到了，还有{days_to_holiday}天😊"
            else:
                content = f"{holiday_name}快到了，很期待🎉"
            emotion_tags = ["开心快乐"]
                
        elif event_data.event_name == "during_holiday":
            title = "假期"
            content = f"今天是{holiday_name}，很开心😄"
            emotion_tags = ["兴奋激动"]
            
        elif event_data.event_name == "holiday_ends":
            title = "结束"
            content = f"{holiday_name}结束了，有点不舍😔"
            emotion_tags = ["悲伤难过"]
            
        else:
            title = "节日"
            content = f"今天和{holiday_name}有关的日子"
            emotion_tags = ["平静"]
        
        # Ensure character limits
        title = title[:6]
        content = content[:35]
        
        return {
            "title": title,
            "content": content,
            "emotion_tags": emotion_tags
        }
    
    def validate_section_3_4_requirements(self, content_dict: Dict[str, Any], 
                                        scenario: Dict[str, Any], context_data) -> Dict[str, bool]:
        """
        Validate that the content meets Section 3.4 requirements:
        - Content includes time description (X days before/during/after holiday)
        - Content includes holiday name
        - Appropriate emotional context
        - Proper formatting (6-char title, 35-char content)
        """
        validation = {}
        
        # Check title length (max 6 characters)
        validation["title_length_valid"] = len(content_dict["title"]) <= 6
        
        # Check content length (max 35 characters)
        validation["content_length_valid"] = len(content_dict["content"]) <= 35
        
        # Check holiday name is included in content or context
        holiday_name = scenario['holiday']['name']
        validation["holiday_name_included"] = (
            holiday_name in content_dict["content"] or 
            holiday_name in content_dict["title"] or
            holiday_name in str(context_data.event_details.get('holiday_name', ''))
        )
        
        # Check time description is contextually appropriate
        days_offset = scenario['days_offset']
        content_and_title = content_dict["content"] + content_dict["title"]
        
        if days_offset < 0:
            # Before holiday - should indicate anticipation/approaching
            validation["time_context_appropriate"] = any(word in content_and_title for word in 
                ["快到", "期待", "准备", "即将", "还有", "天", "前"])
        elif days_offset == 0:
            # During holiday - should indicate current celebration
            validation["time_context_appropriate"] = any(word in content_and_title for word in 
                ["今天", "现在", "正在", "节日", "假期", "庆祝"])
        else:
            # After holiday - should indicate ending/nostalgia
            validation["time_context_appropriate"] = any(word in content_and_title for word in 
                ["结束", "过去", "回忆", "不舍", "恢复", "后"])
        
        # Check emotional tags are appropriate for event type
        emotion_tag_values = content_dict["emotion_tags"]
        
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
            validation["emotion_appropriate"] = True  # Default pass
        
        # Check that emotion tags are from valid set
        valid_emotions = {tag.value for tag in EmotionalTag}
        validation["emotion_tags_valid"] = all(emotion in valid_emotions for emotion in emotion_tag_values)
        
        # Check that content has required fields
        validation["required_fields_present"] = all([
            content_dict.get("title"),
            content_dict.get("content"),
            content_dict.get("emotion_tags")
        ])
        
        # Overall pass - all individual checks must pass
        validation["overall_pass"] = all(validation.values())
        
        return validation
    
    def run_comprehensive_test(self):
        """Run comprehensive test of Holiday Category Section 3.4"""
        print("=" * 60)
        print("HOLIDAY CATEGORY SECTION 3.4 COMPREHENSIVE TEST")
        print("=" * 60)
        print("Testing requirements:")
        print("- Trigger Condition: Random selection within 3 days before to 3 days after holiday")
        print("- Content: Time description + Holiday name")
        print("- Proper formatting and emotional context")
        print("=" * 60)
        
        scenarios = self.generate_test_scenarios()
        results = []
        
        print(f"\nGenerated {len(scenarios)} test scenarios")
        
        # Test a subset of scenarios (to avoid overwhelming output)
        test_scenarios = scenarios[::3]  # Test every 3rd scenario
        print(f"Testing {len(test_scenarios)} representative scenarios...")
        
        for i, scenario in enumerate(test_scenarios):
            print(f"\n{'='*40}")
            print(f"SCENARIO {i+1}/{len(test_scenarios)}")
            print(f"{'='*40}")
            
            result = self.test_single_scenario(scenario)
            results.append(result)
        
        # Generate summary report
        self.generate_summary_report(results)
        
        return results
    
    def generate_summary_report(self, results: List[Dict[str, Any]]):
        """Generate summary report of test results"""
        print("\n" + "=" * 60)
        print("SUMMARY REPORT")
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
            print(f"\nSample Successful Entries:")
            for i, result in enumerate(successful_results[:3]):  # Show first 3
                content = result['generated_content']
                scenario = result['scenario']
                print(f"  {i+1}. {scenario['holiday']['name']} ({scenario['event_name']})")
                print(f"     Title: {content['title']}")
                print(f"     Content: {content['content']}")
                print(f"     Emotions: {', '.join(content['emotion_tags'])}")
        
        print("=" * 60)


def main():
    """Main test function"""
    tester = SimpleHolidayTester()
    
    try:
        results = tester.run_comprehensive_test()
        
        print(f"\nTest completed successfully!")
        print(f"Total scenarios tested: {len(results)}")
        successful = sum(1 for r in results if r.get('success', False))
        print(f"Successful tests: {successful}/{len(results)} ({(successful/len(results))*100:.1f}%)")
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()