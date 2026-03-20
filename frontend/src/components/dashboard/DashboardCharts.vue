<template>
  <div>
    <div class="mb-3 flex flex-wrap items-center gap-2">
      <h2 class="text-lg font-semibold text-slate-800 dark:text-white">農場數據</h2>
      <span class="text-slate-400 dark:text-slate-500">—</span>
      <select
        v-model="farmId"
        class="cursor-pointer rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700
          dark:border-slate-600 dark:bg-slate-900 dark:text-slate-300"
      >
        <option v-for="farm in farms" :key="farm.id" :value="farm.id">
          {{ farm.name }}
        </option>
      </select>
    </div>

    <!-- 趨勢（近 30 天） -->
    <div class="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
      <ChartCard
        title="溫度 / 濕度趨勢（近 30 天）"
        class="lg:col-span-2"
        :loading="loading"
        :empty="!timeSeries.length"
      >
        <TemperatureHumidityChart :time-series="timeSeries" :farm-names="farmNames" />
      </ChartCard>

      <ChartCard title="降水量（近 30 天）" :loading="loading" :empty="!timeSeries.length">
        <PrecipitationChart :time-series="timeSeries" :farm-names="farmNames" />
      </ChartCard>
    </div>

    <!-- 最新狀態 -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <ChartCard title="土壤養分 (NPK)" :loading="loading" :empty="!latestList.length">
        <SoilNutrientChart :latest-per-farm="latestList" />
      </ChartCard>

      <ChartCard title="農場環境比較" :loading="loading" :empty="!latestList.length">
        <FarmComparisonChart :latest-per-farm="latestList" />
      </ChartCard>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import ChartCard from './ChartCard.vue'
import TemperatureHumidityChart from './TemperatureHumidityChart.vue'
import PrecipitationChart from './PrecipitationChart.vue'
import SoilNutrientChart from './SoilNutrientChart.vue'
import FarmComparisonChart from './FarmComparisonChart.vue'

const props = defineProps({
  farms: { type: Array, default: () => [] },
})

const { showToast } = useToast()

const farmId = ref(null)
const loading = ref(false)
const timeSeries = ref([])
const latestList = ref([])
const farmNames = ref({})

watch(
  () => props.farms,
  (farms) => {
    const map = {}
    farms.forEach((f) => (map[f.id] = f.name))
    farmNames.value = map

    if (farms.length && !farmId.value) {
      farmId.value = farms[0].id
    }
  },
  { immediate: true },
)

async function loadData() {
  if (!farmId.value) return
  loading.value = true
  try {
    const data = await api.getChartData(farmId.value, 30)
    timeSeries.value = data.time_series
    latestList.value = data.latest_per_farm
  } catch (error) {
    timeSeries.value = []
    latestList.value = []
    showToast(error.message || '載入農場數據失敗', 'error')
  } finally {
    loading.value = false
  }
}

watch(farmId, loadData)
onMounted(loadData)
</script>
