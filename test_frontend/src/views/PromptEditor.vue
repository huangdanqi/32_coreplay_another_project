<template>
  <div class="prompt-editor">
    <div class="page-header">
      <h2>
        <el-icon><Edit /></el-icon>
        {{ languageStore.t('prompt_editor.title') }}
      </h2>
      <p>{{ languageStore.t('prompt_editor.subtitle') }}</p>
    </div>

    <el-row :gutter="20">
      <!-- Agent Selection -->
      <el-col :span="6">
        <el-card class="agent-selector">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>Select Agent</span>
            </div>
          </template>
          
          <el-radio-group v-model="selectedAgent" @change="onAgentChange">
            <el-radio 
              v-for="agent in availableAgents" 
              :key="agent.type" 
              :label="agent.type"
              class="agent-radio"
            >
              <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-desc">{{ agent.description }}</div>
              </div>
            </el-radio>
          </el-radio-group>
        </el-card>
      </el-col>

      <!-- Prompt Editor -->
      <el-col :span="12">
        <el-card class="prompt-editor-card">
          <template #header>
            <div class="card-header">
              <el-icon><Edit /></el-icon>
              <span>Prompt Configuration</span>
              <div class="header-actions">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="savePrompt"
                  :disabled="!selectedAgent"
                >
                  <el-icon><Check /></el-icon>
                  {{ languageStore.t('prompt_editor.save_prompt') }}
                  <el-tag v-if="hasUnsavedChanges" type="warning" size="small" style="margin-left: 8px;">
                    Unsaved
                  </el-tag>
                </el-button>
                <el-button 
                  type="success" 
                  size="small" 
                  @click="testPrompt"
                  :loading="testing"
                  :disabled="!selectedAgent"
                >
                  <el-icon><DocumentAdd /></el-icon>
                  Save Prompt Temporarily
                </el-button>
                <el-button 
                  type="info" 
                  size="small" 
                  @click="goToAgentTester"
                  :disabled="!selectedAgent"
                >
                  <el-icon><Cpu /></el-icon>
                  Go to Agent Tester
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="selectedAgent" class="prompt-form">
            <el-form :model="currentPrompt" label-width="120px">
              <el-form-item label="Agent Type">
                <el-input v-model="currentPrompt.agent_type" readonly />
              </el-form-item>
              
              <el-form-item label="System Prompt">
                <el-input 
                  v-model="currentPrompt.system_prompt" 
                  type="textarea" 
                  :rows="6"
                  placeholder="Enter system prompt..."
                  @input="checkForChanges"
                />
              </el-form-item>
              
              <el-form-item label="User Prompt Template">
                <el-input 
                  v-model="currentPrompt.user_prompt_template" 
                  type="textarea" 
                  :rows="4"
                  placeholder="Enter user prompt template with {variables}..."
                  @input="checkForChanges"
                />
              </el-form-item>
              
              <el-form-item label="Output Format">
                <el-input 
                  v-model="currentPrompt.output_format_json" 
                  type="textarea" 
                  :rows="3"
                  placeholder='{"title": "string", "content": "string", "emotion": "string"}'
                  @input="checkForChanges"
                />
              </el-form-item>
              
              <el-form-item label="Validation Rules">
                <el-input 
                  v-model="currentPrompt.validation_rules_json" 
                  type="textarea" 
                  :rows="3"
                  placeholder='{"title_max_length": 6, "content_max_length": 35}'
                  @input="checkForChanges"
                />
              </el-form-item>
            </el-form>
          </div>

          <div v-else class="no-selection">
            <el-empty description="Select an agent to edit prompts">
              <el-button type="primary" @click="selectedAgent = 'diary'">
                Select Agent
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>

      <!-- Temporary History -->
      <el-col :span="6">
        <el-card class="test-results">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>Temporary History</span>
              <div class="header-actions">
                <el-button 
                  v-if="testHistory.length > 0"
                  type="danger" 
                  size="small" 
                  @click="clearTestHistory"
                >
                  <el-icon><Delete /></el-icon>
                  Clear History
                </el-button>
              </div>
            </div>
          </template>

          <div class="test-info">
            <div v-if="testHistory.length > 0" class="test-history">
              <h4>Temporary Prompt History</h4>
              <div class="history-list">
                <div 
                  v-for="test in testHistory" 
                  :key="test.id"
                  class="history-item"
                  :class="{ 'success': test.success, 'error': !test.success }"
                >
                  <div class="history-header">
                    <span class="test-time">{{ formatTime(test.timestamp) }}</span>
                    <div class="history-actions">
                      <el-tag :type="test.success ? 'success' : 'danger'" size="small" style="margin-right:8px;">
                        {{ test.success ? 'Success' : 'Failed' }}
                      </el-tag>
                      <el-button 
                        type="danger" 
                        link 
                        size="small" 
                        @click="removeHistoryItem(test.id)"
                        :title="'Delete this record'"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  
                  <!-- Agent Type -->
                  <div class="agent-info">
                    <el-tag type="info" size="small">
                      <el-icon><Cpu /></el-icon>
                      {{ test.agent_type || 'Unknown' }}
                    </el-tag>
                  </div>
                  
                  <!-- Prompt Content -->
                  <div class="prompt-preview">
                    <div class="prompt-section">
                      <strong>System Prompt:</strong>
                      <div class="prompt-text" :title="test.prompt?.system_prompt || 'N/A'">
                        {{ truncateText(test.prompt?.system_prompt || 'N/A', 100) }}
                      </div>
                    </div>
                    <div class="prompt-section" v-if="test.prompt?.user_prompt_template">
                      <strong>User Template:</strong>
                      <div class="prompt-text" :title="test.prompt.user_prompt_template">
                        {{ truncateText(test.prompt.user_prompt_template, 100) }}
                      </div>
                    </div>
                  </div>
                  
                  <div class="test-result">
                    <div v-if="test.success && test.result.data" class="result-content">
                      <div v-if="test.result.data.title" class="result-item">
                        <strong>Title:</strong> {{ test.result.data.title }}
                      </div>
                      <div v-if="test.result.data.content" class="result-item">
                        <strong>Content:</strong> {{ test.result.data.content }}
                      </div>
                      <div v-if="test.result.data.emotion_tags" class="result-item">
                        <strong>Emotions:</strong> {{ test.result.data.emotion_tags.join(', ') }}
                      </div>
                      <div v-if="test.result.data.description" class="result-item">
                        <strong>Description:</strong> {{ test.result.data.description }}
                      </div>
                      <div v-if="test.result.data.bazi" class="result-item">
                        <strong>BaZi:</strong> {{ test.result.data.bazi.join(' ') }}
                      </div>
                      <div v-if="test.result.data.wuxing" class="result-item">
                        <strong>WuXing:</strong> {{ test.result.data.wuxing.join(' ') }}
                      </div>
                    </div>
                    <div v-else-if="!test.success" class="error-content">
                      <strong>Error:</strong> {{ test.result.error || 'Unknown error' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-tests">
              <el-empty description="No temporary prompts saved yet">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="testPrompt"
                  :disabled="!selectedAgent"
                >
                  <el-icon><VideoPlay /></el-icon>
                  Test Current Prompt
                </el-button>
              </el-empty>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Prompt Templates -->
    <el-row :gutter="20" class="templates-section">
      <el-col :span="24">
        <el-card class="templates-card">
          <template #header>
            <div class="card-header">
              <el-icon><Collection /></el-icon>
              <span>Prompt Templates</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="loadTemplates"
                :loading="loadingTemplates"
              >
                <el-icon><Refresh /></el-icon>
                Refresh Templates
              </el-button>
            </div>
          </template>

          <div v-if="templates.length > 0" class="templates-grid">
            <div 
              v-for="template in templates" 
              :key="template.agent_type"
              class="template-item"
              @click="loadTemplate(template)"
            >
              <div class="template-header">
                <h4>{{ template.agent_type }}</h4>
                <el-tag size="small">{{ template.version || 'v1.0' }}</el-tag>
              </div>
              <div class="template-preview">
                <p>{{ template.system_prompt.substring(0, 100) }}...</p>
              </div>
              <div class="template-actions">
                <el-button size="small" type="primary" @click.stop="loadTemplate(template)">
                  Load Template
                </el-button>
              </div>
            </div>
          </div>

          <div v-else class="no-templates">
            <el-empty description="No templates available">
              <el-button type="primary" @click="loadTemplates">
                Load Templates
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Password Verification Dialog -->
    <PasswordVerifyDialog 
      v-model="showPasswordDialog"
      :prompt-data="getPromptData()"
      @success="handlePromptSaveSuccess"
      @error="handlePromptSaveError"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, reactive, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useLanguageStore } from '@/stores/languageStore'
import apiService from '@/services/apiService'
import { ElMessage, ElMessageBox } from 'element-plus'
import PasswordVerifyDialog from '@/components/PasswordVerifyDialog.vue'
import { 
  Edit, 
  List, 
  VideoPlay, 
  Check, 
  Document, 
  Collection, 
  Refresh,
  Delete,
  Cpu,
  Clock,
  DocumentAdd
} from '@element-plus/icons-vue'

const appStore = useAppStore()
const languageStore = useLanguageStore()

// Reactive data
const selectedAgent = ref('diary')
const loadingTemplates = ref(false)
const templates = ref([])
const showPasswordDialog = ref(false)
const hasUnsavedChanges = ref(false)
const originalPrompt = ref({})
const testHistory = ref([])
const testing = ref(false)

// Persisted history key
const HISTORY_STORAGE_KEY = 'promptEditor:testHistory'
const MAX_HISTORY_ITEMS = 28

const loadHistoryFromStorage = () => {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        testHistory.value = parsed
      }
    }
  } catch (e) {
    // ignore storage errors
  }
}

