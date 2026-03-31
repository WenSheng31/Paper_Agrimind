<template>
  <div class="p-4 sm:p-6">
    <h1 class="text-3xl font-bold text-slate-800 dark:text-white">首頁</h1>
    <p class="mt-1 mb-4 text-slate-600 dark:text-slate-400">
      歡迎回來，{{ authStore.user?.username }}
    </p>

    <FarmQuickNav :farms="farms" class="mb-4" />

    <AiSummary
      id="ai-summary"
      class="mb-4"
      :prompt="`請使用 get_farms_overview 工具取得所有農場的最新狀態，並使用 get_latest_image_per_farm 取得每個農場最新的影像紀錄，如果有影像紀錄則用 analyze_image_record 分析圖片。然後嚴格按照以下固定 Markdown 格式回覆，不要加入其他內容：\n\n## 整體狀態\n一句話總結所有農場的整體情況。\n\n## 各農場摘要\n- **農場名稱**：環境（溫度/濕度），土壤狀況，最近操作，影像觀察（如有）。\n（每個農場一行，格式一致）\n\n## 建議事項\n1. 第一個建議\n2. 第二個建議\n（最多3條，針對當前數據與影像觀察給出具體建議）`"
      cache-key="home-summary"
    />

    <DashboardCharts class="mb-4" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import FarmQuickNav from '@/components/dashboard/FarmQuickNav.vue'
import DashboardCharts from '@/components/dashboard/DashboardCharts.vue'
import AiSummary from '@/components/ai/AiSummary.vue'
// import { useOnboardingTour } from '@/composables/useOnboardingTour'

const authStore = useAuthStore()
const { showToast } = useToast()
// const { startTour } = useOnboardingTour('home')

const farms = ref([])

async function loadFarms() {
  try {
    farms.value = await api.getFarms()
  } catch (error) {
    showToast(error.message || '載入農場資料失敗', 'error')
  }
}

onMounted(async () => {
  await loadFarms()
  // setTimeout(() => startTour(), 500)
})
</script>
