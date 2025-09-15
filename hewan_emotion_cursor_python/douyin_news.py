# douyin_news.py
import os
import re
import random
import json
from typing import List, Tuple, Literal, Optional

from db_utils import get_emotion_data
from emotion_database import update_emotion_in_database

# --- Configuration ---
DOUYIN_WORDS_FILE = "douyin_words_20250826_212805.json"

# --- Keywords for classification ---
DISASTER_KEYWORDS = [
    # Chinese keywords for disasters
    "地震", "洪水", "野火", "飓风", "台风", "海啸", "泥石流", "火山喷发", "灾难", "爆炸", "袭击", "恐袭",
    "战争", "冲突", "死亡", "死亡人数", "疫情", "爆发", "坠机", "空难", "枪击", "暴力", "受伤", "通报",
    "恐怖", "面具", "反诈", "蹦极", "受伤"
]

CELEBRATION_KEYWORDS = [
    # Chinese keywords for celebrations
    "节日", "庆典", "假期", "游行", "胜利", "冠军", "颁奖", "婚礼", "开幕", "周年", "新年", "国庆", 
    "演唱会", "典礼", "嘉年华", "灯光秀", "见面", "中国行", "留学", "明星", "可爱", "烘焙", "朋友",
    "订婚", "官宣", "挑战", "变装", "穿搭", "体验", "传奇", "加油", "整活", "口碑"
]

# --- Role weights ---
ROLE_WEIGHTS = {
    "disaster": {"lively": 1.5, "clam": 1.0},
    "celebration": {"lively": 2.0, "clam": 1.5}
}

TRIGGER_PROBABILITY = 0.6

def load_douyin_hot_words(file_path: str = None, page_size: int = 50) -> List[str]:
    """
    Load Douyin hot words from JSON file.
    
    :param file_path: Path to the JSON file (defaults to DOUYIN_WORDS_FILE)
    :param page_size: Number of words to load
    :return: List of hot words
    """
    if file_path is None:
        file_path = DOUYIN_WORDS_FILE
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found")
            return []
        
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract words from the JSON structure
        words = []
        if "words" in data:
            word_entries = data["words"][:page_size]  # Limit to page_size
            words = [word.get("word", "") for word in word_entries if word.get("word")]
        
        # Clean and deduplicate
        clean_words = []
        seen = set()
        for word in words:
            word = word.strip()
            if word and word not in seen:
                seen.add(word)
                clean_words.append(word)
        
        print(f"Loaded {len(clean_words)} hot words from {file_path}")
        return clean_words
        
    except Exception as e:
        print(f"Error reading Douyin words file: {e}")
        return []