const saveHistoryToStorage = () => {
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(testHistory.value))
  } catch (e) {
    // ignore storage errors
  }
}

// Agent configurations
const availableAgents = ref([
  {
    type: 'diary',
    name: 'Diary Agent',
    description: 'Generate diary entries from events'
  },
  {
    type: 'sensor',
    name: 'Sensor Event Agent',
    description: 'Translate sensor data to cute descriptions'
  },
  {
    type: 'bazi',
    name: 'BaZi/WuXing Agent',
    description: 'Calculate Chinese astrology elements'
  },
  {
    type: 'event',
    name: 'Event Agent',
    description: 'Extract and update events from dialogue'
  },
  {
    type: 'trending',
    name: 'Trending Agent',
    description: 'Generate diary entries about trending topics'
  },
  {
    type: 'weather',
    name: 'Weather Agent',
    description: 'Generate diary entries about weather'
  }
])

// Current prompt configuration
const currentPrompt = ref({
  agent_type: 'diary',
  system_prompt: '你是一个可爱的玩具日记助手，请根据事件信息写一篇简短的日记。直接输出日记内容，不要包含任何思考过程或标签。',
  user_prompt_template: '事件类型: {event_type}\n事件名称: {event_name}\n事件详情: {event_details}\n\n请写一篇简短的日记，包含标题和内容。',
  output_format_json: '{"title": "string", "content": "string", "emotion_tags": ["string"]}',
  validation_rules_json: '{"title_max_length": 6, "content_max_length": 35, "required_fields": ["title", "content", "emotion_tags"]}'
})

