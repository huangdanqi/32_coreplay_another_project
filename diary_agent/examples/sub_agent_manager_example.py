"""
Example usage of SubAgentManager for managing diary generation sub-agents.
Demonstrates initialization, event processing, health monitoring, and failure handling.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from diary_agent.core.sub_agent_manager import SubAgentManager
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.utils.data_models import EventData


async def main():
    """Demonstrate SubAgentManager usage."""
    
    print("=== SubAgentManager Example ===\n")
    
    # 1. Initialize LLM Manager
    print("1. Initializing LLM Manager...")
    try:
        llm_manager = LLMConfigManager("config/llm_configuration.json")
        print(f"   ✓ LLM Manager initialized with providers: {list(llm_manager.providers.keys())}")
    except Exception as e:
        print(f"   ✗ Failed to initialize LLM Manager: {e}")
        return
    
    # 2. Initialize SubAgentManager
    print("\n2. Initializing SubAgentManager...")
    try:
        manager = SubAgentManager(
            llm_manager=llm_manager,
            config_dir="diary_agent/config",
            max_retry_attempts=3,
            retry_delay=1.0
        )
        print("   ✓ SubAgentManager initialized")
        print(f"   ✓ Data readers initialized: {len(manager.data_readers)}")
    except Exception as e:
        print(f"   ✗ Failed to initialize SubAgentManager: {e}")
        return
    
    # 3. Initialize all agents
    print("\n3. Initializing agents...")
    try:
        success = await manager.initialize_agents()
        if success:
            print("   ✓ All agents initialized successfully")
        else:
            print("   ⚠ Some agents failed to initialize")
        
        agents = manager.list_agents()
        print(f"   ✓ Active agents: {agents}")
        
        events = manager.list_supported_events()
        print(f"   ✓ Supported events: {len(events)} events")
        
    except Exception as e:
        print(f"   ✗ Failed to initialize agents: {e}")
        return
    
    # 4. Get system status
    print("\n4. System Status:")
    status = manager.get_system_status()
    print(f"   • Total agents: {status['total_agents']}")
    print(f"   • Healthy agents: {status['healthy_agents']}")
    print(f"   • Supported events: {status['supported_events']}")
    print(f"   • Success rate: {status['success_rate']}%")
    
    # 5. Process sample events
    print("\n5. Processing sample events...")
    
    sample_events = [
        EventData(
            event_id="weather_001",
            event_type="weather",
            event_name="favorite_weather",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"weather": "sunny", "temperature": 25},
            metadata={"location": "Beijing"}
        ),
        EventData(
            event_id="trending_001", 
            event_type="trending",
            event_name="celebration",
            timestamp=datetime.now(),
            user_id=1,
            context_data={"topic": "New Year", "sentiment": "positive"},
            metadata={"source": "douyin"}
        ),
        EventData(
            event_id="unknown_001",
            event_type="unknown",
            event_name="unknown_event",
            timestamp=datetime.now(),
            user_id=1,
            context_data={},
            metadata={}
        )
    ]
    
    for event in sample_events:
        print(f"\n   Processing event: {event.event_name}")
        try:
            # Find appropriate agent
            agent = manager.get_agent_for_event(event.event_name)
            if agent:
                print(f"   ✓ Found agent: {agent.get_agent_type()}")
                
                # Process event with retry
                diary_entry = await manager.process_event_with_retry(event)
                if diary_entry:
                    print(f"   ✓ Generated diary entry:")
                    print(f"     Title: {diary_entry.title}")
                    print(f"     Content: {diary_entry.content}")
                    print(f"     Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
                else:
                    print("   ✗ Failed to generate diary entry")
            else:
                print(f"   ⚠ No agent found for event: {event.event_name}")
                
        except Exception as e:
            print(f"   ✗ Error processing event: {e}")
    
    # 6. Health monitoring
    print("\n6. Agent Health Status:")
    health = manager.get_agent_health()
    for agent_type, health_info in health.items():
        status_icon = "✓" if health_info.get("status") == "healthy" else "✗"
        print(f"   {status_icon} {agent_type}: {health_info.get('status', 'unknown')}")
        print(f"     Requests: {health_info.get('total_requests', 0)} total, "
              f"{health_info.get('successful_requests', 0)} successful")
    
    # 7. Configuration management
    print("\n7. Configuration Management:")
    try:
        print("   • Reloading configurations...")
        manager.reload_configurations()
        print("   ✓ Configurations reloaded successfully")
    except Exception as e:
        print(f"   ✗ Failed to reload configurations: {e}")
    
    # 8. Agent restart demonstration
    print("\n8. Agent Management:")
    agents = manager.list_agents()
    if agents:
        test_agent = agents[0]
        print(f"   • Restarting agent: {test_agent}")
        try:
            success = await manager.restart_agent(test_agent)
            if success:
                print(f"   ✓ Agent {test_agent} restarted successfully")
            else:
                print(f"   ✗ Failed to restart agent {test_agent}")
        except Exception as e:
            print(f"   ✗ Error restarting agent: {e}")
    
    # 9. Restart unhealthy agents
    print("\n   • Checking for unhealthy agents...")
    try:
        results = await manager.restart_unhealthy_agents()
        if results:
            print(f"   ✓ Restarted {len(results)} unhealthy agents")
            for agent_type, success in results.items():
                status = "✓" if success else "✗"
                print(f"     {status} {agent_type}")
        else:
            print("   ✓ No unhealthy agents found")
    except Exception as e:
        print(f"   ✗ Error restarting unhealthy agents: {e}")
    
    # 10. Final system status
    print("\n10. Final System Status:")
    final_status = manager.get_system_status()
    print(f"    • Total requests processed: {final_status['total_requests']}")
    print(f"    • Overall success rate: {final_status['success_rate']}%")
    print(f"    • System health: {final_status['healthy_agents']}/{final_status['total_agents']} agents healthy")
    
    # 11. Graceful shutdown
    print("\n11. Shutting down...")
    try:
        await manager.shutdown()
        print("   ✓ SubAgentManager shutdown complete")
    except Exception as e:
        print(f"   ✗ Error during shutdown: {e}")
    
    print("\n=== Example Complete ===")


def create_sample_configuration():
    """Create sample configuration files for demonstration."""
    
    # Create config directory
    config_dir = Path("diary_agent/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample LLM configuration
    llm_config = {
        "providers": {
            "qwen": {
                "provider_name": "qwen",
                "api_endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                "api_key": "your-qwen-api-key-here",
                "model_name": "qwen-turbo",
                "max_tokens": 150,
                "temperature": 0.7,
                "timeout": 30,
                "retry_attempts": 3
            },
            "deepseek": {
                "provider_name": "deepseek",
                "api_endpoint": "https://api.deepseek.com/v1/chat/completions",
                "api_key": "your-deepseek-api-key-here",
                "model_name": "deepseek-chat",
                "max_tokens": 150,
                "temperature": 0.7,
                "timeout": 30,
                "retry_attempts": 3
            }
        }
    }
    
    llm_config_path = Path("config") / "llm_configuration.json"
    with open(llm_config_path, 'w', encoding='utf-8') as f:
        json.dump(llm_config, f, indent=2, ensure_ascii=False)
    
    print(f"Created sample configuration at: {llm_config_path}")


if __name__ == "__main__":
    # Create sample configuration if needed
    create_sample_configuration()
    
    # Run the example
    asyncio.run(main())