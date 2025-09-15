"""
LLM Configuration Manager for the diary agent system.
Handles multiple LLM providers with failover and retry mechanisms.
Enhanced with comprehensive error handling and circuit breaker patterns.
"""

import json
import asyncio
import aiohttp
import time
import random
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import asdict
from datetime import datetime

try:
    from ..utils.data_models import LLMConfig
    from ..utils.error_handler import (
        ErrorHandler, ErrorCategory, ErrorContext, CircuitBreakerConfig,
        with_error_handling, global_error_handler
    )
    from ..utils.logger import get_component_logger, diary_logger
    from ..utils.graceful_degradation import with_graceful_degradation, register_component_health_check
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_models import LLMConfig
    from utils.error_handler import (
        ErrorHandler, ErrorCategory, ErrorContext, CircuitBreakerConfig,
        with_error_handling, global_error_handler
    )
    from utils.logger import get_component_logger, diary_logger
    from utils.graceful_degradation import with_graceful_degradation, register_component_health_check


class LLMProviderError(Exception):
    """Exception raised when LLM provider fails."""
    pass


class LLMConfigurationError(Exception):
    """Exception raised when LLM configuration is invalid."""
    pass


class APIClient:
    """Base API client for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using the LLM provider."""
        raise NotImplementedError("Subclasses must implement generate_text")
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }


