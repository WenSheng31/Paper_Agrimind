<template>
  <div>
    <!-- 圓形懸浮按鈕 + 提示框 -->
    <transition name="fab">
      <div v-if="!isOpen" class="fixed right-4 bottom-4 z-50 sm:right-6 sm:bottom-6">
        <!-- 提示框 -->
        <transition name="tooltip">
          <div
            v-if="showTooltip"
            class="absolute bottom-20 right-0 w-48 rounded-lg border border-slate-200 bg-white
              p-3 text-sm text-slate-700 shadow-lg dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
          >
            <button
              @click="dismissTooltip"
              class="absolute top-1 right-1 cursor-pointer p-1 text-slate-400 hover:text-slate-600
                dark:hover:text-slate-200"
            >
              <X :size="14" />
            </button>
            <p>有任何農業問題？<br>點我開啟 AI 助手聊天！</p>
            <!-- 小三角箭頭 -->
            <div
              class="absolute -bottom-2 right-6 h-4 w-4 rotate-45 border-r border-b
                border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800"
            ></div>
          </div>
        </transition>

        <button
          @click="isOpen = true"
          class="flex h-16 w-16 cursor-pointer items-center justify-center rounded-full
            bg-emerald-600 text-white shadow-lg transition-transform duration-75 select-none
            hover:bg-emerald-700 active:scale-90"
        >
          <Bot :size="32" />
        </button>
      </div>
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
          <!-- 問題範例（無訊息時顯示） -->
          <div v-if="messages.length === 0 && !loading" key="suggestions" class="flex h-full flex-col items-center justify-center gap-4">
            <Bot :size="40" class="text-slate-300 dark:text-slate-600" />
            <p class="text-sm text-slate-500 dark:text-slate-400">試試問我這些問題：</p>
            <div class="flex w-full flex-col gap-2">
              <button
                v-for="(q, i) in suggestedQuestions"
                :key="i"
                @click="sendSuggestion(q)"
                class="w-full cursor-pointer rounded border border-slate-200 bg-white px-4 py-3
                  text-left text-sm text-slate-700 transition hover:border-emerald-400 hover:bg-emerald-50
                  dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300
                  dark:hover:border-emerald-500 dark:hover:bg-emerald-900/20"
              >
                {{ q }}
              </button>
            </div>
          </div>

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
          <form @submit.prevent="sendMessage" class="flex items-center gap-2">
            <input
              ref="inputField"
              v-model="inputMessage"
              type="text"
              placeholder="輸入訊息並按 Enter 發送..."
              :disabled="loading"
              class="min-w-0 flex-1 rounded border border-slate-200 px-4 py-3 text-base focus:outline-none
                disabled:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:disabled:bg-slate-900"
            />
            <button
              v-if="speechSupported"
              type="button"
              @click="toggleListening"
              :disabled="loading"
              :class="[
                'flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center rounded-full transition',
                isListening
                  ? 'animate-pulse bg-red-500 text-white'
                  : 'bg-slate-200 text-slate-600 hover:bg-emerald-100 hover:text-emerald-600 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-emerald-900 dark:hover:text-emerald-400',
              ]"
            >
              <Mic v-if="!isListening" :size="20" />
              <MicOff v-else :size="20" />
            </button>
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
import { X, Bot, Mic, MicOff } from 'lucide-vue-next'

const { showToast } = useToast()
const { render: renderMarkdown } = useMarkdown()

const isOpen = ref(false)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const inputField = ref(null)
const expandedTools = ref({})
const showTooltip = ref(false)

// 語音輸入
const isListening = ref(false)
const speechSupported = ref(false)
let recognition = null

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
if (SpeechRecognition) {
  speechSupported.value = true
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-TW'
  recognition.interimResults = true
  recognition.continuous = false

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map((r) => r[0].transcript)
      .join('')
    inputMessage.value = transcript
  }

  recognition.onend = () => {
    isListening.value = false
  }

  recognition.onerror = () => {
    isListening.value = false
  }
}

const toggleListening = () => {
  if (!recognition) return
  if (isListening.value) {
    recognition.stop()
  } else {
    recognition.start()
    isListening.value = true
  }
}

setTimeout(() => {
  showTooltip.value = true
}, 3000)

const dismissTooltip = () => {
  showTooltip.value = false
}

const suggestedQuestions = [
  '我的農場最近感測數據如何？',
  '幫我查詢今天的天氣',
  '最近有哪些農務操作記錄？',
  '有什麼病蟲害防治的建議嗎？',
]

const sendSuggestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

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
    showTooltip.value = false
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
  if (recognition && isListening.value) recognition.stop()
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
    await nextTick()
    inputField.value?.focus()
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

/* 提示框動畫 */
.tooltip-enter-active,
.tooltip-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateY(8px);
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
