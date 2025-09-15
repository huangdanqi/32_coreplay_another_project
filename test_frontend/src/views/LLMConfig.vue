<template>
  <div class="llm-config">
    <div class="page-header">
      <h2>
        <el-icon><Setting /></el-icon>
        LLM Configuration
      </h2>
      <p>Manage LLM providers and their settings</p>
    </div>

    <el-row :gutter="20">
      <!-- Provider List -->
      <el-col :span="8">
        <el-card class="provider-list">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>Enabled Providers</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="addNewProvider"
                :icon="Plus"
              >
                Add Provider
              </el-button>
            </div>
          </template>

          <div class="provider-items">
            <div 
              v-for="provider in enabledProviders" 
              :key="provider.provider_name"
              class="provider-item"
              :class="{ active: selectedProvider === provider.provider_name }"
              @click="selectProvider(provider.provider_name)"
            >
              <div class="provider-info">
                <div class="provider-name">{{ provider.provider_name }}</div>
                <div class="provider-type">{{ provider.provider_type }}</div>
              </div>
              <div class="provider-status">
                <el-tag 
                  :type="provider.enabled ? 'success' : 'danger'" 
                  size="small"
                >
                  {{ provider.enabled ? 'Enabled' : 'Disabled' }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Provider Configuration -->
      <el-col :span="16">
        <el-card class="provider-config">
          <template #header>
            <div class="card-header">
              <el-icon><Edit /></el-icon>
              <span>Provider Configuration</span>
              <div class="header-actions">
                <el-button 
                  type="success" 
                  size="small" 
                  @click="testProvider"
                  :loading="testingProvider"
                  :disabled="!selectedProvider"
                >
                  <el-icon><Connection /></el-icon>
                  Test Connection
                </el-button>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="saveProvider"
                  :disabled="!selectedProvider"
                >
                  <el-icon><Check /></el-icon>
                  Save Changes
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="selectedProvider" class="config-form">
            <el-form :model="currentProviderConfig" label-width="140px">
              <!-- Basic Settings -->
              <el-divider content-position="left">Basic Settings</el-divider>
              
              <el-form-item label="Provider Name">
                <el-input v-model="currentProviderConfig.provider_name" />
              </el-form-item>
              
              <el-form-item label="Provider Type">
                <el-select v-model="currentProviderConfig.provider_type">
                  <el-option label="Cloud" value="cloud" />
                  <el-option label="Local" value="local" />
                  <el-option label="Ollama" value="ollama" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="API Endpoint">
                <el-input v-model="currentProviderConfig.api_endpoint" />
              </el-form-item>
              
              <el-form-item label="API Key">
                <el-input 
                  v-model="currentProviderConfig.api_key" 
                  type="password" 
                  show-password
                />
              </el-form-item>
              
              <el-form-item label="Model Name">
                <el-input v-model="currentProviderConfig.model_name" />
              </el-form-item>

              <!-- Performance Settings -->
              <el-divider content-position="left">Performance Settings</el-divider>
              
              <el-form-item label="Max Tokens">
                <el-input-number 
                  v-model="currentProviderConfig.max_tokens" 
                  :min="1" 
                  :max="4000"
                />
              </el-form-item>
              
              <el-form-item label="Temperature">
                <el-slider 
                  v-model="currentProviderConfig.temperature" 
                  :min="0" 
                  :max="2" 
                  :step="0.1"
                  show-input
                />
              </el-form-item>
              
              <el-form-item label="Timeout (seconds)">
                <el-input-number 
                  v-model="currentProviderConfig.timeout" 
                  :min="5" 
                  :max="120"
                />
              </el-form-item>
              
              <el-form-item label="Retry Attempts">
                <el-input-number 
                  v-model="currentProviderConfig.retry_attempts" 
                  :min="1" 
                  :max="10"
                />
              </el-form-item>

              <!-- Priority & Status -->
              <el-divider content-position="left">Priority & Status</el-divider>
              
              <el-form-item label="Priority">
                <el-input-number 
                  v-model="currentProviderConfig.priority" 
                  :min="1" 
                  :max="10"
                />
                <span class="form-help">Lower number = higher priority</span>
              </el-form-item>
              
              <el-form-item label="Enabled">
                <div class="enabled-control">
                  <el-switch 
                    v-model="currentProviderConfig.enabled" 
                    :disabled="!canEnableProvider"
                  />
                  <div v-if="!canEnableProvider" class="validation-message">
                    <el-icon v-if="isCloudProvider"><Warning /></el-icon>
                    <el-icon v-else-if="isLocalProvider"><Warning /></el-icon>
                    <span v-if="isCloudProvider">API Key required</span>
                    <span v-else-if="isLocalProvider">Model name required</span>
                  </div>
                </div>
              </el-form-item>
              
              <el-form-item label="Capabilities">
                <el-checkbox-group v-model="currentProviderConfig.capabilities">
                  <el-checkbox label="general">General</el-checkbox>
                  <el-checkbox label="creative">Creative</el-checkbox>
                  <el-checkbox label="analytical">Analytical</el-checkbox>
                  <el-checkbox label="coding">Coding</el-checkbox>
                  <el-checkbox label="chinese">Chinese</el-checkbox>
                  <el-checkbox label="fast">Fast</el-checkbox>
                  <el-checkbox label="local">Local</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-form>
          </div>

          <div v-else class="no-selection">
            <el-empty description="Select a provider to configure">
              <el-button type="primary" @click="addNewProvider">
                Add New Provider
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Global Settings -->
    <el-row :gutter="20" class="global-settings">
      <el-col :span="24">
        <el-card class="global-config">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>Global Settings</span>
            </div>
          </template>

          <el-form :model="globalSettings" label-width="200px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Default Provider">
                  <el-select v-model="globalSettings.default_provider">
                    <el-option 
                      v-for="provider in providers" 
                      :key="provider.provider_name" 
                      :label="provider.provider_name" 
                      :value="provider.provider_name"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="Enable Auto Switch">
                  <el-switch v-model="globalSettings.enable_auto_switch" />
                </el-form-item>
                
                <el-form-item label="Switch on Failure">
                  <el-switch v-model="globalSettings.switch_on_failure" />
                </el-form-item>
              </el-col>
              
              <el-col :span="12">
                <el-form-item label="Switch on Timeout">
                  <el-switch v-model="globalSettings.switch_on_timeout" />
                </el-form-item>
                
                <el-form-item label="Max Switches per Request">
                  <el-input-number 
                    v-model="globalSettings.max_switches_per_request" 
                    :min="1" 
                    :max="5"
                  />
                </el-form-item>
                
                <el-form-item label="Timeout Threshold">
                  <el-input-number 
                    v-model="globalSettings.timeout_threshold" 
                    :min="1" 
                    :max="60"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item>
              <el-button type="primary" @click="saveGlobalSettings">
                <el-icon><Check /></el-icon>
                Save Global Settings
              </el-button>
              <el-button @click="resetGlobalSettings">
                <el-icon><Refresh /></el-icon>
                Reset to Default
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- Password Verification Dialog -->
    <PasswordVerifyDialog 
      v-model="showPasswordDialog"
      :prompt-data="getConfigData()"
      @success="handleSaveSuccess"
      @error="handleSaveError"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useAuthStore } from '@/stores/authStore'
