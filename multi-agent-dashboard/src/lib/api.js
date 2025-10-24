/**
 * API Service for Multi-Agent E-commerce Platform
 * 
 * This module provides centralized API communication with all backend agents.
 * It handles authentication, error handling, and data transformation.
 */

import axios from 'axios'

// Base configuration for different agent services
const AGENT_PORTS = {
  order: 8001,
  product: 8002,
  inventory: 8003,
  warehouse: 8004,
  carrier: 8005,
  demand: 8006,
  pricing: 8007,
  communication: 8008,
  logistics: 8009,
  risk: 8010,
  marketplace: 8011,
  refurbished: 8012,
  d2c: 8013,
  monitoring: 8014
}

const BASE_URL = 'http://localhost' || process.env.REACT_APP_API_BASE_URL 

// Create axios instances for each agent
const createAgentClient = (agentName) => {
  const client = axios.create({
    baseURL: `${BASE_URL}:${AGENT_PORTS[agentName]}`,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    }
  })

  // Request interceptor for authentication
  client.interceptors.request.use(
    (config) => {
      // Add authentication token if available
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
      console.error(`API Error (${agentName}):`, error.response?.data || error.message)
      
      // Handle specific error cases
      if (error.response?.status === 401) {
        // Unauthorized - redirect to login or refresh token
        localStorage.removeItem('auth_token')
        // Could trigger a global auth state update here
      }
      
      return Promise.reject(error)
    }
  )

  return client
}

// Create clients for all agents
const clients = {}
Object.keys(AGENT_PORTS).forEach(agentName => {
  clients[agentName] = createAgentClient(agentName)
})

// API Service Class
class ApiService {
  
  // ==================== MONITORING AGENT APIs ====================
  
  async getSystemOverview() {
    try {
      const response = await clients.monitoring.get('/system/overview')
      return response.data
    } catch (error) {
      // Fallback to mock data if monitoring agent is not available
      console.warn('Monitoring agent unavailable, using mock data')
      return this.getMockSystemOverview()
    }
  }

  async getAgentHealth() {
    try {
      const response = await clients.monitoring.get('/agents')
      return response.data
    } catch (error) {
      console.warn('Agent health data unavailable, using mock data')
      return this.getMockAgentHealth()
    }
  }

  async getSystemAlerts(activeOnly = true) {
    try {
      const response = await clients.monitoring.get('/alerts', {
        params: { active_only: activeOnly }
      })
      return response.data
    } catch (error) {
      console.warn('Alerts data unavailable, using mock data')
      return this.getMockAlerts()
    }
  }

  async resolveAlert(alertId, resolution) {
    try {
      const response = await clients.monitoring.post(`/alerts/${alertId}/resolve`, resolution)
      return response.data
    } catch (error) {
      throw new Error(`Failed to resolve alert: ${error.message}`)
    }
  }

  // ==================== PRODUCT AGENT APIs ====================

  async getProducts(params = {}) {
    try {
      const response = await clients.product.get('/products', { params })
      return response.data
    } catch (error) {
      console.warn('Product data unavailable, using mock data')
      return this.getMockProducts()
    }
  }

  async getProduct(productId) {
    try {
      const response = await clients.product.get(`/products/${productId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch product: ${error.message}`)
    }
  }

  async createProduct(productData) {
    try {
      const response = await clients.product.post('/products', productData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to create product: ${error.message}`)
    }
  }

  async updateProduct(productId, productData) {
    try {
      const response = await clients.product.put(`/products/${productId}`, productData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to update product: ${error.message}`)
    }
  }

  // ==================== ORDER AGENT APIs ====================

  async getOrders(params = {}) {
    try {
      const response = await clients.order.get('/orders', { params })
      return response.data
    } catch (error) {
      console.warn('Order data unavailable, using mock data')
      return this.getMockOrders()
    }
  }

  async getOrder(orderId) {
    try {
      const response = await clients.order.get(`/orders/${orderId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch order: ${error.message}`)
    }
  }

  async createOrder(orderData) {
    try {
      const response = await clients.order.post('/orders', orderData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to create order: ${error.message}`)
    }
  }

  async updateOrderStatus(orderId, status) {
    try {
      const response = await clients.order.patch(`/orders/${orderId}/status`, { status })
      return response.data
    } catch (error) {
      throw new Error(`Failed to update order status: ${error.message}`)
    }
  }

  // ==================== INVENTORY AGENT APIs ====================

  async getInventory(params = {}) {
    try {
      const response = await clients.inventory.get('/inventory', { params })
      return response.data
    } catch (error) {
      console.warn('Inventory data unavailable, using mock data')
      return this.getMockInventory()
    }
  }

  async updateInventory(productId, warehouseId, quantity) {
    try {
      const response = await clients.inventory.patch('/inventory', {
        product_id: productId,
        warehouse_id: warehouseId,
        quantity
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to update inventory: ${error.message}`)
    }
  }

  // ==================== ANALYTICS & PERFORMANCE APIs ====================

