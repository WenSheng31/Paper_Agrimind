<template>
  <Line :data="chartData" :options="chartOptions" />
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { useChartTheme } from '@/composables/useChartTheme'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Filler)

const props = defineProps({
  timeSeries: { type: Array, required: true },
  farmNames: { type: Object, required: true },
})

const { gridColor, textColor } = useChartTheme()

function formatDateLabel(d) {
  return d.slice(5) // YYYY-MM-DD → MM-DD
}

const TEMP_COLORS = ['#f97316', '#ef4444', '#eab308', '#ec4899', '#14b8a6', '#84cc16']
const HUMIDITY_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#6366f1', '#0ea5e9', '#a855f7']

const chartData = computed(() => {
  const dates = [...new Set(props.timeSeries.map((d) => d.date))].sort()
  const farmIds = [...new Set(props.timeSeries.map((d) => d.farm_id))]

  const datasets = []
  farmIds.forEach((fid, i) => {
    const farmData = props.timeSeries.filter((d) => d.farm_id === fid)
    const name = props.farmNames[fid] || `農場 ${fid}`

    datasets.push({
      label: `${name} 溫度`,
      data: dates.map((date) => farmData.find((d) => d.date === date)?.avg_temperature ?? null),
      borderColor: TEMP_COLORS[i % TEMP_COLORS.length],
      backgroundColor: TEMP_COLORS[i % TEMP_COLORS.length] + '20',
      yAxisID: 'y',
      tension: 0.3,
      pointRadius: 3,
    })

    datasets.push({
      label: `${name} 濕度`,
      data: dates.map((date) => farmData.find((d) => d.date === date)?.avg_humidity ?? null),
      borderColor: HUMIDITY_COLORS[i % HUMIDITY_COLORS.length],
      backgroundColor: HUMIDITY_COLORS[i % HUMIDITY_COLORS.length] + '20',
      borderDash: [5, 5],
      yAxisID: 'y1',
      tension: 0.3,
      pointRadius: 3,
    })
  })

  return {
    labels: dates.map((d) => formatDateLabel(d)),
    datasets,
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
      labels: { color: textColor.value, boxWidth: 12, font: { size: 11 } },
    },
  },
  scales: {
    x: {
      ticks: { color: textColor.value, font: { size: 11 } },
      grid: { color: gridColor.value },
    },
    y: {
      position: 'left',
      title: { display: true, text: '°C', color: textColor.value },
      ticks: { color: textColor.value },
      grid: { color: gridColor.value },
    },
    y1: {
      position: 'right',
      title: { display: true, text: '%', color: textColor.value },
      ticks: { color: textColor.value },
      grid: { drawOnChartArea: false },
      min: 0,
      max: 100,
    },
  },
}))
</script>
