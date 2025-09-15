"""
Script to read douyin_news.py using MCP file server and extract event information.
"""

import asyncio
import json
import re
from mcp.client.stdio import stdio_client

async def read_douyin_file():
    """Read the douyin_news.py file using MCP and extract event information."""
    
    douyin_file_path = r"C:\Users\Danqi28_luck_to_play\Desktop\Work\hewan_emotion_cursor_python\douyin_news.py"
    
    print("Reading douyin_news.py using MCP file server...")
    print("=" * 60)
    
    try:
        # Connect to our local MCP file server
        async with stdio_client("python", ["file_server.py"]) as client:
            # Read the douyin_news.py file
            result = await client.call_tool("read_file", {"path": douyin_file_path})
            
            if result.content and len(result.content) > 0:
                content = result.content[0].text
                print(f"✅ Successfully read douyin_news.py ({len(content)} characters)")
                
                # Extract event information
                lines = content.split('\n')
                
                # Look for event types and keywords
                disaster_keywords = []
                celebration_keywords = []
                functions = []
                event_types = []
                
                in_disaster_keywords = False
                in_celebration_keywords = False
                
                for line in lines:
                    line_stripped = line.strip()
                    
                    # Track when we're in keyword sections
                    if "DISASTER_KEYWORDS" in line:
                        in_disaster_keywords = True
                        in_celebration_keywords = False
                        continue
                    elif "CELEBRATION_KEYWORDS" in line:
                        in_celebration_keywords = True
                        in_disaster_keywords = False
                        continue
                    elif line_stripped.startswith(']') and (in_disaster_keywords or in_celebration_keywords):
                        in_disaster_keywords = False
                        in_celebration_keywords = False
                        continue
                    
                    # Extract keywords
                    if in_disaster_keywords and '"' in line:
                        # Extract Chinese keywords from the line
                        keywords = re.findall(r'"([^"]+)"', line)
                        disaster_keywords.extend(keywords)
                    
                    if in_celebration_keywords and '"' in line:
                        # Extract Chinese keywords from the line
                        keywords = re.findall(r'"([^"]+)"', line)
                        celebration_keywords.extend(keywords)
                    
                    # Extract functions
                    if line_stripped.startswith('def '):
                        functions.append(line_stripped)
                    
                    # Look for event type patterns
                    if any(keyword in line for keyword in ['disaster', 'celebration', 'trending', 'hot']):
                        if line_stripped not in event_types:
                            event_types.append(line_stripped)
                
                print(f"\n📋 Analysis Results:")
                print(f"Functions found: {len(functions)}")
                print(f"Disaster keywords: {len(disaster_keywords)}")
                print(f"Celebration keywords: {len(celebration_keywords)}")
                print(f"Event type lines: {len(event_types)}")
                
                print(f"\n🔧 Functions:")
                for func in functions:
                    print(f"  - {func}")
                
                print(f"\n💥 Disaster Keywords (first 10):")
                for keyword in disaster_keywords[:10]:
                    print(f"  - {keyword}")
                
                print(f"\n🎉 Celebration Keywords (first 10):")
                for keyword in celebration_keywords[:10]:
                    print(f"  - {keyword}")
                
                # Based on the analysis, determine the trending events
                trending_events = []
                
                # Look for specific event patterns in the code
                if disaster_keywords:
                    trending_events.append("disaster_trending")
                if celebration_keywords:
                    trending_events.append("celebration_trending")
                
                # Add other trending event types based on the Chinese requirements
                # 3.3 时事热搜类: 命中重大灾难性/利好性事件后，输入内容包括事件名称、事件标签（重大灾难性、重大利好性）
                trending_events.extend([
                    "major_disaster_trending",  # 重大灾难性
                    "major_positive_trending",  # 重大利好性
                    "hot_search_trending",      # 热搜事件
                    "social_trending"           # 社会热点
                ])
                
                print(f"\n🔥 Recommended Trending Events:")
                for event in trending_events:
                    print(f"  - {event}")
                
                return trending_events
                
            else:
                print("❌ No content returned from MCP server")
                return []
                
    except Exception as e:
        print(f"❌ Error reading file via MCP: {e}")
        return []

async def update_events_json():
    """Update the events.json file with trending events."""
    
    # Read the douyin file to get trending events
    trending_events = await read_douyin_file()
    
    if not trending_events:
        print("❌ No trending events found, using default events")
        trending_events = [
            "major_disaster_trending",
            "major_positive_trending", 
            "hot_search_trending",
            "social_trending"
        ]
    
    # Read current events.json
    try:
        with open('events.json', 'r', encoding='utf-8') as f:
            events_data = json.load(f)
        
        # Update disaster_events to trending_events
        if "disaster_events" in events_data:
            events_data["trending_events"] = trending_events
            del events_data["disaster_events"]
        else:
            events_data["trending_events"] = trending_events
        
        # Write updated events.json
        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(events_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Updated events.json:")
        print(f"   - Changed 'disaster_events' to 'trending_events'")
        print(f"   - Added {len(trending_events)} trending event types")
        
        # Show the updated trending events section
        print(f"\n📄 Updated trending_events section:")
        for event in trending_events:
            print(f"   - {event}")
            
    except Exception as e:
        print(f"❌ Error updating events.json: {e}")

if __name__ == "__main__":
    asyncio.run(update_events_json())