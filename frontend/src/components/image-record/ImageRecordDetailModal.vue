<template>
  <transition name="fade">
    <div
      v-if="recordId !== null"
      class="modal-backdrop z-50 flex items-center justify-center"
      @click.self="$emit('close')"
    >
      <div class="m-4 flex max-h-[90vh] w-full max-w-2xl flex-col rounded bg-white dark:bg-slate-800">
        <!-- Loading -->
        <div v-if="loading" class="p-8 text-center text-slate-500 dark:text-slate-400">載入中...</div>

        <template v-else-if="record">
          <!-- Header -->
          <div class="flex items-center justify-between border-b border-slate-200 p-4 dark:border-slate-700">
            <div>
              <h2 class="text-xl font-bold text-slate-800 dark:text-white">影像紀錄詳情</h2>
              <div class="mt-1 flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <span class="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700
                  dark:bg-emerald-900/30 dark:text-emerald-400">
                  {{ record.farm_name }}
                </span>
                <span>{{ formatDate(record.created_at) }}</span>
              </div>
            </div>
            <button
              @click="$emit('close')"
              class="cursor-pointer text-slate-400 transition hover:text-slate-600 dark:hover:text-slate-300"
            >
              <X :size="24" />
            </button>
          </div>

          <!-- 內容 -->
          <div class="flex-1 overflow-y-auto p-4">
            <!-- 圖片展示 -->
            <div class="mb-4">
              <SafeImage
                :key="currentImage.id"
                :src="getImageUrl(currentImage.filename, record.id)"
                :alt="currentImage.original_filename"
                container-class="mb-2 rounded-lg min-h-40 bg-slate-100 dark:bg-slate-700"
                img-class="mx-auto max-h-80 object-contain"
                spinner-class="h-8 w-8 border-4 border-slate-300"
                :error-icon-size="40"
                :show-error-text="true"
              />
              <div class="flex flex-wrap items-center gap-2">
                <div v-for="(img, i) in record.images" :key="img.id" class="group relative">
                  <button
                    @click="currentImageIndex = i"
                    :class="[
                      'h-16 w-16 cursor-pointer overflow-hidden rounded border-2 transition',
                      currentImageIndex === i
                        ? 'border-emerald-500'
                        : 'border-transparent opacity-60 hover:opacity-100',
                    ]"
                  >
                    <SafeImage
                      :src="getImageUrl(img.filename, record.id)"
                      container-class="h-full w-full"
                      spinner-class="h-4 w-4 border-2 border-slate-300"
                      :error-icon-size="16"
                    />
                  </button>
                  <button
                    v-if="isAdmin && record.images.length > 1"
                    @click="removeImage(img.id)"
                    class="absolute -top-1 -right-1 flex h-5 w-5 cursor-pointer items-center justify-center
                      rounded-full bg-red-500 text-xs text-white opacity-0 transition group-hover:opacity-100"
                  >
                    &times;
                  </button>
                </div>
                <button
                  v-if="isAdmin && record.images.length < 5"
                  @click="$refs.addFileInput.click()"
                  class="flex h-16 w-16 cursor-pointer items-center justify-center rounded border-2
                    border-dashed border-slate-300 text-slate-400 transition hover:border-emerald-500
                    hover:text-emerald-500 dark:border-slate-600"
                >
                  <Plus :size="24" />
                </button>
                <input
                  ref="addFileInput"
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  @change="onAddFiles"
                  class="hidden"
                />
              </div>
            </div>

            <!-- AI 分析 -->
            <div class="mb-4">
              <div v-if="analyzing" class="flex items-center gap-2 text-sm text-slate-400">
                <div class="h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-emerald-500"></div>
                分析中...
              </div>
              <p v-else-if="analysisText" class="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-300">{{ analysisText }}</p>
            </div>

            <!-- 描述 -->
            <div class="mb-4">
              <h3 class="mb-1 text-sm font-medium text-slate-500 dark:text-slate-400">描述</h3>
              <div v-if="!editing">
                <p class="text-slate-700 dark:text-slate-300">{{ record.description || '無描述' }}</p>
              </div>
              <div v-else>
                <textarea
                  v-model="editDescription"
                  rows="2"
                  class="w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-700
                    dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200"
                ></textarea>
                <div class="mt-2 flex gap-2">
                  <button
                    @click="saveDescription"
                    :disabled="saving"
                    class="cursor-pointer rounded bg-emerald-600 px-3 py-1 text-sm text-white
                      hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {{ saving ? '儲存中...' : '儲存' }}
                  </button>
                  <button
                    @click="editing = false"
                    class="cursor-pointer rounded border border-slate-300 px-3 py-1 text-sm text-slate-600
                      hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-700"
                  >
                    取消
                  </button>
                </div>
              </div>
            </div>

          </div>

          <!-- Footer -->
          <div v-if="isAdmin" class="flex gap-2 border-t border-slate-200 p-4 dark:border-slate-700">
            <button
              @click="startEdit"
              class="cursor-pointer rounded border border-slate-300 px-4 py-2 text-sm text-slate-700
                transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              <Pencil :size="16" class="mr-1 inline" />
              編輯描述
            </button>
            <button
              @click="showDeleteConfirm = true"
              class="cursor-pointer rounded border border-red-300 px-4 py-2 text-sm text-red-600
                transition hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20"
            >
              <Trash2 :size="16" class="mr-1 inline" />
              刪除
            </button>
          </div>
        </template>

        <!-- 刪除確認 -->
        <transition name="fade">
          <div
            v-if="showDeleteConfirm"
            class="modal-backdrop z-[60] flex items-center justify-center"
            @click.self="showDeleteConfirm = false"
          >
            <div class="m-4 w-full max-w-sm rounded bg-white p-6 dark:bg-slate-800">
              <h3 class="mb-3 text-lg font-bold text-slate-800 dark:text-white">確認刪除</h3>
              <p class="mb-4 text-sm text-slate-600 dark:text-slate-400">確定要刪除此影像紀錄嗎？此操作無法復原。</p>
              <div class="flex gap-3">
                <button
                  @click="showDeleteConfirm = false"
                  class="flex-1 cursor-pointer rounded border border-slate-300 px-3 py-2 text-sm
                    text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300
                    dark:hover:bg-slate-700"
                >
                  取消
                </button>
                <button
                  @click="confirmDelete"
                  :disabled="deleting"
                  class="flex-1 cursor-pointer rounded bg-red-600 px-3 py-2 text-sm text-white
                    hover:bg-red-700 disabled:opacity-50"
                >
                  {{ deleting ? '刪除中...' : '確認刪除' }}
                </button>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import imageCompression from 'browser-image-compression'
