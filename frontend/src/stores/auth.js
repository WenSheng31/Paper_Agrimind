import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin || false)

  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }

  async function register(userData) {
    loading.value = true
    error.value = null
    try {
      const response = await api.register(userData)
      return { success: true, data: response }
    } catch (err) {
      error.value = err.message
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  async function login(credentials) {
    loading.value = true
    error.value = null
    try {
      const response = await api.login(credentials)
      setToken(response.access_token)
      await fetchUser()
      return { success: true }
    } catch (err) {
      error.value = err.message
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return

    try {
      const userData = await api.getMe()
      user.value = userData
    } catch (err) {
      console.error('獲取用戶資料失敗:', err)
      logout()
    }
  }

  function logout() {
    user.value = null
    setToken(null)
    error.value = null
  }

  async function initialize() {
    if (token.value) {
      await fetchUser()
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    register,
    login,
    logout,
    fetchUser,
    initialize,
  }
})
