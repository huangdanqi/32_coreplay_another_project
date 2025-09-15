# news_function.py - Updated for local MCP server
import os
import re
import random
import json
import subprocess
from typing import List, Tuple, Literal, Optional

from db_utils import get_emotion_data
from weather_function import update_emotion_in_database

# --- Language and Country Options ---
LANGUAGE_OPTIONS = {
    "en": "English",
    "zh": "Chinese", 
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "ko": "Korean"
}

COUNTRY_OPTIONS = {
    "global": "Global News",
    "us": "United States",
    "gb": "United Kingdom", 
    "cn": "China",
    "jp": "Japan",
    "kr": "South Korea",
    "de": "Germany",
    "fr": "France",
    "es": "Spain",
    "it": "Italy",
    "ca": "Canada",
    "au": "Australia",
    "in": "India",
    "br": "Brazil",
    "ru": "Russia"
}

# --- Keywords for classification ---
DISASTER_KEYWORDS = [
    # English
    "earthquake", "flood", "wildfire", "hurricane", "typhoon", "tsunami", "landslide", "eruption",
    "disaster", "explosion", "bomb", "attack", "terror", "war", "conflict", "dead", "death toll",
    "pandemic", "outbreak", "crash", "plane crash", "train crash", "mass shooting", "violence",
    # Chinese
    "地震", "洪水", "野火", "飓风", "台风", "海啸", "泥石流", "火山喷发", "灾难", "爆炸", "袭击", "恐袭",
    "战争", "冲突", "死亡", "死亡人数", "疫情", "爆发", "坠机", "空难", "枪击", "暴力"
]

CELEBRATION_KEYWORDS = [
    # English
    "festival", "celebration", "holiday", "parade", "victory", "championship", "award", "wedding",
    "grand opening", "anniversary", "new year", "national day", "concert", "ceremony", "carnival",
    # Chinese
    "节日", "庆典", "假期", "游行", "胜利", "冠军", "颁奖", "婚礼", "开幕", "周年", "新年", "国庆", "演唱会", "典礼", "嘉年华"
]

# --- Role weights from the image ---
ROLE_WEIGHTS = {
    "disaster": {"lively": 1.5, "clam": 1.0},
    "celebration": {"lively": 2.0, "clam": 1.5}
}

TRIGGER_PROBABILITY = 0.6