class QwenAPIClient(APIClient):
    """API client for Qwen provider."""
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using Qwen API."""
        if not self.session:
            raise LLMProviderError("Session not initialized")
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt} if system_prompt else None,
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        # Remove None values
        payload["messages"] = [msg for msg in payload["messages"] if msg is not None]
        
        try:
            async with self.session.post(
                self.config.api_endpoint,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(f"Qwen API error {response.status}: {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except aiohttp.ClientError as e:
            raise LLMProviderError(f"Qwen API client error: {str(e)}")
        except KeyError as e:
            raise LLMProviderError(f"Qwen API response format error: {str(e)}")


class DeepSeekAPIClient(APIClient):
    """API client for DeepSeek provider."""
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using DeepSeek API."""
        if not self.session:
            raise LLMProviderError("Session not initialized")
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt} if system_prompt else None,
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        # Remove None values
        payload["messages"] = [msg for msg in payload["messages"] if msg is not None]
        
        try:
            async with self.session.post(
                self.config.api_endpoint,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(f"DeepSeek API error {response.status}: {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except aiohttp.ClientError as e:
            raise LLMProviderError(f"DeepSeek API client error: {str(e)}")
        except KeyError as e:
            raise LLMProviderError(f"DeepSeek API response format error: {str(e)}")


class ZhipuAPIClient(APIClient):
    """API client for Zhipu provider."""
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using Zhipu API."""
        if not self.session:
            raise LLMProviderError("Session not initialized")
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt} if system_prompt else None,
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        # Remove None values
        payload["messages"] = [msg for msg in payload["messages"] if msg is not None]
        
        try:
            async with self.session.post(
                self.config.api_endpoint,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(f"Zhipu API error {response.status}: {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except aiohttp.ClientError as e:
            raise LLMProviderError(f"Zhipu API client error: {str(e)}")
        except KeyError as e:
            raise LLMProviderError(f"Zhipu API response format error: {str(e)}")


class OllamaAPIClient(APIClient):
    """API client for Ollama local provider."""
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for Ollama API requests (no auth needed)."""
        return {
            "Content-Type": "application/json"
        }
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using Ollama API."""
        if not self.session:
            raise LLMProviderError("Session not initialized")
        
        # Combine system and user prompts for Ollama
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        
        payload = {
            "model": self.config.model_name,
            "prompt": full_prompt,
            "options": {
                "num_predict": self.config.max_tokens,
                "temperature": self.config.temperature
            },
            "stream": False
        }
        
        try:
            async with self.session.post(
                self.config.api_endpoint,
                headers=self._prepare_headers(),
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(f"Ollama API error {response.status}: {error_text}")
                
                result = await response.json()
                return result["response"].strip()
                
        except aiohttp.ClientError as e:
            raise LLMProviderError(f"Ollama API client error: {str(e)}")
        except KeyError as e:
            raise LLMProviderError(f"Ollama API response format error: {str(e)}")


class LLMConfigManager:
    """Manages LLM provider configurations with failover and retry mechanisms."""
    
    def __init__(self, config_path: str = "config/llm_configuration.json"):
        self.config_path = Path(config_path)
        self.providers: Dict[str, LLMConfig] = {}
        self.provider_order: List[str] = []
        self.current_provider_index = 0
        self.logger = get_component_logger("llm_manager")
        self.error_handler = global_error_handler
        
        # New configuration features
        self.model_selection_config = {}
        self.auto_switch_rules = {}
        self.performance_settings = {}
        
        # Setup circuit breakers for each provider
        self._setup_circuit_breakers()
        
        # Setup health checks
        self._setup_health_checks()
        
        self._load_configuration()
    
    def _setup_circuit_breakers(self):
        """Setup circuit breakers for LLM providers."""
        circuit_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            timeout=30
        )
        
        # Register circuit breakers for common providers
        for provider in ["qwen", "deepseek", "zhipu", "ollama_qwen3"]:
            self.error_handler.register_circuit_breaker(f"llm_{provider}", circuit_config)
    
    def _setup_health_checks(self):
        """Setup health checks for LLM providers."""
        def check_llm_health():
            try:
                # Simple health check - try to get current provider
                current = self.get_current_provider()
                return current is not None
            except Exception:
                return False
        
        register_component_health_check("llm_manager", check_llm_health, interval=120)
    
    def _load_configuration(self):
        """Load LLM provider configurations from file."""
        try:
            if not self.config_path.exists():
                self._create_default_configuration()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.providers = {}
            self.provider_order = []
            
            # Load providers with enhanced configuration
            for provider_name, provider_config in config_data.get("providers", {}).items():
                try:
                    # Check if provider is enabled
                    if provider_config.get("enabled", True):
                        llm_config = LLMConfig(**provider_config)
                        self.providers[provider_name] = llm_config
                        self.provider_order.append(provider_name)
                except TypeError as e:
                    raise LLMConfigurationError(f"Invalid configuration for provider {provider_name}: {str(e)}")
            
            if not self.providers:
                raise LLMConfigurationError("No valid LLM providers configured")
            
            # Load model selection configuration
            self.model_selection_config = config_data.get("model_selection", {})
            self.auto_switch_rules = self.model_selection_config.get("auto_switch_rules", {})
            self.performance_settings = self.model_selection_config.get("performance_settings", {})
            
            # Sort providers by priority if specified
            self._sort_providers_by_priority()
            
            # Set the default provider as the first in the order
            default_provider = self.model_selection_config.get("default_provider")
            if default_provider and default_provider in self.providers:
                # Move default provider to the front of the list
                if default_provider in self.provider_order:
                    self.provider_order.remove(default_provider)
                self.provider_order.insert(0, default_provider)
                self.logger.info(f"Set default provider: {default_provider}")
            elif self.provider_order:
                self.logger.info(f"No default provider specified, using first available: {self.provider_order[0]}")
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise LLMConfigurationError(f"Failed to load LLM configuration: {str(e)}")
    
    def _create_default_configuration(self):
        """Create default LLM configuration file."""
        default_config = {
            "providers": {
                "qwen": {
                    "provider_name": "qwen",
                    "api_endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    "api_key": "your-qwen-api-key",
                    "model_name": "qwen-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                },
                "deepseek": {
                    "provider_name": "deepseek",
                    "api_endpoint": "https://api.deepseek.com/v1/chat/completions",
                    "api_key": "your-deepseek-api-key",
                    "model_name": "deepseek-chat",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                }
            }
        }
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    def _sort_providers_by_priority(self):
        """Sort providers by priority if specified in configuration."""
        if not self.provider_order:
            return
            
        # Create list of (provider_name, priority) tuples
        provider_priorities = []
        for provider_name in self.provider_order:
            provider_config = self.providers[provider_name]
            # Get priority from config, default to 999 if not specified
            priority = getattr(provider_config, 'priority', 999)
            provider_priorities.append((provider_name, priority))
        
        # Sort by priority (lower number = higher priority)
        provider_priorities.sort(key=lambda x: x[1])
        
        # Update provider order
        self.provider_order = [provider_name for provider_name, _ in provider_priorities]
    
    def get_provider_config(self, provider_name: str) -> Optional[LLMConfig]:
        """Get configuration for a specific provider."""
        return self.providers.get(provider_name)
    
    def get_current_provider(self) -> Optional[LLMConfig]:
        """Get the current active provider configuration."""
        if not self.provider_order:
            return None
        
        current_provider_name = self.provider_order[self.current_provider_index]
        return self.providers.get(current_provider_name)
    
    def _create_api_client(self, config: LLMConfig) -> APIClient:
        """Create appropriate API client based on provider."""
        provider_name = config.provider_name.lower()
        
        if provider_name == "qwen":
            return QwenAPIClient(config)
        elif provider_name == "deepseek":
            return DeepSeekAPIClient(config)
        elif provider_name == "zhipu":
            return ZhipuAPIClient(config)
        elif "ollama" in provider_name:
            return OllamaAPIClient(config)
        else:
            raise LLMConfigurationError(f"Unsupported provider: {config.provider_name}")
    
    @with_graceful_degradation("llm_api")
    async def generate_text_with_failover(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text with automatic failover between providers."""
        start_time = datetime.now()
        last_error = None
        
        self.logger.info(f"Starting LLM text generation with {len(self.provider_order)} providers available")
        
        # Try each provider in order
        for attempt in range(len(self.provider_order)):
            current_config = self.get_current_provider()
            if not current_config:
                error_context = ErrorContext(
                    error_category=ErrorCategory.LLM_API_FAILURE,
                    error_message="No providers available",
                    component_name="llm_manager",
                    timestamp=datetime.now()
                )
                self.error_handler.handle_error(
                    LLMConfigurationError("No providers available"), 
                    error_context
                )
                raise LLMConfigurationError("No providers available")
            
            try:
                # Use circuit breaker for this provider
                circuit_breaker = self.error_handler.get_circuit_breaker(f"llm_{current_config.provider_name}")
                
                result = await circuit_breaker.call(
                    self._generate_with_retry, 
                    current_config, 
                    prompt, 
                    system_prompt
                )
                
                # Log successful generation
                duration = (datetime.now() - start_time).total_seconds()
                diary_logger.log_llm_api_call(
                    provider=current_config.provider_name,
                    model=current_config.model_name,
                    tokens_used=len(result.split()),  # Approximate token count
                    response_time=duration,
                    status="success"
                )
                
                self.logger.info(f"Successfully generated text using {current_config.provider_name}")
                return result
                
            except Exception as e:
                last_error = e
                
                # Log the failure
                duration = (datetime.now() - start_time).total_seconds()
                diary_logger.log_llm_api_call(
                    provider=current_config.provider_name,
                    model=current_config.model_name,
                    tokens_used=0,
                    response_time=duration,
                    status="failed"
                )
                
                # Handle the error
                error_context = ErrorContext(
                    error_category=ErrorCategory.LLM_API_FAILURE,
                    error_message=str(e),
                    component_name="llm_manager",
                    timestamp=datetime.now(),
                    retry_count=attempt,
                    metadata={"provider": current_config.provider_name}
                )
                
                recovery_result = self.error_handler.handle_error(e, error_context)
                
                self.logger.warning(f"Provider {current_config.provider_name} failed: {str(e)}")
                self._switch_to_next_provider()
        
        # If all providers failed, raise the last error
        error_msg = f"All LLM providers failed. Last error: {str(last_error)}"
        self.logger.error(error_msg)
        raise LLMProviderError(error_msg)
    
    async def _generate_with_retry(self, config: LLMConfig, prompt: str, system_prompt: str) -> str:
        """Generate text with exponential backoff retry."""
        last_error = None
        
        for attempt in range(config.retry_attempts):
            try:
                async with self._create_api_client(config) as client:
                    result = await client.generate_text(prompt, system_prompt)
                    
                    # Log successful retry if this wasn't the first attempt
                    if attempt > 0:
                        diary_logger.log_error_recovery(
                            component="llm_manager",
                            error_category="llm_api_failure",
                            recovery_action=f"retry_attempt_{attempt + 1}",
                            success=True
                        )
                    
                    return result
                    
            except LLMProviderError as e:
                last_error = e
                
                # Log failed retry attempt
                diary_logger.log_error_recovery(
                    component="llm_manager",
                    error_category="llm_api_failure",
                    recovery_action=f"retry_attempt_{attempt + 1}",
                    success=False
                )
                
                if attempt < config.retry_attempts - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
                    self.logger.info(f"Retry {attempt + 1}/{config.retry_attempts} for {config.provider_name} after {delay:.2f}s")
        
        error_msg = f"Provider {config.provider_name} failed after {config.retry_attempts} attempts: {str(last_error)}"
        self.logger.error(error_msg)
        raise LLMProviderError(error_msg)
    
    def _switch_to_next_provider(self):
        """Switch to the next provider in the list."""
        if len(self.provider_order) > 1:
            self.current_provider_index = (self.current_provider_index + 1) % len(self.provider_order)
            print(f"Switched to provider: {self.provider_order[self.current_provider_index]}")
    
    def reload_configuration(self):
        """Reload configuration from file."""
        self._load_configuration()
        self.current_provider_index = 0
        print("LLM configuration reloaded")
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status information for all providers."""
        return {
            "providers": list(self.providers.keys()),
            "current_provider": self.provider_order[self.current_provider_index] if self.provider_order else None,
            "total_providers": len(self.providers)
        }
    
    def get_providers_by_capability(self, capability: str) -> List[LLMConfig]:
        """Get all providers that support a specific capability."""
        capable_providers = []
        
        for provider_name, provider_config in self.providers.items():
            capabilities = getattr(provider_config, 'capabilities', [])
            if capability in capabilities:
                capable_providers.append(provider_config)
        
        return capable_providers
    
    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled providers."""
        return [name for name, config in self.providers.items() 
                if getattr(config, 'enabled', True)]
    
    def enable_provider(self, provider_name: str) -> bool:
        """Enable a specific provider."""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = True
            if provider_name not in self.provider_order:
                self.provider_order.append(provider_name)
            return True
        return False
    
    def disable_provider(self, provider_name: str) -> bool:
        """Disable a specific provider."""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = False
            if provider_name in self.provider_order:
                self.provider_order.remove(provider_name)
            return True
        return False
    
    def set_provider_priority(self, provider_name: str, priority: int) -> bool:
        """Set priority for a specific provider."""
        if provider_name in self.providers:
            self.providers[provider_name].priority = priority
            self._sort_providers_by_priority()
            return True
        return False
    
    def set_default_provider(self, provider_name: str) -> bool:
        """Set the default provider to use."""
        if provider_name not in self.providers:
            self.logger.error(f"Provider {provider_name} not found")
            return False
        
        # Update the configuration
        self.model_selection_config["default_provider"] = provider_name
        
        # Move the provider to the front of the order
        if provider_name in self.provider_order:
            self.provider_order.remove(provider_name)
        self.provider_order.insert(0, provider_name)
        
        # Reset current provider index
        self.current_provider_index = 0
        
        self.logger.info(f"Set default provider to: {provider_name}")
        return True
    
    def get_default_provider(self) -> Optional[str]:
        """Get the current default provider."""
        return self.model_selection_config.get("default_provider")
    
    def get_fallback_providers(self) -> List[str]:
        """Get the list of fallback providers."""
        return self.model_selection_config.get("fallback_providers", [])