import { reactive } from 'vue'

// 全局 toast 狀態
export const toastState = reactive({
  toasts: [],
})

let toastId = 0

export function useToast() {
  // 顯示 Toast 訊息
  function showToast(message, type = 'success') {
    const id = toastId++
    toastState.toasts.push({
      id,
      type,
      message,
    })

    // 3 秒後自動移除
    setTimeout(() => {
      removeToast(id)
    }, 3000)
  }

  // 移除 toast
  function removeToast(id) {
    const index = toastState.toasts.findIndex((t) => t.id === id)
    if (index > -1) {
      toastState.toasts.splice(index, 1)
    }
  }

  return {
    showToast,
    removeToast,
  }
}
