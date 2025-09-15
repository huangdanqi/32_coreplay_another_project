#!/usr/bin/env python3
"""
Test script for Current Affairs Hot Search functionality (Section 3.3)
Tests the trending agent's ability to handle major catastrophic/beneficial events
and generate diary entries with event names and event tags.

Trigger Condition: After hitting (matching) major catastrophic/beneficial events
Content to Include: Event name, event tags (major catastrophic, major beneficial)
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the diary_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'diary_agent'))

from diary_agent.agents.trending_agent import TrendingAgent
from diary_agent.integration.trending_data_reader import TrendingDataReader
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag


class CurrentAffairsHotSearchTester:
    """Test class for Current Affairs Hot Search functionality."""
    
    def __init__(self):
        self.trending_data_reader = TrendingDataReader()
        self.llm_config_manager = None
        self.trending_agent = None
        self.test_results = []
    
    async def setup(self):
        """Setup test environment."""
        print("=== Setting up Current Affairs Hot Search Test ===")
        
        # Load LLM configuration
        try:
            # Pass the path string, not the loaded config dict
            self.llm_config_manager = LLMConfigManager('config/llm_configuration.json')
        except Exception as e:
            print(f"Warning: Could not load LLM config: {e}")
            self.llm_config_manager = None
        
        # Load trending agent prompt configuration
        try:
            with open('diary_agent/config/agent_prompts/trending_agent.json', 'r', encoding='utf-8') as f:
                prompt_config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load trending agent prompt: {e}")
            prompt_config = self._get_default_prompt_config()
        
        # Initialize trending agent
        self.trending_agent = TrendingAgent(
            agent_type="trending_agent",
            prompt_config=prompt_config,
            llm_manager=self.llm_config_manager,
            data_reader=self.trending_data_reader
        )
        
        print("✓ Test environment setup complete")
    
    def _get_default_prompt_config(self) -> Dict[str, Any]:
        """Get default prompt configuration for testing."""
        return {
            "agent_type": "trending_agent",
            "system_prompt": "你是一个专门写关于热门话题和社会事件日记的助手。",
            "user_prompt_template": "请为以下事件写一篇日记：{event_name}",
            "output_format": {"title": "string", "content": "string", "emotion_tags": "list"},
            "validation_rules": {"title_max_length": 6, "content_max_length": 35}
        }
    
    def create_test_event_data(self, event_name: str, event_type: str = "trending_events", 
                              user_id: int = 1, metadata: Dict[str, Any] = None) -> EventData:
        """Create test event data for current affairs hot search."""
        if metadata is None:
            metadata = {}
        
        return EventData(
            event_id=f"test_{event_name}_{int(datetime.now().timestamp())}",
            event_type=event_type,
            event_name=event_name,
            timestamp=datetime.now(),
            user_id=user_id,
            context_data={},
            metadata=metadata
        )
    
    async def test_major_catastrophic_events(self):
        """Test major catastrophic events detection and diary generation."""
        print("\n=== Testing Major Catastrophic Events ===")
        
        # Test cases for major catastrophic events
        catastrophic_test_cases = [
            {
                "event_name": "disaster",
                "description": "Major disaster event",
                "expected_tags": ["major catastrophic"],
                "sample_trending_words": ["地震", "灾难", "死亡", "受伤", "紧急救援"],
                "expected_emotions": [EmotionalTag.WORRIED.value, EmotionalTag.SAD_UPSET.value, EmotionalTag.ANGRY_FURIOUS.value]
            },
            {
                "event_name": "disaster", 
                "description": "Natural disaster with high impact",
                "expected_tags": ["major catastrophic"],
                "sample_trending_words": ["洪水", "台风", "疫情", "爆发", "通报"],
                "expected_emotions": [EmotionalTag.WORRIED.value, EmotionalTag.ANXIOUS_MELANCHOLY.value]
            },
            {
                "event_name": "disaster",
                "description": "Security incident",
                "expected_tags": ["major catastrophic"],
                "sample_trending_words": ["恐袭", "暴力", "枪击", "爆炸", "袭击"],
                "expected_emotions": [EmotionalTag.ANGRY_FURIOUS.value, EmotionalTag.SURPRISED_SHOCKED.value]
            }
        ]
        
        for i, test_case in enumerate(catastrophic_test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['description']} ---")
            
            # Create event data with test trending words that will actually trigger disaster classification
            # We'll create a temporary test file with disaster keywords
            test_douyin_data = {
                "timestamp": "2025-09-02T22:43:00.000000",
                "total_words": len(test_case["sample_trending_words"]),
                "words": [
                    {
                        "word": word,
                        "hot_value": 10000000 - j * 100000,
                        "position": j + 1,
                        "view_count": 50000000 - j * 1000000
                    }
                    for j, word in enumerate(test_case["sample_trending_words"])
                ]
            }
            
            # Create temporary test file
            test_file_path = f"test_disaster_douyin_{i}.json"
            with open(test_file_path, 'w', encoding='utf-8') as f:
                json.dump(test_douyin_data, f, ensure_ascii=False, indent=2)
            
            metadata = {
                "douyin_file_path": test_file_path,
                "page_size": 50,
                "test_trending_words": test_case["sample_trending_words"]
            }
            
            event_data = self.create_test_event_data(
                event_name=test_case["event_name"],
                metadata=metadata
            )
            
            try:
                # Test context reading
                print("Reading event context...")
                context_data = self.trending_data_reader.read_event_context(event_data)
                
                # Verify context contains expected information
                self._verify_catastrophic_context(context_data, test_case)
                
                # Test diary generation (if LLM is available)
                if self.llm_config_manager:
                    print("Generating diary entry...")
                    diary_entry = await self.trending_agent.process_event(event_data)
                    self._verify_catastrophic_diary_entry(diary_entry, test_case)
                else:
                    print("Skipping diary generation (no LLM available)")
                    # Test fallback content generation
                    fallback_content = self.trending_agent._generate_trending_fallback_content(
                        event_data, context_data
                    )
                    self._verify_catastrophic_fallback_content(fallback_content, test_case)
                
                self.test_results.append({
                    "test_type": "catastrophic",
                    "test_case": test_case["description"],
                    "status": "PASSED",
                    "event_name": test_case["event_name"],
                    "expected_tags": test_case["expected_tags"]
                })
                
                print(f"✓ Test case {i} PASSED")
                
            except Exception as e:
                print(f"✗ Test case {i} FAILED: {e}")
                self.test_results.append({
                    "test_type": "catastrophic",
                    "test_case": test_case["description"],
                    "status": "FAILED",
                    "error": str(e)
                })
            finally:
                # Clean up temporary test file
                if os.path.exists(test_file_path):
                    os.remove(test_file_path)
    
    async def test_major_beneficial_events(self):
        """Test major beneficial events detection and diary generation."""
        print("\n=== Testing Major Beneficial Events ===")
        
        # Test cases for major beneficial events
        beneficial_test_cases = [
            {
                "event_name": "celebration",
                "description": "Major celebration event",
                "expected_tags": ["major beneficial"],
                "sample_trending_words": ["胜利", "冠军", "颁奖", "庆典", "节日"],
                "expected_emotions": [EmotionalTag.HAPPY_JOYFUL.value, EmotionalTag.EXCITED_THRILLED.value]
            },
            {
                "event_name": "celebration",
                "description": "Cultural celebration",
                "expected_tags": ["major beneficial"],
                "sample_trending_words": ["演唱会", "灯光秀", "嘉年华", "典礼", "开幕"],
                "expected_emotions": [EmotionalTag.EXCITED_THRILLED.value, EmotionalTag.CURIOUS.value]
            },
            {
                "event_name": "celebration",
                "description": "Achievement celebration",
                "expected_tags": ["major beneficial"],
                "sample_trending_words": ["官宣", "挑战", "传奇", "加油", "口碑"],
                "expected_emotions": [EmotionalTag.HAPPY_JOYFUL.value, EmotionalTag.EXCITED_THRILLED.value]
            }
        ]
        
        for i, test_case in enumerate(beneficial_test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['description']} ---")
            
            # Create event data with trending words metadata
            metadata = {
                "douyin_file_path": "hewan_emotion_cursor_python/douyin_words_20250826_212805.json",
                "page_size": 50,
                "test_trending_words": test_case["sample_trending_words"]
            }
            
            event_data = self.create_test_event_data(
                event_name=test_case["event_name"],
                metadata=metadata
            )
            
            try:
                # Test context reading
                print("Reading event context...")
                context_data = self.trending_data_reader.read_event_context(event_data)
                
                # Verify context contains expected information
                self._verify_beneficial_context(context_data, test_case)
                
                # Test diary generation (if LLM is available)
                if self.llm_config_manager:
                    print("Generating diary entry...")
                    diary_entry = await self.trending_agent.process_event(event_data)
                    self._verify_beneficial_diary_entry(diary_entry, test_case)
                else:
                    print("Skipping diary generation (no LLM available)")
                    # Test fallback content generation
                    fallback_content = self.trending_agent._generate_trending_fallback_content(
                        event_data, context_data
                    )
                    self._verify_beneficial_fallback_content(fallback_content, test_case)
                
                self.test_results.append({
                    "test_type": "beneficial",
                    "test_case": test_case["description"],
                    "status": "PASSED",
                    "event_name": test_case["event_name"],
                    "expected_tags": test_case["expected_tags"]
                })
                
                print(f"✓ Test case {i} PASSED")
                
            except Exception as e:
                print(f"✗ Test case {i} FAILED: {e}")
                self.test_results.append({
                    "test_type": "beneficial",
                    "test_case": test_case["description"],
                    "status": "FAILED",
                    "error": str(e)
                })
    
    def _verify_catastrophic_context(self, context_data, test_case):
        """Verify context data for catastrophic events."""
        print("Verifying catastrophic event context...")
        
        # Check social context
        social_context = context_data.social_context
        assert social_context.get("social_sentiment") == "negative", f"Expected negative social sentiment, got: {social_context.get('social_sentiment')}"
        
        # The event classification might be based on actual file data, not test data
        # So we check if it's either disaster or the event name itself
        event_classification = social_context.get("event_classification")
        assert event_classification in ["disaster", test_case["event_name"]], f"Expected disaster or {test_case['event_name']} classification, got: {event_classification}"
        
        # Check emotional context
        emotional_context = context_data.emotional_context
        emotional_impact = emotional_context.get("event_emotional_impact", "")
        assert "negative" in emotional_impact, f"Expected negative emotional impact, got: {emotional_impact}"
        
        print("✓ Catastrophic context verification passed")
    
    def _verify_beneficial_context(self, context_data, test_case):
        """Verify context data for beneficial events."""
        print("Verifying beneficial event context...")
        
        # Check social context
        social_context = context_data.social_context
        assert social_context.get("social_sentiment") == "positive", "Expected positive social sentiment"
        assert social_context.get("event_classification") == "celebration", "Expected celebration classification"
        
        # Check emotional context
        emotional_context = context_data.emotional_context
        assert "positive" in emotional_context.get("event_emotional_impact", ""), "Expected positive emotional impact"
        
        print("✓ Beneficial context verification passed")
    
    def _verify_catastrophic_diary_entry(self, diary_entry: DiaryEntry, test_case):
        """Verify diary entry for catastrophic events."""
        print("Verifying catastrophic diary entry...")
        
        # Check basic format
        assert len(diary_entry.title) <= 6, f"Title too long: {diary_entry.title}"
        assert len(diary_entry.content) <= 35, f"Content too long: {diary_entry.content}"
        assert diary_entry.event_name == test_case["event_name"], "Event name mismatch"
        
        # Check emotional tags are appropriate for catastrophic events
        emotion_values = [tag.value for tag in diary_entry.emotion_tags]
        catastrophic_emotions = [
            EmotionalTag.WORRIED.value, EmotionalTag.SAD_UPSET.value, 
            EmotionalTag.ANGRY_FURIOUS.value, EmotionalTag.ANXIOUS_MELANCHOLY.value,
            EmotionalTag.SURPRISED_SHOCKED.value
        ]
        
        assert any(emotion in catastrophic_emotions for emotion in emotion_values), \
            f"Expected catastrophic emotions, got: {emotion_values}"
        
        print(f"✓ Catastrophic diary entry verified: '{diary_entry.title}' - '{diary_entry.content}'")
    
    def _verify_beneficial_diary_entry(self, diary_entry: DiaryEntry, test_case):
        """Verify diary entry for beneficial events."""
        print("Verifying beneficial diary entry...")
        
        # Check basic format
        assert len(diary_entry.title) <= 6, f"Title too long: {diary_entry.title}"
        assert len(diary_entry.content) <= 35, f"Content too long: {diary_entry.content}"
        assert diary_entry.event_name == test_case["event_name"], "Event name mismatch"
        
        # Check emotional tags are appropriate for beneficial events
        emotion_values = [tag.value for tag in diary_entry.emotion_tags]
        beneficial_emotions = [
            EmotionalTag.HAPPY_JOYFUL.value, EmotionalTag.EXCITED_THRILLED.value,
            EmotionalTag.CURIOUS.value, EmotionalTag.CALM.value
        ]
        
        assert any(emotion in beneficial_emotions for emotion in emotion_values), \
            f"Expected beneficial emotions, got: {emotion_values}"
        
        print(f"✓ Beneficial diary entry verified: '{diary_entry.title}' - '{diary_entry.content}'")
    
    def _verify_catastrophic_fallback_content(self, fallback_content: Dict[str, Any], test_case):
        """Verify fallback content for catastrophic events."""
        print("Verifying catastrophic fallback content...")
        
        assert len(fallback_content["title"]) <= 6, "Fallback title too long"
        assert len(fallback_content["content"]) <= 35, "Fallback content too long"
        
        # Check emotional appropriateness
        catastrophic_emotions = [
            EmotionalTag.WORRIED.value, EmotionalTag.SAD_UPSET.value, 
            EmotionalTag.ANGRY_FURIOUS.value
        ]
        
        assert any(emotion in catastrophic_emotions for emotion in fallback_content["emotion_tags"]), \
            f"Expected catastrophic emotions in fallback, got: {fallback_content['emotion_tags']}"
        
        print(f"✓ Catastrophic fallback content verified: '{fallback_content['title']}' - '{fallback_content['content']}'")
    
    def _verify_beneficial_fallback_content(self, fallback_content: Dict[str, Any], test_case):
        """Verify fallback content for beneficial events."""
        print("Verifying beneficial fallback content...")
        
        assert len(fallback_content["title"]) <= 6, "Fallback title too long"
        assert len(fallback_content["content"]) <= 35, "Fallback content too long"
        
        # Check emotional appropriateness
        beneficial_emotions = [
            EmotionalTag.HAPPY_JOYFUL.value, EmotionalTag.EXCITED_THRILLED.value,
            EmotionalTag.CURIOUS.value
        ]
        
        assert any(emotion in beneficial_emotions for emotion in fallback_content["emotion_tags"]), \
            f"Expected beneficial emotions in fallback, got: {fallback_content['emotion_tags']}"
        
        print(f"✓ Beneficial fallback content verified: '{fallback_content['title']}' - '{fallback_content['content']}'")
    
    async def test_trigger_conditions(self):
        """Test trigger conditions for current affairs hot search."""
        print("\n=== Testing Trigger Conditions ===")
        
        # Test that events are properly triggered when matching major events
        test_cases = [
            {
                "trending_words": ["地震", "死亡", "灾难"],
                "expected_classification": "disaster",
                "should_trigger": True
            },
            {
                "trending_words": ["演唱会", "庆典", "胜利"],
                "expected_classification": "celebration", 
                "should_trigger": True
            },
            {
                "trending_words": ["天气", "吃饭", "睡觉"],
                "expected_classification": None,
                "should_trigger": False
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Trigger Test {i}: {test_case['trending_words']} ---")
            
            # Test classification
            from hewan_emotion_cursor_python.douyin_news import classify_douyin_news
            classification = classify_douyin_news(test_case["trending_words"])
            
            print(f"Classification result: {classification}")
            print(f"Expected: {test_case['expected_classification']}")
            
            if test_case["should_trigger"]:
                assert classification == test_case["expected_classification"], \
                    f"Expected {test_case['expected_classification']}, got {classification}"
                print("✓ Trigger condition met as expected")
            else:
                assert classification is None, f"Expected no trigger, but got {classification}"
                print("✓ No trigger as expected")
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*60)
        print("CURRENT AFFAIRS HOT SEARCH TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASSED"])
        failed_tests = total_tests - passed_tests
        
        print(f"\nTest Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "  Success Rate: N/A")
        
        # Group results by test type
        catastrophic_tests = [r for r in self.test_results if r.get("test_type") == "catastrophic"]
        beneficial_tests = [r for r in self.test_results if r.get("test_type") == "beneficial"]
        
        if catastrophic_tests:
            print(f"\nCatastrophic Events Tests:")
            for test in catastrophic_tests:
                status_symbol = "✓" if test["status"] == "PASSED" else "✗"
                print(f"  {status_symbol} {test['test_case']}")
                if test["status"] == "FAILED":
                    print(f"    Error: {test.get('error', 'Unknown error')}")
        
        if beneficial_tests:
            print(f"\nBeneficial Events Tests:")
            for test in beneficial_tests:
                status_symbol = "✓" if test["status"] == "PASSED" else "✗"
                print(f"  {status_symbol} {test['test_case']}")
                if test["status"] == "FAILED":
                    print(f"    Error: {test.get('error', 'Unknown error')}")
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save detailed report to file
        report_file = f"current_affairs_hot_search_test_report_{int(datetime.now().timestamp())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
                },
                "test_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")


async def main():
    """Main test execution function."""
    print("Current Affairs Hot Search Test Suite")
    print("=====================================")
    print("Testing Section 3.3: Current Affairs Hot Search")
    print("- Trigger Condition: After hitting (matching) major catastrophic/beneficial events")
    print("- Content to Include: Event name, event tags (major catastrophic, major beneficial)")
    
    tester = CurrentAffairsHotSearchTester()
    
    try:
        # Setup test environment
        await tester.setup()
        
        # Run all test suites
        await tester.test_major_catastrophic_events()
        await tester.test_major_beneficial_events()
        await tester.test_trigger_conditions()
        
        # Generate final report
        tester.generate_test_report()
        
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())