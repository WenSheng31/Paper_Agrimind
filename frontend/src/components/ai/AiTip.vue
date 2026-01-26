<template>
  <div ref="container" class="relative">
    <button
      @click="toggle"
      class="cursor-pointer rounded p-1.5 text-emerald-600 transition hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-900/30"
      title="AI 分析"
    >
      <Sparkles :size="18" />
    </button>
    <transition name="pop">
      <div
        v-if="show"
        class="absolute top-10 right-0 z-10 w-80 rounded border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800"
      >
        <div class="p-4">
          <div v-if="loading" class="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
            <Bot :size="20" class="animate-pulse" />
            <span class="text-sm">AI 分析中...</span>
          </div>
          <div v-else-if="content" class="text-sm text-slate-600 dark:text-slate-300">
            <div v-html="renderedContent" class="prose prose-sm max-w-none dark:prose-invert"></div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { aiAPI } from '@/services/api'
import { useMarkdown } from '@/composables/useMarkdown'
import { Sparkles, Bot } from 'lucide-vue-next'

const props = defineProps({
  prompt: { type: String, required: true },
})

const { render } = useMarkdown()
const loading = ref(false)
const content = ref('')
const show = ref(false)
const container = ref(null)

const renderedContent = computed(() => render(content.value))

async function toggle() {
  show.value = !show.value
  if (show.value) {
    loading.value = true
    content.value = ''
    try {
      content.value = await aiAPI.ask(props.prompt)
    } catch (err) {
      content.value = err.message || '分析失敗，請稍後再試'
    } finally {
      loading.value = false
    }
  }
}

function handleClickOutside(e) {
  if (container.value && !container.value.contains(e.target)) {
    show.value = false
    content.value = ''
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.pop-enter-active,
.pop-leave-active {
  transition: all 0.2s ease-out;
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
