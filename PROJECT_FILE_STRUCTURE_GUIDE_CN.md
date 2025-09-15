# 📁 CorePlay Agent - 项目文件结构指南

## 🎯 项目概述

本项目实现了一个综合的**日记代理系统**，基于各种事件和条件生成日记条目。系统包括多个API、代理和支持基础设施，用于日记生成。

---

## 📂 根目录结构

```
coreplay_agent/
├── 📁 diary_agent/           # 核心日记代理系统
├── 📁 config/               # 配置文件
├── 📁 logs/                 # 日志文件
├── 📁 scripts/              # 实用脚本
├── 📁 temp/                 # 临时文件
├── 📁 test_config_dir/      # 测试配置
├── 📁 test_logs/            # 测试日志文件
├── 📁 utils/                # 实用模块
├── 📁 hewan_emotion_cursor_python/  # 情感处理
└── 📄 各种Python文件        # 主应用程序文件
```

---

## 🔧 核心API文件

### 🌐 **API服务器**

| 文件 | 用途 | 端口 | 描述 |
|------|------|------|------|
| `simple_diary_api.py` | **主要简单API** | 5003 | 带有自动生成事件详情的简化API |
| `complete_diary_agent_api.py` | **完整工作流API** | 5002 | 完整的日记代理工作流实现 |
| `api_diary_system.py` | **基础API** | 5001 | 基础日记系统API |
| `mock_api_server.py` | **模拟服务器** | 5000 | 用于测试的模拟API |

### 📋 **API文档**

| 文件 | 用途 | 语言 |
|------|------|------|
| `SIMPLE_DIARY_API_GUIDE.md` | 简单API文档 | 英文 |
| `SIMPLE_DIARY_API_GUIDE_CN.md` | 简单API文档 | 中文 |
| `COMPLETE_API_SUMMARY.md` | 完整API概述 | 英文 |
| `README_API.md` | 基础API文档 | 英文 |

### 🧪 **API测试文件**

| 文件 | 用途 | 描述 |
|------|------|------|
| `test_simple_api.py` | 测试简单API | 测试简化API端点 |
| `test_complete_workflow_api.py` | 测试完整API | 测试完整工作流API |
| `api_usage_examples.py` | API使用示例 | API使用示例 |

---

## 📊 条件逻辑文档

### 🎯 **条件逻辑文件**

| 文件 | 用途 | 语言 | 描述 |
|------|------|------|------|
| `CONDITION_LOGIC_EN.md` | 条件逻辑 | 英文 | 基于日记代理规范 |
| `CONDITION_LOGIC_CN.md` | 条件逻辑 | 中文 | 基于日记代理规范 |
| `CONDITION_LOGIC_DETAILED_EN.md` | 详细逻辑 | 英文 | 综合条件逻辑 |
| `CONDITION_LOGIC_DETAILED_CN.md` | 详细逻辑 | 中文 | 综合条件逻辑 |

### 📋 **规范文件**

| 文件 | 用途 | 语言 | 描述 |
|------|------|------|------|
| `diary_agent_specifications_en.md` | 代理规范 | 英文 | 完整的日记代理工作流 |
| `diary_agent_specifications_zh.md` | 代理规范 | 中文 | 完整的日记代理工作流 |

---

## 🏗️ 架构文档

| 文件 | 用途 | 描述 |
|------|------|------|
| `PROJECT_ARCHITECTURE_LOGIC.md` | 项目架构 | 整体系统架构和逻辑 |

---

## 🧪 测试文件

### 🔬 **综合测试**

| 文件 | 用途 | 描述 |
|------|------|------|
| `comprehensive_events_test.py` | 综合事件测试 | 测试所有事件类型 |
| `test_complete_diary_system.py` | 完整系统测试 | 测试整个日记系统 |

### 🌤️ **天气测试**

| 文件 | 用途 | 描述 |
|------|------|------|
| `test_weather_diary.py` | 天气日记测试 | 测试基于天气的日记生成 |
| `simple_weather_test.py` | 简单天气测试 | 基础天气测试 |
| `proper_weather_test.py` | 正确天气测试 | 高级天气测试 |
| `real_api_weather_test.py` | 真实API天气测试 | 使用真实天气API测试 |

### 🎉 **节日测试**

| 文件 | 用途 | 描述 |
|------|------|------|
| `test_holiday_category_comprehensive.py` | 节日综合测试 | 测试节日功能 |
| `test_holiday_section_3_4.py` | 节日部分测试 | 测试特定节日部分 |
| `test_spring_festival_section_3_4.py` | 春节测试 | 测试春节事件 |

### 🤖 **代理测试**

| 文件 | 用途 | 描述 |
|------|------|------|
| `test_dialogue_agent_with_ollama.py` | 对话代理测试 | 使用Ollama测试对话代理 |
| `test_interactive_agent_with_ollama.py` | 交互代理测试 | 使用Ollama测试交互代理 |
| `test_neglect_agent_with_ollama.py` | 忽视代理测试 | 使用Ollama测试忽视代理 |

