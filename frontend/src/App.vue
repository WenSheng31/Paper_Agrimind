<template>
  <router-view />
  <Toast />
</template>

<script setup>
import { onErrorCaptured } from 'vue'
import Toast from '@/components/common/Toast.vue'
import { useTheme } from '@/composables/useTheme'
import { useToast } from '@/composables/useToast'

// 初始化主題邏輯 (監聯系統變更等)
useTheme()

// 全局錯誤邊界：捕捉子組件未處理的錯誤
const { showToast } = useToast()
onErrorCaptured((err) => {
  console.error('Component error:', err)
  showToast('系統發生錯誤，請重新整理頁面', 'error')
  return false
})
</script>
