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
        label: '氮 N (mg/kg)',
        data: props.latestPerFarm.map((f) => f.soil_n ?? 0),
        backgroundColor: '#10b981cc',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: '磷 P (mg/kg)',
        data: props.latestPerFarm.map((f) => f.soil_p ?? 0),
        backgroundColor: '#8b5cf6cc',
        borderColor: '#8b5cf6',
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: '鉀 K (mg/kg)',
        data: props.latestPerFarm.map((f) => f.soil_k ?? 0),
        backgroundColor: '#f59e0bcc',
        borderColor: '#f59e0b',
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
    tooltip: {
      callbacks: {
        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.x} mg/kg`,
      },
    },
  },
  scales: {
    x: {
      title: { display: true, text: 'mg/kg', color: textColor.value },
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
