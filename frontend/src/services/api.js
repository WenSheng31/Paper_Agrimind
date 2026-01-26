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
        // 統一處理 401 Token 過期/無效
        if (response.status === 401) {
          localStorage.removeItem('token')
          throw {
            status: 401,
            message: '憑證過期，請重新登入',
          }
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

  // ===== Farm API =====
  async getFarms() {
    return this.request('/api/agriculture/farms')
  }

  async getFarm(farmId) {
    return this.request(`/api/agriculture/farms/${farmId}`)
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
    return this.request(`/api/agriculture/farms/${farmId}/sensor-data?page=${page}&page_size=${pageSize}`)
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
    return this.request(`/api/agriculture/farms/${farmId}/operations?page=${page}&page_size=${pageSize}`)
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
      tool_calls: data.tool_used
        ? [
            {
              name: data.tool_used.tool_name,
              input: data.tool_used.tool_args,
              output: data.tool_used.tool_output,
            },
          ]
        : [],
    }
  }

  async getTools() {
    return this.api.request('/api/ai/tools')
  }
}

const apiService = new ApiService()
export const aiAPI = new AiService(apiService)
export default apiService
