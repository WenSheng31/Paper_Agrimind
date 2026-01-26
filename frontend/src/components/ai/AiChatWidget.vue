<template>
  <div>
    <!-- 圓形懸浮按鈕 -->
    <transition name="fab">
      <button
        v-if="!isOpen"
        @click="isOpen = true"
        class="fixed right-4 bottom-4 z-50 flex h-16 w-16 cursor-pointer items-center justify-center
          rounded-full bg-emerald-600 text-white shadow-lg transition-transform duration-75
          select-none hover:bg-emerald-700 active:scale-90 sm:right-6 sm:bottom-6"
      >
        <Bot :size="32" />
      </button>
    </transition>

    <!-- 聊天視窗 -->
    <transition name="chat">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex h-[100dvh] flex-col overflow-hidden border-slate-200 bg-white
          md:inset-auto md:right-6 md:bottom-6 md:h-[750px] md:max-h-[90vh] md:w-[500px]
          md:rounded-lg md:border dark:border-slate-700 dark:bg-slate-900"
      >
        <!-- 標題列 -->
        <div
          class="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white p-4
            select-none dark:border-slate-700 dark:bg-slate-900"
        >
          <Bot :size="24" class="text-emerald-600 dark:text-emerald-400" />
          <button
            @click="isOpen = false"
            class="cursor-pointer rounded p-1 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          >
            <X :size="24" />
          </button>
        </div>

        <!-- 訊息顯示區 -->
        <TransitionGroup
          name="message"
          tag="div"
          ref="messagesContainer"
          class="flex-1 space-y-4 overflow-y-auto overscroll-contain bg-slate-50 p-4 dark:bg-slate-950"
        >
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <div
              :class="[
                'max-w-[85%] rounded p-4 text-base font-normal',
                msg.role === 'user'
                  ? 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100'
                  : 'border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200',
              ]"
            >
              <div
                v-html="renderMarkdown(msg.content)"
                class="prose prose-sm prose-p:leading-relaxed prose-p:first:mt-0 prose-p:last:mb-0
                  prose-pre:my-2 max-w-none dark:prose-invert"
              ></div>
              <!-- 顯示工具呼叫 -->
              <div
                v-if="msg.tool_calls && msg.tool_calls.length > 0"
                class="mt-3 space-y-2 border-t border-slate-200/50 pt-3 dark:border-slate-700"
              >
                <div
                  v-for="(tool, idx) in msg.tool_calls"
                  :key="`${msg.id}-${tool.name}-${idx}`"
                  class="overflow-hidden rounded border border-slate-200/50 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-900/50"
                >
                  <!-- 工具標頭 (點擊展開) -->
                  <button
                    @click="toggleToolDetails(msg.id, idx)"
                    class="flex w-full cursor-pointer items-center gap-2 p-2 text-left select-none
                      hover:bg-slate-100/50 dark:hover:bg-slate-800/50"
                  >
                    <div class="flex-1 truncate text-sm font-medium text-emerald-600 dark:text-emerald-400">
                      {{ tool.name }}
                    </div>
                  </button>

                  <!-- 詳細資訊 -->
                  <div v-if="expandedTools[`${msg.id}-${idx}`]" class="space-y-2 px-2 pt-0 pb-2">
                    <!-- 輸入參數 -->
                    <div>
                      <div class="mb-1 text-xs font-semibold text-slate-600 dark:text-slate-400">輸入參數:</div>
                      <div
                        class="overflow-x-auto rounded border border-slate-100 bg-white p-2
                          font-mono text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400"
                      >
                        <pre class="whitespace-pre-wrap">{{
                          JSON.stringify(tool.input, null, 2)
                        }}</pre>
                      </div>
                    </div>

                    <!-- 返回值 -->
                    <div v-if="tool.output">
                      <div class="mb-1 text-xs font-semibold text-slate-600 dark:text-slate-400">返回值:</div>
                      <div
                        class="max-h-60 overflow-x-auto overflow-y-auto rounded border
                          border-slate-100 bg-white p-2 font-mono text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400"
                      >
                        <pre class="whitespace-pre-wrap">{{ formatToolOutput(tool.output) }}</pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading 指示器 -->
          <transition name="message" key="loading">
            <div v-if="loading" class="flex justify-start px-4 py-2">
              <div class="flex gap-1.5">
                <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 dark:bg-slate-600"></span>
                <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 dark:bg-slate-600 delay-100"></span>
                <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 dark:bg-slate-600 delay-200"></span>
              </div>
            </div>
          </transition>
        </TransitionGroup>

        <!-- 輸入區 -->
        <div class="shrink-0 bg-slate-50 p-4 dark:bg-slate-900">
          <form @submit.prevent="sendMessage">
            <input
              ref="inputField"
              v-model="inputMessage"
              type="text"
              placeholder="輸入訊息並按 Enter 發送..."
              :disabled="loading"
              class="w-full rounded border border-slate-200 px-4 py-3 text-base focus:outline-none
                disabled:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:disabled:bg-slate-900"
            />
          </form>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { aiAPI } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { useMarkdown } from '@/composables/useMarkdown'
import { X, Bot } from 'lucide-vue-next'

const { showToast } = useToast()
const { render: renderMarkdown } = useMarkdown()

const isOpen = ref(false)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const inputField = ref(null)
const expandedTools = ref({})

// 每次頁面刷新生成新的 session ID
const sessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
let messageId = 0

const toggleToolDetails = (msgId, toolIndex) => {
  const key = `${msgId}-${toolIndex}`
  if (expandedTools.value[key]) {
    delete expandedTools.value[key]
  } else {
    expandedTools.value[key] = true
  }
}

// 格式化工具輸出
const formatToolOutput = (output) => {
  if (!output) return ''
  try {
    const parsed = JSON.parse(output)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return output
  }
}

// 鍵盤監聽
const handleKeyDown = (event) => {
  if (event.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

// 監控開啟狀態，自動聚焦
watch(isOpen, async (newVal) => {
  if (newVal) {
    await nextTick()
    setTimeout(() => {
      inputField.value?.focus()
    }, 300)
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

// 發送訊息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({
    id: ++messageId,
    role: 'user',
    content: userMessage,
  })

  await scrollToBottom()
  loading.value = true

  try {
    const response = await aiAPI.chat(userMessage, sessionId)

    messages.value.push({
      id: ++messageId,
      role: 'assistant',
      content: response.content,
      tool_calls: response.tool_calls,
    })

    await scrollToBottom()
  } catch (err) {
    showToast(err.message || '發送失敗', 'error')
  } finally {
    loading.value = false
  }
}

// 滾動到底部
const scrollToBottom = async () => {
  await nextTick()
  setTimeout(() => {
    if (messagesContainer.value?.$el) {
      const el = messagesContainer.value.$el
      el.scrollTo({
        top: el.scrollHeight,
        behavior: 'smooth',
      })
    } else if (messagesContainer.value) {
      messagesContainer.value.scrollTo({
        top: messagesContainer.value.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, 50)
}
</script>

<style scoped>
/* 懸浮按鈕動畫 */
.fab-enter-active,
.fab-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fab-enter-from,
.fab-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 聊天視窗動畫 */
.chat-enter-active,
.chat-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-enter-from,
.chat-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

@media (max-width: 768px) {
  .chat-enter-from,
  .chat-leave-to {
    transform: translateY(100%) scale(1);
  }
}

/* 訊息彈出動畫 */
.message-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.message-enter-from {
  opacity: 0;
  transform: scale(0.5) translateY(30px);
}
</style>
