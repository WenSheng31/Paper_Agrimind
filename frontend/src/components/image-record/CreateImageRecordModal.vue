<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="modal-backdrop z-50 flex items-center justify-center"
      @click.self="$emit('close')"
    >
      <div class="m-4 w-full max-w-lg rounded bg-white p-6 dark:bg-slate-800">
        <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">新增影像紀錄</h2>

        <form @submit.prevent="handleSubmit">
          <!-- 農場選擇 -->
          <div class="mb-4">
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">農場 *</label>
            <select
              v-model="farmId"
              required
              class="w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-700
                dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            >
              <option value="" disabled>請選擇農場</option>
              <option v-for="farm in farms" :key="farm.id" :value="farm.id">{{ farm.name }}</option>
            </select>
          </div>

          <!-- 描述 -->
          <div class="mb-4">
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">描述（選填）</label>
            <textarea
              v-model="description"
              rows="2"
              placeholder="例如：稻田第二期插秧後第三週"
              class="w-full rounded border border-slate-300 px-3 py-2 text-slate-700
                dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            ></textarea>
          </div>

          <!-- 圖片上傳 -->
          <div class="mb-4">
            <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              圖片 *（最多 5 張，每張最大 5MB）
            </label>
            <input
              ref="fileInput"
              type="file"
              multiple
              accept="image/jpeg,image/png,image/gif,image/webp"
              @change="onFilesSelected"
              class="hidden"
            />
            <button
              type="button"
              @click="$refs.fileInput.click()"
              :disabled="previews.length >= 5"
              class="w-full cursor-pointer rounded border-2 border-dashed border-slate-300 px-4 py-6
                text-sm text-slate-500 transition hover:border-emerald-500 hover:text-emerald-600
                disabled:cursor-not-allowed disabled:opacity-50
                dark:border-slate-600 dark:text-slate-400 dark:hover:border-emerald-500"
            >
              點擊選擇圖片（{{ previews.length }}/5）
            </button>

            <!-- 預覽 -->
            <div v-if="previews.length > 0" class="mt-3 flex flex-wrap gap-2">
              <div v-for="(p, i) in previews" :key="i" class="group relative">
                <img :src="p.url" class="h-20 w-20 rounded object-cover" />
                <button
                  type="button"
                  @click="removeFile(i)"
                  class="absolute -top-1 -right-1 flex h-5 w-5 cursor-pointer items-center justify-center
                    rounded-full bg-red-500 text-xs text-white opacity-0 transition group-hover:opacity-100"
                >
                  &times;
                </button>
                <div class="mt-0.5 text-center text-[10px] text-slate-400">
                  {{ (p.file.size / 1024).toFixed(0) }}KB
                </div>
              </div>
            </div>
          </div>

          <!-- 按鈕 -->
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
              :disabled="submitting || !farmId || previews.length === 0"
              class="flex-1 cursor-pointer rounded bg-emerald-600 px-4 py-2 text-white transition
                hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
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
import { ref, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import imageCompression from 'browser-image-compression'
import api from '@/services/api'

const compressionOptions = { maxSizeMB: 1, maxWidthOrHeight: 1920 }

const props = defineProps({
  isOpen: Boolean,
  farms: { type: Array, default: () => [] },
  defaultFarmId: { type: Number, default: null },
})

const emit = defineEmits(['close', 'created'])
const { showToast } = useToast()

const farmId = ref('')
const description = ref('')
const previews = ref([])
const submitting = ref(false)
const fileInput = ref(null)

watch(() => props.isOpen, (val) => {
  if (val) {
    farmId.value = props.defaultFarmId || ''
  } else {
    farmId.value = ''
    description.value = ''
    previews.value.forEach(p => URL.revokeObjectURL(p.url))
    previews.value = []
  }
})

async function onFilesSelected(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  for (const file of files) {
    if (previews.value.length >= 5) break
    try {
      const blob = await imageCompression(file, compressionOptions)
      const compressed = new File([blob], file.name, { type: blob.type })
      previews.value.push({ file: compressed, url: URL.createObjectURL(compressed) })
    } catch {
      showToast(`${file.name} 壓縮失敗`, 'error')
    }
  }
}

function removeFile(index) {
  URL.revokeObjectURL(previews.value[index].url)
  previews.value.splice(index, 1)
}

async function handleSubmit() {
  if (!farmId.value || previews.value.length === 0) return
  submitting.value = true
  try {
    const files = previews.value.map(p => p.file)
    await api.createImageRecord(farmId.value, description.value || null, files)
    showToast('影像紀錄已建立')
    emit('created')
    emit('close')
  } catch (error) {
    showToast(error.message || '上傳失敗', 'error')
  } finally {
    submitting.value = false
  }
}
</script>
