import axios from 'axios'

const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || '/api'

const defaultLLMConfig = {
  providers: {
    zhipu: {
      provider_name: 'zhipu',
      provider_type: 'cloud',
      api_endpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
      model_name: 'glm-4',
      max_tokens: 150,
      temperature: 0.7,
      timeout: 30,
      retry_attempts: 3,
      priority: 1,
      enabled: true,
      capabilities: ['general','chinese','creative','analytical']
    },
    qwen: {
      provider_name: 'qwen',
      provider_type: 'cloud',
      api_endpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
      model_name: 'qwen-turbo',
      max_tokens: 150,
      temperature: 0.7,
      timeout: 30,
      retry_attempts: 3,
      priority: 2,
      enabled: true,
      capabilities: ['general','creative','fast']
    },
    deepseek: {
      provider_name: 'deepseek',
      provider_type: 'cloud',
      api_endpoint: 'https://api.deepseek.com/v1/chat/completions',
      model_name: 'deepseek-chat',
      max_tokens: 150,
      temperature: 0.7,
      timeout: 30,
      retry_attempts: 3,
      priority: 3,
      enabled: true,
      capabilities: ['general','coding','analytical']
    },
    ollama_qwen3: {
      provider_name: 'ollama_qwen3',
      provider_type: 'ollama',
      api_endpoint: 'http://localhost:11434/api/generate',
      model_name: 'qwen3:4b',
      max_tokens: 150,
      temperature: 0.7,
      timeout: 60,
      retry_attempts: 3,
      priority: 4,
      enabled: true,
      capabilities: ['general','creative','local']
    }
  },
  model_selection: {
    default_provider: 'zhipu',
    enable_auto_switch: true,
    switch_on_failure: true,
    switch_on_timeout: true,
    max_switches_per_request: 3,
    timeout_threshold: 10,
    prefer_fastest: false,
    prefer_cheapest: false,
    prefer_highest_quality: true
  }
}

