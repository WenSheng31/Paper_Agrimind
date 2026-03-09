<template>
  <div
    class="relative flex min-h-35 flex-col justify-center overflow-hidden rounded border
      border-emerald-500 bg-emerald-100 p-6 dark:border-emerald-700 dark:bg-emerald-950"
  >
    <transition name="fade" mode="out-in">
      <!-- 按鈕 -->
      <div v-if="!loading && !content" key="button" class="flex justify-center">
        <button
          @click="generate"
          class="cursor-pointer rounded bg-emerald-600 px-6 py-2 text-white transition
            hover:bg-emerald-700 dark:bg-emerald-700 dark:hover:bg-emerald-600"
        >
          生成 AI 總結
        </button>
      </div>

      <!-- Loading 指示器 -->
      <div
        v-else-if="loading && !content"
        key="loading"
        class="flex animate-pulse flex-col items-center justify-center gap-2"
      >
        <Bot class="text-emerald-600 dark:text-emerald-400" :size="32" />
        <p class="font-medium text-emerald-700 dark:text-emerald-300">AI 正在分析中...</p>
      </div>

      <!-- 回應內容 -->
      <div v-else-if="content" key="content" class="relative">
        <button
          @click="generate"
          class="absolute top-0 right-0 cursor-pointer rounded p-1.5 text-emerald-600 transition
            hover:bg-emerald-100 dark:text-emerald-400 dark:hover:bg-emerald-900"
          title="重新生成"
        >
          <RefreshCw :size="18" />
        </button>
        <div
          v-html="renderedContent"
          class="prose prose-sm prose-p:leading-relaxed prose-p:first:mt-0 prose-p:last:mb-0
            max-w-none pr-10 text-slate-800 dark:text-slate-200 dark:prose-invert"
        ></div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { aiAPI } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { useMarkdown } from '@/composables/useMarkdown'
import { RefreshCw, Bot } from 'lucide-vue-next'

const props = defineProps({
  prompt: { type: String, required: true },
  cacheKey: { type: String, default: '' },
})

const { showToast } = useToast()
const { render } = useMarkdown()
const loading = ref(false)
const content = ref('')

const renderedContent = computed(() => render(content.value))

async function generate() {
  loading.value = true
  content.value = ''
  const tempSessionId = `summary-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  try {
    await aiAPI.chatStream(props.prompt, tempSessionId, {
      onTextDelta(data) {
        content.value += data.content
      },
      onDone() {
        if (props.cacheKey) localStorage.setItem(props.cacheKey, content.value)
      },
      onError(data) {
        showToast(data.message || '生成 AI 總結失敗', 'error')
      },
    })
  } catch (err) {
    showToast(err.message || '生成 AI 總結失敗', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.cacheKey) {
    const cached = localStorage.getItem(props.cacheKey)
    if (cached) content.value = cached
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
