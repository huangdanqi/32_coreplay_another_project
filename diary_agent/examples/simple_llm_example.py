"""
Simple LLM Configuration Example
Shows how to use default_provider and fallback_providers
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.core.llm_manager import LLMConfigManager

async def simple_llm_example():
    """Simple example of using LLM with default and fallback providers."""
    
    print("🤖 Simple LLM Configuration Example")
    print("=" * 50)
    
    # Initialize the manager
    manager = LLMConfigManager()
    
    # Show current configuration
    print(f"\n📋 Configuration:")
    print(f"Default Provider: {manager.model_selection_config.get('default_provider', 'None')}")
    print(f"Fallback Providers: {manager.model_selection_config.get('fallback_providers', [])}")
    print(f"Provider Order: {manager.provider_order}")
    
    # Show enabled providers
    enabled = manager.get_enabled_providers()
    print(f"Enabled Providers: {enabled}")
    
    print("\n" + "=" * 50)
    
    # Example: Generate text (uses default → fallbacks automatically)
    print("\n📝 Generating text...")
    print("Flow: default_provider → fallback_providers (if needed)")
    
    try:
        result = await manager.generate_text_with_failover(
            prompt="Write a short hello message",
            system_prompt="You are a helpful assistant"
        )
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Show provider status
    status = manager.get_provider_status()
    print(f"\n📊 Provider Status: {status}")
    
    print("\n" + "=" * 50)
    print("✅ Simple and clean! Just use generate_text_with_failover()")
    print("The system automatically handles default → fallback switching")

if __name__ == "__main__":
    asyncio.run(simple_llm_example())
