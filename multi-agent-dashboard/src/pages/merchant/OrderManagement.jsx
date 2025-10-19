import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Order Management
 * 
 * Interface for managing orders across all marketplaces,
 * including processing, fulfillment, and tracking.
 */
function OrderManagement() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    marketplace: '',
    dateRange: '7d' // 7d, 30d, 90d, custom
  });
  const [customDateRange, setCustomDateRange] = useState({
    startDate: '',
    endDate: ''
  });
  const [sort, setSort] = useState({ field: 'createdAt', direction: 'desc' });
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: 10
  });
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [bulkActionMenuOpen, setBulkActionMenuOpen] = useState(false);
  const [marketplaces, setMarketplaces] = useState([]);
  const [showOrderDetailsModal, setShowOrderDetailsModal] = useState(false);
  const [selectedOrderDetails, setSelectedOrderDetails] = useState(null);
  
  // Load orders on component mount and when filters, sort, or pagination change
  useEffect(() => {
    loadOrders();
  }, [filters, sort, pagination.currentPage, pagination.itemsPerPage]);
  
  // Load marketplaces on component mount
  useEffect(() => {
    async function loadMarketplaces() {
      try {
        const marketplacesData = await apiService.getMarketplaces();
        setMarketplaces(marketplacesData);
      } catch (err) {
        console.error("Failed to load marketplaces:", err);
      }
    }
    
    loadMarketplaces();
  }, []);
  
  // Load orders from API
  async function loadOrders() {
    try {
      setLoading(true);
      
      const params = {
        page: pagination.currentPage,
        limit: pagination.itemsPerPage,
        search: searchTerm,
        sortBy: sort.field,
        sortDirection: sort.direction,
        ...filters
      };
      
      // Add custom date range if selected
      if (filters.dateRange === 'custom') {
        params.startDate = customDateRange.startDate;
        params.endDate = customDateRange.endDate;
      }
      
      const data = await apiService.getOrders(params);
      
      setOrders(data.orders);
      setPagination({
        ...pagination,
        totalPages: data.totalPages,
        totalItems: data.totalItems
      });
      
      setError(null);
    } catch (err) {
      setError("Failed to load orders: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Handle search
  function handleSearch(e) {
    e.preventDefault();
    loadOrders();
  }
  
  // Handle filter change
  function handleFilterChange(e) {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
    setPagination(prev => ({
      ...prev,
      currentPage: 1 // Reset to first page when filters change
    }));
  }
  
  // Handle custom date range change
  function handleDateRangeChange(e) {
    const { name, value } = e.target;
    setCustomDateRange(prev => ({
      ...prev,
      [name]: value
    }));
  }
  
  // Handle sort change
  function handleSortChange(field) {
    setSort(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  }
  
  // Handle page change
  function handlePageChange(page) {
    setPagination(prev => ({
      ...prev,
      currentPage: page
    }));
  }
  
  // Handle order selection
  function handleOrderSelection(orderId) {
    setSelectedOrders(prev => {
      if (prev.includes(orderId)) {
        return prev.filter(id => id !== orderId);
      } else {
        return [...prev, orderId];
      }
    });
  }
  
  // Handle select all orders
  function handleSelectAllOrders() {
    if (selectedOrders.length === orders.length) {
      setSelectedOrders([]);
    } else {
      setSelectedOrders(orders.map(order => order.id));
    }
  }
  
  // Handle bulk action
  async function handleBulkAction(action) {
    if (selectedOrders.length === 0) return;
    
    try {
      switch (action) {
        case 'print':
          // Open print modal or redirect to print page
          window.open(`/merchant/orders/print?ids=${selectedOrders.join(',')}`, '_blank');
          break;
        case 'export':
          // Export orders to CSV
          const csvData = await apiService.exportOrders(selectedOrders);
          const blob = new Blob([csvData], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.setAttribute('hidden', '');
          a.setAttribute('href', url);
          a.setAttribute('download', `orders-export-${new Date().toISOString().slice(0, 10)}.csv`);
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          break;
        case 'mark-shipped':
          await apiService.bulkUpdateOrderStatus(selectedOrders, 'shipped');
          loadOrders();
          break;
        case 'cancel':
          if (window.confirm(`Are you sure you want to cancel ${selectedOrders.length} orders?`)) {
            await apiService.bulkUpdateOrderStatus(selectedOrders, 'cancelled');
            loadOrders();
          }
          break;
        default:
          break;
      }
      
      setBulkActionMenuOpen(false);
    } catch (err) {
      setError(`Failed to perform bulk action: ${err.message}`);
      console.error(err);
    }
  }
  
  // Handle view order details
  async function handleViewOrderDetails(orderId) {
    try {
      const orderDetails = await apiService.getOrderDetails(orderId);
      setSelectedOrderDetails(orderDetails);
      setShowOrderDetailsModal(true);
    } catch (err) {
      setError(`Failed to load order details: ${err.message}`);
      console.error(err);
    }
  }
  
  // Handle update order status
  async function handleUpdateOrderStatus(orderId, status) {
    try {
      await apiService.updateOrderStatus(orderId, status);
      
      // If we're viewing the order details, update them
      if (selectedOrderDetails && selectedOrderDetails.id === orderId) {
        setSelectedOrderDetails(prev => ({
          ...prev,
          status
        }));
      }
      
      // Refresh the orders list
      loadOrders();
    } catch (err) {
      setError(`Failed to update order status: ${err.message}`);
      console.error(err);
    }
  }
  
  // Format date
  function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }
  
  // Format currency
  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }
  
  // Get status badge class
  function getStatusBadgeClass(status) {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'shipped':
        return 'bg-purple-100 text-purple-800';
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'refunded':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col md:flex-row md:justify-between md:items-center space-y-4 md:space-y-0">
        <h1 className="text-2xl font-bold text-gray-900">Order Management</h1>
        
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
          {selectedOrders.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setBulkActionMenuOpen(!bulkActionMenuOpen)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
              >
                Actions ({selectedOrders.length})
              </button>
              
              {bulkActionMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                  <div className="py-1">
                    <button
                      onClick={() => handleBulkAction('print')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Print Packing Slips
                    </button>
                    <button
                      onClick={() => handleBulkAction('export')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Export to CSV
                    </button>
                    <button
                      onClick={() => handleBulkAction('mark-shipped')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Mark as Shipped
                    </button>
                    <button
                      onClick={() => handleBulkAction('cancel')}
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                    >
                      Cancel Orders
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <button
            onClick={() => navigate('/merchant/orders/create')}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md"
          >
            Create Manual Order
          </button>
        </div>
      </div>
      
      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row md:items-end space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Search Orders</label>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by order ID, customer name, or email"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              id="status"
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="shipped">Shipped</option>
              <option value="delivered">Delivered</option>
              <option value="cancelled">Cancelled</option>
              <option value="refunded">Refunded</option>
            </select>
          </div>
          
          <div>
            <label htmlFor="marketplace" className="block text-sm font-medium text-gray-700 mb-1">Marketplace</label>
            <select
              id="marketplace"
              name="marketplace"
              value={filters.marketplace}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Marketplaces</option>
              {marketplaces.map(marketplace => (
                <option key={marketplace.id} value={marketplace.id}>{marketplace.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="dateRange" className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
            <select
              id="dateRange"
              name="dateRange"
              value={filters.dateRange}
              onChange={handleFilterChange}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
          
          {filters.dateRange === 'custom' && (
            <>
              <div>
                <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  id="startDate"
                  name="startDate"
                  value={customDateRange.startDate}
                  onChange={handleDateRangeChange}
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
                  onChange={handleDateRangeChange}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          )}
          
          <div>
            <button
              type="submit"
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
            >
              Search
            </button>
          </div>
        </form>
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
            onClick={loadOrders}
            className="mt-2 bg-red-200 hover:bg-red-300 text-red-700 px-3 py-1 rounded"
          >
            Try Again
          </button>
        </div>
      )}
      
      {!loading && !error && (
        <>
          {/* Orders Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedOrders.length === orders.length && orders.length > 0}
                          onChange={handleSelectAllOrders}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('id')}
                        className="flex items-center focus:outline-none"
                      >
                        Order ID
                        {sort.field === 'id' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('createdAt')}
                        className="flex items-center focus:outline-none"
                      >
                        Date
                        {sort.field === 'createdAt' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('customer')}
                        className="flex items-center focus:outline-none"
                      >
                        Customer
                        {sort.field === 'customer' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('total')}
                        className="flex items-center focus:outline-none"
                      >
                        Total
                        {sort.field === 'total' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSortChange('status')}
                        className="flex items-center focus:outline-none"
                      >
                        Status
                        {sort.field === 'status' && (
                          <span className="ml-1">
                            {sort.direction === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </button>
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Marketplace
                    </th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {orders.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="px-6 py-4 text-center text-gray-500">
                        No orders found. Try adjusting your search or filters.
                      </td>
                    </tr>
                  ) : (
                    orders.map(order => (
                      <tr key={order.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedOrders.includes(order.id)}
                            onChange={() => handleOrderSelection(order.id)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {order.id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(order.createdAt)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{order.customer.name}</div>
                          <div className="text-sm text-gray-500">{order.customer.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(order.total)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(order.status)}`}>
                            {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {order.marketplace.icon && (
                              <img
                                src={order.marketplace.icon}
                                alt={order.marketplace.name}
                                className="h-5 w-5 mr-2"
                              />
                            )}
                            <span className="text-sm text-gray-900">{order.marketplace.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleViewOrderDetails(order.id)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            View
                          </button>
                          <Link
                            to={`/merchant/orders/${order.id}/edit`}
                            className="text-indigo-600 hover:text-indigo-900 mr-3"
                          >
                            Edit
                          </Link>
                          <button
                            onClick={() => {
                              if (window.confirm(`Are you sure you want to cancel order ${order.id}?`)) {
                                handleUpdateOrderStatus(order.id, 'cancelled');
                              }
                            }}
                            className="text-red-600 hover:text-red-900"
                          >
                            Cancel
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Pagination */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing <span className="font-medium">{(pagination.currentPage - 1) * pagination.itemsPerPage + 1}</span> to{' '}
              <span className="font-medium">
                {Math.min(pagination.currentPage * pagination.itemsPerPage, pagination.totalItems)}
              </span>{' '}
              of <span className="font-medium">{pagination.totalItems}</span> orders
            </div>
            
            <div className="flex items-center space-x-2">
              <select
                value={pagination.itemsPerPage}
                onChange={(e) => setPagination(prev => ({
                  ...prev,
                  itemsPerPage: Number(e.target.value),
                  currentPage: 1
                }))}
                className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="10">10 per page</option>
                <option value="25">25 per page</option>
                <option value="50">50 per page</option>
                <option value="100">100 per page</option>
              </select>
              
              <nav className="flex items-center">
                <button
                  onClick={() => handlePageChange(pagination.currentPage - 1)}
                  disabled={pagination.currentPage === 1}
                  className={`px-3 py-1 rounded-md ${
                    pagination.currentPage === 1
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Previous
                </button>
                
                <div className="flex items-center mx-2">
                  {Array.from({ length: pagination.totalPages }, (_, i) => i + 1)
                    .filter(pageNum => {
                      // Show first page, last page, and pages around current page
                      return (
                        pageNum === 1 ||
                        pageNum === pagination.totalPages ||
                        (pageNum >= pagination.currentPage - 2 && pageNum <= pagination.currentPage + 2)
                      );
                    })
                    .map((pageNum, index, array) => {
                      // Add ellipsis between non-consecutive pages
                      if (index > 0 && pageNum - array[index - 1] > 1) {
                        return (
                          <span key={`ellipsis-${pageNum}`} className="px-1">...</span>
                        );
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`w-8 h-8 flex items-center justify-center rounded-md mx-1 ${
                            pagination.currentPage === pageNum
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                </div>
                
                <button
                  onClick={() => handlePageChange(pagination.currentPage + 1)}
                  disabled={pagination.currentPage === pagination.totalPages}
                  className={`px-3 py-1 rounded-md ${
                    pagination.currentPage === pagination.totalPages
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </>
      )}
      
      {/* Order Details Modal */}
      {showOrderDetailsModal && selectedOrderDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  Order #{selectedOrderDetails.id}
                </h2>
                <button
                  onClick={() => setShowOrderDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Order Information</h3>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">Date</p>
                        <p className="font-medium">{formatDate(selectedOrderDetails.createdAt)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Status</p>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(selectedOrderDetails.status)}`}>
                          {selectedOrderDetails.status.charAt(0).toUpperCase() + selectedOrderDetails.status.slice(1)}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Payment Method</p>
                        <p className="font-medium">{selectedOrderDetails.paymentMethod}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Marketplace</p>
                        <div className="flex items-center">
                          {selectedOrderDetails.marketplace.icon && (
                            <img
                              src={selectedOrderDetails.marketplace.icon}
                              alt={selectedOrderDetails.marketplace.name}
                              className="h-4 w-4 mr-1"
                            />
                          )}
                          <span className="font-medium">{selectedOrderDetails.marketplace.name}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Customer Information</h3>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <p className="font-medium">{selectedOrderDetails.customer.name}</p>
                    <p className="text-gray-500">{selectedOrderDetails.customer.email}</p>
                    <p className="text-gray-500">{selectedOrderDetails.customer.phone}</p>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Shipping Address</h3>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <p className="font-medium">{selectedOrderDetails.shippingAddress.name}</p>
                    <p className="text-gray-500">{selectedOrderDetails.shippingAddress.street}</p>
                    <p className="text-gray-500">
                      {selectedOrderDetails.shippingAddress.city}, {selectedOrderDetails.shippingAddress.state} {selectedOrderDetails.shippingAddress.zip}
                    </p>
                    <p className="text-gray-500">{selectedOrderDetails.shippingAddress.country}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Billing Address</h3>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <p className="font-medium">{selectedOrderDetails.billingAddress.name}</p>
                    <p className="text-gray-500">{selectedOrderDetails.billingAddress.street}</p>
                    <p className="text-gray-500">
                      {selectedOrderDetails.billingAddress.city}, {selectedOrderDetails.billingAddress.state} {selectedOrderDetails.billingAddress.zip}
                    </p>
                    <p className="text-gray-500">{selectedOrderDetails.billingAddress.country}</p>
                  </div>
                </div>
              </div>
              
              <h3 className="text-lg font-medium text-gray-900 mb-2">Order Items</h3>
              <div className="bg-gray-50 rounded-md overflow-hidden mb-6">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {selectedOrderDetails.items.map(item => (
                      <tr key={item.id} className="hover:bg-gray-100">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {item.image ? (
                              <img
                                src={item.image}
                                alt={item.name}
                                className="h-10 w-10 rounded-md object-cover mr-3"
                              />
                            ) : (
                              <div className="h-10 w-10 rounded-md bg-gray-200 flex items-center justify-center mr-3">
                                <span className="text-gray-500 text-xs">No img</span>
                              </div>
                            )}
                            <span className="font-medium text-gray-900">{item.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.sku}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                          {formatCurrency(item.price)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                          {item.quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                          {formatCurrency(item.price * item.quantity)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr>
                      <td colSpan="4" className="px-6 py-3 text-right text-sm font-medium text-gray-500">
                        Subtotal
                      </td>
                      <td className="px-6 py-3 text-right text-sm font-medium text-gray-900">
                        {formatCurrency(selectedOrderDetails.subtotal)}
                      </td>
                    </tr>
                    <tr>
                      <td colSpan="4" className="px-6 py-3 text-right text-sm font-medium text-gray-500">
                        Shipping
                      </td>
                      <td className="px-6 py-3 text-right text-sm font-medium text-gray-900">
                        {formatCurrency(selectedOrderDetails.shipping)}
                      </td>
                    </tr>
                    <tr>
                      <td colSpan="4" className="px-6 py-3 text-right text-sm font-medium text-gray-500">
                        Tax
                      </td>
                      <td className="px-6 py-3 text-right text-sm font-medium text-gray-900">
                        {formatCurrency(selectedOrderDetails.tax)}
                      </td>
                    </tr>
                    <tr>
                      <td colSpan="4" className="px-6 py-3 text-right text-sm font-bold text-gray-900">
                        Total
                      </td>
                      <td className="px-6 py-3 text-right text-sm font-bold text-gray-900">
                        {formatCurrency(selectedOrderDetails.total)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              
              {selectedOrderDetails.trackingInfo && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Shipping Information</h3>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">Carrier</p>
                        <p className="font-medium">{selectedOrderDetails.trackingInfo.carrier}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Tracking Number</p>
                        <p className="font-medium">{selectedOrderDetails.trackingInfo.trackingNumber}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Shipped Date</p>
                        <p className="font-medium">{formatDate(selectedOrderDetails.trackingInfo.shippedDate)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Estimated Delivery</p>
                        <p className="font-medium">{formatDate(selectedOrderDetails.trackingInfo.estimatedDelivery)}</p>
                      </div>
                    </div>
                    
                    {selectedOrderDetails.trackingInfo.trackingUrl && (
                      <a
                        href={selectedOrderDetails.trackingInfo.trackingUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-flex items-center text-blue-600 hover:text-blue-800"
                      >
                        Track Package
                        <svg className="ml-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              )}
              
              <div className="flex justify-between items-center">
                <div className="flex space-x-2">
                  <button
                    onClick={() => window.open(`/merchant/orders/${selectedOrderDetails.id}/print`, '_blank')}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-2 rounded-md"
                  >
                    Print
                  </button>
                  <Link
                    to={`/merchant/orders/${selectedOrderDetails.id}/edit`}
                    className="bg-blue-100 hover:bg-blue-200 text-blue-800 px-4 py-2 rounded-md"
                  >
                    Edit
                  </Link>
                </div>
                
                <div className="flex space-x-2">
                  {selectedOrderDetails.status === 'pending' && (
                    <button
                      onClick={() => handleUpdateOrderStatus(selectedOrderDetails.id, 'processing')}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
                    >
                      Process Order
                    </button>
                  )}
                  
                  {selectedOrderDetails.status === 'processing' && (
                    <button
                      onClick={() => handleUpdateOrderStatus(selectedOrderDetails.id, 'shipped')}
                      className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-md"
                    >
                      Mark as Shipped
                    </button>
                  )}
                  
                  {selectedOrderDetails.status === 'shipped' && (
                    <button
                      onClick={() => handleUpdateOrderStatus(selectedOrderDetails.id, 'delivered')}
                      className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md"
                    >
                      Mark as Delivered
                    </button>
                  )}
                  
                  {['pending', 'processing'].includes(selectedOrderDetails.status) && (
                    <button
                      onClick={() => {
                        if (window.confirm(`Are you sure you want to cancel order #${selectedOrderDetails.id}?`)) {
                          handleUpdateOrderStatus(selectedOrderDetails.id, 'cancelled');
                        }
                      }}
                      className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md"
                    >
                      Cancel Order
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default OrderManagement;
