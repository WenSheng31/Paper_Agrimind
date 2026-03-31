import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const SESSION_DECIDED_KEY = 'argimind-task-decided'
const SESSION_ACTIVE_KEY = 'argimind-task-active'

export const QUESTIONNAIRE_URL = 'https://forms.gle/mmJdpt1RCdgiAZKS8'
export const TOTAL_TASKS = 9

const tasks = [
  {
    id: 1,
    title: '瀏覽系統總覽',
    description:
      '請瀏覽首頁，了解目前農場的整體狀況。頁面上方有 AI 智慧分析功能，可自動為你總結所有農場的最新狀態。',
    route: { name: 'home' },
    routeLabel: '前往首頁',
    detectType: 'route',
    detectValue: '/home',
  },
  {
    id: 2,
    title: '查看農場詳細資料',
    description:
      '請選擇一個農場，進入該農場頁面，查看感測器數據（溫度、濕度、土壤養分等）與農務操作紀錄。',
    route: { name: 'farms' },
    routeLabel: '前往農場列表',
    detectType: 'route',
    detectValue: '/farms/',
  },
  {
    id: 3,
    title: '瀏覽農場詳情分頁',
    description:
      '在農場詳情頁面中，請點擊任一分頁（感測器數據、農務紀錄、影像紀錄等）來查看不同類型的資料。',
    detectType: 'event',
    detectEvent: 'task-tab-clicked',
  },
  {
    id: 4,
    title: '查看影像紀錄',
    description: '請進入影像紀錄頁面，點擊任何一筆紀錄查看詳細內容與 AI 分析結果。',
    route: { name: 'image-records' },
    routeLabel: '前往影像紀錄',
    detectType: 'event',
    detectEvent: 'task-image-viewed',
  },
  {
    id: 5,
    title: '詢問農場現況',
    description: '假設你想快速了解某個農場目前的狀況，請透過 AI 助手提問。',
    question: '請幫我看看目前各農場的土壤養分狀況如何？',
    detectType: 'event',
    detectEvent: 'task-ai-responded',
  },
  {
    id: 6,
    title: '查詢天氣資訊',
    description: '假設你明天打算進行田間作業，想先確認天氣狀況，請透過 AI 助手查詢。',
    question: '台中市未來一週的天氣如何？',
    detectType: 'event',
    detectEvent: 'task-ai-responded',
  },
  {
    id: 7,
    title: '查詢農產品行情',
    description: '假設你想了解最近某種作物的市場批發價格，請透過 AI 助手查詢。',
    question: '最近番茄的批發價格怎麼樣？',
    detectType: 'event',
    detectEvent: 'task-ai-responded',
  },
  {
    id: 8,
    title: '查詢農業知識',
    description:
      '假設你的作物出現了某種異常（如葉片發黃、蟲害等），想了解可能的原因與防治方法，請透過 AI 助手提問。',
    question: '草莓常見的病蟲害有哪些？怎麼防治？',
    detectType: 'event',
    detectEvent: 'task-ai-responded',
  },
  {
    id: 9,
    title: '綜合情境諮詢',
    description:
      '假設你正在考慮這幾天是否該施肥或噴藥，請透過 AI 助手，綜合考量農場土壤狀況與天氣預報，給你具體建議。',
    question: '根據芒果農場目前的土壤數據和這週天氣，你建議我怎麼施肥？',
    detectType: 'event',
    detectEvent: 'task-ai-responded',
  },
]

// 單例狀態
const hasDecided = sessionStorage.getItem(SESSION_DECIDED_KEY) === 'true'
const wasActive = sessionStorage.getItem(SESSION_ACTIVE_KEY) === 'true'

const showWelcome = ref(!hasDecided)
const isActive = ref(hasDecided && wasActive)
const currentStep = ref(0)
const isCompleted = ref(false)
const initialized = ref(false)
const fulfilled = ref(false)

let eventCleanup = null

function cleanupDetection() {
  if (eventCleanup) {
    eventCleanup()
    eventCleanup = null
  }
}

