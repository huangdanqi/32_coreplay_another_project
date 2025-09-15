# 🎯 Simple Diary API - Condition Logic for Diary Generation Control

## 📊 Diary Generation Condition Flow (English)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DIARY GENERATION CONDITION LOGIC                             │
│                    (Based on Diary Agent Specifications)                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Event Input   │    │  Condition      │    │  Diary Count    │    │  Process         │
│                 │───▶│  Evaluation     │───▶│  Determination  │───▶│  Execution       │
│ event_category  │    │                 │    │                 │    │                 │
│ event_name      │    │ Check if diary  │    │ How many        │    │ Run LLM or       │
└─────────────────┘    │ should generate │    │ diaries to make │    │ Skip process    │
         │               └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Validation    │    │   Random         │    │   Count Logic   │    │   Result         │
│   Layer         │    │   Decision       │    │                 │    │   Generation     │
│                 │    │                 │    │ 0 = Skip        │    │                 │
│ Check events.json│    │ Random chance    │    │ 1 = Single      │    │ Generate diary   │
│ Verify format    │    │ to generate      │    │ 2+ = Multiple   │    │ or return        │
└─────────────────┘    │                 │    │                 │    │ skip reason      │
```

## 🔄 Condition Logic Processing Steps

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CONDITION PROCESSING PIPELINE                             │
│                        (Based on Diary Agent Specifications)                    │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 1: Daily Planning (00:00 Daily)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function dailyPlanning():                                                       │
│   // At 00:00 daily, determine the number of diaries to write for the next day  │
│   dailyDiaryCount = random.randint(0, 5)  // Random number between 0-5           │
│   remainingDiaries = dailyDiaryCount                                            │
│   completedDiaryTypes = []  // Track completed types (only one per type)        │
│                                                                                 │
│   return {                                                                     │
│     daily_count: dailyDiaryCount,                                              │
│     remaining: remainingDiaries,                                               │
│     completed_types: completedDiaryTypes                                       │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 2: Event Processing (When Event Occurs)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function processEvent(eventCategory, eventName, dailyPlan):                    │
│   // Check if we still need diaries for today                                  │
│   if dailyPlan.remaining <= 0:                                                  │
│     return {should_process: false, reason: "Daily diary quota reached"}        │
│                                                                                 │
│   // Check if this diary type already completed (only one per type)            │
│   if eventCategory in dailyPlan.completed_types:                              │
│     return {should_process: false, reason: "Diary type already completed"}     │
│                                                                                 │
│   // Randomly determine if diary needs to be written for this event            │
│   shouldGenerate = random.choice([True, False])  // Random chance               │
│                                                                                 │
│   if shouldGenerate:                                                            │
│     return {                                                                   │
│       should_process: True,                                                     │
│       diary_count: 1,                                                          │
│       reason: "Random condition met"                                            │
│     }                                                                          │
│   else:                                                                        │
│     return {                                                                   │
│       should_process: False,                                                    │
│       diary_count: 0,                                                          │
│       reason: "Random condition not met"                                       │
│     }                                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 3: Diary Generation (If Condition Met)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function generateDiary(eventCategory, eventName, dailyPlan):                   │
│   // Call corresponding query function as input parameters                     │
│   eventData = queryEventData(eventCategory, eventName)                         │
│                                                                                 │
│   // Call agent of corresponding type to write the diary                      │
│   diaryEntry = callAgent(eventCategory, eventData)                             │
│                                                                                 │
│   // Update daily plan                                                         │
│   dailyPlan.remaining -= 1                                                     │
│   dailyPlan.completed_types.append(eventCategory)                             │
│                                                                                 │
│   return {                                                                     │
│     diary_entry: diaryEntry,                                                   │
│     updated_plan: dailyPlan                                                    │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 4: Daily Completion Check
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function checkDailyCompletion(dailyPlan):                                      │
│   if dailyPlan.remaining == 0:                                                 │
│     return {                                                                   │
│       daily_complete: True,                                                    │
│       message: "Daily diary quota completed"                                   │
│     }                                                                          │
│   else:                                                                        │
│     return {                                                                   │
│       daily_complete: False,                                                   │
│       remaining: dailyPlan.remaining,                                          │
│       message: f"{dailyPlan.remaining} diaries still needed"                   │
│     }                                                                          │
│                                                                                 │
│   // Note: If insufficient events lead to incomplete diary writing,           │
│   // no make-up writing is required                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🎯 Current Implementation Logic

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CURRENT IMPLEMENTATION                                │
│                    (Based on Diary Agent Specifications)                       │
└─────────────────────────────────────────────────────────────────────────────────┘

Daily Planning Logic (00:00 Daily):
┌─────────────────────────────────────────────────────────────────────────────────┐
│ def daily_planning():                                                           │
│     """At 00:00 daily, determine the number of diaries to write for the next day"""│
│     # Randomly select a number between 0-5                                     │
│     daily_diary_count = random.randint(0, 5)                                    │
│     remaining_diaries = daily_diary_count                                        │
│     completed_diary_types = []  # Track completed types (only one per type)   │
│                                                                                 │
│     return {                                                                    │
│         "daily_count": daily_diary_count,                                       │
│         "remaining": remaining_diaries,                                         │
│         "completed_types": completed_diary_types                                │
│     }                                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘

Event Processing Logic (When Event Occurs):
┌─────────────────────────────────────────────────────────────────────────────────┐
│ def process_event(event_category, event_name, daily_plan):                     │
│     """Process event and determine if diary should be generated"""              │
│                                                                                 │
│     # Check if we still need diaries for today                                 │
│     if daily_plan["remaining"] <= 0:                                            │
│         return {                                                                │
│             "should_process": False,                                            │
│             "reason": "Daily diary quota reached"                               │
│         }                                                                       │
│                                                                                 │
│     # Check if this diary type already completed (only one per type)           │
│     if event_category in daily_plan["completed_types"]:                        │
│         return {                                                                │
│             "should_process": False,                                            │
│             "reason": "Diary type already completed"                            │
│         }                                                                       │
│                                                                                 │
│     # Randomly determine if diary needs to be written for this event           │
│     should_generate = random.choice([True, False])  // Random chance           │
│                                                                                 │
│     if should_generate:                                                          │
│         return {                                                                │
│             "should_process": True,                                             │
│             "diary_count": 1,                                                   │
│             "reason": "Random condition met"                                     │
│         }                                                                       │
│     else:                                                                       │
│         return {                                                                │
│             "should_process": False,                                             │
│             "diary_count": 0,                                                   │
│             "reason": "Random condition not met"                               │
│         }                                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

Process Flow:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. 00:00 Daily → Randomly select 0-5 diaries for the day                       │
│ 2. Event Occurs → Check if diary quota reached                                 │
│ 3. Event Occurs → Check if diary type already completed                        │
│ 4. Event Occurs → Random chance to generate diary                              │
│ 5. If True → Generate 1 diary, update quota and completed types                │
│ 6. If False → Return "Random condition not met"                               │
│ 7. Continue until daily quota reached or no more events                        │
│ 8. Note: If insufficient events, no make-up writing required                   │
└─────────────────────────────────────────────────────────────────────────────────┘

Response Examples:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ SUCCESS CASE (Condition Met):                                                   │
│ {                                                                               │
│   "success": true,                                                              │
│   "message": "Diary generated successfully",                                    │
│   "data": {                                                                     │
│     "diary_generated": true,                                                    │
│     "diary_entry": { ... },                                                     │
│     "daily_plan": {                                                             │
│       "remaining": 2,                                                           │
│       "completed_types": ["weather_events"]                                     │
│     }                                                                           │
│   }                                                                             │
│ }                                                                               │
│                                                                                 │
│ SKIP CASE (Condition Not Met):                                                  │
│ {                                                                               │
│   "success": true,                                                              │
│   "message": "Event processed but no diary generated",                          │
│   "data": {                                                                     │
│     "diary_generated": false,                                                   │
│     "reason": "Random condition not met"                                       │
│   }                                                                             │
│ }                                                                               │
│                                                                                 │
│ QUOTA REACHED CASE:                                                             │
│ {                                                                               │
│   "success": true,                                                              │
│   "message": "Event processed but no diary generated",                          │
│   "data": {                                                                     │
│     "diary_generated": false,                                                   │
│     "reason": "Daily diary quota reached"                                      │
│   }                                                                             │
│ }                                                                               │
│                                                                                 │
│ TYPE COMPLETED CASE:                                                             │
│ {                                                                               │
│   "success": true,                                                              │
│   "message": "Event processed but no diary generated",                          │
│   "data": {                                                                     │
│     "diary_generated": false,                                                   │
│     "reason": "Diary type already completed"                                    │
│   }                                                                             │
│ }                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Advanced Condition Logic (Future Implementation)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ADVANCED CONDITION LOGIC                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

Multi-Factor Condition System:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function advancedConditionCheck(eventCategory, eventName, context):             │
│   baseProbability = 0.5  // 50% base chance                                    │
│   modifiers = []                                                               │
│                                                                                 │
│   // Event importance factor                                                   │
│   importance = getEventImportance(eventCategory, eventName)                     │
│   if importance == "critical":                                                 │
│     modifiers.append(+0.4)  // +40% for critical events                        │
│   elif importance == "important":                                               │
│     modifiers.append(+0.2)  // +20% for important events                       │
│   elif importance == "minor":                                                  │
│     modifiers.append(-0.2)  // -20% for minor events                           │
│                                                                                 │
│   // Time-based factor                                                          │
│   currentHour = getCurrentHour()                                               │
│   if 6 <= currentHour <= 10:  // Morning                                       │
│     modifiers.append(+0.1)   // +10% morning boost                             │
│   elif 22 <= currentHour <= 24:  // Evening                                    │
│     modifiers.append(+0.15)  // +15% evening boost                             │
│                                                                                 │
│   // Recent diary count factor                                                 │
│   recentDiaries = getRecentDiaryCount(hours=24)                               │
│   if recentDiaries > 5:                                                        │
│     modifiers.append(-0.3)  // -30% if too many recent diaries                │
│   elif recentDiaries == 0:                                                     │
│     modifiers.append(+0.2)  // +20% if no recent diaries                        │
│                                                                                 │
│   // User activity factor                                                       │
│   userActivity = getUserActivityLevel()                                        │
│   if userActivity == "high":                                                   │
│     modifiers.append(+0.1)  // +10% for active users                            │
│   elif userActivity == "low":                                                  │
│     modifiers.append(-0.1)  // -10% for inactive users                         │
│                                                                                 │
│   // Calculate final probability                                                │
│   finalProbability = baseProbability + sum(modifiers)                          │
│   finalProbability = max(0.0, min(1.0, finalProbability))  // Clamp to [0,1]  │
│                                                                                 │
│   // Make decision                                                              │
│   shouldGenerate = random.random() < finalProbability                          │
│                                                                                 │
│   return {                                                                     │
│     should_generate: shouldGenerate,                                           │
│     probability: finalProbability,                                              │
│     modifiers: modifiers,                                                      │
│     reason: generateReason(shouldGenerate, finalProbability, modifiers)        │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

Diary Count Logic:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function determineDiaryCount(conditionResult, eventCategory, eventName):       │
│   if not conditionResult.should_generate:                                      │
│     return {count: 0, should_process: false}                                   │
│                                                                                 │
│   // Determine count based on event type                                       │
│   count = 1  // Default                                                        │
│                                                                                 │
│   if eventCategory == "adopted_function":                                     │
│     count = 2  // Major life events get 2 diaries                              │
│   elif eventCategory == "holiday_events":                                     │
│     if eventName == "during_holiday":                                          │
│       count = 2  // Active holidays get 2 diaries                             │
│     else:                                                                      │
│       count = 1  // Other holidays get 1 diary                                │
│   elif eventCategory == "friends_function":                                   │
│     if eventName == "made_new_friend":                                         │
│       count = 2  // New friends get 2 diaries                                  │
│     elif eventName == "friend_deleted":                                        │
│       count = 2  // Lost friends get 2 diaries                                 │
│     else:                                                                      │
│       count = 1  // Other friend events get 1 diary                            │
│   elif eventCategory == "unkeep_interactive":                                 │
│     if "neglect_30_days" in eventName:                                        │
│       count = 2  // Long neglect gets 2 diaries                                │
│     else:                                                                      │
│       count = 1  // Other neglect gets 1 diary                                 │
│                                                                                 │
│   return {                                                                     │
│     count: count,                                                              │
│     should_process: true,                                                      │
│     reason: f"Generating {count} diary(ies) based on event importance"         │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📊 Condition Logic Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CONDITION DECISION TREE                                │
│                    (Based on Diary Agent Specifications)                        │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   00:00 Daily   │
                    │   Planning      │
                    │                 │
                    │ Randomly select │
                    │ 0-5 diaries     │
                    │ for the day     │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Event Occurs   │
                    │  (Category +    │
                    │   Name)         │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Daily Quota     │
                    │  Reached?       │
                    │  ┌─────────────┐│
                    │  │ Check if    ││
                    │  │ remaining   ││
                    │  │ <= 0        ││
                    │  └─────────────┘│
                    └─────────┬───────┘
                              │
                    ┌─────────┴───────┐
                    │                │
                    ▼                ▼
            ┌─────────────┐  ┌─────────────┐
            │     NO      │  │    YES      │
            │             │  │             │
            ▼             │  │             │
    ┌─────────────┐      │  │             │
    │ Diary Type │      │  │             │
    │ Completed? │      │  │             │
    │ ┌─────────┐│      │  │             │
    │ │ Check if││      │  │             │
    │ │ type in ││      │  │             │
    │ │completed││      │  │             │
    │ │ types   ││      │  │             │
    │ └─────────┘│      │  │             │
    └─────┬───────┘      │  │             │
          │              │  │             │
    ┌─────┴───────┐      │  │             │
    │            │      │  │             │
    ▼            ▼      │  │             │
┌─────────┐ ┌─────────┐│  │             │
│   NO    │ │   YES   ││  │             │
│         │ │         ││  │             │
│ Random  │ │ Skip    ││  │             │
│ Chance  │ │ Process ││  │             │
│ to      │ │ Return  ││  │             │
│ Generate│ │ "Type   ││  │             │
│ Diary?  │ │Already  ││  │             │
│         │ │Completed││  │             │
└─────┬───┘ └─────────┘│  │             │
      │                │  │             │
      ▼                │  │             │
┌─────────────┐        │  │             │
│ Random      │        │  │             │
│ Decision    │        │  │             │
│ (True/False)│        │  │             │
└─────┬───────┘        │  │             │
      │                │  │             │
┌─────┴───────┐        │  │             │
│            │        │  │             │
▼            ▼        │  │             │
┌─────────┐ ┌─────────┐│  │             │
│  TRUE   │ │  FALSE  ││  │             │
│         │ │         ││  │             │
│ Generate│ │ Skip    ││  │             │
│ 1 Diary │ │ Process ││  │             │
│ Update  │ │ Return  ││  │             │
│ Quota   │ │ "Random ││  │             │
│ Update  │ │ Not Met"││  │             │
│ Types   │ │         ││  │             │
└─────────┘ └─────────┘│  │             │
                       │  │             │
                       │  │             │
                       ▼  ▼             ▼
                  ┌─────────────┐ ┌─────────────┐
                  │   Success   │ │    Skip     │
                  │  Response   │ │  Response    │
                  │             │ │             │
                  │ JSON with   │ │ JSON with    │
                  │ Diary +     │ │ Reason       │
                  │ Updated     │ │ (Quota/Type/ │
                  │ Plan        │ │ Random)      │
                  └─────────────┘ └─────────────┘
```

