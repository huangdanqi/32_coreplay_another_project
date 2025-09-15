# 📁 CorePlay Agent - Project File Structure Guide

## 🎯 Project Overview

This project implements a comprehensive **Diary Agent System** that generates diary entries based on various events and conditions. The system includes multiple APIs, agents, and supporting infrastructure for diary generation.

---

## 📂 Root Directory Structure

```
coreplay_agent/
├── 📁 diary_agent/           # Core diary agent system
├── 📁 config/               # Configuration files
├── 📁 logs/                 # Log files
├── 📁 scripts/              # Utility scripts
├── 📁 temp/                 # Temporary files
├── 📁 test_config_dir/      # Test configuration
├── 📁 test_logs/            # Test log files
├── 📁 utils/                # Utility modules
├── 📁 hewan_emotion_cursor_python/  # Emotion processing
└── 📄 Various Python files  # Main application files
```

---

## 🔧 Core API Files

### 🌐 **API Servers**

| File | Purpose | Port | Description |
|------|---------|------|-------------|
| `simple_diary_api.py` | **Main Simple API** | 5003 | Simplified API with auto-generated event details |
| `complete_diary_agent_api.py` | **Complete Workflow API** | 5002 | Full diary agent workflow implementation |
| `api_diary_system.py` | **Basic API** | 5001 | Basic diary system API |
| `mock_api_server.py` | **Mock Server** | 5000 | Mock API for testing |

### 📋 **API Documentation**

| File | Purpose | Language |
|------|---------|----------|
| `SIMPLE_DIARY_API_GUIDE.md` | Simple API documentation | English |
| `SIMPLE_DIARY_API_GUIDE_CN.md` | Simple API documentation | Chinese |
| `COMPLETE_API_SUMMARY.md` | Complete API overview | English |
| `README_API.md` | Basic API documentation | English |

### 🧪 **API Test Files**

| File | Purpose | Description |
|------|---------|-------------|
| `test_simple_api.py` | Test simple API | Tests simplified API endpoints |
| `test_complete_workflow_api.py` | Test complete API | Tests full workflow API |
| `api_usage_examples.py` | API usage examples | Examples for API usage |

---

## 📊 Condition Logic Documentation

### 🎯 **Condition Logic Files**

| File | Purpose | Language | Description |
|------|---------|----------|-------------|
| `CONDITION_LOGIC_EN.md` | Condition logic | English | Based on diary agent specifications |
| `CONDITION_LOGIC_CN.md` | Condition logic | Chinese | Based on diary agent specifications |
| `CONDITION_LOGIC_DETAILED_EN.md` | Detailed logic | English | Comprehensive condition logic |
| `CONDITION_LOGIC_DETAILED_CN.md` | Detailed logic | Chinese | Comprehensive condition logic |

### 📋 **Specifications**

| File | Purpose | Language | Description |
|------|---------|----------|-------------|
| `diary_agent_specifications_en.md` | Agent specifications | English | Complete diary agent workflow |
| `diary_agent_specifications_zh.md` | Agent specifications | Chinese | Complete diary agent workflow |

---

## 🏗️ Architecture Documentation

| File | Purpose | Description |
|------|---------|-------------|
| `PROJECT_ARCHITECTURE_LOGIC.md` | Project architecture | Overall system architecture and logic |

---

## 🧪 Test Files

### 🔬 **Comprehensive Tests**

| File | Purpose | Description |
|------|---------|-------------|
| `comprehensive_events_test.py` | Comprehensive event testing | Tests all event types |
| `test_complete_diary_system.py` | Complete system test | Tests entire diary system |

### 🌤️ **Weather Tests**

| File | Purpose | Description |
|------|---------|-------------|
| `test_weather_diary.py` | Weather diary test | Tests weather-based diary generation |
| `simple_weather_test.py` | Simple weather test | Basic weather testing |
| `proper_weather_test.py` | Proper weather test | Advanced weather testing |
| `real_api_weather_test.py` | Real API weather test | Tests with real weather API |

### 🎉 **Holiday Tests**

| File | Purpose | Description |
|------|---------|-------------|
| `test_holiday_category_comprehensive.py` | Holiday comprehensive test | Tests holiday functionality |
| `test_holiday_section_3_4.py` | Holiday section test | Tests specific holiday section |
| `test_spring_festival_section_3_4.py` | Spring festival test | Tests Spring Festival events |

### 🤖 **Agent Tests**

| File | Purpose | Description |
|------|---------|-------------|
| `test_dialogue_agent_with_ollama.py` | Dialogue agent test | Tests dialogue agent with Ollama |
| `test_interactive_agent_with_ollama.py` | Interactive agent test | Tests interactive agent |
| `test_neglect_agent_with_ollama.py` | Neglect agent test | Tests neglect agent |

