/**
 * Enhanced API Service for Multi-Agent E-commerce Dashboard
 * 
 * This service provides comprehensive API integration with all backend agents
 * including error handling, request/response interceptors, and retry logic.
 */

import axios from 'axios'

// Use relative URL to work with Vite proxy and ngrok
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.config.url} - ${response.status}`)
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        // Attempt to refresh token
        const refreshToken = localStorage.getItem('refresh_token')
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken
        })
        
        const { access_token } = response.data
        localStorage.setItem('auth_token', access_token)
        
        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Helper function for handling API calls
const handleApiCall = async (apiCall) => {
  try {
    const response = await apiCall()
    return response.data
  } catch (error) {
    throw {
      message: error.response?.data?.detail || error.message,
      status: error.response?.status,
      data: error.response?.data
    }
  }
}

// ============================================================================
// SYSTEM & MONITORING APIs
// ============================================================================

export const systemApi = {
  // Get system overview
  getOverview: () => handleApiCall(() => 
    apiClient.get('/api/system/overview')
  ),

  // Get system health
  getHealth: () => handleApiCall(() => 
    apiClient.get('/api/system/health')
  ),

  // Get system metrics
  getMetrics: (timeRange = '24h') => handleApiCall(() => 
    apiClient.get('/api/system/metrics', { params: { range: timeRange } })
  ),

  // Get system configuration
  getConfiguration: () => handleApiCall(() => 
    apiClient.get('/api/system/config')
  ),

  // Update system configuration
  updateConfiguration: (config) => handleApiCall(() => 
    apiClient.put('/api/system/config', config)
  ),
}

// ============================================================================
// AGENT APIs
// ============================================================================

export const agentApi = {
  // Get all agents status
  getAllAgents: () => handleApiCall(() => 
    apiClient.get('/api/agents')
  ),

  // Get specific agent status
  getAgent: (agentId) => handleApiCall(() => 
    apiClient.get(`/api/agents/${agentId}`)
  ),

  // Get agent metrics
  getAgentMetrics: (agentId, timeRange = '24h') => handleApiCall(() => 
    apiClient.get(`/api/agents/${agentId}/metrics`, { params: { range: timeRange } })
  ),

  // Get agent logs
  getAgentLogs: (agentId, limit = 100) => handleApiCall(() => 
    apiClient.get(`/api/agents/${agentId}/logs`, { params: { limit } })
  ),

  // Start agent
  startAgent: (agentId) => handleApiCall(() => 
    apiClient.post(`/api/agents/${agentId}/start`)
  ),

  // Stop agent
  stopAgent: (agentId) => handleApiCall(() => 
    apiClient.post(`/api/agents/${agentId}/stop`)
  ),

  // Restart agent
  restartAgent: (agentId) => handleApiCall(() => 
    apiClient.post(`/api/agents/${agentId}/restart`)
  ),

  // Get agent configuration
  getAgentConfig: (agentId) => handleApiCall(() => 
    apiClient.get(`/api/agents/${agentId}/config`)
  ),

  // Update agent configuration
  updateAgentConfig: (agentId, config) => handleApiCall(() => 
    apiClient.put(`/api/agents/${agentId}/config`, config)
  ),
}

// ============================================================================
// ALERT APIs
// ============================================================================

export const alertApi = {
  // Get all alerts
  getAlerts: (params = {}) => handleApiCall(() => 
    apiClient.get('/api/alerts', { params })
  ),

  // Get alert by ID
  getAlert: (alertId) => handleApiCall(() => 
    apiClient.get(`/api/alerts/${alertId}`)
  ),

  // Acknowledge alert
  acknowledgeAlert: (alertId) => handleApiCall(() => 
    apiClient.post(`/api/alerts/${alertId}/acknowledge`)
  ),

  // Resolve alert
  resolveAlert: (alertId, resolution) => handleApiCall(() => 
    apiClient.post(`/api/alerts/${alertId}/resolve`, { resolution })
  ),

  // Get alert statistics
  getAlertStats: (timeRange = '24h') => handleApiCall(() => 
    apiClient.get('/api/alerts/stats', { params: { range: timeRange } })
  ),
}

// ============================================================================
// ORDER APIs
// ============================================================================

export const orderApi = {
  // Get all orders
  getOrders: (params = {}) => handleApiCall(() => 
    apiClient.get('/api/orders', { params })
  ),

  // Get order by ID
  getOrder: (orderId) => handleApiCall(() => 
    apiClient.get(`/api/orders/${orderId}`)
  ),

  // Create order
  createOrder: (orderData) => handleApiCall(() => 
    apiClient.post('/api/orders', orderData)
  ),

  // Update order
  updateOrder: (orderId, updates) => handleApiCall(() => 
    apiClient.put(`/api/orders/${orderId}`, updates)
  ),

  // Update order status
  updateOrderStatus: (orderId, status) => handleApiCall(() => 
    apiClient.patch(`/api/orders/${orderId}/status`, { status })
  ),

  // Cancel order
  cancelOrder: (orderId, reason) => handleApiCall(() => 
    apiClient.post(`/api/orders/${orderId}/cancel`, { reason })
  ),

  // Get order tracking
  getOrderTracking: (orderId) => handleApiCall(() => 
    apiClient.get(`/api/orders/${orderId}/tracking`)
  ),

  // Get order statistics
  getOrderStats: (timeRange = '30d') => handleApiCall(() => 
    apiClient.get('/api/orders/stats', { params: { range: timeRange } })
  ),
}

// ============================================================================
// PRODUCT APIs
// ============================================================================

export const productApi = {
  // Get all products
  getProducts: (params = {}) => handleApiCall(() => 
    apiClient.get('/api/products', { params })
  ),

  // Get product by ID
  getProduct: (productId) => handleApiCall(() => 
    apiClient.get(`/api/products/${productId}`)
  ),

  // Create product
  createProduct: (productData) => handleApiCall(() => 
    apiClient.post('/api/products', productData)
  ),

  // Update product
  updateProduct: (productId, updates) => handleApiCall(() => 
    apiClient.put(`/api/products/${productId}`, updates)
  ),

  // Delete product
  deleteProduct: (productId) => handleApiCall(() => 
    apiClient.delete(`/api/products/${productId}`)
  ),

  // Bulk import products
  bulkImportProducts: (products) => handleApiCall(() => 
    apiClient.post('/api/products/bulk-import', { products })
  ),

  // Get product statistics
  getProductStats: () => handleApiCall(() => 
    apiClient.get('/api/products/stats')
  ),

  // Search products
  searchProducts: (query, filters = {}) => handleApiCall(() => 
    apiClient.get('/api/products/search', { params: { q: query, ...filters } })
  ),
}

// ============================================================================
// INVENTORY APIs
// ============================================================================

export const inventoryApi = {
  // Get inventory
  getInventory: (params = {}) => handleApiCall(() => 
    apiClient.get('/api/inventory', { params })
  ),

  // Get inventory for product
  getProductInventory: (productId) => handleApiCall(() => 
    apiClient.get(`/api/inventory/product/${productId}`)
  ),

  // Update inventory
  updateInventory: (productId, warehouseId, quantity) => handleApiCall(() => 
    apiClient.put('/api/inventory', { product_id: productId, warehouse_id: warehouseId, quantity })
  ),

  // Adjust inventory
  adjustInventory: (productId, warehouseId, adjustment, reason) => handleApiCall(() => 
    apiClient.post('/api/inventory/adjust', { 
      product_id: productId, 
      warehouse_id: warehouseId, 
      adjustment, 
      reason 
    })
  ),

  // Get low stock items
  getLowStockItems: (threshold = 10) => handleApiCall(() => 
    apiClient.get('/api/inventory/low-stock', { params: { threshold } })
  ),

  // Get inventory movements
  getInventoryMovements: (productId, params = {}) => handleApiCall(() => 
    apiClient.get(`/api/inventory/movements/${productId}`, { params })
  ),
}

// ============================================================================
// WAREHOUSE APIs
// ============================================================================

export const warehouseApi = {
  // Get all warehouses
  getWarehouses: () => handleApiCall(() => 
    apiClient.get('/api/warehouses')
  ),

  // Get warehouse by ID
  getWarehouse: (warehouseId) => handleApiCall(() => 
    apiClient.get(`/api/warehouses/${warehouseId}`)
  ),

  // Get warehouse metrics
  getWarehouseMetrics: (warehouseId) => handleApiCall(() => 
    apiClient.get(`/api/warehouses/${warehouseId}/metrics`)
  ),

  // Get warehouse capacity
  getWarehouseCapacity: (warehouseId) => handleApiCall(() => 
    apiClient.get(`/api/warehouses/${warehouseId}/capacity`)
  ),
}

// ============================================================================
// CARRIER APIs
// ============================================================================

export const carrierApi = {
  // Get all carriers
  getCarriers: () => handleApiCall(() => 
    apiClient.get('/api/carriers')
  ),

  // Get carrier by ID
  getCarrier: (carrierId) => handleApiCall(() => 
    apiClient.get(`/api/carriers/${carrierId}`)
  ),

  // Get carrier performance
  getCarrierPerformance: (carrierId, timeRange = '30d') => handleApiCall(() => 
    apiClient.get(`/api/carriers/${carrierId}/performance`, { params: { range: timeRange } })
  ),

  // Get shipping rates
  getShippingRates: (origin, destination, weight, dimensions) => handleApiCall(() => 
    apiClient.post('/api/carriers/rates', { origin, destination, weight, dimensions })
  ),

  // Create shipment
  createShipment: (shipmentData) => handleApiCall(() => 
    apiClient.post('/api/carriers/shipments', shipmentData)
  ),

  // Track shipment
  trackShipment: (trackingNumber) => handleApiCall(() => 
    apiClient.get(`/api/carriers/track/${trackingNumber}`)
  ),
}

// ============================================================================
// CUSTOMER APIs
// ============================================================================

export const customerApi = {
  // Get all customers
  getCustomers: (params = {}) => handleApiCall(() => 
    apiClient.get('/api/customers', { params })
  ),

  // Get customer by ID
  getCustomer: (customerId) => handleApiCall(() => 
    apiClient.get(`/api/customers/${customerId}`)
  ),

  // Create customer
  createCustomer: (customerData) => handleApiCall(() => 
    apiClient.post('/api/customers', customerData)
  ),

  // Update customer
  updateCustomer: (customerId, updates) => handleApiCall(() => 
    apiClient.put(`/api/customers/${customerId}`, updates)
  ),

  // Get customer orders
  getCustomerOrders: (customerId) => handleApiCall(() => 
    apiClient.get(`/api/customers/${customerId}/orders`)
  ),

  // Get customer statistics
  getCustomerStats: (customerId) => handleApiCall(() => 
    apiClient.get(`/api/customers/${customerId}/stats`)
  ),
}

// ============================================================================
// MERCHANT APIs
// ============================================================================

export const merchantApi = {
  // Get merchant dashboard
  getDashboard: (merchantId) => handleApiCall(() => 
    apiClient.get(`/api/merchants/${merchantId}/dashboard`)
  ),

  // Get merchant analytics
  getAnalytics: (merchantId, timeRange = '30d') => handleApiCall(() => 
    apiClient.get(`/api/merchants/${merchantId}/analytics`, { params: { range: timeRange } })
  ),

  // Get merchant products
  getProducts: (merchantId, params = {}) => handleApiCall(() => 
    apiClient.get(`/api/merchants/${merchantId}/products`, { params })
  ),

  // Get merchant orders
  getOrders: (merchantId, params = {}) => handleApiCall(() => 
    apiClient.get(`/api/merchants/${merchantId}/orders`, { params })
  ),

  // Get marketplace integrations
  getMarketplaceIntegrations: (merchantId) => handleApiCall(() => 
    apiClient.get(`/api/merchants/${merchantId}/marketplaces`)
  ),

  // Sync with marketplace
  syncMarketplace: (merchantId, marketplaceId) => handleApiCall(() => 
    apiClient.post(`/api/merchants/${merchantId}/marketplaces/${marketplaceId}/sync`)
  ),
}

// ============================================================================
// ANALYTICS APIs
// ============================================================================

export const analyticsApi = {
  // Get sales analytics
  getSalesAnalytics: (timeRange = '30d', groupBy = 'day') => handleApiCall(() => 
    apiClient.get('/api/analytics/sales', { params: { range: timeRange, group_by: groupBy } })
  ),

  // Get performance analytics
  getPerformanceAnalytics: (timeRange = '24h') => handleApiCall(() => 
    apiClient.get('/api/analytics/performance', { params: { range: timeRange } })
  ),

  // Get inventory analytics
  getInventoryAnalytics: () => handleApiCall(() => 
    apiClient.get('/api/analytics/inventory')
  ),

  // Get customer analytics
  getCustomerAnalytics: (timeRange = '30d') => handleApiCall(() => 
    apiClient.get('/api/analytics/customers', { params: { range: timeRange } })
  ),

  // Get agent performance
  getAgentPerformance: (timeRange = '24h') => handleApiCall(() => 
    apiClient.get('/api/analytics/agents', { params: { range: timeRange } })
  ),
}

// ============================================================================
// AUTHENTICATION APIs
// ============================================================================

export const authApi = {
  // Login
  login: (email, password) => handleApiCall(() => 
    apiClient.post('/api/auth/login', { email, password })
  ),

  // Logout
  logout: () => handleApiCall(() => 
    apiClient.post('/api/auth/logout')
  ),

  // Register
  register: (userData) => handleApiCall(() => 
    apiClient.post('/api/auth/register', userData)
  ),

  // Get current user
  getCurrentUser: () => handleApiCall(() => 
    apiClient.get('/api/auth/me')
  ),

  // Refresh token
  refreshToken: (refreshToken) => handleApiCall(() => 
    apiClient.post('/api/auth/refresh', { refresh_token: refreshToken })
  ),

  // Change password
  changePassword: (oldPassword, newPassword) => handleApiCall(() => 
    apiClient.post('/api/auth/change-password', { old_password: oldPassword, new_password: newPassword })
  ),
}

// Export all APIs
export const api = {
  system: systemApi,
  agent: agentApi,
  alert: alertApi,
  order: orderApi,
  product: productApi,
  inventory: inventoryApi,
  warehouse: warehouseApi,
  carrier: carrierApi,
  customer: customerApi,
  merchant: merchantApi,
  analytics: analyticsApi,
  auth: authApi,
}

export default api