// Computed
const canSavePrompt = computed(() => {
  return selectedAgent.value && 
         currentPrompt.value.system_prompt && 
         currentPrompt.value.user_prompt_template
})

// Watch for changes
const checkForChanges = () => {
  if (!originalPrompt.value || !currentPrompt.value) return
  
  const hasChanges = 
    originalPrompt.value.system_prompt !== currentPrompt.value.system_prompt ||
    originalPrompt.value.user_prompt_template !== currentPrompt.value.user_prompt_template ||
    originalPrompt.value.output_format_json !== currentPrompt.value.output_format_json ||
    originalPrompt.value.validation_rules_json !== currentPrompt.value.validation_rules_json
  
  hasUnsavedChanges.value = hasChanges
}

// Methods
const onAgentChange = () => {
  // Check if there are unsaved changes before switching
  if (hasUnsavedChanges.value) {
    ElMessageBox.confirm(
      'You have unsaved changes. Do you want to save them before switching agents?',
      'Unsaved Changes',
      {
        confirmButtonText: 'Save & Switch',
        cancelButtonText: 'Discard & Switch',
        type: 'warning',
      }
    ).then(() => {
      // Save first, then switch
      savePrompt().then(() => {
        loadDefaultPrompt()
      })
    }).catch(() => {
      // Discard changes and switch
      loadDefaultPrompt()
    })
  } else {
    loadDefaultPrompt()
  }
}

