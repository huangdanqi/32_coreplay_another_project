<template>
  <div id="app">
    <el-container>
      <!-- Header -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="app-title">
            <span class="title-main">CorePlay Agent</span>
          </div>
          <div class="header-actions">
            <div class="navigation-buttons">
              <el-button 
                :type="$route.path === '/' ? 'primary' : 'default'"
                @click="$router.push('/')"
              >
                {{ languageStore.t('nav.dashboard') }}
              </el-button>
              <el-button 
                :type="$route.path === '/agents' ? 'primary' : 'default'"
                @click="$router.push('/agents')"
              >
                {{ languageStore.t('nav.agent_tester') }}
              </el-button>
              <el-button 
                :type="$route.path === '/prompt-editor' ? 'primary' : 'default'"
                @click="$router.push('/prompt-editor')"
              >
                {{ languageStore.t('nav.prompt_editor') }}
              </el-button>
              <el-button 
                :type="$route.path === '/llm-config' ? 'primary' : 'default'"
                @click="$router.push('/llm-config')"
              >
                {{ languageStore.t('nav.llm_config') }}
              </el-button>
            </div>
            <div class="header-right">
              <el-dropdown @command="handleLanguageChange" class="language-dropdown">
                <span class="language-info">
                  <el-icon><Setting /></el-icon>
                  {{ languageStore.isChinese ? '中文' : 'English' }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="zh" :class="{ active: languageStore.isChinese }">
                      🇨🇳 中文
                    </el-dropdown-item>
                    <el-dropdown-item command="en" :class="{ active: languageStore.isEnglish }">
                      🇺🇸 English
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button 
                type="success" 
                :icon="Connection" 
                @click="checkConnection"
                :loading="checkingConnection"
                size="small"
              >
                {{ languageStore.t('header.check_connection') }}
              </el-button>
              <el-dropdown @command="handleUserCommand" class="user-dropdown">
                <span class="user-info">
                  <el-icon><User /></el-icon>
                  {{ languageStore.t('header.user.admin') }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="change-password">
                      <el-icon><Key /></el-icon>
                      {{ languageStore.t('header.user.change_password') }}
                    </el-dropdown-item>
                    <el-dropdown-item divided command="logout">
                      <el-icon><SwitchButton /></el-icon>
                      {{ languageStore.t('header.user.logout') }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </el-header>

      <!-- Main Content -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- Global Error Dialog -->
    <el-dialog
      v-model="showError"
      title="Error"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-alert
        :title="error"
        type="error"
        :closable="false"
        show-icon
      />
      <template #footer>
        <el-button @click="clearError">Close</el-button>
      </template>
    </el-dialog>

    <!-- Password Change Dialog -->
    <PasswordChangeDialog 
      v-model="showPasswordChangeDialog"
      @success="handlePasswordChangeSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useAuthStore } from '@/stores/authStore'
import { useLanguageStore } from '@/stores/languageStore'
import { useRouter } from 'vue-router'
import apiService from '@/services/apiService'
import { ElMessage, ElMessageBox } from 'element-plus'
import PasswordChangeDialog from '@/components/PasswordChangeDialog.vue'
import { 
  Monitor, 
  Connection, 
  Setting,
  User,
  ArrowDown,
  Key,
  SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const languageStore = useLanguageStore()

// Reactive data
const checkingConnection = ref(false)
const connectionStatus = ref(false)
const showError = ref(false)
const showPasswordChangeDialog = ref(false)

// Computed
const currentProvider = computed(() => appStore.currentLLMProvider)
const error = computed(() => appStore.error)

// Methods
const checkConnection = async () => {
  checkingConnection.value = true
  try {
    const result = await apiService.healthCheck()
    connectionStatus.value = result.success
    if (result.success) {
      await appStore.loadLLMProviders()
    }
  } catch (err) {
    connectionStatus.value = false
    appStore.setError(`Connection failed: ${err.message}`)
    showError.value = true
  } finally {
    checkingConnection.value = false
  }
}

const handleLanguageChange = (lang) => {
  languageStore.setLanguage(lang)
  ElMessage.success(lang === 'zh' ? '语言已切换为中文' : 'Language switched to English')
}

const handleUserCommand = async (command) => {
  switch (command) {
    case 'change-password':
      showPasswordChangeDialog.value = true
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          'Are you sure you want to logout?',
          'Confirm Logout',
          {
            confirmButtonText: 'Logout',
            cancelButtonText: 'Cancel',
            type: 'warning',
          }
        )
        await authStore.logout()
        ElMessage.success('Logged out successfully')
        router.push('/login')
      } catch (error) {
        // User cancelled
      }
      break
  }
}

const handlePasswordChangeSuccess = () => {
  ElMessage.success('Password changed successfully!')
}

const clearError = () => {
  showError.value = false
  appStore.clearError()
}

// Lifecycle
onMounted(() => {
  languageStore.initLanguage()
  authStore.checkAuthStatus()
  checkConnection()
})
</script>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #4a90e2 0%, #7b68ee 100%);
  color: white;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  height: 70px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  width: 100%;
}

.app-title {
  margin: 0;
  display: flex;
  align-items: center;
}

.title-main {
  font-size: 22px;
  font-weight: 600;
  color: white;
  margin: 0;
  padding: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.navigation-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.navigation-buttons .el-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.navigation-buttons .el-button--primary {
  background-color: #409eff;
  border-color: #409eff;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.navigation-buttons .el-button--default {
  background-color: white;
  border-color: #dcdfe6;
  color: #606266;
}

.navigation-buttons .el-button--default:hover {
  background-color: #f5f7fa;
  border-color: #c0c4cc;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-right .el-button--success {
  background-color: #67c23a;
  border-color: #67c23a;
  border-radius: 6px;
  font-weight: 500;
}

.header-right .el-button--success:hover {
  background-color: #5daf34;
  border-color: #5daf34;
}

.language-dropdown {
  cursor: pointer;
}

.language-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.3s;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.language-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.3s;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

.main-content {
  background: #fafafa;
  padding: 24px;
  min-height: calc(100vh - 70px);
}

#app {
  height: 100vh;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
</style>
