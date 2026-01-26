import { ref, watchEffect } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'system')

export function useTheme() {
  // 切換主題
  const toggleTheme = () => {
    if (theme.value === 'light') {
      theme.value = 'dark'
    } else if (theme.value === 'dark') {
      theme.value = 'system'
    } else {
      theme.value = 'light'
    }
  }

  // 設定指定主題
  const setTheme = (newTheme) => {
    theme.value = newTheme
  }

  // 監聽主題變化並應用到 DOM
  watchEffect(() => {
    const root = window.document.documentElement
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches

    // 移除舊的設定
    root.classList.remove('dark')

    // 決定是否應用 dark class
    if (theme.value === 'dark' || (theme.value === 'system' && systemDark)) {
      root.classList.add('dark')
    }

    // 儲存設定
    localStorage.setItem('theme', theme.value)
  })

  // 監聽系統主題變更 (當處於 system 模式時自動切換)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (theme.value === 'system') {
      const root = window.document.documentElement
      if (e.matches) {
        root.classList.add('dark')
      } else {
        root.classList.remove('dark')
      }
    }
  })

  return {
    theme,
    toggleTheme,
    setTheme,
  }
}
