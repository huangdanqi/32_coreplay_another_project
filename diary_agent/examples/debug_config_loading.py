"""
Debug script to see why ollama_qwen3 provider is not being loaded
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from diary_agent.utils.data_models import LLMConfig

def debug_config_loading():
    """Debug the configuration loading process."""
    
    print("🔍 Debugging Configuration Loading")
    print("=" * 50)
    
    # Load the JSON file
    config_path = Path("config/llm_configuration.json")
    
    print(f"\n📁 Loading configuration from: {config_path}")
    print(f"File exists: {config_path.exists()}")
    
    if not config_path.exists():
        print("❌ Configuration file not found!")
        return
    
    # Read the JSON
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    print(f"\n📋 JSON Configuration:")
    print(f"Providers found: {list(config_data.get('providers', {}).keys())}")
    print(f"Model selection: {config_data.get('model_selection', {})}")
    
    # Try to load each provider
    print(f"\n🔧 Testing Provider Loading:")
    
    providers = {}
    provider_order = []
    
    for provider_name, provider_config in config_data.get("providers", {}).items():
        print(f"\n  Testing provider: {provider_name}")
        print(f"    Enabled: {provider_config.get('enabled', True)}")
        
        try:
            if provider_config.get("enabled", True):
                llm_config = LLMConfig(**provider_config)
                providers[provider_name] = llm_config
                provider_order.append(provider_name)
                print(f"    ✅ Successfully loaded: {provider_name}")
                print(f"    Model: {llm_config.model_name}")
                print(f"    Priority: {llm_config.priority}")
            else:
                print(f"    ⚠️  Provider disabled: {provider_name}")
        except TypeError as e:
            print(f"    ❌ Failed to load {provider_name}: {str(e)}")
        except Exception as e:
            print(f"    ❌ Unexpected error loading {provider_name}: {str(e)}")
    
    print(f"\n📊 Final Results:")
    print(f"Loaded providers: {list(providers.keys())}")
    print(f"Provider order: {provider_order}")
    
    # Check model selection
    model_selection = config_data.get("model_selection", {})
    default_provider = model_selection.get("default_provider")
    fallback_providers = model_selection.get("fallback_providers", [])
    
    print(f"\n🎯 Model Selection:")
    print(f"Default provider: {default_provider}")
    print(f"Fallback providers: {fallback_providers}")
    
    if default_provider:
        if default_provider in providers:
            print(f"✅ Default provider '{default_provider}' is available")
        else:
            print(f"❌ Default provider '{default_provider}' is NOT available")
    
    # Check fallback providers
    for fallback in fallback_providers:
        if fallback in providers:
            print(f"✅ Fallback provider '{fallback}' is available")
        else:
            print(f"❌ Fallback provider '{fallback}' is NOT available")

if __name__ == "__main__":
    debug_config_loading()