### 📝 **Claim Event Tests**

| File | Purpose | Description |
|------|---------|-------------|
| `test_claim_event_function.py` | Claim event function test | Tests claim event functionality |
| `test_claim_event_local_llm.py` | Claim event LLM test | Tests claim event with local LLM |
| `run_claim_event_test.py` | Run claim event test | Executes claim event tests |

---

## 📁 diary_agent/ Directory Structure

### 🏗️ **Core Components**

```
diary_agent/
├── 📁 agents/              # Individual agent implementations
├── 📁 core/               # Core system components
├── 📁 config/             # Configuration files
├── 📁 data/               # Data storage
├── 📁 data_sources/       # Data source integrations
├── 📁 examples/           # Usage examples
├── 📁 integration/        # Integration modules
├── 📁 monitoring/         # Monitoring and health checks
├── 📁 tests/              # Test files
└── 📁 utils/              # Utility functions
```

### 🤖 **Agents Directory**

| File | Purpose | Description |
|------|---------|-------------|
| `base_agent.py` | Base agent class | Abstract base class for all agents |
| `weather_agent.py` | Weather agent | Handles weather-based diary generation |
| `holiday_agent.py` | Holiday agent | Handles holiday-based diary generation |
| `dialogue_agent.py` | Dialogue agent | Handles dialogue-based diary generation |
| `interactive_agent.py` | Interactive agent | Handles interaction-based diary generation |
| `neglect_agent.py` | Neglect agent | Handles neglect-based diary generation |
| `adoption_agent.py` | Adoption agent | Handles adoption-based diary generation |
| `friends_agent.py` | Friends agent | Handles friend-based diary generation |
| `same_frequency_agent.py` | Same frequency agent | Handles frequency-based diary generation |
| `trending_agent.py` | Trending agent | Handles trending topics diary generation |

### ⚙️ **Core Directory**

| File | Purpose | Description |
|------|---------|-------------|
| `dairy_agent_controller.py` | Main controller | Controls the entire diary agent system |
| `config_manager.py` | Configuration manager | Manages system configuration |
| `llm_manager.py` | LLM manager | Manages LLM connections and operations |
| `event_router.py` | Event router | Routes events to appropriate agents |
| `condition.py` | Condition checker | Checks diary generation conditions |
| `daily_scheduler.py` | Daily scheduler | Schedules daily diary generation |
| `diary_entry_generator.py` | Diary generator | Generates diary entries |
| `data_persistence.py` | Data persistence | Handles data storage and retrieval |
| `sub_agent_manager.py` | Sub-agent manager | Manages sub-agents |

### 🔧 **Configuration Files**

| File | Purpose | Description |
|------|---------|-------------|
| `agent_configuration.json` | Agent configuration | Configuration for all agents |
| `llm_configuration.json` | LLM configuration | Configuration for LLM providers |
| `condition_rules.json` | Condition rules | Rules for diary generation conditions |

### 📊 **Data Directory**

```
data/
├── 📁 backups/            # Backup files
├── 📁 diary_entries/      # Generated diary entries
├── 📁 entries/            # Entry files
└── 📁 quotas/             # Quota tracking files
```

### 🔗 **Integration Directory**

| File | Purpose | Description |
|------|---------|-------------|
| `database_manager.py` | Database manager | Manages database connections |
| `database_reader.py` | Database reader | Reads data from database |
| `weather_data_reader.py` | Weather data reader | Reads weather data |
| `holiday_data_reader.py` | Holiday data reader | Reads holiday data |
| `dialogue_data_reader.py` | Dialogue data reader | Reads dialogue data |
| `interaction_data_reader.py` | Interaction data reader | Reads interaction data |
| `neglect_data_reader.py` | Neglect data reader | Reads neglect data |
| `adoption_data_reader.py` | Adoption data reader | Reads adoption data |
| `friends_data_reader.py` | Friends data reader | Reads friends data |
| `frequency_data_reader.py` | Frequency data reader | Reads frequency data |
| `trending_data_reader.py` | Trending data reader | Reads trending data |

### 📈 **Monitoring Directory**

| File | Purpose | Description |
|------|---------|-------------|
| `health_checker.py` | Health checker | Checks system health |
| `performance_monitor.py` | Performance monitor | Monitors system performance |
| `alerting_system.py` | Alerting system | Handles system alerts |
| `status_dashboard.py` | Status dashboard | Provides system status |

### 🛠️ **Utils Directory**

