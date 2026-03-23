import axios from 'axios'

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001/api',
  timeout: 10000
})

// Response error interceptor
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    if (error.name !== 'CanceledError' && error.code !== 'ERR_CANCELED') {
      console.error('API Error:', error.message, error.config?.url)
    }
    return Promise.reject(error)
  }
)

export function isAbortError(err) {
  return err.name === 'AbortError' || err.name === 'CanceledError'
}

function buildFilterParams(filters = {}) {
  const params = new URLSearchParams()
  if (filters.warehouse && filters.warehouse !== 'all') params.append('warehouse', filters.warehouse)
  if (filters.category && filters.category !== 'all') params.append('category', filters.category)
  if (filters.status && filters.status !== 'all') params.append('status', filters.status)
  if (filters.month && filters.month !== 'all') params.append('month', filters.month)
  return params
}

export const api = {
  async getInventory(filters = {}, signal) {
    const params = buildFilterParams(filters)
    const response = await axiosInstance.get(`/inventory?${params.toString()}`, { signal })
    return response.data.items || response.data
  },

  async getInventoryItem(id) {
    const response = await axiosInstance.get(`/inventory/${id}`)
    return response.data
  },

  async getOrders(filters = {}, signal) {
    const params = buildFilterParams(filters)
    const response = await axiosInstance.get(`/orders?${params.toString()}`, { signal })
    return response.data.items || response.data
  },

  async getOrder(id) {
    const response = await axiosInstance.get(`/orders/${id}`)
    return response.data
  },

  async getDemandForecasts() {
    const response = await axiosInstance.get('/demand')
    return response.data
  },

  async getBacklog() {
    const response = await axiosInstance.get('/backlog')
    return response.data
  },

  async getDashboardSummary(filters = {}) {
    const params = buildFilterParams(filters)
    const response = await axiosInstance.get(`/dashboard/summary?${params.toString()}`)
    return response.data
  },

  async getSpendingSummary() {
    const response = await axiosInstance.get('/spending/summary')
    return response.data
  },

  async getMonthlySpending() {
    const response = await axiosInstance.get('/spending/monthly')
    return response.data
  },

  async getCategorySpending() {
    const response = await axiosInstance.get('/spending/categories')
    return response.data
  },

  async getTransactions() {
    const response = await axiosInstance.get('/spending/transactions')
    return response.data.items || response.data
  },

  async getTasks() {
    const response = await axiosInstance.get('/tasks')
    return response.data
  },

  async createTask(taskData) {
    const response = await axiosInstance.post('/tasks', taskData)
    return response.data
  },

  async deleteTask(taskId) {
    const response = await axiosInstance.delete(`/tasks/${taskId}`)
    return response.data
  },

  async toggleTask(taskId) {
    const response = await axiosInstance.patch(`/tasks/${taskId}`)
    return response.data
  },

  async createPurchaseOrder(purchaseOrderData) {
    const response = await axiosInstance.post('/purchase-orders', purchaseOrderData)
    return response.data
  },

  async getPurchaseOrderByBacklogItem(backlogItemId) {
    const response = await axiosInstance.get(`/purchase-orders/${backlogItemId}`)
    return response.data
  },

  async getRestockingRecommendations(budget) {
    const response = await axiosInstance.get('/restocking/recommendations', { params: { budget } })
    return response.data
  },

  async createRestockingOrder(orderData) {
    const response = await axiosInstance.post('/restocking/orders', orderData)
    return response.data
  },

  async getRestockingOrders() {
    const response = await axiosInstance.get('/restocking/orders')
    return response.data
  },

  async getQuarterlyReports() {
    const response = await axiosInstance.get('/reports/quarterly')
    return response.data
  },

  async getMonthlyTrends() {
    const response = await axiosInstance.get('/reports/monthly-trends')
    return response.data
  },

  async searchInventoryAdvanced(query, filters = {}, page = 1, pageSize = 50) {
    const params = buildFilterParams(filters)
    if (query) params.append('q', query)
    if (page) params.append('page', page)
    if (pageSize) params.append('page_size', pageSize)
    const response = await axiosInstance.get(`/inventory/search?${params.toString()}`)
    return response.data
  },

  async getInventoryAnalytics(warehouseId, dateRange, groupBy = 'category') {
    const params = new URLSearchParams()
    if (warehouseId) params.append('warehouse_id', warehouseId)
    if (dateRange && dateRange.start) {
      params.append('start_date', dateRange.start)
      params.append('end_date', dateRange.end || new Date().toISOString())
    }
    if (groupBy) params.append('group_by', groupBy)
    const response = await axiosInstance.get(`/inventory/analytics?${params.toString()}`)
    return response.data
  }
}
