import React, { useState, useEffect } from 'react';
import { formatLongDate } from '@/utils/dateFormatter';
import { Link } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Customer Orders List Page
 * 
 * Displays a list of all customer orders with status and details.
 */
function OrdersList() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'processing', 'shipped', 'delivered', 'cancelled'
  
  // Load orders on component mount
  useEffect(() => {
    loadOrders();
  }, []);
  
  // Load orders from API
  async function loadOrders() {
    try {
      setLoading(true);
      const data = await apiService.getCustomerOrders();
      setOrders(data || []);
      setError(null);
    } catch (err) {
      setError("Failed to load orders: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Filter orders based on status
  const filteredOrders = filter === 'all' 
    ? orders 
    : orders.filter(order => order.status?.toLowerCase() === filter.toLowerCase());
  
  // Get status badge color
  function getStatusColor(status) {
    if (!status) return 'bg-gray-100 text-gray-800';
    
    switch (status.toLowerCase()) {
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'shipped':
        return 'bg-green-100 text-green-800';
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your orders...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">⚠️ Error</div>
          <p className="text-gray-600">{error}</p>
          <button 
            onClick={loadOrders}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Orders</h1>
          <p className="mt-2 text-gray-600">View and track your order history</p>
        </div>
        
        {/* Filters */}
        <div className="mb-6 flex gap-2 flex-wrap">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            All Orders
          </button>
          <button
            onClick={() => setFilter('processing')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'processing' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Processing
          </button>
          <button
            onClick={() => setFilter('shipped')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'shipped' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Shipped
          </button>
          <button
            onClick={() => setFilter('delivered')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'delivered' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Delivered
          </button>
        </div>
        
        {/* Orders List */}
        {filteredOrders.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-400 text-6xl mb-4">📦</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No orders found</h3>
            <p className="text-gray-600 mb-6">
              {filter === 'all' 
                ? "You haven't placed any orders yet." 
                : `You don't have any ${filter} orders.`}
            </p>
            <Link 
              to="/products"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Start Shopping
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => (
              <div key={order.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Order #{order.id}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Placed on {formatLongDate(order.created_at || order.createdAt)}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                      {order.status || 'Unknown'}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Amount</p>
                      <p className="text-lg font-semibold text-gray-900">
                        ${(order.total_amount || order.totalAmount || 0).toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Items</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {order.items?.length || order.orderItems?.length || 0} item(s)
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Shipping Address</p>
                      <p className="text-sm text-gray-900">
                        {order.shipping_address || order.shippingAddress || 'N/A'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <Link
                      to={`/account/orders/${order.id}`}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      View Details
                    </Link>
                    {order.tracking_number && (
                      <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                        Track Package
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default OrdersList;
