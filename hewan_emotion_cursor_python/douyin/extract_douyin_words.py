# extract_douyin_words.py
import json
import os
from datetime import datetime
from douyin_self import Douyin
from util import logger

def extract_and_save_words():
    """
    Extract 'word' values from Douyin hot search and save to JSON file.
    """
    try:
        # Initialize Douyin scraper
        dy = Douyin()
        
        # Get hot search data
        items, resp = dy.get_hot_search()
        
        if not items:
            logger.error("No hot search items found")
            return None
        
        # Extract word values
        words = []
        for item in items:
            if 'word' in item and item['word']:
                words.append({
                    'word': item['word'],
                    'hot_value': item.get('hot_value', 0),
                    'position': item.get('position', 0),
                    'view_count': item.get('view_count', 0)
                })
        
        # Create output data structure
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_words': len(words),
            'words': words
        }
        
        # Save to JSON file
        output_file = f"douyin_words_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully extracted {len(words)} words and saved to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error extracting words: {str(e)}")
        return None

if __name__ == "__main__":
    extract_and_save_words()
