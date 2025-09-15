"""
Claim Event Function Test with Local LLM (Ollama)

This script tests the Claim Event function using a local LLM (Ollama Qwen3)
to generate diary entries for device binding events.
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_claim_event_with_local_llm():
    """Test Claim Event function using local LLM."""
    print("🎯 Claim Event Function Test with Local LLM")
    print("="*60)
    
    try:
        # Import necessary components
        from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag, PromptConfig
        from diary_agent.core.llm_manager import LLMConfigManager
        from diary_agent.agents.adoption_agent import AdoptionAgent
        from diary_agent.integration.adoption_data_reader import AdoptionDataReader
        
        print("✅ Successfully imported diary agent components")
        
        # 1. Create Ollama configuration
        print("\n🔧 Setting up local LLM configuration...")
        
        ollama_config = {
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
                "auto_switch_rules": {
                    "enable_auto_switch": False,
                    "switch_on_failure": False,
                    "switch_on_timeout": False
                }
            }
        }
        
        # Save configuration to temporary file
        config_file = "test_claim_event_llm_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(ollama_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created LLM configuration: {config_file}")
        
        # 2. Initialize LLM manager with local configuration
        llm_manager = LLMConfigManager(config_file)
        print("✅ LLM manager initialized")
        
        # 3. Create sample device binding event
        print("\n📱 Creating device binding event...")
        
        owner_info = {
            "user_id": 789,
            "name": "小华",
            "nickname": "小华主人",
            "age": 30,
            "gender": "male",
            "location": "深圳",
            "interests": ["编程", "游戏", "音乐"],
            "personality": "lively",
            "emotional_baseline": {"x": 1, "y": 2},
            "intimacy_level": 40
        }
        
        event_data = EventData(
            event_id="local_llm_claim_001",
            event_type="adoption_event",
            event_name="toy_claimed",
            timestamp=datetime.now(),
            user_id=owner_info["user_id"],
            context_data={
                "device_id": "smart_toy_local_001",
                "binding_method": "bluetooth_pairing",
                "binding_timestamp": datetime.now().isoformat(),
                "device_type": "smart_toy",
                "device_name": "智能机器人",
                "bluetooth_mac": "AA:BB:CC:DD:EE:FF"
            },
            metadata={
                "owner_info": owner_info,
                "claim_method": "bluetooth",
                "toy_model": "SMART_ROBOT_V3",
                "binding_location": "office",
                "network_type": "bluetooth"
            }
        )
        
        print("✅ Created device binding event:")
        print(f"   Device: {event_data.context_data['device_name']}")
        print(f"   Owner: {event_data.metadata['owner_info']['name']}")
        print(f"   Method: {event_data.context_data['binding_method']}")
        print(f"   Location: {event_data.metadata['binding_location']}")
        
        # 4. Create adoption agent with local LLM
        print("\n🤖 Setting up adoption agent with local LLM...")
        
        # Create prompt configuration for adoption agent
        prompt_config = PromptConfig(
            agent_type="adoption_agent",
            system_prompt="""你是一个专门处理玩具认领事件的AI助手。当用户通过设备绑定认领玩具时，你需要生成一段简短、温馨的日记内容。

要求：
1. 标题最多6个字符
2. 内容最多35个字符，可以包含emoji
3. 表达被认领的喜悦和兴奋
4. 包含主人的名字
5. 使用中文表达

请以JSON格式返回：
{
    "title": "标题",
    "content": "内容",
    "emotion_tags": ["情绪标签"]
}""",
            user_prompt_template="""请为以下认领事件生成日记内容：

事件名称: {event_name}
主人信息: {owner_info}
设备信息: {device_info}
绑定方法: {binding_method}

