import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiService } from '@/lib/api'

/**
 * Order Tracking Page
 * 
 * Displays detailed information about a specific order,
 * including order status, delivery tracking, and items.
 */
function OrderTracking() {
  const { orderId } = useParams();
  
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Load order data on component mount
  useEffect(() => {
    loadOrderData();
  }, [orderId]);
  
  // Load order data from API
  async function loadOrderData() {
    try {
      setLoading(true);
      
      const data = await apiService.getOrderDetails(orderId);
      setOrder(data);
      
      setError(null);
    } catch (err) {
      setError("Failed to load order details: " + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }
  
  // Get status color based on order status
  function getStatusColor(status) {
    switch (status.toLowerCase()) {
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'shipped':
        return 'bg-green-100 text-green-800';
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'returned':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }
  
  // Format date
  function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }
  
  // Render loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="bg-white p-6 rounded-lg shadow mb-8">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-8"></div>
              <div className="h-20 bg-gray-200 rounded mb-6"></div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-12 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="flex">
                    <div className="h-16 w-16 bg-gray-200 rounded"></div>
                    <div className="ml-4 flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Order Tracking</h1>
          
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-8">
            <p>{error}</p>
            <button 
              onClick={loadOrderData} 
              className="mt-2 bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded"
            >
              Try Again
            </button>
          </div>
          
          <Link 
            to="/account/orders" 
            className="text-blue-600 hover:text-blue-800 flex items-center"
          >
            <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Back to Orders
          </Link>
        </div>
      </div>
     );
  }
  
  // If order not found
  if (!order) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900">Order Not Found</h2>
          <p className="mt-2 text-gray-600">The order you're looking for doesn't exist or you don't have permission to view it.</p>
          <Link 
            to="/account/orders" 
            className="mt-4 inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            View Your Orders
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Order #{order.order_number}</h1>
            <p className="text-gray-600">Placed on {formatDate(order.order_date)}</p>
          </div>
          
          <div className="mt-4 md:mt-0">
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
              {order.status}
            </span>
          </div>
        </div>
        
        {/* Order Tracking */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-xl font-medium text-gray-900 mb-4">Tracking Information</h2>
          
          {order.tracking_number ? (
            <>
              <div className="flex flex-col md:flex-row md:items-center mb-6">
                <div className="mb-2 md:mb-0 md:mr-6">
                  <span className="text-gray-600">Tracking Number:</span>
                  <span className="ml-2 font-medium">{order.tracking_number}</span>
                </div>
                
                <div className="mb-2 md:mb-0 md:mr-6">
                  <span className="text-gray-600">Carrier:</span>
                  <span className="ml-2 font-medium">{order.carrier}</span>
                </div>
                
                {order.estimated_delivery && (
                  <div>
                    <span className="text-gray-600">Estimated Delivery:</span>
                    <span className="ml-2 font-medium">{formatDate(order.estimated_delivery)}</span>
                  </div>
                )}
              </div>
              
              {/* Tracking Progress */}
              <div className="relative">
                <div className="absolute left-0 top-5 h-0.5 w-full bg-gray-200">
                  <div 
                    className="absolute left-0 top-0 h-full bg-green-500"
                    style={{ width: `${order.progress_percentage}%` }}
                  ></div>
                </div>
                
                <div className="relative flex justify-between">
                  {order.tracking_steps.map((step, index) => {
                    const isCompleted = step.completed;
                    const isCurrent = step.current;
                    
                    return (
                      <div key={index} className="flex flex-col items-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          isCompleted ? 'bg-green-500 text-white' : 
                          isCurrent ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'
                        }`}>
                          {isCompleted ? (
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                            </svg>
                           ) : (
                            <span>{index + 1}</span>
                          )}
                        </div>
                        <div className="mt-2 text-center">
                          <div className="text-sm font-medium text-gray-900">{step.title}</div>
                          {step.date && (
                            <div className="text-xs text-gray-500">{formatDate(step.date)}</div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              
              {/* Tracking Link */}
              {order.tracking_url && (
                <div className="mt-8 text-center">
                  <a 
                    href={order.tracking_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                  >
                    Track Package on {order.carrier}
                  </a>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-600">
              Tracking information will be available once your order ships.
            </p>
          )}
        </div>
        
        {/* Order Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Order Items */}
          <div className="md:col-span-2">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-medium text-gray-900 mb-4">Order Items</h2>
              
              <div className="space-y-6">
                {order.items.map(item => (
                  <div key={item.id} className="flex border-b border-gray-200 pb-6 last:border-b-0 last:pb-0">
                    <div className="w-20 h-20">
                      <img 
                        src={item.image_url} 
                        alt={item.name}
                        className="w-full h-full object-cover rounded"
                      />
                    </div>
                    
                    <div className="ml-4 flex-1">
                      <div className="flex flex-col sm:flex-row sm:justify-between">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            <Link to={`/products/${item.product_id}`} className="hover:text-blue-600">
                              {item.name}
                            </Link>
                          </h3>
                          
                          {item.variant && (
                            <p className="text-sm text-gray-600 mt-1">
                              {Object.entries(item.variant).map(([key, value]) => (
                                <span key={key} className="mr-2">
                                  {key}: {value}
                                </span>
                              ))}
                            </p>
                          )}
                        </div>
                        
                        <div className="mt-2 sm:mt-0 text-right">
                          <p className="text-gray-900 font-medium">${item.price.toFixed(2)}</p>
                          <p className="text-gray-600">Qty: {item.quantity}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Order Summary */}
          <div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-medium text-gray-900 mb-4">Order Summary</h2>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="text-gray-900">${order.subtotal.toFixed(2)}</span>
                </div>
                
                {order.discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span>-${order.discount.toFixed(2)}</span>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Shipping</span>
                  <span className="text-gray-900">
                    {order.shipping === 0 ? 'Free' : `$${order.shipping.toFixed(2)}`}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax</span>
                  <span className="text-gray-900">${order.tax.toFixed(2)}</span>
                </div>
                
                <div className="border-t border-gray-200 pt-3 mt-3">
                  <div className="flex justify-between font-medium">
                    <span className="text-gray-900">Total</span>
                    <span className="text-gray-900">${order.total.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              
              {/* Shipping Address */}
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Shipping Address</h3>
                <address className="text-sm text-gray-600 not-italic">
                  {order.shipping_address.name}  

                  {order.shipping_address.street}  

                  {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.zip}  

                  {order.shipping_address.country}
                </address>
              </div>
              
              {/* Payment Method */}
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Payment Method</h3>
                <p className="text-sm text-gray-600">
                  {order.payment_method.type === 'card' ? (
                    <>
                      {order.payment_method.brand} •••• {order.payment_method.last4}
                    </>
                  ) : (
                    order.payment_method.name
                  )}
                </p>
              </div>
              
              {/* Need Help */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Need Help?</h3>
                <div className="space-y-2">
                  <Link to="/support" className="text-blue-600 hover:text-blue-800 text-sm block">
                    Contact Support
                  </Link>
                  <Link to="/returns" className="text-blue-600 hover:text-blue-800 text-sm block">
                    Return Policy
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Back to Orders */}
        <div className="mt-8">
          <Link 
            to="/account/orders" 
            className="text-blue-600 hover:text-blue-800 flex items-center"
          >
            <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Back to Orders
          </Link>
        </div>
      </div>
    </div>
   );
}

export default OrderTracking;
