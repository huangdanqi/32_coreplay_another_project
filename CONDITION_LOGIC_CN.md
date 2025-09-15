# 🎯 简单日记API - 日记生成条件逻辑

## 📊 日记生成条件流程图 (中文版)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        日记生成条件逻辑                                          │
│                    (基于日记代理规范)                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   事件输入       │    │   条件评估      │    │   日记数量      │    │   处理执行      │
│                 │───▶│                 │───▶│   确定          │───▶│                 │
│ 事件类别         │    │ 检查是否应该    │    │ 生成多少        │    │ 运行LLM或       │
│ 事件名称         │    │ 生成日记        │    │ 日记            │    │ 跳过处理        │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   验证层         │    │   随机决策       │    │   数量逻辑      │    │   结果生成      │
│                 │    │                 │    │                 │    │                 │
│ 检查events.json │    │ 随机概率         │    │ 0 = 跳过        │    │ 生成日记或      │
│ 验证格式        │    │ 生成            │    │ 1 = 单个        │    │ 返回跳过原因    │
└─────────────────┘    │                 │    │ 2+ = 多个       │    └─────────────────┘
```

## 🔄 条件逻辑处理步骤

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            条件处理管道                                          │
│                    (基于日记代理规范)                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

步骤1: 每日规划 (00:00 每日)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function dailyPlanning():                                                       │
│   // 在00:00每日，确定第二天要写的日记数量                                       │
│   dailyDiaryCount = random.randint(0, 5)  // 随机选择0-5之间的数字              │
│   remainingDiaries = dailyDiaryCount                                            │
│   completedDiaryTypes = []  // 跟踪已完成的类型 (每种类型只能一个)               │
│                                                                                 │
│   return {                                                                     │
│     daily_count: dailyDiaryCount,                                              │
│     remaining: remainingDiaries,                                               │
│     completed_types: completedDiaryTypes                                       │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

步骤2: 事件处理 (当事件发生时)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function processEvent(eventCategory, eventName, dailyPlan):                    │
│   // 检查今天是否还需要日记                                                      │
│   if dailyPlan.remaining <= 0:                                                  │
│     return {should_process: false, reason: "每日日记配额已满"}                  │
│                                                                                 │
│   // 检查此日记类型是否已完成 (每种类型只能一个)                                 │
│   if eventCategory in dailyPlan.completed_types:                              │
│     return {should_process: false, reason: "日记类型已完成"}                     │
│                                                                                 │
│   // 随机确定是否需要为此事件写日记                                              │
│   shouldGenerate = random.choice([True, False])  // 随机概率                    │
│                                                                                 │
│   if shouldGenerate:                                                            │
│     return {                                                                   │
│       should_process: True,                                                     │
│       diary_count: 1,                                                          │
│       reason: "随机条件满足"                                                    │
│     }                                                                          │
│   else:                                                                        │
│     return {                                                                   │
│       should_process: False,                                                   │
│       diary_count: 0,                                                          │
│       reason: "随机条件未满足"                                                  │
│     }                                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

步骤3: 日记生成 (如果条件满足)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function generateDiary(eventCategory, eventName, dailyPlan):                   │
│   // 调用相应的查询函数作为输入参数                                              │
│   eventData = queryEventData(eventCategory, eventName)                         │
│                                                                                 │
│   // 调用相应类型的代理来写日记                                                  │
│   diaryEntry = callAgent(eventCategory, eventData)                             │
│                                                                                 │
│   // 更新每日计划                                                               │
│   dailyPlan.remaining -= 1                                                     │
│   dailyPlan.completed_types.append(eventCategory)                              │
│                                                                                 │
│   return {                                                                     │
│     diary_entry: diaryEntry,                                                   │
│     updated_plan: dailyPlan                                                    │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

步骤4: 每日完成检查
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function checkDailyCompletion(dailyPlan):                                      │
│   if dailyPlan.remaining == 0:                                                 │
│     return {                                                                   │
│       daily_complete: True,                                                    │
│       message: "每日日记配额完成"                                               │
│     }                                                                          │
│   else:                                                                        │
│     return {                                                                   │
│       daily_complete: False,                                                  │
│       remaining: dailyPlan.remaining,                                          │
│       message: f"还需要{dailyPlan.remaining}个日记"                            │
│     }                                                                          │
│                                                                                 │
│   // 注意: 如果事件不足导致日记写作任务不完整，                                   │
│   // 不需要补写                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🎯 当前实现逻辑

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              当前实现                                            │
│                    (基于日记代理规范)                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

每日规划逻辑 (00:00 每日):
┌─────────────────────────────────────────────────────────────────────────────────┐
│ def daily_planning():                                                           │
│     """在00:00每日，确定第二天要写的日记数量"""                                   │
│     # 随机选择0-5之间的数字                                                      │
│     daily_diary_count = random.randint(0, 5)                                    │
│     remaining_diaries = daily_diary_count                                        │
│     completed_diary_types = []  # 跟踪已完成的类型 (每种类型只能一个)             │
│                                                                                 │
│     return {                                                                    │
│         "daily_count": daily_diary_count,                                       │
│         "remaining": remaining_diaries,                                          │
│         "completed_types": completed_diary_types                                │
│     }                                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘

事件处理逻辑 (当事件发生时):
┌─────────────────────────────────────────────────────────────────────────────────┐
│ def process_event(event_category, event_name, daily_plan):                     │
│     """处理事件并确定是否应该生成日记"""                                         │
│                                                                                 │
│     # 检查今天是否还需要日记                                                    │
│     if daily_plan["remaining"] <= 0:                                            │
│         return {                                                                │
│             "should_process": False,                                            │
│             "reason": "每日日记配额已满"                                        │
│         }                                                                       │
│                                                                                 │
│     # 检查此日记类型是否已完成 (每种类型只能一个)                               │
│     if event_category in daily_plan["completed_types"]:                        │
│         return {                                                                │
│             "should_process": False,                                            │
│             "reason": "日记类型已完成"                                          │
│         }                                                                       │
│                                                                                 │
│     # 随机确定是否需要为此事件写日记                                            │
│     should_generate = random.choice([True, False])  // 随机概率                │
│                                                                                 │
│     if should_generate:                                                          │
│         return {                                                                │
│             "should_process": True,                                             │
│             "diary_count": 1,                                                   │
│             "reason": "随机条件满足"                                            │
│         }                                                                       │
│     else:                                                                       │
│         return {                                                                │
│             "should_process": False,                                             │
│             "diary_count": 0,                                                   │
│             "reason": "随机条件未满足"                                          │
│         }                                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

处理流程:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. 00:00 每日 → 随机选择0-5个日记                                               │
│ 2. 事件发生 → 检查日记配额是否已满                                              │
│ 3. 事件发生 → 检查日记类型是否已完成                                            │
│ 4. 事件发生 → 随机概率生成日记                                                  │
│ 5. 如果True → 生成1个日记，更新配额和已完成类型                                 │
│ 6. 如果False → 返回"随机条件未满足"                                            │
│ 7. 继续直到每日配额完成或没有更多事件                                           │
│ 8. 注意: 如果事件不足，不需要补写                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

响应示例:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 成功案例 (条件满足):                                                             │
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
│ 跳过案例 (条件不满足):                                                           │
│ {                                                                               │
│   "success": true,                                                              │
│   "message": "Event processed but no diary generated",                          │
│   "data": {                                                                     │
│     "diary_generated": false,                                                   │
│     "reason": "Random condition not met"                                       │
│   }                                                                             │
│ }                                                                               │
│                                                                                 │
│ 配额已满案例:                                                                    │
│ {                                                                               │
│   "success": true,                                                              │
│   "message": "Event processed but no diary generated",                          │
│   "data": {                                                                     │
│     "diary_generated": false,                                                   │
│     "reason": "Daily diary quota reached"                                      │
│   }                                                                             │
│ }                                                                               │
│                                                                                 │
│ 类型已完成案例:                                                                  │
│ {                                                                               │
│   "success": true,                                                              │
│   "message": "Event processed but no diary generated",                          │
│   "data": {                                                                     │
│     "diary_generated": false,                                                   │
│     "reason": "Diary type already completed"                                   │
│   }                                                                             │
│ }                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 高级条件逻辑 (未来实现)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            高级条件逻辑                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

多因素条件系统:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function advancedConditionCheck(eventCategory, eventName, context):             │
│   baseProbability = 0.5  // 50% 基础概率                                        │
│   modifiers = []                                                               │
│                                                                                 │
│   // 事件重要性因素                                                             │
│   importance = getEventImportance(eventCategory, eventName)                     │
│   if importance == "critical":                                                 │
│     modifiers.append(+0.4)  // 关键事件 +40%                                   │
│   elif importance == "important":                                               │
│     modifiers.append(+0.2)  // 重要事件 +20%                                   │
│   elif importance == "minor":                                                  │
│     modifiers.append(-0.2)  // 次要事件 -20%                                   │
│                                                                                 │
│   // 基于时间的因素                                                             │
│   currentHour = getCurrentHour()                                               │
│   if 6 <= currentHour <= 10:  // 早晨                                           │
│     modifiers.append(+0.1)   // 早晨加成 +10%                                   │
│   elif 22 <= currentHour <= 24:  // 晚上                                        │
│     modifiers.append(+0.15)  // 晚上加成 +15%                                  │
│                                                                                 │
│   // 最近日记数量因素                                                           │
│   recentDiaries = getRecentDiaryCount(hours=24)                               │
│   if recentDiaries > 5:                                                        │
│     modifiers.append(-0.3)  // 最近日记太多 -30%                               │
│   elif recentDiaries == 0:                                                     │
│     modifiers.append(+0.2)  // 没有最近日记 +20%                               │
│                                                                                 │
│   // 用户活跃度因素                                                             │
│   userActivity = getUserActivityLevel()                                        │
│   if userActivity == "high":                                                   │
│     modifiers.append(+0.1)  // 活跃用户 +10%                                    │
│   elif userActivity == "low":                                                  │
│     modifiers.append(-0.1)  // 不活跃用户 -10%                                  │
│                                                                                 │
│   // 计算最终概率                                                               │
│   finalProbability = baseProbability + sum(modifiers)                          │
│   finalProbability = max(0.0, min(1.0, finalProbability))  // 限制在[0,1]      │
│                                                                                 │
│   // 做决策                                                                     │
│   shouldGenerate = random.random() < finalProbability                          │
│                                                                                 │
│   return {                                                                     │
│     should_generate: shouldGenerate,                                           │
│     probability: finalProbability,                                              │
│     modifiers: modifiers,                                                       │
│     reason: generateReason(shouldGenerate, finalProbability, modifiers)        │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

日记数量逻辑:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ function determineDiaryCount(conditionResult, eventCategory, eventName):       │
│   if not conditionResult.should_generate:                                      │
│     return {count: 0, should_process: false}                                   │
│                                                                                 │
│   // 基于事件类型确定数量                                                       │
│   count = 1  // 默认                                                            │
│                                                                                 │
│   if eventCategory == "adopted_function":                                      │
│     count = 2  // 重大生活事件生成2个日记                                       │
│   elif eventCategory == "holiday_events":                                      │
│     if eventName == "during_holiday":                                          │
│       count = 2  // 活跃假期生成2个日记                                        │
│     else:                                                                       │
│       count = 1  // 其他假期生成1个日记                                        │
│   elif eventCategory == "friends_function":                                    │
│     if eventName == "made_new_friend":                                         │
│       count = 2  // 新朋友生成2个日记                                           │
│     elif eventName == "friend_deleted":                                        │
│       count = 2  // 失去朋友生成2个日记                                         │
│     else:                                                                       │
│       count = 1  // 其他朋友事件生成1个日记                                     │
│   elif eventCategory == "unkeep_interactive":                                  │
│     if "neglect_30_days" in eventName:                                         │
│       count = 2  // 长期忽视生成2个日记                                         │
│     else:                                                                       │
│       count = 1  // 其他忽视生成1个日记                                        │
│                                                                                 │
│   return {                                                                     │
│     count: count,                                                              │
│     should_process: true,                                                      │
│     reason: f"基于事件重要性生成{count}个日记"                                   │
│   }                                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📊 条件逻辑决策树

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            条件决策树                                            │
│                    (基于日记代理规范)                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   00:00 每日   │
                    │   规划         │
                    │                 │
                    │ 随机选择        │
                    │ 0-5个日记      │
                    │ 用于当天        │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   事件发生      │
                    │  (类别 +        │
                    │   名称)         │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  每日配额       │
                    │  已满?          │
                    │  ┌─────────────┐│
                    │  │ 检查是否     ││
                    │  │ remaining   ││
                    │  │ <= 0        ││
                    │  └─────────────┘│
                    └─────────┬───────┘
                              │
                    ┌─────────┴───────┐
                    │                │
                    ▼                ▼
            ┌─────────────┐  ┌─────────────┐
            │    否       │  │    是       │
            │             │  │             │
            ▼             │  │             │
    ┌─────────────┐      │  │             │
    │ 日记类型    │      │  │             │
    │ 已完成?     │      │  │             │
    │ ┌─────────┐│      │  │             │
    │ │ 检查是否 ││      │  │             │
    │ │ 类型在  ││      │  │             │
    │ │ 已完成  ││      │  │             │
    │ │ 类型中  ││      │  │             │
    │ └─────────┘│      │  │             │
    └─────┬───────┘      │  │             │
          │              │  │             │
    ┌─────┴───────┐      │  │             │
    │            │      │  │             │
    ▼            ▼      │  │             │
┌─────────┐ ┌─────────┐│  │             │
│   否    │ │   是    ││  │             │
│         │ │         ││  │             │
│ 随机    │ │ 跳过    ││  │             │
│ 概率    │ │ 处理    ││  │             │
│ 生成    │ │ 返回    ││  │             │
│ 日记?   │ │ "类型   ││  │             │
│         │ │ 已完成" ││  │             │
└─────┬───┘ └─────────┘│  │             │
      │                │  │             │
      ▼                │  │             │
┌─────────────┐        │  │             │
│ 随机        │        │  │             │
│ 决策        │        │  │             │
│ (真/假)     │        │  │             │
└─────┬───────┘        │  │             │
      │                │  │             │
┌─────┴───────┐        │  │             │
│            │        │  │             │
▼            ▼        │  │             │
┌─────────┐ ┌─────────┐│  │             │
│  真     │ │  假     ││  │             │
│         │ │         ││  │             │
│ 生成    │ │ 跳过    ││  │             │
│ 1个日记 │ │ 处理    ││  │             │
│ 更新    │ │ 返回    ││  │             │
│ 配额    │ │ "随机   ││  │             │
│ 更新    │ │ 未满足" ││  │             │
│ 类型    │ │         ││  │             │
└─────────┘ └─────────┘│  │             │
                       │  │             │
                       │  │             │
                       ▼  ▼             ▼
                  ┌─────────────┐ ┌─────────────┐
                  │   成功      │ │   跳过      │
                  │   响应      │ │   响应      │
                  │             │ │             │
                  │ 包含日记+   │ │ 包含原因    │
                  │ 更新计划    │ │ (配额/类型/ │
                  │ 的JSON      │ │ 随机)的JSON │
                  └─────────────┘ └─────────────┘
```