| File | Purpose | Description |
|------|---------|-------------|
| `data_models.py` | Data models | Data structure definitions |
| `error_handler.py` | Error handler | Handles system errors |
| `logger.py` | Logger | Logging functionality |
| `validators.py` | Validators | Input validation |
| `formatters.py` | Formatters | Data formatting |
| `event_mapper.py` | Event mapper | Maps events to agents |

---

## 📋 Configuration Files

### ⚙️ **Main Configuration**

| File | Purpose | Description |
|------|---------|-------------|
| `requirements.txt` | Python dependencies | Main project dependencies |
| `requirements_api.txt` | API dependencies | API-specific dependencies |
| `ollama_config.json` | Ollama configuration | Ollama LLM configuration |

### 📊 **Event Configuration**

| File | Purpose | Description |
|------|---------|-------------|
| `events.json` | Event definitions | Defines all available events |
| `diary_agent/events.json` | Agent events | Agent-specific event definitions |

---

## 📝 Log Files

### 📊 **API Logs**

| File | Purpose | Description |
|------|---------|-------------|
| `api_diary_system.log` | API system log | Logs from API diary system |
| `complete_diary_agent_api.log` | Complete API log | Logs from complete API |
| `simple_diary_api.log` | Simple API log | Logs from simple API |

### 🧪 **Test Logs**

| File | Purpose | Description |
|------|---------|-------------|
| `comprehensive_events_test.log` | Comprehensive test log | Logs from comprehensive tests |
| `complete_diary_system_test.log` | Complete system test log | Logs from complete system tests |
| `detailed_diary_test.log` | Detailed diary test log | Logs from detailed diary tests |

---

## 📊 Result Files

### 📈 **Test Results**

| File | Purpose | Description |
|------|---------|-------------|
| `comprehensive_events_results.json` | Comprehensive results | Results from comprehensive tests |
| `complete_diary_system_results.json` | Complete system results | Results from complete system tests |
| `detailed_diary_results.json` | Detailed diary results | Results from detailed diary tests |
| `api_results_complete_report.json` | API complete report | Complete API test results |

### 🌤️ **Weather Results**

| File | Purpose | Description |
|------|---------|-------------|
| `complete_weather_test_report.json` | Weather test report | Results from weather tests |

### 🎉 **Holiday Results**

| File | Purpose | Description |
|------|---------|-------------|
| `holiday_section_3_4_fixed_results.json` | Holiday fixed results | Results from fixed holiday tests |
| `holiday_section_3_4_real_results.json` | Holiday real results | Results from real holiday tests |
| `spring_festival_section_3_4_results.json` | Spring festival results | Results from Spring Festival tests |

---

## 🚀 How to Use This Project

### 1. **Start with Simple API**
```bash
python simple_diary_api.py --port 5003
```

### 2. **Test the API**
```bash
python test_simple_api.py
```

### 3. **Use Complete Workflow**
```bash
python complete_diary_agent_api.py --port 5002
```

### 4. **Run Comprehensive Tests**
```bash
python comprehensive_events_test.py
```

---

## 🎯 Key Features

### ✅ **Implemented Features**

- ✅ **Simple API** - Easy-to-use API with auto-generated event details
- ✅ **Complete Workflow API** - Full diary agent workflow implementation
- ✅ **Multiple Agents** - Weather, Holiday, Dialogue, Interactive, Neglect agents
- ✅ **Condition Logic** - Smart diary generation conditions
- ✅ **Comprehensive Testing** - Extensive test coverage
- ✅ **Documentation** - Detailed documentation in English and Chinese
- ✅ **Monitoring** - Health checks and performance monitoring
- ✅ **Data Persistence** - Data storage and retrieval
- ✅ **Error Handling** - Robust error handling and recovery

### 🔄 **Workflow**

1. **Daily Planning** (00:00) → Randomly select 0-5 diaries for the day
2. **Event Processing** → Check quota, type completion, and random chance
3. **Diary Generation** → Generate 1 diary per successful condition
4. **Progress Tracking** → Update quota and completed types

---

## 📚 Documentation Summary

| Category | Files | Purpose |
|----------|-------|---------|
| **API Guides** | 4 files | API usage documentation |
| **Condition Logic** | 4 files | Condition logic documentation |
| **Architecture** | 1 file | System architecture |
| **Specifications** | 2 files | Agent specifications |
| **Test Reports** | Multiple | Test results and reports |

---

## 🎉 Project Status

**✅ COMPLETE** - The project is fully implemented with:
- Multiple API servers
- Comprehensive agent system
- Extensive testing
- Detailed documentation
- Monitoring and health checks
- Data persistence
- Error handling

This is a **production-ready** diary agent system! 🚀
