<template>
  <div class="p-4 sm:p-6">
    <!-- 標題 -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-slate-800 dark:text-white">帳號管理</h1>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <!-- 空狀態 -->
    <div v-else-if="users.length === 0" class="py-12 text-center">
      <Users :size="64" class="mx-auto mb-4 text-slate-400 dark:text-slate-500" />
      <p class="text-slate-600 dark:text-slate-400">尚無使用者</p>
    </div>

    <!-- 使用者列表 -->
    <div v-else>
      <div class="overflow-x-auto rounded border border-slate-200 dark:border-slate-700">
        <table class="w-full min-w-120 text-left text-base">
          <thead class="bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <tr>
              <th class="px-4 py-3 font-medium">使用者名稱</th>
              <th class="px-4 py-3 font-medium">角色</th>
              <th class="px-4 py-3 font-medium">狀態</th>
              <th class="px-4 py-3 font-medium">任務進度</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
            <tr
              v-for="u in users"
              :key="u.id"
              class="cursor-pointer bg-white transition hover:bg-slate-50 dark:bg-slate-900
                dark:hover:bg-slate-800"
              @click="openDetailPopover(u)"
            >
              <td class="px-4 py-3 font-medium text-slate-900 dark:text-white">
                {{ u.username }}
              </td>
              <td class="px-4 py-3">
                <span
                  :class="
                    u.is_admin
                      ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                      : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                  "
                  class="inline-block rounded-full px-2.5 py-0.5 text-sm font-medium"
                >
                  {{ u.is_admin ? '管理員' : '一般用戶' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span
                  :class="
                    u.is_active
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  "
                  class="inline-block rounded-full px-2.5 py-0.5 text-sm font-medium"
                >
                  {{ u.is_active ? '啟用' : '停用' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <template v-if="getTaskStatus(u.id)">
                  <span
                    :class="
                      getTaskStatus(u.id).is_completed
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                        : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                    "
                    class="inline-block rounded-full px-2.5 py-0.5 text-sm font-medium"
                  >
                    {{
                      getTaskStatus(u.id).is_completed
                        ? '已完成'
                        : `進行中 ${getTaskStatus(u.id).current_step}/${TOTAL_TASKS}`
                    }}
                  </span>
                </template>
                <span v-else class="text-sm text-slate-400 dark:text-slate-500">未開始</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 帳號詳情彈窗 -->
    <UserDetailModal
      :user="detailTarget"
      :task-status="detailTarget ? getTaskStatus(detailTarget.id) : null"
      :is-self="detailTarget?.id === currentUser.id"
      @close="detailTarget = null"
      @toggle-admin="handleToggleAdmin"
      @toggle-active="handleToggleActive"

      @reset-task="handleResetTask"
      @delete="openDeleteModal"
    />

    <!-- 刪除確認 Modal -->
    <transition name="fade">
      <div
        v-if="deleteTarget"
        class="modal-backdrop z-[60] flex items-center justify-center"
        @click.self="deleteTarget = null"
      >
        <div class="m-4 w-full max-w-md rounded bg-white p-6 dark:bg-slate-800">
          <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">確認刪除</h2>
          <p class="mb-6 text-slate-600 dark:text-slate-400">
            確定要刪除「{{ deleteTarget.username }}」的帳號嗎？此操作無法復原。
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
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import { Users, Trash2 } from 'lucide-vue-next'
import UserDetailModal from '@/components/admin/UserDetailModal.vue'
import { TOTAL_TASKS } from '@/composables/useTaskGuide'

const authStore = useAuthStore()
const { user: currentUser } = storeToRefs(authStore)
const { showToast } = useToast()

const loading = ref(true)
const submitting = ref(false)
const users = ref([])
const deleteTarget = ref(null)
const taskProgressMap = ref({})
const detailTarget = ref(null)

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('zh-TW')
}

function getTaskStatus(userId) {
  return taskProgressMap.value[userId] || null
}

function openDetailPopover(u) {
  detailTarget.value = u
}

async function loadTaskProgress() {
  try {
    const items = await api.getAllTaskProgress()
    const map = {}
    for (const item of items) {
      map[item.user_id] = item
    }
    taskProgressMap.value = map
  } catch {
    // 靜默失敗
  }
}

async function handleResetTask(u) {
  try {
    await api.resetTaskProgress(u.id)
    showToast(`已重置「${u.username}」的任務進度`)
    await loadTaskProgress()
  } catch (error) {
    showToast(error.message || '重置失敗', 'error')
  }
}

async function loadUsers() {
  loading.value = true
  try {
    users.value = await api.getUsers()
  } catch (error) {
    showToast(error.message || '載入使用者失敗', 'error')
  } finally {
    loading.value = false
  }
}

async function handleToggleAdmin(u) {
  try {
    const updated = await api.toggleUserAdmin(u.id)
    const idx = users.value.findIndex((x) => x.id === u.id)
    if (idx !== -1) users.value[idx] = updated
    if (detailTarget.value?.id === u.id) detailTarget.value = updated
    showToast(
      updated.is_admin
        ? `已將「${u.username}」升級為管理員`
        : `已將「${u.username}」降級為一般用戶`,
    )
  } catch (error) {
    showToast(error.message || '操作失敗', 'error')
  }
}

async function handleToggleActive(u) {
  try {
    const updated = await api.toggleUserActive(u.id)
    const idx = users.value.findIndex((x) => x.id === u.id)
    if (idx !== -1) users.value[idx] = updated
    if (detailTarget.value?.id === u.id) detailTarget.value = updated
    showToast(updated.is_active ? `已啟用「${u.username}」` : `已停用「${u.username}」`)
  } catch (error) {
    showToast(error.message || '操作失敗', 'error')
  }
}

function openDeleteModal(u) {
  deleteTarget.value = u
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  submitting.value = true
  try {
    await api.deleteUser(deleteTarget.value.id)
    showToast(`已刪除「${deleteTarget.value.username}」`)
    deleteTarget.value = null
    detailTarget.value = null
    await loadUsers()
  } catch (error) {
    showToast(error.message || '刪除失敗', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadUsers()
  loadTaskProgress()
})
</script>
