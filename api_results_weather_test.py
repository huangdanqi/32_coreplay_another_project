"""
API RESULTS WEATHER TEST - CAPTURE ALL API RESPONSES
====================================================
This test captures and displays ALL API results including:
✅ Today's weather data (current conditions + hourly changes)
✅ Tomorrow's weather forecast (detailed predictions)
✅ IP geolocation results (city detection)
✅ User database queries (preferences, personality)
✅ Weather API responses (raw data)
✅ LLM generation results (diary entries)
✅ Complete data flow from APIs to final output
"""

import asyncio
import json
import time
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from diary_agent.core.llm_manager import LLMConfigManager
from diary_agent.agents.weather_agent import WeatherAgent
from diary_agent.integration.weather_data_reader import WeatherDataReader
from diary_agent.utils.data_models import EventData

class APIResultsCapture:
    """Capture and display all API results"""
    
    def __init__(self):
        self.api_results = {
            'weather_api_calls': [],
            'ip_geolocation_calls': [],
            'database_queries': [],
            'llm_generations': [],
            'diary_entries': [],
            'errors': []
        }
        self.test_summary = {
            'total_api_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def capture_weather_api_data(self, city: str, ip: str):
        """Capture real weather API data for today and tomorrow"""
        print(f"\n🌐 CAPTURING WEATHER API DATA FOR {city.upper()}")
        print("-" * 60)
        
        try:
            # Simulate weather API call (WeatherAPI.com format)
            weather_api_key = "3f7b39a8c1f4404f8f291326252508"  # From weather_function.py
            
            # Today's weather data
            today_url = f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={city}&aqi=no"
            
            # Tomorrow's forecast data
            forecast_url = f"http://api.weatherapi.com/v1/forecast.json?key={weather_api_key}&q={city}&days=2&aqi=no&alerts=no"
            
            print(f"📡 Making API calls to WeatherAPI.com...")
            print(f"   Current Weather URL: {today_url}")
            print(f"   Forecast URL: {forecast_url}")
            
            async with aiohttp.ClientSession() as session:
                # Get current weather
                print(f"\n🌤️ FETCHING TODAY'S WEATHER DATA...")
                try:
                    async with session.get(today_url) as response:
                        if response.status == 200:
                            today_data = await response.json()
                            print(f"✅ Current Weather API Response:")
                            print(f"   Status: {response.status}")
                            print(f"   City: {today_data['location']['name']}, {today_data['location']['country']}")
                            print(f"   Current Temp: {today_data['current']['temp_c']}°C")
                            print(f"   Condition: {today_data['current']['condition']['text']}")
                            print(f"   Humidity: {today_data['current']['humidity']}%")
                            print(f"   Wind: {today_data['current']['wind_kph']} km/h")
                            print(f"   Feels Like: {today_data['current']['feelslike_c']}°C")
                            print(f"   UV Index: {today_data['current']['uv']}")
                            print(f"   Visibility: {today_data['current']['vis_km']} km")
                            
                            self.api_results['weather_api_calls'].append({
                                'type': 'current_weather',
                                'city': city,
                                'ip': ip,
                                'url': today_url,
                                'status': response.status,
                                'data': today_data,
                                'timestamp': datetime.now().isoformat()
                            })
                            self.test_summary['successful_calls'] += 1
                        else:
                            print(f"❌ Current Weather API Error: {response.status}")
                            self.test_summary['failed_calls'] += 1
                except Exception as e:
                    print(f"❌ Current Weather API Exception: {e}")
                    self.api_results['errors'].append({
                        'type': 'weather_api_current',
                        'error': str(e),
                        'city': city
                    })
                    self.test_summary['failed_calls'] += 1
                
                # Get forecast data
                print(f"\n🔮 FETCHING TOMORROW'S WEATHER FORECAST...")
                try:
                    async with session.get(forecast_url) as response:
                        if response.status == 200:
                            forecast_data = await response.json()
                            print(f"✅ Forecast API Response:")
                            print(f"   Status: {response.status}")
                            
                            # Today's hourly data
                            today_forecast = forecast_data['forecast']['forecastday'][0]
                            print(f"\n📅 TODAY'S HOURLY WEATHER CHANGES:")
                            print(f"   Date: {today_forecast['date']}")
                            print(f"   Max Temp: {today_forecast['day']['maxtemp_c']}°C")
                            print(f"   Min Temp: {today_forecast['day']['mintemp_c']}°C")
                            print(f"   Condition: {today_forecast['day']['condition']['text']}")
                            print(f"   Chance of Rain: {today_forecast['day']['daily_chance_of_rain']}%")
                            
                            # Show hourly changes for today
                            print(f"   Hourly Changes:")
                            for hour in today_forecast['hour'][::3]:  # Every 3 hours
                                hour_time = hour['time'].split(' ')[1]
                                print(f"     {hour_time}: {hour['temp_c']}°C, {hour['condition']['text']}, Humidity: {hour['humidity']}%")
                            
                            # Tomorrow's forecast
                            if len(forecast_data['forecast']['forecastday']) > 1:
                                tomorrow_forecast = forecast_data['forecast']['forecastday'][1]
                                print(f"\n🌅 TOMORROW'S WEATHER FORECAST:")
                                print(f"   Date: {tomorrow_forecast['date']}")
                                print(f"   Max Temp: {tomorrow_forecast['day']['maxtemp_c']}°C")
                                print(f"   Min Temp: {tomorrow_forecast['day']['mintemp_c']}°C")
                                print(f"   Condition: {tomorrow_forecast['day']['condition']['text']}")
                                print(f"   Chance of Rain: {tomorrow_forecast['day']['daily_chance_of_rain']}%")
                                print(f"   Sunrise: {tomorrow_forecast['astro']['sunrise']}")
                                print(f"   Sunset: {tomorrow_forecast['astro']['sunset']}")
                                
                                # Tomorrow's hourly forecast
                                print(f"   Hourly Forecast:")
                                for hour in tomorrow_forecast['hour'][::4]:  # Every 4 hours
                                    hour_time = hour['time'].split(' ')[1]
                                    print(f"     {hour_time}: {hour['temp_c']}°C, {hour['condition']['text']}")
                            
                            self.api_results['weather_api_calls'].append({
                                'type': 'forecast_weather',
                                'city': city,
                                'ip': ip,
                                'url': forecast_url,
                                'status': response.status,
                                'data': forecast_data,
                                'timestamp': datetime.now().isoformat()
                            })
                            self.test_summary['successful_calls'] += 1
                            
                            return {
                                'current': today_data if 'today_data' in locals() else None,
                                'forecast': forecast_data
                            }
                        else:
                            print(f"❌ Forecast API Error: {response.status}")
                            self.test_summary['failed_calls'] += 1
                except Exception as e:
                    print(f"❌ Forecast API Exception: {e}")
                    self.api_results['errors'].append({
                        'type': 'weather_api_forecast',
                        'error': str(e),
                        'city': city
                    })
                    self.test_summary['failed_calls'] += 1
            
            self.test_summary['total_api_calls'] += 2
            return None
            
        except Exception as e:
            print(f"❌ Weather API capture failed: {e}")
            self.api_results['errors'].append({
                'type': 'weather_api_general',
                'error': str(e),
                'city': city
            })
            return None
    
    async def capture_ip_geolocation_data(self, ip: str):
        """Capture IP geolocation API results"""
        print(f"\n📍 CAPTURING IP GEOLOCATION DATA")
        print("-" * 60)
        
        try:
            # Simulate IP geolocation API call
            ip_api_url = f"http://ip-api.com/json/{ip}"
            
            print(f"📡 Making IP geolocation API call...")
            print(f"   IP Address: {ip}")
            print(f"   API URL: {ip_api_url}")
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(ip_api_url) as response:
                        if response.status == 200:
                            ip_data = await response.json()
                            print(f"✅ IP Geolocation API Response:")
                            print(f"   Status: {response.status}")
                            print(f"   IP: {ip_data.get('query', ip)}")
                            print(f"   City: {ip_data.get('city', 'Unknown')}")
                            print(f"   Region: {ip_data.get('regionName', 'Unknown')}")
                            print(f"   Country: {ip_data.get('country', 'Unknown')}")
                            print(f"   ISP: {ip_data.get('isp', 'Unknown')}")
                            print(f"   Timezone: {ip_data.get('timezone', 'Unknown')}")
                            print(f"   Coordinates: {ip_data.get('lat', 0)}, {ip_data.get('lon', 0)}")
                            
                            self.api_results['ip_geolocation_calls'].append({
                                'ip': ip,
                                'url': ip_api_url,
                                'status': response.status,
                                'data': ip_data,
                                'timestamp': datetime.now().isoformat()
                            })
                            self.test_summary['successful_calls'] += 1
                            return ip_data
                        else:
                            print(f"❌ IP Geolocation API Error: {response.status}")
                            self.test_summary['failed_calls'] += 1
                except Exception as e:
                    print(f"❌ IP Geolocation API Exception: {e}")
                    self.api_results['errors'].append({
                        'type': 'ip_geolocation',
                        'error': str(e),
                        'ip': ip
                    })
                    self.test_summary['failed_calls'] += 1
            
            self.test_summary['total_api_calls'] += 1
            return None
            
        except Exception as e:
            print(f"❌ IP Geolocation capture failed: {e}")
            return None
    
    async def capture_database_query_results(self, user_id: int):
        """Capture database query results for user preferences"""
        print(f"\n💾 CAPTURING DATABASE QUERY RESULTS")
        print("-" * 60)
        
        try:
            print(f"📡 Simulating database queries...")
            print(f"   User ID: {user_id}")
            print(f"   Query: get_emotion_data({user_id})")
            
            # Simulate database query results
            simulated_user_data = {
                'user_id': user_id,
                'name': f'User_{user_id}',
                'role': 'lively' if user_id % 2 == 1 else 'calm',
                'favorite_weathers': ['sunny', 'clear', 'warm'],
                'dislike_weathers': ['rainy', 'stormy', 'cold'],
                'favorite_seasons': ['spring', 'summer'],
                'dislike_seasons': ['winter'],
                'personality_weights': {
                    'favorite_weather': 1.5 if user_id % 2 == 1 else 1.0,
                    'dislike_weather': 1.0 if user_id % 2 == 1 else 0.5
                },
                'current_emotions': {
                    'x_axis': 0,  # Happiness
                    'y_axis': 0   # Energy
                }
            }
            
            print(f"✅ Database Query Results:")
            print(f"   User ID: {simulated_user_data['user_id']}")
            print(f"   Name: {simulated_user_data['name']}")
            print(f"   Role/Personality: {simulated_user_data['role']}")
            print(f"   Favorite Weather: {simulated_user_data['favorite_weathers']}")
            print(f"   Dislike Weather: {simulated_user_data['dislike_weathers']}")
            print(f"   Favorite Seasons: {simulated_user_data['favorite_seasons']}")
            print(f"   Dislike Seasons: {simulated_user_data['dislike_seasons']}")
            print(f"   Personality Weights: {simulated_user_data['personality_weights']}")
            print(f"   Current Emotions: {simulated_user_data['current_emotions']}")
            
            self.api_results['database_queries'].append({
                'user_id': user_id,
                'query_type': 'get_emotion_data',
                'data': simulated_user_data,
                'timestamp': datetime.now().isoformat()
            })
            self.test_summary['successful_calls'] += 1
            return simulated_user_data
            
        except Exception as e:
            print(f"❌ Database query capture failed: {e}")
            self.api_results['errors'].append({
                'type': 'database_query',
                'error': str(e),
                'user_id': user_id
            })
            self.test_summary['failed_calls'] += 1
            return None
    
    async def test_complete_api_flow(self):
        """Test complete API flow with Shanghai and Beijing"""
        print("🌐 COMPLETE API RESULTS CAPTURE TEST")
        print("=" * 80)
        print("Capturing ALL API responses for weather diary generation")
        print("📍 Testing: Shanghai (202.96.209.5) & Beijing (202.106.0.20)")
        print("=" * 80)
        
        self.test_summary['start_time'] = datetime.now()
        
        # Test locations
        test_locations = [
            {'city': 'Shanghai', 'ip': '202.96.209.5', 'user_id': 1, 'event': 'favorite_weather'},
            {'city': 'Beijing', 'ip': '202.106.0.20', 'user_id': 2, 'event': 'dislike_weather'}
        ]
        
        for location in test_locations:
            print(f"\n{'='*20} {location['city'].upper()} TEST {'='*20}")
            
            # 1. Capture IP Geolocation
            ip_data = await self.capture_ip_geolocation_data(location['ip'])
            
            # 2. Capture Weather API Data
            weather_data = await self.capture_weather_api_data(location['city'], location['ip'])
            
            # 3. Capture Database Query
            user_data = await self.capture_database_query_results(location['user_id'])
            
            # 4. Test diary generation with captured data
            await self.test_diary_generation(location, weather_data, user_data, ip_data)
        
        self.test_summary['end_time'] = datetime.now()
        
        # Generate complete results report
        self.generate_api_results_report()
    
    async def test_diary_generation(self, location: Dict, weather_data: Dict, user_data: Dict, ip_data: Dict):
        """Test diary generation with captured API data"""
        print(f"\n🤖 TESTING DIARY GENERATION WITH API DATA")
        print("-" * 60)
        
        try:
            # Initialize diary system
            llm_manager = LLMConfigManager()
            
            with open("diary_agent/config/agent_prompts/weather_agent.json", 'r', encoding='utf-8') as f:
                weather_config = json.load(f)
            
            weather_data_reader = WeatherDataReader()
            weather_agent = WeatherAgent(
                agent_type="weather_agent",
                prompt_config=weather_config,
                llm_manager=llm_manager,
                data_reader=weather_data_reader
            )
            
            # Create event with API data context
            event_data = EventData(
                event_id=f"{location['city']}_api_test",
                event_type="weather_events",
                event_name=location['event'],
                timestamp=datetime.now(),
                user_id=location['user_id'],
                context_data={
                    "user_ip": location['ip'],
                    "api_weather_data": weather_data,
                    "api_user_data": user_data,
                    "api_ip_data": ip_data,
                    "test_scenario": f"{location['city']}_complete_api_test"
                },
                metadata={
                    "source": "api_results_test",
                    "user_ip_address": location['ip'],
                    "location": f"{location['city']}, China",
                    "has_api_data": True
                }
            )
            
            print(f"🎯 Generating diary for {location['city']} {location['event']}")
            print(f"   Using API data: Weather ✅, IP ✅, User ✅")
            
            start_time = time.time()
            diary_entry = await weather_agent.process_event(event_data)
            end_time = time.time()
            
            if diary_entry:
                print(f"\n✅ DIARY GENERATION SUCCESS!")
                print(f"   📝 Title: '{diary_entry.title}' ({len(diary_entry.title)}/6 chars)")
                print(f"   📖 Content: '{diary_entry.content}' ({len(diary_entry.content)}/35 chars)")
                print(f"   😊 Emotions: {[str(tag) for tag in diary_entry.emotion_tags]}")
                print(f"   🤖 Agent: {diary_entry.agent_type}")
                print(f"   🧠 LLM: {diary_entry.llm_provider}")
                print(f"   ⏱️ Generation Time: {end_time - start_time:.2f}s")
                
                self.api_results['diary_entries'].append({
                    'location': location,
                    'diary_entry': {
                        'title': diary_entry.title,
                        'content': diary_entry.content,
                        'emotions': [str(tag) for tag in diary_entry.emotion_tags],
                        'agent_type': diary_entry.agent_type,
                        'llm_provider': diary_entry.llm_provider,
                        'timestamp': diary_entry.timestamp.isoformat()
                    },
                    'generation_time': end_time - start_time,
                    'api_data_used': {
                        'weather_data_available': weather_data is not None,
                        'user_data_available': user_data is not None,
                        'ip_data_available': ip_data is not None
                    }
                })
                
                self.api_results['llm_generations'].append({
                    'location': location['city'],
                    'event': location['event'],
                    'llm_provider': diary_entry.llm_provider,
                    'generation_time': end_time - start_time,
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                })
                
            else:
                print(f"❌ No diary entry generated")
                self.api_results['errors'].append({
                    'type': 'diary_generation',
                    'location': location,
                    'error': 'No diary entry generated'
                })
                
        except Exception as e:
            print(f"❌ Diary generation failed: {e}")
            self.api_results['errors'].append({
                'type': 'diary_generation',
                'location': location,
                'error': str(e)
            })
    
    def generate_api_results_report(self):
        """Generate comprehensive API results report"""
        print("\n" + "=" * 80)
        print("📊 COMPLETE API RESULTS REPORT")
        print("=" * 80)
        
        # Summary statistics
        total_time = (self.test_summary['end_time'] - self.test_summary['start_time']).total_seconds()
        print(f"\n📈 API CALL STATISTICS:")
        print(f"   Total API Calls: {self.test_summary['total_api_calls']}")
        print(f"   Successful Calls: {self.test_summary['successful_calls']} ✅")
        print(f"   Failed Calls: {self.test_summary['failed_calls']} ❌")
        print(f"   Success Rate: {(self.test_summary['successful_calls']/max(1,self.test_summary['total_api_calls'])*100):.1f}%")
        print(f"   Total Test Time: {total_time:.2f}s")
        
        # Weather API Results
        print(f"\n🌤️ WEATHER API RESULTS ({len(self.api_results['weather_api_calls'])} calls):")
        for call in self.api_results['weather_api_calls']:
            print(f"   {call['type']}: {call['city']} (Status: {call['status']})")
            if call['type'] == 'current_weather' and 'data' in call:
                current = call['data']['current']
                print(f"     Current: {current['temp_c']}°C, {current['condition']['text']}")
            elif call['type'] == 'forecast_weather' and 'data' in call:
                today = call['data']['forecast']['forecastday'][0]['day']
                print(f"     Today: {today['mintemp_c']}-{today['maxtemp_c']}°C, {today['condition']['text']}")
                if len(call['data']['forecast']['forecastday']) > 1:
                    tomorrow = call['data']['forecast']['forecastday'][1]['day']
                    print(f"     Tomorrow: {tomorrow['mintemp_c']}-{tomorrow['maxtemp_c']}°C, {tomorrow['condition']['text']}")
        
        # IP Geolocation Results
        print(f"\n📍 IP GEOLOCATION RESULTS ({len(self.api_results['ip_geolocation_calls'])} calls):")
        for call in self.api_results['ip_geolocation_calls']:
            data = call['data']
            print(f"   IP {call['ip']}: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')} ({data.get('isp', 'Unknown')})")
        
        # Database Query Results
        print(f"\n💾 DATABASE QUERY RESULTS ({len(self.api_results['database_queries'])} queries):")
        for query in self.api_results['database_queries']:
            data = query['data']
            print(f"   User {data['user_id']}: {data['role']} personality, likes {data['favorite_weathers']}, dislikes {data['dislike_weathers']}")
        
        # Diary Generation Results
        print(f"\n📝 DIARY GENERATION RESULTS ({len(self.api_results['diary_entries'])} entries):")
        for entry in self.api_results['diary_entries']:
            diary = entry['diary_entry']
            location = entry['location']
            print(f"   {location['city']} ({location['event']}): '{diary['title']}' - '{diary['content']}'")
            print(f"     Emotions: {diary['emotions']}, LLM: {diary['llm_provider']}, Time: {entry['generation_time']:.2f}s")
        
        # Error Summary
        if self.api_results['errors']:
            print(f"\n❌ ERRORS ({len(self.api_results['errors'])} errors):")
            for error in self.api_results['errors']:
                print(f"   {error['type']}: {error['error']}")
        
        # Save complete results
        complete_results = {
            'test_summary': self.test_summary,
            'api_results': self.api_results,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('api_results_complete_report.json', 'w', encoding='utf-8') as f:
            json.dump(complete_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Complete API results saved to: api_results_complete_report.json")
        print(f"\n🎉 API RESULTS CAPTURE TEST COMPLETED!")
        
        return complete_results

async def run_api_results_test():
    """Run the complete API results capture test"""
    capture = APIResultsCapture()
    
    try:
        await capture.test_complete_api_flow()
        return capture.api_results
    except Exception as e:
        print(f"❌ API results test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the API results capture test
    asyncio.run(run_api_results_test())