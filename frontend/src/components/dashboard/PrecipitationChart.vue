<template>
  <Bar :data="chartData" :options="chartOptions" />
</template>

<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  BarElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from 'chart.js'
import { useChartTheme } from '@/composables/useChartTheme'

ChartJS.register(BarElement, LinearScale, CategoryScale, Tooltip, Legend)

const props = defineProps({
  timeSeries: { type: Array, required: true },
  farmNames: { type: Object, required: true },
})

const { gridColor, textColor } = useChartTheme()

function formatDateLabel(d) {
  return d.slice(5) // YYYY-MM-DD → MM-DD
}

const BAR_COLORS = ['#06b6d4', '#3b82f6', '#8b5cf6']

const chartData = computed(() => {
  const dates = [...new Set(props.timeSeries.map((d) => d.date))].sort()
  const farmIds = [...new Set(props.timeSeries.map((d) => d.farm_id))]

  const datasets = farmIds.map((fid, i) => {
    const farmData = props.timeSeries.filter((d) => d.farm_id === fid)
    const name = props.farmNames[fid] || `農場 ${fid}`

    return {
      label: name,
      data: dates.map((date) => farmData.find((d) => d.date === date)?.total_precipitation ?? 0),
      backgroundColor: BAR_COLORS[i % BAR_COLORS.length] + 'cc',
      borderColor: BAR_COLORS[i % BAR_COLORS.length],
      borderWidth: 1,
      borderRadius: 3,
    }
  })

  return {
    labels: dates.map((d) => formatDateLabel(d)),
    datasets,
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: textColor.value, boxWidth: 12, font: { size: 11 } },
    },
    tooltip: {
      callbacks: {
        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} mm`,
      },
    },
  },
  scales: {
    x: {
      ticks: { color: textColor.value, font: { size: 11 } },
      grid: { color: gridColor.value },
    },
    y: {
      title: { display: true, text: 'mm', color: textColor.value },
      ticks: { color: textColor.value },
      grid: { color: gridColor.value },
      beginAtZero: true,
    },
  },
}))
</script>