def call_mcp_nytimes_news(language: str = "en", country: str = "global", limit: int = 50) -> List[str]:
    """
    Call local MCP server to get NYTimes news.
    
    :param language: Language code (en, zh, es, fr, de, ja, ko)
    :param country: Country code (global, us, gb, cn, jp, etc.)
    :param limit: Number of articles to fetch
    :return: List of news titles
    """
    try:
        # MCP command to get NYTimes news
        # Adjust the command based on your MCP server setup
        cmd = [
            "mcp",  # or "npx", "node", etc. depending on your MCP setup
            "trends-hub",
            "get-nytimes-news",
            "--language", language,
            "--limit", str(limit)
        ]
        
        # Add country if not global
        if country != "global":
            cmd.extend(["--country", country])
        
        print(f"Calling MCP: {' '.join(cmd)}")
        
        # Execute MCP command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse MCP response
            try:
                data = json.loads(result.stdout)
                
                # Extract titles from MCP response
                titles = []
                if isinstance(data, dict):
                    if "articles" in data:
                        titles = [article.get("title", "") for article in data["articles"] if article.get("title")]
                    elif "data" in data and isinstance(data["data"], list):
                        titles = [item.get("title", "") for item in data["data"] if item.get("title")]
                    elif "results" in data:
                        titles = [item.get("title", "") for item in data["results"] if item.get("title")]
                elif isinstance(data, list):
                    titles = [item.get("title", "") for item in data if item.get("title")]
                
                # Clean and deduplicate
                clean_titles = []
                seen = set()
                for title in titles:
                    title = title.strip()
                    if title and title not in seen:
                        seen.add(title)
                        clean_titles.append(title)
                
                print(f"✓ Successfully fetched {len(clean_titles)} NYTimes articles via MCP")
                return clean_titles
                
            except json.JSONDecodeError as e:
                print(f"Error parsing MCP response: {e}")
                print(f"Raw output: {result.stdout}")
                return []
        else:
            print(f"MCP command failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        print("MCP command timed out")
        return []
    except FileNotFoundError:
        print("MCP command not found. Make sure MCP is installed and in PATH")
        return []
    except Exception as e:
        print(f"Error calling MCP: {e}")
        return []

def get_sample_nytimes_news(language: str = "en") -> List[str]:
    """Sample NYTimes-style news for testing"""
    sample_news = {
        "en": [
            "Major Earthquake Strikes California Coast",
            "International Music Festival Celebrates Global Unity",
            "Scientific Breakthrough in Renewable Energy",
            "Olympic Team Wins Gold Medal in Championship",
            "Natural Disaster Affects Thousands in Region",
            "Cultural Festival Brings Joy to Community",
            "Technology Innovation Announced by Major Company",
            "Sports Victory Celebrated Nationwide"
        ],
        "zh": [
            "加州海岸发生大地震",
            "国际音乐节庆祝全球团结",
            "可再生能源科学突破",
            "奥运队在锦标赛中赢得金牌",
            "自然灾害影响地区数千人",
            "文化节为社区带来欢乐",
            "大公司宣布技术创新",
            "体育胜利举国庆祝"
        ]
    }
    
    return sample_news.get(language, sample_news["en"])

def classify_news(titles: List[str]) -> Optional[Literal["disaster", "celebration"]]:
    """Classify news as disaster or celebration based on keywords."""
    if not titles:
        return None
    
    text = " ".join(titles).lower()
    
    disaster_hits = sum(1 for keyword in DISASTER_KEYWORDS if re.search(re.escape(keyword.lower()), text))
    celebration_hits = sum(1 for keyword in CELEBRATION_KEYWORDS if re.search(re.escape(keyword.lower()), text))
    
    if disaster_hits == 0 and celebration_hits == 0:
        return None
    
    return "disaster" if disaster_hits >= celebration_hits else "celebration"

def get_user_data(user_id: int) -> Optional[dict]:
    """Get user data from database."""
    all_data = get_emotion_data()
    return next((user for user in all_data if user.get("id") == user_id), None)

def calculate_y_change(x_value: int, event_type: Literal["disaster", "celebration"]) -> int:
    """
    Calculate Y-axis change based on the image's rules.
    Only uses x<0, y+1 or y-1 logic as requested.
    """
    if event_type == "disaster":
        # For disaster: x<0, y+1; x>=0, y-1
        return 1 if x_value < 0 else -1
    else:  # celebration
        # For celebration: x<0, y-1; x>=0, y+1  
        return -1 if x_value < 0 else 1

def process_nytimes_news_event(user_id: int, language: str = "en", country: str = "global") -> Optional[dict]:
    """
    Process NYTimes news events using local MCP server.
    
    :param user_id: User ID to process
    :param language: Language for news (en, zh, es, fr, de, ja, ko)
    :param country: Country for news (global, us, gb, cn, jp, etc.)
    :return: Result dictionary or None
    """
    print(f"\n=== Processing NYTimes News Event for User {user_id} ===")
    print(f"Language: {LANGUAGE_OPTIONS.get(language, language)}")
    print(f"Country: {COUNTRY_OPTIONS.get(country, country)}")
    print(f"Source: NYTimes via Local MCP Server")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        print(f"User {user_id} not found in database")
        return None
    
    print(f"Found user: {user_data.get('name', 'Unknown')} (role: {user_data.get('role', 'Unknown')})")
    
    # Fetch NYTimes news titles via local MCP
    titles = call_mcp_nytimes_news(language=language, country=country)
    
    # Fallback to sample data if MCP fails
    if not titles:
        print("MCP failed, using sample NYTimes news for testing...")
        titles = get_sample_nytimes_news(language)
    
    if not titles:
        print("No NYTimes news titles available")
        return None
    
    print(f"Using {len(titles)} NYTimes news titles")
    
    # Classify news
    event_type = classify_news(titles)
    if not event_type:
        print("No qualifying news event detected")
        return None
    
    print(f"NYTimes news classified as: {event_type}")
    
    # Apply probability check
    if random.random() >= TRIGGER_PROBABILITY:
        print(f"Probability check failed ({TRIGGER_PROBABILITY}) - no update")
        return {"user_id": user_id, "event_type": event_type, "updated": False}
    
    print(f"Probability check passed ({TRIGGER_PROBABILITY}) - proceeding with update")
    
    # Get current X value
    current_x = user_data.get("update_x_value", 0)
    current_y = user_data.get("update_y_value", 0)
    current_intimacy = user_data.get("intimacy_value", 0)
    
    # Calculate changes based on image rules
    if event_type == "disaster":
        x_change = -1
    else:  # celebration
        x_change = 1
    
    # Calculate Y change using the simplified rule: only x<0, y+1 or y-1
    y_change = calculate_y_change(current_x, event_type)
    intimacy_change = 0  # Always 0 for news events
    
    # Apply role weights
    role = user_data.get("role", "clam").lower()
    if role not in ["lively", "clam"]:
        role = "clam"
    
    weight = ROLE_WEIGHTS[event_type][role]
    x_change = int(x_change * weight)
    y_change = int(y_change * weight)
    
    print(f"Current X: {current_x}, Y: {current_y}")
    print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
    print(f"Applied weight: {weight} (role: {role})")
    
    # Update database
    update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
    
    return {
        "user_id": user_id,
        "event_type": event_type,
        "language": language,
        "country": country,
        "source": "nytimes_local_mcp",
        "x_change": x_change,
        "y_change": y_change,
        "intimacy_change": intimacy_change,
        "updated": True,
        "sample_titles": titles[:3]
    }

def show_available_options():
    """Display available language and country options."""
    print("\n=== Available Options ===")
    print("Languages:")
    for code, name in LANGUAGE_OPTIONS.items():
        print(f"  {code}: {name}")
    
    print("\nCountries:")
    for code, name in COUNTRY_OPTIONS.items():
        print(f"  {code}: {name}")

# Example usage and testing
if __name__ == "__main__":
    print("NYTimes News Event Processing System via Local MCP")
    print("==================================================")
    
    # Show available options
    show_available_options()
    
    # Example 1: Global English NYTimes news
    print("\n--- Example 1: Global English NYTimes News ---")
    result1 = process_nytimes_news_event(user_id=1, language="en", country="global")
    if result1:
        print(f"Result: {result1}")
    
    # Example 2: US English NYTimes news
    print("\n--- Example 2: US English NYTimes News ---")
    result2 = process_nytimes_news_event(user_id=1, language="en", country="us")
    if result2:
        print(f"Result: {result2}")