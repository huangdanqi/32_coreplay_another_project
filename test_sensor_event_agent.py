#!/usr/bin/env python3
"""
Comprehensive Test for Sensor Event Translation Agent
测试传感器事件翻译Agent的功能
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback

# Add sensor_event_agent to path
sensor_agent_path = Path(__file__).parent / "sensor_event_agent"
sys.path.append(str(sensor_agent_path))

try:
    from core.sensor_event_agent import SensorEventAgent
    from core.mqtt_handler import MQTTHandler
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're running from the correct directory")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SensorEventAgentTester:
    """Test class for Sensor Event Agent."""
    
    def __init__(self):
        """Initialize tester."""
        self.agent = None
        self.mqtt_handler = MQTTHandler()
        self.test_results = []
        self.start_time = datetime.now()
    
    async def initialize_agent(self):
        """Initialize the sensor event agent."""
        try:
            print("🔧 初始化传感器事件翻译Agent...")
            self.agent = SensorEventAgent()
            print("✅ Agent初始化成功")
            return True
        except Exception as e:
            print(f"❌ Agent初始化失败: {e}")
            traceback.print_exc()
            return False
    
    def log_test_result(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    async def test_mqtt_handler(self):
        """Test MQTT message handler functionality."""
        print("\\n🧪 测试MQTT消息处理器...")
        
        test_messages = [
            # Valid messages
            {
                "sensor_type": "accelerometer",
                "x": 0.1, "y": 0.2, "z": 9.8,
                "count": 3,
                "device_id": "toy_001"
            },
            {
                "type": "touch",
                "data": 1,
                "id": "toy_002"
            },
            # Invalid messages
            {},
            {"invalid": "data"}
        ]
        
        for i, message in enumerate(test_messages, 1):
            try:
                is_valid = self.mqtt_handler.validate_message(message)
                if i <= 2:  # First two should be valid
                    if is_valid:
                        self.log_test_result(f"MQTT验证测试{i}", True, "消息格式有效")
                        # Test parsing
                        parsed = self.mqtt_handler.parse_mqtt_message(message)
                        if parsed.get("sensor_data", {}).get("type"):
                            self.log_test_result(f"MQTT解析测试{i}", True, f"解析成功: {parsed['sensor_data']['type']}")
                        else:
                            self.log_test_result(f"MQTT解析测试{i}", False, "解析结果缺少传感器类型")
                    else:
                        self.log_test_result(f"MQTT验证测试{i}", False, "有效消息被错误拒绝")
                else:  # Last two should be invalid
                    if not is_valid:
                        self.log_test_result(f"MQTT验证测试{i}", True, "正确识别无效消息")
                    else:
                        self.log_test_result(f"MQTT验证测试{i}", False, "无效消息被错误接受")
            except Exception as e:
                self.log_test_result(f"MQTT测试{i}", False, f"异常: {str(e)}")
    
    async def test_single_message_translation(self):
        """Test single message translation."""
        print("\\n🧪 测试单条消息翻译...")
        
        test_cases = [
            {
                "name": "加速度计摇动",
                "message": {
                    "sensor_type": "accelerometer",
                    "x": 0.2, "y": 0.1, "z": 9.8,
                    "count": 3,
                    "device_id": "toy_001"
                },
                "expected_keywords": ["摇", "3"]
            },
            {
                "name": "触摸传感器",
                "message": {
                    "sensor_type": "touch",
                    "value": 1,
                    "duration": 2.5,
                    "device_id": "toy_001"
                },
                "expected_keywords": ["触摸", "触"]
            },
            {
                "name": "陀螺仪旋转",
                "message": {
                    "sensor_type": "gyroscope",
                    "yaw": 90,
                    "speed": "fast",
                    "device_id": "toy_001"
                },
                "expected_keywords": ["转", "身"]
            },
            {
                "name": "手势识别",
                "message": {
                    "sensor_type": "gesture",
                    "gesture_type": "shake",
                    "confidence": 0.9,
                    "count": 2,
                    "device_id": "toy_001"
                },
                "expected_keywords": ["摇", "头", "手势"]
            },
            {
                "name": "声音传感器",
                "message": {
                    "sensor_type": "sound",
                    "decibel": 65,
                    "frequency": 1000,
                    "device_id": "toy_001"
                },
                "expected_keywords": ["声音", "发出"]
            }
        ]
        
        for test_case in test_cases:
            try:
                result = await self.agent.translate_sensor_event(test_case["message"])
                
                if result["success"]:
                    description = result["description"]
                    
                    # Check length constraint
                    if len(description) <= 20:
                        length_ok = True
                    else:
                        length_ok = False
                    
                    # Check if contains expected keywords
                    keyword_found = any(
                        any(keyword in description for keyword in keywords) 
                        for keywords in [test_case["expected_keywords"]]
                    )
                    
                    if length_ok and keyword_found:
                        self.log_test_result(
                            test_case["name"], 
                            True, 
                            f"翻译成功: '{description}' (长度: {len(description)})",
                            {"result": result}
                        )
                    else:
                        issues = []
                        if not length_ok:
                            issues.append(f"长度超限({len(description)}>20)")
                        if not keyword_found:
                            issues.append("缺少关键词")
                        
                        self.log_test_result(
                            test_case["name"], 
                            False, 
                            f"翻译有问题: '{description}' - {', '.join(issues)}",
                            {"result": result}
                        )
                else:
                    self.log_test_result(
                        test_case["name"], 
                        False, 
                        f"翻译失败: {result.get('error', '未知错误')}",
                        {"result": result}
                    )
            
            except Exception as e:
                self.log_test_result(test_case["name"], False, f"异常: {str(e)}")
                traceback.print_exc()
    
    def test_batch_processing(self):
        """Test batch message processing (synchronous)."""
        print("\\n🧪 测试批量消息处理...")
        
        batch_messages = [
            {"sensor_type": "accelerometer", "x": 0.1, "count": 1},
            {"sensor_type": "touch", "value": 1},
            {"sensor_type": "sound", "decibel": 50},
            {"sensor_type": "light", "lux": 300},
            {"sensor_type": "temperature", "temperature": 25.5}
        ]
        
        try:
            results = self.agent.process_batch_messages(batch_messages)
            
            success_count = sum(1 for r in results if r["success"])
            total_count = len(results)
            
            if success_count >= total_count * 0.8:  # At least 80% success rate
                self.log_test_result(
                    "批量处理", 
                    True, 
                    f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)",
                    {"results": results}
                )
            else:
                self.log_test_result(
                    "批量处理", 
                    False, 
                    f"成功率过低: {success_count}/{total_count}",
                    {"results": results}
                )
        
        except Exception as e:
            self.log_test_result("批量处理", False, f"异常: {str(e)}")
    
    async def test_error_handling(self):
        """Test error handling with invalid inputs."""
        print("\\n🧪 测试错误处理...")
        
        invalid_inputs = [
            # Malformed JSON
            '{"sensor_type": "invalid", "missing_bracket"',
            # Empty message
            {},
            # Missing required fields
            {"device_id": "toy_001"},
            # Invalid sensor type with no data
            {"sensor_type": "unknown_sensor"},
        ]
        
        for i, invalid_input in enumerate(invalid_inputs, 1):
            try:
                result = await self.agent.translate_sensor_event(invalid_input)
                
                # Should not succeed but should handle gracefully
                if not result["success"] and result.get("description"):
                    self.log_test_result(
                        f"错误处理{i}", 
                        True, 
                        f"正确处理错误，提供备用描述: '{result['description']}'",
                        {"result": result}
                    )
                else:
                    self.log_test_result(
                        f"错误处理{i}", 
                        False, 
                        f"错误处理不当: {result}",
                        {"result": result}
                    )
            
            except Exception as e:
                # Should not raise exceptions
                self.log_test_result(f"错误处理{i}", False, f"抛出异常: {str(e)}")
    
    async def test_performance(self):
        """Test performance with multiple messages."""
        print("\\n🧪 测试性能...")
        
        # Create 10 test messages
        test_messages = []
        for i in range(10):
            test_messages.append({
                "sensor_type": "accelerometer",
                "x": 0.1 * i,
                "y": 0.2 * i,
                "z": 9.8,
                "count": i + 1,
                "device_id": f"toy_{i:03d}"
            })
        
        start_time = datetime.now()
        
        try:
            # Test async processing
            tasks = [self.agent.translate_sensor_event(msg) for msg in test_messages]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            avg_time = duration / len(test_messages)
            
            if avg_time < 5.0 and success_count >= 8:  # Average under 5 seconds, at least 80% success
                self.log_test_result(
                    "性能测试", 
                    True, 
                    f"处理{len(test_messages)}条消息用时{duration:.2f}秒，平均{avg_time:.2f}秒/条，成功{success_count}条",
                    {"duration": duration, "success_rate": success_count/len(test_messages)}
                )
            else:
                self.log_test_result(
                    "性能测试", 
                    False, 
                    f"性能不达标: 用时{duration:.2f}秒，成功{success_count}条",
                    {"duration": duration, "success_rate": success_count/len(test_messages)}
                )
        
        except Exception as e:
            self.log_test_result("性能测试", False, f"异常: {str(e)}")
    
    def generate_report(self):
        """Generate test report."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print("\\n" + "="*60)
        print("🧪 传感器事件翻译Agent测试报告")
        print("="*60)
        print(f"📊 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过: {passed_tests} ✅")
        print(f"   失败: {failed_tests} ❌")
        print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
        print(f"   总用时: {total_duration:.2f}秒")
        
        if failed_tests > 0:
            print(f"\\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test_name']}: {result['message']}")
        
        # Save detailed report
        report_file = Path("sensor_event_agent_test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100,
                    "duration": total_duration,
                    "timestamp": self.start_time.isoformat()
                },
                "test_results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\\n📄 详细报告已保存到: {report_file}")
        
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 开始传感器事件翻译Agent测试")
        print("="*60)
        
        # Initialize agent
        if not await self.initialize_agent():
            return False
        
        # Run tests
        await self.test_mqtt_handler()
        await self.test_single_message_translation()
        self.test_batch_processing()
        await self.test_error_handling()
        await self.test_performance()
        
        # Generate report
        return self.generate_report()


async def main():
    """Main test function."""
    tester = SensorEventAgentTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\\n🎉 所有测试通过！")
            return 0
        else:
            print("\\n⚠️ 部分测试失败，请检查详细报告")
            return 1
    
    except Exception as e:
        print(f"\\n💥 测试过程中出现严重错误: {e}")
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n👋 测试被用户中断")
        sys.exit(0)
