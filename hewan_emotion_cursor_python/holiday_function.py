# holiday_function.py
import os
import random
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Literal, Optional, Dict
import requests

from db_utils import get_emotion_data
from emotion_database import update_emotion_in_database

# --- Configuration ---
# Chinese calendar API (using a free service)
CHINESE_CALENDAR_API = "https://api.apihubs.cn/holiday/get"

# --- Holiday Event Types ---
# IMPORTANT: How the system works:
# 1. Holiday events are DETECTED on specific days:
#    - "approaching_holiday": 3 days before holiday
#    - "during_holiday": on the actual holiday day
#    - "holiday_ends": 3 days after holiday ends
# 2. Probability determines whether emotion update happens:
#    - 70% chance for approaching holiday
#    - 90% chance for during holiday  
#    - 50% chance for holiday ends
# 3. This simulates real-world where not every detected event affects emotions
#
# Based on the requirements table:
# 快到节假日: 节前3天中,随机某一天, 概率0.7, X+1, Y条件变化, 亲密度0, 活泼权重2, 平和权重1
HOLIDAY_EVENTS = {
    "approaching_holiday": {
        "name": "快到节假日",
        "trigger_days": 3,  # 节前3天中,随机某一天
        "probability": 0.7,
        "x_change": 1,  # +1
        "y_change_logic": {
            "x_less_than_0": -1,  # x<0时,y-1
            "x_greater_equal_0": 1  # x>=0时,y+1
        },
        "intimacy_change": 0,  # 0
        "weights": {"lively": 2, "clam": 1}  # 活泼角色权重2, 平和角色权重1
    },
    "during_holiday": {
        "name": "节假日期间",
        "trigger_days": 0,  # During the holiday
        "probability": 0.9,
        "x_change": 2,
        "y_change_logic": {
            "x_less_than_0": -2,
            "x_greater_equal_0": 2
        },
        "intimacy_change": 0,
        "weights": {"lively": 2, "clam": 1}
    },
    "holiday_ends": {
        "name": "节假日结束",
        "trigger_days": 3,  # 3 days after holiday
        "probability": 0.5,
        "x_change": -1,
        "y_change_logic": {
            "x_less_than_0": 1,
            "x_greater_equal_0": -1
        },
        "intimacy_change": 0,
        "weights": {"lively": 2, "clam": 1}
    }
}

# Major Chinese holidays (approximate dates, will be verified with API)
MAJOR_CHINESE_HOLIDAYS = {
    "春节": {"month": 1, "day": 1, "duration": 7},  # Spring Festival
    "清明节": {"month": 4, "day": 5, "duration": 3},  # Qingming Festival
    "劳动节": {"month": 5, "day": 1, "duration": 3},  # Labor Day
    "端午节": {"month": 5, "day": 5, "duration": 3},  # Dragon Boat Festival
    "中秋节": {"month": 8, "day": 15, "duration": 3},  # Mid-Autumn Festival
    "国庆节": {"month": 10, "day": 1, "duration": 7},  # National Day
}

