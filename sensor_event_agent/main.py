"""
Main entry point for Sensor Event Translation Agent
传感器事件翻译Agent主程序

Usage:
    python main.py --message '{"sensor_type": "accelerometer", "x": 0.1, "y": 0.2, "z": 9.8}'
    python main.py --file messages.json
    python main.py --interactive
"""

import asyncio
import json
import argparse
import logging
import sys
from pathlib import Path
from typing import Union, Dict, Any

# Add core directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from core.sensor_event_agent import SensorEventAgent


def setup_logging(level=logging.INFO):
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(current_dir / 'sensor_agent.log', encoding='utf-8')
        ]
    )


async def process_single_message(agent: SensorEventAgent, message: Union[str, Dict[str, Any]]):
    """Process a single MQTT message."""
    print(f"\\n📥 处理消息: {json.dumps(message, ensure_ascii=False) if isinstance(message, dict) else message}")
    
    try:
        result = await agent.translate_sensor_event(message)
        
        if result["success"]:
            print(f"✅ 翻译成功!")
            print(f"   📝 描述: \"{result['description']}\"")
            print(f"   🔧 传感器类型: {result['sensor_type']}")
            print(f"   📊 事件类型: {result['event_type']}")
            print(f"   🕐 时间: {result['timestamp']}")
        else:
            print(f"❌ 翻译失败!")
            print(f"   📝 备用描述: \"{result['description']}\"")
            print(f"   ⚠️  错误: {result.get('error', '未知错误')}")
            
        return result
        
    except Exception as e:
        print(f"❌ 处理异常: {e}")
        return {"success": False, "error": str(e)}


def process_batch_messages_sync(agent: SensorEventAgent, messages: list):
    """Process multiple messages synchronously."""
    print(f"\\n🔄 批量处理 {len(messages)} 条消息...")
    
    results = agent.process_batch_messages(messages)
    
    print("\\n📊 批量处理结果:")
    print("-" * 40)
    
    success_count = 0
    for i, result in enumerate(results, 1):
        if result["success"]:
            print(f"{i:2d}. ✅ \"{result['description']}\" ({result.get('sensor_type', 'unknown')})")
            success_count += 1
        else:
            print(f"{i:2d}. ❌ 失败: {result.get('error', '未知错误')}")
    
    print(f"\\n📈 成功率: {success_count}/{len(messages)} ({success_count/len(messages)*100:.1f}%)")
    return results


async def interactive_mode(agent: SensorEventAgent):
    """Interactive mode for testing messages."""
    print("\\n🎮 进入交互模式 (输入 'quit' 或 'exit' 退出)")
    print("请输入MQTT JSON消息:")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\\n📥 消息> ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 退出交互模式")
                break
            
            if not user_input:
                continue
            
            # Try to parse as JSON
            try:
                message = json.loads(user_input)
            except json.JSONDecodeError:
                print("❌ 无效的JSON格式，请重新输入")
                continue
            
            await process_single_message(agent, message)
            
        except KeyboardInterrupt:
            print("\\n👋 用户中断，退出交互模式")
            break
        except Exception as e:
            print(f"❌ 交互模式错误: {e}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="传感器事件翻译Agent")
    parser.add_argument("--message", "-m", type=str, help="单个MQTT消息JSON字符串")
    parser.add_argument("--file", "-f", type=str, help="包含MQTT消息的JSON文件路径")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--batch", "-b", action="store_true", help="批量处理模式（同步）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    parser.add_argument("--config", "-c", type=str, help="自定义prompt配置文件路径")
    parser.add_argument("--llm-config", type=str, help="自定义LLM配置文件路径")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    print("🤖 传感器事件翻译Agent")
    print("=" * 50)
    
    # Initialize agent
    try:
        agent = SensorEventAgent(
            prompt_config_path=args.config,
            llm_config_path=args.llm_config
        )
        print("✅ Agent初始化成功")
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        return 1
    
    # Process based on arguments
    if args.interactive:
        await interactive_mode(agent)
        
    elif args.message:
        try:
            message = json.loads(args.message)
            await process_single_message(agent, message)
        except json.JSONDecodeError:
            print("❌ 无效的JSON消息格式")
            return 1
            
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ 文件不存在: {args.file}")
            return 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                messages = data
            elif isinstance(data, dict):
                messages = [data]
            else:
                print("❌ 文件格式错误，应为JSON对象或数组")
                return 1
            
            if args.batch:
                process_batch_messages_sync(agent, messages)
            else:
                # Process sequentially with async
                for i, message in enumerate(messages, 1):
                    print(f"\\n📍 消息 {i}/{len(messages)}")
                    await process_single_message(agent, message)
                    
        except Exception as e:
            print(f"❌ 文件处理错误: {e}")
            return 1
    
    else:
        # Default: show help and example
        print("\\n📋 使用示例:")
        print("-" * 20)
        print("1. 单条消息:")
        print('   python main.py -m \'{"sensor_type": "touch", "value": 1}\'')
        print("\\n2. 文件处理:")
        print("   python main.py -f messages.json")
        print("\\n3. 交互模式:")
        print("   python main.py -i")
        print("\\n4. 批量处理:")
        print("   python main.py -f messages.json --batch")
        
        # Show example message formats
        print("\\n📋 支持的消息格式:")
        example_formats = [
            {"sensor_type": "accelerometer", "x": 0.1, "y": 0.2, "z": 9.8, "count": 3},
            {"sensor_type": "touch", "value": 1, "duration": 2.5},
            {"sensor_type": "gesture", "gesture_type": "shake", "confidence": 0.9}
        ]
        
        for i, fmt in enumerate(example_formats, 1):
            print(f"   {i}. {json.dumps(fmt, ensure_ascii=False)}")
    
    print("\\n🎉 程序执行完成!")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n👋 用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ 程序异常: {e}")
        sys.exit(1)
