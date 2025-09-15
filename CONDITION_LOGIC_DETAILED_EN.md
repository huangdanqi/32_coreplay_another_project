# 🧠 Simple Diary API - Condition Logic Detailed Analysis

## 📊 Condition Logic Flow Diagram (English)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CONDITION LOGIC FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Event Input    │    │  Event Details  │    │ Condition Check │    │ Decision Logic  │
│                 │───▶│   Generation    │───▶│   Engine        │───▶│   Processor     │
│ event_category   │    │                 │    │                 │    │                 │
│ event_name       │    │ Auto-generated  │    │ Multi-factor    │    │ Random + Rules  │
└─────────────────┘    │ based on type   │    │ Analysis        │    │ Combination     │
         │               └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Validation    │    │   Context       │    │   Probability   │    │   Result        │
│   Layer         │    │   Building      │    │   Calculation   │    │   Generation    │
│                 │    │                 │    │                 │    │                 │
│ Check events.json│    │ Add timestamps  │    │ Base: 50%       │    │ Diary or        │
│ Verify format    │    │ Add emotions    │    │ Modifiers: ±20% │    │ Reason message   │
└─────────────────┘    │ Add metadata    │    │ Rules: ±30%     │    └─────────────────┘
```

## 🔄 Detailed Condition Processing Steps

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CONDITION PROCESSING PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 1: Input Validation
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function validateInput(eventCategory, eventName):                               │
│   if eventCategory not in events.json:                                        │
│     return {valid: false, error: "Invalid category"}                           │
│                                                                                 │
│   if eventName not in events.json[eventCategory]:                             │
│     return {valid: false, error: "Invalid event"}                              │
│                                                                                 │
│   return {valid: true, data: {category: eventCategory, name: eventName}}       │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 2: Context Building
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function buildContext(eventCategory, eventName):                               │
│   context = {                                                                  │
│     timestamp: getCurrentTime(),                                               │
│     event_type: eventCategory,                                                 │
│     event_name: eventName,                                                     │
│     auto_generated: true                                                       │
│   }                                                                            │
│                                                                                 │
│   // Add category-specific context                                             │
│   switch eventCategory:                                                        │
│     case "human_toy_interactive_function":                                     │
│       context.interaction_context = buildInteractionContext(eventName)        │
│       context.emotion_base = getEmotionFromEvent(eventName)                    │
│       context.intensity = getIntensityFromEvent(eventName)                     │
│                                                                                 │
│     case "weather_events":                                                     │
│       context.weather_context = buildWeatherContext(eventName)                 │
│       context.seasonal_factor = getSeasonalFactor()                           │
│                                                                                 │
│     case "unkeep_interactive":                                                 │
│       context.neglect_context = buildNeglectContext(eventName)                 │
│       context.time_factor = getTimeFactor(eventName)                           │
│                                                                                 │
│   return context                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 3: Condition Evaluation
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function evaluateCondition(context):                                           │
│   baseProbability = 0.5  // 50% base chance                                    │
│   modifiers = []                                                               │
│                                                                                 │
│   // Event type modifiers                                                      │
│   if context.event_type == "human_toy_interactive_function":                   │
│     if "liked" in context.event_name:                                          │
│       modifiers.append(+0.2)  // +20% for positive interactions               │
│     elif "disliked" in context.event_name:                                    │
│       modifiers.append(-0.1)  // -10% for negative interactions               │
│                                                                                 │
│   // Time-based modifiers                                                      │
│   currentHour = getCurrentHour()                                               │
│   if 6 <= currentHour <= 10:  // Morning                                       │
│     modifiers.append(+0.1)   // +10% morning boost                             │
│   elif 22 <= currentHour <= 24:  // Evening                                    │
│     modifiers.append(+0.15)  // +15% evening boost                            │
│                                                                                 │
│   // Emotional intensity modifiers                                             │
│   if context.intensity == "high":                                             │
│     modifiers.append(+0.2)   // +20% for high intensity                       │
│   elif context.intensity == "low":                                             │
│     modifiers.append(-0.1)   // -10% for low intensity                       │
│                                                                                 │
│   // Calculate final probability                                               │
│   finalProbability = baseProbability + sum(modifiers)                         │
│   finalProbability = max(0.0, min(1.0, finalProbability))  // Clamp to [0,1]  │
│                                                                                 │
│   return {                                                                     │
│     should_generate: random.random() < finalProbability,                       │
│     probability: finalProbability,                                            │
│     modifiers: modifiers,                                                      │
│     reason: generateReason(finalProbability, modifiers)                        │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 4: Decision Processing
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function processDecision(conditionResult, context):                            │
│   if conditionResult.should_generate:                                          │
│     // Generate diary entry                                                    │
│     diaryEntry = generateDiaryEntry(context)                                    │
│     return {                                                                   │
│       success: true,                                                           │
│       diary_generated: true,                                                   │
│       diary_entry: diaryEntry,                                                 │
│       probability: conditionResult.probability,                               │
│       modifiers: conditionResult.modifiers                                     │
│     }                                                                          │
│   else:                                                                        │
│     // Return reason for not generating                                        │
│     return {                                                                   │
│       success: true,                                                           │
│       diary_generated: false,                                                  │
│       reason: conditionResult.reason,                                         │
│       probability: conditionResult.probability,                               │
│       modifiers: conditionResult.modifiers                                     │
│     }                                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🎯 Condition Logic Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DECISION TREE LOGIC                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   Event Input   │
                    │  (Category +    │
                    │   Name)         │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Input Valid?   │
                    │  ┌─────────────┐│
                    │  │ Check in    ││
                    │  │ events.json ││
                    │  └─────────────┘│
                    └─────────┬───────┘
                              │
                    ┌─────────┴───────┐
                    │                │
                    ▼                ▼
            ┌─────────────┐  ┌─────────────┐
            │    YES      │  │     NO       │
            │             │  │             │
            ▼             │  │             │
    ┌─────────────┐      │  │             │
    │ Build       │      │  │             │
    │ Context     │      │  │             │
    └─────┬───────┘      │  │             │
          │              │  │             │
          ▼              │  │             │
    ┌─────────────┐      │  │             │
    │ Calculate   │      │  │             │
    │ Probability │      │  │             │
    └─────┬───────┘      │  │             │
          │              │  │             │
          ▼              │  │             │
    ┌─────────────┐      │  │             │
    │ Apply       │      │  │             │
    │ Modifiers   │      │  │             │
    └─────┬───────┘      │  │             │
          │              │  │             │
          ▼              │  │             │
    ┌─────────────┐      │  │             │
    │ Random      │      │  │             │
    │ Decision    │      │  │             │
    └─────┬───────┘      │  │             │
          │              │  │             │
          ▼              │  │             │
    ┌─────────────┐      │  │             │
    │ Generate    │      │  │             │
    │ Diary?      │      │  │             │
    └─────┬───────┘      │  │             │
          │              │  │             │
    ┌─────┴───────┐      │  │             │
    │            │      │  │             │
    ▼            ▼      │  │             │
┌─────────┐ ┌─────────┐│  │             │
│   YES   │ │   NO    ││  │             │
│         │ │         ││  │             │
│ Call    │ │ Return  ││  │             │
│ LLM     │ │ Reason  ││  │             │
│ Generate│ │ Message ││  │             │
│ Diary   │ │         ││  │             │
└─────────┘ └─────────┘│  │             │
                       │  │             │
                       │  │             │
                       ▼  ▼             ▼
                  ┌─────────────┐ ┌─────────────┐
                  │   Success   │ │    Error    │
                  │  Response   │ │  Response   │
                  │             │ │             │
                  │ JSON with   │ │ JSON with   │
                  │ Diary or    │ │ Error       │
                  │ Reason      │ │ Message     │
                  └─────────────┘ └─────────────┘
```