def get_chinese_holidays(year: int = None) -> List[Dict]:
    """
    Get Chinese holidays for a specific year using API.
    
    :param year: Year to get holidays for (defaults to current year)
    :return: List of holiday information
    """
    if year is None:
        year = datetime.now().year
    
    try:
        # Try to get holidays from API
        params = {
            "year": year,
            "type": "holiday"
        }
        
        response = requests.get(CHINESE_CALENDAR_API, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:  # Success
                api_data = data.get("data", [])
                # Check if API data is in correct format
                if api_data and isinstance(api_data[0], dict):
                    return api_data
                else:
                    print("API data format not as expected, using fallback")
    except Exception as e:
        print(f"Error fetching Chinese holidays from API: {e}")
    
    # Fallback to predefined holidays
    print("Using fallback holiday data")
    holidays = []
    for name, info in MAJOR_CHINESE_HOLIDAYS.items():
        holidays.append({
            "name": name,
            "date": f"{year}-{info['month']:02d}-{info['day']:02d}",
            "duration": info["duration"]
        })
    
    return holidays

def is_holiday_period(date: datetime, holidays: List[Dict]) -> Optional[Dict]:
    """
    Check if a given date falls within any holiday period.
    
    :param date: Date to check
    :param holidays: List of holiday information
    :return: Holiday info if in holiday period, None otherwise
    """
    date_str = date.strftime("%Y-%m-%d")
    
    for holiday in holidays:
        holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
        duration = holiday.get("duration", 1)
        
        # Check if date is within holiday period
        if holiday_date <= date <= holiday_date + timedelta(days=duration - 1):
            return holiday
    
    return None

def get_holiday_event_type(date: datetime, holidays: List[Dict]) -> Optional[Literal["approaching_holiday", "during_holiday", "holiday_ends"]]:
    """
    Determine what type of holiday event should be triggered for a given date.
    
    :param date: Date to check
    :param holidays: List of holiday information
    :return: Holiday event type or None
    """
    # Check if currently in holiday period
    current_holiday = is_holiday_period(date, holidays)
    if current_holiday:
        return "during_holiday"
    
    # Check if approaching holiday (节前3天中,随机某一天)
    # Need to check holidays from both current year and next year
    all_holidays = holidays.copy()
    
    # Add holidays from next year for approaching holiday detection
    if date.month == 12:  # If we're in December, check next year's holidays
        next_year_holidays = get_chinese_holidays(date.year + 1)
        all_holidays.extend(next_year_holidays)
    
    for holiday in all_holidays:
        holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
        days_before = (holiday_date - date).days
        
        # 节前3天中,随机某一天 (random day within 3 days before holiday)
        if 1 <= days_before <= 3:
            return "approaching_holiday"
    
    # Check if holiday just ended (within 3 days after)
    for holiday in holidays:
        holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
        duration = holiday.get("duration", 1)
        holiday_end_date = holiday_date + timedelta(days=duration - 1)
        days_after = (date - holiday_end_date).days
        
        if 1 <= days_after <= 3:
            return "holiday_ends"
    
    return None

def calculate_holiday_emotion_changes(user_data: Dict, event_type: str, current_x: int) -> Tuple[int, int, int]:
    """
    Calculate emotion changes based on holiday event type and user data.
    
    :param user_data: User data from database
    :param event_type: Type of holiday event
    :param current_x: Current X value
    :return: Tuple of (x_change, y_change, intimacy_change)
    """
    if event_type not in HOLIDAY_EVENTS:
        return 0, 0, 0
    
    event_config = HOLIDAY_EVENTS[event_type]
    
    # Get base changes
    x_change = event_config["x_change"]
    intimacy_change = event_config["intimacy_change"]
    
    # Calculate Y change based on current X value
    if current_x < 0:
        y_change = event_config["y_change_logic"]["x_less_than_0"]
    else:
        y_change = event_config["y_change_logic"]["x_greater_equal_0"]
    
    # Apply role weights
    role = user_data.get("role", "clam").lower()
    if role not in ["lively", "clam"]:
        role = "clam"
    
    weight = event_config["weights"][role]
    x_change = int(x_change * weight)
    y_change = int(y_change * weight)
    
    return x_change, y_change, intimacy_change

def get_user_data(user_id: int) -> Optional[Dict]:
    """Get user data from database."""
    all_data = get_emotion_data()
    return next((user for user in all_data if user.get("id") == user_id), None)

def process_holiday_event(user_id: int, date: datetime = None) -> Optional[Dict]:
    """
    Process holiday events for a given user and date.
    
    :param user_id: User ID to process
    :param date: Date to check for holiday events (defaults to current date)
    :return: Result dictionary or None
    """
    if date is None:
        date = datetime.now()
    
    print(f"\n=== Processing Holiday Event for User {user_id} ===")
    print(f"Date: {date.strftime('%Y-%m-%d')}")
    
    # Get user data
    user_data = get_user_data(user_id)
    if not user_data:
        print(f"User {user_id} not found in database")
        return None
    
    print(f"Found user: {user_data.get('name', 'Unknown')} (role: {user_data.get('role', 'Unknown')})")
    
    # Get Chinese holidays for the year
    holidays = get_chinese_holidays(date.year)
    print(f"Found {len(holidays)} holidays for {date.year}")
    
    # Determine holiday event type
    event_type = get_holiday_event_type(date, holidays)
    if not event_type:
        print("No holiday event detected for this date")
        return None
    
    event_config = HOLIDAY_EVENTS[event_type]
    print(f"Holiday event detected: {event_config['name']}")
    print(f"Event will trigger on this date with {event_config['probability']*100}% probability")
    
    # Apply probability check - this determines if emotion update happens
    if random.random() >= event_config["probability"]:
        print(f"Probability check failed ({event_config['probability']:.1%}) - event detected but no emotion update")
        return {
            "user_id": user_id,
            "event_type": event_type,
            "event_name": event_config["name"],
            "date": date.strftime("%Y-%m-%d"),
            "event_detected": True,
            "emotion_updated": False,
            "reason": "Probability check failed"
        }
    
    print(f"Probability check passed ({event_config['probability']:.1%}) - proceeding with emotion update")
    
    # Get current values
    current_x = user_data.get("update_x_value", 0)
    current_y = user_data.get("update_y_value", 0)
    current_intimacy = user_data.get("intimacy_value", 0)
    
    # Calculate changes
    x_change, y_change, intimacy_change = calculate_holiday_emotion_changes(
        user_data, event_type, current_x
    )
    
    print(f"Current X: {current_x}, Y: {current_y}, Intimacy: {current_intimacy}")
    print(f"Calculated changes: X={x_change}, Y={y_change}, Intimacy={intimacy_change}")
    
    # Update database
    try:
        update_emotion_in_database(user_id, x_change, y_change, intimacy_change)
        print(f"Successfully updated database for holiday event: {event_config['name']}")
    except Exception as e:
        print(f"Error updating database: {e}")
        return None
    
    return {
        "user_id": user_id,
        "event_type": event_type,
        "event_name": event_config["name"],
        "date": date.strftime("%Y-%m-%d"),
        "x_change": x_change,
        "y_change": y_change,
        "intimacy_change": intimacy_change,
        "event_detected": True,
        "emotion_updated": True,
        "current_x": current_x,
        "current_y": current_y,
        "current_intimacy": current_intimacy
    }

def test_holiday_dates(user_id: int, start_date: str, end_date: str) -> List[Dict]:
    """
    Test holiday events for a range of dates.
    
    :param user_id: User ID to test
    :param start_date: Start date in YYYY-MM-DD format
    :param end_date: End date in YYYY-MM-DD format
    :return: List of results for each date
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    results = []
    current = start
    
    print(f"\n{'='*60}")
    print(f"TESTING HOLIDAY EVENTS FROM {start_date} TO {end_date}")
    print(f"{'='*60}")
    
    while current <= end:
        result = process_holiday_event(user_id, current)
        if result:
            results.append(result)
            if result.get("emotion_updated"):
                status = "✅ EVENT + EMOTION UPDATE"
            else:
                status = "🔍 EVENT DETECTED (no emotion update)"
            print(f"{current.strftime('%Y-%m-%d')}: {result['event_name']} - {status}")
        else:
            print(f"{current.strftime('%Y-%m-%d')}: No holiday event")
        
        current += timedelta(days=1)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"{'='*60}")
    total_events = len(results)
    total_updates = sum(1 for r in results if r.get("emotion_updated"))
    print(f"Total holiday events detected: {total_events}")
    print(f"Total emotion updates: {total_updates}")
    print(f"Events detected but no updates: {total_events - total_updates}")
    
    # Show probability explanation
    print(f"\nEXPLANATION:")
    print(f"- Events are DETECTED on specific days (before/during/after holidays)")
    print(f"- Probability determines whether emotion update actually happens")
    print(f"- This simulates real-world where not every detected event affects emotions")
    
    return results

def get_holiday_info(year: int = None) -> Dict:
    """
    Get information about holidays for a year.
    
    :param year: Year to get holiday info for
    :return: Dictionary with holiday information
    """
    if year is None:
        year = datetime.now().year
    
    holidays = get_chinese_holidays(year)
    
    return {
        "year": year,
        "total_holidays": len(holidays),
        "holidays": holidays,
        "event_types": list(HOLIDAY_EVENTS.keys())
    }

# Example usage and testing
if __name__ == "__main__":
    print("Holiday Event Processing System")

    
    # Example 2: Test specific date (Spring Festival period)
    print("\n--- Example 2: Test Spring Festival Period ---")
    spring_festival_date = datetime(2024, 2, 10)  # Approximate Spring Festival date
    result2 = process_holiday_event(user_id=1, date=spring_festival_date)
    if result2:
        print(f"Result: {result2}")
    
    # Example 3: Test date range (including approaching holiday period)
    print("\n--- Example 3: Test Date Range (Including Approaching Holiday) ---")
    test_results = test_holiday_dates(1, "2023-12-29", "2024-01-10")
    print(f"Found {len(test_results)} holiday events in the test period")
    
    # Show which events were detected
    for result in test_results:
        status = "Updated" if result.get("emotion_updated") else "Detected (no update)"
        print(f"  {result['date']}: {result['event_name']} - {status}")
    
