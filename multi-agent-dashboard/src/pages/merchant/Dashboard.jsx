import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Merchant Dashboard
 * 
 * Main dashboard for merchants with key performance indicators,
 * recent orders, inventory alerts, and marketplace performance.
 */
function Dashboard() {
  const [kpis, setKpis] = useState({
    totalSales: 0,
    totalOrders: 0,
    averageOrderValue: 0,
    conversionRate: 0
  });
  const [recentOrders, setRecentOrders] = useState([]);
  const [inventoryAlerts, setInventoryAlerts] = useState([]);
  const [marketplacePerformance, setMarketplacePerformance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('7d'); // 7d, 30d, 90d, 1y
  
  // Load dashboard data on component mount and when timeRange changes
  useEffect(() => {
    loadDashboardData();
  }, [timeRange]);
  
  // Load dashboard data from API
  async function loadDashboardData() {
    try {
      setLoading(true);
      
      // Load KPIs
      const kpiData = await apiService.getMerchantKpis(timeRange);
      setKpis(kpiData);
      
      // Load recent orders
      const orders = await apiService.getRecentOrders();
      setRecentOrders(orders);
      
      // Load inventory alerts
      const alertsResponse = await apiService.getInventoryAlerts();
      setInventoryAlerts(alertsResponse.alerts || alertsResponse || []);
      
      // Load marketplace performance
      const performance = await apiService.getMarketplacePerformance(timeRange);
      setMarketplacePerformance(performance);
      
      setError(null);
    } catch (err) {
      setError("Failed to load dashboard data: " + err.message);
      console.error(err);
    
      // Set empty arrays on error to prevent undefined errors
      setRecentOrders([]);
      setInventoryAlerts([]);
      setMarketplacePerformance([]);
    } finally {
      setLoading(false);
    }
  }
  
  // Format currency
  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }
  
  // Format percentage
  function formatPercent(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value / 100);
  }
  
  // Format date
  function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Merchant Dashboard</h1>
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="1y">Last Year</option>
          </select>
          <button
            onClick={loadDashboardData}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
          >
            Refresh
          </button>
        </div>
      </div>
      
      {loading && (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      )}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <p>{error}</p>
          <button
            onClick={loadDashboardData}
            className="mt-2 bg-red-200 hover:bg-red-300 text-red-700 px-3 py-1 rounded"
          >
            Try Again
          </button>
        </div>
      )}
      
      {!loading && !error && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Total Sales</h3>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.totalSales)}</p>
              <p className={`text-sm ${kpis.salesGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {kpis.salesGrowth >= 0 ? '↑' : '↓'} {Math.abs(kpis.salesGrowth)}% from previous period
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Total Orders</h3>
              <p className="text-2xl font-bold text-gray-900">{kpis.totalOrders}</p>
              <p className={`text-sm ${kpis.ordersGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {kpis.ordersGrowth >= 0 ? '↑' : '↓'} {Math.abs(kpis.ordersGrowth)}% from previous period
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Average Order Value</h3>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.averageOrderValue)}</p>
              <p className={`text-sm ${kpis.aovGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {kpis.aovGrowth >= 0 ? '↑' : '↓'} {Math.abs(kpis.aovGrowth)}% from previous period
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Conversion Rate</h3>
              <p className="text-2xl font-bold text-gray-900">{formatPercent(kpis.conversionRate)}</p>
              <p className={`text-sm ${kpis.conversionGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {kpis.conversionGrowth >= 0 ? '↑' : '↓'} {Math.abs(kpis.conversionGrowth)}% from previous period
              </p>
            </div>
          </div>
          
          {/* Recent Orders */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-gray-900">Recent Orders</h2>
              <Link to="/merchant/orders" className="text-blue-500 hover:text-blue-700">
                View All
              </Link>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order ID</th>
                    <th className="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                    <th className="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {recentOrders.map(order => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 whitespace-nowrap">{order.id}</td>
                      <td className="py-3 px-4 whitespace-nowrap">{formatDate(order.created_at)}</td>
                      <td className="py-3 px-4 whitespace-nowrap">{order.customer}</td>
                      <td className="py-3 px-4 whitespace-nowrap">{formatCurrency(order.total)}</td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          order.status === 'completed' ? 'bg-green-100 text-green-800' :
                          order.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                          order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <Link to={`/merchant/orders/${order.id}`} className="text-blue-500 hover:text-blue-700 mr-3">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Inventory Alerts */}
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-gray-900">Inventory Alerts</h2>
                <Link to="/merchant/inventory" className="text-blue-500 hover:text-blue-700">
                  View All
                </Link>
              </div>
              
              {inventoryAlerts.length === 0 ? (
                <p className="text-gray-500">No inventory alerts at this time.</p>
              ) : (
                <div className="space-y-4">
                  {inventoryAlerts.map(alert => (
                    <div key={alert.id} className="flex items-center justify-between border-b pb-3">
                      <div>
                        <p className="font-medium text-gray-900">{alert.product}</p>
                        <p className="text-sm text-gray-500">
                          {alert.type === 'low_stock' ? 'Low Stock' : 'Out of Stock'} - {alert.warehouse}
                        </p>
                      </div>
                      <div className="flex items-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          alert.type === 'low_stock' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {alert.quantity} left
                        </span>
                        <Link to={`/merchant/products/${alert.productId}`} className="ml-3 text-blue-500 hover:text-blue-700">
                          Restock
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Marketplace Performance */}
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-gray-900">Marketplace Performance</h2>
                <Link to="/merchant/analytics" className="text-blue-500 hover:text-blue-700">
                  View Details
                </Link>
              </div>
              
              <div className="space-y-4">
                {marketplacePerformance.map((marketplace, index) => (
                  <div key={marketplace.marketplace || index} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="font-medium text-gray-900">{marketplace.marketplace}</span>
                      <span className="ml-2 text-sm text-gray-500">({marketplace.orders} orders)</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="font-medium text-gray-900">{formatCurrency(marketplace.sales)}</span>
                      <span className={`text-sm ${marketplace.growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {marketplace.growth >= 0 ? '↑' : '↓'} {Math.abs(marketplace.growth)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
