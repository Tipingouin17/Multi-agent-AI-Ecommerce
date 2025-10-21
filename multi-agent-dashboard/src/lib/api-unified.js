/**
 * Unified API Service for Multi-Agent E-commerce Platform
 * Connects to the unified API server on port 8000
 */

import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

// Create axios instance
const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor for authentication
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
    }
    
    return Promise.reject(error)
  }
)

// API Service Class
class UnifiedApiService {
  
  // Health check
  async healthCheck() {
    const response = await client.get('/health')
    return response.data
  }

  // Products
  async getProducts(params = {}) {
    const response = await client.get('/products', { params })
    return response.data
  }

  async getProduct(productId) {
    const response = await client.get(`/products/${productId}`)
    return response.data
  }

  async createProduct(productData) {
    const response = await client.post('/products', productData)
    return response.data
  }

  // Customers
  async getCustomers(params = {}) {
    const response = await client.get('/customers', { params })
    return response.data
  }

  async getCustomer(customerId) {
    const response = await client.get(`/customers/${customerId}`)
    return response.data
  }

  // Orders
  async getOrders(params = {}) {
    const response = await client.get('/orders', { params })
    return response.data
  }

  async getOrder(orderId) {
    const response = await client.get(`/orders/${orderId}`)
    return response.data
  }

  // Warehouses
  async getWarehouses() {
    const response = await client.get('/warehouses')
    return response.data
  }

  async getWarehouse(warehouseId) {
    const response = await client.get(`/warehouses/${warehouseId}`)
    return response.data
  }

  // Inventory
  async getInventory(params = {}) {
    const response = await client.get('/inventory', { params })
    return response.data
  }

  // Dashboard metrics
  async getDashboardMetrics() {
    const response = await client.get('/metrics/dashboard')
    return response.data
  }

  // Agents
  async getAgentsStatus() {
    const response = await client.get('/agents')
    return response.data
  }

  // System health
  async getSystemHealth() {
    const response = await client.get('/system/health')
    return response.data
  }
}

// Export singleton instance
export default new UnifiedApiService()

