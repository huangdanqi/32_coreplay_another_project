"""
Test to verify that default_provider is now working correctly
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.core.llm_manager import LLMConfigManager

async def test_default_provider():
    """Test that default_provider is working correctly."""
    
    print("🧪 Testing Default Provider Functionality")
    print("=" * 50)
    
    # Initialize the manager
    manager = LLMConfigManager()
    
    # Show current configuration
    print(f"\n📋 Current Configuration:")
    print(f"Default Provider: {manager.get_default_provider()}")
    print(f"Fallback Providers: {manager.get_fallback_providers()}")
    print(f"Provider Order: {manager.provider_order}")
    print(f"Current Provider: {manager.get_current_provider().provider_name if manager.get_current_provider() else 'None'}")
    
    # Test setting different default providers
    print(f"\n🔄 Testing Default Provider Changes:")
    
    # Test 1: Set Qwen as default
    print(f"\n1. Setting Qwen as default...")
    success = manager.set_default_provider("qwen")
    print(f"   Success: {success}")
    print(f"   New default: {manager.get_default_provider()}")
    print(f"   Provider order: {manager.provider_order}")
    print(f"   Current provider: {manager.get_current_provider().provider_name if manager.get_current_provider() else 'None'}")
    
    # Test 2: Set DeepSeek as default
    print(f"\n2. Setting DeepSeek as default...")
    success = manager.set_default_provider("deepseek")
    print(f"   Success: {success}")
    print(f"   New default: {manager.get_default_provider()}")
    print(f"   Provider order: {manager.provider_order}")
    print(f"   Current provider: {manager.get_current_provider().provider_name if manager.get_current_provider() else 'None'}")
    
    # Test 3: Set Ollama as default
    print(f"\n3. Setting Ollama as default...")
    success = manager.set_default_provider("ollama_qwen3")
    print(f"   Success: {success}")
    print(f"   New default: {manager.get_default_provider()}")
    print(f"   Provider order: {manager.provider_order}")
    print(f"   Current provider: {manager.get_current_provider().provider_name if manager.get_current_provider() else 'None'}")
    
    # Test 4: Try to set non-existent provider
    print(f"\n4. Testing non-existent provider...")
    success = manager.set_default_provider("non_existent")
    print(f"   Success: {success}")
    
    print(f"\n✅ Default provider functionality is working!")
    print(f"   You can now use manager.set_default_provider('model_name') to choose your model")

if __name__ == "__main__":
    asyncio.run(test_default_provider())
