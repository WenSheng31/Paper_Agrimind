<template>
  <div class="p-4 sm:p-6">
    <h1 class="text-3xl font-bold text-slate-800 dark:text-white">首頁</h1>
    <p class="mt-1 mb-4 text-slate-600 dark:text-slate-400">
      歡迎回來，{{ authStore.user?.username }}
    </p>

    <FarmQuickNav :farms="farms" class="mb-4" />

    <AiSummary
      class="mb-4"
      :prompt="`請使用 get_farms_overview 工具取得所有農場的最新狀態，然後嚴格按照以下固定 Markdown 格式回覆，不要加入其他內容：\n\n## 整體狀態\n一句話總結所有農場的整體情況。\n\n## 各農場摘要\n- **農場名稱**：環境（溫度/濕度），土壤狀況，最近操作。\n（每個農場一行，格式一致）\n\n## 建議事項\n1. 第一個建議\n2. 第二個建議\n（最多3條，針對當前數據給出具體建議）`"
      cache-key="home-summary"
    />

    <DashboardCharts v-if="farms.length" :farms="farms" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import FarmQuickNav from '@/components/dashboard/FarmQuickNav.vue'
import AiSummary from '@/components/ai/AiSummary.vue'
import DashboardCharts from '@/components/dashboard/DashboardCharts.vue'

const authStore = useAuthStore()
const { showToast } = useToast()

const farms = ref([])

async function loadDashboardData() {
  try {
    const farmsData = await api.getFarms()
    farms.value = farmsData
  } catch (error) {
    showToast(error.message || '載入儀表板數據失敗', 'error')
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>