const loadDefaultPrompt = () => {
  const defaultPrompts = {
    diary: {
      agent_type: 'diary',
      system_prompt: '你是一个可爱的玩具日记助手，请根据事件信息写一篇简短的日记。直接输出日记内容，不要包含任何思考过程或标签。',
      user_prompt_template: '事件类型: {event_type}\n事件名称: {event_name}\n事件详情: {event_details}\n\n请写一篇简短的日记，包含标题和内容。',
      output_format_json: '{"title": "string", "content": "string", "emotion_tags": ["string"]}',
      validation_rules_json: '{"title_max_length": 6, "content_max_length": 35, "required_fields": ["title", "content", "emotion_tags"]}'
    },
    sensor: {
      agent_type: 'sensor',
      system_prompt: '你是一个可爱的翻译助手，将传感器数据翻译成萌系中文描述。输出要简洁可爱，不超过20个字符。',
      user_prompt_template: '请将以下传感器数据翻译成可爱的中文描述：\n传感器类型: {sensor_type}\n数据: {sensor_data}\n\n输出格式: 直接输出描述，不要包含任何标签或解释。',
      output_format_json: '{"description": "string"}',
      validation_rules_json: '{"max_length": 20, "required_fields": ["description"]}'
    },
    bazi: {
      agent_type: 'bazi',
      system_prompt: '你是一个专业的八字五行计算助手，根据出生信息计算八字和五行。',
      user_prompt_template: '请根据以下出生信息计算八字和五行：\n出生年份: {birth_year}\n出生月份: {birth_month}\n出生日期: {birth_day}\n出生时辰: {birth_hour}\n出生地: {birthplace}\n\n请输出JSON格式：{"bazi": ["年干","年支","月干","月支","日干","日支","时干","时支"], "wuxing": ["五行1","五行2",...]}',
      output_format_json: '{"bazi": ["string"], "wuxing": ["string"]}',
      validation_rules_json: '{"bazi_length": 8, "wuxing_max": 6}'
    },
    event: {
      agent_type: 'event',
      system_prompt: '你是一个事件提取助手，从对话中提取关键事件信息。',
      user_prompt_template: '请从以下对话中提取事件信息：\n对话: {dialogue}\n\n输出JSON格式：{"topic": "主题", "title": "标题", "summary": "摘要", "emotion": ["情感"], "type": "new|update"}',
      output_format_json: '{"topic": "string", "title": "string", "summary": "string", "emotion": ["string"], "type": "string"}',
      validation_rules_json: '{"summary_max_length": 50, "emotion_max": 3}'
    },
    trending: {
      agent_type: 'trending',
      system_prompt: '你是一个热门话题日记助手，根据社会热点生成日记条目。',
      user_prompt_template: '请根据以下热门话题信息生成日记：\n话题: {topic}\n社会情绪: {social_sentiment}\n事件分类: {event_classification}\n\n请生成一篇关于当前热门话题的日记，要求：\n1. 标题最多6个字符\n2. 内容最多35个字符\n3. 选择合适的情感标签',
      output_format_json: '{"title": "string", "content": "string", "emotion_tags": ["string"]}',
      validation_rules_json: '{"title_max_length": 6, "content_max_length": 35}'
    },
    weather: {
      agent_type: 'weather',
      system_prompt: '你是一个天气日记助手，根据天气信息生成日记条目。',
      user_prompt_template: '请根据以下天气信息生成日记：\n天气类型: {weather_type}\n温度: {temperature}\n季节: {season}\n\n请生成一篇关于天气的日记，要求简洁可爱。',
      output_format_json: '{"title": "string", "content": "string", "emotion_tags": ["string"]}',
      validation_rules_json: '{"title_max_length": 6, "content_max_length": 35}'
    }
  }
  
  if (defaultPrompts[selectedAgent.value]) {
    currentPrompt.value = { ...defaultPrompts[selectedAgent.value] }
    // Store original prompt for change tracking
    originalPrompt.value = { ...defaultPrompts[selectedAgent.value] }
    hasUnsavedChanges.value = false
  }
}


