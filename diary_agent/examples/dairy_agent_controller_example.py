"""
Example usage of the DairyAgentController.
Demonstrates system initialization, event processing, and monitoring.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from diary_agent.core.dairy_agent_controller import (
    DairyAgentController, create_and_start_system, run_system_with_monitoring
)
from diary_agent.utils.data_models import EventData


async def basic_controller_example():
    """Basic example of using DairyAgentController."""
    print("=== Basic DairyAgentController Example ===")
    
    # Create controller
    controller = DairyAgentController(
        config_dir="diary_agent/config",
        data_dir="diary_agent/data",
        log_level="INFO"
    )
    
    try:
        # Initialize system
        print("Initializing system...")
        if not await controller.initialize_system():
            print("Failed to initialize system")
            return
        
        print("System initialized successfully")
        
        # Start system
        print("Starting system...")
        if not await controller.start_system():
            print("Failed to start system")
            return
        
        print("System started successfully")
        
        # Get system status
        status = controller.get_system_status()
        print(f"System Status: {status['health_status']['system_status']}")
        print(f"Components: {len(status['component_status'])} initialized")
        
        # Process a manual event
        print("\nProcessing manual event...")
        diary_entry = await controller.process_manual_event(
            event_name="favorite_weather",
            user_id=1,
            context_data={
                "weather": "sunny",
                "temperature": 25,
                "city": "Beijing"
            }
        )
        
        if diary_entry:
            print(f"Generated diary entry:")
            print(f"  Title: {diary_entry.title}")
            print(f"  Content: {diary_entry.content}")
            print(f"  Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
        else:
            print("No diary entry generated (quota or conditions not met)")
        
        # Get supported events
        supported_events = controller.get_supported_events()
        print(f"\nSupported events: {len(supported_events)}")
        for event in supported_events[:5]:  # Show first 5
            print(f"  - {event}")
        
        # Wait a bit to see system in action
        print("\nSystem running... (waiting 10 seconds)")
        await asyncio.sleep(10)
        
        # Get updated statistics
        final_status = controller.get_system_status()
        stats = final_status['statistics']
        print(f"\nFinal Statistics:")
        print(f"  Events processed: {stats['events_processed']}")
        print(f"  Diaries generated: {stats['diaries_generated']}")
        print(f"  Errors encountered: {stats['errors_encountered']}")
        
    finally:
        # Stop system
        print("\nStopping system...")
        await controller.stop_system()
        print("System stopped")


async def event_processing_example():
    """Example of processing multiple events."""
    print("\n=== Event Processing Example ===")
    
    controller = DairyAgentController(log_level="DEBUG")
    
    try:
        await controller.initialize_system()
        await controller.start_system()
        
        # Create multiple test events
        events = [
            EventData(
                event_id="weather_1",
                event_type="weather",
                event_name="favorite_weather",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"weather": "sunny", "temperature": 22},
                metadata={"source": "example"}
            ),
            EventData(
                event_id="social_1",
                event_type="friends",
                event_name="made_new_friend",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"friend_name": "Alice", "interaction_type": "positive"},
                metadata={"source": "example"}
            ),
            EventData(
                event_id="holiday_1",
                event_type="holiday",
                event_name="approaching_holiday",
                timestamp=datetime.now(),
                user_id=1,
                context_data={"holiday": "Spring Festival", "days_until": 7},
                metadata={"source": "example"}
            )
        ]
        
        print(f"Processing {len(events)} events...")
        
        # Process events
        results = []
        for event in events:
            print(f"\nProcessing event: {event.event_name}")
            result = await controller.process_event(event)
            results.append(result)
            
            if result:
                print(f"  ✓ Generated: {result.title} - {result.content}")
            else:
                print(f"  ✗ No diary generated")
        
        # Summary
        successful = len([r for r in results if r is not None])
        print(f"\nProcessing Summary:")
        print(f"  Total events: {len(events)}")
        print(f"  Successful generations: {successful}")
        print(f"  Skipped/Failed: {len(events) - successful}")
        
    finally:
        await controller.stop_system()


async def health_monitoring_example():
    """Example of health monitoring and recovery."""
    print("\n=== Health Monitoring Example ===")
    
    controller = DairyAgentController(log_level="INFO")
    
    try:
        await controller.initialize_system()
        await controller.start_system()
        
        print("Performing health checks...")
        
        # Perform multiple health checks
        for i in range(3):
            print(f"\nHealth Check #{i+1}")
            health_status = await controller._perform_health_check()
            
            print(f"  Overall Health: {'✓ Healthy' if health_status['overall_healthy'] else '✗ Unhealthy'}")
            print(f"  Components Checked: {len(health_status['components'])}")
            
            if health_status['issues']:
                print(f"  Issues Found: {len(health_status['issues'])}")
                for issue in health_status['issues']:
                    print(f"    - {issue}")
            else:
                print("  No issues found")
            
            await asyncio.sleep(2)
        
        # Test system restart
        print("\nTesting system restart...")
        restart_success = await controller.restart_system()
        print(f"Restart {'successful' if restart_success else 'failed'}")
        
        # Final health check
        final_health = await controller._perform_health_check()
        print(f"\nFinal health status: {'Healthy' if final_health['overall_healthy'] else 'Unhealthy'}")
        
    finally:
        await controller.stop_system()


async def daily_quota_example():
    """Example of daily quota management."""
    print("\n=== Daily Quota Example ===")
    
    controller = DairyAgentController(log_level="INFO")
    
    try:
        await controller.initialize_system()
        
        # Check initial quota
        today = datetime.now()
        initial_quota = controller.diary_generator.get_daily_quota(today) if controller.diary_generator else None
        print(f"Initial daily quota: {initial_quota.total_quota if initial_quota else 'Not set'}")
        
        # Force daily reset to see quota generation
        print("\nForcing daily reset...")
        await controller.force_daily_reset()
        
        # Check new quota
        new_quota = controller.diary_generator.get_daily_quota(today) if controller.diary_generator else None
        print(f"New daily quota: {new_quota.total_quota if new_quota else 'Not set'}")
        
        # Simulate quota usage
        if controller.event_router:
            routing_stats = controller.event_router.get_routing_statistics()
            quota_info = routing_stats.get('daily_quota', {})
            print(f"Quota usage: {quota_info.get('current_count', 0)}/{quota_info.get('total_quota', 0)}")
        
    finally:
        await controller.stop_system()


async def convenience_functions_example():
    """Example using convenience functions."""
    print("\n=== Convenience Functions Example ===")
    
    try:
        # Create and start system in one call
        print("Creating and starting system...")
        controller = await create_and_start_system(
            config_dir="diary_agent/config",
            data_dir="diary_agent/data",
            log_level="INFO"
        )
        
        print("System created and started successfully")
        
        # Process some events
        diary_entry = await controller.process_manual_event(
            event_name="dislike_weather",
            user_id=1,
            context_data={"weather": "rainy", "mood": "gloomy"}
        )
        
        if diary_entry:
            print(f"Generated diary: {diary_entry.title} - {diary_entry.content}")
        
        # Get diary entries
        entries = await controller.get_diary_entries(user_id=1)
        print(f"Total diary entries for user 1: {len(entries)}")
        
        # Stop system
        await controller.stop_system()
        
    except Exception as e:
        print(f"Error in convenience functions example: {e}")


async def monitoring_with_recovery_example():
    """Example of running system with continuous monitoring."""
    print("\n=== Monitoring with Recovery Example ===")
    
    controller = DairyAgentController(log_level="INFO")
    
    try:
        await controller.initialize_system()
        await controller.start_system()
        
        print("Starting monitoring (will run for 30 seconds)...")
        
        # Create a task for monitoring
        monitor_task = asyncio.create_task(
            run_system_with_monitoring(controller, monitor_interval=10)
        )
        
        # Simulate some activity
        activity_task = asyncio.create_task(simulate_system_activity(controller))
        
        # Run both tasks for a limited time
        try:
            await asyncio.wait_for(
                asyncio.gather(monitor_task, activity_task),
                timeout=30
            )
        except asyncio.TimeoutError:
            print("Monitoring example completed (timeout)")
            monitor_task.cancel()
            activity_task.cancel()
        
    finally:
        await controller.stop_system()


async def simulate_system_activity(controller):
    """Simulate system activity for monitoring example."""
    events = [
        ("favorite_weather", {"weather": "sunny"}),
        ("made_new_friend", {"friend": "Bob"}),
        ("approaching_holiday", {"holiday": "New Year"}),
        ("dislike_weather", {"weather": "stormy"}),
        ("toy_claimed", {"toy": "robot"})
    ]
    
    for i in range(10):  # Generate 10 events
        event_name, context = events[i % len(events)]
        
        try:
            await controller.process_manual_event(
                event_name=event_name,
                user_id=1,
                context_data=context
            )
            print(f"Processed event: {event_name}")
        except Exception as e:
            print(f"Error processing event {event_name}: {e}")
        
        await asyncio.sleep(2)  # Wait 2 seconds between events


async def error_handling_example():
    """Example of error handling and recovery."""
    print("\n=== Error Handling Example ===")
    
    controller = DairyAgentController(log_level="DEBUG")
    
    try:
        # Test initialization with potential errors
        print("Testing initialization...")
        init_success = await controller.initialize_system()
        
        if not init_success:
            print("Initialization failed - testing recovery...")
            # In real scenario, you might retry or fix configuration
            return
        
        await controller.start_system()
        
        # Test processing invalid event
        print("\nTesting invalid event processing...")
        invalid_event = EventData(
            event_id="invalid",
            event_type="unknown",
            event_name="invalid_event",
            timestamp=datetime.now(),
            user_id=999,
            context_data={},
            metadata={}
        )
        
        result = await controller.process_event(invalid_event)
        print(f"Invalid event result: {result}")
        
        # Test emergency shutdown
        print("\nTesting emergency shutdown...")
        await controller.emergency_shutdown()
        print("Emergency shutdown completed")
        
    except Exception as e:
        print(f"Error in error handling example: {e}")


async def main():
    """Run all examples."""
    print("DairyAgentController Examples")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Run examples
        await basic_controller_example()
        await event_processing_example()
        await health_monitoring_example()
        await daily_quota_example()
        await convenience_functions_example()
        await monitoring_with_recovery_example()
        await error_handling_example()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())