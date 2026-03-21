<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="modal-backdrop z-50 flex items-center justify-center overflow-y-auto"
      @click.self="$emit('close')"
    >
      <div class="m-4 w-full max-w-md rounded bg-white p-6 dark:bg-slate-800">
        <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">新增感測器數據</h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">環境溫度 (°C)</label>
              <input
                v-model.number="formData.temperature"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">環境濕度 (%)</label>
              <input
                v-model.number="formData.humidity"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">降水量 (mm)</label>
              <input
                v-model.number="formData.precipitation"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">日照時數 (hr)</label>
              <input
                v-model.number="formData.sunshine_hours"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">土壤濕度 (%)</label>
              <input
                v-model.number="formData.soil_moisture"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">土壤氮 (mg/kg)</label>
              <input
                v-model.number="formData.soil_n"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">土壤磷 (mg/kg)</label>
              <input
                v-model.number="formData.soil_p"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">土壤鉀 (mg/kg)</label>
              <input
                v-model.number="formData.soil_k"
                type="number"
                step="0.1"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
          </div>
          <div class="flex gap-3">
            <button
              type="button"
              @click="$emit('close')"
              class="flex-1 cursor-pointer rounded border border-slate-300 px-4 py-2 text-slate-700
                transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 cursor-pointer rounded bg-emerald-600 px-4 py-2 text-white transition
                hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {{ submitting ? '新增中...' : '新增' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  submitting: Boolean,
})

const emit = defineEmits(['close', 'submit'])

const formData = ref({
  temperature: null,
  humidity: null,
  precipitation: null,
  sunshine_hours: null,
  soil_moisture: null,
  soil_n: null,
  soil_p: null,
  soil_k: null,
})

function handleSubmit() {
  const hasValue = Object.values(formData.value).some(v => v !== null && v !== '')
  if (!hasValue) return
  emit('submit', formData.value)
  formData.value = {
    temperature: null,
    humidity: null,
    precipitation: null,
    sunshine_hours: null,
    soil_moisture: null,
    soil_n: null,
    soil_p: null,
    soil_k: null,
  }
}
</script>