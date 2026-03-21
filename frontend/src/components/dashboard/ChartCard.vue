<template>
  <div
    class="rounded border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800"
  >
    <h3 class="mb-3 text-base font-semibold text-slate-700 dark:text-slate-300">
      {{ title }}
    </h3>
    <div class="relative" :style="{ height: height + 'px' }">
      <div
        v-if="loading"
        class="absolute inset-0 flex items-center justify-center"
      >
        <div
          class="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"
        />
      </div>
      <div v-else-if="empty" class="flex h-full items-center justify-center text-base text-slate-400">
        暫無資料
      </div>
      <slot v-else />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  loading: { type: Boolean, default: false },
  empty: { type: Boolean, default: false },
  height: { type: Number, default: 256 },
})
</script>
