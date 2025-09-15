"""
Simple test to read the weather function file directly.
"""

import os

def test_direct_file_access():
    """Test direct file access to the weather function."""
    
    weather_file_path = r"C:\Users\Danqi28_luck_to_play\Desktop\Work\hewan_emotion_cursor_python\weather_function.py"
    
    print("Direct File Access Test")
    print("=" * 50)
    print(f"Attempting to read: {weather_file_path}")
    
    try:
        if os.path.exists(weather_file_path):
            with open(weather_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✅ Successfully read file ({len(content)} characters)")
            
            # Extract key information for the dairy agent
            lines = content.split('\n')
            
            # Find event types
            event_types = []
            role_weights = []
            functions = []
            json_keys = []
            
            for line in lines:
                line_stripped = line.strip()
                
                # Event types
                if any(event in line for event in ['favorite_weather', 'dislike_weather', 'favorite_season', 'dislike_season']):
                    if line_stripped not in event_types:
                        event_types.append(line_stripped)
                
                # Role weights
                if '"clam"' in line or '"lively"' in line:
                    role_weights.append(line_stripped)
                
                # Functions
                if line_stripped.startswith('def '):
                    functions.append(line_stripped)
                
                # JSON keys
                if '"' in line and ':' in line and ('favorite_' in line or 'dislike_' in line):
                    json_keys.append(line_stripped)
            
            print(f"\n📋 Analysis for Dairy Agent Integration:")
            print(f"Event types found: {len(event_types)}")
            print(f"Role weights found: {len(role_weights)}")
            print(f"Functions found: {len(functions)}")
            print(f"JSON keys found: {len(json_keys)}")
            
            print(f"\n🎯 Event Types (for weather agent):")
            for event in event_types:
                print(f"  - {event}")
            
            print(f"\n⚖️ Role Weights:")
            for weight in role_weights[:5]:  # Show first 5
                print(f"  - {weight}")
            
            print(f"\n🔧 Key Functions:")
            for func in functions:
                print(f"  - {func}")
            
            print(f"\n🔑 JSON Keys:")
            for key in json_keys[:5]:  # Show first 5
                print(f"  - {key}")
            
            # Extract the specific structure needed for dairy agent
            print(f"\n🏗️ Structure for Dairy Agent:")
            print("Event Names to Handle:")
            print("  - favorite_weather")
            print("  - dislike_weather") 
            print("  - favorite_season")
            print("  - dislike_season")
            
            print("\nRole Types:")
            print("  - clam (calm personality)")
            print("  - lively (active personality)")
            
            print("\nKey Data Fields:")
            print("  - user_id: int")
            print("  - user_ip_address: str")
            print("  - city: str (from IP lookup)")
            print("  - current_weather: str (from WeatherAPI)")
            print("  - current_season: str (Spring/Summer/Autumn/Winter)")
            print("  - role: str (clam/lively)")
            print("  - favorite_weathers: List[str] (JSON array)")
            print("  - dislike_weathers: List[str] (JSON array)")
            print("  - favorite_seasons: List[str] (JSON array)")
            print("  - dislike_seasons: List[str] (JSON array)")
            
        else:
            print(f"❌ File not found: {weather_file_path}")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    test_direct_file_access()