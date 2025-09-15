# 🎯 简单日记API - 用户指南

## 📋 概述

简单日记API是一个精简的REST API，用于处理来自`diary_agent/events.json`的事件，并在满足条件时生成日记条目。它只需要**事件类别**和**事件名称**——无需复杂的事件详情！

## 🚀 快速开始

### 1. 启动API服务器

```bash
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 启动服务器
python simple_diary_api.py --port 5003
```

### 2. 测试API

```bash
# 运行测试客户端
python test_simple_api.py
```

## 🌐 API端点

| 方法 | 端点 | 描述 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/events` | 获取events.json中的所有事件 |
| `POST` | `/api/diary/process` | 处理单个事件 |
| `POST` | `/api/diary/batch-process` | 处理多个事件 |
| `POST` | `/api/diary/test` | 使用示例事件进行测试 |

## 📝 输入格式

### 单个事件处理

**端点:** `POST /api/diary/process`

**输入（简化版）:**
```json
{
  "event_category": "human_toy_interactive_function",
  "event_name": "liked_interaction_once"
}
```

**必需字段:**
- `event_category`: 来自events.json的事件类别
- `event_name`: 来自events.json的具体事件名称

**无需`event_details`！** API会自动生成适当的详情。

### 批量事件处理

**端点:** `POST /api/diary/batch-process`

**输入:**
```json
{
  "events": [
    {
      "event_category": "human_toy_interactive_function",
      "event_name": "liked_interaction_once"
    },
    {
      "event_category": "human_toy_talk",
      "event_name": "positive_emotional_dialogue"
    },
    {
      "event_category": "weather_events",
      "event_name": "favorite_weather"
    }
  ]
}
```

## 📤 输出格式

### 成功生成日记

```json
{
  "success": true,
  "message": "Diary generated successfully",
  "data": {
    "event_category": "human_toy_interactive_function",
    "event_name": "liked_interaction_once",
    "diary_generated": true,
    "diary_entry": {
      "title": "被抚摸的快乐",
      "content": "今天主人轻轻地抚摸了我，感觉特别温暖和舒适...",
      "emotion_tags": ["开心", "温暖"],
      "timestamp": "2025-09-04T19:38:07.921834",
      "entry_id": "1_simple_event_a5fd1572-7f7d-47f8-8d0b-4f6168441356_1757039887",
      "agent_type": "interactive_agent",
      "llm_provider": "ollama_qwen3"
    }
  },
  "timestamp": "2025-09-04T19:39:06.367488"
}
```

### 事件已处理（未生成日记）

```json
{
  "success": true,
  "message": "Event processed but no diary generated",
  "data": {
    "event_category": "human_toy_talk",
    "event_name": "positive_emotional_dialogue",
    "diary_generated": false,
    "reason": "Random condition not met"
  },
  "timestamp": "2025-09-04T19:39:08.407585"
}
```

### 错误响应

```json
{
  "success": false,
  "message": "Event not found in events.json",
  "error": "Invalid event data",
  "timestamp": "2025-09-04T19:39:08.407585"
}
```

## 📚 可用事件类别

API支持来自`events.json`的**10个事件类别**：

### 1. **human_toy_interactive_function** (6个事件)
- `liked_interaction_once` - 喜欢单次互动
- `liked_interaction_3_to_5_times` - 喜欢3-5次互动
- `liked_interaction_over_5_times` - 喜欢5次以上互动
- `disliked_interaction_once` - 不喜欢单次互动
- `disliked_interaction_3_to_5_times` - 不喜欢3-5次互动
- `neutral_interaction_over_5_times` - 中性5次以上互动

### 2. **human_toy_talk** (2个事件)
- `positive_emotional_dialogue` - 积极情感对话
- `negative_emotional_dialogue` - 消极情感对话

### 3. **unkeep_interactive** (9个事件)
- `neglect_1_day_no_dialogue` - 1天无对话
- `neglect_1_day_no_interaction` - 1天无互动
- `neglect_3_days_no_dialogue` - 3天无对话
- `neglect_3_days_no_interaction` - 3天无互动
- `neglect_7_days_no_dialogue` - 7天无对话
- `neglect_7_days_no_interaction` - 7天无互动
- `neglect_15_days_no_interaction` - 15天无互动
- `neglect_30_days_no_dialogue` - 30天无对话
- `neglect_30_days_no_interaction` - 30天无互动

### 4. **weather_events** (4个事件)
- `favorite_weather` - 喜欢的天气
- `dislike_weather` - 不喜欢的天气
- `favorite_season` - 喜欢的季节
- `dislike_season` - 不喜欢的季节

### 5. **seasonal_events** (2个事件)
- `favorite_season` - 喜欢的季节
- `dislike_season` - 不喜欢的季节

### 6. **trending_events** (2个事件)
- `celebration` - 庆祝事件
- `disaster` - 灾难事件

### 7. **holiday_events** (3个事件)
- `approaching_holiday` - 临近假期
- `during_holiday` - 假期期间
- `holiday_ends` - 假期结束

### 8. **friends_function** (8个事件)
- `made_new_friend` - 交新朋友
- `friend_deleted` - 删除朋友
- `liked_single` - 单次点赞
- `liked_3_to_5` - 3-5次点赞
- `liked_5_plus` - 5次以上点赞
- `disliked_single` - 单次不喜欢
- `disliked_3_to_5` - 3-5次不喜欢
- `disliked_5_plus` - 5次以上不喜欢

### 9. **same_frequency** (1个事件)
- `close_friend_frequency` - 密友同频

### 10. **adopted_function** (1个事件)
- `toy_claimed` - 玩具被认领

## 🔧 使用示例

### 示例1: 单个事件 (PowerShell)

```powershell
$body = '{"event_category": "human_toy_interactive_function", "event_name": "liked_interaction_once"}'
Invoke-WebRequest -Uri "http://localhost:5003/api/diary/process" -Method POST -Body $body -ContentType "application/json"
```

### 示例2: 单个事件 (Python)

```python
import requests