def classify_douyin_news(words: List[str]) -> Optional[Literal["disaster", "celebration"]]:
    """
    Classify Douyin hot words as disaster or celebration based on keywords.
    
    :param words: List of Douyin hot words
    :return: Classification result or None
    """
    if not words:
        return None
    
    text = " ".join(words).lower()
    
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
    Calculate Y-axis change based on the emotion rules.
    Only uses x<0, y+1 or y-1 logic as requested.
    """
    if event_type == "disaster":
        # For disaster: x<0, y+1; x>=0, y-1
        return 1 if x_value < 0 else -1
    else:  # celebration
        # For celebration: x<0, y-1; x>=0, y+1  
        return -1 if x_value < 0 else 1

def process_douyin_news_event(user_id: int, file_path: str = None, page_size: int = 50) -> Optional[dict]:
    """
    Process Douyin hot words events with emotion updates.
    
    :param user_id: User ID to process
    :param file_path: Path to Douyin words JSON file (optional)
    :param page_size: Number of hot words to process
    :return: Result dictionary or None
    """
    print(f"\n=== Processing Douyin News Event for User {user_id} ===")
    print(f"Data Source: {file_path or DOUYIN_WORDS_FILE}")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        print(f"User {user_id} not found in database")
        return None
    
    print(f"Found user: {user_data.get('name', 'Unknown')} (role: {user_data.get('role', 'Unknown')})")
    
    # Load Douyin hot words
    words = load_douyin_hot_words(file_path=file_path, page_size=page_size)
    if not words:
        print("No hot words loaded from file")
        return None
    
    print(f"Loaded {len(words)} hot words from file")
    
    # Classify hot words
    event_type = classify_douyin_news(words)
    if not event_type:
        print("No qualifying event detected in hot words")
        return None
    
    print(f"Hot words classified as: {event_type}")
    
    # Apply probability check
    if random.random() >= TRIGGER_PROBABILITY:
        print(f"Probability check failed ({TRIGGER_PROBABILITY}) - no update")
        return {"user_id": user_id, "event_type": event_type, "updated": False}
    
    print(f"Probability check passed ({TRIGGER_PROBABILITY}) - proceeding with update")
    
    # Get current values
    current_x = user_data.get("update_x_value", 0)
    current_y = user_data.get("update_y_value", 0)
    current_intimacy = user_data.get("intimacy_value", 0)
    
    # Calculate changes based on emotion rules
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
    
    print(f"Current X: {current_x}, Y: {current_y}, Intimacy: {current_intimacy}")
    print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
    print(f"Applied weight: {weight} (role: {role})")
    
    # Update database
    update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
    
    return {
        "user_id": user_id,
        "event_type": event_type,
        "x_change": x_change,
        "y_change": y_change,
        "intimacy_change": intimacy_change,
        "updated": True,
        "sample_words": words[:5],  # Show first 5 words
        "data_source": file_path or DOUYIN_WORDS_FILE,
        "total_words_processed": len(words)
    }

def test_individual_topic(topic: str, user_role: str = "clam") -> dict:
    """
    Test a single topic to determine its classification and emotion effects.
    
    :param topic: The topic/word to test
    :param user_role: User role (lively or clam)
    :return: Dictionary with classification and emotion effects
    """
    print(f"\n--- Testing Topic: '{topic}' ---")
    
    # Classify the topic
    event_type = classify_douyin_news([topic])
    
    if not event_type:
        print(f"Topic '{topic}' does not match disaster or celebration keywords")
        return {
            "topic": topic,
            "classification": None,
            "event_type": None,
            "x_change": 0,
            "y_change": 0,
            "intimacy_change": 0,
            "matched_keywords": []
        }
    
    print(f"Topic '{topic}' classified as: {event_type}")
    
    # Find matched keywords
    matched_keywords = []
    if event_type == "disaster":
        matched_keywords = [kw for kw in DISASTER_KEYWORDS if kw in topic]
    else:
        matched_keywords = [kw for kw in CELEBRATION_KEYWORDS if kw in topic]
    
    print(f"Matched keywords: {matched_keywords}")
    
    # Calculate emotion effects (assuming current x=0 for baseline)
    current_x = 0
    
    # Calculate changes based on emotion rules
    if event_type == "disaster":
        x_change = -1
    else:  # celebration
        x_change = 1
    
    # Calculate Y change
    y_change = calculate_y_change(current_x, event_type)
    intimacy_change = 0  # Always 0 for news events
    
    # Apply role weights
    if user_role not in ["lively", "clam"]:
        user_role = "clam"
    
    weight = ROLE_WEIGHTS[event_type][user_role]
    x_change_weighted = int(x_change * weight)
    y_change_weighted = int(y_change * weight)
    
    print(f"Base changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
    print(f"Weighted changes (role: {user_role}): X={x_change_weighted}, Y={y_change_weighted}")
    
    return {
        "topic": topic,
        "classification": event_type,
        "event_type": event_type,
        "x_change": x_change_weighted,
        "y_change": y_change_weighted,
        "intimacy_change": intimacy_change,
        "matched_keywords": matched_keywords,
        "weight": weight,
        "role": user_role
    }

def process_all_topics_for_user(user_id: int, file_path: str = None, page_size: int = 50) -> List[dict]:
    """
    Process all topics from the Douyin words file and update database for a specific user.
    
    :param user_id: User ID to process
    :param file_path: Path to the JSON file (optional)
    :param page_size: Number of topics to process
    :return: List of processing results for each topic
    """
    print(f"\n=== Processing All Topics for User {user_id} ===")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        print(f"User {user_id} not found in database")
        return []
    
    print(f"Found user: {user_data.get('name', 'Unknown')} (role: {user_data.get('role', 'Unknown')})")
    
    # Load topics
    topics = load_douyin_hot_words(file_path=file_path, page_size=page_size)
    if not topics:
        print("No topics loaded")
        return []
    
    results = []
    disaster_count = 0
    celebration_count = 0
    neutral_count = 0
    updated_count = 0
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{len(topics)}] Processing: {topic}")
        
        # Classify the topic
        event_type = classify_douyin_news([topic])
        
        if not event_type:
            print(f"Topic '{topic}' does not match disaster or celebration keywords")
            result = {
                "topic": topic,
                "classification": None,
                "event_type": None,
                "x_change": 0,
                "y_change": 0,
                "intimacy_change": 0,
                "updated": False,
                "user_id": user_id
            }
            results.append(result)
            neutral_count += 1
            continue
        
        print(f"Topic '{topic}' classified as: {event_type}")
        
        # Apply probability check
        if random.random() >= TRIGGER_PROBABILITY:
            print(f"Probability check failed ({TRIGGER_PROBABILITY}) - no update")
            result = {
                "topic": topic,
                "classification": event_type,
                "event_type": event_type,
                "x_change": 0,
                "y_change": 0,
                "intimacy_change": 0,
                "updated": False,
                "user_id": user_id
            }
            results.append(result)
            if event_type == "disaster":
                disaster_count += 1
            else:
                celebration_count += 1
            continue
        
        print(f"Probability check passed ({TRIGGER_PROBABILITY}) - proceeding with update")
        
        # Get current values
        current_x = user_data.get("update_x_value", 0)
        current_y = user_data.get("update_y_value", 0)
        current_intimacy = user_data.get("intimacy_value", 0)
        
        # Calculate changes based on emotion rules
        if event_type == "disaster":
            x_change = -1
        else:  # celebration
            x_change = 1
        
        # Calculate Y change
        y_change = calculate_y_change(current_x, event_type)
        intimacy_change = 0  # Always 0 for news events
        
        # Apply role weights
        role = user_data.get("role", "clam").lower()
        if role not in ["lively", "clam"]:
            role = "clam"
        
        weight = ROLE_WEIGHTS[event_type][role]
        x_change_weighted = int(x_change * weight)
        y_change_weighted = int(y_change * weight)
        
        print(f"Current X: {current_x}, Y: {current_y}, Intimacy: {current_intimacy}")
        print(f"Calculated changes: X={x_change_weighted}, Y={y_change_weighted}, Intimacy={intimacy_change}")
        print(f"Applied weight: {weight} (role: {role})")
        
        # Update database
        try:
            update_emotion_in_database(user_id, x_change_weighted, y_change_weighted, intimacy_change)
            updated_count += 1
            print(f"Successfully updated database for topic: {topic}")
        except Exception as e:
            print(f"Error updating database for topic {topic}: {e}")
        
        result = {
            "topic": topic,
            "classification": event_type,
            "event_type": event_type,
            "x_change": x_change_weighted,
            "y_change": y_change_weighted,
            "intimacy_change": intimacy_change,
            "updated": True,
            "user_id": user_id,
            "weight": weight,
            "role": role
        }
        results.append(result)
        
        if event_type == "disaster":
            disaster_count += 1
        else:
            celebration_count += 1
    
    # Summary
    print(f"\n=== PROCESSING SUMMARY ===")
    print(f"Total topics processed: {len(topics)}")
    print(f"Disaster topics: {disaster_count}")
    print(f"Celebration topics: {celebration_count}")
    print(f"Neutral topics: {neutral_count}")
    print(f"Database updates: {updated_count}")
    
    return results

def test_all_topics(file_path: str = None, page_size: int = 50, user_role: str = "clam") -> List[dict]:
    """
    Test all topics from the Douyin words file for classification and emotion effects.
    
    :param file_path: Path to the JSON file (optional)
    :param page_size: Number of topics to test
    :param user_role: User role (lively or clam)
    :return: List of test results for each topic
    """
    print(f"\n=== Testing All Topics (Role: {user_role}) ===")
    
    # Load topics
    topics = load_douyin_hot_words(file_path=file_path, page_size=page_size)
    if not topics:
        print("No topics loaded")
        return []
    
    results = []
    disaster_count = 0
    celebration_count = 0
    neutral_count = 0
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{len(topics)}] Testing: {topic}")
        result = test_individual_topic(topic, user_role)
        results.append(result)
        
        if result["classification"] == "disaster":
            disaster_count += 1
        elif result["classification"] == "celebration":
            celebration_count += 1
        else:
            neutral_count += 1
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total topics tested: {len(topics)}")
    print(f"Disaster topics: {disaster_count}")
    print(f"Celebration topics: {celebration_count}")
    print(f"Neutral topics: {neutral_count}")
    
    return results

def get_douyin_words_info(file_path: str = None) -> dict:
    """
    Get information about the Douyin words file.
    
    :param file_path: Path to the JSON file (optional)
    :return: Dictionary with file information
    """
    if file_path is None:
        file_path = DOUYIN_WORDS_FILE
    
    try:
        if not os.path.exists(file_path):
            return {"error": f"File {file_path} not found"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "timestamp": data.get("timestamp", "Unknown"),
            "total_words": data.get("total_words", 0),
            "file_path": file_path,
            "sample_words": [word.get("word", "") for word in data.get("words", [])[:5]]
        }
        
    except Exception as e:
        return {"error": f"Error reading file: {e}"}

# Example usage and testing
if __name__ == "__main__":
    print("Douyin News Event Processing System")
    print("===================================")
    
    # Show file information
    # print("\n--- File Information ---")
    # info = get_douyin_words_info()
    # if "error" not in info:
    #     print(f"Timestamp: {info['timestamp']}")
    #     print(f"Total Words: {info['total_words']}")
    #     print(f"Sample Words: {info['sample_words']}")
    # else:
    #     print(f"Error: {info['error']}")
    
    # # Example 1: Test individual topics
    # print("\n--- Example 1: Test Individual Topics ---")
    # test_topics = ["地震", "演唱会", "疫情", "灯光秀", "受伤", "胜利", "灾难", "明星"]
    # for topic in test_topics:
    #     result = test_individual_topic(topic, "clam")
    #     print(f"Topic: {result['topic']} | Classification: {result['classification']} | X: {result['x_change']} | Y: {result['y_change']} | Intimacy: {result['intimacy_change']}")
    
    # Example 2: Test with different roles
    # print("\n--- Example 2: Test with Different Roles ---")
    # test_topic = "演唱会"
    # print(f"Testing topic: {test_topic}")
    
    # result_clam = test_individual_topic(test_topic, "clam")
    # result_lively = test_individual_topic(test_topic, "lively")
    
    # print(f"\nComparison for '{test_topic}':")
    # print(f"Clam role:   X={result_clam['x_change']}, Y={result_clam['y_change']}")
    # print(f"Lively role: X={result_lively['x_change']}, Y={result_lively['y_change']}")
    
    # Example 3: Process all topics and update database for user 1
    print("\n--- Example 3: Process All Topics and Update Database ---")
    all_results = process_all_topics_for_user(user_id=1, page_size=50)
    
    # Show summary of results
    print("\n--- Processing Results Summary ---")
    updated_results = [r for r in all_results if r['updated']]
    neutral_results = [r for r in all_results if not r['updated'] and r['classification'] is None]
    skipped_results = [r for r in all_results if not r['updated'] and r['classification'] is not None]
    
    print(f"Total topics processed: {len(all_results)}")
    print(f"Database updates: {len(updated_results)}")
    print(f"Neutral topics (no classification): {len(neutral_results)}")
    print(f"Skipped topics (probability check failed): {len(skipped_results)}")
    
    # Show some examples of updated topics
    if updated_results:
        print("\n--- Examples of Updated Topics ---")
        for result in updated_results[:5]:  # Show first 5
            print(f"'{result['topic']}' -> {result['classification']} | X: {result['x_change']}, Y: {result['y_change']}")
    
    # Example 4: Test disaster vs celebration topics (testing only)
    # print("\n--- Example 4: Disaster vs Celebration Analysis (Testing) ---")
    # disaster_topics = ["地震", "疫情", "受伤", "灾难", "暴力"]
    # celebration_topics = ["演唱会", "灯光秀", "胜利", "明星", "可爱"]
    
    # print("Disaster Topics:")
    # for topic in disaster_topics:
    #     result = test_individual_topic(topic, "clam")
    #     print(f"  {topic}: X={result['x_change']}, Y={result['y_change']}")
    
    # print("\nCelebration Topics:")
    # for topic in celebration_topics:
    #     result = test_individual_topic(topic, "clam")
    #     print(f"  {topic}: X={result['x_change']}, Y={result['y_change']}")
    
    # Example 5: Process with default file (original functionality)
    # print("\n--- Example 5: Single Event Processing (Original) ---")
    # result5 = process_douyin_news_event(user_id=1, page_size=5)
    # if result5:
    #     print(f"Result: {result5}")
