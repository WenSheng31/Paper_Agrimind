import { driver } from 'driver.js'
import 'driver.js/dist/driver.css'

const STORAGE_PREFIX = 'argimind-tour-'

const tours = {
  home: [
    {
      element: '#sidebar-nav',
      popover: {
        title: '導航選單',
        description: '從這裡切換首頁、農場管理和知識庫頁面。',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '#ai-summary',
      popover: {
        title: 'AI 智慧總結',
        description: '點擊按鈕讓 AI 自動分析所有農場的最新狀態，產生摘要與建議。',
        side: 'bottom',
        align: 'start',
      },
    },
    {
      element: '#dashboard-charts',
      popover: {
        title: '數據圖表',
        description: '查看各農場的溫度、濕度、降水量及土壤養分趨勢圖。',
        side: 'top',
        align: 'start',
      },
    },
    {
      element: '#ai-chat-btn',
      popover: {
        title: 'AI 助手',
        description: '點擊開啟 AI 聊天，可用文字或語音提問農業相關問題。',
        side: 'left',
        align: 'end',
      },
    },
  ],
  farmDetail: [
    {
      element: '#farm-info',
      popover: {
        title: '農場資訊',
        description: '這裡顯示農場的基本資料。',
        side: 'bottom',
        align: 'start',
      },
    },
    {
      element: '#farm-ai-summary',
      popover: {
        title: 'AI 農場分析',
        description: '讓 AI 根據這個農場的感測器資料與農務記錄，產生狀態總結與建議。',
        side: 'bottom',
        align: 'start',
      },
    },
    {
      element: '#farm-tabs',
      popover: {
        title: '感測器與農務記錄',
        description: '切換查看感測器數據（溫度、濕度、土壤等）和農務操作記錄。',
        side: 'top',
        align: 'start',
      },
    },
  ],
}

export function useOnboardingTour(tourName = 'home') {
  const storageKey = STORAGE_PREFIX + tourName

  const hasSeenTour = () => localStorage.getItem(storageKey) === 'true'

  const startTour = (force = false) => {
    if (!force && hasSeenTour()) return

    const steps = tours[tourName]
    if (!steps) return

    const driverObj = driver({
      showProgress: true,
      animate: true,
      nextBtnText: '下一步',
      prevBtnText: '上一步',
      doneBtnText: '知道了',
      progressText: '{{current}} / {{total}}',
      onDestroyed: () => {
        localStorage.setItem(storageKey, 'true')
      },
      steps,
    })

    driverObj.drive()
  }

  return { startTour, hasSeenTour }
}
