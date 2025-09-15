"""
Simple test to show task_specific_models are working
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.core.llm_manager import LLMConfigManager

async def test_task_specific_models():
    """Test that task_specific_models are working."""
    
    print("🧪 Testing Task-Specific Models")
    print("=" * 40)
    
    # Initialize the manager
    manager = LLMConfigManager()
    
    # Check if task_specific_models are loaded
    print(f"\n📋 Task-specific models found: {len(manager.task_specific_models)}")
    
    for task_type, config in manager.task_specific_models.items():
        print(f"  ✅ {task_type}: {config['preferred_providers']}")
    
    # Test getting provider for specific task
    print(f"\n🔍 Testing provider selection:")
    
    diary_provider = manager.get_provider_for_task("diary_writing")
    print(f"  Diary writing provider: {diary_provider.provider_name if diary_provider else 'None'}")
    
    coding_provider = manager.get_provider_for_task("coding_tasks")
    print(f"  Coding tasks provider: {coding_provider.provider_name if coding_provider else 'None'}")
    
    # Test getting task-specific settings
    diary_settings = manager.get_task_specific_settings("diary_writing")
    print(f"  Diary writing settings: {diary_settings}")
    
    coding_settings = manager.get_task_specific_settings("coding_tasks")
    print(f"  Coding tasks settings: {coding_settings}")
    
    print(f"\n✅ Task-specific models are working!")

if __name__ == "__main__":
    asyncio.run(test_task_specific_models())
