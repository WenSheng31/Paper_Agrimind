<template>
  <div class="p-4 sm:p-6">
    <div v-if="isAdmin" class="mb-4 flex items-center justify-between">
      <button
        @click="showAddModal = true"
        class="flex cursor-pointer items-center gap-2 rounded bg-emerald-600 px-4 py-2 text-white
          transition hover:bg-emerald-700"
      >
        <Plus :size="20" />
        新增數據
      </button>
    </div>

    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <div v-else-if="data.length === 0" class="py-12 text-center text-slate-600 dark:text-slate-400">
      尚無感測器數據
    </div>

    <div v-else class="space-y-4">
      <!-- 最新數據卡片 -->
      <div
        v-if="latestSensorData"
        class="rounded border border-emerald-200 bg-gradient-to-r from-emerald-50 to-green-50 p-4
          md:p-6 dark:border-emerald-900/50 dark:from-emerald-900/20 dark:to-green-900/20"
      >
        <h3 class="mb-4 text-lg font-semibold text-slate-800 dark:text-white">最新數據</h3>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">環境溫度</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.temperature?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">°C</span>
            </p>
          </div>
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">環境濕度</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.humidity?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">%</span>
            </p>
          </div>
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">降水量</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.precipitation?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">mm</span>
            </p>
          </div>
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">日照時數</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.sunshine_hours?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">hr</span>
            </p>
          </div>
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">土壤濕度</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.soil_moisture?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">%</span>
            </p>
          </div>
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">土壤氮 (N)</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.soil_n?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">mg/kg</span>
            </p>
          </div>
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">土壤磷 (P)</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.soil_p?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">mg/kg</span>
            </p>
          </div>
          <div>
            <p class="text-base text-slate-600 dark:text-slate-400">土壤鉀 (K)</p>
            <p class="text-xl font-bold text-slate-800 md:text-2xl dark:text-white">
              {{ latestSensorData.soil_k?.toFixed(1) || '-' }}
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">mg/kg</span>
            </p>
          </div>
        </div>
      </div>

      <!-- 歷史數據表格 -->
      <div>
        <h3 class="mb-4 text-lg font-semibold text-slate-800 dark:text-white">歷史數據</h3>
        <div class="overflow-x-auto rounded border border-slate-200 dark:border-slate-700">
          <table class="w-full min-w-250">
            <thead class="bg-slate-50 dark:bg-slate-900/50">
              <tr>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  時間
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  溫度
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  濕度
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  降水
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  日照
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  土壤濕度
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  氮(N)
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  磷(P)
                </th>
                <th
                  class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  鉀(K)
                </th>
                <th
                  v-if="isAdmin"
                  class="w-16 border-b border-slate-200 px-4 py-3 text-center text-base font-medium
                    text-slate-700 dark:border-slate-700 dark:text-slate-300"
                >
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in data"
                :key="item.id"
                class="transition hover:bg-slate-50 dark:hover:bg-slate-700/50"
              >
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-600
                    dark:border-slate-700 dark:text-slate-400"
                >
                  {{ formatDateTime(item.timestamp) }}
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.temperature?.toFixed(1) || '-' }}°C
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.humidity?.toFixed(1) || '-' }}%
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.precipitation?.toFixed(1) || '-' }}mm
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.sunshine_hours?.toFixed(1) || '-' }}hr
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.soil_moisture?.toFixed(1) || '-' }}%
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.soil_n?.toFixed(1) || '-' }}
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.soil_p?.toFixed(1) || '-' }}
                </td>
                <td
                  class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                    dark:border-slate-700 dark:text-slate-200"
                >
                  {{ item.soil_k?.toFixed(1) || '-' }}
                </td>
                <td v-if="isAdmin" class="border-b border-slate-200 px-4 py-3 text-center dark:border-slate-700">
                  <button
                    @click="handleDelete(item)"
                    class="cursor-pointer text-red-600 transition hover:text-red-700
                      dark:text-red-400 dark:hover:text-red-300"
                    title="刪除"
                  >
                    <Trash2 :size="18" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分頁控制 -->
        <div
          v-if="total > pageSize"
          class="mt-4 flex flex-col items-center justify-between gap-4 sm:flex-row"
        >
          <div class="order-2 text-base text-slate-600 sm:order-1 dark:text-slate-400">
            顯示 {{ (currentPage - 1) * pageSize + 1 }} -
            {{ Math.min(currentPage * pageSize, total) }} 筆，共 {{ total }} 筆
          </div>
          <div class="order-1 flex items-center gap-2 sm:order-2">
            <button
              @click="changePage(currentPage - 1)"
              :disabled="currentPage === 1"
              class="flex h-8 w-8 cursor-pointer items-center justify-center rounded border border-slate-300 text-slate-700 transition
                hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50
                dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
              title="上一頁"
            >
              <ChevronLeft :size="16" />
            </button>
            <div class="flex gap-1">
              <button
                v-for="page in displayPages"
                :key="page"
                @click="changePage(page)"
                :class="[
                  'flex h-8 min-w-8 cursor-pointer items-center justify-center rounded border px-2 text-sm transition',
                  page === currentPage
                    ? 'border-emerald-600 bg-emerald-600 text-white'
                    : `border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-600
                      dark:text-slate-300 dark:hover:bg-slate-700`,
                ]"
              >
                {{ page }}
              </button>
            </div>
            <button
              @click="changePage(currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="flex h-8 w-8 cursor-pointer items-center justify-center rounded border border-slate-300 text-slate-700 transition
                hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50
                dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
              title="下一頁"
            >
              <ChevronRight :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <AddSensorModal
      :is-open="showAddModal"
      :submitting="submitting"
      @close="showAddModal = false"
      @submit="handleAdd"
    />

    <!-- 刪除確認 Modal -->
    <transition name="fade">
      <div
        v-if="deleteTarget"
        class="modal-backdrop z-50 flex items-center justify-center"
        @click.self="deleteTarget = null"
      >
        <div class="m-4 w-full max-w-md rounded bg-white p-6 dark:bg-slate-800">
          <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">確認刪除</h2>
          <p class="mb-6 text-slate-600 dark:text-slate-400">
            確定要刪除這筆感測器數據嗎？
            <br />
            <span class="text-base text-slate-500 dark:text-slate-500"
              >時間：{{ formatDateTime(deleteTarget.timestamp) }}</span
            >
          </p>
          <div class="flex gap-3">
            <button
              @click="deleteTarget = null"
              class="flex-1 cursor-pointer rounded border border-slate-300 px-4 py-2 text-slate-700
                transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300
                dark:hover:bg-slate-700"
            >
              取消
            </button>
            <button
              @click="confirmDelete"
              :disabled="submitting"
              class="flex-1 cursor-pointer rounded bg-red-600 px-4 py-2 text-white transition
                hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {{ submitting ? '刪除中...' : '確認刪除' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import AddSensorModal from './AddSensorModal.vue'

const authStore = useAuthStore()
const { isAdmin } = storeToRefs(authStore)

const props = defineProps({
  farmId: {
    type: Number,
    required: true,
  },
})

const { showToast } = useToast()

const loading = ref(false)
const submitting = ref(false)
const data = ref([])
const showAddModal = ref(false)
const deleteTarget = ref(null)
const latestSensorData = ref(null)

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = ref(0)

const displayPages = computed(() => {
  const pages = []
  const maxDisplay = 5
  let startPage = Math.max(1, currentPage.value - Math.floor(maxDisplay / 2))
  let endPage = Math.min(totalPages.value, startPage + maxDisplay - 1)

  if (endPage - startPage + 1 < maxDisplay) {
    startPage = Math.max(1, endPage - maxDisplay + 1)
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }
  return pages
})

function formatDateTime(dateString) {
  return new Date(dateString).toLocaleString('zh-TW')
}

async function loadData() {
  loading.value = true
  try {
    const response = await api.getSensorData(props.farmId, currentPage.value, pageSize.value)
    data.value = response.items
    total.value = response.total
    totalPages.value = response.total_pages

    if (currentPage.value === 1 && response.items.length > 0) {
      latestSensorData.value = response.items[0]
    } else if (currentPage.value === 1) {
      latestSensorData.value = null
    }

    if (currentPage.value !== 1 && !latestSensorData.value) {
      const latestResponse = await api.getSensorData(props.farmId, 1, 1)
      if (latestResponse.items.length > 0) {
        latestSensorData.value = latestResponse.items[0]
      }
    }
  } catch (error) {
    showToast('載入感測器數據失敗', 'error')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function changePage(page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    await loadData()
  }
}

async function handleAdd(formData) {
  submitting.value = true
  try {
    await api.createSensorData(props.farmId, formData)
    showToast('感測器數據新增成功')
    showAddModal.value = false
    currentPage.value = 1
    await loadData()
  } catch (error) {
    showToast(error.message || '新增失敗', 'error')
  } finally {
    submitting.value = false
  }
}

function handleDelete(item) {
  deleteTarget.value = item
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  submitting.value = true
  try {
    await api.deleteSensorData(deleteTarget.value.id)
    showToast('感測器數據已刪除')
    deleteTarget.value = null
    await loadData()
  } catch (error) {
    showToast(error.message || '刪除失敗', 'error')
  } finally {
    submitting.value = false
  }
}

watch(
  () => props.farmId,
  () => {
    currentPage.value = 1
    loadData()
  },
)

onMounted(() => {
  loadData()
})
</script>
