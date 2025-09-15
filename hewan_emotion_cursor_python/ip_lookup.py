# ip_lookup.py
import requests

def get_ip_city(ip_address: str) -> str:
    """
    Get the city of a given IP address using the ip-api.com free API.
    
    Args:
        ip_address (str): The IP address to look up.
    
    Returns:
        str: The city name if found, otherwise "Unknown".
    """
    url = f"http://ip-api.com/json/{ip_address}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("status") == "success":
            return data.get("city", "Unknown")
        else:
            return "Unknown"
    except Exception as e:
        return f"Error: {e}"
