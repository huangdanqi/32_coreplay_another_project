import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/apiService'

export const useAuthStore = defineStore('auth', () => {
  // State
  const isAuthenticated = ref(false)
  const user = ref(null)
  const isLoading = ref(false)

  // Computed
  const isLoggedIn = computed(() => isAuthenticated.value && user.value)

  // Actions
  const login = async (username, password) => {
    isLoading.value = true
    try {
      const response = await apiService.login(username, password)
      if (response.success) {
        isAuthenticated.value = true
        user.value = { username, role: response.role || 'admin' }
        localStorage.setItem('auth_token', response.token || 'authenticated')
        return { success: true, message: 'Login successful' }
      } else {
        return { success: false, message: response.message || 'Login failed' }
      }
    } catch (error) {
      return { success: false, message: error.message || 'Login failed' }
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      await apiService.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      isAuthenticated.value = false
      user.value = null
      localStorage.removeItem('auth_token')
    }
  }

  const changePassword = async (oldPassword, newPassword) => {
    isLoading.value = true
    try {
      const response = await apiService.changePassword(oldPassword, newPassword)
      return response
    } catch (error) {
      return { success: false, message: error.message || 'Password change failed' }
    } finally {
      isLoading.value = false
    }
  }

  const verifyPassword = async (password) => {
    try {
      const response = await apiService.verifyPassword(password)
      return response
    } catch (error) {
      return { success: false, message: error.message || 'Password verification failed' }
    }
  }

  const savePrompt = async (promptData) => {
    try {
      const response = await apiService.savePrompt(promptData)
      return response
    } catch (error) {
      return { success: false, message: error.message || 'Failed to save prompt' }
    }
  }

  const checkAuthStatus = () => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      isAuthenticated.value = true
      user.value = { username: 'admin', role: 'admin' }
    }
  }

  return {
    // State
    isAuthenticated,
    user,
    isLoading,
    // Computed
    isLoggedIn,
    // Actions
    login,
    logout,
    changePassword,
    verifyPassword,
    savePrompt,
    checkAuthStatus
  }
})
