<template>
  <div class="p-4 sm:p-6">
    <!-- 標題列 -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-3xl font-bold text-slate-800 dark:text-white">對話紀錄</h1>
      <select
        v-model="filterUserId"
        @change="onFilterChange"
        class="rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700
          dark:border-slate-600 dark:bg-slate-950 dark:text-slate-300"
      >
        <option :value="null">所有使用者</option>
        <option v-for="u in users" :key="u.id" :value="u.id">{{ u.username }}</option>
      </select>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <!-- 空狀態 -->
    <div v-else-if="sessions.length === 0" class="py-12 text-center">
      <MessageSquareText :size="64" class="mx-auto mb-4 text-slate-400 dark:text-slate-500" />
      <p class="text-slate-600 dark:text-slate-400">尚無對話紀錄</p>
    </div>

    <!-- 對話列表 -->
    <div v-else>
      <div class="overflow-x-auto rounded border border-slate-200 dark:border-slate-700">
        <table class="w-full min-w-[700px] text-left text-sm">
          <thead class="bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <tr>
              <th class="px-4 py-3 font-medium">使用者</th>
              <th class="px-4 py-3 font-medium">對話主題</th>
              <th class="px-4 py-3 font-medium">訊息數</th>
              <th class="px-4 py-3 font-medium">最後活動</th>
              <th class="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
            <tr
              v-for="s in sessions"
              :key="s.session_id"
              class="bg-white dark:bg-slate-900"
            >
              <td class="max-w-[120px] truncate px-4 py-3 text-slate-600 dark:text-slate-400" :title="s.username">{{ s.username }}</td>
              <td class="max-w-[250px] px-4 py-3">
                <router-link
                  :to="`/chat-logs/${encodeURIComponent(s.session_id)}`"
                  class="block truncate font-medium text-emerald-700 hover:underline dark:text-emerald-400"
                  :title="s.first_query"
                >
                  {{ s.first_query || '(空)' }}
                </router-link>
              </td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{{ s.message_count }}</td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{{ formatDate(s.last_active) }}</td>
              <td class="px-4 py-3">
                <button
                  @click="openDeleteModal(s)"
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
    </div>

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
            確定要刪除「{{ deleteTarget.first_query || deleteTarget.session_id }}」的完整對話紀錄嗎？此操作無法復原。
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
import { MessageSquareText, Trash2 } from 'lucide-vue-next'

const { showToast } = useToast()

const loading = ref(true)
const submitting = ref(false)
const sessions = ref([])
const users = ref([])
const filterUserId = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const deleteTarget = ref(null)

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('zh-TW')
}

async function loadUsers() {
  try {
    users.value = await api.getUsers()
  } catch {
    // 靜默失敗
  }
}

async function loadSessions() {
  loading.value = true
  try {
    const res = await api.getChatSessions(currentPage.value, 10, filterUserId.value)
    sessions.value = res.items
    totalPages.value = res.total_pages
  } catch (error) {
    showToast(error.message || '載入對話紀錄失敗', 'error')
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  currentPage.value = 1
  loadSessions()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadSessions()
}

function openDeleteModal(session) {
  deleteTarget.value = session
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  submitting.value = true
  const sessionId = deleteTarget.value.session_id
  try {
    await api.deleteChatSession(sessionId)
    showToast('對話紀錄已刪除')
    deleteTarget.value = null
    await loadSessions()
  } catch (error) {
    showToast(error.message || '刪除失敗', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadUsers()
  loadSessions()
})
</script>