payload = {
    "event_category": "human_toy_interactive_function",
    "event_name": "liked_interaction_once"
}

response = requests.post("http://localhost:5003/api/diary/process", json=payload)
print(response.json())
```

### 示例3: 批量处理 (Python)

```python
import requests

payload = {
    "events": [
        {
            "event_category": "weather_events",
            "event_name": "favorite_weather"
        },
        {
            "event_category": "unkeep_interactive",
            "event_name": "neglect_1_day_no_dialogue"
        }
    ]
}

response = requests.post("http://localhost:5003/api/diary/batch-process", json=payload)
print(response.json())
```

### 示例4: 获取所有事件

```python
import requests

response = requests.get("http://localhost:5003/api/events")
events = response.json()
print(f"找到 {len(events['data'])} 个事件类别")
```

## 🎯 主要特性

### ✅ **简化输入**
- 只需要`event_category`和`event_name`
- 无需复杂的`event_details`
- 自动生成适当的事件详情

### ✅ **条件处理**
- 随机决定是否生成日记（50%概率）
- 仅在满足条件时返回日记
- 当未生成日记时提供原因

### ✅ **事件验证**
- 根据`events.json`验证事件
- 对无效事件返回错误
- 支持所有10个事件类别

### ✅ **自动生成详情**
- 根据事件名称创建适当的事件详情
- 包含时间戳、情感和上下文
- 为每种事件类型定制详情

### ✅ **多种输出格式**
- 单个事件处理
- 批量事件处理
- 健康检查和事件列表

## 🚨 错误处理

### 常见错误响应

**1. 缺少必需字段:**
```json
{
  "success": false,
  "message": "Missing required field: event_category",
  "error": "Invalid request data"
}
```

**2. 无效事件:**
```json
{
  "success": false,
  "message": "Event not found in events.json",
  "error": "Invalid event data"
}
```

**3. 无JSON数据:**
```json
{
  "success": false,
  "message": "No JSON data provided",
  "error": "Missing request body"
}
```

## 🌐 服务器配置

### 默认设置
- **主机:** `0.0.0.0` (所有接口)
- **端口:** `5003`
- **调试模式:** `False`
- **CORS:** 对所有来源启用

### 更改端口
```bash
python simple_diary_api.py --port 8080
```

### 生产部署
对于生产环境，请将Flask开发服务器替换为生产WSGI服务器，如Gunicorn：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5003 simple_diary_api:app
```

## 📊 性能

### 响应时间
- **健康检查:** ~10ms
- **获取事件:** ~50ms
- **单个事件处理:** ~1-2秒（包括LLM生成）
- **批量处理:** 每个事件~1-2秒

### LLM提供商
- **默认:** `ollama_qwen3`
- **备用:** `llm_qwen`, `llm_deepseek`
- **熔断器:** 自动故障转移

## 🔄 迁移到云服务器

要部署到云服务器，只需更改基础URL：

```python
# 本地开发
base_url = "http://localhost:5003"

# 云服务器
base_url = "https://your-cloud-server.com/api"
```

## 📞 支持

### 健康检查
```bash
curl http://localhost:5003/api/health
```

### 测试端点
```bash
curl -X POST http://localhost:5003/api/diary/test
```

### 日志
检查终端输出以获取详细日志，包括：
- 事件处理状态
- LLM生成进度
- 错误详情
- 性能指标

---

## 🎉 准备使用！

简单日记API现在已准备好用于生产环境。它提供了一个干净、简单的接口来处理事件并根据您的`events.json`配置生成日记条目。

**祝您日记生成愉快！** 📖✨
