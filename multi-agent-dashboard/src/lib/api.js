/**
 * API Service for Multi-Agent E-commerce Platform
 * 
 * This module provides centralized API communication with all backend agents.
 * It handles authentication, error handling, and data transformation.
 */

import axios from 'axios'

// Base configuration for different agent services
// Port assignments match actual agent startup configuration from StartAllAgents.bat
const AGENT_PORTS = {
  // Core Business Agents
  order: 8000,              // order_agent_v3.py
  product: 8001,            // product_agent_v3.py
  inventory: 8002,          // inventory_agent_v3.py
  marketplace: 8003,        // marketplace_connector_v3.py
  payment: 8004,            // payment_agent_v3.py
  pricing: 8005,            // dynamic_pricing_v3.py
  carrier: 8006,            // carrier_agent_v3.py
  customer: 8007,           // customer_agent_v3.py
  warehouse: 8008,          // warehouse_agent_v3.py
  returns: 8009,            // returns_agent_v3.py
  fraud: 8010,              // fraud_detection_agent_v3.py
  risk: 8011,               // risk_anomaly_detection_v3.py
  knowledge: 8012,          // knowledge_management_agent_v3.py
  analytics: 8013,          // analytics_agent_v3.py
  recommendation: 8014,     // recommendation_agent_v3.py
  transport: 8015,          // transport_management_v3.py
  documents: 8016,          // document_generation_agent_v3.py
  support: 8018,            // support_agent_v3.py
  communication: 8019,      // customer_communication_v3.py
  promotion: 8020,          // promotion_agent_v3.py
  aftersales: 8021,         // after_sales_agent_v3.py
  infrastructure: 8022,     // infrastructure_v3.py
  monitoring: 8023,         // monitoring_agent_v3.py
  aimonitoring: 8024,       // ai_monitoring_agent_v3.py
  d2c: 8026,                // d2c_ecommerce_agent_v3.py
  backoffice: 8027,         // backoffice_agent_v3.py
  quality: 8028,            // quality_control_agent_v3.py
  // Feature Agents
  replenishment: 8031,      // replenishment_agent_v3.py
  inbound: 8032,            // inbound_management_agent_v3.py
  fulfillment: 8033,        // fulfillment_agent_v3.py
  carrierai: 8034,          // carrier_agent_ai_v3.py
  rma: 8035,                // rma_agent_v3.py
  advancedanalytics: 8036,  // advanced_analytics_agent_v3.py
  forecasting: 8037,        // demand_forecasting_agent_v3.py
  international: 8038,      // international_shipping_agent_v3.py
  // System Gateway
  gateway: 8100             // system_api_gateway_v3.py
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
  
  // ==================== WAREHOUSE AGENT APIs ====================
  
  async getWarehouses() {
    try {
      const response = await clients.warehouse.get('/warehouses')
      return response.data
    } catch (error) {
      console.warn('Warehouses unavailable, using mock data')
      return this.getMockWarehouses()
    }
  }
  
  async getWarehouse(warehouseId) {
    try {
      const response = await clients.warehouse.get(`/warehouses/${warehouseId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to get warehouse: ${error.message}`)
    }
  }
  
  // ==================== MARKETPLACE AGENT APIs ====================
  
  async getMarketplaces() {
    try {
      const response = await clients.marketplace.get('/marketplaces')
      return response.data
    } catch (error) {
      console.warn('Marketplaces unavailable, using mock data')
      return this.getMockMarketplaces()
    }
  }
  
  async getMarketplace(marketplaceId) {
    try {
      const response = await clients.marketplace.get(`/marketplaces/${marketplaceId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to get marketplace: ${error.message}`)
    }
  }

  // ==================== WAREHOUSE AGENT APIs ====================
  
  async getWarehouses() {
    try {
      const response = await clients.warehouse.get('/warehouses')
      return response.data
    } catch (error) {
      console.warn('Warehouses unavailable, using mock data')
      return this.getMockWarehouses()
    }
  }
  
  async getWarehouse(warehouseId) {
    try {
      const response = await clients.warehouse.get(`/warehouses/${warehouseId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to get warehouse: ${error.message}`)
    }
  }
  
  // ==================== MARKETPLACE AGENT APIs ====================
  
  async getMarketplaces() {
    try {
      const response = await clients.marketplace.get('/marketplaces')
      return response.data
    } catch (error) {
      console.warn('Marketplaces unavailable, using mock data')
      return this.getMockMarketplaces()
    }
  }
  
  async getConnectedMarketplaces() {
    // Alias for getMarketplaces
    return this.getMarketplaces()
  }
  
  async getAvailableMarketplaces() {
    try {
      const response = await clients.marketplace.get('/marketplaces/available')
      return response.data
    } catch (error) {
      console.warn('Available marketplaces unavailable, using mock data')
      return this.getMockAvailableMarketplaces()
    }
  }
  
  async getMarketplace(marketplaceId) {
    try {
      const response = await clients.marketplace.get(`/marketplaces/${marketplaceId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to get marketplace: ${error.message}`)
    }
  }

  // ==================== MARKETPLACE SYNC APIs ====================
  
  async getMarketplaceSyncStatus() {
    const response = await clients.marketplace.get('/sync/status')
    return response.data
  }

  // ==================== ANALYTICS APIs ====================
  
  async getProductAnalytics(params = {}) {
    const response = await clients.product.get('/analytics', { params })
    return response.data
  }

  // ==================== CUSTOMER PORTAL APIs ====================
  
  async getFeaturedProducts(limit = 10) {
    const response = await clients.product.get('/featured', { params: { limit } })
    return response.data
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
  
  getMockWarehouses() {
    return [
      {
        id: 'WH-001',
        name: 'Main Distribution Center',
        location: 'Paris, France',
        capacity: 50000,
        current_stock: 32450,
        status: 'active',
        address: '123 Rue de la Logistique, 75001 Paris'
      },
      {
        id: 'WH-002',
        name: 'North Regional Warehouse',
        location: 'Lille, France',
        capacity: 25000,
        current_stock: 18750,
        status: 'active',
        address: '456 Avenue du Commerce, 59000 Lille'
      },
      {
        id: 'WH-003',
        name: 'South Regional Warehouse',
        location: 'Marseille, France',
        capacity: 30000,
        current_stock: 21200,
        status: 'active',
        address: '789 Boulevard de la Distribution, 13001 Marseille'
      },
      {
        id: 'WH-004',
        name: 'Returns Processing Center',
        location: 'Lyon, France',
        capacity: 15000,
        current_stock: 5400,
        status: 'active',
        address: '321 Rue des Retours, 69001 Lyon'
      }
    ]
  }
  
  getMockMarketplaces() {
    return [
      {
        id: 'MKT-001',
        name: 'Amazon France',
        platform: 'Amazon',
        status: 'connected',
        active_listings: 1245,
        monthly_sales: 45230.50,
        commission_rate: 15,
        last_sync: '2024-10-24T10:30:00Z'
      },
      {
        id: 'MKT-002',
        name: 'eBay France',
        platform: 'eBay',
        status: 'connected',
        active_listings: 892,
        monthly_sales: 32450.75,
        commission_rate: 12,
        last_sync: '2024-10-24T10:25:00Z'
      },
      {
        id: 'MKT-003',
        name: 'CDiscount',
        platform: 'CDiscount',
        status: 'connected',
        active_listings: 567,
        monthly_sales: 18900.25,
        commission_rate: 10,
        last_sync: '2024-10-24T10:20:00Z'
      },
      {
        id: 'MKT-004',
        name: 'BackMarket',
        platform: 'BackMarket',
        status: 'connected',
        active_listings: 234,
        monthly_sales: 12340.00,
        commission_rate: 8,
        last_sync: '2024-10-24T10:15:00Z'
      },
      {
        id: 'MKT-005',
        name: 'Refurbed',
        platform: 'Refurbed',
        status: 'pending',
        active_listings: 0,
        monthly_sales: 0,
        commission_rate: 9,
        last_sync: null
      }
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

  getMockWarehouses() {
    return [
      {
        id: 'WH-001',
        name: 'Main Distribution Center',
        location: 'Paris, France',
        capacity: 50000,
        current_stock: 32450,
        utilization: 64.9,
        status: 'active',
        address: '123 Rue de la Logistique, 75001 Paris'
      },
      {
        id: 'WH-002',
        name: 'North Regional Warehouse',
        location: 'Lille, France',
        capacity: 25000,
        current_stock: 18750,
        utilization: 75.0,
        status: 'active',
        address: '456 Avenue du Commerce, 59000 Lille'
      },
      {
        id: 'WH-003',
        name: 'South Regional Warehouse',
        location: 'Marseille, France',
        capacity: 30000,
        current_stock: 21200,
        utilization: 70.7,
        status: 'active',
        address: '789 Boulevard de la Distribution, 13001 Marseille'
      },
      {
        id: 'WH-004',
        name: 'Returns Processing Center',
        location: 'Lyon, France',
        capacity: 15000,
        current_stock: 5400,
        utilization: 36.0,
        status: 'active',
        address: '321 Rue des Retours, 69001 Lyon'
      }
    ]
  }
  
  getMockMarketplaces() {
    return [
      {
        id: 'MKT-001',
        name: 'Amazon France',
        platform: 'Amazon',
        status: 'connected',
        active_listings: 1245,
        monthly_sales: 45230.50,
        monthly_orders: 523,
        commission_rate: 15,
        last_sync: new Date(Date.now() - 300000).toISOString(),
        integration_status: 'healthy'
      },
      {
        id: 'MKT-002',
        name: 'eBay France',
        platform: 'eBay',
        status: 'connected',
        active_listings: 892,
        monthly_sales: 32450.75,
        monthly_orders: 412,
        commission_rate: 12,
        last_sync: new Date(Date.now() - 600000).toISOString(),
        integration_status: 'healthy'
      },
      {
        id: 'MKT-003',
        name: 'CDiscount',
        platform: 'CDiscount',
        status: 'connected',
        active_listings: 567,
        monthly_sales: 18900.25,
        monthly_orders: 234,
        commission_rate: 10,
        last_sync: new Date(Date.now() - 900000).toISOString(),
        integration_status: 'healthy'
      },
      {
        id: 'MKT-004',
        name: 'BackMarket',
        platform: 'BackMarket',
        status: 'connected',
        active_listings: 234,
        monthly_sales: 12340.00,
        monthly_orders: 156,
        commission_rate: 8,
        last_sync: new Date(Date.now() - 1200000).toISOString(),
        integration_status: 'healthy'
      },
      {
        id: 'MKT-005',
        name: 'Refurbed',
        platform: 'Refurbed',
        status: 'pending',
        active_listings: 0,
        monthly_sales: 0,
        monthly_orders: 0,
        commission_rate: 9,
        last_sync: null,
        integration_status: 'pending_setup'
      }
    ]
  }
  
  getMockAvailableMarketplaces() {
    return [
      {
        id: 'available-1',
        name: 'Fnac',
        platform: 'Fnac',
        description: 'Major French retailer',
        commission_rate: 12,
        setup_complexity: 'medium',
        estimated_reach: 'high'
      },
      {
        id: 'available-2',
        name: 'Rakuten France',
        platform: 'Rakuten',
        description: 'E-commerce marketplace',
        commission_rate: 10,
        setup_complexity: 'easy',
        estimated_reach: 'medium'
      },
      {
        id: 'available-3',
        name: 'Vinted',
        platform: 'Vinted',
        description: 'Second-hand marketplace',
        commission_rate: 5,
        setup_complexity: 'easy',
        estimated_reach: 'high'
      }
    ]
  }

}

// Export singleton instance
export const apiService = new ApiService()
export default apiService

  // ==================== MISSING APIs - IMPLEMENTATION ====================
  
  // Order Management APIs
  async getOrderDetails(orderId) {
    try {
      const response = await clients.order.get(`/orders/${orderId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to get order details: ${error.message}`)
    }
  }
  
  async exportOrders(orderIds) {
    try {
      const response = await clients.order.post('/orders/export', { orderIds })
      return response.data
    } catch (error) {
      throw new Error(`Failed to export orders: ${error.message}`)
    }
  }
  
  async bulkUpdateOrderStatus(orderIds, status) {
    try {
      const response = await clients.order.post('/orders/bulk-update-status', { orderIds, status })
      return response.data
    } catch (error) {
      throw new Error(`Failed to bulk update order status: ${error.message}`)
    }
  }
  
  // Product Management APIs
  async deleteProduct(productId) {
    try {
      const response = await clients.product.delete(`/products/${productId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to delete product: ${error.message}`)
    }
  }
  
  async bulkDeleteProducts(productIds) {
    try {
      const response = await clients.product.post('/products/bulk-delete', { productIds })
      return response.data
    } catch (error) {
      throw new Error(`Failed to bulk delete products: ${error.message}`)
    }
  }
  
  async bulkSyncProducts(productIds) {
    try {
      const response = await clients.product.post('/products/bulk-sync', { productIds })
      return response.data
    } catch (error) {
      throw new Error(`Failed to bulk sync products: ${error.message}`)
    }
  }
  
  async bulkUpdateProductStatus(productIds, status) {
    try {
      const response = await clients.product.post('/products/bulk-update-status', { productIds, status })
      return response.data
    } catch (error) {
      throw new Error(`Failed to bulk update product status: ${error.message}`)
    }
  }
  
  async syncProductsWithMarketplaces() {
    try {
      const response = await clients.product.post('/products/sync-all')
      return response.data
    } catch (error) {
      throw new Error(`Failed to sync products with marketplaces: ${error.message}`)
    }
  }
  
  async getProductDetails(productId) {
    try {
      const response = await clients.product.get(`/products/${productId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to get product details: ${error.message}`)
    }
  }
  
  async getProductReviews(productId) {
    try {
      const response = await clients.product.get(`/products/${productId}/reviews`)
      return response.data
    } catch (error) {
      console.warn('Product reviews unavailable, returning empty array')
      return []
    }
  }
  
  async getRelatedProducts(productId) {
    try {
      const response = await clients.recommendation.get(`/products/${productId}/related`)
      return response.data
    } catch (error) {
      console.warn('Related products unavailable, returning empty array')
      return []
    }
  }
  
  // Inventory Management APIs
  async exportInventory(itemIds) {
    try {
      const response = await clients.inventory.post('/inventory/export', { itemIds })
      return response.data
    } catch (error) {
      throw new Error(`Failed to export inventory: ${error.message}`)
    }
  }
  
  async bulkReorderItems(itemIds) {
    try {
      const response = await clients.inventory.post('/inventory/bulk-reorder', { itemIds })
      return response.data
    } catch (error) {
      throw new Error(`Failed to bulk reorder items: ${error.message}`)
    }
  }
  
  async transferInventory(data) {
    try {
      const response = await clients.inventory.post('/inventory/transfer', data)
      return response.data
    } catch (error) {
      throw new Error(`Failed to transfer inventory: ${error.message}`)
    }
  }
  
  async adjustInventory(data) {
    try {
      const response = await clients.inventory.post('/inventory/adjust', data)
      return response.data
    } catch (error) {
      throw new Error(`Failed to adjust inventory: ${error.message}`)
    }
  }
  
  // Shopping Cart APIs
  async getCart() {
    try {
      const response = await clients.order.get('/cart')
      return response.data
    } catch (error) {
      console.warn('Cart unavailable, returning empty cart')
      return { items: [], total: 0 }
    }
  }
  
  async addToCart(productId, quantity = 1) {
    try {
      const response = await clients.order.post('/cart/add', { productId, quantity })
      return response.data
    } catch (error) {
      throw new Error(`Failed to add to cart: ${error.message}`)
    }
  }
  
  async updateCartItem(itemId, quantity) {
    try {
      const response = await clients.order.patch(`/cart/items/${itemId}`, { quantity })
      return response.data
    } catch (error) {
      throw new Error(`Failed to update cart item: ${error.message}`)
    }
  }
  
  async removeCartItem(itemId) {
    try {
      const response = await clients.order.delete(`/cart/items/${itemId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to remove cart item: ${error.message}`)
    }
  }
  
  async applyCoupon(couponCode) {
    try {
      const response = await clients.order.post('/cart/apply-coupon', { couponCode })
      return response.data
    } catch (error) {
      throw new Error(`Failed to apply coupon: ${error.message}`)
    }
  }
  
  // Customer Account APIs
  async getCustomerProfile() {
    try {
      const response = await clients.customer.get('/profile')
      return response.data
    } catch (error) {
      throw new Error(`Failed to get customer profile: ${error.message}`)
    }
  }
  
  async updateCustomerProfile(profileData) {
    try {
      const response = await clients.customer.patch('/profile', profileData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to update customer profile: ${error.message}`)
    }
  }
  
  async getCustomerOrders() {
    try {
      const response = await clients.order.get('/customer/orders')
      return response.data
    } catch (error) {
      console.warn('Customer orders unavailable, returning empty array')
      return []
    }
  }
  
  async getCustomerAddresses() {
    try {
      const response = await clients.customer.get('/addresses')
      return response.data
    } catch (error) {
      console.warn('Customer addresses unavailable, returning empty array')
      return []
    }
  }
  
  async deleteCustomerAddress(addressId) {
    try {
      const response = await clients.customer.delete(`/addresses/${addressId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to delete address: ${error.message}`)
    }
  }
  
  async getCustomerPaymentMethods() {
    try {
      const response = await clients.payment.get('/payment-methods')
      return response.data
    } catch (error) {
      console.warn('Payment methods unavailable, returning empty array')
      return []
    }
  }
  
  async deleteCustomerPaymentMethod(paymentMethodId) {
    try {
      const response = await clients.payment.delete(`/payment-methods/${paymentMethodId}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to delete payment method: ${error.message}`)
    }
  }
  
  // Marketplace Integration APIs
  async connectMarketplace(marketplaceData) {
    try {
      const response = await clients.marketplace.post('/marketplaces/connect', marketplaceData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to connect marketplace: ${error.message}`)
    }
  }
  
  async disconnectMarketplace(marketplaceId) {
    try {
      const response = await clients.marketplace.post(`/marketplaces/${marketplaceId}/disconnect`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to disconnect marketplace: ${error.message}`)
    }
  }
  
  async syncMarketplace(data) {
    try {
      const response = await clients.marketplace.post('/marketplaces/sync', data)
      return response.data
    } catch (error) {
      throw new Error(`Failed to sync marketplace: ${error.message}`)
    }
  }
  
  // Analytics APIs
  async getCustomerAnalytics(params = {}) {
    try {
      const response = await clients.analytics.get('/customer-analytics', { params })
      return response.data
    } catch (error) {
      console.warn('Customer analytics unavailable, returning mock data')
      return { totalCustomers: 0, newCustomers: 0, retention: 0 }
    }
  }
  
  async getInventoryAnalytics(params = {}) {
    try {
      const response = await clients.analytics.get('/inventory-analytics', { params })
      return response.data
    } catch (error) {
      console.warn('Inventory analytics unavailable, returning mock data')
      return { totalItems: 0, lowStock: 0, outOfStock: 0 }
    }
  }
  
  async getMarketplaceAnalytics(params = {}) {
    try {
      const response = await clients.analytics.get('/marketplace-analytics', { params })
      return response.data
    } catch (error) {
      console.warn('Marketplace analytics unavailable, returning mock data')
      return { totalSales: 0, orders: 0, channels: [] }
    }
  }
  
  // Customer Portal APIs
  async getCategories() {
    try {
      const response = await clients.product.get('/categories')
      return response.data
    } catch (error) {
      console.warn('Categories unavailable, returning empty array')
      return []
    }
  }
  
  async getNewArrivals(limit = 10) {
    try {
      const response = await clients.product.get('/new-arrivals', { params: { limit } })
      return response.data
    } catch (error) {
      console.warn('New arrivals unavailable, returning empty array')
      return []
    }
  }
  
  async getPromotions() {
    try {
      const response = await clients.promotion.get('/active-promotions')
      return response.data
    } catch (error) {
      console.warn('Promotions unavailable, returning empty array')
      return []
    }
  }
  
  async getRecommendations() {
    try {
      const response = await clients.recommendation.get('/recommendations')
      return response.data
    } catch (error) {
      console.warn('Recommendations unavailable, returning empty array')
      return []
    }
  }
  
  // Admin APIs
  async getSystemConfiguration() {
    try {
      const response = await clients.infrastructure.get('/system/configuration')
      return response.data
    } catch (error) {
      console.warn('System configuration unavailable, returning defaults')
      return {}
    }
  }
  
  async updateSystemConfiguration(configData) {
    try {
      const response = await clients.infrastructure.patch('/system/configuration', configData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to update system configuration: ${error.message}`)
    }
  }
  
  async getAgentLogs(agentId, params = {}) {
    try {
      const response = await clients.monitoring.get(`/agents/${agentId}/logs`, { params })
      return response.data
    } catch (error) {
      console.warn('Agent logs unavailable, returning empty array')
      return []
    }
  }
  
  async restartAgent(agentId) {
    try {
      const response = await clients.infrastructure.post(`/agents/${agentId}/restart`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to restart agent: ${error.message}`)
    }
  }
  
  async stopAgent(agentId) {
    try {
      const response = await clients.infrastructure.post(`/agents/${agentId}/stop`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to stop agent: ${error.message}`)
    }
  }
  
  async connectWebSocket(url) {
    // WebSocket connection is handled separately in WebSocketContext
    // This is a placeholder for compatibility
    console.log('WebSocket connection requested:', url)
    return { status: 'connected' }
  }

