"""
Test script to verify Ollama connection and Qwen3 model availability.
Run this to make sure your local Ollama setup is working before running the diary agent.
"""

import asyncio
import aiohttp
import json


async def test_ollama_connection():
    """Test if Ollama is running and Qwen3 model is available."""
    
    print("🔍 Testing Ollama Connection...")
    
    # Test 1: Check if Ollama is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    print("✅ Ollama is running!")
                    print(f"📋 Available models: {len(models.get('models', []))}")
                    
                    # Check if qwen3 is available
                    model_names = [model['name'] for model in models.get('models', [])]
                    print(f"🔍 Models found: {model_names}")
                    
                    if any('qwen3' in name.lower() for name in model_names):
                        print("✅ Qwen3 model found!")
                    else:
                        print("❌ Qwen3 model not found. Available models:")
                        for model in models.get('models', []):
                            print(f"   - {model['name']}")
                        print("\n💡 To install Qwen3, run: ollama pull qwen3")
                        return False
                else:
                    print(f"❌ Ollama API returned status {response.status}")
                    return False
                    
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to Ollama. Is it running?")
        print("💡 Start Ollama with: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False
    
    # Test 2: Try generating text with Qwen3
    print("\n🧪 Testing text generation with Qwen3...")
    
    try:
        payload = {
            "model": "qwen3:4b",
            "prompt": "你好，请用中文回答：今天天气很好。请写一句简短的日记。",
            "options": {
                "num_predict": 50,
                "temperature": 0.7
            },
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                headers={"Content-Type": "application/json"},
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    generated_text = result.get("response", "").strip()
                    print(f"✅ Text generation successful!")
                    print(f"📝 Generated: {generated_text}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Text generation failed: {response.status}")
                    print(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error during text generation: {e}")
        return False


async def test_diary_agent_llm_config():
    """Test the diary agent LLM configuration."""
    
    print("\n🔧 Testing Diary Agent LLM Configuration...")
    
    try:
        from diary_agent.core.llm_manager import LLMConfigManager
        
        # Initialize LLM manager
        llm_manager = LLMConfigManager()
        
        # Check if ollama_qwen3 provider is configured
        ollama_config = llm_manager.get_provider_config("ollama_qwen3")
        if ollama_config:
            print("✅ Ollama Qwen3 provider configured!")
            print(f"   Endpoint: {ollama_config.api_endpoint}")
            print(f"   Model: {ollama_config.model_name}")
        else:
            print("❌ Ollama Qwen3 provider not found in configuration")
            return False
        
        # Test text generation through LLM manager
        print("\n🧪 Testing text generation through LLM manager...")
        
        test_prompt = "今天是晴天，心情很好。请写一句简短的日记。"
        system_prompt = "你是一个日记助手，请用中文写简短的日记内容，不超过35个字符。"
        
        generated_text = await llm_manager.generate_text_with_failover(
            prompt=test_prompt,
            system_prompt=system_prompt
        )
        
        print(f"✅ LLM Manager text generation successful!")
        print(f"📝 Generated: {generated_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM manager: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    
    print("🎯 OLLAMA CONNECTION TEST")
    print("=" * 50)
    
    # Test Ollama connection
    ollama_ok = await test_ollama_connection()
    
    if ollama_ok:
        # Test diary agent configuration
        config_ok = await test_diary_agent_llm_config()
        
        if config_ok:
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED!")
            print("✅ Ollama is working")
            print("✅ Qwen3 model is available") 
            print("✅ Diary agent LLM configuration is correct")
            print("\n🚀 You can now run: python diary_agent_api_example.py")
        else:
            print("\n❌ LLM configuration test failed")
    else:
        print("\n❌ Ollama connection test failed")
        print("\n🔧 Setup steps:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Start Ollama: ollama serve")
        print("3. Install Qwen3: ollama pull qwen3")


if __name__ == "__main__":
    asyncio.run(main())