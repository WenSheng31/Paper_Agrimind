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
  latestPerFarm: { type: Array, required: true },
})

const { gridColor, textColor } = useChartTheme()

const chartData = computed(() => {
  const labels = props.latestPerFarm.map((f) => f.farm_name)

  return {
    labels,
    datasets: [
      {
        label: '溫度 (°C)',
        data: props.latestPerFarm.map((f) => f.temperature ?? 0),
        backgroundColor: '#f97316cc',
        borderColor: '#f97316',
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: '濕度 (%)',
        data: props.latestPerFarm.map((f) => f.humidity ?? 0),
        backgroundColor: '#3b82f6cc',
        borderColor: '#3b82f6',
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: '土壤濕度 (%)',
        data: props.latestPerFarm.map((f) => f.soil_moisture ?? 0),
        backgroundColor: '#10b981cc',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 3,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: textColor.value, boxWidth: 12, font: { size: 11 } },
    },
  },
  scales: {
    x: {
      ticks: { color: textColor.value },
      grid: { color: gridColor.value },
      beginAtZero: true,
    },
    y: {
      ticks: { color: textColor.value, font: { size: 11 } },
      grid: { color: gridColor.value },
    },
  },
}))
</script>
