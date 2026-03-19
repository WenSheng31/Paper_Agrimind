<template>
  <div class="p-4 sm:p-6">
    <!-- 載入中 -->
    <div v-if="loading" class="py-12 text-center text-slate-600 dark:text-slate-400">載入中...</div>

    <!-- 載入成功 -->
    <div v-else-if="farm">
      <div class="mb-4">
        <button
          @click="$router.push('/farms')"
          class="mb-4 flex cursor-pointer items-center gap-2 text-slate-600 hover:text-slate-800
            dark:text-slate-400 dark:hover:text-slate-200"
        >
          <ChevronLeft :size="20" />
          返回農場列表
        </button>

        <!-- 農場資訊 -->
        <div
          id="farm-info"
          class="rounded border border-slate-200 bg-white p-6 dark:border-slate-700
            dark:bg-slate-800"
        >
          <div class="mb-4 flex items-start justify-between">
            <div>
              <h1 class="text-3xl font-bold text-slate-800 dark:text-white">{{ farm.name }}</h1>
              <p class="mt-2 text-slate-600 dark:text-slate-400">
                {{ farm.location || '未設定位置' }}
              </p>
            </div>
            <button
              v-if="isAdmin"
              @click="showEditModal = true"
              class="cursor-pointer rounded border border-slate-300 px-4 py-2 text-slate-700
                transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300
                dark:hover:bg-slate-700"
            >
              編輯
            </button>
          </div>
          <p v-if="farm.description" class="text-slate-600 dark:text-slate-400">{{ farm.description }}</p>
          <div class="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
            <p class="text-sm text-slate-500 dark:text-slate-500">
              建立時間：{{ formatDate(farm.created_at) }}
            </p>
          </div>
        </div>
      </div>

      <!-- AI 總結 -->
      <AiSummary
        id="farm-ai-summary"
        class="mb-4"
        :prompt="`查詢農場「${farm.name}」(ID: ${farm.id}) 最新的感測器資料、農務記錄與影像紀錄，給出該農場的狀態總結與建議。如果有影像紀錄，請分析最新一筆的圖片。字數控制在200字內。`"
        :cache-key="`farm-${farm.id}-summary`"
      />

      <!-- Tab 切換 -->
      <div
        id="farm-tabs"
        class="mb-4 rounded border border-slate-200 bg-white dark:border-slate-700
          dark:bg-slate-800"
      >
        <div class="border-b border-slate-200 dark:border-slate-700">
          <div class="flex">
            <button
              @click="activeTab = 'sensor'"
              :class="[
                'cursor-pointer px-6 py-3 font-medium transition',
                activeTab === 'sensor'
                  ? `border-b-2 border-emerald-600 text-emerald-600 dark:border-emerald-400
                    dark:text-emerald-400`
                  : `text-slate-600 hover:text-slate-800 dark:text-slate-400
                    dark:hover:text-slate-200`,
              ]"
            >
              感測器數據
            </button>
            <button
              @click="activeTab = 'operations'"
              :class="[
                'cursor-pointer px-6 py-3 font-medium transition',
                activeTab === 'operations'
                  ? `border-b-2 border-emerald-600 text-emerald-600 dark:border-emerald-400
                    dark:text-emerald-400`
                  : `text-slate-600 hover:text-slate-800 dark:text-slate-400
                    dark:hover:text-slate-200`,
              ]"
            >
              農務記錄
            </button>
            <button
              @click="activeTab = 'images'"
              :class="[
                'cursor-pointer px-6 py-3 font-medium transition',
                activeTab === 'images'
                  ? `border-b-2 border-emerald-600 text-emerald-600 dark:border-emerald-400
                    dark:text-emerald-400`
                  : `text-slate-600 hover:text-slate-800 dark:text-slate-400
                    dark:hover:text-slate-200`,
              ]"
            >
              影像紀錄
            </button>
          </div>
        </div>

        <!-- 感測器數據/農務記錄 -->
        <div class="min-h-100">
          <KeepAlive>
            <FarmSensorTab v-if="activeTab === 'sensor'" :farm-id="farm.id" />
            <FarmOperationsTab v-else-if="activeTab === 'operations'" :farm-id="farm.id" />
            <FarmImageRecordsTab v-else-if="activeTab === 'images'" :farm-id="farm.id" :farm-name="farm.name" />
          </KeepAlive>
        </div>
      </div>
    </div>

    <!-- 編輯農場 Modal-->
    <EditFarmModal
      :is-open="showEditModal"
      :submitting="submitting"
      :initial-data="farm"
      @close="showEditModal = false"
      @submit="handleUpdateFarm"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import api from '@/services/api'

const authStore = useAuthStore()
const { isAdmin } = storeToRefs(authStore)
import { ChevronLeft } from 'lucide-vue-next'

// Sub-components
import EditFarmModal from '@/components/farm/EditFarmModal.vue'
import FarmSensorTab from '@/components/farm/FarmSensorTab.vue'
import FarmOperationsTab from '@/components/farm/FarmOperationsTab.vue'
import FarmImageRecordsTab from '@/components/farm/FarmImageRecordsTab.vue'
import AiSummary from '@/components/ai/AiSummary.vue'
import { useOnboardingTour } from '@/composables/useOnboardingTour'

const route = useRoute()
const { showToast } = useToast()

const { startTour } = useOnboardingTour('farmDetail')

const loading = ref(true)
const submitting = ref(false)
const farm = ref(null)
const activeTab = ref('sensor')
const showEditModal = ref(false)

// 格式化日期字串
function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('zh-TW')
}

// 載入農場資料
async function loadFarmData() {
  loading.value = true
  try {
    const farmId = parseInt(route.params.id)
    farm.value = await api.getFarm(farmId)
  } catch (error) {
    showToast(error.message || '載入農場資料失敗', 'error')
    console.error('Error loading farm data:', error)
  } finally {
    loading.value = false
  }
}

// 更新農場資料
async function handleUpdateFarm(formData) {
  submitting.value = true
  try {
    await api.updateFarm(farm.value.id, formData)
    showToast('農場更新成功')
    showEditModal.value = false
    await loadFarmData()
  } catch (error) {
    showToast(error.message || '更新農場失敗', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadFarmData()
  setTimeout(() => startTour(), 500)
})
</script>
