<template>
  <div class="p-6">
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

    <div class="grid grid-cols-1 gap-4">
      <ChartCard title="土壤養分 (NPK)" :loading="loading" :empty="!latestList.length">
        <SoilNutrientChart :latest-per-farm="latestList" />
      </ChartCard>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import ChartCard from '@/components/dashboard/ChartCard.vue'
import TemperatureHumidityChart from '@/components/dashboard/TemperatureHumidityChart.vue'
import PrecipitationChart from '@/components/dashboard/PrecipitationChart.vue'
import SoilNutrientChart from '@/components/dashboard/SoilNutrientChart.vue'

const props = defineProps({
  farmId: { type: Number, required: true },
})

const { showToast } = useToast()

const loading = ref(false)
const timeSeries = ref([])
const latest = ref(null)

const farmNames = computed(() => {
  const map = {}
  timeSeries.value.forEach((d) => {
    if (!map[d.farm_id]) map[d.farm_id] = d.farm_name
  })
  return map
})

const latestList = computed(() => {
  return latest.value ? [latest.value] : []
})

async function loadData() {
  loading.value = true
  try {
    const data = await api.getFarmChartData(props.farmId, 30)
    timeSeries.value = data.time_series
    latest.value = data.latest
  } catch (error) {
    timeSeries.value = []
    latest.value = null
    showToast(error.message || '載入圖表數據失敗', 'error')
  } finally {
    loading.value = false
  }
}

watch(() => props.farmId, loadData)
onMounted(loadData)
</script>
