<template>
  <router-view />
  <Toast />
</template>

<script setup>
import Toast from '@/components/common/Toast.vue'
import { useTheme } from '@/composables/useTheme'

// 初始化主題邏輯 (監聽系統變更等)
useTheme()
</script>