import apiService from '@/services/apiService'
import { ElMessage, ElMessageBox } from 'element-plus'
import PasswordVerifyDialog from '@/components/PasswordVerifyDialog.vue'
import { 
  Setting, 
  List, 
  Plus, 
  Edit, 
  Connection, 
  Check, 
  Refresh,
  Warning
} from '@element-plus/icons-vue'

const appStore = useAppStore()
const authStore = useAuthStore()

// Reactive data
const providers = ref([])
const selectedProvider = ref('')
const testingProvider = ref(false)
const showPasswordDialog = ref(false)
const globalSettings = ref({
  default_provider: 'zhipu',
  enable_auto_switch: true,
  switch_on_failure: true,
  switch_on_timeout: true,
  switch_on_high_cost: false,
  max_switches_per_request: 3,
  timeout_threshold: 10,
  prefer_fastest: false,
  prefer_cheapest: false,
  prefer_highest_quality: true
})

// Computed
const enabledProviders = computed(() => {
  return providers.value.filter(provider => provider.enabled)
})

const currentProviderConfig = computed(() => {
  return providers.value.find(p => p.provider_name === selectedProvider.value) || {}
})

const isCloudProvider = computed(() => {
  return currentProviderConfig.value.provider_type === 'cloud'
})

const isLocalProvider = computed(() => {
  return currentProviderConfig.value.provider_type === 'ollama' || 
         currentProviderConfig.value.provider_type === 'local'
})

