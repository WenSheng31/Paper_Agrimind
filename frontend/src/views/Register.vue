<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-100 p-4 dark:bg-slate-900">
    <div class="w-full max-w-md">
      <div class="rounded border border-slate-200 bg-white p-8 dark:border-slate-700 dark:bg-slate-800">
        <h1 class="mb-6 text-center text-2xl font-bold text-slate-800 dark:text-white">註冊</h1>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label for="username" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              用戶名稱
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              required
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white dark:placeholder-slate-400"
              placeholder="請輸入用戶名稱"
            />
          </div>

          <div>
            <label for="email" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              電子郵件
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white dark:placeholder-slate-400"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label for="password" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              密碼
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              minlength="6"
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white dark:placeholder-slate-400"
              placeholder="至少 6 個字元"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full cursor-pointer rounded bg-emerald-600 py-2 text-white transition
              hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-emerald-600 dark:hover:bg-emerald-700"
          >
            {{ loading ? '註冊中...' : '註冊' }}
          </button>
        </form>

        <div class="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
          已經有帳號？
          <router-link to="/login" class="text-emerald-600 hover:underline dark:text-emerald-400"> 立即登入 </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const authStore = useAuthStore()
const { loading } = storeToRefs(authStore)
const { showToast } = useToast()

const form = ref({
  username: '',
  email: '',
  password: '',
})

async function handleRegister() {
  const result = await authStore.register(form.value)

  if (result.success) {
    showToast('註冊成功，請登入')
    router.push('/login')
  } else {
    showToast(result.message, 'error')
  }
}
</script>
