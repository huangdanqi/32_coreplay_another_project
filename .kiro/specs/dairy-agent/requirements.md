# Requirements Document

## Introduction

The Diary Agent is an intelligent multi-agent system that automatically generates diary entries based on various life events occurring in a user's daily life. The system consists of 10 specialized sub-agents, each handling specific event types with unique prompt configurations and data sources. Each agent generates diary entries with emotional context, timestamps, and content following strict formatting rules (6-character titles, 35-character content with emoji support). The system operates on a real-time trigger mechanism where diary entries are generated based on events that occurred, with each event type having its own specialized agent, prompt, and corresponding data source file from the hewan_emotion_cursor_python directory.

## Requirements

### Requirement 1

**User Story:** As a user, I want the system to automatically detect and process different types of life events so that relevant diary entries can be generated without manual intervention.

#### Acceptance Criteria

1. WHEN an event occurs THEN the system SHALL identify the event type and route it to the appropriate sub-agent based on the events.json mapping
2. WHEN multiple events occur simultaneously THEN the system SHALL process each event with its corresponding specialized agent
3. IF an event type is not recognized THEN the system SHALL log the unhandled event and continue processing other events
4. WHEN processing events THEN the system SHALL maintain compatibility with the existing hewan_emotion_cursor_python codebase structure and database schema
5. WHEN routing events THEN the system SHALL use the predefined event mappings: weather_events and seasonal_events use weather_function.py, trending_events use douyin_news.py, holiday_events use holiday_function.py, friends_function uses friends_function.py, same_frequency uses same_frequency.py, adopted_function uses adopted_function.py, human_toy_interactive_function uses human_toy_interactive_function.py, human_toy_talk uses human_toy_talk.py, and unkeep_interactive uses unkeep_interactive.py

### Requirement 2

**User Story:** As a system administrator, I want to configure different LLM providers (Qwen, DeepSeek) so that the system can use various AI models based on availability and requirements.

#### Acceptance Criteria

1. WHEN configuring LLM providers THEN the system SHALL support multiple API endpoints including Qwen and DeepSeek
2. WHEN an LLM API is unavailable THEN the system SHALL fallback to alternative configured providers
3. IF all configured LLM providers fail THEN the system SHALL log the error and queue the request for retry
4. WHEN switching between LLM providers THEN the system SHALL maintain consistent output format and quality

### Requirement 3

**User Story:** As a user, I want specialized sub-agents for different event types so that diary entries are contextually appropriate and emotionally relevant.

#### Acceptance Criteria

1. WHEN weather events occur THEN the weather sub-agent SHALL process specific event types: "favorite_weather", "dislike_weather", "favorite_season", "dislike_season" using weather_function.py logic
2. WHEN weather events occur THEN the system SHALL generate entries about today's weather changes, next day weather changes, city conditions, weather preferences, IP personality types, and role-based emotion calculations
3. WHEN seasonal events occur THEN the seasonal sub-agent SHALL process "favorite_season", "dislike_season" events using the same weather_function.py logic with seasonal focus
4. WHEN trending events occur THEN the trending sub-agent SHALL process "celebration", "disaster" events using douyin_news.py with keyword classification and probability-based triggering
5. WHEN holiday events occur THEN the holiday sub-agent SHALL process "approaching_holiday", "during_holiday", "holiday_ends" events using holiday_function.py with Chinese calendar API integration
6. WHEN friend events occur THEN the friends sub-agent SHALL process "made_new_friend", "friend_deleted", "liked_single", "liked_3_to_5", "liked_5_plus", "disliked_single", "disliked_3_to_5", "disliked_5_plus" events using friends_function.py
7. WHEN same frequency events occur THEN the same frequency sub-agent SHALL process "close_friend_frequency" events using same_frequency.py with 5-second synchronization detection
8. WHEN adoption events occur THEN the adoption sub-agent SHALL process "toy_claimed" events using adopted_function.py
9. WHEN human-toy interaction events occur THEN the interactive sub-agent SHALL process "liked_interaction_once", "liked_interaction_3_to_5_times", "liked_interaction_over_5_times", "disliked_interaction_once", "disliked_interaction_3_to_5_times", "neutral_interaction_over_5_times" events using human_toy_interactive_function.py
10. WHEN dialogue events occur THEN the dialogue sub-agent SHALL process "positive_emotional_dialogue", "negative_emotional_dialogue" events using human_toy_talk.py
11. WHEN neglect events occur THEN the neglect sub-agent SHALL process "neglect_1_day_no_dialogue", "neglect_1_day_no_interaction", "neglect_3_days_no_dialogue", "neglect_3_days_no_interaction", "neglect_7_days_no_dialogue", "neglect_7_days_no_interaction", "neglect_15_days_no_interaction", "neglect_30_days_no_dialogue", "neglect_30_days_no_interaction" events using unkeep_interactive.py

### Requirement 4

**User Story:** As a user, I want each sub-agent to have its own specialized prompt configuration so that diary entries match the specific context and tone appropriate for each event type.

#### Acceptance Criteria