## 🎯 关键要点总结

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            关键要点总结                                          │
│                    (基于日记代理规范)                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

1. 每日规划 (00:00 每日):
   - 随机选择0-5个日记用于当天
   - 跟踪剩余日记和已完成类型
   - 在午夜重置每日

2. 事件处理条件:
   - 检查每日配额是否已满 (remaining <= 0)
   - 检查日记类型是否已完成 (每种类型只能一个)
   - 随机概率为每个事件生成日记

3. 日记生成规则:
   - 每天每种类型只能一个日记条目
   - 每个成功条件生成1个日记
   - 生成后更新配额和已完成类型

4. 完成逻辑:
   - 继续直到每日配额完成
   - 如果事件不足，不需要补写
   - 全天跟踪进度

5. 响应结构:
   - 总是返回 success: true
   - diary_generated: true/false
   - 包含决策原因
   - 适用时包含每日计划更新
```

## 🔍 实际代码示例

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            实际代码实现                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

当前实现 (simple_diary_api.py):
┌─────────────────────────────────────────────────────────────────────────────────┐
│ def should_generate_diary(self, event_category: str, event_name: str) -> bool:  │
│     """确定是否应该为此事件生成日记。"""                                         │
│     # 随机决策 (50% 概率)                                                       │
│     return random.choice([True, False])                                        │
│                                                                                 │
│ def process_event(self, event_category: str, event_name: str):                │
│     # 1. 验证事件                                                               │
│     if not self.validate_event(event_category, event_name):                    │
│         return {"success": False, "error": "Invalid event"}                     │
│                                                                                 │
│     # 2. 检查条件                                                               │
│     if not self.should_generate_diary(event_category, event_name):            │
│         return {                                                               │
│             "success": True,                                                    │
│             "diary_generated": False,                                           │
│             "reason": "Random condition not met"                               │
│         }                                                                      │
│                                                                                 │
│     # 3. 条件满足 - 生成日记                                                    │
│     diary_entry = self.generate_diary_entry(event_category, event_name)        │
│     return {                                                                   │
│         "success": True,                                                        │
│         "diary_generated": True,                                               │
│         "diary_entry": diary_entry                                             │
│     }                                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

未来实现示例:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ def advanced_should_generate_diary(self, event_category: str, event_name: str): │
│     """高级条件检查 - 多因素决策"""                                             │
│     base_prob = 0.5                                                             │
│     modifiers = []                                                              │
│                                                                                 │
│     # 事件重要性                                                               │
│     if event_category == "adopted_function":                                   │
│         modifiers.append(+0.4)  # 重大事件                                     │
│     elif event_category == "weather_events":                                   │
│         modifiers.append(-0.1)  # 普通事件                                     │
│                                                                                 │
│     # 时间因素                                                                  │
│     hour = datetime.now().hour                                                  │
│     if 6 <= hour <= 10:  # 早晨                                                │
│         modifiers.append(+0.1)                                                 │
│     elif 22 <= hour <= 24:  # 晚上                                              │
│         modifiers.append(+0.15)                                                │
│                                                                                 │
│     # 计算最终概率                                                              │
│     final_prob = base_prob + sum(modifiers)                                    │
│     final_prob = max(0.0, min(1.0, final_prob))                               │
│                                                                                 │
│     # 随机决策                                                                  │
│     return random.random() < final_prob                                         │
│                                                                                 │
│ def determine_diary_count(self, event_category: str, event_name: str) -> int:  │
│     """确定生成日记的数量"""                                                    │
│     if event_category == "adopted_function":                                   │
│         return 2  # 重大事件生成2个日记                                         │
│     elif event_category == "holiday_events":                                   │
│         if event_name == "during_holiday":                                     │
│             return 2  # 活跃假期生成2个日记                                     │
│         else:                                                                   │
│             return 1  # 其他假期生成1个日记                                     │
│     else:                                                                       │
│         return 1  # 默认生成1个日记                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 总结

条件逻辑是一个**综合日记生成控制系统**，它实现了日记代理规范:

### 🔑 **核心逻辑:**

1. **每日规划 (00:00)**: 随机选择0-5个日记用于当天
2. **事件处理**: 检查配额、类型完成和随机概率
3. **日记生成**: 每个成功条件生成1个日记
4. **进度跟踪**: 更新配额和已完成类型

### 📊 **关键规则:**

- **每日配额**: 每天0-5个日记 (午夜随机确定)
- **类型限制**: 每天每种类型只能一个日记条目
- **随机概率**: 每个事件都有随机概率生成日记
- **无需补写**: 如果事件不足，不需要补写

### 🎯 **决策流程:**

1. **检查每日配额** → 如果已满，跳过处理
2. **检查类型完成** → 如果已完成，跳过处理  
3. **随机决策** → 随机概率生成日记
4. **生成日记** → 如果条件满足，生成1个日记并更新计划

这个系统确保**受控的日记生成**，同时保持**多样性**并**防止过度生成**日记! 🎉

