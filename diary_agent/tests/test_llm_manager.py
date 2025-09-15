"""
Unit tests for LLM Configuration Manager.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from diary_agent.core.llm_manager import (
    LLMConfigManager, 
    QwenAPIClient, 
    DeepSeekAPIClient,
    LLMProviderError,
    LLMConfigurationError
)
from diary_agent.utils.data_models import LLMConfig


class TestLLMConfig:
    """Test LLMConfig data model."""
    
    def test_llm_config_creation(self):
        """Test LLMConfig creation with default values."""
        config = LLMConfig(
            provider_name="test",
            api_endpoint="https://api.test.com",
            api_key="test-key",
            model_name="test-model"
        )
        
        assert config.provider_name == "test"
        assert config.api_endpoint == "https://api.test.com"
        assert config.api_key == "test-key"
        assert config.model_name == "test-model"
        assert config.max_tokens == 150
        assert config.temperature == 0.7
        assert config.timeout == 30
        assert config.retry_attempts == 3
    
    def test_llm_config_custom_values(self):
        """Test LLMConfig creation with custom values."""
        config = LLMConfig(
            provider_name="custom",
            api_endpoint="https://api.custom.com",
            api_key="custom-key",
            model_name="custom-model",
            max_tokens=200,
            temperature=0.5,
            timeout=60,
            retry_attempts=5
        )
        
        assert config.max_tokens == 200
        assert config.temperature == 0.5
        assert config.timeout == 60
        assert config.retry_attempts == 5


class TestAPIClients:
    """Test API client implementations."""
    
    @pytest.fixture
    def qwen_config(self):
        """Fixture for Qwen configuration."""
        return LLMConfig(
            provider_name="qwen",
            api_endpoint="https://api.qwen.com/v1/chat",
            api_key="test-qwen-key",
            model_name="qwen-turbo"
        )
    
    @pytest.fixture
    def deepseek_config(self):
        """Fixture for DeepSeek configuration."""
        return LLMConfig(
            provider_name="deepseek",
            api_endpoint="https://api.deepseek.com/v1/chat",
            api_key="test-deepseek-key",
            model_name="deepseek-chat"
        )
    
    @pytest.mark.asyncio
    async def test_qwen_client_success(self, qwen_config):
        """Test successful Qwen API call."""
        mock_response = {
            "choices": [
                {"message": {"content": "Generated diary content"}}
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aenter__.return_value = mock_resp
            
            async with QwenAPIClient(qwen_config) as client:
                result = await client.generate_text("Test prompt", "System prompt")
                
            assert result == "Generated diary content"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_qwen_client_api_error(self, qwen_config):
        """Test Qwen API error handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_resp = AsyncMock()
            mock_resp.status = 400
            mock_resp.text = AsyncMock(return_value="Bad Request")
            mock_post.return_value.__aenter__.return_value = mock_resp
            
            with pytest.raises(LLMProviderError, match="Qwen API error 400"):
                async with QwenAPIClient(qwen_config) as client:
                    await client.generate_text("Test prompt")
    
    @pytest.mark.asyncio
    async def test_deepseek_client_success(self, deepseek_config):
        """Test successful DeepSeek API call."""
        mock_response = {
            "choices": [
                {"message": {"content": "Generated diary content"}}
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aenter__.return_value = mock_resp
            
            async with DeepSeekAPIClient(deepseek_config) as client:
                result = await client.generate_text("Test prompt", "System prompt")
                
            assert result == "Generated diary content"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deepseek_client_network_error(self, deepseek_config):
        """Test DeepSeek network error handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientError("Network error")
            
            with pytest.raises(LLMProviderError, match="DeepSeek API client error"):
                async with DeepSeekAPIClient(deepseek_config) as client:
                    await client.generate_text("Test prompt")
    
    @pytest.mark.asyncio
    async def test_api_client_response_format_error(self, qwen_config):
        """Test API client response format error."""
        mock_response = {"invalid": "response"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aenter__.return_value = mock_resp
            
            with pytest.raises(LLMProviderError, match="response format error"):
                async with QwenAPIClient(qwen_config) as client:
                    await client.generate_text("Test prompt")


class TestLLMConfigManager:
    """Test LLM Configuration Manager."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary configuration file."""
        config_data = {
            "providers": {
                "qwen": {
                    "provider_name": "qwen",
                    "api_endpoint": "https://api.qwen.com/v1/chat",
                    "api_key": "test-qwen-key",
                    "model_name": "qwen-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                },
                "deepseek": {
                    "provider_name": "deepseek",
                    "api_endpoint": "https://api.deepseek.com/v1/chat",
                    "api_key": "test-deepseek-key",
                    "model_name": "deepseek-chat",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_load_configuration_success(self, temp_config_file):
        """Test successful configuration loading."""
        manager = LLMConfigManager(temp_config_file)
        
        assert len(manager.providers) == 2
        assert "qwen" in manager.providers
        assert "deepseek" in manager.providers
        assert manager.provider_order == ["qwen", "deepseek"]
        assert manager.current_provider_index == 0
    
    def test_load_configuration_file_not_found(self):
        """Test configuration loading when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "nonexistent.json")
            manager = LLMConfigManager(config_path)
            
            # Should create default configuration
            assert os.path.exists(config_path)
            assert len(manager.providers) == 2
    
    def test_load_configuration_invalid_json(self):
        """Test configuration loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            with pytest.raises(LLMConfigurationError, match="Failed to load LLM configuration"):
                LLMConfigManager(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_configuration_invalid_provider_config(self):
        """Test configuration loading with invalid provider configuration."""
        config_data = {
            "providers": {
                "invalid": {
                    "provider_name": "invalid"
                    # Missing required fields
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(LLMConfigurationError, match="Invalid configuration for provider"):
                LLMConfigManager(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_get_provider_config(self, temp_config_file):
        """Test getting specific provider configuration."""
        manager = LLMConfigManager(temp_config_file)
        
        qwen_config = manager.get_provider_config("qwen")
        assert qwen_config is not None
        assert qwen_config.provider_name == "qwen"
        assert qwen_config.api_key == "test-qwen-key"
        
        nonexistent_config = manager.get_provider_config("nonexistent")
        assert nonexistent_config is None
    
    def test_get_current_provider(self, temp_config_file):
        """Test getting current active provider."""
        manager = LLMConfigManager(temp_config_file)
        
        current = manager.get_current_provider()
        assert current is not None
        assert current.provider_name == "qwen"  # First in order
    
    def test_switch_to_next_provider(self, temp_config_file):
        """Test switching to next provider."""
        manager = LLMConfigManager(temp_config_file)
        
        # Initially on first provider (qwen)
        assert manager.current_provider_index == 0
        assert manager.get_current_provider().provider_name == "qwen"
        
        # Switch to next provider
        manager._switch_to_next_provider()
        assert manager.current_provider_index == 1
        assert manager.get_current_provider().provider_name == "deepseek"
        
        # Switch again (should wrap around)
        manager._switch_to_next_provider()
        assert manager.current_provider_index == 0
        assert manager.get_current_provider().provider_name == "qwen"
    
    def test_create_api_client(self, temp_config_file):
        """Test API client creation."""
        manager = LLMConfigManager(temp_config_file)
        
        qwen_config = manager.get_provider_config("qwen")
        qwen_client = manager._create_api_client(qwen_config)
        assert isinstance(qwen_client, QwenAPIClient)
        
        deepseek_config = manager.get_provider_config("deepseek")
        deepseek_client = manager._create_api_client(deepseek_config)
        assert isinstance(deepseek_client, DeepSeekAPIClient)
    
    def test_create_api_client_unsupported_provider(self, temp_config_file):
        """Test API client creation with unsupported provider."""
        manager = LLMConfigManager(temp_config_file)
        
        unsupported_config = LLMConfig(
            provider_name="unsupported",
            api_endpoint="https://api.unsupported.com",
            api_key="test-key",
            model_name="test-model"
        )
        
        with pytest.raises(LLMConfigurationError, match="Unsupported provider"):
            manager._create_api_client(unsupported_config)
    
    @pytest.mark.asyncio
    async def test_generate_text_with_failover_success(self, temp_config_file):
        """Test successful text generation with first provider."""
        manager = LLMConfigManager(temp_config_file)
        
        with patch.object(manager, '_generate_with_retry') as mock_generate:
            mock_generate.return_value = "Generated content"
            
            result = await manager.generate_text_with_failover("Test prompt")
            
            assert result == "Generated content"
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_with_failover_switch_provider(self, temp_config_file):
        """Test failover to second provider when first fails."""
        manager = LLMConfigManager(temp_config_file)
        
        with patch.object(manager, '_generate_with_retry') as mock_generate:
            # First call fails, second succeeds
            mock_generate.side_effect = [
                LLMProviderError("First provider failed"),
                "Generated content"
            ]
            
            result = await manager.generate_text_with_failover("Test prompt")
            
            assert result == "Generated content"
            assert mock_generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_text_with_failover_all_providers_fail(self, temp_config_file):
        """Test when all providers fail."""
        manager = LLMConfigManager(temp_config_file)
        
        with patch.object(manager, '_generate_with_retry') as mock_generate:
            mock_generate.side_effect = LLMProviderError("Provider failed")
            
            with pytest.raises(LLMProviderError, match="All LLM providers failed"):
                await manager.generate_text_with_failover("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_with_retry_success(self, temp_config_file):
        """Test successful generation with retry mechanism."""
        manager = LLMConfigManager(temp_config_file)
        config = manager.get_provider_config("qwen")
        
        with patch.object(manager, '_create_api_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_client.generate_text.return_value = "Generated content"
            mock_create_client.return_value.__aenter__.return_value = mock_client
            
            result = await manager._generate_with_retry(config, "Test prompt", "System prompt")
            
            assert result == "Generated content"
            mock_client.generate_text.assert_called_once_with("Test prompt", "System prompt")
    
    @pytest.mark.asyncio
    async def test_generate_with_retry_exhausted(self, temp_config_file):
        """Test retry mechanism when all attempts fail."""
        manager = LLMConfigManager(temp_config_file)
        config = manager.get_provider_config("qwen")
        config.retry_attempts = 2  # Reduce for faster testing
        
        with patch.object(manager, '_create_api_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_client.generate_text.side_effect = LLMProviderError("API error")
            mock_create_client.return_value.__aenter__.return_value = mock_client
            
            with patch('asyncio.sleep') as mock_sleep:  # Speed up test
                with pytest.raises(LLMProviderError, match="failed after 2 attempts"):
                    await manager._generate_with_retry(config, "Test prompt", "System prompt")
                
                # Should have attempted retries
                assert mock_sleep.call_count == 1  # One retry delay
    
    def test_get_provider_status(self, temp_config_file):
        """Test getting provider status information."""
        manager = LLMConfigManager(temp_config_file)
        
        status = manager.get_provider_status()
        
        assert status["providers"] == ["qwen", "deepseek"]
        assert status["current_provider"] == "qwen"
        assert status["total_providers"] == 2
    
    def test_reload_configuration(self, temp_config_file):
        """Test configuration reloading."""
        manager = LLMConfigManager(temp_config_file)
        
        # Switch to second provider
        manager._switch_to_next_provider()
        assert manager.current_provider_index == 1
        
        # Reload configuration
        manager.reload_configuration()
        
        # Should reset to first provider
        assert manager.current_provider_index == 0
        assert len(manager.providers) == 2


if __name__ == "__main__":
    pytest.main([__file__])