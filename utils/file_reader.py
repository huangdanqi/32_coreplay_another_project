"""
Local file reader utility for accessing files outside the workspace.
This utility helps read the existing weather_function.py and other reference files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class LocalFileReader:
    """Utility class for reading local files outside the workspace."""
    
    def __init__(self, base_path: str = None):
        """Initialize with optional base path."""
        self.base_path = Path(base_path) if base_path else None
    
    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read a file and return its contents as string.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File contents as string, or None if file cannot be read
        """
        try:
            path = Path(file_path)
            if self.base_path:
                path = self.base_path / path
                
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def read_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Read a JSON file and return parsed content.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON content, or None if file cannot be read
        """
        content = self.read_file(file_path)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from {file_path}: {e}")
        return None
    
    def extract_weather_function_structure(self, weather_function_path: str) -> Dict[str, Any]:
        """
        Extract the structure and key information from weather_function.py
        
        Args:
            weather_function_path: Path to weather_function.py
            
        Returns:
            Dictionary containing extracted structure information
        """
        content = self.read_file(weather_function_path)
        if not content:
            return {}
            
        # Extract key information from the weather function
        structure = {
            "event_types": [],
            "json_keys": [],
            "functions": [],
            "data_structures": []
        }
        
        # Parse the content to extract relevant information
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Look for event type definitions
            if 'favorite_weather' in line or 'dislike_weather' in line or \
               'favorite_season' in line or 'dislike_season' in line:
                if line not in structure["event_types"]:
                    structure["event_types"].append(line)
            
            # Look for JSON key patterns
            if '"' in line and ':' in line:
                structure["json_keys"].append(line)
            
            # Look for function definitions
            if line.startswith('def '):
                structure["functions"].append(line)
        
        return structure

# Example usage for the dairy agent project
def get_weather_function_info():
    """Get information from the existing weather function."""
    reader = LocalFileReader()
    weather_path = r"C:\Users\Danqi28_luck_to_play\Desktop\Work\hewan_emotion_cursor_python\weather_function.py"
    
    return reader.extract_weather_function_structure(weather_path)

if __name__ == "__main__":
    # Test the file reader
    info = get_weather_function_info()
    print("Weather function structure:")
    print(json.dumps(info, indent=2, ensure_ascii=False))