## 🎯 Key Points Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           KEY POINTS SUMMARY                                    │
│                    (Based on Diary Agent Specifications)                       │
└─────────────────────────────────────────────────────────────────────────────────┘

1. DAILY PLANNING (00:00 Daily):
   - Randomly select 0-5 diaries for the day
   - Track remaining diaries and completed types
   - Reset daily at midnight

2. EVENT PROCESSING CONDITIONS:
   - Check if daily quota reached (remaining <= 0)
   - Check if diary type already completed (only one per type)
   - Random chance to generate diary for each event

3. DIARY GENERATION RULES:
   - Only one diary entry per type per day
   - Generate 1 diary per successful condition
   - Update quota and completed types after generation

4. COMPLETION LOGIC:
   - Continue until daily quota reached
   - If insufficient events, no make-up writing required
   - Track progress throughout the day

5. RESPONSE STRUCTURE:
   - Always returns success: true
   - diary_generated: true/false
   - Includes reason for decision
   - Includes daily plan updates when applicable
```

---

## 🎯 Summary

The condition logic is a **comprehensive diary generation control system** that implements the diary agent specifications:

### 🔑 **Core Logic:**

1. **Daily Planning (00:00)**: Randomly select 0-5 diaries for the day
2. **Event Processing**: Check quota, type completion, and random chance
3. **Diary Generation**: Generate 1 diary per successful condition
4. **Progress Tracking**: Update quota and completed types

### 📊 **Key Rules:**

- **Daily Quota**: 0-5 diaries per day (randomly determined at midnight)
- **Type Limitation**: Only one diary entry per type per day
- **Random Chance**: Each event has a random chance to generate a diary
- **No Make-up**: If insufficient events, no make-up writing required

### 🎯 **Decision Flow:**

1. **Check Daily Quota** → If reached, skip processing
2. **Check Type Completion** → If already completed, skip processing  
3. **Random Decision** → Random chance to generate diary
4. **Generate Diary** → If condition met, generate 1 diary and update plan

This system ensures **controlled diary generation** while maintaining **variety** and **preventing over-generation** of diaries! 🎉

