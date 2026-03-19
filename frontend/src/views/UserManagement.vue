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
        <table class="w-full min-w-[900px] text-left text-sm">
          <thead class="bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <tr>
              <th class="px-4 py-3 font-medium">使用者名稱</th>
              <th class="px-4 py-3 font-medium">Email</th>
              <th class="px-4 py-3 font-medium">角色</th>
              <th class="px-4 py-3 font-medium">狀態</th>
              <th class="px-4 py-3 font-medium">建立時間</th>
              <th class="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
            <tr v-for="u in users" :key="u.id" class="bg-white dark:bg-slate-900">
              <td class="max-w-[150px] truncate px-4 py-3 font-medium text-slate-900 dark:text-white" :title="u.username">{{ u.username }}</td>
              <td class="max-w-[200px] truncate px-4 py-3 text-slate-600 dark:text-slate-400" :title="u.email">{{ u.email }}</td>
              <td class="px-4 py-3">
                <span
                  :class="u.is_admin
                    ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                    : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'"
                  class="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
                >
                  {{ u.is_admin ? '管理員' : '一般用戶' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span
                  :class="u.is_active
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'"
                  class="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
                >
                  {{ u.is_active ? '啟用' : '停用' }}
                </span>
              </td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{{ formatDate(u.created_at) }}</td>
              <td class="px-4 py-3">
                <div v-if="u.id !== currentUser.id" class="flex items-center gap-2">
                  <button
                    @click="handleToggleAdmin(u)"
                    :title="u.is_admin ? '降級為一般用戶' : '升級為管理員'"
                    class="cursor-pointer rounded p-1.5 text-amber-600 transition hover:bg-amber-50
                      dark:text-amber-400 dark:hover:bg-amber-900/30"
                  >
                    <ShieldCheck v-if="u.is_admin" :size="18" />
                    <Shield v-else :size="18" />
                  </button>
                  <button
                    @click="handleToggleActive(u)"
                    :title="u.is_active ? '停用帳號' : '啟用帳號'"
                    class="cursor-pointer rounded p-1.5 transition"
                    :class="u.is_active
                      ? 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700'
                      : 'text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-900/30'"
                  >
                    <UserX v-if="u.is_active" :size="18" />
                    <UserCheck v-else :size="18" />
                  </button>
                  <button
                    @click="openResetPasswordModal(u)"
                    title="重設密碼"
                    class="cursor-pointer rounded p-1.5 text-blue-600 transition hover:bg-blue-50
                      dark:text-blue-400 dark:hover:bg-blue-900/30"
                  >
                    <KeyRound :size="18" />
                  </button>
                  <button
                    @click="openDeleteModal(u)"
                    title="刪除帳號"
                    class="cursor-pointer rounded p-1.5 text-red-600 transition hover:bg-red-50
                      dark:text-red-400 dark:hover:bg-red-900/30"
                  >
                    <Trash2 :size="18" />
                  </button>
                </div>
                <span v-else class="text-xs text-slate-400 dark:text-slate-500">目前帳號</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 重設密碼 Modal -->
    <transition name="fade">
      <div
        v-if="resetTarget"
        class="modal-backdrop z-50 flex items-center justify-center"
        @click.self="resetTarget = null"
      >
        <div class="m-4 w-full max-w-md rounded bg-white p-6 dark:bg-slate-800">
          <h2 class="mb-4 text-2xl font-bold text-slate-800 dark:text-white">重設密碼</h2>
          <p class="mb-4 text-sm text-slate-600 dark:text-slate-400">
            為「{{ resetTarget.username }}」設定新密碼
          </p>
          <input
            v-model="newPassword"
            type="password"
            placeholder="請輸入新密碼"
            class="mb-4 w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm
              text-slate-900 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500
              dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-emerald-500"
          />
          <div class="flex gap-3">
            <button
              @click="resetTarget = null; newPassword = ''"
              class="flex-1 cursor-pointer rounded border border-slate-300 px-4 py-2 text-slate-700
                transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              取消
            </button>
            <button
              @click="confirmResetPassword"
              :disabled="submitting || !newPassword"
              class="flex-1 cursor-pointer rounded bg-emerald-600 px-4 py-2 text-white transition
                hover:bg-emerald-700 disabled:opacity-50"
            >
              {{ submitting ? '處理中...' : '確認重設' }}
            </button>
          </div>
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
            確定要刪除「{{ deleteTarget.username }}」的帳號嗎？此操作無法復原。
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
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import { Users, Shield, ShieldCheck, UserX, UserCheck, KeyRound, Trash2 } from 'lucide-vue-next'

const authStore = useAuthStore()
const { user: currentUser } = storeToRefs(authStore)
const { showToast } = useToast()

const loading = ref(true)
const submitting = ref(false)
const users = ref([])
const deleteTarget = ref(null)
const resetTarget = ref(null)
const newPassword = ref('')

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('zh-TW')
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
    const idx = users.value.findIndex(x => x.id === u.id)
    if (idx !== -1) users.value[idx] = updated
    showToast(updated.is_admin ? `已將「${u.username}」升級為管理員` : `已將「${u.username}」降級為一般用戶`)
  } catch (error) {
    showToast(error.message || '操作失敗', 'error')
  }
}

async function handleToggleActive(u) {
  try {
    const updated = await api.toggleUserActive(u.id)
    const idx = users.value.findIndex(x => x.id === u.id)
    if (idx !== -1) users.value[idx] = updated
    showToast(updated.is_active ? `已啟用「${u.username}」` : `已停用「${u.username}」`)
  } catch (error) {
    showToast(error.message || '操作失敗', 'error')
  }
}

function openResetPasswordModal(u) {
  resetTarget.value = u
  newPassword.value = ''
}

async function confirmResetPassword() {
  if (!resetTarget.value || !newPassword.value) return
  submitting.value = true
  try {
    await api.resetUserPassword(resetTarget.value.id, newPassword.value)
    showToast(`已重設「${resetTarget.value.username}」的密碼`)
    resetTarget.value = null
    newPassword.value = ''
  } catch (error) {
    showToast(error.message || '重設密碼失敗', 'error')
  } finally {
    submitting.value = false
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
    await loadUsers()
  } catch (error) {
    showToast(error.message || '刪除失敗', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadUsers()
})
</script>