## 🔧 Modifier System Details

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MODIFIER SYSTEM                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

Base Probability: 50% (0.5)

Event Type Modifiers:
┌─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┐
│    Event Category   │    Event Pattern    │    Modifier Value   │    Reason           │
├─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ human_toy_interactive│ liked_interaction   │ +20% (+0.2)        │ Positive emotion   │
│ human_toy_interactive│ disliked_interaction│ -10% (-0.1)        │ Negative emotion   │
│ human_toy_interactive│ neutral_interaction │ +5% (+0.05)        │ Neutral state      │
│ human_toy_talk      │ positive_dialogue   │ +15% (+0.15)       │ Positive dialogue  │
│ human_toy_talk      │ negative_dialogue   │ -5% (-0.05)        │ Negative dialogue  │
│ unkeep_interactive  │ neglect_1_day       │ +10% (+0.1)        │ Short neglect      │
│ unkeep_interactive  │ neglect_7_days       │ -15% (-0.15)       │ Medium neglect     │
│ unkeep_interactive  │ neglect_30_days      │ -25% (-0.25)       │ Long neglect       │
│ weather_events      │ favorite_weather     │ +25% (+0.25)       │ Preferred weather  │
│ weather_events      │ dislike_weather      │ -20% (-0.2)        │ Disliked weather   │
│ holiday_events      │ approaching_holiday  │ +30% (+0.3)        │ Anticipation       │
│ holiday_events      │ during_holiday       │ +35% (+0.35)       │ Active celebration │
│ holiday_events      │ holiday_ends          │ -10% (-0.1)        │ Post-holiday blues │
│ friends_function    │ made_new_friend      │ +40% (+0.4)        │ Social excitement │
│ friends_function    │ friend_deleted       │ -30% (-0.3)        │ Social loss        │
│ friends_function    │ liked_5_plus          │ +20% (+0.2)        │ Social validation  │
│ adopted_function    │ toy_claimed           │ +50% (+0.5)        │ Major life event   │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘

