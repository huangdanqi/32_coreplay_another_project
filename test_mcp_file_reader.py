"""
Test script to verify the MCP file server can read the weather_function.py file.
"""

import asyncio
import json
from mcp.client import Client
from mcp.client.stdio import stdio_client

async def test_file_reading():
    """Test reading the weather function file via MCP."""
    
    # Path to the weather function file
    weather_file_path = r"C:\Users\Danqi28_luck_to_play\Desktop\Work\hewan_emotion_cursor_python\weather_function.py"
    
    print("Testing MCP File Server")
    print("=" * 50)
    print(f"Attempting to read: {weather_file_path}")
    
    try:
        # Start the MCP client
        async with stdio_client("python", ["file_server.py"]) as client:
            # List available tools
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Call the read_file tool
            result = await client.call_tool("read_file", {"path": weather_file_path})
            
            if result.content and len(result.content) > 0:
                content = result.content[0].text
                print(f"✅ Successfully read file ({len(content)} characters)")
                
                # Show first 500 characters
                print("\nFirst 500 characters:")
                print("-" * 30)
                print(content[:500])
                print("-" * 30)
                
                # Extract key information
                lines = content.split('\n')
                event_types = []
                functions = []
                
                for line in lines:
                    line = line.strip()
                    if any(event in line for event in ['favorite_weather', 'dislike_weather', 'favorite_season', 'dislike_season']):
                        if line not in event_types:
                            event_types.append(line)
                    if line.startswith('def '):
                        functions.append(line)
                
                print(f"\n📋 Analysis Results:")
                print(f"Event types found: {len(event_types)}")
                print(f"Functions found: {len(functions)}")
                
                if event_types:
                    print("\n🎯 Event Types:")
                    for event in event_types[:5]:  # Show first 5
                        print(f"  - {event}")
                
                if functions:
                    print("\n🔧 Functions:")
                    for func in functions:
                        print(f"  - {func}")
                        
            else:
                print("❌ No content returned")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_file_reading())