import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/apiService'

export const useAppStore = defineStore('app', () => {
  // State
  const currentLLMProvider = ref('zhipu')
  const availableProviders = ref([])
  const currentPrompt = ref('')
  const testResults = ref([])
  const isLoading = ref(false)
  const error = ref('')

  // Getters
  const hasResults = computed(() => testResults.value.length > 0)
  const currentProviderConfig = computed(() => 
    availableProviders.value.find(p => p.provider_name === currentLLMProvider.value)
  )

  // Actions
  const loadLLMProviders = async () => {
    try {
      const config = await apiService.getLLMConfig()
      if (config.success && config.data && config.data.providers) {
        availableProviders.value = Object.values(config.data.providers)
      } else {
        availableProviders.value = []
      }
    } catch (err) {
      error.value = `Failed to load LLM providers: ${err.message}`
      availableProviders.value = []
    }
  }

  const setLLMProvider = (provider) => {
    currentLLMProvider.value = provider
  }

  const setPrompt = (prompt) => {
    currentPrompt.value = prompt
  }

  const addTestResult = (result) => {
    testResults.value.unshift({
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...result
    })
  }

  const clearResults = () => {
    testResults.value = []
  }

  const setLoading = (loading) => {
    isLoading.value = loading
  }

  const setError = (err) => {
    error.value = err
  }

  const clearError = () => {
    error.value = ''
  }

  return {
    // State
    currentLLMProvider,
    availableProviders,
    currentPrompt,
    testResults,
    isLoading,
    error,
    
    // Getters
    hasResults,
    currentProviderConfig,
    
    // Actions
    loadLLMProviders,
    setLLMProvider,
    setPrompt,
    addTestResult,
    clearResults,
    setLoading,
    setError,
    clearError
  }
})