const canEnableProvider = computed(() => {
  if (isCloudProvider.value) {
    return currentProviderConfig.value.api_key && 
           currentProviderConfig.value.api_key.trim() !== ''
  }
  if (isLocalProvider.value) {
    return currentProviderConfig.value.model_name && 
           currentProviderConfig.value.model_name.trim() !== ''
  }
  return true
})

// Methods
const loadProviders = async () => {
  try {
    const response = await apiService.getLLMConfig()
    if (response.success && response.data && response.data.providers) {
      providers.value = Object.values(response.data.providers)
      
      if (response.data.model_selection) {
        globalSettings.value = {
          ...globalSettings.value,
          ...response.data.model_selection
        }
      }
    } else {
      ElMessage.error('Failed to load LLM configuration')
    }
  } catch (error) {
    ElMessage.error(`Failed to load providers: ${error.message}`)
  }
}

const selectProvider = (providerName) => {
  selectedProvider.value = providerName
}

const addNewProvider = () => {
  const newProvider = {
    provider_name: `provider_${Date.now()}`,
    provider_type: 'cloud',
    api_endpoint: '',
    api_key: '',
    model_name: '',
    max_tokens: 150,
    temperature: 0.7,
    timeout: 30,
    retry_attempts: 3,
    priority: 5,
    enabled: true,
    capabilities: ['general']
  }
  
  providers.value.push(newProvider)
  selectedProvider.value = newProvider.provider_name
}

const testProvider = async () => {
  if (!selectedProvider.value) return
  
  testingProvider.value = true
  try {
    const response = await apiService.testLLMProvider(selectedProvider.value)
    if (response.success) {
      ElMessage.success(`Provider ${selectedProvider.value} test successful!`)
    } else {
      ElMessage.error(`Provider test failed: ${response.message}`)
    }
  } catch (error) {
    ElMessage.error(`Test error: ${error.message}`)
  } finally {
    testingProvider.value = false
  }
}

const checkLocalModel = async () => {
  if (!isLocalProvider.value || !currentProviderConfig.value.model_name) return true
  
  try {
    const response = await apiService.checkLocalModel(currentProviderConfig.value.model_name)
    if (response.success && response.running) {
      ElMessage.success(`Model ${currentProviderConfig.value.model_name} is available`)
      return true
    } else {
      ElMessage.warning(`Model ${currentProviderConfig.value.model_name} is not available: ${response.message}`)
      return false
    }
  } catch (error) {
    ElMessage.error(`Error checking local model: ${error.message}`)
    return false
  }
}

const saveProvider = async () => {
  if (!selectedProvider.value) return
  
  // Validate configuration
  if (isCloudProvider.value && !currentProviderConfig.value.api_key?.trim()) {
    ElMessage.error('API Key is required for cloud providers')
    return
  }
  
  if (isLocalProvider.value && !currentProviderConfig.value.model_name?.trim()) {
    ElMessage.error('Model name is required for local providers')
    return
  }
  
  // For local providers, check if model is available
  if (isLocalProvider.value) {
    const modelAvailable = await checkLocalModel()
    if (!modelAvailable) {
      ElMessage.warning('Cannot enable provider: Local model is not available')
      return
    }
  }
  
  // Show password verification dialog
  showPasswordDialog.value = true
}

