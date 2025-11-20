import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Merchant Analytics
 * 
 * Comprehensive analytics dashboard for merchants with sales data,
 * customer insights, marketplace performance, and inventory analytics.
 */
function Analytics() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('30d'); // 7d, 30d, 90d, 1y, custom
  const [customDateRange, setCustomDateRange] = useState({
    startDate: '',
    endDate: ''
  });
  const [salesData, setSalesData] = useState({
    revenue: 0,
    orders: 0,
    aov: 0,
    growth: 0,
    chart: []
  });
  const [productData, setProductData] = useState({
    topProducts: [],
    categoryBreakdown: []
  });
  const [customerData, setCustomerData] = useState({
    newCustomers: 0,
    repeatRate: 0,
    averageLifetimeValue: 0,
    geographicDistribution: []
  });
  const [marketplaceData, setMarketplaceData] = useState({
    breakdown: [],
    performance: []
  });
  const [inventoryData, setInventoryData] = useState({
    totalValue: 0,
    turnoverRate: 0,
    lowStockItems: 0,
    warehouseUtilization: []
  });
  const [activeTab, setActiveTab] = useState('sales');
  
  // Load analytics data on component mount and when timeRange changes
  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange, customDateRange]);
  
  // Load analytics data from API
  async function loadAnalyticsData() {
    try {
      setLoading(true);
      
      let dateParams = { timeRange };
      if (timeRange === 'custom') {
        dateParams = {
          startDate: customDateRange.startDate,
          endDate: customDateRange.endDate
        };
      }
      
      // Load sales data
      const sales = await apiService.getSalesAnalytics(dateParams);
      setSalesData(sales);
      
      // Load product data
      const products = await apiService.getProductAnalytics(dateParams);
      setProductData(products);
      
      // Load customer data
      const customers = await apiService.getCustomerAnalytics(dateParams);
      setCustomerData(customers);
      
      // Load marketplace data
      const marketplaces = await apiService.getMarketplaceAnalytics(dateParams);
      setMarketplaceData(marketplaces);
      
      // Load inventory data
      const inventory = await apiService.getInventoryAnalytics(dateParams);
      setInventoryData(inventory);
      
      setError(null);
    } catch (err) {
      setError("Failed to load analytics data: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Handle time range change
  function handleTimeRangeChange(range) {
    setTimeRange(range);
  }
  
  // Handle custom date range change
  function handleCustomDateChange(e) {
    const { name, value } = e.target;
    setCustomDateRange(prev => ({
      ...prev,
      [name]: value
    }));
  }
  
  // Handle custom date range submit
  function handleCustomDateSubmit(e) {
    e.preventDefault();
    loadAnalyticsData();
  }
  
  // Format currency
  function formatCurrency(amount) {
    // Handle NaN, null, undefined, or invalid values
    const validAmount = (amount && !isNaN(amount)) ? amount : 0;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(validAmount);
  }
  
  // Format percentage
  function formatPercentage(value) {
    // Handle NaN, null, undefined, or invalid values
    const validValue = (value && !isNaN(value)) ? value : 0;
    return `${(validValue * 100).toFixed(1)}%`;
  }
  
  // Format number with commas
  function formatNumber(num) {
    // Handle NaN, null, undefined, or invalid values
    const validNum = (num && !isNaN(num)) ? num : 0;
    return new Intl.NumberFormat('en-US').format(validNum);
  }
  
  // Get trend indicator class
  function getTrendClass(value) {
    if (value > 0) {
      return 'text-green-500';
    } else if (value < 0) {
      return 'text-red-500';
    }
    return 'text-gray-500';
  }
  
  // Get trend indicator icon
  function getTrendIcon(value) {
    if (value > 0) {
      return (
        <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      );
    } else if (value < 0) {
      return (
        <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      );
    }
    return (
      <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h14" />
      </svg>
    );
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col md:flex-row md:justify-between md:items-center space-y-4 md:space-y-0">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        
        <div className="flex flex-wrap items-center space-x-2">
          <button
            onClick={() => handleTimeRangeChange('7d')}
            className={`px-3 py-1 rounded-md text-sm ${
              timeRange === '7d'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            7 Days
          </button>
          <button
            onClick={() => handleTimeRangeChange('30d')}
            className={`px-3 py-1 rounded-md text-sm ${
              timeRange === '30d'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            30 Days
          </button>
          <button
            onClick={() => handleTimeRangeChange('90d')}
            className={`px-3 py-1 rounded-md text-sm ${
              timeRange === '90d'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            90 Days
          </button>
          <button
            onClick={() => handleTimeRangeChange('1y')}
            className={`px-3 py-1 rounded-md text-sm ${
              timeRange === '1y'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            1 Year
          </button>
          <button
            onClick={() => handleTimeRangeChange('custom')}
            className={`px-3 py-1 rounded-md text-sm ${
              timeRange === 'custom'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Custom
          </button>
        </div>
      </div>
      
      {timeRange === 'custom' && (
        <div className="mb-6 bg-white p-4 rounded-lg shadow-md">
          <form onSubmit={handleCustomDateSubmit} className="flex flex-wrap items-end space-x-0 space-y-2 sm:space-y-0 sm:space-x-4">
            <div>
              <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                id="startDate"
                name="startDate"
                value={customDateRange.startDate}
                onChange={handleCustomDateChange}
                required
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                id="endDate"
                name="endDate"
                value={customDateRange.endDate}
                onChange={handleCustomDateChange}
                required
                min={customDateRange.startDate}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <button
                type="submit"
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
              >
                Apply
              </button>
            </div>
          </form>
        </div>
      )}
      
      <div className="mb-6 bg-white rounded-lg shadow-md overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex">
            <button
              onClick={() => setActiveTab('sales')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'sales'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Sales
            </button>
            <button
              onClick={() => setActiveTab('products')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'products'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Products
            </button>
            <button
              onClick={() => setActiveTab('customers')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'customers'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Customers
            </button>
            <button
              onClick={() => setActiveTab('marketplaces')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'marketplaces'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Marketplaces
            </button>
            <button
              onClick={() => setActiveTab('inventory')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'inventory'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Inventory
            </button>
          </nav>
        </div>
        
        <div className="p-6">
          {loading && (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          )}
          
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
              <p>{error}</p>
              <button
                onClick={loadAnalyticsData}
                className="mt-2 bg-red-200 hover:bg-red-300 text-red-700 px-3 py-1 rounded"
              >
                Try Again
              </button>
            </div>
          )}
          
          {!loading && !error && activeTab === 'sales' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Total Revenue</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(salesData.revenue)}</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(salesData.growth)}`}>
                      {getTrendIcon(salesData.growth)}
                      <span className="ml-1 text-sm">{formatPercentage(salesData.growth)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Total Orders</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(salesData.orders)}</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(salesData.orderGrowth)}`}>
                      {getTrendIcon(salesData.orderGrowth)}
                      <span className="ml-1 text-sm">{formatPercentage(salesData.orderGrowth)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Average Order Value</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(salesData.aov)}</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(salesData.aovGrowth)}`}>
                      {getTrendIcon(salesData.aovGrowth)}
                      <span className="ml-1 text-sm">{formatPercentage(salesData.aovGrowth)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Conversion Rate</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatPercentage(salesData.conversionRate)}</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(salesData.conversionGrowth)}`}>
                      {getTrendIcon(salesData.conversionGrowth)}
                      <span className="ml-1 text-sm">{formatPercentage(salesData.conversionGrowth)}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 mb-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Revenue Over Time</h3>
                <div className="h-80">
                  {/* This would be a chart component in a real application */}
                  <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-500">Revenue chart would be displayed here</p>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Sales by Channel</h3>
                  <div className="h-64">
                    {/* This would be a pie chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Channel distribution chart would be displayed here</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Sales by Payment Method</h3>
                  <div className="h-64">
                    {/* This would be a pie chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Payment method chart would be displayed here</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {!loading && !error && activeTab === 'products' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Total Products</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(productData.totalProducts)}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Active Products</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(productData.activeProducts)}</p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatPercentage(productData.activeProducts / productData.totalProducts)}
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Out of Stock</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(productData.outOfStockProducts)}</p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatPercentage(productData.outOfStockProducts / productData.totalProducts)}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Top Selling Products</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Product
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Units Sold
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Revenue
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {productData.topProducts.map((product, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                {product.image ? (
                                  <img
                                    src={product.image}
                                    alt={product.name}
                                    className="h-10 w-10 rounded-md object-cover mr-3"
                                  />
                                ) : (
                                  <div className="h-10 w-10 rounded-md bg-gray-200 flex items-center justify-center mr-3">
                                    <span className="text-gray-500 text-xs">No img</span>
                                  </div>
                                )}
                                <div>
                                  <div className="font-medium text-gray-900">{product.name}</div>
                                  <div className="text-sm text-gray-500">{product.sku}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatNumber(product.unitsSold)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(product.revenue)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Sales by Category</h3>
                  <div className="h-64 mb-4">
                    {/* This would be a pie chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Category distribution chart would be displayed here</p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Category
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Revenue
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            %
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {productData.categoryBreakdown.map((category, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {category.name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(category.revenue)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatPercentage(category.percentage)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {!loading && !error && activeTab === 'customers' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Total Customers</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(customerData.totalCustomers)}</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(customerData.customerGrowth)}`}>
                      {getTrendIcon(customerData.customerGrowth)}
                      <span className="ml-1 text-sm">{formatPercentage(customerData.customerGrowth)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">New Customers</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(customerData.newCustomers)}</p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatPercentage(customerData.newCustomers / customerData.totalCustomers)}
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Repeat Rate</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatPercentage(customerData.repeatRate)}</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(customerData.repeatRateGrowth)}`}>
                      {getTrendIcon(customerData.repeatRateGrowth)}
                      <span className="ml-1 text-sm">{formatPercentage(customerData.repeatRateGrowth)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Avg. Lifetime Value</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(customerData.averageLifetimeValue)}</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(customerData.ltvGrowth)}`}>
                      {getTrendIcon(customerData.ltvGrowth)}
                      <span className="ml-1 text-sm">{formatPercentage(customerData.ltvGrowth)}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Acquisition</h3>
                  <div className="h-64">
                    {/* This would be a line chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Customer acquisition chart would be displayed here</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Geographic Distribution</h3>
                  <div className="h-64">
                    {/* This would be a map chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Geographic distribution map would be displayed here</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Segments</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Segment
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Customers
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Revenue
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Avg. Order Value
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Lifetime Value
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {customerData.segments?.map((segment, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {segment.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatNumber(segment.customers)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(segment.revenue)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(segment.aov)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(segment.ltv)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
          
          {!loading && !error && activeTab === 'marketplaces' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Marketplace Revenue</h3>
                  <div className="h-64 mb-4">
                    {/* This would be a pie chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Marketplace revenue chart would be displayed here</p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Marketplace
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Revenue
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            %
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Growth
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {marketplaceData.breakdown.map((marketplace, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <img
                                  src={marketplace.logo}
                                  alt={marketplace.name}
                                  className="h-6 object-contain mr-3"
                                />
                                <div className="font-medium text-gray-900">{marketplace.name}</div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(marketplace.revenue)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatPercentage(marketplace.percentage)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className={`flex items-center ${getTrendClass(marketplace.growth)}`}>
                                {getTrendIcon(marketplace.growth)}
                                <span className="ml-1 text-sm">{formatPercentage(marketplace.growth)}</span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Marketplace Performance</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Marketplace
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Orders
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            AOV
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Conversion
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Rating
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {marketplaceData.performance.map((marketplace, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <img
                                  src={marketplace.logo}
                                  alt={marketplace.name}
                                  className="h-6 object-contain mr-3"
                                />
                                <div className="font-medium text-gray-900">{marketplace.name}</div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatNumber(marketplace.orders)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(marketplace.aov)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatPercentage(marketplace.conversionRate)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-sm font-medium text-gray-900 mr-1">{marketplace.rating.toFixed(1)}</span>
                                <div className="flex text-yellow-400">
                                  {[1, 2, 3, 4, 5].map(star => (
                                    <svg
                                      key={star}
                                      className={`h-4 w-4 ${star <= Math.round(marketplace.rating) ? 'text-yellow-400' : 'text-gray-300'}`}
                                      fill="currentColor"
                                      viewBox="0 0 20 20"
                                    >
                                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                    </svg>
                                  ))}
                                </div>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Marketplace Fees</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Marketplace
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Revenue
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Commission
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Fee %
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Net Revenue
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Margin
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {marketplaceData.fees?.map((marketplace, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <img
                                src={marketplace.logo}
                                alt={marketplace.name}
                                className="h-6 object-contain mr-3"
                              />
                              <div className="font-medium text-gray-900">{marketplace.name}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(marketplace.revenue)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(marketplace.commission)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatPercentage(marketplace.feePercentage)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(marketplace.netRevenue)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatPercentage(marketplace.margin)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
          
          {!loading && !error && activeTab === 'inventory' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Total Inventory Value</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(inventoryData.totalValue)}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Inventory Turnover</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{inventoryData.turnoverRate.toFixed(1)}x</p>
                    </div>
                    <div className={`flex items-center ${getTrendClass(inventoryData.turnoverGrowth)}`}>
                      {getTrendIcon(inventoryData.turnoverGrowth)}
                      <span className="ml-1 text-sm">{formatPercentage(inventoryData.turnoverGrowth)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Low Stock Items</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(inventoryData.lowStockItems)}</p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatPercentage(inventoryData.lowStockItems / inventoryData.totalItems)}
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Out of Stock Items</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatNumber(inventoryData.outOfStockItems)}</p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatPercentage(inventoryData.outOfStockItems / inventoryData.totalItems)}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Warehouse Utilization</h3>
                  <div className="h-64 mb-4">
                    {/* This would be a bar chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Warehouse utilization chart would be displayed here</p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Warehouse
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Capacity
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Utilization
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {inventoryData.warehouseUtilization.map((warehouse, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {warehouse.name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatNumber(warehouse.capacity)} units
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-full bg-gray-200 rounded-full h-2.5">
                                  <div
                                    className={`h-2.5 rounded-full ${
                                      warehouse.utilization > 0.9 ? 'bg-red-500' :
                                      warehouse.utilization > 0.7 ? 'bg-yellow-500' : 'bg-green-500'
                                    }`}
                                    style={{ width: `${warehouse.utilization * 100}%` }}
                                  ></div>
                                </div>
                                <span className="ml-2 text-sm text-gray-900">
                                  {formatPercentage(warehouse.utilization)}
                                </span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Inventory Aging</h3>
                  <div className="h-64 mb-4">
                    {/* This would be a pie chart component in a real application */}
                    <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-gray-500">Inventory aging chart would be displayed here</p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Age
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Items
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Value
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            %
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {inventoryData.aging?.map((age, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {age.range}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatNumber(age.items)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(age.value)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatPercentage(age.percentage)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Inventory Alerts</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Product
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          SKU
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Current Stock
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Threshold
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Action
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {inventoryData.alerts?.map((alert, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {alert.image ? (
                                <img
                                  src={alert.image}
                                  alt={alert.name}
                                  className="h-10 w-10 rounded-md object-cover mr-3"
                                />
                              ) : (
                                <div className="h-10 w-10 rounded-md bg-gray-200 flex items-center justify-center mr-3">
                                  <span className="text-gray-500 text-xs">No img</span>
                                </div>
                              )}
                              <div className="font-medium text-gray-900">{alert.name}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {alert.sku}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatNumber(alert.currentStock)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatNumber(alert.threshold)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              alert.currentStock === 0
                                ? 'bg-red-100 text-red-800'
                                : alert.currentStock < alert.threshold
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-green-100 text-green-800'
                            }`}>
                              {alert.currentStock === 0
                                ? 'Out of Stock'
                                : alert.currentStock < alert.threshold
                                ? 'Low Stock'
                                : 'In Stock'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button className="text-blue-600 hover:text-blue-900">
                              Reorder
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Analytics;
