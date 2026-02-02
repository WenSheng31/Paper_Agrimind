import { ref, watchEffect } from 'vue'

const isDark = ref(document.documentElement.classList.contains('dark'))

// 監聽 dark class 變化
const observer = new MutationObserver(() => {
  isDark.value = document.documentElement.classList.contains('dark')
})
observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

export function useChartTheme() {
  const gridColor = ref('')
  const textColor = ref('')

  watchEffect(() => {
    gridColor.value = isDark.value ? '#334155' : '#e2e8f0'
    textColor.value = isDark.value ? '#94a3b8' : '#64748b'
  })

  return { isDark, gridColor, textColor }
}