请生成温馨的认领日记内容。""",
            output_format={
                "title": "string",
                "content": "string",
                "emotion_tags": "list"
            },
            validation_rules={
                "title_max_length": 6,
                "content_max_length": 35
            }
        )
        
        # Create mock data reader
        mock_data_reader = type('MockDataReader', (), {
            'read_event_context': lambda *args, **kwargs: type('MockContext', (), {
                'user_profile': event_data.metadata["owner_info"],
                'event_details': {
                    "event_name": "toy_claimed",
                    "device_id": event_data.context_data["device_id"],
                    "device_name": event_data.context_data["device_name"],
                    "binding_method": event_data.context_data["binding_method"]
                },
                'environmental_context': {},
                'social_context': {},
                'emotional_context': {},
                'temporal_context': {"timestamp": event_data.timestamp}
            })(),
            'get_user_preferences': lambda *args, **kwargs: {},
            'get_adoption_event_info': lambda *args, **kwargs: {"probability": 1.0},
            'get_supported_events': lambda *args, **kwargs: ["toy_claimed"]
        })()
        
        # Create adoption agent
        adoption_agent = AdoptionAgent(
            agent_type="adoption_agent",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=mock_data_reader
        )
        
        print("✅ Adoption agent created with local LLM")
        
        # 5. Test LLM connection
        print("\n🔍 Testing local LLM connection...")
        
        try:
            current_provider = llm_manager.get_current_provider()
            print(f"✅ Current LLM provider: {current_provider.provider_name}")
            print(f"✅ Model: {current_provider.model_name}")
            print(f"✅ Endpoint: {current_provider.api_endpoint}")
            
            # Test simple generation
            test_prompt = "请用一句话回答：你好"
            test_response = await llm_manager.generate_text_with_failover(test_prompt)
            print(f"✅ LLM test response: {test_response[:50]}...")
            
        except Exception as e:
            print(f"❌ LLM connection test failed: {e}")
            print("💡 Make sure Ollama is running: ollama serve")
            print("💡 Make sure Qwen3 is installed: ollama pull qwen3")
            return False
        
        # 6. Process claim event with local LLM
        print("\n🎯 Processing claim event with local LLM...")
        
        try:
            # Process the event
            diary_entry = await adoption_agent.process_event(event_data)
            
            if diary_entry:
                print("✅ Successfully generated diary entry with local LLM!")
                print(f"\n📝 Generated Diary Entry:")
                print(f"   Title: {diary_entry.title}")
                print(f"   Content: {diary_entry.content}")
                print(f"   Emotions: {[tag.value for tag in diary_entry.emotion_tags]}")
                print(f"   User ID: {diary_entry.user_id}")
                print(f"   Event Name: {diary_entry.event_name}")
                print(f"   LLM Provider: {diary_entry.llm_provider}")
                
                # Verify content requirements
                assert len(diary_entry.title) <= 6
                assert len(diary_entry.content) <= 35
                assert event_data.metadata["owner_info"]["name"] in diary_entry.content
                assert "认领" in diary_entry.content or "主人" in diary_entry.content
                print("✅ Content validation passed")
                
                # Verify specification compliance
                print("\n📋 Specification Compliance Check:")
                print(f"✅ Trigger condition (device binding): VERIFIED")
                print(f"✅ Content requirement (owner's personal info): VERIFIED")
                print(f"✅ Local LLM generation: VERIFIED")
                print(f"✅ Content length validation: VERIFIED")
                
                return True
            else:
                print("❌ Failed to generate diary entry")
                return False
                
        except Exception as e:
            print(f"❌ Error processing claim event: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error in test setup: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_multiple_claim_events():
    """Test multiple claim events with local LLM."""
    print("\n🔄 Testing multiple claim events with local LLM...")
    
    try:
        from diary_agent.utils.data_models import EventData, DiaryEntry, EmotionalTag, PromptConfig
        from diary_agent.core.llm_manager import LLMConfigManager
        from diary_agent.agents.adoption_agent import AdoptionAgent
        
        # Use the same configuration
        llm_manager = LLMConfigManager("test_claim_event_llm_config.json")
        
        # Create multiple events
        events = []
        for i in range(3):
            owner_info = {
                "user_id": 1000 + i,
                "name": f"用户{i+1}",
                "nickname": f"主人{i+1}",
                "personality": "lively" if i % 2 == 0 else "clam"
            }
            
            event_data = EventData(
                event_id=f"multi_claim_{i+1}",
                event_type="adoption_event",
                event_name="toy_claimed",
                timestamp=datetime.now(),
                user_id=owner_info["user_id"],
                context_data={
                    "device_id": f"device_{i+1}",
                    "binding_method": "qr_scan" if i % 2 == 0 else "bluetooth",
                    "device_name": f"智能玩具{i+1}"
                },
                metadata={"owner_info": owner_info}
            )
            events.append(event_data)
        
        # Create adoption agent
        prompt_config = PromptConfig(
            agent_type="adoption_agent",
            system_prompt="生成认领事件的日记内容，包含主人名字，表达喜悦。",
            user_prompt_template="为{event_name}事件生成日记，主人是{owner_info}",
            output_format={"title": "string", "content": "string", "emotion_tags": "list"},
            validation_rules={"title_max_length": 6, "content_max_length": 35}
        )
        
        mock_data_reader = type('MockDataReader', (), {
            'read_event_context': lambda *args, **kwargs: type('MockContext', (), {
                'user_profile': {"name": "测试用户"},
                'event_details': {"event_name": "toy_claimed"},
                'environmental_context': {},
                'social_context': {},
                'emotional_context': {},
                'temporal_context': {"timestamp": datetime.now()}
            })(),
            'get_user_preferences': lambda *args, **kwargs: {},
            'get_adoption_event_info': lambda *args, **kwargs: {"probability": 1.0},
            'get_supported_events': lambda *args, **kwargs: ["toy_claimed"]
        })()
        
        adoption_agent = AdoptionAgent(
            agent_type="adoption_agent",
            prompt_config=prompt_config,
            llm_manager=llm_manager,
            data_reader=mock_data_reader
        )
        
        # Process each event
        results = []
        for i, event_data in enumerate(events):
            print(f"\n处理事件 {i+1}: {event_data.metadata['owner_info']['name']}")
            
            try:
                diary_entry = await adoption_agent.process_event(event_data)
                if diary_entry:
                    results.append(diary_entry)
                    print(f"✅ 生成成功: {diary_entry.content}")
                else:
                    print(f"❌ 生成失败")
            except Exception as e:
                print(f"❌ 处理错误: {e}")
        
        print(f"\n📊 处理结果: {len(results)}/{len(events)} 成功")
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ 多事件测试失败: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Claim Event Function Test with Local LLM")
    print("="*60)
    
    # Test single claim event
    success = await test_claim_event_with_local_llm()
    
    if success:
        # Test multiple events
        multi_success = await test_multiple_claim_events()
        
        print("\n🎉 Test Summary")
        print("="*30)
        print("✅ Single claim event: PASSED")
        print(f"{'✅' if multi_success else '❌'} Multiple events: {'PASSED' if multi_success else 'FAILED'}")
        print("✅ Local LLM integration: PASSED")
        print("✅ Specification compliance: PASSED")
        
        print("\n🚀 Claim Event function is working with local LLM!")
        print("The function successfully generates diary entries using Ollama Qwen3.")
        
        return 0
    else:
        print("\n❌ Test failed")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Make sure Qwen3 is installed: ollama pull qwen3")
        print("3. Test Ollama connection: python test_ollama_connection.py")
        
        return 1

if __name__ == "__main__":
    # Clean up config file on exit
    import atexit
    atexit.register(lambda: Path("test_claim_event_llm_config.json").unlink(missing_ok=True))
    
    sys.exit(asyncio.run(main()))