const testPrompt = async () => {
  if (!selectedAgent.value) return
  
  testing.value = true
  try {
    // Use current prompt configuration for testing
    const testData = {
      agent_type: selectedAgent.value,
      system_prompt: currentPrompt.value.system_prompt,
      user_prompt_template: currentPrompt.value.user_prompt_template,
      output_format: JSON.parse(currentPrompt.value.output_format_json || '{}'),
      validation_rules: JSON.parse(currentPrompt.value.validation_rules_json || '{}')
    }
    
    // Create test payload based on agent type
    let testPayload = {}
    switch (selectedAgent.value) {
      case 'diary':
        testPayload = {
          event_category: 'human_toy_interactive_function',
          event_name: 'liked_interaction_once',
          sub_agent: 'interactive',
          interaction_type: '抚摸',
          duration: '5分钟',
          user_response: 'positive'
        }
        break
      case 'sensor':
        testPayload = {
          sensor_type: 'temperature',
          sensor_data: '25.5°C'
        }
        break
      case 'bazi':
        testPayload = {
          birth_year: 1990,
          birth_month: 5,
          birth_day: 15,
          birth_hour: 10,
          birthplace: '北京'
        }
        break
      default:
        testPayload = { test: 'sample data' }
    }
    
    // Test the prompt using custom prompt endpoint for diary agent
    let result
    if (selectedAgent.value === 'diary') {
      result = await apiService.testDiaryAgentWithCustomPrompt(testPayload, testData)
    } else {
      result = await apiService.testPrompt(testData, testPayload)
    }
    
    // Add to test history (most recent first)
    testHistory.value.unshift({
      id: Date.now(),
      timestamp: new Date().toISOString(),
      agent_type: selectedAgent.value,
      prompt: testData,
      payload: testPayload,
      result: result,
      success: result.success
    })
    
    // Keep only last MAX_HISTORY_ITEMS (overwrite oldest)
    if (testHistory.value.length > MAX_HISTORY_ITEMS) {
      testHistory.value = testHistory.value.slice(0, MAX_HISTORY_ITEMS)
    }
    // persist
    saveHistoryToStorage()
    
    ElMessage.success('Prompt saved temporarily!')
    
  } catch (error) {
    ElMessage.error(`Failed to save temporarily: ${error.message}`)
    
    // Add failed test to history
    testHistory.value.unshift({
      id: Date.now(),
      timestamp: new Date().toISOString(),
      agent_type: selectedAgent.value,
      prompt: testData,
      payload: testPayload,
      result: { error: error.message },
      success: false
    })
    saveHistoryToStorage()
  } finally {
    testing.value = false
  }
}

const goToAgentTester = () => {
  if (!selectedAgent.value) return
  
  // Store the current rewritten prompt in sessionStorage for Agent Tester to use
  const currentPromptData = {
    agent_type: selectedAgent.value,
    system_prompt: currentPrompt.value.system_prompt,
    user_prompt_template: currentPrompt.value.user_prompt_template,
    output_format: JSON.parse(currentPrompt.value.output_format_json || '{}'),
    validation_rules: JSON.parse(currentPrompt.value.validation_rules_json || '{}'),
    timestamp: new Date().toISOString(),
    isCustomPrompt: true
  }
  
  // Store in sessionStorage so Agent Tester can access it
  sessionStorage.setItem('testPromptData', JSON.stringify(currentPromptData))
  
  // Navigate to Agent Tester
  window.location.href = '/agents'
}

const savePrompt = async () => {
  if (!selectedAgent.value) return
  
  // Show password verification dialog
  showPasswordDialog.value = true
}

const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const result = await apiService.getPromptTemplates()
    templates.value = result.data || []
  } catch (error) {
    ElMessage.error(`Failed to load templates: ${error.message}`)
  } finally {
    loadingTemplates.value = false
  }
}

const loadTemplate = (template) => {
  currentPrompt.value = {
    agent_type: template.agent_type,
    system_prompt: template.system_prompt,
    user_prompt_template: template.user_prompt_template,
    output_format_json: JSON.stringify(template.output_format, null, 2),
    validation_rules_json: JSON.stringify(template.validation_rules, null, 2)
  }
  selectedAgent.value = template.agent_type
  ElMessage.success(`Template loaded for ${template.agent_type}`)
}

const getPromptData = () => {
  return {
    agent_type: selectedAgent.value,
    system_prompt: currentPrompt.value.system_prompt,
    user_prompt_template: currentPrompt.value.user_prompt_template,
    output_format: JSON.parse(currentPrompt.value.output_format_json),
    validation_rules: JSON.parse(currentPrompt.value.validation_rules_json)
  }
}