import api from '@/services/api'

const compressionOptions = { maxSizeMB: 1, maxWidthOrHeight: 1920 }
import { X, Pencil, Trash2, Plus } from 'lucide-vue-next'
import SafeImage from '@/components/common/SafeImage.vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const props = defineProps({
  recordId: { type: Number, default: null },
})

const emit = defineEmits(['close', 'updated', 'deleted'])

const authStore = useAuthStore()
const { isAdmin } = storeToRefs(authStore)
const { showToast } = useToast()

const record = ref(null)
const loading = ref(false)
const currentImageIndex = ref(0)
const editing = ref(false)
const editDescription = ref('')
const saving = ref(false)
const showDeleteConfirm = ref(false)
const deleting = ref(false)
const addFileInput = ref(null)

// AI 分析
const analyzing = ref(false)
const analysisText = ref('')
const analysisError = ref('')
const CACHE_KEY = 'image-record-analysis-cache'
function getCache() {
  try { return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}') } catch { return {} }
}
function setCache(id, text) {
  const cache = getCache()
  cache[id] = text
  localStorage.setItem(CACHE_KEY, JSON.stringify(cache))
}
function clearCache(id) {
  const cache = getCache()
  delete cache[id]
  localStorage.setItem(CACHE_KEY, JSON.stringify(cache))
}
async function reAnalyze() {
  const id = record.value?.id
  if (!id) return
  clearCache(id)
  analysisText.value = ''
  analyzing.value = true
  try {
    const res = await api.analyzeImageRecord(id)
    analysisText.value = res.analysis
    setCache(id, res.analysis)
  } catch {
    // silent
  } finally {
    analyzing.value = false
  }
}

const currentImage = computed(() => {
  if (!record.value?.images?.length) return {}
  return record.value.images[currentImageIndex.value] || record.value.images[0]
})

// recordId 變化時拉資料 + 自動分析
watch(() => props.recordId, async (id) => {
  if (id !== null) {
    currentImageIndex.value = 0
    editing.value = false
    showDeleteConfirm.value = false
    analysisText.value = ''
    analysisError.value = ''
    loading.value = true
    try {
      record.value = await api.getImageRecord(id)
    } catch (error) {
      showToast(error.message || '載入失敗', 'error')
      emit('close')
      return
    } finally {
      loading.value = false
    }
    // AI 分析（有快取就用快取）
    const cached = getCache()[id]
    if (cached) {
      analysisText.value = cached
    } else {
      analyzing.value = true
      try {
        const res = await api.analyzeImageRecord(id)
        analysisText.value = res.analysis
        setCache(id, res.analysis)
      } catch (error) {
        analysisError.value = error.message || 'AI 分析失敗'
      } finally {
        analyzing.value = false
      }
    }
  } else {
    record.value = null
  }
})

function getImageUrl(filename, recordId) {
  return `${API_BASE_URL}/uploads/image-records/${recordId}/${filename}`
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('zh-TW')
}

function startEdit() {
  editDescription.value = record.value?.description || ''
  editing.value = true
}

async function saveDescription() {
  saving.value = true
  try {
    record.value = await api.updateImageRecord(record.value.id, { description: editDescription.value })
    showToast('描述已更新')
    editing.value = false
    emit('updated')
  } catch (error) {
    showToast(error.message || '更新失敗', 'error')
  } finally {
    saving.value = false
  }
}

async function onAddFiles(e) {
  const files = Array.from(e.target.files || [])
  if (files.length === 0) return
  e.target.value = ''
  try {
    const compressed = await Promise.all(
      files.map(async f => {
        const blob = await imageCompression(f, compressionOptions)
        return new File([blob], f.name, { type: blob.type })
      })
    )
    record.value = await api.addImageRecordImages(record.value.id, compressed)
    showToast('圖片已新增')
    emit('updated')
    reAnalyze()
  } catch (error) {
    showToast(error.message || '新增圖片失敗', 'error')
  }
}

async function removeImage(imageId) {
  try {
    record.value = await api.deleteImageRecordImage(record.value.id, imageId)
    if (currentImageIndex.value >= record.value.images.length) {
      currentImageIndex.value = record.value.images.length - 1
    }
    showToast('圖片已刪除')
    emit('updated')
    reAnalyze()
  } catch (error) {
    showToast(error.message || '刪除圖片失敗', 'error')
  }
}

async function confirmDelete() {
  deleting.value = true
  try {
    await api.deleteImageRecord(record.value.id)
    showToast('影像紀錄已刪除')
    showDeleteConfirm.value = false
    emit('deleted')
  } catch (error) {
    showToast(error.message || '刪除失敗', 'error')
  } finally {
    deleting.value = false
  }
}
</script>
