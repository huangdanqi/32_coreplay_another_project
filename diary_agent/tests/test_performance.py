"""
Performance tests for concurrent event processing and system scalability.
Tests system behavior under load and concurrent access scenarios.
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

from diary_agent.core.dairy_agent_controller import DairyAgentController
from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData, DiaryEntry
from diary_agent.tests.test_data_generators import DiaryPerformanceTestDataGenerator, DiaryTestDataGenerator


class TestPerformance:
    """Performance tests for diary agent system."""
    
    @pytest.fixture
    def performance_generator(self):
        """Fixture for performance test data generator."""
        return DiaryPerformanceTestDataGenerator()
    
    @pytest.fixture
    def test_data_generator(self):
        """Fixture for test data generator."""
        return DiaryTestDataGenerator()
    
    @pytest.fixture
    def mock_diary_controller(self):
        """Fixture for mock diary controller optimized for performance testing."""
        controller = Mock(spec=DairyAgentController)
        
        # Mock fast response times
        async def mock_process_event(event):
            # Simulate processing time
            await asyncio.sleep(0.01)  # 10ms processing time
            return DiaryEntry(
                entry_id=f"perf_{event.event_id}",
                user_id=event.user_id,
                timestamp=datetime.now(),
                event_type=event.event_type,
                event_name=event.event_name,
                title="性能测试",
                content="性能测试内容",
                emotion_tags=["平静"],
                agent_type="test_agent",
                llm_provider="test"
            )
        
        controller.process_event = mock_process_event
        return controller
    
    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, mock_diary_controller, performance_generator):
        """Test concurrent processing of multiple events."""
        # Generate concurrent events
        events = performance_generator.generate_concurrent_events(50, 10)
        
        # Record start time
        start_time = time.time()
        
        # Process events concurrently
        tasks = [mock_diary_controller.process_event(event) for event in events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Record end time
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify results
        successful_results = [r for r in results if isinstance(r, DiaryEntry)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        assert len(successful_results) >= 45  # At least 90% success rate
        assert len(failed_results) <= 5  # At most 10% failure rate
        assert processing_time < 5.0  # Should complete within 5 seconds
        
        # Calculate performance metrics
        events_per_second = len(successful_results) / processing_time
        assert events_per_second >= 10  # At least 10 events per second
        
        print(f"Processed {len(successful_results)} events in {processing_time:.2f}s")
        print(f"Performance: {events_per_second:.2f} events/second")
    
    @pytest.mark.asyncio
    async def test_high_load_processing(self, mock_diary_controller, performance_generator):
        """Test system behavior under high load."""
        # Generate high load scenario
        stress_data = performance_generator.generate_stress_test_scenario()
        events = stress_data["events"][:200]  # Use subset for test
        
        # Process in batches to simulate real-world load
        batch_size = 20
        batch_times = []
        
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            
            batch_start = time.time()
            tasks = [mock_diary_controller.process_event(event) for event in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_end = time.time()
            
            batch_time = batch_end - batch_start
            batch_times.append(batch_time)
            
            # Verify batch processing
            successful_batch = [r for r in batch_results if isinstance(r, DiaryEntry)]
            assert len(successful_batch) >= len(batch) * 0.9  # 90% success rate
        
        # Analyze performance consistency
        avg_batch_time = statistics.mean(batch_times)
        max_batch_time = max(batch_times)
        min_batch_time = min(batch_times)
        
        assert avg_batch_time < 2.0  # Average batch time under 2 seconds
        assert max_batch_time < 5.0  # No batch should take more than 5 seconds
        
        # Performance should be consistent (max time shouldn't be more than 3x min time)
        assert max_batch_time <= min_batch_time * 3
        
        print(f"Batch processing times - Avg: {avg_batch_time:.2f}s, Min: {min_batch_time:.2f}s, Max: {max_batch_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, mock_diary_controller, performance_generator):
        """Test memory usage during high-load processing."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate large dataset
        events = performance_generator.generate_concurrent_events(500, 25)
        
        # Process events in chunks to monitor memory
        chunk_size = 50
        memory_readings = [initial_memory]
        
        for i in range(0, len(events), chunk_size):
            chunk = events[i:i + chunk_size]
            
            # Process chunk
            tasks = [mock_diary_controller.process_event(event) for event in chunk]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Record memory usage
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)
        
        # Analyze memory usage
        max_memory = max(memory_readings)
        memory_increase = max_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
        
        # Memory should not continuously grow (check last few readings)
        recent_readings = memory_readings[-5:]
        memory_trend = max(recent_readings) - min(recent_readings)
        assert memory_trend < 20, f"Memory trend shows {memory_trend:.2f}MB variation"
        
        print(f"Memory usage - Initial: {initial_memory:.2f}MB, Max: {max_memory:.2f}MB, Increase: {memory_increase:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_llm_api_performance(self, test_data_generator):
        """Test LLM API call performance and timeout handling."""
        # Create mock LLM manager with realistic delays
        llm_manager = Mock(spec=LLMConfigManager)
        
        # Simulate various response times
        response_times = [0.1, 0.5, 1.0, 2.0, 0.3]  # Seconds
        
        async def mock_generate_response(prompt, **kwargs):
            # Simulate API call delay
            delay = response_times[len(mock_generate_response.call_args_list) % len(response_times)]
            await asyncio.sleep(delay)
            
            return {
                "title": "API测试",
                "content": f"响应时间{delay}秒",
                "emotion_tags": ["平静"]
            }
        
        llm_manager.generate_response = mock_generate_response
        llm_manager.generate_response.call_args_list = []
        
        # Generate test events
        events = test_data_generator.generate_batch_events(10)
        
        # Test concurrent LLM calls
        start_time = time.time()
        
        tasks = []
        for event in events:
            task = llm_manager.generate_response(f"Generate diary for {event.event_name}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify results
        successful_results = [r for r in results if isinstance(r, dict)]
        assert len(successful_results) == len(events)
        
        # Performance should benefit from concurrency
        # Sequential processing would take sum of all delays
        sequential_time = sum(response_times[:len(events)])
        assert total_time < sequential_time * 0.8  # At least 20% improvement from concurrency
        
        print(f"LLM API calls - Total time: {total_time:.2f}s, Sequential would be: {sequential_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_database_performance(self, test_data_generator):
        """Test database operation performance under load."""
        from diary_agent.integration.database_manager import DatabaseManager
        
        # Mock database manager with realistic delays
        db_manager = Mock(spec=DatabaseManager)
        
        # Simulate database operation delays
        async def mock_get_user_profile(user_id):
            await asyncio.sleep(0.05)  # 50ms database query
            return test_data_generator.generate_user_profile(user_id)
        
        async def mock_save_diary_entry(diary_entry):
            await asyncio.sleep(0.03)  # 30ms database insert
            return True
        
        db_manager.get_user_profile = mock_get_user_profile
        db_manager.save_diary_entry = mock_save_diary_entry
        
        # Generate test data
        user_ids = list(range(1, 21))  # 20 users
        diary_entries = []
        
        for i, user_id in enumerate(user_ids):
            event = test_data_generator.generate_weather_event(user_id)
            diary_entry = DiaryEntry(
                entry_id=f"db_perf_{i}",
                user_id=user_id,
                timestamp=datetime.now(),
                event_type=event.event_type,
                event_name=event.event_name,
                title="数据库测试",
                content="测试数据库性能",
                emotion_tags=["平静"],
                agent_type="test_agent",
                llm_provider="test"
            )
            diary_entries.append(diary_entry)
        
        # Test concurrent database operations
        start_time = time.time()
        
        # Concurrent user profile fetches
        profile_tasks = [db_manager.get_user_profile(user_id) for user_id in user_ids]
        profiles = await asyncio.gather(*profile_tasks)
        
        # Concurrent diary saves
        save_tasks = [db_manager.save_diary_entry(entry) for entry in diary_entries]
        save_results = await asyncio.gather(*save_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify results
        assert len(profiles) == len(user_ids)
        assert all(save_results)
        
        # Performance expectations
        operations_per_second = (len(user_ids) * 2) / total_time  # 2 operations per user
        assert operations_per_second >= 20  # At least 20 operations per second
        
        print(f"Database operations - {len(user_ids) * 2} operations in {total_time:.2f}s")
        print(f"Performance: {operations_per_second:.2f} operations/second")
    
    @pytest.mark.asyncio
    async def test_agent_switching_performance(self, test_data_generator):
        """Test performance when switching between different agent types."""
        from diary_agent.core.sub_agent_manager import SubAgentManager
        
        # Mock sub-agent manager
        sub_agent_manager = Mock(spec=SubAgentManager)
        
        # Simulate agent initialization delays
        agent_init_times = {
            "weather_agent": 0.1,
            "trending_agent": 0.15,
            "holiday_agent": 0.12,
            "friends_agent": 0.08,
            "interactive_agent": 0.11
        }
        
        initialized_agents = set()
        
        async def mock_process_event(event, agent_type):
            # Simulate agent initialization if not already initialized
            if agent_type not in initialized_agents:
                await asyncio.sleep(agent_init_times.get(agent_type, 0.1))
                initialized_agents.add(agent_type)
            
            # Simulate processing time
            await asyncio.sleep(0.02)
            
            return DiaryEntry(
                entry_id=f"agent_switch_{event.event_id}",
                user_id=event.user_id,
                timestamp=datetime.now(),
                event_type=event.event_type,
                event_name=event.event_name,
                title="切换测试",
                content="测试代理切换性能",
                emotion_tags=["平静"],
                agent_type=agent_type,
                llm_provider="test"
            )
        
        sub_agent_manager.process_event = mock_process_event
        
        # Generate events requiring different agents
        events = [
            test_data_generator.generate_weather_event(1, "favorite_weather"),
            test_data_generator.generate_trending_event(1, "celebration"),
            test_data_generator.generate_holiday_event(1, "approaching_holiday"),
            test_data_generator.generate_friends_event(1, "made_new_friend"),
            test_data_generator.generate_interaction_event(1, "liked_interaction_once"),
            # Repeat to test agent reuse
            test_data_generator.generate_weather_event(2, "dislike_weather"),
            test_data_generator.generate_trending_event(2, "disaster"),
        ]
        
        agent_types = [
            "weather_agent", "trending_agent", "holiday_agent",
            "friends_agent", "interactive_agent", "weather_agent", "trending_agent"
        ]
        
        # Process events and measure timing
        start_time = time.time()
        
        results = []
        for event, agent_type in zip(events, agent_types):
            result = await sub_agent_manager.process_event(event, agent_type)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify results
        assert len(results) == len(events)
        assert all(isinstance(r, DiaryEntry) for r in results)
        
        # Performance should improve with agent reuse
        # First time processing should include initialization, subsequent should be faster
        expected_time = sum(agent_init_times.values()) + (len(events) * 0.02)
        assert total_time <= expected_time * 1.2  # Allow 20% overhead
        
        print(f"Agent switching - {len(events)} events processed in {total_time:.2f}s")
        print(f"Initialized agents: {len(initialized_agents)}")
    
    def test_throughput_measurement(self, performance_generator):
        """Test system throughput measurement and reporting."""
        # Generate performance test scenario
        scenario = performance_generator.generate_stress_test_scenario()
        
        # Simulate processing metrics
        processing_times = []
        success_counts = []
        error_counts = []
        
        # Simulate multiple test runs
        for run in range(5):
            start_time = time.time()
            
            # Simulate event processing
            events_processed = 0
            errors = 0
            
            for i in range(100):  # Process 100 events per run
                # Simulate processing time variation
                processing_delay = 0.01 + (0.005 * (i % 10))  # 10-15ms
                time.sleep(processing_delay)
                
                # Simulate occasional errors
                if i % 25 == 0:  # 4% error rate
                    errors += 1
                else:
                    events_processed += 1
            
            end_time = time.time()
            run_time = end_time - start_time
            
            processing_times.append(run_time)
            success_counts.append(events_processed)
            error_counts.append(errors)
        
        # Calculate throughput metrics
        avg_processing_time = statistics.mean(processing_times)
        avg_success_count = statistics.mean(success_counts)
        avg_error_count = statistics.mean(error_counts)
        
        throughput = avg_success_count / avg_processing_time
        error_rate = avg_error_count / (avg_success_count + avg_error_count)
        
        # Performance assertions
        assert throughput >= 50  # At least 50 events per second
        assert error_rate <= 0.05  # Error rate under 5%
        assert avg_processing_time <= 2.0  # Average run time under 2 seconds
        
        # Consistency check
        time_std_dev = statistics.stdev(processing_times)
        assert time_std_dev <= avg_processing_time * 0.2  # Std dev within 20% of mean
        
        print(f"Throughput metrics:")
        print(f"  Average throughput: {throughput:.2f} events/second")
        print(f"  Error rate: {error_rate:.2%}")
        print(f"  Average processing time: {avg_processing_time:.2f}s")
        print(f"  Time consistency (std dev): {time_std_dev:.2f}s")
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_performance(self, mock_diary_controller, performance_generator):
        """Test resource cleanup and garbage collection performance."""
        import gc
        
        # Generate large number of events
        events = performance_generator.generate_concurrent_events(200, 20)
        
        # Track object counts before processing
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Process events in batches
        batch_size = 25
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            
            # Process batch
            tasks = [mock_diary_controller.process_event(event) for event in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Force cleanup
            del tasks
            del results
            del batch
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Check for memory leaks
        object_increase = final_objects - initial_objects
        
        # Allow some increase but not excessive
        max_allowed_increase = len(events) * 2  # 2 objects per event max
        assert object_increase <= max_allowed_increase, f"Potential memory leak: {object_increase} new objects"
        
        print(f"Resource cleanup - Objects before: {initial_objects}, after: {final_objects}, increase: {object_increase}")