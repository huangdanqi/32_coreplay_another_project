"""
Example demonstrating the difference between default_provider and fallback_providers
"""

import asyncio
from diary_agent.core.llm_manager import LLMConfigManager

async def demonstrate_provider_selection():
    """Demonstrate how default_provider and fallback_providers work."""
    
    print("🤖 Provider Selection Demonstration")
    print("=" * 50)
    
    # Initialize the manager
    manager = LLMConfigManager()
    
    # Show current configuration
    print("\n📋 Current Configuration:")
    print(f"Default Provider: {manager.model_selection_config.get('default_provider', 'None')}")
    print(f"Fallback Providers: {manager.model_selection_config.get('fallback_providers', [])}")
    
    # Show provider order (how they're actually used)
    print(f"\n🔀 Provider Order (for failover): {manager.provider_order}")
    
    print("\n" + "=" * 50)
    
    # Example 1: General request (uses default + fallbacks)
    print("\n📝 Example 1: General Request")
    print("Flow: default_provider → fallback_providers")
    
    try:
        result = await manager.generate_text_with_failover(
            prompt="Write a simple hello message",
            system_prompt="You are a helpful assistant"
        )
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Task-specific request (uses task preferences + fallbacks)
    print("\n📝 Example 2: Task-Specific Request (diary_writing)")
    print("Flow: task_preferred_providers → default_provider → fallback_providers")
    
    try:
        result = await manager.generate_text_for_task(
            task_type="diary_writing",
            prompt="今天天气很好",
            system_prompt="你是一个日记助手"
        )
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 3: Show provider selection logic
    print("\n🔍 Provider Selection Logic:")
    
    # Get current provider
    current = manager.get_current_provider()
    print(f"Current provider: {current.provider_name if current else 'None'}")
    
    # Get task-specific provider
    task_provider = manager.get_provider_for_task("diary_writing")
    print(f"Task-specific provider for 'diary_writing': {task_provider.provider_name if task_provider else 'None'}")
    
    # Show all enabled providers
    enabled = manager.get_enabled_providers()
    print(f"All enabled providers: {enabled}")
    
    print("\n" + "=" * 50)
    print("📚 Summary:")
    print("• default_provider: Always tried FIRST")
    print("• fallback_providers: Used when others FAIL")
    print("• Task-specific providers: Override default for specific tasks")
    print("• Priority order: Task-specific → Default → Fallbacks")

if __name__ == "__main__":
    asyncio.run(demonstrate_provider_selection())
