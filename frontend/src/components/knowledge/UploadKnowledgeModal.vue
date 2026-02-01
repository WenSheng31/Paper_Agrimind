<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="modal-backdrop z-50 flex items-center justify-center"
      @click.self="$emit('close')"
    >
      <div class="m-4 w-full max-w-lg rounded bg-white p-6 dark:bg-slate-800">
        <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">新增知識</h2>

        <!-- Tab 切換 -->
        <div class="mb-4 flex gap-2">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'cursor-pointer rounded px-4 py-2 text-sm font-medium transition',
              activeTab === tab.key
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600',
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- 標題 -->
          <div>
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">標題</label>
            <input
              v-model="title"
              type="text"
              required
              placeholder="例如：番茄種植指南"
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            />
          </div>

          <!-- 純文字 Tab -->
          <div v-if="activeTab === 'text'">
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">內容</label>
            <textarea
              v-model="content"
              rows="8"
              required
              placeholder="貼上知識文件內容..."
              class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            ></textarea>
          </div>

          <!-- PDF Tab -->
          <div v-if="activeTab === 'pdf'">
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">PDF 檔案</label>
            <input
              type="file"
              accept=".pdf"
              @change="onFileChange"
              class="w-full rounded border border-slate-300 px-3 py-2 text-sm
                dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            />
          </div>

          <!-- 按鈕 -->
          <div class="flex gap-3">
            <button
              type="button"
              @click="$emit('close')"
              class="flex-1 cursor-pointer rounded border border-slate-300 px-4 py-2
                text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 cursor-pointer rounded bg-emerald-600 px-4 py-2 text-white transition
                hover:bg-emerald-700 disabled:opacity-50"
            >
              {{ submitting ? '上傳中...' : '上傳' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'

defineProps({
  isOpen: Boolean,
})

const emit = defineEmits(['close', 'uploaded'])
const { showToast } = useToast()

const tabs = [
  { key: 'text', label: '純文字' },
  { key: 'pdf', label: 'PDF 上傳' },
]

const activeTab = ref('text')
const title = ref('')
const content = ref('')
const pdfFile = ref(null)
const submitting = ref(false)

function onFileChange(e) {
  pdfFile.value = e.target.files[0] || null
}

async function handleSubmit() {
  if (!title.value.trim()) {
    showToast('請輸入標題', 'error')
    return
  }

  submitting.value = true
  try {
    if (activeTab.value === 'text') {
      if (!content.value.trim()) {
        showToast('請輸入內容', 'error')
        return
      }
      await api.uploadKnowledgeText(title.value, content.value)
    } else {
      if (!pdfFile.value) {
        showToast('請選擇 PDF 檔案', 'error')
        return
      }
      await api.uploadKnowledgePdf(title.value, pdfFile.value)
    }
    showToast('知識文件上傳成功')
    emit('uploaded')
    emit('close')
  } catch (error) {
    showToast(error.message || '上傳失敗', 'error')
  } finally {
    submitting.value = false
  }
}
</script>