Time-based Modifiers:
┌─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┐
│    Time Period      │    Hour Range       │    Modifier Value   │    Reason           │
├─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Early Morning       │ 06:00 - 10:00      │ +10% (+0.1)        │ Fresh start         │
│ Late Morning        │ 10:00 - 12:00      │ +5% (+0.05)        │ Active period       │
│ Afternoon           │ 12:00 - 18:00      │ +0% (0.0)          │ Neutral period      │
│ Evening             │ 18:00 - 22:00      │ +15% (+0.15)       │ Reflection time     │
│ Late Night          │ 22:00 - 24:00      │ +20% (+0.2)        │ Deep reflection     │
│ Night               │ 00:00 - 06:00      │ -10% (-0.1)        │ Sleep time          │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘

Intensity Modifiers:
┌─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┐
│    Intensity Level  │    Description     │    Modifier Value   │    Reason           │
├─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ High                │ Strong emotions    │ +20% (+0.2)        │ Memorable events    │
│ Medium              │ Moderate emotions  │ +0% (0.0)          │ Standard events     │
│ Low                 │ Mild emotions      │ -10% (-0.1)        │ Less memorable      │
│ Extreme             │ Intense emotions  │ +30% (+0.3)        │ Highly memorable    │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘

Frequency Modifiers:
┌─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┐
│    Frequency        │    Pattern          │    Modifier Value   │    Reason           │
├─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ First Time          │ Initial occurrence │ +25% (+0.25)       │ Novelty factor      │
│ Occasional          │ 2-5 times           │ +10% (+0.1)        │ Regular pattern    │
│ Frequent            │ 5+ times            │ -5% (-0.05)        │ Routine behavior   │
│ Rare                │ <1% occurrence      │ +40% (+0.4)        │ Uniqueness factor  │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘
```

## 🎲 Probability Calculation Examples

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        PROBABILITY CALCULATION EXAMPLES                         │
└─────────────────────────────────────────────────────────────────────────────────┘

Example 1: Positive Interaction in Evening
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Event: human_toy_interactive_function + liked_interaction_once                  │
│ Time: 20:30 (Evening)                                                          │
│                                                                                 │
│ Base Probability: 50% (0.5)                                                    │
│ Event Modifier: +20% (liked interaction)                                        │
│ Time Modifier: +15% (evening)                                                  │
│ Intensity Modifier: +10% (medium-high intensity)                               │
│                                                                                 │
│ Final Probability = 0.5 + 0.2 + 0.15 + 0.1 = 0.95 (95%)                      │
│ Result: Very likely to generate diary                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

Example 2: Negative Weather in Night
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Event: weather_events + dislike_weather                                         │
│ Time: 02:15 (Night)                                                            │
│                                                                                 │
│ Base Probability: 50% (0.5)                                                    │
│ Event Modifier: -20% (dislike weather)                                         │
│ Time Modifier: -10% (night)                                                    │
│ Intensity Modifier: -5% (low intensity)                                        │
│                                                                                 │
│ Final Probability = 0.5 - 0.2 - 0.1 - 0.05 = 0.15 (15%)                      │
│ Result: Unlikely to generate diary                                              │
└─────────────────────────────────────────────────────────────────────────────────┘

Example 3: Holiday Celebration in Morning
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Event: holiday_events + during_holiday                                          │
│ Time: 09:30 (Morning)                                                          │
│                                                                                 │
│ Base Probability: 50% (0.5)                                                    │
│ Event Modifier: +35% (during holiday)                                           │
│ Time Modifier: +10% (morning)                                                  │
│ Intensity Modifier: +20% (high intensity)                                      │
│                                                                                 │
│ Final Probability = 0.5 + 0.35 + 0.1 + 0.2 = 1.15 → 1.0 (100%)               │
│ Result: Guaranteed to generate diary                                           │
└─────────────────────────────────────────────────────────────────────────────────┘

Example 4: Long Neglect in Afternoon
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Event: unkeep_interactive + neglect_30_days_no_interaction                     │
│ Time: 15:45 (Afternoon)                                                        │
│                                                                                 │
│ Base Probability: 50% (0.5)                                                    │
│ Event Modifier: -25% (long neglect)                                            │
│ Time Modifier: +0% (afternoon)                                                 │
│ Intensity Modifier: -15% (negative intensity)                                  │
│                                                                                 │
│ Final Probability = 0.5 - 0.25 - 0.0 - 0.15 = 0.1 (10%)                     │
│ Result: Very unlikely to generate diary                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Condition Logic State Machine

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           STATE MACHINE LOGIC                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

States and Transitions:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   INITIAL       │───▶│   VALIDATING    │───▶│   PROCESSING    │───▶│   DECIDING      │
│                 │    │                 │    │                 │    │                 │
│ Waiting for     │    │ Checking input  │    │ Building        │    │ Calculating     │
│ input           │    │ validity         │    │ context         │    │ probability     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ERROR         │    │   CONTEXT       │    │   MODIFIER      │    │   RESULT        │
│                 │    │   BUILDING      │    │   APPLYING      │    │                 │
│ Invalid input   │    │ Adding metadata │    │ Adjusting       │    │ Generating      │
│ or format       │    │ and timestamps  │    │ probabilities   │    │ final decision  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RESPONSE      │    │   ENHANCED      │    │   FINALIZED     │    │   OUTPUT        │
│                 │    │   CONTEXT       │    │   PROBABILITY   │    │                 │
│ Error message   │    │ Ready for       │    │ Ready for       │    │ Diary or        │
│ to client       │    │ processing      │    │ decision        │    │ reason message  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🎯 Summary

The condition logic system uses a sophisticated multi-factor approach:

1. **Base Probability**: 50% starting point
2. **Event Modifiers**: Based on event type and emotional content
3. **Time Modifiers**: Based on time of day and human behavior patterns
4. **Intensity Modifiers**: Based on emotional intensity of events
5. **Frequency Modifiers**: Based on novelty and rarity of events

The final probability is calculated by summing all modifiers and clamping between 0% and 100%, then a random decision is made based on this probability.

