<template>
  <transition name="fade">
    <div
      v-if="user"
      class="modal-backdrop z-50 flex items-center justify-center"
      @click.self="$emit('close')"
    >
      <div class="m-4 w-full max-w-md overflow-hidden rounded bg-white dark:bg-slate-800">
        <!-- 頂部彩色區域 -->
        <div class="relative bg-emerald-600 px-6 pt-6 pb-10 dark:bg-emerald-700">
          <button
            @click="$emit('close')"
            class="absolute top-3 right-3 cursor-pointer rounded p-1 text-emerald-200 transition
              hover:text-white"
          >
            <X :size="20" />
          </button>
          <div class="text-lg font-bold text-white">{{ user.username }}</div>
          <div class="text-sm text-emerald-100">{{ user.email }}</div>
        </div>

        <!-- 頭像（跨區域） -->
        <div class="relative -mt-7 px-6">
          <div
            class="flex h-14 w-14 items-center justify-center rounded-full border-4 border-white
              bg-slate-700 dark:border-slate-800 dark:bg-slate-600"
          >
            <span class="text-xl font-bold text-white">
              {{ user.username?.charAt(0).toUpperCase() }}
            </span>
          </div>
        </div>

        <!-- 內容 -->
        <div class="px-6 pt-3 pb-6">
          <!-- 標籤列 -->
          <div class="mb-4 flex flex-wrap gap-2">
            <span
              :class="
                user.is_admin
                  ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
              "
              class="rounded-full px-2.5 py-0.5 text-sm font-medium"
            >
              {{ user.is_admin ? '管理員' : '一般用戶' }}
            </span>
            <span
              :class="
                user.is_active
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                  : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              "
              class="rounded-full px-2.5 py-0.5 text-sm font-medium"
            >
              {{ user.is_active ? '啟用中' : '已停用' }}
            </span>
            <span
              v-if="taskStatus"
              :class="
                taskStatus.is_completed
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
              "
              class="rounded-full px-2.5 py-0.5 text-sm font-medium"
            >
              {{
                taskStatus.is_completed
                  ? '任務已完成'
                  : `任務 ${taskStatus.current_step}/${TOTAL_TASKS}`
              }}
            </span>
          </div>

          <!-- 資訊列 -->
          <div
            class="mb-5 space-y-2.5 border-t border-slate-100 pt-4 text-sm dark:border-slate-700"
          >
            <div class="flex items-center gap-3 text-slate-600 dark:text-slate-400">
              <Calendar :size="16" class="shrink-0 text-slate-400 dark:text-slate-500" />
              建立於 {{ formatDate(user.created_at) }}
            </div>
            <div
              v-if="taskStatus?.is_completed && taskStatus?.completed_at"
              class="flex items-center gap-3 text-slate-600 dark:text-slate-400"
            >
              <CheckCircle :size="16" class="shrink-0 text-blue-500" />
              任務完成於 {{ formatDate(taskStatus.completed_at) }}
            </div>
          </div>

          <!-- 操作按鈕 -->
          <div v-if="!isSelf" class="space-y-2">
            <div class="flex gap-2">
              <button
                @click="$emit('toggle-admin', user)"
                class="flex flex-1 cursor-pointer items-center justify-center gap-1.5 rounded
                  border border-slate-200 py-2 text-sm text-slate-700 transition hover:bg-slate-50
                  dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                <ShieldCheck v-if="user.is_admin" :size="15" />
                <Shield v-else :size="15" />
                {{ user.is_admin ? '降級' : '升級管理員' }}
              </button>
              <button
                @click="$emit('toggle-active', user)"
                class="flex flex-1 cursor-pointer items-center justify-center gap-1.5 rounded
                  border border-slate-200 py-2 text-sm text-slate-700 transition hover:bg-slate-50
                  dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                <UserX v-if="user.is_active" :size="15" />
                <UserCheck v-else :size="15" />
                {{ user.is_active ? '停用' : '啟用' }}
              </button>
            </div>
            <div v-if="taskStatus" class="flex gap-2">
              <button
                @click="$emit('reset-task', user)"
                class="flex flex-1 cursor-pointer items-center justify-center gap-1.5 rounded
                  border border-slate-200 py-2 text-sm text-slate-700 transition hover:bg-slate-50
                  dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                <RotateCcw :size="15" />
                重置任務
              </button>
            </div>
            <button
              @click="$emit('delete', user)"
              class="flex w-full cursor-pointer items-center justify-center gap-1.5 rounded py-2
                text-sm text-red-600 transition hover:bg-red-50 dark:text-red-400
                dark:hover:bg-red-900/20"
            >
              <Trash2 :size="15" />
              刪除帳號
            </button>
          </div>
          <div v-else class="text-center text-sm text-slate-400 dark:text-slate-500">
            目前登入帳號
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import {
  X,
  Shield,
  ShieldCheck,
  UserX,
  UserCheck,

  Trash2,
  RotateCcw,
  Calendar,
  CheckCircle,
} from 'lucide-vue-next'
import { TOTAL_TASKS } from '@/composables/useTaskGuide'

defineProps({
  user: { type: Object, default: null },
  taskStatus: { type: Object, default: null },
  isSelf: { type: Boolean, default: false },
})

defineEmits(['close', 'toggle-admin', 'toggle-active', 'reset-task', 'delete'])

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('zh-TW')
}
</script>