const handleSaveSuccess = async (result) => {
  try {
    // Update the provider in the list
    const index = providers.value.findIndex(p => p.provider_name === selectedProvider.value)
    if (index !== -1) {
      providers.value[index] = { ...currentProviderConfig.value }
    }
    
    // Save to backend
    const configData = {
      providers: providers.value.reduce((acc, provider) => {
        acc[provider.provider_name] = provider
        return acc
      }, {}),
      model_selection: globalSettings.value
    }
    
    const response = await apiService.updateLLMConfig(configData)
    if (response.success) {
      ElMessage.success('LLM configuration saved successfully!')
      // Update app store
      appStore.loadLLMProviders()
    } else {
      ElMessage.error(`Failed to save: ${response.message}`)
    }
  } catch (error) {
    ElMessage.error(`Save error: ${error.message}`)
  } finally {
    showPasswordDialog.value = false
  }
}

const handleSaveError = (error) => {
  ElMessage.error(`Failed to save configuration: ${error.message || 'Unknown error'}`)
  showPasswordDialog.value = false
}

const getConfigData = () => {
  return {
    provider_name: currentProviderConfig.value.provider_name,
    provider_type: currentProviderConfig.value.provider_type,
    api_endpoint: currentProviderConfig.value.api_endpoint,
    api_key: currentProviderConfig.value.api_key,
    model_name: currentProviderConfig.value.model_name,
    max_tokens: currentProviderConfig.value.max_tokens,
    temperature: currentProviderConfig.value.temperature,
    timeout: currentProviderConfig.value.timeout,
    retry_attempts: currentProviderConfig.value.retry_attempts,
    priority: currentProviderConfig.value.priority,
    enabled: currentProviderConfig.value.enabled,
    capabilities: currentProviderConfig.value.capabilities
  }
}

const saveGlobalSettings = async () => {
  try {
    const config = {
      providers: {},
      model_selection: globalSettings.value
    }
    
    // Convert array back to object
    providers.value.forEach(provider => {
      config.providers[provider.provider_name] = provider
    })
    
    await apiService.updateLLMConfig(config)
    ElMessage.success('Global settings saved successfully!')
  } catch (error) {
    ElMessage.error(`Failed to save global settings: ${error.message}`)
  }
}

const resetGlobalSettings = async () => {
  try {
    await ElMessageBox.confirm(
      'This will reset all global settings to default values. Continue?',
      'Reset Settings',
      {
        confirmButtonText: 'Reset',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    
    globalSettings.value = {
      default_provider: 'zhipu',
      enable_auto_switch: true,
      switch_on_failure: true,
      switch_on_timeout: true,
      switch_on_high_cost: false,
      max_switches_per_request: 3,
      timeout_threshold: 10,
      prefer_fastest: false,
      prefer_cheapest: false,
      prefer_highest_quality: true
    }
    
    ElMessage.success('Global settings reset to default!')
  } catch {
    // User cancelled
  }
}

// Watch for changes
watch(globalSettings, (newSettings) => {
  // Auto-save global settings after a delay
  clearTimeout(window.globalSettingsTimeout)
  window.globalSettingsTimeout = setTimeout(() => {
    saveGlobalSettings()
  }, 2000)
}, { deep: true })

// Lifecycle
onMounted(async () => {
  await loadProviders()
  if (enabledProviders.value.length > 0 && !selectedProvider.value) {
    selectedProvider.value = enabledProviders.value[0].provider_name
  }
})
</script>

<style scoped>
.llm-config {
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

.provider-list {
  height: fit-content;
}

.provider-items {
  max-height: 500px;
  overflow-y: auto;
}

.provider-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  margin-bottom: 10px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.provider-item:hover {
  background: #f5f5f5;
  border-color: #e0e0e0;
}

.provider-item.active {
  background: #e6f7ff;
  border-color: #409eff;
}

.provider-info {
  flex: 1;
}

.provider-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.provider-type {
  font-size: 12px;
  color: #666;
  text-transform: capitalize;
}

.provider-status {
  margin-left: 15px;
}

.config-form {
  padding: 20px 0;
}

.form-help {
  margin-left: 10px;
  font-size: 12px;
  color: #666;
}

.no-selection {
  text-align: center;
  padding: 60px 20px;
}

.global-settings {
  margin-top: 30px;
}

.global-config {
  margin-top: 20px;
}

.el-divider {
  margin: 30px 0 20px 0;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.el-checkbox {
  margin-right: 0;
}

.enabled-control {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.validation-message {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #f56c6c;
}
</style>
