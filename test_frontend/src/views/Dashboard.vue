<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>
        <el-icon><House /></el-icon>
        {{ languageStore.t('dashboard.title') }}
      </h2>
      <p>{{ languageStore.t('dashboard.subtitle') }}</p>
    </div>

    <!-- System Status Cards -->
    <el-row :gutter="20" class="status-cards">
      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <div class="card-icon connection">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="card-info">
              <h3>{{ languageStore.t('dashboard.connection_status') }}</h3>
              <p :class="connectionStatus ? 'status-online' : 'status-offline'">
                {{ connectionStatus ? languageStore.t('dashboard.connected') : languageStore.t('dashboard.disconnected') }}
              </p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <div class="card-icon llm">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="card-info">
              <h3>{{ languageStore.t('dashboard.llm_provider') }}</h3>
              <p>{{ enabledProvidersCount }} {{ languageStore.t('common.enabled') }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <div class="card-icon agents">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="card-info">
              <h3>{{ languageStore.t('dashboard.agent_count') }}</h3>
              <p>{{ agentCount }} {{ languageStore.t('common.enabled') }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <div class="card-icon tests">
              <el-icon><Document /></el-icon>
            </div>
            <div class="card-info">
              <h3>Tests Run</h3>
              <p>{{ testResults.length }} Total</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Actions -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="12">
        <el-card class="action-card">
          <template #header>
            <div class="card-header">
              <el-icon><Lightning /></el-icon>
              <span>Quick Actions</span>
            </div>
          </template>
          
          <div class="action-buttons">
            <el-button 
              type="primary" 
              size="large" 
              @click="$router.push('/agents')"
              class="action-btn"
            >
              <el-icon><Cpu /></el-icon>
              Test Agents
            </el-button>
            
            <el-button 
              type="success" 
              size="large" 
              @click="$router.push('/llm-config')"
              class="action-btn"
            >
              <el-icon><Setting /></el-icon>
              Configure LLM
            </el-button>
            
            <el-button 
              type="info" 
              size="large" 
              @click="$router.push('/prompt-editor')"
              class="action-btn"
            >
              <el-icon><Edit /></el-icon>
              Edit Prompts
            </el-button>
            
            <el-button 
              type="warning" 
              size="large" 
              @click="runQuickTest"
              :loading="quickTesting"
              class="action-btn"
            >
              <el-icon><VideoPlay /></el-icon>
              Quick Test
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="recent-tests">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>Recent Tests</span>
            </div>
          </template>
          
          <div v-if="recentTests.length > 0" class="test-list">
            <div 
              v-for="test in recentTests" 
              :key="test.id"
              class="test-item"
            >
              <div class="test-info">
                <div class="test-agent">{{ test.agent }}</div>
                <div class="test-time">{{ formatTime(test.timestamp) }}</div>
              </div>
              <div class="test-status">
                <el-tag :type="test.success ? 'success' : 'danger'" size="small">
                  {{ test.success ? 'Success' : 'Failed' }}
                </el-tag>
              </div>
            </div>
          </div>
          
          <div v-else class="no-tests">
            <el-empty description="No tests run yet" :image-size="80">
              <el-button type="primary" @click="$router.push('/agents')">
                Run Your First Test
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- System Information -->
    <el-row :gutter="20" class="system-info">
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>System Information</span>
            </div>
          </template>
          
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">Backend API:</span>
              <span class="info-value">http://localhost:5000</span>
            </div>
            <div class="info-item">
              <span class="info-label">Frontend Port:</span>
              <span class="info-value">3000</span>
            </div>
            <div class="info-item">
              <span class="info-label">Current Provider:</span>
              <span class="info-value">{{ currentProvider }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Last Updated:</span>
              <span class="info-value">{{ lastUpdated }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>Available Agents</span>
            </div>
          </template>
          
          <div class="agent-list">
            <div 
              v-for="agent in availableAgents" 
              :key="agent.type"
              class="agent-item"
            >
              <div class="agent-icon">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="agent-details">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-desc">{{ agent.description }}</div>
                <div v-if="agent.subagents && agent.subagents.length" class="subagent-list">
                  <el-tag
                    v-for="sub in agent.subagents"
                    :key="sub"
                    size="small"
                    class="subagent-tag"
                  >{{ sub }}</el-tag>
                </div>
              </div>
              <div class="agent-status">
                <el-tag type="success" size="small">Ready</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useLanguageStore } from '@/stores/languageStore'
import apiService from '@/services/apiService'
import { ElMessage } from 'element-plus'
import { 
  House, 
  Connection, 
  Cpu, 
  Monitor, 
  Document, 
  Lightning, 
  Setting, 
  Edit, 
  VideoPlay, 
  Clock, 
  InfoFilled, 
  DataAnalysis 
} from '@element-plus/icons-vue'

const appStore = useAppStore()
const languageStore = useLanguageStore()

// Reactive data
const connectionStatus = ref(false)
const quickTesting = ref(false)
const lastUpdated = ref('')

// Computed
const availableProviders = computed(() => appStore.availableProviders)
const testResults = computed(() => appStore.testResults)
const currentProvider = computed(() => appStore.currentLLMProvider)

const agentCount = computed(() => 4) // diary, sensor, bazi, event

const enabledProvidersCount = computed(() => {
  return availableProviders.value.filter(provider => provider.enabled).length
})

const recentTests = computed(() => {
  return testResults.value.slice(0, 5).map(result => ({
    id: result.id,
    agent: result.agent || 'Unknown',
    timestamp: result.timestamp,
    success: result.success
  }))
})

const availableAgents = ref([
  {
    type: 'diary',
    name: 'Diary Agent',
    description: 'Core diary system with multiple specialized sub-agents',
    subagents: [
      'Weather Agent',
      'Trending Agent',
      'Holiday Agent',
      'Friends Agent',
      'Interactive Agent',
      'Dialogue Agent',
      'Neglect Agent',
      'Adoption Agent'
    ]
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
  }
])

// Methods
const checkConnection = async () => {
  try {
    const result = await apiService.healthCheck()
    connectionStatus.value = result.success
    if (result.success) {
      await appStore.loadLLMProviders()
      lastUpdated.value = new Date().toLocaleString()
    }
  } catch (error) {
    connectionStatus.value = false
    console.error('Connection check failed:', error)
  }
}

const runQuickTest = async () => {
  quickTesting.value = true
  try {
    // Run a simple diary agent test
    const testData = {
      event_type: 'human_machine_interaction',
      event_name: 'quick_test',
      event_details: {
        interaction_type: '抚摸',
        duration: '1分钟',
        user_response: 'positive'
      }
    }
    
    const result = await apiService.testDiaryAgent(testData)
    
    appStore.addTestResult({
      agent: 'Diary Agent',
      success: result.success,
      timestamp: new Date().toISOString(),
      data: result
    })
    
    ElMessage.success('Quick test completed successfully!')
  } catch (error) {
    ElMessage.error(`Quick test failed: ${error.message}`)
  } finally {
    quickTesting.value = false
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) { // Less than 1 minute
    return 'Just now'
  } else if (diff < 3600000) { // Less than 1 hour
    return `${Math.floor(diff / 60000)} minutes ago`
  } else if (diff < 86400000) { // Less than 1 day
    return `${Math.floor(diff / 3600000)} hours ago`
  } else {
    return date.toLocaleDateString()
  }
}

// Lifecycle
onMounted(async () => {
  languageStore.initLanguage()
  await checkConnection()
  
  // Auto-refresh every 30 seconds
  setInterval(checkConnection, 30000)
})
</script>

<style scoped>
.dashboard {
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

.status-cards {
  margin-bottom: 30px;
}

.status-card {
  height: 120px;
}

.card-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  font-size: 24px;
  color: white;
}

.card-icon.connection {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.card-icon.llm {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.card-icon.agents {
  background: linear-gradient(135deg, #e6a23c, #f0c78a);
}

.card-icon.tests {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.card-info h3 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 18px;
}

.card-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.status-online {
  color: #67c23a !important;
  font-weight: 600;
}

.status-offline {
  color: #f56c6c !important;
  font-weight: 600;
}

.quick-actions {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.action-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.action-btn {
  height: 60px;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-list {
  max-height: 300px;
  overflow-y: auto;
}

.test-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.test-item:last-child {
  border-bottom: none;
}

.test-info {
  flex: 1;
}

.test-agent {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.test-time {
  font-size: 12px;
  color: #666;
}

.test-status {
  margin-left: 15px;
}

.no-tests {
  text-align: center;
  padding: 20px;
}

.system-info {
  margin-bottom: 30px;
}

.info-list {
  padding: 10px 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 600;
  color: #333;
}

.info-value {
  color: #666;
  font-family: 'Courier New', monospace;
}

.agent-list {
  max-height: 300px;
  overflow-y: auto;
}

.agent-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.agent-item:last-child {
  border-bottom: none;
}

.agent-icon {
  width: 40px;
  height: 40px;
  background: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: #666;
}

.agent-details {
  flex: 1;
}

.agent-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}

.agent-desc {
  font-size: 12px;
  color: #666;
}

.agent-status {
  margin-left: 15px;
}

.subagent-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.subagent-tag {
  background: #f0f9ff;
  color: #409eff;
  border-color: #c6e2ff;
}
</style>