  async getPerformanceMetrics(timeRange = '24h') {
    try {
      const response = await clients.monitoring.get('/metrics/performance', {
        params: { time_range: timeRange }
      })
      return response.data
    } catch (error) {
      console.warn('Performance metrics unavailable, using mock data')
      return this.getMockPerformanceMetrics()
    }
  }

  async getSalesAnalytics(params = {}) {
    try {
      const response = await clients.order.get('/analytics/sales', { params })
      return response.data
    } catch (error) {
      console.warn('Sales analytics unavailable, using mock data')
      return this.getMockSalesAnalytics()
    }
  }

  // ==================== MERCHANT DASHBOARD APIs ====================
  
  async getMerchantKpis(timeRange = '7d') {
    try {
      const response = await clients.order.get('/analytics/kpis', { params: { timeRange } })
      return response.data
    } catch (error) {
      console.warn('Merchant KPIs unavailable, using mock data')
      return this.getMockMerchantKpis()
    }
  }
  
  async getRecentOrders(limit = 10) {
    try {
      const response = await clients.order.get('/orders/recent', { params: { limit } })
      return response.data
    } catch (error) {
      console.warn('Recent orders unavailable, using mock data')
      return this.getMockRecentOrders()
    }
  }
  
  async getInventoryAlerts() {
    try {
      const response = await clients.inventory.get('/alerts')
      return response.data
    } catch (error) {
      console.warn('Inventory alerts unavailable, using mock data')
      return this.getMockInventoryAlerts()
    }
  }
  
  async getMarketplacePerformance(timeRange = '7d') {
    try {
      const response = await clients.marketplace.get('/performance', { params: { timeRange } })
      return response.data
    } catch (error) {
      console.warn('Marketplace performance unavailable, using mock data')
      return this.getMockMarketplacePerformance()
    }
  }
  
  async getProductCategories() {
    try {
      const response = await clients.product.get('/categories')
      return response.data
    } catch (error) {
      console.warn('Product categories unavailable, using mock data')
      return this.getMockProductCategories()
    }
  }

  // ==================== MOCK DATA METHODS ====================
  // These provide fallback data when agents are unavailable

  getMockSystemOverview() {
    return {
      timestamp: new Date().toISOString(),
      system_status: 'healthy',
      agents: {
        order_agent: { status: 'healthy', response_time: 245, cpu_usage: 68, memory_usage: 72 },
        product_agent: { status: 'healthy', response_time: 189, cpu_usage: 45, memory_usage: 58 },
        inventory_agent: { status: 'warning', response_time: 567, cpu_usage: 82, memory_usage: 79 },
        monitoring_agent: { status: 'healthy', response_time: 123, cpu_usage: 34, memory_usage: 41 }
      },
      active_alerts: [
        {
          id: 'alert_001',
          severity: 'medium',
          title: 'High CPU Usage - Inventory Agent',
          description: 'CPU usage exceeded 80% threshold',
          timestamp: new Date(Date.now() - 3600000).toISOString()
        }
      ],
      system_metrics: {
        cpu_usage: 68,
        memory_usage: 72,
        disk_usage: 45,
        response_time: 245,
        error_rate: 0.2,
        throughput: 1247
      }
    }
  }

  getMockAgentHealth() {
    return [
      { agent_id: 'order_agent', agent_name: 'Order Management', status: 'healthy', cpu_usage: 68, memory_usage: 72, response_time: 245 },
      { agent_id: 'product_agent', agent_name: 'Product Management', status: 'healthy', cpu_usage: 45, memory_usage: 58, response_time: 189 },
      { agent_id: 'inventory_agent', agent_name: 'Inventory Management', status: 'warning', cpu_usage: 82, memory_usage: 79, response_time: 567 },
      { agent_id: 'warehouse_agent', agent_name: 'Warehouse Selection', status: 'healthy', cpu_usage: 56, memory_usage: 63, response_time: 298 }
    ]
  }

  getMockAlerts() {
    return [
      {
        id: 'alert_001',
        severity: 'medium',
        title: 'High CPU Usage - Inventory Agent',
        description: 'CPU usage exceeded 80% threshold for the past 15 minutes',
        affected_agents: ['inventory_agent'],
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        status: 'active'
      },
      {
        id: 'alert_002',
        severity: 'low',
        title: 'Low Stock Alert',
        description: '15 products below reorder point',
        affected_agents: ['inventory_agent', 'product_agent'],
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        status: 'active'
      }
    ]
  }

  getMockProducts() {
    return {
      products: [
        { id: '1', sku: 'SKU-001', name: 'Wireless Headphones', category: 'Electronics', price: 99.99, stock: 150 },
        { id: '2', sku: 'SKU-002', name: 'Smart Watch', category: 'Electronics', price: 299.99, stock: 75 },
        { id: '3', sku: 'SKU-003', name: 'Bluetooth Speaker', category: 'Electronics', price: 79.99, stock: 200 }
      ],
      total: 3,
      page: 1,
      per_page: 10
    }
  }

