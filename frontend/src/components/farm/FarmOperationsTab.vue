<template>
  <div class="p-4 sm:p-6">
    <div v-if="isAdmin" class="mb-4 flex items-center justify-between">
      <button
        @click="showAddModal = true"
        class="flex cursor-pointer items-center gap-2 rounded bg-emerald-600 px-4 py-2 text-white
          transition hover:bg-emerald-700"
      >
        <Plus :size="20" />
        新增記錄
      </button>
    </div>

    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <div
      v-else-if="operations.length === 0"
      class="py-12 text-center text-slate-600 dark:text-slate-400"
    >
      尚無農務記錄
    </div>

    <div v-else class="overflow-x-auto rounded border border-slate-200 dark:border-slate-700">
      <table class="w-full min-w-150">
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
              描述
            </th>
            <th
              class="border-b border-slate-200 px-4 py-3 text-left text-base font-medium
                text-slate-700 dark:border-slate-700 dark:text-slate-300"
            >
              操作人員
            </th>
            <th
              v-if="isAdmin"
              class="w-24 border-b border-slate-200 px-4 py-3 text-center text-base font-medium
                text-slate-700 dark:border-slate-700 dark:text-slate-300"
            >
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="op in operations"
            :key="op.id"
            class="transition hover:bg-slate-50 dark:hover:bg-slate-700/50"
          >
            <td
              class="border-b border-slate-200 px-4 py-3 text-base whitespace-nowrap text-slate-600
                dark:border-slate-700 dark:text-slate-400"
            >
              {{ formatDateTime(op.performed_at) }}
            </td>
            <td
              class="border-b border-slate-200 px-4 py-3 text-base text-slate-800
                dark:border-slate-700 dark:text-slate-200"
            >
              {{ op.description }}
            </td>
            <td
              class="border-b border-slate-200 px-4 py-3 text-base text-slate-600
                dark:border-slate-700 dark:text-slate-400"
            >
              {{ op.operator_name || '—' }}
            </td>
            <td
              v-if="isAdmin"
              class="border-b border-slate-200 px-4 py-3 text-center dark:border-slate-700"
            >
              <button
                @click="handleDelete(op)"
                class="cursor-pointer text-red-600 transition hover:text-red-700 dark:text-red-400
                  dark:hover:text-red-300"
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
            hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600
            dark:text-slate-300 dark:hover:bg-slate-700"
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
            hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600
            dark:text-slate-300 dark:hover:bg-slate-700"
          title="下一頁"
        >
          <ChevronRight :size="16" />
        </button>
      </div>
    </div>

    <AddOperationModal
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
            確定要刪除這筆操作記錄嗎？
            <br />
            <span class="text-base text-slate-500 dark:text-slate-500">
              時間：{{ formatDateTime(deleteTarget.performed_at) }}
              <br />
              內容：{{ deleteTarget.description }}
            </span>
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
import { ref, onMounted, watch, computed } from 'vue'
import { Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import AddOperationModal from './AddOperationModal.vue'

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
const operations = ref([])
const showAddModal = ref(false)
const deleteTarget = ref(null)
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
  const d = new Date(dateString)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function loadData() {
  loading.value = true
  try {
    const response = await api.getOperations(props.farmId, currentPage.value, pageSize.value)
    operations.value = response.items
    total.value = response.total
    totalPages.value = response.total_pages
  } catch (error) {
    showToast('載入農務記錄失敗', 'error')
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
    await api.createOperation(props.farmId, formData)
    showToast('農務記錄新增成功')
    showAddModal.value = false
    currentPage.value = 1
    await loadData()
  } catch (error) {
    showToast(error.message || '新增失敗', 'error')
  } finally {
    submitting.value = false
  }
}

function handleDelete(op) {
  deleteTarget.value = op
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  submitting.value = true
  try {
    await api.deleteOperation(deleteTarget.value.id)
    showToast('農務記錄已刪除')
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
