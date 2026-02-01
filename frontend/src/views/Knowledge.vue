<template>
  <div class="p-4 sm:p-6">
    <!-- 標題 -->
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-3xl font-bold text-slate-800 dark:text-white">知識庫</h1>
      <button
        @click="showUploadModal = true"
        class="flex cursor-pointer items-center gap-2 rounded bg-emerald-600 px-4 py-2 text-white
          transition hover:bg-emerald-700"
      >
        <Plus :size="20" />
        新增知識
      </button>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <!-- 空狀態 -->
    <div v-else-if="documents.length === 0" class="py-12 text-center">
      <BookOpen :size="64" class="mx-auto mb-4 text-slate-400 dark:text-slate-500" />
      <p class="mb-4 text-slate-600 dark:text-slate-400">尚無知識文件</p>
      <button
        @click="showUploadModal = true"
        class="cursor-pointer rounded bg-emerald-600 px-4 py-2 text-white transition hover:bg-emerald-700"
      >
        上傳第一份文件
      </button>
    </div>

    <!-- 文件列表 -->
    <div v-else>
      <div class="overflow-x-auto rounded border border-slate-200 dark:border-slate-700">
        <table class="w-full text-left text-sm">
          <thead class="bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <tr>
              <th class="px-4 py-3 font-medium">標題</th>
              <th class="px-4 py-3 font-medium">來源檔名</th>
              <th class="px-4 py-3 font-medium">片段數</th>
              <th class="px-4 py-3 font-medium">建立時間</th>
              <th class="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
            <tr
              v-for="doc in documents"
              :key="doc.title"
              class="bg-white dark:bg-slate-900"
            >
              <td class="px-4 py-3 font-medium text-slate-800 dark:text-white">{{ doc.title }}</td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{{ doc.source_filename || '-' }}</td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{{ doc.chunk_count }}</td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{{ formatDate(doc.created_at) }}</td>
              <td class="px-4 py-3">
                <button
                  @click="openDeleteModal(doc)"
                  class="cursor-pointer text-red-600 transition hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                >
                  <Trash2 :size="18" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分頁 -->
      <div v-if="totalPages > 1" class="mt-4 flex items-center justify-center gap-2">
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="currentPage <= 1"
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
          :disabled="currentPage >= totalPages"
          class="cursor-pointer rounded border border-slate-300 px-3 py-1 text-sm transition
            hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50
            dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          下一頁
        </button>
      </div>
    </div>

    <!-- 上傳 Modal -->
    <UploadKnowledgeModal
      :isOpen="showUploadModal"
      @close="showUploadModal = false"
      @uploaded="loadDocuments"
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
            確定要刪除「{{ deleteTarget.title }}」的所有片段嗎？此操作無法復原。
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
                hover:bg-red-700 disabled:opacity-50"
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
import api from '@/services/api'
import { Plus, BookOpen, Trash2 } from 'lucide-vue-next'
import UploadKnowledgeModal from '@/components/knowledge/UploadKnowledgeModal.vue'

const { showToast } = useToast()

const loading = ref(true)
const submitting = ref(false)
const documents = ref([])
const showUploadModal = ref(false)
const deleteTarget = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('zh-TW')
}

async function loadDocuments() {
  loading.value = true
  try {
    const res = await api.getKnowledgeDocuments(currentPage.value)
    documents.value = res.items
    totalPages.value = res.total_pages
  } catch (error) {
    showToast(error.message || '載入知識庫失敗', 'error')
  } finally {
    loading.value = false
  }
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadDocuments()
}

function openDeleteModal(doc) {
  deleteTarget.value = doc
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  submitting.value = true
  try {
    await api.deleteKnowledge(deleteTarget.value.title)
    showToast('知識文件已刪除')
    deleteTarget.value = null
    await loadDocuments()
  } catch (error) {
    showToast(error.message || '刪除失敗', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadDocuments()
})
</script>