  getMockOrders() {
    return {
      orders: [
        { id: '1', order_number: 'ORD-2024-001', customer_name: 'John Doe', status: 'processing', total: 199.98, created_at: new Date().toISOString() },
        { id: '2', order_number: 'ORD-2024-002', customer_name: 'Jane Smith', status: 'shipped', total: 299.99, created_at: new Date(Date.now() - 86400000).toISOString() },
        { id: '3', order_number: 'ORD-2024-003', customer_name: 'Bob Johnson', status: 'delivered', total: 79.99, created_at: new Date(Date.now() - 172800000).toISOString() }
      ],
      total: 3,
      page: 1,
      per_page: 10
    }
  }

  getMockInventory() {
    return [
      { product_id: '1', product_name: 'Wireless Headphones', warehouse: 'NA-DC-01', quantity: 150, reserved: 25 },
      { product_id: '2', product_name: 'Smart Watch', warehouse: 'NA-DC-01', quantity: 75, reserved: 10 },
      { product_id: '3', product_name: 'Bluetooth Speaker', warehouse: 'EU-DH-01', quantity: 200, reserved: 35 }
    ]
  }

  getMockPerformanceMetrics() {
    const data = []
    const now = new Date()
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000)
      data.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        cpu: Math.floor(Math.random() * 30) + 50,
        memory: Math.floor(Math.random() * 25) + 60,
        response_time: Math.floor(Math.random() * 100) + 200,
        throughput: Math.floor(Math.random() * 500) + 1000
      })
    }
    
    return data
  }

  getMockSalesAnalytics() {
    return {
      total_revenue: 125847.50,
      total_orders: 1247,
      avg_order_value: 100.92,
      conversion_rate: 3.2,
      top_products: [
        { name: 'Wireless Headphones', revenue: 15000, units: 150 },
        { name: 'Smart Watch', revenue: 22500, units: 75 },
        { name: 'Bluetooth Speaker', revenue: 16000, units: 200 }
      ]
    }
  }

  // ==================== WEBSOCKET CONNECTION ====================

  connectWebSocket(onMessage, onError) {
    try {
      const ws = new WebSocket(`ws://localhost:${AGENT_PORTS.monitoring}/ws`)
      
      ws.onopen = () => {
        console.log('WebSocket connected to monitoring agent')
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (onError) onError(error)
      }
      
      ws.onclose = () => {
        console.log('WebSocket connection closed')
        // Implement reconnection logic here if needed
      }
      
      return ws
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      if (onError) onError(error)
      return null
    }
  }

  getMockMerchantKpis() {
    return {
      totalSales: 125847.50,
      totalOrders: 1247,
      averageOrderValue: 100.92,
      conversionRate: 3.45,
      salesGrowth: 12.5,
      ordersGrowth: 8.3
    }
  }
  
  getMockRecentOrders() {
    return [
      {
        id: 'ORD-2024-1247',
        customer: 'John Doe',
        total: 299.99,
        status: 'processing',
        created_at: new Date(Date.now() - 1800000).toISOString()
      },
      {
        id: 'ORD-2024-1246',
        customer: 'Jane Smith',
        total: 149.50,
        status: 'shipped',
        created_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 'ORD-2024-1245',
        customer: 'Bob Johnson',
        total: 89.99,
        status: 'delivered',
        created_at: new Date(Date.now() - 7200000).toISOString()
      }
    ]
  }
  
  getMockInventoryAlerts() {
    return [
      {
        id: 'INV-001',
        product: 'Wireless Headphones',
        sku: 'SKU-001',
        current_stock: 15,
        reorder_point: 50,
        severity: 'high',
        message: 'Stock below reorder point'
      },
      {
        id: 'INV-002',
        product: 'Smart Watch',
        sku: 'SKU-002',
        current_stock: 8,
        reorder_point: 20,
        severity: 'critical',
        message: 'Stock critically low'
      }
    ]
  }
  
  getMockMarketplacePerformance() {
    return [
      {
        marketplace: 'Amazon',
        sales: 45230.50,
        orders: 523,
        growth: 15.2
      },
      {
        marketplace: 'eBay',
        sales: 32450.75,
        orders: 412,
        growth: 8.7
      },
      {
        marketplace: 'Direct',
        sales: 48166.25,
        orders: 312,
        growth: 22.1
      }
    ]
  }
  
  getMockProductCategories() {
    return [
      { id: 'electronics', name: 'Electronics', count: 245 },
      { id: 'clothing', name: 'Clothing', count: 189 },
      { id: 'home', name: 'Home & Garden', count: 156 },
      { id: 'sports', name: 'Sports & Outdoors', count: 98 }
    ]
  }

  getMockSalesAnalytics() {
    return {
      daily_sales: [
        { date: '2024-10-16', sales: 12450.50, orders: 124 },
        { date: '2024-10-17', sales: 15230.75, orders: 156 },
        { date: '2024-10-18', sales: 13890.25, orders: 142 },
        { date: '2024-10-19', sales: 16540.00, orders: 168 },
        { date: '2024-10-20', sales: 14230.50, orders: 145 },
        { date: '2024-10-21', sales: 17890.75, orders: 182 },
        { date: '2024-10-22', sales: 15615.75, orders: 159 }
      ],
      total_sales: 105847.50,
      total_orders: 1076,
      average_order_value: 98.37
    }
  }
}

// Export singleton instance
export const apiService = new ApiService()
export default apiService