### 📝 **声明事件测试**

| 文件 | 用途 | 描述 |
|------|------|------|
| `test_claim_event_function.py` | 声明事件功能测试 | 测试声明事件功能 |
| `test_claim_event_local_llm.py` | 声明事件LLM测试 | 使用本地LLM测试声明事件 |
| `run_claim_event_test.py` | 运行声明事件测试 | 执行声明事件测试 |

---

## 📁 diary_agent/ 目录结构

### 🏗️ **核心组件**

```
diary_agent/
├── 📁 agents/              # 单个代理实现
├── 📁 core/               # 核心系统组件
├── 📁 config/             # 配置文件
├── 📁 data/               # 数据存储
├── 📁 data_sources/       # 数据源集成
├── 📁 examples/           # 使用示例
├── 📁 integration/        # 集成模块
├── 📁 monitoring/         # 监控和健康检查
├── 📁 tests/              # 测试文件
└── 📁 utils/              # 实用函数
```

### 🤖 **代理目录**

| 文件 | 用途 | 描述 |
|------|------|------|
| `base_agent.py` | 基础代理类 | 所有代理的抽象基类 |
| `weather_agent.py` | 天气代理 | 处理基于天气的日记生成 |
| `holiday_agent.py` | 节日代理 | 处理基于节日的日记生成 |
| `dialogue_agent.py` | 对话代理 | 处理基于对话的日记生成 |
| `interactive_agent.py` | 交互代理 | 处理基于交互的日记生成 |
| `neglect_agent.py` | 忽视代理 | 处理基于忽视的日记生成 |
| `adoption_agent.py` | 收养代理 | 处理基于收养的日记生成 |
| `friends_agent.py` | 朋友代理 | 处理基于朋友的日记生成 |
| `same_frequency_agent.py` | 同频代理 | 处理基于频率的日记生成 |
| `trending_agent.py` | 趋势代理 | 处理趋势话题日记生成 |

### ⚙️ **核心目录**

| 文件 | 用途 | 描述 |
|------|------|------|
| `dairy_agent_controller.py` | 主控制器 | 控制整个日记代理系统 |
| `config_manager.py` | 配置管理器 | 管理系统配置 |
| `llm_manager.py` | LLM管理器 | 管理LLM连接和操作 |
| `event_router.py` | 事件路由器 | 将事件路由到适当的代理 |
| `condition.py` | 条件检查器 | 检查日记生成条件 |
| `daily_scheduler.py` | 每日调度器 | 调度每日日记生成 |
| `diary_entry_generator.py` | 日记生成器 | 生成日记条目 |
| `data_persistence.py` | 数据持久化 | 处理数据存储和检索 |
| `sub_agent_manager.py` | 子代理管理器 | 管理子代理 |

### 🔧 **配置文件**

| 文件 | 用途 | 描述 |
|------|------|------|
| `agent_configuration.json` | 代理配置 | 所有代理的配置 |
| `llm_configuration.json` | LLM配置 | LLM提供商的配置 |
| `condition_rules.json` | 条件规则 | 日记生成条件的规则 |

### 📊 **数据目录**

```
data/
├── 📁 backups/            # 备份文件
├── 📁 diary_entries/      # 生成的日记条目
├── 📁 entries/            # 条目文件
└── 📁 quotas/             # 配额跟踪文件
```

### 🔗 **集成目录**

| 文件 | 用途 | 描述 |
|------|------|------|
| `database_manager.py` | 数据库管理器 | 管理数据库连接 |
| `database_reader.py` | 数据库读取器 | 从数据库读取数据 |
| `weather_data_reader.py` | 天气数据读取器 | 读取天气数据 |
| `holiday_data_reader.py` | 节日数据读取器 | 读取节日数据 |
| `dialogue_data_reader.py` | 对话数据读取器 | 读取对话数据 |
| `interaction_data_reader.py` | 交互数据读取器 | 读取交互数据 |
| `neglect_data_reader.py` | 忽视数据读取器 | 读取忽视数据 |
| `adoption_data_reader.py` | 收养数据读取器 | 读取收养数据 |
| `friends_data_reader.py` | 朋友数据读取器 | 读取朋友数据 |
| `frequency_data_reader.py` | 频率数据读取器 | 读取频率数据 |
| `trending_data_reader.py` | 趋势数据读取器 | 读取趋势数据 |

### 📈 **监控目录**

| 文件 | 用途 | 描述 |
|------|------|------|
| `health_checker.py` | 健康检查器 | 检查系统健康状态 |
| `performance_monitor.py` | 性能监控器 | 监控系统性能 |
| `alerting_system.py` | 警报系统 | 处理系统警报 |
| `status_dashboard.py` | 状态仪表板 | 提供系统状态 |

### 🛠️ **工具目录**

