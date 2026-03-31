<template>
  <!-- 全螢幕歡迎頁 -->
  <div
    v-if="showWelcome && !isAdmin"
    class="flex min-h-screen items-center justify-center bg-slate-100 p-6 dark:bg-slate-900"
  >
    <div
      class="relative w-full max-w-lg rounded border border-slate-200 bg-white p-8 text-center
        dark:border-slate-700 dark:bg-slate-800"
    >
      <button
        @click="skipExperience"
        class="absolute top-3 right-3 cursor-pointer rounded p-1 text-slate-400 transition
          hover:text-slate-600 dark:text-slate-600 dark:hover:text-slate-400"
      >
        <X :size="20" />
      </button>
      <div class="mb-4 text-4xl">👋</div>
      <h1 class="mb-3 text-2xl font-bold text-slate-800 dark:text-white">
        歡迎使用 AgriMind 智慧農業管理系統
      </h1>
      <p class="mb-6 text-base leading-relaxed text-slate-600 dark:text-slate-400">
        我們準備了一系列操作任務，幫助你快速熟悉系統的各項功能。<br />
        完成後可填寫問卷，協助我們改善系統體驗。
      </p>
      <button
        @click="startExperience"
        class="w-full cursor-pointer rounded bg-blue-600 px-4 py-3 text-base font-medium
          text-white transition hover:bg-blue-700"
      >
        開始體驗
      </button>
    </div>
  </div>

  <!-- 主佈局 -->
  <div
    v-else
    :class="[
      'bg-slate-100 dark:bg-slate-900',
      isActive && !isAdmin ? 'flex h-screen flex-col lg:block lg:h-auto lg:min-h-screen' : 'min-h-screen',
    ]"
  >
    <!-- 上半部：主應用區域 -->
    <div
      :class="[
        'relative flex flex-col overflow-hidden',
        isActive && !isAdmin
          ? 'flex-1 max-lg:[transform:translateZ(0)] lg:min-h-screen'
          : 'min-h-screen',
      ]"
    >
      <Sidebar :isOpen="isSidebarOpen" @close="isSidebarOpen = false" />

      <div
        class="flex flex-1 flex-col overflow-hidden transition-[padding-left] duration-300
          ease-in-out lg:min-h-screen lg:pl-64"
      >
        <Header @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />

        <main class="flex flex-1 flex-col overflow-y-auto">
          <div class="flex-1">
            <router-view v-slot="{ Component }">
              <transition name="fade-page" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </div>
          <Footer />
        </main>
      </div>

      <AiChatWidget />
    </div>

    <!-- 下半部：任務面板 - 手機/平板（上下分割） -->
    <div
      v-if="isActive && !isAdmin"
      class="shrink-0 border-t border-blue-200 bg-blue-50 p-4 lg:hidden
        dark:border-blue-900/50 dark:bg-blue-950"
    >
      <TaskGuidePanel />
    </div>

    <!-- 電腦版：懸浮視窗 -->
    <div
      v-if="isActive && !isAdmin"
      class="fixed inset-x-0 bottom-6 z-40 hidden pl-64 lg:block"
    >
      <div
        class="ml-6 w-[28rem] rounded border border-blue-200 bg-blue-50 p-4 shadow-lg
          dark:border-blue-900/50 dark:bg-blue-950"
      >
        <TaskGuidePanel />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { X } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import Header from '@/components/layout/Header.vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import Footer from '@/components/layout/Footer.vue'
import AiChatWidget from '@/components/ai/AiChatWidget.vue'
import TaskGuidePanel from '@/components/common/TaskGuidePanel.vue'
import { useTaskGuide } from '@/composables/useTaskGuide'

const authStore = useAuthStore()
const { isAdmin } = storeToRefs(authStore)

const isSidebarOpen = ref(false)

const { showWelcome, isActive, startExperience, skipExperience, loadProgress } = useTaskGuide()

onMounted(() => {
  if (!isAdmin.value) {
    loadProgress()
  }
})
</script>
