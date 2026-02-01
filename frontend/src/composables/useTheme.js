import { ref, watchEffect } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'system')

// 系統主題監聽器只綁定一次
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
mediaQuery.addEventListener('change', (e) => {
  if (theme.value === 'system') {
    const root = window.document.documentElement
    if (e.matches) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }
})

export function useTheme() {
  const toggleTheme = () => {
    if (theme.value === 'light') {
      theme.value = 'dark'
    } else if (theme.value === 'dark') {
      theme.value = 'system'
    } else {
      theme.value = 'light'
    }
  }

  const setTheme = (newTheme) => {
    theme.value = newTheme
  }

  watchEffect(() => {
    const root = window.document.documentElement
    const systemDark = mediaQuery.matches

    root.classList.remove('dark')

    if (theme.value === 'dark' || (theme.value === 'system' && systemDark)) {
      root.classList.add('dark')
    }

    localStorage.setItem('theme', theme.value)
  })

  return {
    theme,
    toggleTheme,
    setTheme,
  }
}
