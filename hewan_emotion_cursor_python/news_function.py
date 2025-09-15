# get_news.py
import os
import re
import random
import json
from typing import List, Tuple, Literal, Optional

from db_utils import get_emotion_data
from emotion_database import update_emotion_in_database

# --- Configuration ---
DOUYIN_WORDS_FILE = "douyin_words_20250826_212805.json"

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

def fetch_news_titles(language: str = "zh", country: str = "cn", page_size: int = 50) -> List[str]:
    """
    Fetch news titles from local Douyin words JSON file.
    
    :param language: Language code (currently only supports "zh" for Chinese)
    :param country: Country code (currently only supports "cn" for China)
    :param page_size: Number of articles to fetch
    :return: List of news titles (Douyin hot words)
    """
    try:
        # Check if file exists
        if not os.path.exists(DOUYIN_WORDS_FILE):
            print(f"Warning: {DOUYIN_WORDS_FILE} not found")
            return []
        
        # Read the JSON file
        with open(DOUYIN_WORDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract words from the JSON structure
        titles = []
        if "words" in data:
            words = data["words"][:page_size]  # Limit to page_size
            titles = [word.get("word", "") for word in words if word.get("word")]
        
        # Clean and deduplicate
        clean_titles = []
        seen = set()
        for title in titles:
            title = title.strip()
            if title and title not in seen:
                seen.add(title)
                clean_titles.append(title)
        
        print(f"Loaded {len(clean_titles)} hot words from {DOUYIN_WORDS_FILE}")
        return clean_titles
        
    except Exception as e:
        print(f"Error reading Douyin words file: {e}")
        return []

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

def process_news_event(user_id: int, language: str = "zh", country: str = "cn") -> Optional[dict]:
    """
    Process news events using local Douyin hot words data.
    
    :param user_id: User ID to process
    :param language: Language for news (currently only supports "zh" for Chinese)
    :param country: Country for news (currently only supports "cn" for China)
    :return: Result dictionary or None
    """
    print(f"\n=== Processing News Event for User {user_id} ===")
    print(f"Language: {LANGUAGE_OPTIONS.get(language, language)}")
    print(f"Country: {COUNTRY_OPTIONS.get(country, country)}")
    print(f"Data Source: {DOUYIN_WORDS_FILE}")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        print(f"User {user_id} not found in database")
        return None
    
    print(f"Found user: {user_data.get('name', 'Unknown')} (role: {user_data.get('role', 'Unknown')})")
    
    # Fetch news titles from local file
    titles = fetch_news_titles(language=language, country=country)
    if not titles:
        print("No hot words loaded from local file")
        return None
    
    print(f"Loaded {len(titles)} hot words from local file")
    
    # Classify news
    event_type = classify_news(titles)
    if not event_type:
        print("No qualifying news event detected")
        return None
    
    print(f"News classified as: {event_type}")
    
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
        "x_change": x_change,
        "y_change": y_change,
        "intimacy_change": intimacy_change,
        "updated": True,
        "sample_titles": titles[:3],
        "data_source": DOUYIN_WORDS_FILE
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
    print("Douyin Hot Words Event Processing System")
    print("========================================")
    
    # Show available options
    show_available_options()
    
    # Example 1: Chinese hot words from China (default)
    print("\n--- Example 1: Chinese Hot Words from China (Default) ---")
    result1 = process_news_event(user_id=1, language="zh", country="cn")
    if result1:
        print(f"Result: {result1}")
    
    # Example 2: Chinese hot words with custom page size
    print("\n--- Example 2: Chinese Hot Words (Top 20) ---")
    result2 = process_news_event(user_id=1, language="zh", country="cn")
    if result2:
        print(f"Result: {result2}")
    
    # Example 3: Test with different user
    print("\n--- Example 3: Different User ---")
    result3 = process_news_event(user_id=2, language="zh", country="cn")
    if result3:
        print(f"Result: {result3}")
    
    # Example 4: Test classification with sample titles
    print("\n--- Example 4: Test Classification ---")
    sample_titles = ["地震", "节日庆典", "疫情", "胜利", "灾难"]
    event_type = classify_news(sample_titles)
    print(f"Sample titles: {sample_titles}")
    print(f"Classified as: {event_type}")