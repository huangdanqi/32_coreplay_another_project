<template>
  <el-dialog
    v-model="visible"
    title="Verify Password"
    width="400px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <div class="password-verify-content">
      <el-icon class="lock-icon"><Lock /></el-icon>
      <h3>Enter Password to Save Prompt</h3>
      <p>Please enter your password to save the prompt configuration to the backend files.</p>
      
      <el-form
        :model="verifyForm"
        :rules="verifyRules"
        ref="verifyFormRef"
        @submit.prevent="handleSubmit"
      >
        <el-form-item prop="password">
          <el-input
            v-model="verifyForm.password"
            type="password"
            placeholder="Enter your password"
            show-password
            size="large"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">Cancel</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="isLoading"
        >
          Verify & Save
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'

const authStore = useAuthStore()

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  promptData: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'success', 'error'])

// State
const visible = ref(false)
const isLoading = ref(false)
const verifyFormRef = ref(null)

const verifyForm = reactive({
  password: ''
})

// Validation rules
const verifyRules = {
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' }
  ]
}

// Methods
const handleSubmit = async () => {
  if (!verifyFormRef.value) return

  try {
    await verifyFormRef.value.validate()
    
    isLoading.value = true
    
    // Verify password
    const verifyResult = await authStore.verifyPassword(verifyForm.password)
    
    if (verifyResult.success) {
      // Password verified, now save the prompt
      const saveResult = await authStore.savePrompt(props.promptData)
      
      if (saveResult.success) {
        ElMessage.success('Prompt saved successfully!')
        emit('success', saveResult)
        handleCancel()
      } else {
        ElMessage.error(saveResult.message || 'Failed to save prompt')
        emit('error', saveResult)
      }
    } else {
      ElMessage.error(verifyResult.message || 'Invalid password')
      emit('error', verifyResult)
    }
  } catch (error) {
    ElMessage.error('Please check your input')
    emit('error', error)
  } finally {
    isLoading.value = false
  }
}

const handleCancel = () => {
  // Reset form
  verifyForm.password = ''
  
  // Close dialog
  visible.value = false
  emit('update:modelValue', false)
}

// Watch for prop changes
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})
</script>

<style scoped>
.password-verify-content {
  text-align: center;
  padding: 20px 0;
}

.lock-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 20px;
}

.password-verify-content h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.password-verify-content p {
  margin: 0 0 30px 0;
  color: #666;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