1. WHEN a sub-agent processes an event THEN it SHALL use its specialized prompt template
2. WHEN prompt configurations are updated THEN the system SHALL reload the new prompts without restart
3. IF a prompt file is missing or corrupted THEN the system SHALL use a default prompt and log the error
4. WHEN generating diary entries THEN each sub-agent SHALL maintain consistent formatting and emotional tone

### Requirement 5

**User Story:** As a user, I want the system to trigger diary generation based on specific conditions so that entries are created at appropriate times and contexts.

#### Acceptance Criteria

1. WHEN trigger conditions are met THEN the system SHALL activate the appropriate sub-agent
2. WHEN condition.py evaluates to true THEN the system SHALL begin event processing
3. IF trigger conditions are not met THEN the system SHALL remain in monitoring mode
4. WHEN processing image inputs THEN the system SHALL extract relevant event information for diary generation

### Requirement 6

**User Story:** As a user, I want diary entries to include emotional context and personal details so that the entries feel authentic and meaningful.

#### Acceptance Criteria

1. WHEN generating diary entries THEN the system SHALL include emotional indicators (生气愤怒, 悲伤难过, 担忧, 焦虑忧愁, 惊讶震惊, 好奇, 羞愧, 平静, 开心快乐, 兴奋激动)
2. WHEN creating entries THEN the system SHALL include timestamps, event names, and content details
3. WHEN processing events THEN the system SHALL generate titles (6 characters max) and content (35 characters max, emoji allowed)
4. IF emotional context cannot be determined THEN the system SHALL use neutral emotional indicators

### Requirement 7

**User Story:** As a user, I want the weather agent to handle specific weather and seasonal preference events so that diary entries reflect personal weather preferences and seasonal changes.

#### Acceptance Criteria

1. WHEN "favorite_weather" event occurs THEN the weather agent SHALL generate diary entries about preferred weather conditions with positive emotional context using WeatherAPI.com integration
2. WHEN "dislike_weather" event occurs THEN the weather agent SHALL generate diary entries about disliked weather conditions with appropriate negative emotional context
3. WHEN "favorite_season" event occurs THEN the weather agent SHALL generate diary entries about preferred seasonal activities and positive seasonal emotions based on current month calculation
4. WHEN "dislike_season" event occurs THEN the weather agent SHALL generate diary entries about disliked seasonal conditions with appropriate emotional responses
5. WHEN processing weather events THEN the system SHALL include city weather information from IP geolocation, current and next day weather changes, and role-based personality weights ("clam" vs "lively")
6. WHEN generating weather diary entries THEN the system SHALL follow the existing weather_function.py emotion calculation logic with X/Y axis changes and role weight multipliers
7. WHEN calculating emotions THEN the system SHALL apply the conditional Y-axis logic: if X < 0 then Y+1 for favorites (Y-1 for dislikes), else Y-1 for favorites (Y+1 for dislikes)
8. WHEN applying role weights THEN the system SHALL use "clam" weights (favorite: 1.0, dislike: 0.5) and "lively" weights (favorite: 1.5, dislike: 1.0)

### Requirement 8

**User Story:** As a developer, I want the diary system to operate independently from the existing emotion system while reading necessary data for diary generation context.

#### Acceptance Criteria

1. WHEN the diary system starts THEN it SHALL establish read-only access to necessary data sources without interfering with existing emotion calculations
2. WHEN diary generation is needed THEN the system SHALL read event context from existing modules without modifying emotion database operations
3. WHEN user data is required THEN the system SHALL query only the necessary fields for diary context (user preferences, role, current events)
4. WHEN processing events THEN the system SHALL focus solely on diary generation as specified in diary_agent_specifications_en.md
5. WHEN generating diary entries THEN the system SHALL NOT modify existing emotion calculation logic or database update operations
6. WHEN reading event data THEN the system SHALL use existing module outputs as input context without changing their functionality

### Requirement 9

**User Story:** As a user, I want the system to generate diary entries with proper formatting and emotional context so that the entries feel authentic and meaningful.

#### Acceptance Criteria

1. WHEN generating diary entries THEN the system SHALL include timestamps in the format specified by the diary agent specifications
2. WHEN creating diary content THEN the system SHALL generate titles with maximum 6 characters and content with maximum 35 characters including emoji support
3. WHEN determining emotional context THEN the system SHALL select from the specified emotional tags: 生气愤怒, 悲伤难过, 担忧, 焦虑忧愁, 惊讶震惊, 好奇, 羞愧, 平静, 开心快乐, 兴奋激动
4. WHEN processing daily diary generation THEN the system SHALL randomly determine 0-5 diary entries to write per day at 00:00
5. WHEN claimed events occur THEN the system SHALL always generate diary entries for those events
6. WHEN an event occurs and daily quota is not 0 THEN the system SHALL randomly determine if a diary entry should be written for that event
7. WHEN diary generation is needed THEN the system SHALL call the corresponding query function as input parameters, then call the agent of the corresponding type to write the diary
8. WHEN daily quota is reached THEN the system SHALL stop generating diary entries until the next day
9. WHEN multiple events of the same type occur THEN the system SHALL write only one diary entry per event type per day
10. WHEN the daily event count is insufficient THEN the system SHALL not require make-up diary writing
11. WHEN using alternative approach THEN the system SHALL randomly draw the corresponding number of tags from event types to select diary types to be written today