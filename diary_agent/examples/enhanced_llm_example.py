"""
Enhanced LLM Configuration Usage Example
This demonstrates how to use the new convenient model selection features.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.core.llm_manager import LLMConfigManager


async def demonstrate_task_specific_models():
    """Demonstrate how to use task-specific model selection."""
    print("=== Task-Specific Model Selection ===")
    
    # Initialize the manager
    manager = LLMConfigManager()
    
    # Show available tasks
    available_tasks = manager.get_available_tasks()
    print(f"Available task types: {available_tasks}")
    
    # Example 1: Diary writing (uses Qwen or Ollama with creative settings)
    print("\n1. Diary Writing Task:")
    diary_prompt = "今天天气很好，心情愉快。请写一篇简短的日记。"
    diary_result = await manager.generate_text_for_task(
        task_type="diary_writing",
        prompt=diary_prompt,
        system_prompt="你是一个日记助手，请用中文写简短的日记内容。"
    )
    print(f"Diary result: {diary_result}")
    
    # Example 2: Weather analysis (uses DeepSeek with analytical settings)
    print("\n2. Weather Analysis Task:")
    weather_prompt = "分析今天的天气数据：温度25°C，湿度60%，风速5km/h"
    weather_result = await manager.generate_text_for_task(
        task_type="weather_analysis",
        prompt=weather_prompt,
        system_prompt="你是一个天气分析专家，请分析天气数据。"
    )
    print(f"Weather analysis: {weather_result}")
    
    # Example 3: Creative content (uses Qwen with high creativity)
    print("\n3. Creative Content Task:")
    creative_prompt = "写一个关于魔法森林的短故事"
    creative_result = await manager.generate_text_for_task(
        task_type="creative_content",
        prompt=creative_prompt,
        system_prompt="你是一个创意作家，请写一个有趣的故事。"
    )
    print(f"Creative story: {creative_result}")
    
    # Example 4: Coding task (uses DeepSeek with coding settings)
    print("\n4. Coding Task:")
    coding_prompt = "写一个Python函数来计算斐波那契数列"
    coding_result = await manager.generate_text_for_task(
        task_type="coding_tasks",
        prompt=coding_prompt,
        system_prompt="你是一个编程助手，请写清晰的代码。"
    )
    print(f"Coding result: {coding_result}")


async def demonstrate_provider_management():
    """Demonstrate provider management features."""
    print("\n=== Provider Management ===")
    
    manager = LLMConfigManager()
    
    # Show enabled providers
    enabled_providers = manager.get_enabled_providers()
    print(f"Enabled providers: {enabled_providers}")
    
    # Show providers by capability
    creative_providers = manager.get_providers_by_capability("creative")
    print(f"Creative providers: {[p.provider_name for p in creative_providers]}")
    
    coding_providers = manager.get_providers_by_capability("coding")
    print(f"Coding providers: {[p.provider_name for p in coding_providers]}")
    
    # Show provider priorities
    print("\nProvider priorities:")
    for provider_name in manager.provider_order:
        provider = manager.providers[provider_name]
        priority = getattr(provider, 'priority', 999)
        print(f"  {provider_name}: priority {priority}")


async def demonstrate_dynamic_configuration():
    """Demonstrate dynamic configuration changes."""
    print("\n=== Dynamic Configuration ===")
    
    manager = LLMConfigManager()
    
    # Add a new task configuration
    print("Adding new task configuration...")
    manager.add_task_configuration(
        task_type="translation",
        preferred_providers=["qwen", "deepseek"],
        model_settings={
            "max_tokens": 400,
            "temperature": 0.3
        }
    )
    
    # Show updated available tasks
    available_tasks = manager.get_available_tasks()
    print(f"Updated available tasks: {available_tasks}")
    
    # Test the new task
    translation_prompt = "Translate this text to English: 今天天气很好"
    translation_result = await manager.generate_text_for_task(
        task_type="translation",
        prompt=translation_prompt,
        system_prompt="你是一个翻译助手，请准确翻译文本。"
    )
    print(f"Translation result: {translation_result}")
    
    # Remove the task configuration
    manager.remove_task_configuration("translation")
    print("Removed translation task configuration")


async def demonstrate_provider_control():
    """Demonstrate provider enable/disable functionality."""
    print("\n=== Provider Control ===")
    
    manager = LLMConfigManager()
    
    # Show current enabled providers
    enabled_providers = manager.get_enabled_providers()
    print(f"Currently enabled: {enabled_providers}")
    
    # Disable a provider
    print("Disabling DeepSeek provider...")
    manager.disable_provider("deepseek")
    
    # Show updated enabled providers
    enabled_providers = manager.get_enabled_providers()
    print(f"After disabling DeepSeek: {enabled_providers}")
    
    # Re-enable the provider
    print("Re-enabling DeepSeek provider...")
    manager.enable_provider("deepseek")
    
    # Show final enabled providers
    enabled_providers = manager.get_enabled_providers()
    print(f"After re-enabling DeepSeek: {enabled_providers}")


async def main():
    """Run all demonstrations."""
    print("Enhanced LLM Configuration Demonstrations")
    print("=" * 60)
    
    try:
        await demonstrate_task_specific_models()
        await demonstrate_provider_management()
        await demonstrate_dynamic_configuration()
        await demonstrate_provider_control()
        
        print("\n" + "=" * 60)
        print("✓ All demonstrations completed successfully!")
        print("\nKey Benefits:")
        print("- Task-specific model selection")
        print("- Automatic provider switching based on task type")
        print("- Dynamic configuration management")
        print("- Provider capability-based selection")
        print("- Easy enable/disable of providers")
        
    except Exception as e:
        print(f"\n✗ Demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