function setupDetection(task, router) {
  cleanupDetection()
  fulfilled.value = false

  if (!task) return

  // 設定偵測
  if (task.detectType === 'route') {
    // 先檢查當前路由是否已符合
    if (router.currentRoute.value.path.startsWith(task.detectValue)) {
      fulfilled.value = true
    }
    // 監聽路由變化
    const unwatch = router.afterEach((to) => {
      if (to.path.startsWith(task.detectValue)) {
        fulfilled.value = true
        cleanupDetection()
      }
    })
    eventCleanup = unwatch
  } else if (task.detectType === 'event') {
    const handler = () => {
      fulfilled.value = true
      cleanupDetection()
    }
    window.addEventListener(task.detectEvent, handler)
    eventCleanup = () => window.removeEventListener(task.detectEvent, handler)
  }
}

// 初始化：從後端載入進度
async function loadProgress() {
  if (initialized.value) return
  try {
    const data = await api.getTaskProgress()
    currentStep.value = data.current_step
    isCompleted.value = data.is_completed
    // 已完成任務則跳過歡迎頁
    if (data.is_completed) {
      showWelcome.value = false
      isActive.value = false
      sessionStorage.setItem(SESSION_DECIDED_KEY, 'true')
      sessionStorage.setItem(SESSION_ACTIVE_KEY, 'false')
    }
  } catch {
    currentStep.value = 0
    isCompleted.value = false
    isActive.value = false
    showWelcome.value = true
    sessionStorage.removeItem(SESSION_DECIDED_KEY)
    sessionStorage.removeItem(SESSION_ACTIVE_KEY)
  }
  initialized.value = true
}

// 背景同步到後端
function syncToBackend() {
  api
    .updateTaskProgress({
      current_step: currentStep.value,
      is_completed: isCompleted.value,
    })
    .catch(() => {})
}

export function useTaskGuide() {
  const router = useRouter()

  const currentTask = computed(() => tasks[currentStep.value] ?? null)
  const progress = computed(
    () => `${Math.min(currentStep.value + 1, tasks.length)} / ${tasks.length}`,
  )
  const progressPercent = computed(() =>
    isCompleted.value ? 100 : (currentStep.value / tasks.length) * 100,
  )

  // 當任務步驟變化時重新設定偵測
  watch(
    [currentStep, isActive],
    () => {
      if (isActive.value && !isCompleted.value) {
        setupDetection(currentTask.value, router)
      } else {
        cleanupDetection()
      }
    },
    { immediate: true },
  )

  function startExperience() {
    showWelcome.value = false
    isActive.value = true
    sessionStorage.setItem(SESSION_DECIDED_KEY, 'true')
    sessionStorage.setItem(SESSION_ACTIVE_KEY, 'true')
    syncToBackend()
  }

  function skipExperience() {
    showWelcome.value = false
    isActive.value = false
    sessionStorage.setItem(SESSION_DECIDED_KEY, 'true')
    sessionStorage.setItem(SESSION_ACTIVE_KEY, 'false')
  }

  function endExperience() {
    isActive.value = false
    cleanupDetection()
    sessionStorage.setItem(SESSION_ACTIVE_KEY, 'false')
  }

  function resetState() {
    currentStep.value = 0
    isCompleted.value = false
    isActive.value = false
    showWelcome.value = true
    initialized.value = false
    fulfilled.value = false
    cleanupDetection()
    sessionStorage.removeItem(SESSION_DECIDED_KEY)
    sessionStorage.removeItem(SESSION_ACTIVE_KEY)
  }

  function completeCurrentTask() {
    if (!fulfilled.value) return
    if (currentStep.value >= tasks.length - 1) {
      currentStep.value = tasks.length
      isCompleted.value = true
    } else {
      currentStep.value++
    }
    fulfilled.value = false
    syncToBackend()
  }

  function goBack() {
    if (currentStep.value > 0) {
      isCompleted.value = false
      currentStep.value--
      fulfilled.value = false
      syncToBackend()
    }
  }

  return {
    tasks,
    currentStep,
    currentTask,
    isCompleted,
    isActive,
    showWelcome,
    progress,
    progressPercent,
    fulfilled,
    loadProgress,
    startExperience,
    skipExperience,
    endExperience,
    completeCurrentTask,
    goBack,
    resetState,
  }
}