| 文件 | 用途 | 描述 |
|------|------|------|
| `data_models.py` | 数据模型 | 数据结构定义 |
| `error_handler.py` | 错误处理器 | 处理系统错误 |
| `logger.py` | 日志记录器 | 日志记录功能 |
| `validators.py` | 验证器 | 输入验证 |
| `formatters.py` | 格式化器 | 数据格式化 |
| `event_mapper.py` | 事件映射器 | 将事件映射到代理 |

---

## 📋 配置文件

### ⚙️ **主要配置**

| 文件 | 用途 | 描述 |
|------|------|------|
| `requirements.txt` | Python依赖 | 主要项目依赖 |
| `requirements_api.txt` | API依赖 | API特定依赖 |
| `ollama_config.json` | Ollama配置 | Ollama LLM配置 |

### 📊 **事件配置**

| 文件 | 用途 | 描述 |
|------|------|------|
| `events.json` | 事件定义 | 定义所有可用事件 |
| `diary_agent/events.json` | 代理事件 | 代理特定事件定义 |

---

## 📝 日志文件

### 📊 **API日志**

| 文件 | 用途 | 描述 |
|------|------|------|
| `api_diary_system.log` | API系统日志 | 来自API日记系统的日志 |
| `complete_diary_agent_api.log` | 完整API日志 | 来自完整API的日志 |
| `simple_diary_api.log` | 简单API日志 | 来自简单API的日志 |

### 🧪 **测试日志**

| 文件 | 用途 | 描述 |
|------|------|------|
| `comprehensive_events_test.log` | 综合测试日志 | 来自综合测试的日志 |
| `complete_diary_system_test.log` | 完整系统测试日志 | 来自完整系统测试的日志 |
| `detailed_diary_test.log` | 详细日记测试日志 | 来自详细日记测试的日志 |

---

## 📊 结果文件

### 📈 **测试结果**

| 文件 | 用途 | 描述 |
|------|------|------|
| `comprehensive_events_results.json` | 综合结果 | 来自综合测试的结果 |
| `complete_diary_system_results.json` | 完整系统结果 | 来自完整系统测试的结果 |
| `detailed_diary_results.json` | 详细日记结果 | 来自详细日记测试的结果 |
| `api_results_complete_report.json` | API完整报告 | 完整API测试结果 |

### 🌤️ **天气结果**

| 文件 | 用途 | 描述 |
|------|------|------|
| `complete_weather_test_report.json` | 天气测试报告 | 来自天气测试的结果 |

### 🎉 **节日结果**

| 文件 | 用途 | 描述 |
|------|------|------|
| `holiday_section_3_4_fixed_results.json` | 节日修复结果 | 来自修复节日测试的结果 |
| `holiday_section_3_4_real_results.json` | 节日真实结果 | 来自真实节日测试的结果 |
| `spring_festival_section_3_4_results.json` | 春节结果 | 来自春节测试的结果 |

---

## 🚀 如何使用本项目

### 1. **从简单API开始**
```bash
python simple_diary_api.py --port 5003
```

### 2. **测试API**
```bash
python test_simple_api.py
```

### 3. **使用完整工作流**
```bash
python complete_diary_agent_api.py --port 5002
```

### 4. **运行综合测试**
```bash
python comprehensive_events_test.py
```

---

## 🎯 主要功能

### ✅ **已实现功能**

- ✅ **简单API** - 易于使用的API，带有自动生成的事件详情
- ✅ **完整工作流API** - 完整的日记代理工作流实现
- ✅ **多个代理** - 天气、节日、对话、交互、忽视代理
- ✅ **条件逻辑** - 智能日记生成条件
- ✅ **综合测试** - 广泛的测试覆盖
- ✅ **文档** - 英文和中文的详细文档
- ✅ **监控** - 健康检查和性能监控
- ✅ **数据持久化** - 数据存储和检索
- ✅ **错误处理** - 强大的错误处理和恢复

### 🔄 **工作流程**

1. **每日规划** (00:00) → 随机选择0-5个日记用于当天
2. **事件处理** → 检查配额、类型完成和随机概率
3. **日记生成** → 每个成功条件生成1个日记
4. **进度跟踪** → 更新配额和已完成类型

---

## 📚 文档摘要

| 类别 | 文件 | 用途 |
|------|------|------|
| **API指南** | 4个文件 | API使用文档 |
| **条件逻辑** | 4个文件 | 条件逻辑文档 |
| **架构** | 1个文件 | 系统架构 |
| **规范** | 2个文件 | 代理规范 |
| **测试报告** | 多个 | 测试结果和报告 |

---

## 🎉 项目状态

**✅ 完成** - 项目已完全实现，包括：
- 多个API服务器
- 综合代理系统
- 广泛测试
- 详细文档
- 监控和健康检查
- 数据持久化
- 错误处理

这是一个**生产就绪**的日记代理系统！🚀
