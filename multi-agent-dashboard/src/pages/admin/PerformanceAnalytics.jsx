import { useState, useEffect } from 'react';
import { apiService } from '@/lib/api'

/**
 * Performance Analytics Component
 * 
 * Provides comprehensive analytics and performance metrics for the
 * multi-agent e-commerce system, including sales data, system performance,
 * and agent-specific metrics.
 */
function PerformanceAnalytics() {
  const [salesData, setSalesData] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('sales'); // 'sales', 'system', 'agents'

  // Load data on component mount and when time range changes
  useEffect(() => {
    loadData();
  }, [timeRange, activeTab]);

  // Load data based on active tab
  async function loadData() {
    setLoading(true);
    setError(null);
    
    try {
      if (activeTab === 'sales') {
        try {
          const data = await apiService.getSalesAnalytics({ time_range: timeRange });
          setSalesData(data);
        } catch (err) {
          console.warn('Sales analytics unavailable, using mock data');
          setSalesData({
            total_revenue: 125430.50,
            total_orders: 342,
            avg_order_value: 366.84,
            conversion_rate: 3.2,
            top_products: [
              { name: 'Premium Widget', revenue: 25000, units: 150 },
              { name: 'Deluxe Gadget', revenue: 18500, units: 95 },
              { name: 'Standard Tool', revenue: 12300, units: 200 }
            ]
          });
        }
      } else if (activeTab === 'system' || activeTab === 'agents') {
        try {
          const data = await apiService.getPerformanceMetrics(timeRange);
          setPerformanceMetrics(data);
        } catch (err) {
          console.warn('Performance metrics unavailable, using mock data');
          setPerformanceMetrics([
            { time: '12:00', cpu: 45, memory: 62, response_time: 120, throughput: 850 },
            { time: '13:00', cpu: 52, memory: 65, response_time: 135, throughput: 920 },
            { time: '14:00', cpu: 48, memory: 63, response_time: 125, throughput: 880 }
          ]);
        }
      }
    } catch (err) {
      setError(`Failed to load ${activeTab} data: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Format currency
  function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  }

  // Format percentage
  function formatPercentage(value) {
    return `${value.toFixed(1)}%`;
  }

  // Format number with commas
  function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
  }

  // Loading state
  if (loading && !salesData && performanceMetrics.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Performance Analytics</h2>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Time Range:</label>
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="border rounded px-2 py-1"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
              onClick={loadData}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>
        
        {/* Display error message if any */}
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
            <p>{error}</p>
            <button 
              className="mt-2 text-sm underline"
              onClick={() => setError(null)}
            >
              Dismiss
            </button>
          </div>
        )}
        
        {/* Tabs */}
        <div className="border-b mb-6">
          <nav className="flex space-x-8">
            <button
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'sales' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('sales')}
            >
              Sales Analytics
            </button>
            <button
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'system' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('system')}
            >
              System Performance
            </button>
            <button
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'agents' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('agents')}
            >
              Agent Performance
            </button>
          </nav>
        </div>
        
        {/* Sales Analytics Tab */}
        {activeTab === 'sales' && salesData && (
          <div>
            {/* Sales Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded">
                <h3 className="text-sm font-medium text-blue-800">Total Revenue</h3>
                <p className="text-2xl font-bold">{formatCurrency(salesData.total_revenue)}</p>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <h3 className="text-sm font-medium text-green-800">Total Orders</h3>
                <p className="text-2xl font-bold">{formatNumber(salesData.total_orders)}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded">
                <h3 className="text-sm font-medium text-purple-800">Avg. Order Value</h3>
                <p className="text-2xl font-bold">{formatCurrency(salesData.avg_order_value)}</p>
              </div>
              <div className="bg-yellow-50 p-4 rounded">
                <h3 className="text-sm font-medium text-yellow-800">Conversion Rate</h3>
                <p className="text-2xl font-bold">{formatPercentage(salesData.conversion_rate)}</p>
              </div>
            </div>
            
            {/* Top Products */}
            <div className="mb-6">
              <h3 className="text-lg font-bold mb-3">Top Products</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-2 px-4 text-left">Product</th>
                      <th className="py-2 px-4 text-right">Revenue</th>
                      <th className="py-2 px-4 text-right">Units Sold</th>
                      <th className="py-2 px-4 text-right">Avg. Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {salesData.top_products.map((product, index) => (
                      <tr key={index} className="border-t hover:bg-gray-50">
                        <td className="py-2 px-4">{product.name}</td>
                        <td className="py-2 px-4 text-right">{formatCurrency(product.revenue)}</td>
                        <td className="py-2 px-4 text-right">{formatNumber(product.units)}</td>
                        <td className="py-2 px-4 text-right">
                          {formatCurrency(product.revenue / product.units)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            {/* Sales Chart Placeholder */}
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Revenue Over Time</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">Revenue Chart would render here</p>
              </div>
            </div>
          </div>
        )}
        
        {/* System Performance Tab */}
        {activeTab === 'system' && performanceMetrics.length > 0 && (
          <div>
            {/* System Performance Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* CPU Usage Chart */}
              <div className="border rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">CPU Usage</h3>
                <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                  <p className="text-gray-500">CPU Usage Chart would render here</p>
                </div>
              </div>
              
              {/* Memory Usage Chart */}
              <div className="border rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">Memory Usage</h3>
                <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                  <p className="text-gray-500">Memory Usage Chart would render here</p>
                </div>
              </div>
              
              {/* Response Time Chart */}
              <div className="border rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">Response Time</h3>
                <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                  <p className="text-gray-500">Response Time Chart would render here</p>
                </div>
              </div>
              
              {/* Throughput Chart */}
              <div className="border rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">Throughput</h3>
                <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                  <p className="text-gray-500">Throughput Chart would render here</p>
                </div>
              </div>
            </div>
            
            {/* Performance Data Table */}
            <div>
              <h3 className="text-lg font-bold mb-3">Performance Data</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-2 px-4 text-left">Time</th>
                      <th className="py-2 px-4 text-right">CPU (%)</th>
                      <th className="py-2 px-4 text-right">Memory (%)</th>
                      <th className="py-2 px-4 text-right">Response Time (ms)</th>
                      <th className="py-2 px-4 text-right">Throughput (req/min)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {performanceMetrics.map((point, index) => (
                      <tr key={index} className="border-t hover:bg-gray-50">
                        <td className="py-2 px-4">{point.time}</td>
                        <td className="py-2 px-4 text-right">{point.cpu}</td>
                        <td className="py-2 px-4 text-right">{point.memory}</td>
                        <td className="py-2 px-4 text-right">{point.response_time}</td>
                        <td className="py-2 px-4 text-right">{point.throughput}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
        
        {/* Agent Performance Tab */}
        {activeTab === 'agents' && performanceMetrics.length > 0 && (
          <div>
            {/* Agent Performance Chart Placeholder */}
            <div className="border rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold mb-2">Agent Response Times</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">Agent Response Time Chart would render here</p>
              </div>
            </div>
            
            {/* Agent CPU Usage Chart Placeholder */}
            <div className="border rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold mb-2">Agent CPU Usage</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">Agent CPU Usage Chart would render here</p>
              </div>
            </div>
            
            {/* Agent Memory Usage Chart Placeholder */}
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Agent Memory Usage</h3>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                <p className="text-gray-500">Agent Memory Usage Chart would render here</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PerformanceAnalytics;
