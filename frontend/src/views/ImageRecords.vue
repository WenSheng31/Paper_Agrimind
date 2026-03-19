<template>
  <div class="p-4 sm:p-6">
    <!-- 標題列 -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-3xl font-bold text-slate-800 dark:text-white">影像紀錄</h1>
      <div id="image-records-filter" class="flex items-center gap-3">
        <select
          v-model="selectedFarmId"
          @change="onFilterChange"
          class="rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700
            dark:border-slate-600 dark:bg-slate-950 dark:text-slate-300"
        >
          <option :value="null">所有農場</option>
          <option v-for="farm in farms" :key="farm.id" :value="farm.id">{{ farm.name }}</option>
        </select>
        <button
          v-if="isAdmin"
          @click="showCreateModal = true"
          class="flex cursor-pointer items-center gap-2 rounded bg-emerald-600 px-4 py-2 text-white
            transition hover:bg-emerald-700"
        >
          <Plus :size="20" />
          新增紀錄
        </button>
      </div>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <!-- 空狀態 -->
    <div v-else-if="records.length === 0" class="py-12 text-center">
      <Camera :size="64" class="mx-auto mb-4 text-slate-400 dark:text-slate-500" />
      <p class="text-slate-600 dark:text-slate-400">尚無影像紀錄</p>
    </div>

    <!-- 卡片 Grid -->
    <div id="image-records-grid" v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <div
        v-for="record in records"
        :key="record.id"
        @click="openDetail(record.id)"
        class="cursor-pointer overflow-hidden rounded border border-slate-200 bg-white transition
          hover:border-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-emerald-400"
      >
        <!-- 縮圖 -->
        <div class="aspect-video">
          <SafeImage
            v-if="record.images.length > 0"
            :src="getImageUrl(record.images[0].filename, record.id)"
            :alt="record.description || '影像紀錄'"
            container-class="h-full"
          />
          <div v-else class="flex h-full items-center justify-center bg-slate-100 dark:bg-slate-700">
            <ImageIcon :size="40" class="text-slate-400" />
          </div>
        </div>
        <!-- 資訊 -->
        <div class="p-4">
          <div class="mb-2 flex items-center gap-2">
            <span class="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700
              dark:bg-emerald-900/30 dark:text-emerald-400">
              {{ record.farm_name }}
            </span>
            <span class="text-xs text-slate-400">{{ record.images.length }} 張</span>
          </div>
          <p v-if="record.description" class="line-clamp-2 text-sm text-slate-600 dark:text-slate-400">
            {{ record.description }}
          </p>
          <div class="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
            <p class="text-sm text-slate-500 dark:text-slate-500">{{ formatDate(record.created_at) }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 分頁 -->
    <div v-if="totalPages > 1" class="mt-6 flex items-center justify-center gap-2">
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage <= 1 || loading"
        class="cursor-pointer rounded border border-slate-300 px-3 py-1 text-sm transition
          hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50
          dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
      >
        上一頁
      </button>
      <span class="text-sm text-slate-600 dark:text-slate-400">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage >= totalPages || loading"
        class="cursor-pointer rounded border border-slate-300 px-3 py-1 text-sm transition
          hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50
          dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
      >
        下一頁
      </button>
    </div>

    <!-- 新增 Modal -->
    <CreateImageRecordModal
      :isOpen="showCreateModal"
      :farms="farms"
      @close="showCreateModal = false"
      @created="loadRecords"
    />

    <!-- 詳情 Modal -->
    <ImageRecordDetailModal
      :recordId="selectedRecordId"
      @close="selectedRecordId = null"
      @updated="loadRecords"
      @deleted="onRecordDeleted"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import { Plus, Camera, Image as ImageIcon } from 'lucide-vue-next'
import SafeImage from '@/components/common/SafeImage.vue'
import CreateImageRecordModal from '@/components/image-record/CreateImageRecordModal.vue'
import ImageRecordDetailModal from '@/components/image-record/ImageRecordDetailModal.vue'
import { useOnboardingTour } from '@/composables/useOnboardingTour'

const { startTour } = useOnboardingTour('imageRecords')

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const authStore = useAuthStore()
const { isAdmin } = storeToRefs(authStore)
const { showToast } = useToast()

const loading = ref(true)
const records = ref([])
const farms = ref([])
const selectedFarmId = ref(null)
const showCreateModal = ref(false)
const selectedRecordId = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)

function getImageUrl(filename, recordId) {
  return `${API_BASE_URL}/uploads/image-records/${recordId}/${filename}`
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('zh-TW')
}

async function loadFarms() {
  try {
    farms.value = await api.getFarms()
  } catch {
    // silent
  }
}

async function loadRecords() {
  loading.value = true
  try {
    const res = await api.getImageRecords(currentPage.value, 12, selectedFarmId.value)
    records.value = res.items
    totalPages.value = res.total_pages
  } catch (error) {
    showToast(error.message || '載入影像紀錄失敗', 'error')
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  currentPage.value = 1
  loadRecords()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadRecords()
}

function openDetail(recordId) {
  selectedRecordId.value = recordId
}

function onRecordDeleted() {
  selectedRecordId.value = null
  loadRecords()
}

onMounted(async () => {
  await Promise.all([loadFarms(), loadRecords()])
  setTimeout(() => startTour(), 500)
})
</script>
