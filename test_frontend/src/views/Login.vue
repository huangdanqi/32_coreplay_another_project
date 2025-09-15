<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>
          <el-icon><Monitor /></el-icon>
          {{ languageStore.t('login.title') }}
        </h1>
        <p>{{ languageStore.t('login.subtitle') }}</p>
      </div>

      <el-card class="login-card" shadow="hover">
        <el-form 
          :model="loginForm" 
          :rules="loginRules" 
          ref="loginFormRef"
          @submit.prevent="handleLogin"
        >
          <el-form-item :label="languageStore.t('login.username')" prop="username">
            <el-input 
              v-model="loginForm.username" 
              :placeholder="languageStore.t('login.username')"
              prefix-icon="User"
              size="large"
            />
          </el-form-item>

          <el-form-item :label="languageStore.t('login.password')" prop="password">
            <el-input 
              v-model="loginForm.password" 
              type="password" 
              :placeholder="languageStore.t('login.password')"
              prefix-icon="Lock"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              :loading="authStore.isLoading"
              @click="handleLogin"
              class="login-button"
            >
              <el-icon><Right /></el-icon>
              {{ languageStore.t('login.login_button') }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <h4 class="system-info-title">{{ languageStore.t('login.system_info') }}</h4>
          <div class="system-info">
            <div class="info-item">
              <span class="info-label">{{ languageStore.t('login.version') }}:</span>
              <span class="info-value">1.0.0</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ languageStore.t('login.environment') }}:</span>
              <span class="info-value">Development</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ languageStore.t('login.backend') }}:</span>
              <span class="info-value" :class="backendStatus === 'Connected' ? 'status-connected' : 'status-disconnected'">
                {{ backendStatus }}
              </span>
            </div>
          </div>
          <div class="default-credentials">
            <p>{{ languageStore.t('login.default_credentials') }}</p>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useLanguageStore } from '@/stores/languageStore'
import { useAppStore } from '@/stores/appStore'
import { ElMessage } from 'element-plus'
import { Monitor, Right } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const languageStore = useLanguageStore()
const appStore = useAppStore()

// Form data
const loginForm = reactive({
  username: 'admin',
  password: 'GOODluck!328'
})

const loginFormRef = ref(null)
const backendStatus = ref('Checking...')

// Validation rules
const loginRules = {
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 3, max: 20, message: 'Username must be 3-20 characters', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ]
}

// Methods
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    
    const result = await authStore.login(loginForm.username, loginForm.password)
    
    if (result.success) {
      ElMessage.success(result.message)
      router.push('/')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('Please check your input')
  }
}

const checkBackendStatus = async () => {
  try {
    await appStore.checkConnection()
    backendStatus.value = 'Connected'
  } catch (error) {
    backendStatus.value = 'Disconnected'
  }
}

// Lifecycle
onMounted(() => {
  languageStore.initLanguage()
  checkBackendStatus()
  
  // Check if already logged in
  authStore.checkAuthStatus()
  if (authStore.isLoggedIn) {
    router.push('/')
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.login-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5rem;
  font-weight: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.login-header p {
  margin: 0;
  font-size: 1.1rem;
  opacity: 0.9;
}

.login-card {
  border-radius: 15px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.login-card :deep(.el-card__body) {
  padding: 40px;
}

.login-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
}

.login-footer {
  margin-top: 30px;
}

.system-info-title {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.system-info {
  color: #666;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-label {
  font-weight: 500;
}

.info-value {
  font-weight: 400;
}

.status-connected {
  color: #67c23a;
  font-weight: 600;
}

.status-disconnected {
  color: #f56c6c;
  font-weight: 600;
}
</style>
