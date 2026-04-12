<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-100 p-4 dark:bg-slate-900">
    <div class="w-full max-w-md">
      <div class="rounded border border-slate-200 bg-white p-8 dark:border-slate-700 dark:bg-slate-800">
        <h1 class="mb-6 text-center text-2xl font-bold text-slate-800 dark:text-white">登入</h1>
        <div ref="googleBtnRef" class="flex justify-center"></div>
        <p v-if="loading" class="mt-4 text-center text-slate-600 dark:text-slate-400">登入中...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const authStore = useAuthStore()
const { showToast } = useToast()
const loading = ref(false)
const googleBtnRef = ref(null)

async function handleCredentialResponse(response) {
  loading.value = true
  const result = await authStore.loginWithGoogle(response.credential)
  if (result.success) {
    showToast('登入成功')
    router.push('/home')
  } else {
    showToast(result.message, 'error')
  }
  loading.value = false
}

onMounted(() => {
  const initGoogle = () => {
    if (window.google?.accounts?.id) {
      window.google.accounts.id.initialize({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
      })
      window.google.accounts.id.renderButton(googleBtnRef.value, {
        theme: 'outline',
        size: 'large',
        width: 300,
        text: 'signin_with',
        locale: 'zh-TW',
      })
    } else {
      setTimeout(initGoogle, 100)
    }
  }
  initGoogle()
})
</script>
