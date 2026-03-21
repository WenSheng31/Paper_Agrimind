<template>
  <div class="p-4 sm:p-6">
    <!-- 標題 -->
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-3xl font-bold text-slate-800 dark:text-white">農場管理</h1>
      <button
        v-if="isAdmin"
        @click="showCreateModal = true"
        class="flex cursor-pointer items-center gap-2 rounded bg-emerald-600 px-4 py-2 text-white
          transition hover:bg-emerald-700"
      >
        <Plus :size="20" />
        新增農場
      </button>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <!-- 如果無農場資料 -->
    <div v-else-if="farms.length === 0" class="py-12 text-center">
      <Building :size="64" class="mx-auto mb-4 text-slate-400 dark:text-slate-500" />
      <p class="mb-4 text-slate-600 dark:text-slate-400">尚無農場資料</p>
      <button
        v-if="isAdmin"
        @click="showCreateModal = true"
        class="cursor-pointer rounded bg-emerald-600 px-4 py-2 text-white transition
          hover:bg-emerald-700"
      >
        建立第一個農場
      </button>
    </div>

    <!-- 如果有農場資料 -->
    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="farm in farms"
        :key="farm.id"
        class="cursor-pointer rounded border border-slate-200 bg-white p-6 transition
          hover:border-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-emerald-400"
        @click="$router.push(`/farms/${farm.id}`)"
      >
        <div class="mb-4 flex items-start justify-between">
          <!-- 農場名稱 -->
          <h2 class="text-xl font-semibold text-slate-800 dark:text-white">{{ farm.name }}</h2>
          <!-- 刪除農場按鈕（僅管理員） -->
          <button
            v-if="isAdmin"
            @click.stop="openDeleteModal(farm)"
            class="cursor-pointer text-red-600 transition hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          >
            <Trash2 :size="20" />
          </button>
        </div>
        <p class="mb-2 text-slate-600 dark:text-slate-400">
          <span class="font-medium">位置：</span>{{ farm.location || '未設定' }}
        </p>
        <p v-if="farm.description" class="line-clamp-2 text-base text-slate-600 dark:text-slate-400">
          {{ farm.description }}
        </p>
        <div class="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
          <p class="text-base text-slate-500 dark:text-slate-500">建立時間：{{ formatDate(farm.created_at) }}</p>
        </div>
      </div>
    </div>

    <!-- 新增農場 Modal -->
    <transition name="fade">
      <div
        v-if="showCreateModal"
        class="modal-backdrop z-50 flex items-center justify-center"
        @click.self="showCreateModal = false"
      >
        <div class="m-4 w-full max-w-md rounded bg-white p-6 dark:bg-slate-800">
          <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">新增農場</h2>
          <form @submit.prevent="createFarm" class="space-y-4">
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">農場名稱</label>
              <input
                v-model="formData.name"
                type="text"
                required
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">位置</label>
              <input
                v-model="formData.location"
                type="text"
                class="w-full rounded border border-slate-300 px-3 py-2 focus:ring-2
                  focus:ring-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-950 dark:text-white"
              />
            </div>
            <div>
              <label class="mb-1 block text-base font-medium text-slate-700 dark:text-slate-300">描述</label>
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
                @click="showCreateModal = false"
                class="flex-1 cursor-pointer rounded border border-slate-300 px-4 py-2
                  text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="submitting"
                class="flex-1 cursor-pointer rounded bg-emerald-600 px-4 py-2 text-white transition
                  hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {{ submitting ? '建立中...' : '建立' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </transition>

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
            確定要刪除農場「{{ deleteTarget.name }}」嗎？此操作無法復原。
          </p>
          <div class="flex gap-3">
            <button
              @click="deleteTarget = null"
              class="flex-1 cursor-pointer rounded border border-slate-300 px-4 py-2 text-slate-700
                transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
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
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import { Plus, Building, Trash2 } from 'lucide-vue-next'

const authStore = useAuthStore()
const { isAdmin } = storeToRefs(authStore)

const { showToast } = useToast()

const loading = ref(true)
const submitting = ref(false)
const farms = ref([])
const showCreateModal = ref(false)
const deleteTarget = ref(null)
const formData = ref({
  name: '',
  location: '',
  description: '',
})

// 格式化日期字串
function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('zh-TW')
}

// 載入農場列表
async function loadFarms() {
  loading.value = true
  try {
    farms.value = await api.getFarms()
  } catch (error) {
    showToast(error.message || '載入農場列表失敗', 'error')
  } finally {
    loading.value = false
  }
}

// 新增農場
async function createFarm() {
  submitting.value = true
  try {
    await api.createFarm(formData.value)
    showToast('農場建立成功')
    showCreateModal.value = false
    formData.value = { name: '', location: '', description: '' }
    await loadFarms()
  } catch (error) {
    showToast(error.message || '建立農場失敗', 'error')
  } finally {
    submitting.value = false
  }
}

// 開啟刪除 Modal
function openDeleteModal(farm) {
  deleteTarget.value = farm
}

// 刪除農場
async function confirmDelete() {
  if (!deleteTarget.value) return
  submitting.value = true
  try {
    await api.deleteFarm(deleteTarget.value.id)
    showToast('農場已刪除')
    deleteTarget.value = null
    await loadFarms()
  } catch (error) {
    showToast(error.message || '刪除農場失敗', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadFarms()
})
</script>