const handlePromptSaveSuccess = (result) => {
  const pathMsg = result?.config_path ? ` (${result.config_path})` : ''
  ElMessage.success(`Prompt saved successfully${pathMsg}`)
  showPasswordDialog.value = false
  // Reset change tracking
  originalPrompt.value = { ...currentPrompt.value }
  hasUnsavedChanges.value = false
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

const truncateText = (text, maxLength) => {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const clearTestHistory = () => {
  testHistory.value = []
  try { localStorage.removeItem(HISTORY_STORAGE_KEY) } catch (e) {}
  ElMessage.success('Test history cleared')
}

const removeHistoryItem = (id) => {
  const before = testHistory.value.length
  testHistory.value = testHistory.value.filter(item => item.id !== id)
  saveHistoryToStorage()
  if (testHistory.value.length < before) {
    ElMessage.success('History item deleted')
  }
}

// Lifecycle
onMounted(() => {
  languageStore.initLanguage()
  loadDefaultPrompt()
  loadTemplates()
  loadHistoryFromStorage()
})

onBeforeUnmount(() => {
  // Check for unsaved changes before leaving
  if (hasUnsavedChanges.value) {
    ElMessageBox.confirm(
      'You have unsaved changes. Do you want to save them before leaving?',
      'Unsaved Changes',
      {
        confirmButtonText: 'Save & Leave',
        cancelButtonText: 'Leave Without Saving',
        type: 'warning',
      }
    ).then(() => {
      // Save before leaving
      savePrompt()
    }).catch(() => {
      // Leave without saving
    })
  }
})
</script>

<style scoped>
.prompt-editor {
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h2 {
  margin: 0 0 10px 0;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 10px;
}

.agent-selector {
  height: fit-content;
}

.agent-radio {
  width: 100%;
  margin-bottom: 15px;
}

.agent-info {
  margin-left: 10px;
}

.agent-name {
  font-weight: 600;
  color: #333;
}

.agent-desc {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.prompt-editor-card {
  height: fit-content;
}

.prompt-form {
  padding: 20px 0;
}

.no-selection {
  text-align: center;
  padding: 60px 20px;
}

.test-results {
  height: fit-content;
}

.result-content {
  margin-top: 20px;
}

.result-details {
  margin: 20px 0;
}

.result-details h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.result-output {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.output-item {
  margin-bottom: 8px;
  font-size: 14px;
}

.output-item:last-child {
  margin-bottom: 0;
}

.result-meta {
  margin-top: 15px;
  padding: 15px;
  background: #f0f0f0;
  border-radius: 4px;
}

.result-meta p {
  margin: 5px 0;
  font-size: 14px;
}

.no-results {
  text-align: center;
  padding: 40px 20px;
}

.templates-section {
  margin-top: 30px;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.template-item {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.template-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.template-header h4 {
  margin: 0;
  color: #333;
  text-transform: capitalize;
}

.template-preview {
  margin-bottom: 15px;
}

.template-preview p {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.template-actions {
  text-align: right;
}

.no-templates {
  text-align: center;
  padding: 40px 20px;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-textarea {
  font-family: 'Courier New', monospace;
}

/* Test History Styles */
.test-history {
  max-height: 400px;
  overflow-y: auto;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
}

.history-item.success {
  border-color: #67c23a;
  background: #f0f9ff;
}

.history-item.error {
  border-color: #f56c6c;
  background: #fef0f0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.test-time {
  font-size: 12px;
  color: #666;
}

.agent-info {
  margin-bottom: 8px;
}

.prompt-preview {
  margin-bottom: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.prompt-section {
  margin-bottom: 8px;
}

.prompt-section:last-child {
  margin-bottom: 0;
}

.prompt-section strong {
  display: block;
  font-size: 12px;
  color: #495057;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.prompt-text {
  font-size: 11px;
  color: #6c757d;
  background: white;
  padding: 4px 6px;
  border-radius: 3px;
  border: 1px solid #dee2e6;
  max-height: 40px;
  overflow-y: auto;
  line-height: 1.3;
  word-break: break-word;
  font-family: 'Courier New', monospace;
}

.test-result {
  font-size: 14px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-item {
  margin-bottom: 4px;
}

.result-item strong {
  color: #333;
  margin-right: 8px;
}

.error-content {
  color: #f56c6c;
}

.no-tests {
  text-align: center;
  padding: 40px 20px;
}
</style>
