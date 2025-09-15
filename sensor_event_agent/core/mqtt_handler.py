"""
MQTT Message Handler for Sensor Events
Processes MQTT JSON messages and extracts sensor event data.
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime


class MQTTHandler:
    """
    Handles MQTT message processing for sensor events.
    Parses JSON messages and extracts relevant sensor data.
    """
    
    def __init__(self):
        """Initialize MQTT handler."""
        self.logger = logging.getLogger(__name__)
        self.supported_sensor_types = {
            "accelerometer", "gyroscope", "magnetometer", "temperature",
            "humidity", "light", "sound", "pressure", "proximity", 
            "touch", "vibration", "motion", "orientation", "gesture"
        }
    
    def parse_mqtt_message(self, mqtt_message: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse MQTT message and extract sensor data.
        
        Args:
            mqtt_message: MQTT message as JSON string or dict
            
        Returns:
            Parsed sensor data dictionary
        """
        try:
            # Convert string to dict if necessary
            if isinstance(mqtt_message, str):
                message_data = json.loads(mqtt_message)
            else:
                message_data = mqtt_message.copy()
            
            # Extract and structure sensor data
            sensor_data = self._extract_sensor_data(message_data)
            device_info = self._extract_device_info(message_data)
            event_metadata = self._extract_event_metadata(message_data)
            
            # Create structured data
            parsed_data = {
                "mqtt_message": json.dumps(message_data, ensure_ascii=False),
                "sensor_data": sensor_data,
                "device_info": device_info,
                "event_type": self._determine_event_type(sensor_data),
                "timestamp": event_metadata.get("timestamp", datetime.now().isoformat()),
                "raw_data": message_data
            }
            
            self.logger.info(f"Successfully parsed MQTT message for sensor: {sensor_data.get('type', 'unknown')}")
            return parsed_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse MQTT JSON message: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing MQTT message: {e}")
            raise ValueError(f"Failed to parse MQTT message: {e}")
    
    def _extract_sensor_data(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sensor-specific data from MQTT message."""
        sensor_data = {}
        
        # Basic sensor information
        sensor_data["type"] = message_data.get("sensor_type", 
                                             message_data.get("type", 
                                                           message_data.get("sensorType", "unknown")))
        
        sensor_data["value"] = message_data.get("value", 
                                              message_data.get("data", 
                                                            message_data.get("measurement", 0)))
        
        sensor_data["unit"] = message_data.get("unit", "")
        sensor_data["count"] = message_data.get("count", 1)
        sensor_data["frequency"] = message_data.get("frequency", 1)
        sensor_data["duration"] = message_data.get("duration", 0)
        sensor_data["intensity"] = self._calculate_intensity(message_data)
        
        # Handle specific sensor types
        sensor_type = sensor_data["type"].lower()
        if "accelerometer" in sensor_type:
            sensor_data.update(self._parse_accelerometer(message_data))
        elif "gyroscope" in sensor_type:
            sensor_data.update(self._parse_gyroscope(message_data))
        elif "gesture" in sensor_type:
            sensor_data.update(self._parse_gesture(message_data))
        elif "motion" in sensor_type:
            sensor_data.update(self._parse_motion(message_data))
        elif "touch" in sensor_type:
            sensor_data.update(self._parse_touch(message_data))
        elif "sound" in sensor_type:
            sensor_data.update(self._parse_sound(message_data))
        elif "light" in sensor_type:
            sensor_data.update(self._parse_light(message_data))
        elif "temperature" in sensor_type:
            sensor_data.update(self._parse_temperature(message_data))
        
        return sensor_data
    
    def _extract_device_info(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract device information from MQTT message."""
        return {
            "device_id": message_data.get("device_id", 
                                        message_data.get("deviceId", 
                                                      message_data.get("id", "unknown"))),
            "device_name": message_data.get("device_name", 
                                          message_data.get("name", "toy")),
            "location": message_data.get("location", ""),
            "battery": message_data.get("battery", 100),
            "signal_strength": message_data.get("signal_strength", 
                                              message_data.get("rssi", 0))
        }
    
    def _extract_event_metadata(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract event metadata from MQTT message."""
        timestamp = message_data.get("timestamp", 
                                   message_data.get("time", 
                                                 message_data.get("ts", datetime.now().isoformat())))
        
        return {
            "timestamp": timestamp,
            "topic": message_data.get("topic", ""),
            "qos": message_data.get("qos", 0),
            "retain": message_data.get("retain", False)
        }
    
    def _parse_accelerometer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse accelerometer data."""
        result = {}
        if "x" in data and "y" in data and "z" in data:
            result["x"] = float(data["x"])
            result["y"] = float(data["y"])
            result["z"] = float(data["z"])
            # Calculate magnitude
            magnitude = (result["x"]**2 + result["y"]**2 + result["z"]**2) ** 0.5
            result["magnitude"] = magnitude
        return result
    
    def _parse_gyroscope(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse gyroscope data."""
        result = {}
        for axis in ["pitch", "roll", "yaw"]:
            if axis in data:
                result[axis] = float(data[axis])
        return result
    
    def _parse_gesture(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse gesture data."""
        return {
            "gesture_type": data.get("gesture", data.get("gesture_type", "unknown")),
            "confidence": data.get("confidence", 1.0),
            "direction": data.get("direction", "")
        }
    
    def _parse_motion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse motion data."""
        return {
            "motion_type": data.get("motion", data.get("motion_type", "movement")),
            "speed": data.get("speed", 0),
            "direction": data.get("direction", ""),
            "distance": data.get("distance", 0)
        }
    
    def _parse_touch(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse touch sensor data."""
        return {
            "touch_type": data.get("touch_type", "tap"),
            "pressure": data.get("pressure", 0),
            "duration": data.get("duration", 0)
        }
    
    def _parse_sound(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse sound sensor data."""
        return {
            "decibel": data.get("decibel", data.get("db", 0)),
            "frequency": data.get("frequency", 0),
            "sound_type": data.get("sound_type", "noise")
        }
    
    def _parse_light(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse light sensor data."""
        return {
            "lux": data.get("lux", data.get("brightness", 0)),
            "color": data.get("color", ""),
            "light_type": data.get("light_type", "ambient")
        }
    
    def _parse_temperature(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse temperature sensor data."""
        return {
            "temperature": data.get("temperature", data.get("temp", 0)),
            "humidity": data.get("humidity", 0),
            "heat_index": data.get("heat_index", 0)
        }
    
    def _calculate_intensity(self, data: Dict[str, Any]) -> str:
        """Calculate intensity level based on sensor value."""
        value = data.get("value", 0)
        try:
            if isinstance(value, (int, float)):
                if value > 50:
                    return "strong"
                elif value > 20:
                    return "medium" 
                elif value > 5:
                    return "light"
                else:
                    return "very_light"
            else:
                return "medium"
        except:
            return "medium"
    
    def _determine_event_type(self, sensor_data: Dict[str, Any]) -> str:
        """Determine event type based on sensor data."""
        sensor_type = sensor_data.get("type", "").lower()
        
        event_type_mapping = {
            "accelerometer": "motion",
            "gyroscope": "rotation", 
            "touch": "interaction",
            "gesture": "gesture",
            "sound": "audio",
            "light": "lighting",
            "temperature": "environmental",
            "humidity": "environmental",
            "motion": "motion",
            "vibration": "vibration"
        }
        
        for sensor_key, event_type in event_type_mapping.items():
            if sensor_key in sensor_type:
                return event_type
        
        return "sensor_event"
    
    def validate_message(self, mqtt_message: Union[str, Dict[str, Any]]) -> bool:
        """
        Validate MQTT message format.
        
        Args:
            mqtt_message: MQTT message to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parsed_data = self.parse_mqtt_message(mqtt_message)
            
            # Check if essential fields exist
            if not parsed_data.get("sensor_data", {}).get("type"):
                return False
            
            # Check if message has some data value
            sensor_data = parsed_data.get("sensor_data", {})
            if sensor_data.get("value") is None and not any(
                key in sensor_data for key in ["x", "y", "z", "gesture_type", "motion_type"]
            ):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Message validation failed: {e}")
            return False
