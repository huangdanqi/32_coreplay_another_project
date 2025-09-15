"""
Sensor Event Translation Agent
Translates sensor MQTT messages into human-readable descriptions.
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Union
from datetime import datetime

# Add the diary_agent path to import LLM manager
current_dir = Path(__file__).parent.parent
parent_dir = current_dir.parent
diary_agent_path = parent_dir / "diary_agent"
sys.path.append(str(diary_agent_path))
sys.path.append(str(parent_dir))

try:
    from core.llm_manager import LLMConfigManager
except ImportError:
    try:
        from diary_agent.core.llm_manager import LLMConfigManager
    except ImportError as e:
        print(f"Failed to import LLMConfigManager: {e}")
        print(f"Diary agent path: {diary_agent_path}")
        print(f"Parent dir: {parent_dir}")
        raise

from .mqtt_handler import MQTTHandler


class SensorEventAgent:
    """
    Agent for translating sensor events to human language.
    Uses LLM to convert technical sensor data into natural language descriptions.
    """
    
    def __init__(self, 
                 prompt_config_path: str = None,
                 llm_config_path: str = None):
        """
        Initialize Sensor Event Agent.
        
        Args:
            prompt_config_path: Path to prompt configuration file
            llm_config_path: Path to LLM configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default paths
        if prompt_config_path is None:
            prompt_config_path = current_dir / "config" / "prompt.json"
        if llm_config_path is None:
            llm_config_path = parent_dir / "config" / "llm_configuration.json"
        
        # Load configurations
        self.prompt_config = self._load_prompt_config(prompt_config_path)
        
        # Initialize components
        self.llm_manager = LLMConfigManager(config_path=str(llm_config_path))
        self.mqtt_handler = MQTTHandler()
        
        self.logger.info("SensorEventAgent initialized successfully")
    
    def _load_prompt_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load prompt configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Loaded prompt configuration from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load prompt configuration: {e}")
            raise ValueError(f"Cannot load prompt config: {e}")
    
    async def translate_sensor_event(self, mqtt_message: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Translate sensor event from MQTT message to human language.
        
        Args:
            mqtt_message: MQTT message as JSON string or dictionary
            
        Returns:
            Dictionary with translation result
        """
        try:
            self.logger.info("Starting sensor event translation")
            
            # Validate MQTT message
            if not self.mqtt_handler.validate_message(mqtt_message):
                raise ValueError("Invalid MQTT message format")
            
            # Parse MQTT message
            parsed_data = self.mqtt_handler.parse_mqtt_message(mqtt_message)
            
            # Generate human language description using LLM
            description = await self._generate_description(parsed_data)
            
            # Validate result
            validated_description = self._validate_description(description)
            
            result = {
                "description": validated_description,
                "timestamp": datetime.now().isoformat(),
                "sensor_type": parsed_data["sensor_data"]["type"],
                "event_type": parsed_data["event_type"],
                "success": True
            }
            
            self.logger.info(f"Successfully translated sensor event: {validated_description}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error translating sensor event: {e}")
            return {
                "description": "检测到传感器活动",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
    
    async def _generate_description(self, parsed_data: Dict[str, Any]) -> str:
        """Generate human language description using LLM."""
        # Prepare prompt
        user_prompt = self._prepare_prompt(parsed_data)
        system_prompt = self.prompt_config["system_prompt"]
        
        try:
            # Generate description using LLM
            generated_text = await self.llm_manager.generate_text_with_failover(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            # Clean up the generated text
            clean_text = generated_text.strip()
            
            # Remove <think> tags and extract actual response
            if clean_text.startswith('<think>'):
                thinking_parts = clean_text.split('\n')
                # Look for JSON-like fragments with "description":
                for line in thinking_parts:
                    if '"description"' in line:
                        json_start = line.find('{')
                        json_end = line.rfind('}')
                        if json_start != -1 and json_end != -1 and json_end > json_start:
                            clean_text = line[json_start:json_end+1]
                            break
            
            # Try various extraction methods
            try:
                # Try parsing as JSON
                response = json.loads(clean_text)
                description = response.get("description", "").strip()
                if description:
                    return description
            except json.JSONDecodeError:
                pass
            
            # Look for description pattern
            if '"description"' in clean_text:
                try:
                    description_part = clean_text.split('"description"')[1]
                    if ':' in description_part:
                        value_part = description_part.split(':', 1)[1].strip()
                        # Remove quotes and commas
                        value_part = value_part.strip(',').strip().strip('"').strip("'").strip()
                        if value_part:
                            return value_part
                except Exception:
                    pass
            
            # Look for direct Chinese text
            chinese_parts = []
            for char in clean_text:
                if '\u4e00' <= char <= '\u9fff':  # Check if character is Chinese
                    chinese_parts.append(char)
            
            if chinese_parts:
                # Join Chinese characters and take first 20
                chinese_text = ''.join(chinese_parts)[:20]
                if chinese_text:
                    return chinese_text
            
            # Fallback to sensor-specific cute descriptions
            sensor_type = parsed_data["sensor_data"].get("type", "").lower()
            count = parsed_data["sensor_data"].get("count", 1)
            
            if "accelerometer" in sensor_type and count > 1:
                return f"小身体晃了{count}下~"
            elif "touch" in sensor_type:
                return "被温柔地抚摸着"
            elif "gyroscope" in sensor_type:
                return "转了个大圈圈"
            
            # If all else fails, use general fallback
            return self._generate_fallback_description(parsed_data)
            
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback_description(parsed_data)
    
    def _prepare_prompt(self, parsed_data: Dict[str, Any]) -> str:
        """Prepare prompt for LLM generation."""
        template = self.prompt_config["user_prompt_template"]
        
        # Format template with parsed data
        formatted_prompt = template.format(
            mqtt_message=parsed_data["mqtt_message"],
            sensor_data=json.dumps(parsed_data["sensor_data"], ensure_ascii=False),
            event_type=parsed_data["event_type"],
            timestamp=parsed_data["timestamp"],
            device_info=json.dumps(parsed_data["device_info"], ensure_ascii=False)
        )
        
        return formatted_prompt
    
    def _generate_fallback_description(self, parsed_data: Dict[str, Any]) -> str:
        """Generate cute and interesting fallback description when LLM fails."""
        sensor_data = parsed_data["sensor_data"]
        sensor_type = sensor_data.get("type", "unknown").lower()
        count = sensor_data.get("count", 1)
        intensity = sensor_data.get("intensity", "medium")
        
        # Cute rule-based translation with emojis and adorable language
        if "accelerometer" in sensor_type or "motion" in sensor_type:
            if count > 1:
                return f"小身体晃了{count}下~"
            else:
                intensity_map = {"strong": "用力", "medium": "轻快地", "light": "轻轻", "very_light": "微微"}
                return f"{intensity_map.get(intensity, '轻快地')}摇摆"
        
        elif "touch" in sensor_type:
            duration = sensor_data.get("duration", 0)
            if duration > 2:
                return "被温柔地抚摸着"
            else:
                return "被轻轻碰了一下"
        
        elif "sound" in sensor_type:
            decibel = sensor_data.get("decibel", 0)
            if decibel > 70:
                return "大声叫了一声"
            elif decibel > 40:
                return "轻声嘟囔了一下"
            else:
                return "发出微弱的声音"
        
        elif "light" in sensor_type:
            lux = sensor_data.get("lux", 0)
            if lux > 500:
                return "感受到明亮阳光"
            elif lux > 100:
                return "看到了温和光线"
            else:
                return "察觉到微弱亮光"
        
        elif "temperature" in sensor_type:
            temp = sensor_data.get("temperature", 0)
            if temp > 30:
                return "感觉热热的呢"
            elif temp < 10:
                return "有点凉飕飕的"
            else:
                return "温度刚刚好"
        
        elif "gyroscope" in sensor_type:
            yaw = sensor_data.get("yaw", 0)
            if abs(yaw) > 45:
                return "转了个大圈圈"
            else:
                return "轻轻转了转身"
        
        elif "gesture" in sensor_type:
            gesture_type = sensor_data.get("gesture_type", "unknown")
            confidence = sensor_data.get("confidence", 0)
            
            if "shake" in gesture_type.lower():
                if confidence > 0.8:
                    return "使劲摇头晃脑"
                else:
                    return "轻轻摇摆脑袋"
            elif "nod" in gesture_type.lower():
                return "认真地点点头"
            elif "wave" in gesture_type.lower():
                return "挥挥小手打招呼"
            else:
                return "做了个可爱手势"
        
        elif "proximity" in sensor_type:
            return "感受到有人靠近"
        
        elif "vibration" in sensor_type:
            return "感受到轻微震动"
        
        elif "pressure" in sensor_type:
            return "感受到压力变化"
        
        elif "humidity" in sensor_type:
            return "感受到湿度变化"
        
        else:
            return "在默默感受着周围"
    
    def _validate_description(self, description: str) -> str:
        """Validate and clean description."""
        # Remove quotes and extra whitespace
        description = description.strip().strip('"').strip("'")
        
        # Check length (max 20 characters)
        max_length = self.prompt_config.get("validation_rules", {}).get("max_length", 20)
        if len(description) > max_length:
            description = description[:max_length]
        
        # Ensure non-empty
        if not description:
            description = "检测到活动"
        
        return description
    
    def process_batch_messages(self, mqtt_messages: list) -> list:
        """
        Process multiple MQTT messages in batch.
        
        Args:
            mqtt_messages: List of MQTT messages
            
        Returns:
            List of translation results
        """
        results = []
        for message in mqtt_messages:
            try:
                # Note: This is synchronous version for batch processing
                # For async batch processing, use asyncio.gather()
                result = self.translate_sensor_event_sync(message)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Batch processing error: {e}")
                results.append({
                    "description": "处理失败",
                    "error": str(e),
                    "success": False
                })
        return results
    
    def translate_sensor_event_sync(self, mqtt_message: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synchronous version of translate_sensor_event for batch processing.
        Uses fallback generation only.
        """
        try:
            # Parse MQTT message
            parsed_data = self.mqtt_handler.parse_mqtt_message(mqtt_message)
            
            # Generate description using fallback method
            description = self._generate_fallback_description(parsed_data)
            validated_description = self._validate_description(description)
            
            return {
                "description": validated_description,
                "timestamp": datetime.now().isoformat(),
                "sensor_type": parsed_data["sensor_data"]["type"],
                "event_type": parsed_data["event_type"],
                "success": True
            }
        except Exception as e:
            return {
                "description": "检测到传感器活动",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
