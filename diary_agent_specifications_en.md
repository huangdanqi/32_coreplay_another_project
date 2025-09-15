# (III) Diary Agent (Real-time)

## 1. Task
Based on all events that occurred with the toy on that day, randomly write diary entries. Each event type has an independent Agent and prompt, with identical input parameters and output parameters.

## 2. Process
- Claimed events must result in diary entries
- At 00:00 daily, determine the number of diaries to write for the next day: randomly select a number between 0-5
- When the number of diaries to write is not 0, upon an event occurring daily, randomly determine if a diary needs to be written for this event. If needed, call the corresponding query function as input parameters, then call the agent of the corresponding type to write the diary, until the number of diaries required for the day is completed. If the number of events on the day is insufficient, leading to the diary writing task being incomplete, no make-up writing is required. (Alternatively, you can randomly draw the corresponding number of tags from the event types to select the diary types to be written today)
- Only one diary entry per type

## 3. Input Content

### 3.1 Weather Category Diary
- **Trigger Condition:** After hitting (matching) liked/disliked weather
- **Data to Query:** Query today's complete weather changes and tomorrow's weather changes
- **Content to Include:** City, weather changes, IP's liked weather, IP's disliked weather, IP's personality type

### 3.2 Season Category Diary
- **Trigger Condition:** After hitting (matching) liked/disliked season
- **Data to Query:** Query the season and temperature of the city where the device's IP address/mobile phone's IP address is located
- **Content to Include:** City, season, temperature, IP's liked season, IP's disliked season, IP's personality type

### 3.3 Current Affairs Hot Search
- **Trigger Condition:** After hitting (matching) major catastrophic/beneficial events
- **Content to Include:** Event name, event tags (major catastrophic, major beneficial)

### 3.4 Holiday Category
- **Trigger Condition:** Randomly select 1 day within the period of 3 days before to 3 days after the holiday, then randomly select an event to write a diary
- **Content to Include:** Time (X days before holiday / Xth day of holiday / X days after holiday), holiday name

### 3.5 Remote Toy Interaction with Emotion Event
- **Trigger Condition:** Each time a liked/disliked remote interaction is triggered
- **Content to Include:** Event name triggered by remote interaction from close friend, close friend's nickname, close friend's owner's nickname, the triggered toy's preference for the action

### 3.6 Toy Close Friend Same Frequency Event
- **Trigger Condition:** Each time a same frequency event is triggered
- **Content to Include:** Event name of the triggered same frequency event, toy owner's nickname, close friend's nickname, close friend's owner's nickname

### 3.7 Claim Event
- **Trigger Condition:** Each time a device is bound
- **Content to Include:** Owner's personal information

### 3.8 Human-Machine Interaction Event
- **Trigger Condition:** Each time an MQTT message is received, and the message type is an event
- **Content to Include:** Event name of the triggered same frequency event, toy owner's nickname, close friend's nickname, close friend's owner's nickname

### 3.9 Human-Machine Dialogue Event
- **Trigger Condition:** Each time an event extraction result for a segment of dialogue is generated
- **Content to Include:** Event summary, event title, content theme, owner's emotion

### 3.10 Interaction Reduction Event
- **Trigger Condition:** After each trigger, write at a random time on the second day
- **Content to Include:** Event name, disconnection type (completely no interaction / no dialogue but with interaction), number of days disconnected

## 4. Output Diary Content
- **Time**
- **Toy's Emotional Tags:** Angry/Furious, Sad/Upset, Worried, Anxious/Melancholy, Surprised/Shocked, Curious, Confused, Calm, Happy/Joyful, Excited/Thrilled
- **Title:** Within 6 characters, generated based on content
- **Content:** Within 35 characters, can include emojis
