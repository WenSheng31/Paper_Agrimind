<template>
  <div class="relative overflow-hidden" :class="containerClass">
    <!-- 載入中 -->
    <div v-if="status === 'loading'" class="absolute inset-0 flex items-center justify-center bg-slate-100 dark:bg-slate-700">
      <div class="animate-spin rounded-full border-t-emerald-500" :class="spinnerClass"></div>
    </div>
    <!-- 載入失敗 -->
    <div v-if="status === 'error'" class="absolute inset-0 flex flex-col items-center justify-center gap-1 bg-slate-100 dark:bg-slate-700 text-slate-400">
      <ImageOff :size="errorIconSize" />
      <span v-if="showErrorText" class="text-base">圖片無法載入</span>
    </div>
    <!-- 圖片（用 opacity 控制顯示，不用 v-show/display:none，避免 lazy loading 失效） -->
    <img
      :src="src"
      :alt="alt"
      :class="[imgClass, status === 'loaded' ? 'opacity-100' : 'opacity-0']"
      class="transition-opacity duration-200"
      loading="lazy"
      @load="status = 'loaded'"
      @error="status = 'error'"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ImageOff } from 'lucide-vue-next'

const props = defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: '' },
  containerClass: { type: String, default: '' },
  imgClass: { type: String, default: 'h-full w-full object-cover' },
  spinnerClass: { type: String, default: 'h-6 w-6 border-3 border-slate-300' },
  errorIconSize: { type: Number, default: 24 },
  showErrorText: { type: Boolean, default: false },
})

const status = ref('loading')

watch(() => props.src, () => {
  status.value = 'loading'
})
</script>
