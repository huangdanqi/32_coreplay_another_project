# Data Source Mappings

This directory contains documentation of data source mappings for the diary agent system.

## Module Mappings

The diary agent reads data from existing hewan_emotion_cursor_python modules:

### Weather Events
- **Source Module**: `weather_function.py`
- **Event Types**: `weather_events`, `seasonal_events`
- **Events**: `favorite_weather`, `dislike_weather`, `favorite_season`, `dislike_season`
- **Data Reader**: `weather_data_reader.py`

### Trending Events  
- **Source Module**: `douyin_news.py`
- **Event Types**: `trending_events`
- **Events**: `celebration`, `disaster`
- **Data Reader**: `douyin_data_reader.py`

### Holiday Events
- **Source Module**: `holiday_function.py`
- **Event Types**: `holiday_events`
- **Events**: `approaching_holiday`, `during_holiday`, `holiday_ends`
- **Data Reader**: `holiday_data_reader.py`

### Friend Events
- **Source Module**: `friends_function.py`
- **Event Types**: `friends_function`
- **Events**: `made_new_friend`, `friend_deleted`, `liked_single`, `liked_3_to_5`, `liked_5_plus`, `disliked_single`, `disliked_3_to_5`, `disliked_5_plus`
- **Data Reader**: `friends_data_reader.py`

### Same Frequency Events
- **Source Module**: `same_frequency.py`
- **Event Types**: `same_frequency`
- **Events**: `close_friend_frequency`
- **Data Reader**: `frequency_data_reader.py`

### Adoption Events
- **Source Module**: `adopted_function.py`
- **Event Types**: `adopted_function`
- **Events**: `toy_claimed`
- **Data Reader**: `adoption_data_reader.py`

### Interactive Events
- **Source Module**: `human_toy_interactive_function.py`
- **Event Types**: `human_toy_interactive_function`
- **Events**: `liked_interaction_once`, `liked_interaction_3_to_5_times`, `liked_interaction_over_5_times`, `disliked_interaction_once`, `disliked_interaction_3_to_5_times`, `neutral_interaction_over_5_times`
- **Data Reader**: `interaction_data_reader.py`

### Dialogue Events
- **Source Module**: `human_toy_talk.py`
- **Event Types**: `human_toy_talk`
- **Events**: `positive_emotional_dialogue`, `negative_emotional_dialogue`
- **Data Reader**: `dialogue_data_reader.py`

### Neglect Events
- **Source Module**: `unkeep_interactive.py`
- **Event Types**: `unkeep_interactive`
- **Events**: `neglect_1_day_no_dialogue`, `neglect_1_day_no_interaction`, `neglect_3_days_no_dialogue`, `neglect_3_days_no_interaction`, `neglect_7_days_no_dialogue`, `neglect_7_days_no_interaction`, `neglect_15_days_no_interaction`, `neglect_30_days_no_dialogue`, `neglect_30_days_no_interaction`
- **Data Reader**: `neglect_data_reader.py`

## Integration Approach

The diary agent system operates independently from the existing emotion calculation system:

1. **Read-Only Access**: Data readers provide read-only access to existing modules
2. **Context Extraction**: Extract relevant information for diary generation context
3. **No Modification**: Do not modify existing emotion calculation logic or database operations
4. **Separation**: Maintain clear separation between diary generation and emotion calculation systems

## Database Access

- **Read-Only**: Access existing database tables for user context
- **Tables**: `emotion`, `toy_interaction_events`, `toy_friendships`
- **Fields**: User preferences, role, current events, interaction history
- **No Updates**: Do not update emotion calculations or existing database operations