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
        title: '感測器、農務與影像紀錄',
        description: '切換查看感測器數據、農務操作記錄，以及田間影像紀錄與 AI 分析。',
        side: 'top',
        align: 'start',
      },
    },
  ],
  knowledge: [
    {
      element: '#knowledge-table',
      popover: {
        title: '知識文件列表',
        description: '點擊標題可展開查看文件片段內容，也可刪除不需要的文件。',
        side: 'top',
        align: 'start',
      },
    },
    {
      element: '#knowledge-upload-btn',
      popover: {
        title: '新增知識',
        description: '上傳文字或 PDF 文件，系統會自動分段並建立向量索引，供 AI 助手搜尋參考。',
        side: 'bottom',
        align: 'end',
      },
    },
    {
      element: '#ai-chat-btn',
      popover: {
        title: 'AI 助手',
        description: 'AI 助手會自動搜尋知識庫中的相關內容來回答你的問題。',
        side: 'left',
        align: 'end',
      },
    },
  ],
  imageRecords: [
    {
      element: '#image-records-filter',
      popover: {
        title: '農場篩選',
        description: '選擇特定農場來篩選影像紀錄，或查看所有農場的紀錄。',
        side: 'bottom',
        align: 'end',
      },
    },
    {
      element: '#image-records-grid',
      popover: {
        title: '影像紀錄列表',
        description: '點擊卡片查看詳情，AI 會自動分析圖片中的作物狀況並給出建議。',
        side: 'top',
        align: 'start',
      },
    },
    {
      element: '#ai-chat-btn',
      popover: {
        title: 'AI 助手',
        description: 'AI 助手也能查詢影像紀錄並分析圖片，試試問它農場的作物狀況。',
        side: 'left',
        align: 'end',
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
