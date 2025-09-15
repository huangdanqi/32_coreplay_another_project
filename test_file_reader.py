"""
Test script to read the weather_function.py file and extract its structure.
Run this to understand the existing codebase structure.
"""

import sys
import os
sys.path.append('utils')

from file_reader import LocalFileReader

def main():
    """Main function to test file reading."""
    reader = LocalFileReader()
    
    # Path to the existing weather function
    weather_path = r"C:\Users\Danqi28_luck_to_play\Desktop\Work\hewan_emotion_cursor_python\weather_function.py"
    
    print("Attempting to read weather_function.py...")
    print(f"Path: {weather_path}")
    print("-" * 50)
    
    # Try to read the file
    content = reader.read_file(weather_path)
    
    if content:
        print("✅ Successfully read weather_function.py")
        print(f"File size: {len(content)} characters")
        print("\nFirst 500 characters:")
        print(content[:500])
        print("\n" + "=" * 50)
        
        # Extract structure information
        structure = reader.extract_weather_function_structure(weather_path)
        print("\n📋 Extracted Structure Information:")
        
        if structure["event_types"]:
            print("\n🎯 Event Types Found:")
            for event in structure["event_types"]:
                print(f"  - {event}")
        
        if structure["functions"]:
            print("\n🔧 Functions Found:")
            for func in structure["functions"][:10]:  # Show first 10
                print(f"  - {func}")
        
        if structure["json_keys"]:
            print("\n🔑 JSON Keys Found (first 10):")
            for key in structure["json_keys"][:10]:
                print(f"  - {key}")
                
    else:
        print("❌ Failed to read weather_function.py")
        print("Please check:")
        print("1. File path is correct")
        print("2. File exists and is readable")
        print("3. No permission issues")

if __name__ == "__main__":
    main()