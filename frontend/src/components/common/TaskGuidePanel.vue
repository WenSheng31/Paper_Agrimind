<template>
  <div>
    <!-- 進度條 -->
    <div class="mb-3 flex items-center justify-between">
      <span class="text-sm font-medium text-blue-700 dark:text-blue-300">{{ progress }}</span>
      <div class="ml-3 h-2 flex-1 rounded-full bg-blue-200 dark:bg-blue-800">
        <div
          class="h-2 rounded-full bg-blue-600 transition-all duration-300"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
    </div>

    <!-- 完成狀態 -->
    <div v-if="isCompleted" class="text-center">
      <h4 class="mb-2 text-lg font-semibold text-slate-800 dark:text-slate-100">
        所有任務已完成！
      </h4>
      <p class="mb-4 text-base text-slate-500 dark:text-slate-400">
        感謝你的參與，請點擊下方連結填寫問卷。
      </p>
      <div class="flex items-center gap-2">
        <a
          :href="questionnaireUrl"
          target="_blank"
          class="flex flex-1 items-center justify-center gap-2 rounded bg-blue-600 px-4 py-2.5
            text-base font-medium text-white transition hover:bg-blue-700"
        >
          <ExternalLink :size="16" />
          填寫問卷
        </a>
        <button
          @click="endExperience"
          class="cursor-pointer rounded border border-slate-200 px-3 py-2.5 text-base
            text-slate-600 transition hover:bg-slate-50 dark:border-slate-700
            dark:text-slate-400 dark:hover:bg-slate-800"
        >
          關閉
        </button>
      </div>
    </div>

    <!-- 當前任務 -->
    <div v-else-if="currentTask">
      <h4 class="mb-1 text-base font-semibold text-slate-800 dark:text-white">
        {{ currentTask.title }}
      </h4>
      <p class="mb-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        {{ currentTask.description }}
      </p>

      <!-- 頁面快捷連結 -->
      <router-link
        v-if="currentTask.route"
        :to="currentTask.route"
        class="mb-3 flex w-full cursor-pointer items-center justify-center gap-2 rounded border
          border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-700 transition hover:bg-blue-100
          dark:border-blue-800 dark:bg-blue-950 dark:text-blue-300 dark:hover:bg-blue-900"
      >
        點我{{ currentTask.routeLabel }}
      </router-link>

      <!-- 快捷詢問 AI -->
      <button
        v-if="currentTask.question"
        @click="askAi(currentTask.question)"
        class="mb-3 flex w-full cursor-pointer items-center gap-2 rounded border border-blue-200
          bg-blue-50 px-3 py-2 text-left text-sm text-blue-700 transition hover:bg-blue-100
          dark:border-blue-800 dark:bg-blue-950 dark:text-blue-300 dark:hover:bg-blue-900"
      >
        <Bot :size="16" class="shrink-0" />
        點我詢問：{{ currentTask.question }}
      </button>

      <!-- 完成按鈕 -->
      <button
        @click="completeCurrentTask"
        :disabled="!fulfilled"
        class="flex w-full cursor-pointer items-center justify-center gap-2 rounded bg-blue-600
          px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700
          active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Check :size="16" />
        完成此任務
      </button>
    </div>
  </div>
</template>

<script setup>
import { useTaskGuide, QUESTIONNAIRE_URL } from '@/composables/useTaskGuide'
import { Check, ExternalLink, Bot } from 'lucide-vue-next'

const {
  currentTask,
  currentStep,
  isCompleted,
  progress,
  progressPercent,
  fulfilled,
  completeCurrentTask,
  endExperience,
} = useTaskGuide()

const questionnaireUrl = QUESTIONNAIRE_URL

function askAi(question) {
  window.dispatchEvent(new CustomEvent('task-ask-ai', { detail: { question } }))
}
</script>