const apiService = {
  // Health check
  async healthCheck() {
    const response = await axios.get(`${API_BASE_URL}/health`)
    return response.data
  },

  // LLM Configuration
  async getLLMConfig() {
    try {
      const response = await axios.get(`${API_BASE_URL}/llm-config`)
      return response.data
    } catch (err) {
      // Fallback: server does not expose llm-config in simple_api
      return defaultLLMConfig
    }
  },

  async updateLLMConfig(config) {
    try {
      const response = await axios.post(`${API_BASE_URL}/llm-config`, config)
      return response.data
    } catch (err) {
      // Not supported in simple_api; simulate success for frontend state
      return { success: true, message: 'LLM config update simulated (not persisted in simple_api)', data: config }
    }
  },

  async testLLMProvider(providerName) {
    try {
      const response = await axios.post(`${API_BASE_URL}/llm-config/test`, {
        provider_name: providerName
      })
      return response.data
    } catch (err) {
      return { success: false, message: 'Test endpoint not available', error: err.message }
    }
  },

  async checkLocalModel(modelName) {
    try {
      const response = await axios.post(`${API_BASE_URL}/llm-config/check-local`, {
        model_name: modelName
      })
      return response.data
    } catch (err) {
      return { success: false, message: 'Local model check not available', error: err.message }
    }
  },

  // Diary Agent Testing
  async testDiaryAgent(eventData, provider = null) {
    // simple_api expects event_category and event_name
    const response = await axios.post(`${API_BASE_URL}/diary/process`, eventData)
    return response.data
  },

  async testDiaryAgentWithCustomPrompt(eventData, customPrompt, provider = null) {
    // Use the new custom prompt endpoint
    const requestData = {
      ...eventData,
      custom_prompt: customPrompt
    }
    const response = await axios.post(`${API_BASE_URL}/diary/process-custom`, requestData)
    return response.data
  },

  async testBatchDiaryAgent(events, provider = null) {
    const payload = { events }
    const response = await axios.post(`${API_BASE_URL}/diary/batch-process`, payload)
    return response.data
  },

  // Sensor Event Agent Testing
  async testSensorAgent(sensorData, provider = null) {
    try {
      const payload = { ...sensorData, provider }
      const response = await axios.post(`${API_BASE_URL}/sensor/translate`, payload)
      return response.data
    } catch (err) {
      console.error('Sensor agent test failed:', err)
      return { 
        success: false, 
        message: err.response?.data?.message || 'Sensor agent test failed', 
        error: err.response?.data?.error || 'SENSOR_ERROR' 
      }
    }
  },

  async testBatchSensorAgent(sensorEvents, provider = null) {
    try {
      const payload = { events: sensorEvents, provider }
      const response = await axios.post(`${API_BASE_URL}/sensor/batch`, payload)
      return response.data
    } catch (err) {
      return { success: false, message: 'Sensor batch endpoint is not available in simple_diary_api', error: 'NOT_SUPPORTED' }
    }
  },

  // BaZi/WuXing Agent Testing
  async testBaziAgent(birthData, provider = null) {
    const payload = {
      ...birthData,
      provider
    }
    const response = await axios.post(`${API_BASE_URL}/bazi_wuxing/calc`, payload)
    return response.data
  },

  // Event Agents Testing
  async testEventExtract(dialogueData, provider = null) {
    const payload = {
      ...dialogueData,
      provider
    }
    const response = await axios.post(`${API_BASE_URL}/event/extract`, payload)
    return response.data
  },

  async testEventUpdate(extractionResult, relatedEvents, provider = null) {
    const payload = {
      extraction_result: extractionResult,
      related_events: relatedEvents,
      provider
    }
    const response = await axios.post(`${API_BASE_URL}/event/update`, payload)
    return response.data
  },

  async testEventPipeline(dialoguePayload, relatedEvents, provider = null) {
    const payload = {
      dialogue_payload: dialoguePayload,
      related_events: relatedEvents,
      provider
    }
    const response = await axios.post(`${API_BASE_URL}/event/pipeline`, payload)
    return response.data
  },

  // Authentication
  async login(username, password) {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, {
      username,
      password
    })
    return response.data
  },

  async logout() {
    const response = await axios.post(`${API_BASE_URL}/auth/logout`)
    return response.data
  },

  async verifyPassword(password) {
    const response = await axios.post(`${API_BASE_URL}/auth/verify`, {
      password
    })
    return response.data
  },

  async changePassword(oldPassword, newPassword) {
    const response = await axios.post(`${API_BASE_URL}/auth/change-password`, {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  },

  // Prompt Management
  async getPromptTemplates() {
    const response = await axios.get(`${API_BASE_URL}/prompts/templates`)
    return response.data
  },

  async savePrompt(promptData) {
    const response = await axios.post(`${API_BASE_URL}/prompts/save`, promptData)
    return response.data
  },

  async testPrompt(promptData, testPayload) {
    // Test the prompt with the given payload
    const { agent_type } = promptData
    
    switch (agent_type) {
      case 'diary':
        return await this.testDiaryAgent(testPayload)
      case 'sensor':
        return await this.testSensorAgent(testPayload)
      case 'bazi':
        return await this.testBaziAgent(testPayload)
      case 'event':
        return await this.testEventExtract(testPayload)
      default:
        return { success: false, message: `No test method available for agent type: ${agent_type}` }
    }
  },

  async updatePromptTemplate(agentType, promptConfig) {
    const response = await axios.post(`${API_BASE_URL}/prompts/update`, {
      agent_type: agentType,
      prompt_config: promptConfig
    })
    return response.data
  },

  // Test Templates
  async getTestTemplates() {
    const response = await axios.get(`${API_BASE_URL}/test/templates`)
    return response.data
  },

  // Custom Test
  async runCustomTest(testConfig) {
    // Not supported; simulate failure with hint
    return { success: false, message: 'Custom test not supported in simple_diary_api' }
  }
}

export default apiService
