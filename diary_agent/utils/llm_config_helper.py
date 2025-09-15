"""
LLM Configuration Helper
A simple tool to manage LLM configuration conveniently.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any


class LLMConfigHelper:
    """Helper class to manage LLM configuration easily."""
    
    def __init__(self, config_path: str = "config/llm_configuration.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._get_default_config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_config(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "providers": {
                "ollama_qwen3": {
                    "provider_name": "ollama_qwen3",
                    "api_endpoint": "http://localhost:11434/api/generate",
                    "api_key": "not-required",
                    "model_name": "qwen3:4b",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 60,
                    "retry_attempts": 3,
                    "provider_type": "ollama",
                    "enabled": True,
                    "priority": 1,
                    "capabilities": ["general", "creative", "local"]
                }
            },
            "model_selection": {
                "default_provider": "ollama_qwen3",
                "fallback_providers": [],
                "task_specific_models": {},
                "auto_switch_rules": {
                    "enable_auto_switch": True,
                    "switch_on_failure": True,
                    "switch_on_timeout": True,
                    "switch_on_high_cost": False,
                    "max_switches_per_request": 3
                },
                "performance_settings": {
                    "prefer_fastest": False,
                    "prefer_cheapest": False,
                    "prefer_highest_quality": True,
                    "timeout_threshold": 10
                }
            },
            "usage_tracking": {
                "enabled": True,
                "track_cost": True,
                "track_performance": True,
                "track_quality": True
            }
        }
    
    def add_provider(self, name: str, provider_config: Dict[str, Any]):
        """Add a new provider."""
        self.config["providers"][name] = provider_config
        self._save_config()
        print(f"✅ Added provider: {name}")
    
    def remove_provider(self, name: str):
        """Remove a provider."""
        if name in self.config["providers"]:
            del self.config["providers"][name]
            self._save_config()
            print(f"✅ Removed provider: {name}")
        else:
            print(f"❌ Provider not found: {name}")
    
    def enable_provider(self, name: str):
        """Enable a provider."""
        if name in self.config["providers"]:
            self.config["providers"][name]["enabled"] = True
            self._save_config()
            print(f"✅ Enabled provider: {name}")
        else:
            print(f"❌ Provider not found: {name}")
    
    def disable_provider(self, name: str):
        """Disable a provider."""
        if name in self.config["providers"]:
            self.config["providers"][name]["enabled"] = False
            self._save_config()
            print(f"✅ Disabled provider: {name}")
        else:
            print(f"❌ Provider not found: {name}")
    
    def set_provider_priority(self, name: str, priority: int):
        """Set provider priority."""
        if name in self.config["providers"]:
            self.config["providers"][name]["priority"] = priority
            self._save_config()
            print(f"✅ Set priority for {name}: {priority}")
        else:
            print(f"❌ Provider not found: {name}")
    
    def add_task_config(self, task_type: str, preferred_providers: List[str], 
                        model_settings: Dict[str, Any]):
        """Add task-specific configuration."""
        self.config["model_selection"]["task_specific_models"][task_type] = {
            "preferred_providers": preferred_providers,
            "model_settings": model_settings
        }
        self._save_config()
        print(f"✅ Added task configuration: {task_type}")
    
    def remove_task_config(self, task_type: str):
        """Remove task-specific configuration."""
        if task_type in self.config["model_selection"]["task_specific_models"]:
            del self.config["model_selection"]["task_specific_models"][task_type]
            self._save_config()
            print(f"✅ Removed task configuration: {task_type}")
        else:
            print(f"❌ Task configuration not found: {task_type}")
    
    def set_default_provider(self, name: str):
        """Set default provider."""
        if name in self.config["providers"]:
            self.config["model_selection"]["default_provider"] = name
            self._save_config()
            print(f"✅ Set default provider: {name}")
        else:
            print(f"❌ Provider not found: {name}")
    
    def list_providers(self):
        """List all providers."""
        print("\n📋 Available Providers:")
        print("-" * 50)
        
        for name, config in self.config["providers"].items():
            status = "✅ Enabled" if config.get("enabled", True) else "❌ Disabled"
            priority = config.get("priority", 999)
            model = config["model_name"]
            provider_type = config["provider_type"]
            
            print(f"  {name}:")
            print(f"    Model: {model}")
            print(f"    Type: {provider_type}")
            print(f"    Status: {status}")
            print(f"    Priority: {priority}")
            print()
    
    def list_tasks(self):
        """List all task configurations."""
        print("\n📋 Task Configurations:")
        print("-" * 50)
        
        tasks = self.config["model_selection"]["task_specific_models"]
        if not tasks:
            print("  No task configurations defined")
            return
        
        for task_type, config in tasks.items():
            providers = config["preferred_providers"]
            settings = config["model_settings"]
            
            print(f"  {task_type}:")
            print(f"    Preferred providers: {providers}")
            print(f"    Settings: {settings}")
            print()
    
    def show_config_summary(self):
        """Show configuration summary."""
        print("\n📊 Configuration Summary:")
        print("-" * 50)
        
        # Provider summary
        providers = self.config["providers"]
        enabled_count = sum(1 for p in providers.values() if p.get("enabled", True))
        print(f"  Total providers: {len(providers)}")
        print(f"  Enabled providers: {enabled_count}")
        
        # Task summary
        tasks = self.config["model_selection"]["task_specific_models"]
        print(f"  Task configurations: {len(tasks)}")
        
        # Default provider
        default = self.config["model_selection"]["default_provider"]
        print(f"  Default provider: {default}")
        
        print()


def main():
    """Interactive configuration helper."""
    helper = LLMConfigHelper()
    
    print("🤖 LLM Configuration Helper")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. List providers")
        print("2. List tasks")
        print("3. Show summary")
        print("4. Add provider")
        print("5. Remove provider")
        print("6. Enable provider")
        print("7. Disable provider")
        print("8. Set provider priority")
        print("9. Add task configuration")
        print("10. Remove task configuration")
        print("11. Set default provider")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-11): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            helper.list_providers()
        elif choice == "2":
            helper.list_tasks()
        elif choice == "3":
            helper.show_config_summary()
        elif choice == "4":
            name = input("Provider name: ").strip()
            model = input("Model name: ").strip()
            endpoint = input("API endpoint: ").strip()
            api_key = input("API key (or 'not-required'): ").strip()
            provider_type = input("Provider type (cloud/ollama/local): ").strip()
            
            provider_config = {
                "provider_name": name,
                "api_endpoint": endpoint,
                "api_key": api_key,
                "model_name": model,
                "max_tokens": 150,
                "temperature": 0.7,
                "timeout": 30,
                "retry_attempts": 3,
                "provider_type": provider_type,
                "enabled": True,
                "priority": 999,
                "capabilities": ["general"]
            }
            
            helper.add_provider(name, provider_config)
        elif choice == "5":
            name = input("Provider name to remove: ").strip()
            helper.remove_provider(name)
        elif choice == "6":
            name = input("Provider name to enable: ").strip()
            helper.enable_provider(name)
        elif choice == "7":
            name = input("Provider name to disable: ").strip()
            helper.disable_provider(name)
        elif choice == "8":
            name = input("Provider name: ").strip()
            priority = int(input("Priority (lower = higher): ").strip())
            helper.set_provider_priority(name, priority)
        elif choice == "9":
            task_type = input("Task type: ").strip()
            providers_input = input("Preferred providers (comma-separated): ").strip()
            preferred_providers = [p.strip() for p in providers_input.split(",")]
            
            max_tokens = int(input("Max tokens: ").strip())
            temperature = float(input("Temperature: ").strip())
            
            model_settings = {
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            helper.add_task_config(task_type, preferred_providers, model_settings)
        elif choice == "10":
            task_type = input("Task type to remove: ").strip()
            helper.remove_task_config(task_type)
        elif choice == "11":
            name = input("Provider name for default: ").strip()
            helper.set_default_provider(name)
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
