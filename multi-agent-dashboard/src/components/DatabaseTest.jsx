import { useState, useEffect } from 'react'

const API_BASE_URL = 'http://localhost'

const AGENTS = [
  { name: 'Monitoring Agent', port: 8014, endpoint: '/health' },
  { name: 'Product Agent', port: 8002, endpoint: '/health' },
  { name: 'Order Agent', port: 8001, endpoint: '/health' },
  { name: 'Inventory Agent', port: 8003, endpoint: '/health' },
  { name: 'Communication Agent', port: 8008, endpoint: '/health' }
]

export default function DatabaseTest({ onReset }) {
  const [agentStatus, setAgentStatus] = useState([])
  const [systemOverview, setSystemOverview] = useState(null)
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const checkAgentHealth = async (agent) => {
    try {
      const startTime = Date.now()
      const response = await fetch(`${API_BASE_URL}:${agent.port}${agent.endpoint}`)
      const responseTime = Date.now() - startTime
      
      if (response.ok) {
        return {
          ...agent,
          status: 'healthy',
          responseTime
        }
      } else {
        return {
          ...agent,
          status: 'error',
          responseTime,
          error: `HTTP ${response.status}`
        }
      }
    } catch (error) {
      return {
        ...agent,
        status: 'error',
        responseTime: 0,
        error: error.message
      }
    }
  }

  const fetchSystemOverview = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}:8014/system/overview`)
      if (response.ok) {
        const data = await response.json()
        setSystemOverview(data)
        return data
      } else {
        throw new Error(`Failed to fetch system overview: HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to fetch system overview:', error)
      throw error
    }
  }

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}:8002/products`)
      if (response.ok) {
        const data = await response.json()
        const products = data.products || data || []
        setProducts(products)
        return products
      } else {
        throw new Error(`Failed to fetch products: HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to fetch products:', error)
      setProducts([])
      throw error
    }
  }

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}:8001/orders`)
      if (response.ok) {
        const data = await response.json()
        const orders = data.orders || data || []
        setOrders(orders)
        return orders
      } else {
        throw new Error(`Failed to fetch orders: HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error)
      setOrders([])
      throw error
    }
  }

  const runDatabaseTests = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Check agent health
      const healthPromises = AGENTS.map(checkAgentHealth)
      const healthResults = await Promise.all(healthPromises)
      setAgentStatus(healthResults)
      
      // Only proceed if at least one agent is healthy
      const healthyAgents = healthResults.filter(agent => agent.status === 'healthy')
      
      if (healthyAgents.length === 0) {
        throw new Error('No healthy agents found. Please ensure backend services are running and connected to the database.')
      }
      
      // Fetch data from database via agents
      const dataPromises = []
      
      // Only fetch from healthy agents
      if (healthResults.find(a => a.name === 'Monitoring Agent' && a.status === 'healthy')) {
        dataPromises.push(fetchSystemOverview())
      }
      
      if (healthResults.find(a => a.name === 'Product Agent' && a.status === 'healthy')) {
        dataPromises.push(fetchProducts())
      }
      
      if (healthResults.find(a => a.name === 'Order Agent' && a.status === 'healthy')) {
        dataPromises.push(fetchOrders())
      }
      
      // Execute all data fetching operations
      await Promise.allSettled(dataPromises)
      
    } catch (error) {
      setError(error.message)
      console.error('Database test failed:', error)
    }
    
    setLoading(false)
  }

  useEffect(() => {
    runDatabaseTests()
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'bg-green-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'healthy': return 'Healthy'
      case 'error': return 'Error'
      default: return 'Unknown'
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Database Integration Test</h1>
            <button
              onClick={onReset}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              ← Back to Interface Selector
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Multi-Agent E-commerce System - Database Integration
            </h2>
            <button
              onClick={runDatabaseTests}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
            >
              {loading ? 'Testing...' : 'Refresh Database Tests'}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="text-red-800">
                  <h3 className="text-sm font-medium">Database Connection Error</h3>
                  <div className="mt-2 text-sm">{error}</div>
                  <div className="mt-2 text-xs text-red-600">
                    Note: This system is configured to use ONLY real database data. 
                    Mock data fallbacks have been disabled to ensure data integrity.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Agent Health Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Database Agent Health Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentStatus.map((agent, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`}></div>
                    <span className="font-medium">{agent.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      agent.status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {getStatusText(agent.status)}
                    </span>
                    {agent.responseTime > 0 && (
                      <span className="text-sm text-gray-500">{agent.responseTime}ms</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* System Overview from Database */}
          {systemOverview && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">System Overview (Database)</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{systemOverview.system_metrics?.cpu_usage || 0}%</div>
                  <div className="text-sm text-gray-600">CPU Usage</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{systemOverview.system_metrics?.memory_usage || 0}%</div>
                  <div className="text-sm text-gray-600">Memory Usage</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">{systemOverview.system_metrics?.response_time || 0}ms</div>
                  <div className="text-sm text-gray-600">Response Time</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{systemOverview.active_alerts || 0}</div>
                  <div className="text-sm text-gray-600">Active Alerts</div>
                </div>
              </div>
              <div className="text-sm text-gray-500">
                Last updated: {new Date(systemOverview.timestamp).toLocaleString()}
              </div>
            </div>
          )}

          {/* Products from Database */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Products from Database ({products.length})</h3>
            {products.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {products.slice(0, 6).map((product) => (
                  <div key={product.id} className="border rounded-lg p-4">
                    <div className="font-medium">{product.name}</div>
                    <div className="text-sm text-gray-600 mb-2">{product.description || product.sku}</div>
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-green-600">${product.price}</span>
                      <span className="text-sm text-gray-500">Stock: {product.stock}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No products found in database.</p>
                <p className="text-sm mt-2">Ensure the Product Agent is connected to a populated database.</p>
              </div>
            )}
          </div>

          {/* Orders from Database */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Orders from Database ({orders.length})</h3>
            {orders.length > 0 ? (
              <div className="space-y-4">
                {orders.slice(0, 5).map((order) => (
                  <div key={order.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="font-medium">{order.order_number}</div>
                      <div className="text-sm text-gray-600">
                        {order.customer_name} {order.customer_email && `- ${order.customer_email}`}
                      </div>
                      <div className="text-sm text-gray-500">
                        Total: ${order.total}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                        order.status === 'shipped' ? 'bg-blue-100 text-blue-800' :
                        order.status === 'processing' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {order.status}
                      </span>
                      <div className="text-sm text-gray-500 mt-1">
                        {new Date(order.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No orders found in database.</p>
                <p className="text-sm mt-2">Ensure the Order Agent is connected to a populated database.</p>
              </div>
            )}
          </div>

          {/* Database Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Database Integration Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium">Database Connection</div>
                  <div className="text-sm text-gray-500">Direct connection to PostgreSQL database</div>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  systemOverview ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {systemOverview ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium">Real-time Data Sync</div>
                  <div className="text-sm text-gray-500">Live data synchronization with agents</div>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  agentStatus.some(a => a.status === 'healthy') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {agentStatus.some(a => a.status === 'healthy') ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium">Mock Data Fallback</div>
                  <div className="text-sm text-gray-500">Fallback to mock data when database unavailable</div>
                </div>
                <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                  DISABLED
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
