"""
Example usage of LLM Configuration Manager.
This demonstrates how to use the LLM manager with failover capabilities.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.core.llm_manager import LLMConfigManager, LLMProviderError


async def example_basic_usage():
    """Example of basic LLM manager usage."""
    print("=== Basic LLM Manager Usage ===")
    
    # Initialize the manager
    manager = LLMConfigManager()
    
    # Get provider status
    status = manager.get_provider_status()
    print(f"Available providers: {status['providers']}")
    print(f"Current provider: {status['current_provider']}")
    print(f"Total providers: {status['total_providers']}")
    
    # Get current provider configuration
    current_config = manager.get_current_provider()
    print(f"\nCurrent provider config:")
    print(f"  Name: {current_config.provider_name}")
    print(f"  Model: {current_config.model_name}")
    print(f"  Max tokens: {current_config.max_tokens}")
    print(f"  Temperature: {current_config.temperature}")
    print(f"  Timeout: {current_config.timeout}")
    print(f"  Retry attempts: {current_config.retry_attempts}")


async def example_failover_simulation():
    """Example of failover mechanism (simulated)."""
    print("\n=== Failover Mechanism Simulation ===")
    
    manager = LLMConfigManager()
    
    print(f"Starting with provider: {manager.get_current_provider().provider_name}")
    
    # Simulate switching to next provider
    manager._switch_to_next_provider()
    print(f"Switched to provider: {manager.get_current_provider().provider_name}")
    
    # Switch again (should wrap around)
    manager._switch_to_next_provider()
    print(f"Switched to provider: {manager.get_current_provider().provider_name}")


async def example_configuration_management():
    """Example of configuration management features."""
    print("\n=== Configuration Management ===")
    
    manager = LLMConfigManager()
    
    # Get specific provider configurations
    qwen_config = manager.get_provider_config("qwen")
    deepseek_config = manager.get_provider_config("deepseek")
    
    print("Qwen Configuration:")
    print(f"  Endpoint: {qwen_config.api_endpoint}")
    print(f"  Model: {qwen_config.model_name}")
    
    print("DeepSeek Configuration:")
    print(f"  Endpoint: {deepseek_config.api_endpoint}")
    print(f"  Model: {deepseek_config.model_name}")
    
    # Demonstrate configuration reloading
    print("\nReloading configuration...")
    manager.reload_configuration()
    print("Configuration reloaded successfully")


async def example_api_client_creation():
    """Example of API client creation."""
    print("\n=== API Client Creation ===")
    
    manager = LLMConfigManager()
    
    # Create clients for different providers
    qwen_config = manager.get_provider_config("qwen")
    qwen_client = manager._create_api_client(qwen_config)
    print(f"Created Qwen client: {qwen_client.__class__.__name__}")
    
    deepseek_config = manager.get_provider_config("deepseek")
    deepseek_client = manager._create_api_client(deepseek_config)
    print(f"Created DeepSeek client: {deepseek_client.__class__.__name__}")


async def example_error_handling():
    """Example of error handling."""
    print("\n=== Error Handling Examples ===")
    
    manager = LLMConfigManager()
    
    # Example 1: Unsupported provider
    try:
        from diary_agent.utils.data_models import LLMConfig
        unsupported_config = LLMConfig(
            provider_name="unsupported",
            api_endpoint="https://api.unsupported.com",
            api_key="test-key",
            model_name="test-model"
        )
        manager._create_api_client(unsupported_config)
    except Exception as e:
        print(f"Caught expected error for unsupported provider: {type(e).__name__}")
    
    # Example 2: Non-existent provider
    nonexistent_config = manager.get_provider_config("nonexistent")
    print(f"Non-existent provider config: {nonexistent_config}")


async def main():
    """Run all examples."""
    print("LLM Configuration Manager Examples")
    print("=" * 50)
    
    try:
        await example_basic_usage()
        await example_failover_simulation()
        await example_configuration_management()
        await example_api_client_creation()
        await example_error_handling()
        
        print("\n" + "=" * 50)
        print("✓ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())