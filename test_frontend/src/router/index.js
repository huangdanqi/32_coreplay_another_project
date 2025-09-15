import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import AgentTester from '../views/AgentTester.vue'
import LLMConfig from '../views/LLMConfig.vue'
import PromptEditor from '../views/PromptEditor.vue'
import Dashboard from '../views/Dashboard.vue'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/agents',
    name: 'AgentTester',
    component: AgentTester,
    meta: { requiresAuth: true }
  },
  {
    path: '/llm-config',
    name: 'LLMConfig',
    component: LLMConfig,
    meta: { requiresAuth: true }
  },
  {
    path: '/prompt-editor',
    name: 'PromptEditor',
    component: PromptEditor,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (authStore.isLoggedIn) {
      next()
    } else {
      next('/login')
    }
  } else {
    // If already logged in and trying to access login page, redirect to dashboard
    if (to.name === 'Login' && authStore.isLoggedIn) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
