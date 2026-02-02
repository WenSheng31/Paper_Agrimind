<template>
  <div>
    <h2 class="mb-3 text-lg font-semibold text-slate-800 dark:text-white">快速導航</h2>

    <p v-if="!farms.length" class="text-sm text-slate-500 dark:text-slate-400">
      尚無農場資料
    </p>

    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <div
        v-for="farm in farms"
        :key="farm.id"
        class="flex cursor-pointer items-center justify-between rounded border border-slate-200
          bg-white p-4 transition hover:border-emerald-500 dark:border-slate-700 dark:bg-slate-800
          dark:hover:border-emerald-400"
        @click="$router.push(`/farms/${farm.id}`)"
      >
        <div class="flex items-center gap-3">
          <div class="rounded-full bg-emerald-100 p-2 dark:bg-emerald-900/30">
            <Sprout :size="20" class="text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h3 class="font-bold text-slate-800 dark:text-white">{{ farm.name }}</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400">
              {{ farm.location || '未設定位置' }}
            </p>
          </div>
        </div>
        <ArrowRight :size="20" class="text-slate-400 dark:text-slate-500" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Sprout, ArrowRight } from 'lucide-vue-next'

defineProps({
  farms: { type: Array, default: () => [] },
})
</script>
