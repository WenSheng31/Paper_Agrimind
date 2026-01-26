<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="modal-backdrop z-50 flex items-center justify-center"
      @click.self="$emit('close')"
    >
      <div class="m-4 w-full max-w-md rounded bg-white p-6 dark:bg-slate-800">
        <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">編輯農場</h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">農場名稱</label>
            <input
              v-model="formData.name"
              type="text"
              required
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">位置</label>
            <input
              v-model="formData.location"
              type="text"
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">描述</label>
            <textarea
              v-model="formData.description"
              rows="3"
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            ></textarea>
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
                hover:bg-emerald-700 disabled:opacity-50"
            >
              {{ submitting ? '儲存中...' : '儲存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  submitting: Boolean,
  initialData: Object,
})

const emit = defineEmits(['close', 'submit'])

const formData = ref({
  name: '',
  location: '',
  description: '',
})

watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      formData.value = { ...newData }
    }
  },
  { immediate: true },
)

function handleSubmit() {
  emit('submit', formData.value)
}
</script>
