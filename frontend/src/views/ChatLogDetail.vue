<template>
  <div class="p-4 sm:p-6">
    <div class="mb-4">
      <button
        @click="$router.push('/chat-logs')"
        class="mb-4 flex cursor-pointer items-center gap-2 text-slate-600 hover:text-slate-800
          dark:text-slate-400 dark:hover:text-slate-200"
      >
        <ChevronLeft :size="20" />
        返回對話紀錄
      </button>

      <!-- 對話資訊 -->
      <div class="rounded border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <h1 class="text-3xl font-bold text-slate-800 dark:text-white">
          {{ firstQuery || '對話詳情' }}
        </h1>
        <p v-if="username" class="mt-2 text-slate-600 dark:text-slate-400">
          使用者：{{ username }}
        </p>
      </div>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <!-- 對話內容 -->
    <div v-else class="space-y-4 rounded bg-slate-50 p-4 dark:bg-slate-950">
      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div
          :class="[
            'max-w-[85%] rounded p-4 text-sm',
            msg.role === 'user'
              ? 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100'
              : 'border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200',
          ]"
        >
          <!-- 角色 + 時間 -->
          <div class="mb-2 flex items-center gap-2 text-xs">
            <span class="font-medium opacity-70">
              {{ msg.role === 'user' ? '使用者' : 'AI 助手' }}
            </span>
            <span class="opacity-50">{{ formatTime(msg.created_at) }}</span>
          </div>
          <!-- 使用者上傳的圖片 -->
          <div v-if="msg.images && msg.images.length > 0" class="mb-2 flex flex-wrap gap-2">
            <img
              v-for="(img, idx) in msg.images"
              :key="idx"
              :src="`data:${img.media_type};base64,${img.data}`"
              class="max-h-40 rounded border border-slate-200 object-contain dark:border-slate-700"
            />
          </div>
          <!-- 訊息內容 -->
          <div
            v-if="msg.role === 'assistant'"
            v-html="renderMarkdown(msg.content)"
            class="prose prose-sm prose-p:leading-relaxed prose-p:first:mt-0 prose-p:last:mb-0
              prose-pre:my-2 max-w-none dark:prose-invert"
          ></div>
          <p v-else class="whitespace-pre-wrap">{{ msg.content }}</p>
          <!-- 工具呼叫 -->
          <div
            v-if="msg.tool_calls && msg.tool_calls.length > 0"
            class="mt-3 space-y-2 border-t border-slate-200/50 pt-3 dark:border-slate-700"
          >
            <div
              v-for="(tc, idx) in msg.tool_calls"
              :key="idx"
              class="overflow-hidden rounded border border-slate-200/50 bg-slate-50/50
                dark:border-slate-700 dark:bg-slate-900/50"
            >
              <button
                @click="toggleTools(msg.id, idx)"
                class="flex w-full cursor-pointer items-center gap-2 p-2 text-left select-none
                  hover:bg-slate-100/50 dark:hover:bg-slate-800/50"
              >
                <div class="flex-1 truncate text-sm font-medium text-emerald-600 dark:text-emerald-400">
                  {{ tc.name }}
                </div>
              </button>
              <div v-if="expandedToolKeys.has(`${msg.id}-${idx}`)" class="space-y-2 px-2 pt-0 pb-2">
                <div>
                  <div class="mb-1 text-xs font-semibold text-slate-600 dark:text-slate-400">輸入參數:</div>
                  <div
                    class="overflow-x-auto rounded border border-slate-100 bg-white p-2
                      font-mono text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400"
                  >
                    <pre class="whitespace-pre-wrap">{{ JSON.stringify(tc.args, null, 2) }}</pre>
                  </div>
                </div>
                <div v-if="tc.output">
                  <div class="mb-1 text-xs font-semibold text-slate-600 dark:text-slate-400">返回值:</div>
                  <div
                    class="max-h-60 overflow-x-auto overflow-y-auto rounded border
                      border-slate-100 bg-white p-2 font-mono text-xs text-slate-500
                      dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400"
                  >
                    <pre class="whitespace-pre-wrap">{{ formatToolOutput(tc.output) }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useMarkdown } from '@/composables/useMarkdown'
import api from '@/services/api'
import { ChevronLeft } from 'lucide-vue-next'

const route = useRoute()
const { showToast } = useToast()
const { render: renderMarkdown } = useMarkdown()

const loading = ref(true)
const messages = ref([])
const expandedToolKeys = reactive(new Set())
const firstQuery = ref('')
const username = ref('')

function formatTime(dateString) {
  return new Date(dateString).toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
}

function formatToolOutput(output) {
  if (!output) return ''
  try {
    const parsed = JSON.parse(output)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return output
  }
}

function toggleTools(msgId, idx) {
  const key = `${msgId}-${idx}`
  if (expandedToolKeys.has(key)) {
    expandedToolKeys.delete(key)
  } else {
    expandedToolKeys.add(key)
  }
}

async function loadMessages() {
  loading.value = true
  try {
    const sessionId = route.params.sessionId
    const data = await api.getChatSessionMessages(sessionId)
    messages.value = data
    // 取第一筆 user 訊息作為標題
    const firstUserMsg = data.find((m) => m.role === 'user')
    if (firstUserMsg) {
      firstQuery.value = firstUserMsg.content.slice(0, 50)
      username.value = firstUserMsg.username
    }
  } catch (error) {
    showToast(error.message || '載入對話內容失敗', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMessages()
})
</script>
