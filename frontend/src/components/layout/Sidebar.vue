<template>
  <!-- 移動設備的遮罩層 -->
  <transition name="fade">
    <div v-if="isOpen" @click="$emit('close')" class="modal-backdrop z-40 lg:hidden"></div>
  </transition>

  <!-- Sidebar -->
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-200 bg-white',
      'dark:border-slate-700 dark:bg-slate-800',
      'transition-transform duration-300 ease-in-out',
      'lg:translate-x-0',
      isOpen ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <!-- 系統 Logo -->
    <div class="flex items-center gap-3 p-6">
      <Leaf :size="28" class="text-emerald-600 dark:text-emerald-400" />
      <h1 class="text-xl font-bold text-slate-900 dark:text-white">AgriMind</h1>
    </div>

    <!-- 導航選單 -->
    <nav class="flex-1 p-4 py-0">
      <ul class="space-y-2">
        <li>
          <router-link
            to="/home"
            @click="$emit('close')"
            class="flex cursor-pointer items-center gap-3 rounded p-3 text-slate-700 transition
              hover:bg-emerald-50 hover:text-emerald-700 dark:text-slate-300
              dark:hover:bg-emerald-900/30 dark:hover:text-emerald-400"
            active-class="bg-emerald-50 text-emerald-700 font-medium dark:bg-emerald-900/30 dark:text-emerald-400"
          >
            <Home :size="20" />
            <span>首頁</span>
          </router-link>
        </li>

        <li>
          <router-link
            to="/farms"
            @click="$emit('close')"
            class="flex cursor-pointer items-center gap-3 rounded p-3 text-slate-700 transition
              hover:bg-emerald-50 hover:text-emerald-700 dark:text-slate-300
              dark:hover:bg-emerald-900/30 dark:hover:text-emerald-400"
            active-class="bg-emerald-50 text-emerald-700 font-medium dark:bg-emerald-900/30 dark:text-emerald-400"
          >
            <Tractor :size="20" />
            <span>農場管理</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- 用戶資訊和登出 -->
    <div class="p-4">
      <!-- 主題切換按鈕 -->
      <button
        @click="toggleTheme"
        class="mb-3 flex w-full cursor-pointer items-center justify-between rounded bg-slate-50 p-2 px-3
          text-sm text-slate-700 transition hover:bg-slate-100 dark:bg-slate-700/50
          dark:text-slate-300 dark:hover:bg-slate-700"
      >
        <span class="flex items-center gap-2">
          <component :is="themeIcon" :size="16" />
          <span>{{ themeLabel }}</span>
        </span>
        <span class="text-xs text-slate-400">{{ themeModeLabel }}</span>
      </button>

      <div class="mb-3 flex items-center gap-3 rounded bg-slate-50 p-2 dark:bg-slate-700/50">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 dark:bg-emerald-500">
          <span class="text-sm font-medium text-white">
            {{ user?.username?.charAt(0).toUpperCase() || '?' }}
          </span>
        </div>
        <div class="min-w-0 flex-1">
          <div class="truncate text-sm font-medium text-slate-900 dark:text-white">
            {{ user?.username || '訪客' }}
          </div>
          <div v-if="isAdmin" class="text-xs text-emerald-600 dark:text-emerald-400">管理員</div>
          <div v-else class="text-xs text-slate-500 dark:text-slate-400">{{ user?.email }}</div>
        </div>
      </div>
      <button
        @click="handleLogout"
        class="flex w-full cursor-pointer items-center justify-center gap-2 rounded bg-slate-100 p-2
          text-sm text-slate-700 transition hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300
          dark:hover:bg-slate-600"
      >
        <LogOut :size="16" />
        <span>登出</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { Home, Tractor, LogOut, Leaf, Sun, Moon, Laptop } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'

defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close'])

const authStore = useAuthStore()
const router = useRouter()
const { user, isAdmin } = storeToRefs(authStore)
const { theme, toggleTheme } = useTheme()

// 計算顯示的主題圖示與文字
const themeIcon = computed(() => {
  if (theme.value === 'light') return Sun
  if (theme.value === 'dark') return Moon
  return Laptop
})

const themeLabel = computed(() => {
  if (theme.value === 'light') return '淺色模式'
  if (theme.value === 'dark') return '深色模式'
  return '跟隨系統'
})

const themeModeLabel = computed(() => {
  if (theme.value === 'light') return 'Light'
  if (theme.value === 'dark') return 'Dark'
  return 'Auto'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
