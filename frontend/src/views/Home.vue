<template>
  <div class="p-4 sm:p-6">
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-slate-800 dark:text-white">首頁</h1>
      <p class="mt-1 text-slate-600 dark:text-slate-400">
        歡迎回來，{{ authStore.user?.username }}
      </p>
    </div>

    <!-- AI 總結 -->
    <AiSummary
      class="mb-4"
      :prompt="`請使用 get_farms_overview 工具取得所有農場的最新狀態，然後嚴格按照以下固定 Markdown 格式回覆，不要加入其他內容：\n\n## 整體狀態\n一句話總結所有農場的整體情況。\n\n## 各農場摘要\n- **農場名稱**：環境（溫度/濕度），土壤狀況，最近操作。\n（每個農場一行，格式一致）\n\n## 建議事項\n1. 第一個建議\n2. 第二個建議\n（最多3條，針對當前數據給出具體建議）`"
      cache-key="home-summary"
    />

    <div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div
        class="rounded border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-600 dark:text-slate-400">總農場數</p>
            <p class="mt-1 text-3xl font-bold text-slate-800 dark:text-white">
              {{ stats.totalFarms }}
            </p>
          </div>
          <div
            class="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100
              dark:bg-emerald-900/30"
          >
            <Tractor :size="24" class="text-emerald-600 dark:text-emerald-400" />
          </div>
        </div>
      </div>

      <div
        class="rounded border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-600 dark:text-slate-400">感測器數據</p>
            <p class="mt-1 text-3xl font-bold text-slate-800 dark:text-white">
              {{ stats.totalSensorData }}
            </p>
          </div>
          <div
            class="flex h-12 w-12 items-center justify-center rounded-full bg-green-100
              dark:bg-green-900/30"
          >
            <Activity :size="24" class="text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>

      <div
        class="rounded border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-600 dark:text-slate-400">操作記錄</p>
            <p class="mt-1 text-3xl font-bold text-slate-800 dark:text-white">
              {{ stats.totalOperations }}
            </p>
          </div>
          <div
            class="flex h-12 w-12 items-center justify-center rounded-full bg-green-100
              dark:bg-green-900/30"
          >
            <FileText :size="24" class="text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- 快速導航卡片 -->
    <div
      class="rounded border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800"
    >
      <h2 class="mb-6 text-lg font-semibold text-slate-800 dark:text-white">快速導航</h2>

      <div v-if="farms.length === 0" class="text-sm text-slate-500 dark:text-slate-400">
        尚無農場資料
      </div>

      <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="farm in farms"
          :key="farm.id"
          class="flex cursor-pointer items-center justify-between rounded border border-slate-100
            bg-slate-50 p-4 transition hover:border-emerald-500 hover:bg-white dark:border-slate-700
            dark:bg-slate-900/50 dark:hover:border-emerald-400 dark:hover:bg-slate-800"
          @click="$router.push(`/farms/${farm.id}`)"
        >
          <div class="flex items-center gap-3">
            <div class="rounded-full bg-emerald-100 p-2 dark:bg-emerald-900/30">
              <Sprout :size="20" class="text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white">{{ farm.name }}</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                {{ farm.location || '未設定位置' }}
              </p>
            </div>
          </div>
          <div class="text-slate-400 dark:text-slate-500">
            <ArrowRight :size="20" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import { Sprout, Activity, FileText, Tractor, ArrowRight } from 'lucide-vue-next'
import AiSummary from '@/components/ai/AiSummary.vue'

const authStore = useAuthStore()
const { showToast } = useToast()

const stats = ref({
  totalFarms: 0,
  totalSensorData: 0,
  totalOperations: 0,
})
const farms = ref([])

async function loadDashboardData() {
  try {
    const [statsData, farmsData] = await Promise.all([api.getDashboardStats(), api.getFarms()])

    stats.value = {
      totalFarms: statsData.total_farms,
      totalSensorData: statsData.total_sensor_data,
      totalOperations: statsData.total_operations,
    }
    farms.value = farmsData
  } catch (error) {
    showToast(error.message || '載入儀表板數據失敗', 'error')
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>
