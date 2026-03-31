const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  getAuthHeader() {
    const token = localStorage.getItem('token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader(),
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json().catch(() => null)

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/login'
          throw { status: 401, message: '登入已過期，請重新登入' }
        }

        throw {
          status: response.status,
          message: data?.detail || '請求失敗',
          data,
        }
      }

      return data
    } catch (error) {
      if (error.status) throw error
      throw {
        status: 0,
        message: '網路連線錯誤',
        error,
      }
    }
  }

  // ===== Auth API =====
  async register(userData) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  async login(credentials) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
  }

  async getMe() {
    return this.request('/api/auth/me')
  }

  async getDashboardStats() {
    return this.request('/api/agriculture/dashboard/stats')
  }

  async getDashboardOverview(days = 30) {
    return this.request(`/api/agriculture/dashboard/overview?days=${days}`)
  }

  // ===== Farm API =====
  async getFarms() {
    return this.request('/api/agriculture/farms')
  }

  async getFarm(farmId) {
    return this.request(`/api/agriculture/farms/${farmId}`)
  }

  async getFarmChartData(farmId, days = 30) {
    return this.request(`/api/agriculture/farms/${farmId}/chart-data?days=${days}`)
  }

  async createFarm(farmData) {
    return this.request('/api/agriculture/farms', {
      method: 'POST',
      body: JSON.stringify(farmData),
    })
  }

  async updateFarm(farmId, farmData) {
    return this.request(`/api/agriculture/farms/${farmId}`, {
      method: 'PUT',
      body: JSON.stringify(farmData),
    })
  }

  async deleteFarm(farmId) {
    return this.request(`/api/agriculture/farms/${farmId}`, {
      method: 'DELETE',
    })
  }

  // ===== Sensor Data API =====
  async getSensorData(farmId, page = 1, pageSize = 10) {
    return this.request(
      `/api/agriculture/farms/${farmId}/sensor-data?page=${page}&page_size=${pageSize}`,
    )
  }

  async createSensorData(farmId, sensorData) {
    return this.request(`/api/agriculture/farms/${farmId}/sensor-data`, {
      method: 'POST',
      body: JSON.stringify(sensorData),
    })
  }

  async deleteSensorData(dataId) {
    return this.request(`/api/agriculture/sensor-data/${dataId}`, {
      method: 'DELETE',
    })
  }

  // ===== Operation API =====
  async getOperations(farmId, page = 1, pageSize = 10) {
    return this.request(
      `/api/agriculture/farms/${farmId}/operations?page=${page}&page_size=${pageSize}`,
    )
  }

  async createOperation(farmId, operationData) {
    return this.request(`/api/agriculture/farms/${farmId}/operations`, {
      method: 'POST',
      body: JSON.stringify(operationData),
    })
  }

  async updateOperation(opId, operationData) {
    return this.request(`/api/agriculture/operations/${opId}`, {
      method: 'PUT',
      body: JSON.stringify(operationData),
    })
  }

  async deleteOperation(opId) {
    return this.request(`/api/agriculture/operations/${opId}`, {
      method: 'DELETE',
    })
  }

  // ===== Image Record API =====
  async getImageRecords(page = 1, pageSize = 12, farmId = null) {
    const params = new URLSearchParams({ page, page_size: pageSize })
    if (farmId) params.append('farm_id', farmId)
    return this.request(`/api/image-records?${params}`)
  }

  async getImageRecord(id) {
    return this.request(`/api/image-records/${id}`)
  }

  async createImageRecord(farmId, description, files) {
    const formData = new FormData()
    formData.append('farm_id', farmId)
    if (description) formData.append('description', description)
    for (const file of files) {
      formData.append('files', file)
    }
    const url = `${this.baseURL}/api/image-records`
    const response = await fetch(url, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: formData,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      throw { status: response.status, message: data?.detail || '上傳失敗' }
    }
    return data
  }

  async updateImageRecord(id, updateData) {
    return this.request(`/api/image-records/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    })
  }

  async deleteImageRecord(id) {
    return this.request(`/api/image-records/${id}`, {
      method: 'DELETE',
    })
  }

  async addImageRecordImages(recordId, files) {
    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }
    const url = `${this.baseURL}/api/image-records/${recordId}/images`
    const response = await fetch(url, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: formData,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      throw { status: response.status, message: data?.detail || '上傳失敗' }
    }
    return data
  }

  async analyzeImageRecord(recordId) {
    return this.request(`/api/image-records/${recordId}/analysis`)
  }

  async deleteImageRecordImage(recordId, imageId) {
    return this.request(`/api/image-records/${recordId}/images/${imageId}`, {
      method: 'DELETE',
    })
  }

  // ===== Knowledge API =====
  async getKnowledgeDocuments(page = 1, pageSize = 10) {
    return this.request(`/api/knowledge/?page=${page}&page_size=${pageSize}`)
  }

  async uploadKnowledgeText(title, content) {
    return this.request('/api/knowledge/upload/text', {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    })
  }

  async uploadKnowledgePdf(title, file) {
    const formData = new FormData()
    formData.append('title', title)
    formData.append('file', file)
    const url = `${this.baseURL}/api/knowledge/upload/pdf`
    const response = await fetch(url, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: formData,
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      throw { status: response.status, message: data?.detail || '上傳失敗' }
    }
    return data
  }

  async getKnowledgeChunks(title) {
    return this.request(`/api/knowledge/${encodeURIComponent(title)}/chunks`)
  }

  async deleteKnowledge(title) {
    return this.request(`/api/knowledge/${encodeURIComponent(title)}`, {
      method: 'DELETE',
    })
  }

  // ===== Chat Logs API (Admin) =====
  async getChatSessions(page = 1, pageSize = 10, userId = null) {
    const params = new URLSearchParams({ page, page_size: pageSize })
    if (userId) params.append('user_id', userId)
    return this.request(`/api/admin/chat-logs?${params}`)
  }

  async getChatSessionMessages(sessionId) {
    return this.request(`/api/admin/chat-logs/${encodeURIComponent(sessionId)}`)
  }

  async deleteChatSession(sessionId) {
    return this.request(`/api/admin/chat-logs/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    })
  }

  async deleteChatSessionsBatch(sessionIds) {
    return this.request('/api/admin/chat-logs/batch-delete', {
      method: 'POST',
      body: JSON.stringify({ session_ids: sessionIds }),
    })
  }

  // ===== Task Progress API =====
  async getTaskProgress() {
    return this.request('/api/task-progress')
  }

  async updateTaskProgress(data) {
    return this.request('/api/task-progress', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getAllTaskProgress() {
    return this.request('/api/task-progress/all')
  }

  async resetTaskProgress(userId) {
    return this.request(`/api/task-progress/${userId}`, { method: 'DELETE' })
  }

  // ===== Admin Users API =====
  async getUsers() {
    return this.request('/api/admin/users')
  }

  async deleteUser(userId) {
    return this.request(`/api/admin/users/${userId}`, { method: 'DELETE' })
  }

  async toggleUserActive(userId) {
    return this.request(`/api/admin/users/${userId}/toggle-active`, { method: 'PUT' })
  }

  async toggleUserAdmin(userId) {
    return this.request(`/api/admin/users/${userId}/toggle-admin`, { method: 'PUT' })
  }

  async resetUserPassword(userId, password) {
    return this.request(`/api/admin/users/${userId}/reset-password`, {
      method: 'PUT',
      body: JSON.stringify({ password }),
    })
  }

  async createUser(userData) {
    return this.request('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }
}

// ===== AI API =====
class AiService {
  constructor(apiService) {
    this.api = apiService
  }

  // 單次查詢（不保留對話歷史）
  async ask(query) {
    const tempSessionId = `temp-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    const data = await this.api.request('/api/ai/query', {
      method: 'POST',
      body: JSON.stringify({
        query,
        session_id: tempSessionId,
      }),
    })
    return data.response
  }

  // 對話式查詢（保留對話歷史）
  async chat(query, sessionId) {
    const data = await this.api.request('/api/ai/query', {
      method: 'POST',
      body: JSON.stringify({
        query,
        session_id: sessionId,
      }),
    })

    return {
      content: data.response,
      tool_calls: Array.isArray(data.tool_used)
        ? data.tool_used.map((t) => ({
            name: t.tool_name,
            input: t.tool_args,
            output: t.tool_output,
          }))
        : [],
    }
  }

  // 串流對話查詢（SSE）
  async chatStream(query, sessionId, { onToolStart, onToolEnd, onTextDelta, onDone, onError, images = [] }) {
    const url = `${this.api.baseURL}/api/ai/stream`
    const body = { query, session_id: sessionId }
    if (images.length > 0) {
      body.images = images
    }
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 120000)
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.api.getAuthHeader(),
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        throw { status: 401, message: '登入已過期，請重新登入' }
      }
      const data = await response.json().catch(() => null)
      throw {
        status: response.status,
        message: data?.detail || '請求失敗',
      }
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      // 保留最後一個不完整的行
      buffer = lines.pop()

      let eventType = null
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim()
        } else if (line.startsWith('data: ') && eventType) {
          const data = JSON.parse(line.slice(6))
          if (eventType === 'tool_start') onToolStart?.(data)
          else if (eventType === 'tool_end') onToolEnd?.(data)
          else if (eventType === 'text_delta') onTextDelta?.(data)
          else if (eventType === 'done') onDone?.(data)
          else if (eventType === 'error') onError?.(data)
          eventType = null
        }
      }
    }
    clearTimeout(timeout)
  }

  async getTools() {
    return this.api.request('/api/ai/tools')
  }
}

const apiService = new ApiService()
export const aiAPI = new AiService(apiService)
export default apiService
